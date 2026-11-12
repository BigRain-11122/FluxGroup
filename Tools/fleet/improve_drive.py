#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""improve_drive.py - 持续改进的台账与推进器（不是报告生成器）。

Why（2026-11-12 CEO「你持续改进，列好计划，分布推进，自动化」）：
计划写在回复里会过期、会忘、会跟事实脱节。所以把它做成三件事：
    ① 台账落盘（cph4/fleet/IMPROVE-BACKLOG-v1.json），每项带证据与验收判据；
    ② 扫描器**扫真实事实**生成待办（不是手写清单），幂等去重；
    ③ 校验器抓两类假动作：DONE 却没证据、"已修"但触发条件仍然成立（假完成）。
推进仍归本地：每台机器 --next 拿自己的项，主控只读、只报、只下发。

判据约定：
  evidence   = 触发条件（"什么事实成立时这条算存在"），机器可复算；
  accept     = 关闭条件（"什么事实成立时这条算修好"），人工/机器都要能核；
  status     = OPEN / DOING / DONE / BLOCKED（DONE 必须带 close_evidence）。

用法：
    python3 Tools/fleet/improve_drive.py --scan          # 扫事实并入台账
    python3 Tools/fleet/improve_drive.py --check         # 校验台账（抓假完成）
    python3 Tools/fleet/improve_drive.py --next --station control
    python3 Tools/fleet/improve_drive.py --close IMP-XXX --evidence "提交 abc123"
    python3 Tools/fleet/improve_drive.py --self-test
返回码：0 无问题 / 1 有 OPEN 项（正常状态）/ 2 校验失败（假完成/证据缺失）/ 3 自检失败
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
LEDGER = os.path.join(FLEET, "IMPROVE-BACKLOG-v1.json")
NOW = lambda: datetime.now().isoformat(timespec="seconds")  # noqa: E731

STATUSES = ("OPEN", "DOING", "DONE", "BLOCKED", "DROPPED")


