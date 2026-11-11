#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""station_drive.py - 机器自驱主循环（station self-drive）。

CEO 2026-11-11：「机队机器要有完全的自驱力，而不是什么都等主控，主控只是搜集了解
和分发，还有模型赋能，机器没活自己找，自己全链路解决，自己搞定一切。」

所以这台机不再等卡。一个循环做六件事：

  1 SENSE   读自己的领域（TAXONOMY 里以本工位为承接方的工序），看产物缺了或过期了
  2 SUPPLY  缺就自己建卡写进自己的分片（不需要主控派）；同一工序同一天只建一次
  3 CLAIM   自己领，自己写 owner/claimed_at
  4 RUN     跑卡上的 cmd，结果与日志落到 out/<产品>/<工序>/_run.json
  5 VERIFY  按卡上的判据自验：确定性判据过了才算 DONE；人判型一律 PENDING_HUMAN
  6 RECORD  写回执（含 sha256/字节数/耗时/判据结论），并把下一道工序的输入交给目标工位

只写自己的分片。跨机只做 handoff 追加，不改别人的卡状态。
找主控只有三件事：要模型（8792 网关）、目标工位不在线、对外/花钱/不可逆。

边界（硬）：
  * 不自动对外：不登录、不发送、不发布、不注册。
  * 不自封人判：judge 是 manual/human 的，永远停在 PENDING_HUMAN。
  * 不造活：产物路径没有契约（PRODUCTS.outputs 没写）的工序，只报 UNKNOWN-OUTPUT，不建卡。

用法：
  python3 Tools/fleet/station_drive.py --station control --dry     # 只看它想干什么
  python3 Tools/fleet/station_drive.py --station control --once     # 干一轮
  python3 Tools/fleet/station_drive.py --station control --loop 300
  python3 Tools/fleet/station_drive.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")

sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402

MANUAL_JUDGES = ("manual", "human")
DONE_STATES = ("DONE", "CANCELLED", "SHELVED")


def _now():
    return datetime.now()


def _load(name, root=None):
    base = os.path.join(root, "cph4", "fleet") if root else F
    with open(os.path.join(base, name), encoding="utf-8") as f:
        return json.load(f)


def _sha(path, limit=64 * 1024 * 1024):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
            if n > limit:
                break
    return h.hexdigest()


def _tree_sha(path):
    """目录指纹：路径+大小+文件哈希按序拼起来再取 sha256。目录产物也能被抽验。"""
    h = hashlib.sha256()
    for d, _, xs in sorted(os.walk(path)):
        for x in sorted(xs):
            fp = os.path.join(d, x)
            rel = os.path.relpath(fp, path)
            try:
                h.update(rel.encode())
                h.update(b"|")
                h.update(str(os.path.getsize(fp)).encode())
                h.update(b"|")
                with open(fp, "rb") as f:
                    h.update(hashlib.sha256(f.read()).digest())
            except OSError:
                continue
    return h.hexdigest()


def _digest(path):
    """统一走 station_shards.digest，禁止本地另写一份。"""
    return ss.digest(path)


def _size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    if os.path.isdir(path):
        return sum(os.path.getsize(os.path.join(d, x))
                   for d, _, xs in os.walk(path) for x in xs)
    return -1


def _newest_mtime(path):
    """产物的新鲜度看目录里最新文件，不看目录自身 mtime（目录 mtime 只在增删文件时变）。"""
    if os.path.isfile(path):
        return os.path.getmtime(path)
    newest = 0
    for d, _, xs in os.walk(path):
        for x in xs:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(d, x)))
            except OSError:
                pass
    return newest or os.path.getmtime(path)


def _fresh_enough(path, refresh_h, now=None):
    """产物算不算"已经做过了"。
    - 产物不存在 -> 不算做（要补）
    - 没有 refresh_h -> 一次性工序：有产物就算做完，绝不每轮重做
      （2026-11-11 预演实锚：原实现把"无保质期"当"已过期"，每轮重跑，
       五台机上线就会无限重复劳动）
    - 有 refresh_h -> 按最新文件时间判周期重置"""
    if not os.path.exists(path):
        return False
    if not refresh_h:
        return True
    # now 允许 datetime 或 float（2026-11-11 鲁棒性用例 R-09 实锚：只收 datetime 时，
    # 传时间戳的调用方直接 TypeError，而这类判据恰好是"过期/重建"的入口）
    _n = now if now is not None else _now()
    if isinstance(_n, (int, float)):
        _n = datetime.fromtimestamp(_n)
    age_h = (_n - datetime.fromtimestamp(_newest_mtime(path))).total_seconds() / 3600
    return age_h < float(refresh_h)


def plan(station, root=None, now=None):
    """SENSE + SUPPLY 的判定部分：算出该建哪些卡、哪些工序没有产物契约。"""
    tax = _load("TAXONOMY-v1.json", root)
    products = _load("PRODUCTS.json", root)["products"]
    types = {t["id"]: t for t in tax["task_types"]}
    smap = tax.get("stage_map") or {}
    rroot = root or ROOT

    have = ss.read_queue(station, root)
    open_keys = {(c.get("product_id"), c.get("stage")) for c in have
                 if c.get("state") not in DONE_STATES}

    want, unknown = [], []
    for p in products:
        pid = p["id"]
        outputs = p.get("outputs") or {}
        for stage in (p.get("stages") or []):
            tid = (smap.get(pid) or {}).get(stage)
            if not tid or tid not in types:
                continue
            t = types[tid]
            owners = t.get("stations") or []
            if not owners:
                # 无承接方：权限件（CEO 亲办）要报出来，别静默跳过；其余是真缺口
                unknown.append({"product": pid, "stage": stage, "task_type": tid,
                                "why": ("AUTHORITY：CEO 权限件，机器不代做" if t.get("human")
                                        else "NO-OWNER：没有任何工位承接")})
                continue
            if station not in owners:
                continue
            if stage in (p.get("manual_stages") or []):
                unknown.append({"product": pid, "stage": stage, "task_type": tid,
                                "why": "AUTHORITY：CEO 权限件（发送/注册/备案），机器不代做"})
                continue
            rel = outputs.get(stage)
            if not rel:
                unknown.append({"product": pid, "stage": stage, "task_type": tid,
                                "why": "NO-CONTRACT：未声明产物路径，不建卡（不造活）"})
                continue
            if not (p.get("commands") or {}).get(stage) and not t.get("selfdrive_cmd"):
                unknown.append({"product": pid, "stage": stage, "task_type": tid,
                                "why": "TOOL-PENDING：契约有、命令未接，先不建卡"})
                continue
            path = os.path.join(rroot, rel)
            if _fresh_enough(path, t.get("refresh_h"), now):
                continue
            if (pid, stage) in open_keys:
                continue
            want.append({"product": pid, "stage": stage, "task_type": tid, "cmd": (p.get("commands") or {}).get(stage),
                         "output": rel, "refresh_h": t.get("refresh_h"),
                         "judge": t.get("judge"),
                         "missing": not os.path.exists(path)})
    return want, unknown


def make_card(station, item, day=None, now=None):
    day = day or (now or _now()).strftime("%Y%m%d")
    pid, stage = item["product"], item["stage"]
    return {
        "id": "SD-%s-%s-%s-%s" % (station, pid, stage.replace(" ", ""), day),
        "title": "[self-drive] %s · %s" % (pid, stage),
        "product_id": pid,
        "stage": stage,
        "task_type": item["task_type"],
        "station": station,
        "nodes": [station],
        "state": "OPEN",
        "owner": None,
        "created_by": "self-drive",
        "created_at": _now().isoformat(timespec="seconds"),
        "why": "产物%s（%s）" % ("缺失" if item.get("missing") else "过期", item.get("output")),
        "deliverable": item.get("output"),
        "judge": item.get("judge"),
        "accept": "判据见 task_type=%s（judge=%s）" % (item["task_type"], item.get("judge")),
        "cmd": item.get("cmd") or "",
        "prio": "P2",
        "needs": "cpu",
        "route": "local",
    }


def claim(station, card, root=None):
    card = dict(card)
    card.update({"state": "RUNNING", "owner": station,
                 "claimed_at": _now().isoformat(timespec="seconds")})
    ss.upsert(station, card, root)
    return card