def _j(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _read_ledger(root=None):
    p = os.path.join(root or ROOT, "cph4", "fleet", "IMPROVE-BACKLOG-v1.json")
    d = _j(p, None)
    if not isinstance(d, dict):
        return {"version": "v1-20261112", "updated_at": NOW(), "items": []}
    d.setdefault("items", [])
    return d


def _write_ledger(d, root=None):
    p = os.path.join(root or ROOT, "cph4", "fleet", "IMPROVE-BACKLOG-v1.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    d["updated_at"] = NOW()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    return p


# ---------------------------------------------------------------- 扫描器
def _products(root=None):
    d = _j(os.path.join(root or ROOT, "cph4", "fleet", "PRODUCTS.json"), {}) or {}
    return d.get("products") or []


def scan_supply(root=None):
    """供给缺口：有产物契约但没有执行命令的工序（TOOL-PENDING）。"""
    out = []
    for p in _products(root):
        pid = p.get("id")
        cmds = p.get("commands") or {}
        for stg in (p.get("stages") or []):
            if not (p.get("outputs") or {}).get(stg):
                continue
            if cmds.get(stg):
                continue
            out.append({"id": "IMP-SUPPLY-%s-%s" % (pid, stg.replace(" ", "")),
                        "batch": 2, "domain": "供给", "owner": "control",
                        "title": "%s/%s 缺执行命令" % (pid, stg),
                        "evidence": "PRODUCTS.json 中 %s.commands.%s 为空且 outputs.%s 已声明" % (pid, stg, stg),
                        "fix": "补命令（复用现成工具）或在 PRODUCTS 里明确标 manual_stages（CEO 权限件）",
                        "accept": "PRODUCTS.json 里 %s.commands.%s 非空，或 stage 进入 manual_stages 且理由可查" % (pid, stg),
                        "status": "OPEN", "depends": []})
    return out


def scan_legacy_queue(root=None):
    """仍在读已归档旧队列的工具（旧队列已移入 storage/archive，读了就崩或空转）。"""
    root = root or ROOT
    hits = []
    for p in glob.glob(os.path.join(root, "Tools", "**", "*.py"), recursive=True):
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if "PRODUCTION-QUEUE.jsonl" in t and "storage/archive" not in t:
            hits.append(os.path.relpath(p, root))
    if not hits:
        return []
    return [{"id": "IMP-LEGACY-QUEUE", "batch": 3, "domain": "数据",
             "owner": "control",
             "title": "仍有 %d 个工具读已归档的旧队列" % len(hits),
             "evidence": "grep 命中：%s" % ", ".join(hits[:8]) + ("…" if len(hits) > 8 else ""),
             "fix": "逐个改读 rt/<station>/queue.jsonl；确属退役的标 RETIRED 并从排班/入口移除",
             "accept": "grep 'PRODUCTION-QUEUE.jsonl' Tools/ 命中为 0，或全部带 RETIRED 标记",
             "status": "OPEN", "depends": [],
             "detail": hits}]


def scan_docs(root=None):
    """文档陈旧：上位指针仍指被取代的正典；Windows 岗书写 python3。"""
    root = root or ROOT
    out = []
    ai = os.path.join(root, "AI.md")
    try:
        t = open(ai, encoding="utf-8", errors="replace").read()
    except OSError:
        t = ""
    # 判据只认"现行/正身"这类指针行；变更日志里出现旧正典名是历史记录，不是缺口。
    # （2026-11-12 实测：首版拿整篇字符串搜，把历史行也判成"仍指 V2"，属假红。）
    _bad = [ln for ln in t.splitlines() if ("现行" in ln or "正身" in ln) and "CANON-V2" in ln]
    if _bad:
        out.append({"id": "IMP-DOC-CANON", "batch": 1, "domain": "文档", "owner": "control",
                    "title": "AI.md 仍指 CANON-V2（已被 V3 取代）",
                    "evidence": "AI.md 含 CANON-V2 且不含 CANON-V3",
                    "fix": "上位指针改为 CANON-V3",
                    "accept": "AI.md 含 CANON-V3", "status": "OPEN", "depends": []})
    # 只判 Windows 工位；brain 的 OS 还没定档（os=unverified），不判——未定档就判
    # 等于逼人猜。另要跳过否定语境：岗书里"不存在 python3，实测 rc=9009"这类
    # 警告语含 python3 字样，首版把它们当成违规，是典型的字符串判据假红。
    WIN_STATIONS = {"delivery", "visual", "audio"}
    NEG = ("不存在", "不要", "禁用", "不用", "禁止", "别用", "没有", "不得")
    win3 = []
    for p in glob.glob(os.path.join(root, "cph4", "fleet", "stations", "*", "*.md")):
        sid = os.path.basename(os.path.dirname(p))
        if sid not in WIN_STATIONS:
            continue
        try:
            for ln in open(p, encoding="utf-8", errors="replace").read().splitlines():
                if "python3" in ln and not any(n in ln for n in NEG):
                    win3.append(os.path.relpath(p, root))
                    break
        except OSError:
            continue
    if win3:
        out.append({"id": "IMP-DOC-WIN-PY3", "batch": 1, "domain": "文档", "owner": "control",
                    "title": "Windows 岗书里仍有 python3（实际 rc=9009）",
                    "evidence": "命中：%s" % ", ".join(win3[:6]),
                    "fix": "按 OS 写解释器名：Windows 用 python，mac/linux 用 python3",
                    "accept": "工位文档中 Windows 段落不再出现 python3", "status": "OPEN",
                    "depends": [], "detail": win3})
    return out


def scan_executor(root=None):
    """执行体：状态说能干活、却没有任何心跳证据的工位。"""
    out = []
    try:
        sys.path.insert(0, HERE)
        import station_shards as ss
    except Exception:
        return out
    st = (_j(os.path.join(root or ROOT, "cph4", "fleet", "STATIONS.json"), {}) or {}).get("stations") or []
    for s in st:
        sid = s.get("id")
        status = str(s.get("status") or "")
        if status not in ("ready", "online", "network_ok_not_registered"):
            continue
        if sid == "control":
            continue          # 本机由 master_patrol 直接判，避免重复计项
        if ss.heartbeat_read(sid, root) is None:
            out.append({"id": "IMP-EXEC-%s" % sid, "batch": 3, "domain": "机队",
                        "owner": sid,
                        "title": "%s 执行体未注册（状态=%s）" % (sid, status),
                        "evidence": "STATIONS.json status=%s，且分片目录无 heartbeat.json" % status,
                        "fix": "在该机安装并启动 station_drive（install_drive_agent.py 生成，现场执行）",
                        "accept": "该机 heartbeat.json 存在且龄期 < 30 分钟",
                        "status": "OPEN", "depends": []})
    return out


def scan_all(root=None):
    found = []
    for fn in (scan_supply, scan_legacy_queue, scan_docs, scan_executor):
        try:
            found.extend(fn(root) or [])
        except Exception as e:
            found.append({"id": "IMP-SCAN-%s" % fn.__name__,
                          "batch": 0, "domain": "元", "owner": "control",
                          "title": "扫描器自身失败：%s" % fn.__name__,
                          "evidence": type(e).__name__, "fix": "修扫描器",
                          "accept": "扫描器返回正常", "status": "OPEN", "depends": []})
    return found


# ---------------------------------------------------------------- 合并/校验
def merge(ledger, found):
    """幂等合并：新项加入；已有项**不覆盖状态**（人工进展不能被扫描冲掉）。

    但 DONE 项若触发条件重新成立，必须退回 OPEN——否则"修好又坏"永远看不见。
    """
    have = {i["id"]: i for i in ledger.get("items") or []}
    found_ids = {f["id"] for f in found}
    added, reopened, dropped = 0, 0, 0
    # 触发条件不再成立的 OPEN 项 -> DROPPED（留痕不删）。否则判据一改，旧待办就成
    # 僵尸：永远 OPEN、永远没人能做、还把"还剩多少活"算错。
    for i in ledger.get("items") or []:
        if str(i.get("status")).upper() == "OPEN" and i["id"] not in found_ids:
            i.update({"status": "DROPPED", "dropped_at": NOW(),
                      "drop_reason": "触发条件不再成立（判据修正或事实已变），留痕不删"})
            dropped += 1
    for f in found:
        cur = have.get(f["id"])
        if cur is None:
            f.setdefault("created_at", NOW())
            ledger["items"].append(f)
            have[f["id"]] = f
            added += 1
            continue
        if str(cur.get("status")).upper() == "DONE":
            cur["status"] = "OPEN"
            cur["reopened_at"] = NOW()
            cur["reopen_reason"] = "触发条件重新成立（扫描再次命中）"
            reopened += 1
    return {"added": added, "reopened": reopened, "dropped": dropped}


def check(ledger, found=None):
    """校验台账：DONE 必须有证据；DONE 不许与当前事实矛盾；依赖必须存在。"""
    items = ledger.get("items") or []
    ids = {i["id"] for i in items}
    found_ids = {f["id"] for f in (found if found is not None else scan_all())}
    problems = []
    for i in items:
        st = str(i.get("status") or "").upper()
        if st not in STATUSES:
            problems.append({"kind": "BAD-STATUS", "id": i["id"], "why": "未知状态 %r" % i.get("status")})
        if st == "DONE" and not str(i.get("close_evidence") or "").strip():
            problems.append({"kind": "DONE-NO-EVIDENCE", "id": i["id"],
                             "why": "标记 DONE 但没写关闭证据"})
        if st == "DONE" and i["id"] in found_ids:
            problems.append({"kind": "FALSE-DONE", "id": i["id"],
                             "why": "标记已修，但触发条件仍然成立（假完成）"})
        for d in (i.get("depends") or []):
            if d not in ids:
                problems.append({"kind": "MISSING-DEP", "id": i["id"], "why": "依赖 %s 不在台账" % d})
        if not str(i.get("accept") or "").strip():
            problems.append({"kind": "NO-ACCEPT", "id": i["id"], "why": "没写关闭判据，无法验收"})
    return problems


def next_items(ledger, station=None, limit=5):
    """可执行项：OPEN + 依赖全 DONE + 归属本机（station 为空则全列）。"""
    by = {i["id"]: i for i in ledger.get("items") or []}
    out = []
    for i in ledger.get("items") or []:
        if str(i.get("status")).upper() != "OPEN":
            continue
        if station and (i.get("owner") or "") != station:
            continue
        if any(str((by.get(d) or {}).get("status", "")).upper() != "DONE"
               for d in (i.get("depends") or [])):
            continue
        out.append(i)
    out.sort(key=lambda x: (int(x.get("batch") or 9), x["id"]))
    return out[:limit]


# ---------------------------------------------------------------- 自检
def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    # 1 合并幂等 + 不覆盖人工状态
    led = {"items": []}
    f = [{"id": "X", "status": "OPEN", "accept": "a", "owner": "control", "batch": 1}]
    r1 = merge(led, f)
    r2 = merge(led, f)
    chk("合并幂等（第二次不新增）", r1["added"] == 1 and r2["added"] == 0, (r1, r2))
    led["items"][0]["status"] = "DOING"
    merge(led, f)
    chk("扫描不覆盖人工进展（DOING 保留）", led["items"][0]["status"] == "DOING")

    # 2 修好又坏 -> 退回 OPEN（负控：不重开就永远看不见）
    led["items"][0].update({"status": "DONE", "close_evidence": "提交 abc"})
    r3 = merge(led, f)
    chk("DONE 项触发条件重现 -> 退回 OPEN", led["items"][0]["status"] == "OPEN" and r3["reopened"] == 1)

    # 3 假完成被抓
    led2 = {"items": [{"id": "Y", "status": "DONE", "close_evidence": "x", "accept": "a"}]}
    probs = check(led2, found=[{"id": "Y"}])
    chk("负控：DONE 但事实仍成立 -> FALSE-DONE",
        any(p["kind"] == "FALSE-DONE" for p in probs), probs)

    # 4 DONE 无证据
    led3 = {"items": [{"id": "Z", "status": "DONE", "accept": "a"}]}
    chk("DONE 无关闭证据 -> DONE-NO-EVIDENCE",
        any(p["kind"] == "DONE-NO-EVIDENCE" for p in check(led3, found=[])))

    # 5 无判据
    led4 = {"items": [{"id": "W", "status": "OPEN"}]}
    chk("缺关闭判据 -> NO-ACCEPT", any(p["kind"] == "NO-ACCEPT" for p in check(led4, found=[])))

    # 6 next：依赖未完成不给
    led5 = {"items": [
        {"id": "A", "status": "OPEN", "accept": "a", "owner": "control", "batch": 1},
        {"id": "B", "status": "OPEN", "accept": "a", "owner": "control", "batch": 2, "depends": ["A"]},
        {"id": "C", "status": "OPEN", "accept": "a", "owner": "visual", "batch": 1}]}
    got = [i["id"] for i in next_items(led5, "control")]
    chk("next：依赖未完成不派 + 只派本机", got == ["A"], got)
    led5["items"][0]["status"] = "DONE"
    got2 = [i["id"] for i in next_items(led5, "control")]
    chk("依赖完成后放行", got2 == ["B"], got2)

    # 7 真仓扫描必须产出（不是空表）
    found = scan_all(ROOT)
    chk("真仓扫描非空（否则扫描器是假的）", len(found) >= 3, len(found))
    chk("扫描项都带 evidence/accept", all(f.get("evidence") and f.get("accept") for f in found),
        [f["id"] for f in found if not (f.get("evidence") and f.get("accept"))])

    # 8 触发条件消失 -> DROPPED（不是删掉，也不是假装完成）
    led6 = {"items": [{"id": "A", "status": "OPEN", "accept": "a"}]}
    r6 = merge(led6, [{"id": "B", "status": "OPEN", "accept": "a"}])
    chk("不再命中的 OPEN -> DROPPED 且留痕",
        led6["items"][0]["status"] == "DROPPED" and r6["dropped"] == 1, (led6, r6))
    chk("DROPPED 不算校验问题", check(led6, found=[{"id": "B"}]) == [], check(led6, found=[{"id": "B"}]))

    # 9 台账文件可往返
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = {"version": "v1", "items": [{"id": "T", "status": "OPEN", "accept": "a"}]}
        _write_ledger(d, td)
        back = _read_ledger(td)
        chk("台账写读往返", len(back["items"]) == 1 and back["items"][0]["id"] == "T", back)

    print("\n[improve_drive] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--station", default=None)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--close", default=None)
    ap.add_argument("--evidence", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()

    led = _read_ledger()
    if a.scan:
        found = scan_all()
        if not found:
            print("扫描为空，拒绝合并（防止扫描器故障把台账清空）")
            return 2
        r = merge(led, found)
        _write_ledger(led)
        print("扫描 %d 项｜新增 %d｜重开 %d｜台账共 %d 项"
              % (len(found), r["added"], r["reopened"], len(led["items"])))
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
        return 1 if any(str(i.get("status")) == "OPEN" for i in led["items"]) else 0

    if a.check:
        probs = check(led)
        if a.json:
            print(json.dumps(probs, ensure_ascii=False, indent=1))
        else:
            if not probs:
                print("台账一致：%d 项，无假完成" % len(led["items"]))
            for p in probs:
                print("[%s] %s：%s" % (p["kind"], p["id"], p["why"]))
        return 2 if probs else 0

    if a.next:
        items = next_items(led, a.station, a.limit)
        for i in items:
            print("%-40s 批%s %s｜%s" % (i["id"], i.get("batch"), i.get("owner"), i.get("title")))
        if not items:
            print("（本机当前没有可执行项）")
        return 0

    if a.close:
        hit = [i for i in led["items"] if i["id"] == a.close]
        if not hit:
            print("台账里没有 %s" % a.close)
            return 2
        if not (a.evidence or "").strip():
            print("关闭必须带 --evidence（不接受'我觉得修好了'）")
            return 2
        hit[0].update({"status": "DONE", "close_evidence": a.evidence, "closed_at": NOW()})
        _write_ledger(led)
        print("已关闭 %s：%s" % (a.close, a.evidence))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