def run_card(station, card, root=None, timeout=1800):
    """执行卡上的 cmd。没有 cmd 的卡不假装跑过——直接判 NEED-CMD。"""
    rroot = root or ROOT
    cmd = (card.get("cmd") or "").strip()
    out_rel = os.path.join("cph4", "fleet", "out", card.get("product_id") or "_",
                           (card.get("stage") or "_").replace(" ", ""))
    out_abs = os.path.join(rroot, out_rel)
    os.makedirs(out_abs, exist_ok=True)
    man_p = os.path.join(out_abs, "_run.json")

    if not cmd:
        man = {"ts": _now().isoformat(timespec="seconds"), "rc": None,
               "note": "无 cmd：自驱只建卡不代劳，需补执行命令", "station": station}
        _write_manifest(man_p, man)
        return {"ok": False, "rc": None, "why": "NEED-CMD", "manifest": man_p, "out": out_abs}

    t0 = time.time()
    with open(os.path.join(out_abs, "run.log"), "w", encoding="utf-8") as log:
        p = subprocess.run(cmd, shell=True, cwd=rroot, stdout=log,
                           stderr=subprocess.STDOUT, timeout=timeout)
    man = {"ts": _now().isoformat(timespec="seconds"), "rc": p.returncode,
           "seconds": round(time.time() - t0, 1), "cmd": cmd, "station": station}
    _write_manifest(man_p, man)
    return {"ok": p.returncode == 0, "rc": p.returncode, "why": "" if p.returncode == 0 else "RC!=0",
            "manifest": man_p, "out": out_abs}


def _write_manifest(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def verify(station, card, run, root=None):
    """自验：确定性判据过了才算 DONE；人判型一律 PENDING_HUMAN。"""
    rroot = root or ROOT
    judge = (card.get("judge") or "").strip()
    if not judge and card.get("task_type"):
        try:
            types = {t["id"]: t for t in _load("TAXONOMY-v1.json", root)["task_types"]}
            judge = (types.get(card["task_type"]) or {}).get("judge") or ""
        except Exception:
            judge = ""
    # 先看跑没跑成：命令失败就别花算力去评审（顺序错了会白烧 token）
    if run.get("why") == "NEED-CMD":
        return "BLOCKED", "NEED-CMD：缺执行命令"
    if not run.get("ok"):
        return "FAILED", "执行失败 rc=%s" % run.get("rc")
    if not judge:
        # 判据没写就不许自证完成（诚实律）
        return "PENDING_HUMAN", "未写判据，不许自证"
    if judge == "panel":
        try:
            import panel_review as pr
        except Exception as e:
            return "PENDING_REVIEW", "评审团不可用: %s" % str(e)[:40]
        deliverable = card.get("deliverable")
        r = pr.review(product=card.get("product_id"), stage=card.get("stage"),
                      task_type=card.get("task_type"),
                      evidence=[deliverable] if deliverable else [])
        v = r.get("verdict")
        if v == "PASS":
            return "DONE", "评审团通过(%s): %s" % (r.get("skill"), r.get("why"))
        if v == "REVISE":
            return "REVISE", "评审团要求返工: %s" % (r.get("why") or "")[:80]
        return "FAILED", "评审团否决: %s" % (r.get("why") or "")[:80]
    if judge in MANUAL_JUDGES:
        return "PENDING_HUMAN", "judge=%s 需人判" % judge
    deliverable = card.get("deliverable")
    if deliverable:
        p = os.path.join(rroot, deliverable)
        if _size(p) <= 0:
            return "FAILED", "产物不存在或为空: %s" % deliverable
    vc = (card.get("verify_cmd") or "").strip()
    if vc:
        p = subprocess.run(vc, shell=True, cwd=rroot, capture_output=True, text=True)
        if p.returncode != 0:
            return "FAILED", "判据命令 rc=%s" % p.returncode
    return "DONE", "判据通过(%s)" % judge


def record(station, card, verdict, why, root=None):
    rroot = root or ROOT
    deliverable = card.get("deliverable")
    p = os.path.join(rroot, deliverable) if deliverable else ""
    rcpt = {
        "id": card["id"], "station": station, "product_id": card.get("product_id"),
        "stage": card.get("stage"), "task_type": card.get("task_type"),
        "verdict": verdict, "why": why,
        "deliverable": deliverable,
        "bytes": _size(p) if p else None,
        "sha256": _digest(p) if p and os.path.exists(p) else None,
        "ts": _now().isoformat(timespec="seconds"),
        "by": "self-drive",
    }
    ss.append_receipt(station, rcpt, root)
    card = dict(card)
    card.update({"state": verdict, "finished_at": rcpt["ts"],
                 "result": {"why": why, "bytes": rcpt["bytes"]}})
    ss.upsert(station, card, root)
    return rcpt


def handoff(station, card, root=None):
    """把下一道工序的输入交给目标工位（跨机直连，不经过主控）。"""
    tax = _load("TAXONOMY-v1.json", root)
    types = {t["id"]: t for t in tax["task_types"]}
    products = {p["id"]: p for p in _load("PRODUCTS.json", root)["products"]}
    p = products.get(card.get("product_id")) or {}
    stages = p.get("stages") or []
    try:
        i = stages.index(card.get("stage"))
    except ValueError:
        return None
    if i + 1 >= len(stages):
        return None
    nxt = stages[i + 1]
    tid = (tax.get("stage_map") or {}).get(p["id"], {}).get(nxt)
    if not tid or tid not in types:
        return None
    targets = types[tid].get("stations") or []
    if not targets:
        return None
    tgt = targets[0]
    if tgt == station:
        return {"to": station, "stage": nxt, "task_type": tid, "note": "同机下一道，循环内自然接上"}
    if tgt not in ss.STATIONS:
        # 目标工位不在登记表：安静跳过并留痕，不许让一个坏配置把整轮打断
        return {"to": tgt, "stage": nxt, "task_type": tid,
                "note": "目标工位不在登记表，跳过交接（配置需修）"}
    hid = "HO-%s-%s" % (card.get("product_id"), nxt.replace(" ", ""))
    for exist in ss.read_queue(tgt, root):
        # 只要下游已经有这道工序的卡（任何状态），就不再投一张——否则同一件活干两遍
        if str(exist.get("id")) == hid or (
                exist.get("product_id") == card.get("product_id")
                and exist.get("stage") == nxt):
            return {"to": tgt, "stage": nxt, "task_type": tid, "card": exist.get("id"),
                    "note": "下游已有这道工序的卡，未重复投递"}
    row = {
        "id": hid,
        "title": "[handoff] %s · %s" % (card.get("product_id"), nxt),
        "product_id": card.get("product_id"), "stage": nxt, "task_type": tid,
        "station": tgt, "nodes": [tgt], "state": "OPEN", "created_by": "handoff:" + station,
        "created_at": _now().isoformat(timespec="seconds"),
        "why": "上游 %s 已完成：%s" % (station, card.get("id")),
        "deliverable": (products.get(card.get("product_id")) or {}).get("outputs", {}).get(nxt),
        # 交接单必须自带执行命令与判据，否则下游接得住也跑不了（R14 实测）
        "cmd": ((products.get(card.get("product_id")) or {}).get("commands") or {}).get(nxt, ""),
        "judge": (types.get(tid) or {}).get("judge"),
        "needs": "cpu",
    }
    if tgt in ss.STATIONS:
        ss.upsert(tgt, row, root)
    return {"to": tgt, "stage": nxt, "task_type": tid, "card": row["id"]}


RUNNABLE = ("ready", "online", "network_ok_not_registered")


def _lease_minutes(root=None):
    """租约分钟：只从配置读，不写死。"""
    try:
        cfg = _load("AUTONOMY-CONFIG.json", root) or {}
        v = ((cfg.get("lease_minutes") or {}).get("default")
             or cfg.get("lease_minutes_default") or cfg.get("lease_minutes"))
        if isinstance(v, int):
            return v
    except Exception:
        pass
    try:
        cfg = _load("CARD-POLICY-v1.json", root) or {}
        v = (cfg.get("lease") or {}).get("minutes") or cfg.get("lease_minutes")
        if isinstance(v, int):
            return v
    except Exception:
        pass
    return 45


def reclaim(station, root=None, now=None, lease_min=None):
    """回收卡死的 RUNNING：认领超租约且无新回执 -> 退回 OPEN，写 release_reason。
    2026-11-11 预演发现：进程被 kill 后卡永久 RUNNING，新机队没有回收机制。"""
    now_dt = now or _now()
    lease = lease_min or _lease_minutes(root)
    rows = ss.read_queue(station, root)
    rec = 0
    for r in rows:
        if str(r.get("state")).upper() != "RUNNING":
            continue
        if (r.get("owner") or "") != station:
            continue
        ts = str(r.get("claimed_at") or r.get("assign_ts") or "")
        try:
            age = (now_dt - datetime.fromisoformat(ts[:19])).total_seconds() / 60
        except Exception:
            age = None
        if age is None or age <= lease:
            continue
        row = dict(r)
        row.update({"state": "OPEN", "owner": None, "release_reason":
                    "认领 %.0f 分钟无回执（租约 %s 分钟），已回收重排" % (age, lease)})
        ss.upsert(station, row, root)
        rec += 1
    return rec


def _status_ok(station, root=None, force=False):
    """机器自己先看状态：被暂停/离线/未安装就不干活。手工演练用 --force 显式越过。"""
    if force:
        return True, "force"
    try:
        st = {s["id"]: s for s in _load("STATIONS.json", root)["stations"]}[station]
    except Exception:
        return True, ""
    status = st.get("status") or ""
    if status in RUNNABLE:
        return True, status
    return False, "本机状态=%s，不自驱（停/离线/未装）" % status


def _disk_ok(station, root=None):
    """领活前查盘：低于配置水位就不跑，写一条 BLOCKED 理由，不许失败循环。"""
    try:
        st = {s["id"]: s for s in _load("STATIONS.json", root)["stations"]}[station]
    except Exception:
        return True, ""
    need = st.get("min_free_gb")
    if not need:
        return True, ""
    try:
        free = shutil.disk_usage(root or ROOT).free / (1024 ** 3)
    except Exception:
        return True, ""
    if free < float(need):
        return False, "磁盘余 %.1fG < 水位 %sG" % (free, need)
    return True, ""


def once(station, root=None, dry=False, now=None, run_limit=3, force=False):
    ok, why = _status_ok(station, root, force)
    if not ok:
        return {"station": station, "ts": _now().isoformat(timespec="seconds"),
                "blocked": why, "would_create": [], "unknown_output": [], "ran": []}
    ok, why = _disk_ok(station, root)
    if not ok:
        return {"station": station, "ts": _now().isoformat(timespec="seconds"),
                "blocked": why, "would_create": [], "unknown_output": [], "ran": []}
    reclaimed = reclaim(station, root, now)
    want, unknown = plan(station, root, now)
    report = {"station": station, "ts": _now().isoformat(timespec="seconds"),
              "reclaimed": reclaimed,
              "would_create": [w["product"] + "/" + w["stage"] for w in want],
              "unknown_output": ["%s/%s" % (u["product"], u["stage"]) for u in unknown],
              "ran": [], "handoff": []}
    if dry:
        return report
    for item in want:
        card = make_card(station, item, now=now)
        ss.upsert(station, card, root)
        report["would_create"].append(card["id"])
    # 领自己队列里可跑的
    n = 0
    for card in ss.read_queue(station, root):
        if n >= run_limit:
            break
        # 只认"本分片里的可执行 OPEN 卡"——不管是谁写的：
        # 自驱建的、主控 fleet_cmd 下的、回收后重排的，一律执行。
        # 2026-11-11 预演发现：只跑 created_by=self-drive 会让主控下的卡永远躺着。
        if card.get("state") != "OPEN" or not (card.get("cmd") or "").strip():
            continue
        card = claim(station, card, root)
        run = run_card(station, card, root)
        verdict, why = verify(station, card, run, root)
        rc = record(station, card, verdict, why, root)
        report["ran"].append({"id": card["id"], "verdict": verdict, "why": why,
                             "bytes": rc.get("bytes")})
        if verdict == "DONE":
            h = handoff(station, card, root)
            if h:
                report["handoff"].append(h)
        n += 1
    ss.append_log(station, {"kind": "self-drive", "report": report}, root)
    return report


# ---------------------------------------------------------------- 自检
def self_test():
    import tempfile
    ok = 0
    total = 0

    def chk(name, cond):
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
            print("ok   " + name)
        else:
            print("FAIL " + name)

    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, "cph4", "fleet")
        os.makedirs(os.path.join(base, "rt", "control"))
        tax = {
            "task_types": [
                {"id": "T-COMMENT", "stations": ["control"], "refresh_h": 24, "judge": "path"},
                {"id": "T-MANUAL", "stations": ["control"], "judge": "manual"},
                {"id": "T-NOOUT", "stations": ["control"], "judge": "path"},
            ],
            "stage_map": {"P1": {"草稿": "T-COMMENT", "复盘": "T-MANUAL"},
                          "P2": {"步骤": "T-NOOUT"}},
        }
        prods = {"products": [
            {"id": "P1", "stages": ["草稿", "复盘"],
             "outputs": {"草稿": "out/p1/drafts.jsonl"},
             "commands": {"草稿": "true"}, "manual_stages": ["复盘"]},
            {"id": "P2", "stages": ["步骤"], "outputs": {}},
        ]}
        json.dump(tax, open(os.path.join(base, "TAXONOMY-v1.json"), "w"), ensure_ascii=False)
        json.dump(prods, open(os.path.join(base, "PRODUCTS.json"), "w"), ensure_ascii=False)

        want, unknown = plan("control", td)
        chk("缺产物 -> 建卡", [w["stage"] for w in want] == ["草稿"])
        chk("无产物契约 -> UNKNOWN-OUTPUT 不建卡",
            [u["stage"] for u in unknown] == ["复盘", "步骤"])

        card = make_card("control", want[0])
        chk("卡带 product_id/stage/task_type",
            card["product_id"] == "P1" and card["stage"] == "草稿" and card["task_type"] == "T-COMMENT")
        ss.upsert("control", card, td)
        want2, _ = plan("control", td)
        chk("已建卡不重复建", want2 == [])

        p = os.path.join(td, "out", "p1")
        os.makedirs(p)
        f = os.path.join(p, "drafts.jsonl")
        open(f, "w").write('{"a":1}\n')
        card_done = dict(card); card_done["state"] = "DONE"
        ss.upsert("control", card_done, td)
        want3, _ = plan("control", td)
        chk("产物新鲜 -> 不再建卡", want3 == [])

        old = time.time() - 3 * 24 * 3600
        os.utime(f, (old, old))
        want4, _ = plan("control", td)
        chk("产物过期(refresh_h=24h) -> 重建卡", [w["stage"] for w in want4] == ["草稿"])

        c2 = make_card("control", want4[0])
        rc = verify("control", c2, {"ok": True, "rc": 0}, td)
        chk("判据 path + 产物在盘 -> DONE", rc[0] == "DONE")

        c3 = dict(c2); c3["judge"] = "manual"
        chk("人判型 -> PENDING_HUMAN（不自证）", verify("control", c3, {"ok": True}, td)[0] == "PENDING_HUMAN")

        c4 = dict(c2); c4["judge"] = ""; c4["task_type"] = "T-NO-SUCH"
        chk("未写判据且查不到任务类型 -> 不许自证",
            verify("control", c4, {"ok": True}, td)[0] == "PENDING_HUMAN")
        c4b = dict(c2); c4b["judge"] = ""
        chk("卡没写判据时回退任务类型判据（path）",
            verify("control", c4b, {"ok": True}, td)[0] == "DONE")

        c5 = dict(c2); c5["deliverable"] = "out/none/x.bin"
        chk("产物缺失 -> FAILED", verify("control", c5, {"ok": True}, td)[0] == "FAILED")

        c_nocmd = dict(c2); c_nocmd["cmd"] = ""
        chk("无 cmd -> NEED-CMD 不假跑", run_card("control", c_nocmd, td)["why"] == "NEED-CMD")

    print("[station_drive] %d/%d" % (ok, total))
    return 0 if ok == total else 2


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", choices=list(ss.STATIONS), default="control")
    ap.add_argument("--root", default=None)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", type=int, default=0)
    ap.add_argument("--run-limit", type=int, default=3)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()
    if a.loop:
        while True:
            r = once(a.station, a.root, dry=a.dry, run_limit=a.run_limit, force=a.force)
            print(json.dumps(r, ensure_ascii=False))
            time.sleep(a.loop)
    r = once(a.station, a.root, dry=a.dry, run_limit=a.run_limit, force=a.force)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
