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
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")

sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402

MANUAL_JUDGES = ("manual", "human")
# plan() 判定"这道工序是否已有卡、不用再建"用（从 state_machine 派生，不许再各写一份）。
# 2026-11-12：原为本地常量 ("DONE","CANCELLED","SHELVED")，与 station_shards.TERMINAL
# 是两套互不相认的定义，ARCHIVED/SHELVED 行为正好相反。注意语义是 rebuild（可重建），
# 不是 closed（已结束）——BLOCKED 属停放但仍挡重建，否则缺输入的工序每轮刷一张卡。
import state_machine as _smk   # noqa: E402
DONE_STATES = _smk.rebuildable()

# 刚跑完的工序在 N 分钟内不再重建。防的是"累加式产物跑完不重写 → mtime 不变 →
# 永远判过期 → 每轮建一张新卡"（2026-11-12 实测同一草稿工序 23 分钟建了 4 张）。
REBUILD_GUARD_MIN = 60


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


def _prodsig(path):
    """产物签名：size + 前 64KB 哈希。

    不能用 mtime：run_card 成功后会 touch 产物（防"永远过期"），mtime 每次都变，
    拿它当签名等于每次都判"变了"，重复建卡照样发生。也不能全文件哈希：出图/出片
    动辄几百 MB，供给每轮都算承受不起。size + 头部哈希足够区分"有没有新内容"。
    """
    try:
        sz = os.path.getsize(path)
    except OSError:
        return None
    if sz == 0:
        return "0:"
    try:
        return "%d:%s" % (sz, _sha(path, 64 * 1024)[:16])
    except OSError:
        return None


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
    # 2026-11-12（根因修复）：open_keys 原来只来自**本分片**，且拿 (product_id, stage)
    # 原样比对。两个漏洞都是实测踩到的：
    #   ①同一工序的卡可能落在别的分片（老格式按 owner/nodes 定责，视觉分片里就有
    #     归属 asset-lib 的卡）——本分片看不见，于是判"没在跑"再建一张；
    #   ②老格式卡没有 product_id（只有标题或 line），比对恒不命中，同样判"没在跑"。
    # 结果：同一草稿工序 13:41/14:04/14:05/14:06 连出 4 张，全部 DONE，产物一模一样。
    # 现在改用跨分片归一化视图 inflight()（station_shards），加 recent_done 保护
    # "刚跑完但产物没刷新"的情况。写仍然只写本分片，这里只读。
    # 本地闭环（2026-11-12 CEO 校正）：供给只判**本分片**。本机工序的卡必然在
    # 自己分片里（实测错位为 0）；错位是数据问题，由巡检报出（MISPLACED-CARD），
    # 不由别的机器代判、更不由主控代写。stage_key 归一化保证老格式卡也能认出。
    inflight = set()
    for c in have:
        if str(c.get("state") or c.get("status") or "").upper() in ss.NON_BLOCKING_STATES:
            continue
        k = ss.stage_key(c) or ((c.get("product_id") or "").strip(),
                                (c.get("stage") or "").replace(" ", "").strip())
        if k[0] and k[1]:
            inflight.add(k)
    last_done = ss.last_done_cards(root, stations=[station])

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
            # 归一化后跨分片查在飞（与 ss.stage_key 同一把尺，避免两处各写一份归一化）
            key = (pid, stage.replace(" ", ""))
            if key in inflight or (pid, stage) in open_keys:
                continue
            # 上次跑完产物没变 = 命令成功但没产出新东西（累加式产物、inbox 空、
            # 或命令本身是空转）。这时重建只会重复烧算力，必须报缺口让人修命令，
            # 不能靠"再跑一次"自欺（实测同一工序 23 分钟被建 4 张、产物一模一样）。
            prev = last_done.get(key) or last_done.get((pid, stage))
            if prev is not None:
                prev_sig = prev.get("product_sig")
                now_sig = _prodsig(path) if os.path.exists(path) else None
                if prev_sig and now_sig and prev_sig == now_sig:
                    unknown.append({"product": pid, "stage": stage, "task_type": tid,
                                    "why": "OUTPUT-NOT-REFRESHED：上次执行成功但产物未更新"
                                           "（size/mtime 与上次一致），重复跑无意义"})
                    continue
            want.append({"product": pid, "stage": stage, "task_type": tid, "cmd": (p.get("commands") or {}).get(stage),
                         "output": rel, "refresh_h": t.get("refresh_h"),
                         "judge": t.get("judge"),
                         "requires": (p.get("requires") or {}).get(stage) or [],
                         "missing": not os.path.exists(path)})
    return want, unknown


def make_card(station, item, day=None, now=None):
    day = day or (now or _now()).strftime("%Y%m%d")
    pid, stage = item["product"], item["stage"]
    return {
        # 2026-11-12：id 到时分（原来只到日）。同一天重跑同一工序若生成同名卡，
        # 而终态回跳护栏拒绝把已有 DONE 卡改回 OPEN → 当天第二次起的重建全部失败
        # （调度器实测 SELF-DRIVE 每轮 rc=1）。同工序重跑必须是新卡。
        "id": "SD-%s-%s-%s-%s-%s" % (station, pid, stage.replace(" ", ""), day,
                                     (now or _now()).strftime("%H%M")),
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
        "requires": item.get("requires") or [],
        "prio": "P2",
        "needs": "cpu",
        "route": "local",
    }


def _singleton_acquire(station):
    """本工位进程级单例锁：同一台机不许两个自驱同时跑。

    2026-11-12（批次3.1）。CAS 保证"同一张卡只被领一次"，但两个自驱同时跑还会
    抢同一分片、同时写状态与日志；launchd 的 keep_alive 重启也可能与上一轮重叠。
    返回值：文件句柄（成功，进程退出自动释放）或 None（已有实例）。
    """
    import tempfile as _tf
    p = os.path.join(_tf.gettempdir(), "fluxgroup-station-%s.lock" % station)
    try:
        fh = open(p, "a+")
    except Exception:
        return None
    try:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except ImportError:
        try:
            import msvcrt
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return fh
        except Exception:
            fh.close()
            return None
    except Exception:
        fh.close()
        return None


def claim(station, card, root=None):
    """原子取件：锁内复读，仍为 OPEN 才写 RUNNING；抢不到返回 None。

    2026-11-12 改（批次3.1）。原来是"读快照 → 无条件写 RUNNING"，三个进程同时
    --once 会各自领到同一张卡（实测执行 3 次、钱扣 3 遍、回执只剩 2 份）。
    """
    patch = {"state": "RUNNING", "owner": station,
             "claimed_at": _now().isoformat(timespec="seconds")}
    ok, cur = ss.cas_state(station, card.get("id"), "OPEN", patch, root)
    if not ok:
        return None
    out = dict(card)
    out.update(patch)
    return out


DANGER_PATTERNS = (";", "&&", "||", "$(", "`", "rm -rf", "curl ", "wget ",
                   "git push", "> /", "chmod 777", "sudo ")


def _cmd_guard(cmd, card, root=None):
    """命令授权闸（2026-11-12，批次2.1）。

    背景：run_card 用 shell=True 执行卡上的任意字符串，而卡来自分片（可被提交/推送
    改写）。能往 rt/*/queue.jsonl 写一行的人，就能在五台机上以本机用户身份执行任意
    命令——实测能读令牌、改台账、git push 把恶意卡播给全机队。

    规则（默认拒绝，白名单优先）：
      1) cmd 与 PRODUCTS.json 里某道工序的 commands 完全一致 → 放行（已审命令）；
      2) 否则必须 card.cmd_reviewed 为真，且不含危险拼接/外联模式；
      3) 其余一律 CMD-REJECTED，不执行。
    """
    cmd = (cmd or "").strip()
    if not cmd:
        return True, ""
    try:
        products = _load("PRODUCTS.json", root)["products"]
        known = set()
        for pr in products:
            for c in (pr.get("commands") or {}).values():
                if c:
                    known.add(str(c).strip())
        if cmd in known:
            return True, "allowlisted"
    except Exception:
        pass                     # 取不到白名单就走第 2 条，不因此放行
    if not card.get("cmd_reviewed"):
        return False, "命令不在 PRODUCTS 已审清单里，且卡上没有 cmd_reviewed 标记"
    # 已审命令不再用黑名单硬拒：产物命令本来就常用 &&、管道与重定向（实测 R3 的
    # `mkdir -p x && echo > x/f` 被首版黑名单误杀）。授权靠"谁审过"，黑名单只作审计标记。
    hit = [d for d in DANGER_PATTERNS if d in cmd]
    return True, ("reviewed" + ("（含高危模式：%s，已记入 manifest）" % ", ".join(hit) if hit else ""))


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

    # 前置输入检查（2026-11-12，批次5）：requires 里的路径不存在 -> BLOCKED（缺输入）。
    # 原来索引工序因 out/asset-pack 不存在每天 FAIL 一次，既不成功也不告诉人缺什么。
    _miss = [q for q in (card.get("requires") or [])
             if not os.path.exists(os.path.join(rroot, q))]
    if _miss:
        man = {"ts": _now().isoformat(timespec="seconds"), "rc": None,
               "note": "缺前置输入：" + ", ".join(_miss), "cmd": cmd, "station": station}
        _write_manifest(man_p, man)
        return {"ok": False, "rc": None, "why": "BLOCKED",
                "detail": "缺前置输入：" + ", ".join(_miss), "manifest": man_p, "out": out_abs}

    allowed, _why = _cmd_guard(cmd, card, root)
    if not allowed:
        man = {"ts": _now().isoformat(timespec="seconds"), "rc": None,
               "note": "命令未授权：" + _why, "cmd": cmd, "station": station}
        _write_manifest(man_p, man)
        return {"ok": False, "rc": None, "why": "CMD-REJECTED",
                "detail": _why, "manifest": man_p, "out": out_abs}

    t0 = time.time()
    timed_out = False
    with open(os.path.join(out_abs, "run.log"), "w", encoding="utf-8") as log:
        # 2026-11-12（批次4.1）：原实现直接 subprocess.run(timeout=...)，超时抛异常穿出
        # once() → 卡已是 RUNNING 但 record/append_log 都没写（无回执、无日志）；
        # 且 shell=True 只杀掉 shell，真正的子进程继续跑并继续写同一产物目录，
        # 45 分钟后 reclaim 退回 OPEN 重跑 → 两个写者同写一个产物。
        # 现在：独立进程组 + 超时整组杀 + 判 TIMEOUT 并写回执。
        # 用 Popen 自己管超时：subprocess.run 超时只 kill 直接子进程（shell），
        # 杀不到它拉起的 ffmpeg/blender，孤儿会继续写同一产物目录。
        proc = subprocess.Popen(cmd, shell=True, cwd=rroot, stdout=log,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            _rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                proc.wait(timeout=30)
            except Exception:
                pass
            _rc = -9

        class _R:
            returncode = _rc
        p = _R()
    if timed_out:
        man = {"ts": _now().isoformat(timespec="seconds"), "rc": -9,
               "seconds": round(time.time() - t0, 1), "cmd": cmd, "station": station,
               "note": "超时 %ss，已杀进程组" % timeout}
        _write_manifest(man_p, man)
        return {"ok": False, "rc": -9, "why": "TIMEOUT", "manifest": man_p, "out": out_abs}
    # 刷新计时器（2026-11-12 实测）：refresh_h 的语义是"每 N 小时检查一次"，
    # 但很多工序是累加式产物（如评论草稿：没有新输入就不重写文件），跑完 mtime 不变
    # → 永远判过期 → 每轮建卡（实测每 5 分钟一张，一天几百张）。检查完成即重置。
    # 只在命令成功且产物存在时 touch；失败不重置（否则坏件会被当成"刚检查过"）。
    _dlv = card.get("deliverable")
    if p.returncode == 0 and _dlv:
        _d = os.path.join(rroot, _dlv)
        try:
            if os.path.exists(_d):
                os.utime(_d, None)
        except Exception:
            pass
    man = {"ts": _now().isoformat(timespec="seconds"), "rc": p.returncode,
           "seconds": round(time.time() - t0, 1), "cmd": cmd, "station": station}
    _write_manifest(man_p, man)
    return {"ok": p.returncode == 0, "rc": p.returncode, "why": "" if p.returncode == 0 else "RC!=0",
            "manifest": man_p, "out": out_abs}


def _write_manifest(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def _judge_of(card, root=None):
    """解析判据与来源：taxonomy 的人判优先于卡级（唯一判据，verify/record 共用）。"""
    judge = (card.get("judge") or "").strip().lower()
    tjudge = ""
    if card.get("task_type"):
        try:
            types = {t["id"]: t for t in _load("TAXONOMY-v1.json", root)["task_types"]}
            tjudge = ((types.get(card["task_type"]) or {}).get("judge") or "").strip().lower()
        except Exception:
            tjudge = ""
    if tjudge in MANUAL_JUDGES:
        return tjudge, "taxonomy"
    if judge:
        return judge, "card"
    return tjudge, ("taxonomy" if tjudge else "none")


def verify(station, card, run, root=None):
    """自验：确定性判据过了才算 DONE；人判型一律 PENDING_HUMAN。

    两条护栏（2026-11-11 审出来，都是可绕过的真洞）：
      1) judge 大小写敏感：「MANUAL」/「Manual」过去判不进 MANUAL_JUDGES，
         卡上写个大写就能自标 DONE —— 统一 strip().lower()。
      2) 卡级 judge 不许把 taxonomy 的人判件降级：只有 taxonomy（或更高权威）
         说是人判，卡上写 path/auto 也不能把它改成机器判。
    """
    rroot = root or ROOT
    judge, _src = _judge_of(card, root)   # 唯一判据：record() 写回执用同一实现
    # 先看跑没跑成：命令失败就别花算力去评审（顺序错了会白烧 token）
    if run.get("why") == "NEED-CMD":
        return "BLOCKED", "NEED-CMD：缺执行命令"
    if run.get("why") == "BLOCKED":
        return "BLOCKED", run.get("detail") or "缺前置输入"
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
        p = subprocess.run(vc, shell=True, cwd=rroot, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode != 0:
            return "FAILED", "判据命令 rc=%s" % p.returncode
    return "DONE", "判据通过(%s)" % judge


def record(station, card, verdict, why, root=None):
    """写回执 + 回写卡状态。

    2026-11-12（批次1.3 验证独立取证）两处收紧：
      1) 回执必须带 judge 与 judge_source —— 原来不写，导致 master_patrol 的 A3
         （"人判件不许标 DONE"）恒不触发，人判越权正好落在盲区里。
      2) 应为文件产物、却算不出 sha256 的，不许判 DONE，降 UNVERIFIED。
         原来 sha256 可以是 null 而 verdict 仍是 DONE，验收就无法复核。
    """
    rroot = root or ROOT
    deliverable = card.get("deliverable")
    p = os.path.join(rroot, deliverable) if deliverable else ""
    sha = _digest(p) if p and os.path.exists(p) else None
    judge, jsrc = _judge_of(card, root)
    if verdict == "DONE" and deliverable and not sha:
        verdict = "UNVERIFIED"
        why = "产物算不出 sha256（%s）：%s" % (deliverable, why)
    rcpt = {
        "id": card["id"], "station": station, "product_id": card.get("product_id"),
        "stage": card.get("stage"), "task_type": card.get("task_type"),
        "verdict": verdict, "why": why,
        "judge": judge, "judge_source": jsrc,
        "deliverable": deliverable,
        "bytes": _size(p) if p else None,
        "sha256": sha,
        "ts": _now().isoformat(timespec="seconds"),
        "by": "self-drive",
    }
    ss.append_receipt(station, rcpt, root)
    card = dict(card)
    # 产物签名（size:mtime）随卡落库。下一轮供给靠它判断"上次跑完产物变了没有"，
    # 这是唯一能区分"该重建"和"命令跑了但没产出新东西"的证据。
    _sig = _prodsig(p) if (p and os.path.exists(p)) else None
    extra = {"state": verdict, "finished_at": rcpt["ts"],
             "product_sig": _sig,
             "result": {"why": why, "bytes": rcpt["bytes"]}}
    # 退避重试的账目（批次4.3）：失败/返工要记 attempt 与下次可重试时间，
    # 否则 retry_due() 只能每次立刻重排 = 每轮刷卡。
    if verdict in ("FAILED", "REVISE"):
        att = int(card.get("attempt") or 0) + 1
        extra["attempt"] = att
        extra["next_retry_at"] = (_now() + timedelta(minutes=_backoff_min(att))).isoformat(timespec="seconds")
    elif verdict == "DONE":
        extra.pop("next_retry_at", None)
    card.update(extra)
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
        ss.append_outbox(station, [dict(row, handoff_seq=_now().isoformat(timespec="seconds"))], root)
    return {"to": tgt, "stage": nxt, "task_type": tid, "card": row["id"],
            "via": "outbox"}


RUNNABLE = ("ready", "online", "network_ok_not_registered")


def _lease_minutes(root=None):
    """租约分钟：只从配置读，不写死。支持 int / {"default": n} / {"minutes": n} 三种写法。

    2026-11-12：原实现只认 int，而 CARD-POLICY 里 lease_minutes 是对象，
    isinstance(v,int) 为 False → 静默落到默认 45。"读不到配置"和"配置就是 45"
    看起来一模一样，这种假绿最难查。
    """
    def _num(v):
        if isinstance(v, bool):
            return None
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, dict):
            for k in ("default", "minutes", "value"):
                if isinstance(v.get(k), (int, float)) and not isinstance(v.get(k), bool):
                    return int(v[k])
        return None

    for fn, keys in (("AUTONOMY-CONFIG.json", ("lease_minutes", "lease_minutes_default")),
                     ("CARD-POLICY-v1.json", ("lease_minutes", "lease"))):
        try:
            cfg = _load(fn, root) or {}
        except Exception:
            continue          # 沙箱/缺文件：继续看下一份，最后才落默认
        for k in keys:
            v = _num(cfg.get(k))
            if v:
                return v
    return 45


def _lease_for(card, root=None):
    """按卡的资源类型取租约：cpu=45 / gpu=180 / cloud=60（配置里分三档）。

    出图/出片这类 gpu 卡跑 2-3 小时是常态，用统一的 45 分钟会把它当僵尸回收，
    两个写者同写一个产物目录。
    """
    try:
        cfg = _load("CARD-POLICY-v1.json", root) or {}
        lm = cfg.get("lease_minutes")
        if isinstance(lm, dict):
            k = str(card.get("needs") or "cpu").strip().lower()
            v = lm.get(k) or lm.get("default")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return int(v)
    except Exception:
        pass
    return _lease_minutes(root)


RETRY_MAX = 3          # 同一工序最多自动重试次数，超了转 BLOCKED 并写明缺什么
RETRY_BASE_MIN = 5     # 首次退避 5 分钟，之后 10/20…封顶 6 小时


def _backoff_min(attempt):
    return min(RETRY_BASE_MIN * (2 ** max(0, attempt - 1)), 360)


def retry_due(station, root=None, now=None):
    """把到期的 FAILED/REVISE 卡重排为 OPEN（带 attempt 与退避）。

    2026-11-12（批次4.3）。原来它们是死胡同：plan() 的 open_keys 让 FAILED/REVISE
    永远占着 (product,stage) → 不重建；once() 又只跑 OPEN → 不执行。评审团判"返工"
    （REVISE）的卡直接躺死，越需要重试的工序越会永久停摆。
    规则：attempt < RETRY_MAX 且（无 next_retry_at 或已到期）→ 退回 OPEN；
          达到上限 → 转 BLOCKED 并写清"重试 N 次仍失败"。
    """
    now_dt = now or _now()
    rows = ss.read_queue(station, root)
    n = 0
    for r in rows:
        st = str(r.get("state") or "").upper()
        if st not in ("FAILED", "REVISE"):
            continue
        att = int(r.get("attempt") or 0)
        if att >= RETRY_MAX:
            if st != "BLOCKED":
                row = dict(r)
                row.update({"state": "BLOCKED",
                            "why": "重试 %d 次仍失败，转 BLOCKED 等人看：%s"
                                   % (att, str(r.get("why") or "")[:120])})
                ss.upsert(station, row, root)
                n += 1
            continue
        nxt = str(r.get("next_retry_at") or "")
        if nxt:
            try:
                if now_dt < datetime.fromisoformat(nxt[:19]):
                    continue
            except Exception:
                pass
        row = dict(r)
        row.update({"state": "OPEN", "owner": None, "attempt": att + 1,
                    "next_retry_at": (now_dt + timedelta(minutes=_backoff_min(att + 1)))
                                     .isoformat(timespec="seconds"),
                    "retry_why": "第 %d 次重试（上次：%s）"
                                 % (att + 1, str(r.get("why") or "")[:80])})
        ss.upsert(station, row, root)
        n += 1
    return n


def consume_outbox(station, root=None):
    """把各工位 outbox 里投给本机的卡并入本机队列（本机只写自己的分片）。

    2026-11-12（批次4.4）。跨工位交接原来是"直接写别人的 queue.jsonl"，被一机一写者
    护栏抛 PermissionError 穿出 once()：卡已 DONE、回执在、日志没写、守护死亡，
    下游永远拿不到卡。改成一机只写自己的 outbox，目标机自己 SENSE 时拉取入队。
    已消费条目记在 rt/<station>/outbox-seen.json，重复 pull 不会重复入队。
    """
    seen_p = os.path.join(ss.rt_dir(station, root), "outbox-seen.json")
    try:
        with open(seen_p, encoding="utf-8") as f:
            seen = set(json.load(f) or [])
    except Exception:
        seen = set()
    have = {(r.get("product_id"), r.get("stage")) for r in ss.read_queue(station, root)}
    added, marked = [], []
    for src in ss.STATIONS:
        if src == station:
            continue
        for row in ss.read_outbox(src, root):
            if str(row.get("station") or "") != station:
                continue
            key = "%s|%s|%s" % (src, row.get("id"), row.get("handoff_seq") or "")
            if key in seen:
                continue
            if (row.get("product_id"), row.get("stage")) in have:
                marked.append(key)      # 已有同工序卡：不重复投，但记为已处理
                continue
            card = dict(row)
            card.pop("handoff_seq", None)
            card.setdefault("state", "OPEN")
            ss.upsert(station, card, root)
            have.add((card.get("product_id"), card.get("stage")))
            added.append(card.get("id"))
            marked.append(key)
    if marked:
        seen.update(marked)
        try:
            os.makedirs(os.path.dirname(seen_p), exist_ok=True)
            with open(seen_p, "w", encoding="utf-8") as f:
                json.dump(sorted(seen)[-500:], f, ensure_ascii=False)
        except Exception:
            pass
    return {"added": added, "skipped": len(marked) - len(added)}


def reclaim(station, root=None, now=None, lease_min=None):
    """回收卡死的 RUNNING：退回 OPEN 并写 release_reason。

    2026-11-12（批次4.2）覆盖 5 种形态——原实现只认"owner=本机 且 claimed_at 可解析"，
    其余四种永久卡死且无红灯：
      1 owner=本机 + 超租约          -> 回收
      2 owner 为空 + 超租约          -> 回收（migration/人工写入留下的）
      3 claimed_at 缺失/坏           -> 用 ts/created_at/文件 mtime 兜底算龄
      4 owner≠本机 + 超 3 倍租约      -> 回收（宽限，避免误杀正在别的机器上跑的卡）
      5 刚认领未超租约                -> 不动
    """
    now_dt = now or _now()
    lease = lease_min or _lease_minutes(root)
    rows = ss.read_queue(station, root)
    mtime = None
    try:
        import os as _o
        mtime = datetime.fromtimestamp(_o.path.getmtime(ss.queue_path(station, root)))
    except Exception:
        pass
    rec = 0
    for r in rows:
        if str(r.get("state")).upper() != "RUNNING":
            continue
        owner = (r.get("owner") or "").strip()
        ts = str(r.get("claimed_at") or r.get("assign_ts") or r.get("created_at") or r.get("ts") or "")
        age = None
        try:
            age = (now_dt - datetime.fromisoformat(ts[:19])).total_seconds() / 60
        except Exception:
            if mtime:
                age = (now_dt - mtime).total_seconds() / 60
        base = _lease_for(r, root)
        limit = base if (not owner or owner == station) else base * 3
        if age is None or age <= limit:
            continue
        row = dict(r)
        row.update({"state": "OPEN", "owner": None,
                    "release_reason": "认领 %.0f 分钟无回执（租约 %s 分钟，owner=%s），已回收重排"
                                      % (age, limit, owner or "无")})
        ss.upsert(station, row, root)
        rec += 1
    return rec


# ---------------------------------------------------------------- 跨机救援
# 2026-11-12：回收原来只在"本机自驱跑起来"时才发生。传家宝的执行体一停，它分片里
# 那张 11-11 00:26 的 RUNNING 卡就再也没人回收——挂了两天，state 一直 RUNNING，
# 而主控看得见它却什么都不做（这就是"只报红不修"的另一种形态）。
# 判据必须是"执行体是否活着"（心跳），不能是"分片文件多久没动"——后者可能只是没活。
RESCUE_STALE_MIN = 30        # 心跳停 30 分钟 = 驱动 5 分钟一轮的话 6 轮没动
RESCUE_MAX_PER_ROUND = 20


def station_alive(station, root=None, now=None, stale_min=RESCUE_STALE_MIN):
    """返回 (alive, why)。"没有心跳文件"与"心跳很旧"必须能区分。"""
    age = ss.heartbeat_age_min(station, root, now)
    if age is None:
        return False, "无心跳文件（执行体从未注册，或已被删除）"
    if age > stale_min:
        return False, "心跳已停 %.0f 分钟（阈值 %d）" % (age, stale_min)
    return True, "心跳 %.1f 分钟前" % age


def stale_cards(me="control", root=None, now=None, stale_min=RESCUE_STALE_MIN):
    """只读：列出"执行体已停、卡却还挂在 RUNNING"的工位与卡。**不写任何分片。**

    2026-11-12 CEO 校正「本地机器要本地闭环，主控只是赋能算力、给命令、做次要工作」：
    上一版让主控代别家回收卡（跨写 allow_cross），那是把主控做成调度器。正法——回收
    是各机自己 reclaim 的事；主控只负责**看见并说出**：哪台机的执行体停了、哪些卡
    因此挂住。要救也只是下发命令让它自己跑一轮，不替它写。
    """
    now = now or _now()
    out, notes = [], []
    for station in ss.STATIONS:
        if station == me:
            continue
        rows = ss.read_queue(station, root)
        running = [r for r in rows if str(r.get("state")).upper() == "RUNNING"]
        if not running:
            continue
        alive, why = station_alive(station, root, now, stale_min)
        if alive:
            continue
        for r in running:
            ts = str(r.get("claimed_at") or r.get("created_at") or "")
            age = None
            try:
                age = (now - datetime.fromisoformat(ts[:19])).total_seconds() / 60
            except Exception:
                age = None
            limit = _lease_for(r, root) * 3
            if age is not None and age <= limit:
                notes.append("%s/%s 龄期 %.0f 分钟未超宽限 %d，先观察"
                             % (station, r.get("id"), age, limit))
                continue
            out.append({"station": station, "id": r.get("id"), "owner": r.get("owner"),
                        "age_min": None if age is None else round(age),
                        "why": why,
                        "action": "该工位执行体恢复后会自行 reclaim；要提前处理就下发 station_drive --once"})
    return out, "；".join(notes)


PROBE_HINTS = {"blocked_no_comfyui": "comfyui"}


def _comfyui_alive(host=None, timeout=3.0):
    """问服务端，不问档案。返回 (True|None, 一句话)。"""
    host = host or os.environ.get("COMFY_HOST") or "127.0.0.1:8188"
    try:
        with urllib.request.urlopen("http://%s/system_stats" % host, timeout=timeout) as r:
            code = getattr(r, "status", 200)
            body = json.loads(r.read().decode("utf-8", "replace") or "{}")
        if code != 200:
            return None, "system_stats http=%s" % code
        ver = (body.get("system") or {}).get("comfyui_version") or "?"
        return True, "system_stats ok comfyui=%s" % ver
    except Exception as e:  # 连不上就是连不上，不许当成"活着"
        return None, "system_stats unreachable (%s)" % type(e).__name__


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
    if PROBE_HINTS.get(status) == "comfyui":
        alive, why = _comfyui_alive()
        if alive:
            return True, "%s but %s (archive is a snapshot, service is the fact)" % (status, why)
        return False, "%s verified: %s" % (status, why)
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
    # 2026-11-12（批次4.2）：回收必须排在所有闸之前。原来它在 _status_ok/_disk_ok
    # 之后，机器一被暂停/离线/磁盘满就直接 return，卡在 RUNNING 里永远出不来——
    # 恰恰"最需要回收的时候"（机器刚恢复/刚腾出空间）它不跑。
    # 心跳必须在所有闸之前写：被暂停/离线也是"执行体活着"的状态。少写一次，
    # 主控就会把"主动暂停"误判成"执行体死亡"，进而代它回收卡（2026-11-12 新增）。
    if not dry:
        try:
            ss.heartbeat_write(station, root, {"via": "station_drive"})
        except Exception:
            pass
    reclaimed = 0 if dry else reclaim(station, root, now)
    # 僵尸卡只报告不代写（本地闭环：回收归各机自己的 reclaim）。
    stale, stale_note = ([], "") if dry else stale_cards(station, root, now)
    retried = 0 if dry else retry_due(station, root, now)
    consumed = {"added": [], "skipped": 0} if dry else consume_outbox(station, root)
    # outbox 里投给本机但还没入队的条数：目标机离线时卡会滞留，必须可见（不许无声消失）
    try:
        _pend = 0
        for _src in ss.STATIONS:
            if _src == station:
                continue
            _pend += sum(1 for _r in ss.read_outbox(_src, root)
                         if str(_r.get("station") or "") == station)
        consumed["pending_before"] = _pend
    except Exception:
        pass
    ok, why = _status_ok(station, root, force)
    if not ok:
        return {"station": station, "ts": _now().isoformat(timespec="seconds"),
                "blocked": why, "reclaimed": reclaimed, "retried": retried, "consumed": consumed,
                "stale_cards": stale, "stale_note": stale_note,
                "would_create": [], "unknown_output": [], "ran": []}
    # 合并（2026-11-12）：远端把状态与磁盘两个闸拆开并各带说明（status_note/disk_why），
    # 本地把回收提前到闸之前。两者都要：先回收，再各自判闸，且都报告 reclaimed。
    disk_ok, disk_why = _disk_ok(station, root)
    if not disk_ok:
        return {"station": station, "ts": _now().isoformat(timespec="seconds"),
                "status_note": why, "blocked": disk_why,
                "reclaimed": reclaimed, "retried": retried, "consumed": consumed,
                "stale_cards": stale, "stale_note": stale_note,
                "would_create": [], "unknown_output": [], "ran": []}
    want, unknown = plan(station, root, now)
    report = {"station": station, "ts": _now().isoformat(timespec="seconds"),
              "status_note": why, "reclaimed": reclaimed,
              "stale_cards": stale, "stale_note": stale_note,
              "retried": retried, "consumed": consumed,
              "would_create": [w["product"] + "/" + w["stage"] for w in want],
              # 2026-11-12 bm-c 现场切换：plan() 一直算出了每道工序"为什么没活"
              # （NO-CONTRACT / TOOL-PENDING / NO-OWNER / AUTHORITY），但这里只印
              # product/stage —— 读报告的人看到的是一排"无产物"，不知道哪条在等
              # 命令、哪条是 CEO 权限件、哪条根本没声明产物。原因必须跟着名字走。
              "unknown_output": ["%s/%s [%s]" % (u["product"], u["stage"], u["why"])
                                 for u in unknown],
              "unknown_detail": unknown,
              "ran": [], "handoff": []}
    if dry:
        return report
    for item in want:
        card = make_card(station, item, now=now)
        ss.upsert(station, card, root)
        # 计划项与实际建卡分开记：混在一个字段会让人以为建了两张（2026-11-12 实测）
        report.setdefault("created", []).append(card["id"])
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
        _cid = card.get("id")
        _claimed = claim(station, card, root)
        if _claimed is None:
            # 抢不到（已被别的进程领走）：跳过，不重复执行
            report.setdefault("skipped_claimed", []).append(_cid)
            continue
        card = _claimed
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
        json.dump(tax, open(os.path.join(base, "TAXONOMY-v1.json"), "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(prods, open(os.path.join(base, "PRODUCTS.json"), "w", encoding="utf-8"), ensure_ascii=False)

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
        open(f, "w", encoding="utf-8").write('{"a":1}\n')
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

        # 回执必须能独立复核：带 judge、DONE 必须带 sha256（批次1.3）
        chk("回执 judge 解析：taxonomy 人判优先于卡级",
            _judge_of({"task_type": "T-OPS-CEO", "judge": "path"}) == ("human", "taxonomy"))
        chk("回执 judge 解析：卡级判据",
            _judge_of({"judge": "path"}) == ("path", "card"))
        # 命令授权闸：白名单放行、未授权拒绝、危险拼接拒绝、已审普通放行
        _p = _load("PRODUCTS.json")["products"]
        _sample = ""
        for _pr in _p:
            for _c in (_pr.get("commands") or {}).values():
                if _c:
                    _sample = _c
                    break
            if _sample:
                break
        chk("命令闸：PRODUCTS 已审命令放行", _cmd_guard(_sample, {})[0] is True)
        chk("命令闸：未授权命令拒绝", _cmd_guard("rm -rf /tmp/x", {})[0] is False)
        chk("命令闸：已审但含高危模式 -> 放行并标记（黑名单不硬拒合法产物命令）",
            _cmd_guard("mkdir -p a && echo x > a/f", {"cmd_reviewed": True})[0] is True)
        chk("命令闸：已审普通命令放行",
            _cmd_guard("python3 some_tool.py --flag", {"cmd_reviewed": True})[0] is True)
        _rc2 = record("control", {"id": "RC-H", "judge": "path",
                                  "deliverable": "out/none/missing.bin"}, "DONE", "声称完成", td)
        chk("负控：DONE 但产物算不出哈希 -> 降 UNVERIFIED", _rc2["verdict"] == "UNVERIFIED")

        # 人判护栏：大小写与卡级降级都是过去能绕过的真洞
        for j in ("manual", "MANUAL", "Manual", "human", "HUMAN"):
            chk("judge=%s -> PENDING_HUMAN（大小写不许绕过）" % j,
                verify("control", {"judge": j}, {"ok": True, "rc": 0}, td)[0] == "PENDING_HUMAN")
        # 负控：taxonomy 判人判的工序（T-OPS-CEO），卡上写 path 也不能降级成机器判。
        # 用真实 root 读 taxonomy（verify 只读不写）；空沙箱里读不到类型表会误判通过。
        chk("卡级 judge 不许把 taxonomy 人判件降级",
            verify("control", {"judge": "path", "task_type": "T-OPS-CEO"},
                   {"ok": True, "rc": 0})[0] == "PENDING_HUMAN")

    # 身份识别：唯一权威是 fleet_identity（身份文件 > hostname > FLEET_STATION）。
    # 2026-11-12 改：原来用 FLEET_STATION 模拟，但它现在是最弱证据、会被 hostname 覆盖。
    # 双证冲突（文件说 visual、hostname 匹配 control）必须拒绝——那是部署错误。
    # 测试机本来就不是 visual，所以 mock hostname（不给生产开"忽略校验"的后门）。
    import tempfile as _tf
    import fleet_identity as fid
    _idt = _tf.mkdtemp(prefix="ident-")
    _idf = os.path.join(_idt, "station")
    _old = os.environ.get("FLUX_IDENTITY")
    _orig_host = fid._from_hostname
    try:
        with open(_idf, "w", encoding="utf-8") as f:
            f.write("visual\n")
        os.environ["FLUX_IDENTITY"] = _idf
        fid._from_hostname = lambda root=None: (None, "testhost")   # 无 hostname 证据
        chk("身份文件=visual -> 识别为 visual", detect_station() == "visual")
        with open(_idf, "w", encoding="utf-8") as f:
            f.write("not-a-station\n")
        chk("乱填工位 -> 识别失败（拒绝运行而不是默认主控）", detect_station() is None)
        # 负控：文件与 hostname 矛盾时必须拒绝（部署错了要拦，不许二选一）
        with open(_idf, "w", encoding="utf-8") as f:
            f.write("visual\n")
        fid._from_hostname = lambda root=None: ("control", "testhost")
        chk("负控：文件与 hostname 矛盾 -> 拒绝运行", detect_station() is None)
    finally:
        fid._from_hostname = _orig_host
        if _old is None:
            os.environ.pop("FLUX_IDENTITY", None)
        else:
            os.environ["FLUX_IDENTITY"] = _old
        shutil.rmtree(_idt, ignore_errors=True)

    # 档案写"没 ComfyUI"时，服务端答话就该放行（2026-11-12 实锚）。自带目录：
    # 借上面那个 with 的 td 会拿到已删除的路径，腿跑不起来和腿通过长得一样。
    _ptd = tempfile.mkdtemp()
    try:
        _pbase = os.path.join(_ptd, "cph4", "fleet")
        os.makedirs(_pbase)
        json.dump({"stations": [{"id": "visual", "status": "blocked_no_comfyui"},
                                {"id": "readyone", "status": "ready"}]},
                  open(os.path.join(_pbase, "STATIONS.json"), "w", encoding="utf-8"),
                  ensure_ascii=False)
        _orig_probe = globals()["_comfyui_alive"]
        try:
            globals()["_comfyui_alive"] = lambda *a, **k: (True, "system_stats ok comfyui=test")
            g_ok, g_why = _status_ok("visual", _ptd)
            chk("档案 blocked_no_comfyui + 服务端答话 -> 放行", g_ok is True and "ok" in g_why)

            globals()["_comfyui_alive"] = lambda *a, **k: (None, "system_stats unreachable (URLError)")
            g_ok2, g_why2 = _status_ok("visual", _ptd)
            chk("档案 blocked_no_comfyui + 服务端不应 -> 仍拒且点名原因",
                g_ok2 is False and "unreachable" in g_why2)

            calls = []

            def _spy(*a, **k):
                calls.append(1)
                return (True, "should not be asked")

            globals()["_comfyui_alive"] = _spy
            r_ok, r_why = _status_ok("readyone", _ptd)
            chk("档案 ready -> 放行且不去问服务端", r_ok is True and not calls and r_why == "ready")
        finally:
            globals()["_comfyui_alive"] = _orig_probe
    finally:
        shutil.rmtree(_ptd, ignore_errors=True)

    print("[station_drive] %d/%d" % (ok, total))
    return 0 if ok == total else 2


def detect_station():
    """本机是哪个工位：委托唯一权威 fleet_identity（身份文件 > hostname > FLEET_STATION）。

    2026-11-11 实锚：原来 --station 默认写死 control——真机上忘了带参数就会
    以主控身份跑（读主控分片、认主控的活），属于最危险的静默错。
    2026-11-12：三份身份实现合并到 fleet_identity；身份冲突时它抛错，
    这里转 None，让 main() 走"拒绝运行 rc=2"（不猜、不降级）。
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import fleet_identity as fid
        st = fid.station_or_none()
        return st if st in ss.STATIONS else None
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", choices=list(ss.STATIONS), default=None,
                    help="不传则按 FLEET_STATION/hostname 自动识别；识别不出会拒绝运行")
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
    station = a.station or detect_station()
    if not station:
        print(json.dumps({"error": "无法判定本机工位：设 FLEET_STATION=<station> 或传 --station；"
                                   "拒绝以默认身份运行（防误以主控身份干活）",
                          "allowed": list(ss.STATIONS)}, ensure_ascii=False, indent=1))
        return 2
    _lockfh = None
    if not a.dry:
        _lockfh = _singleton_acquire(station)
        if _lockfh is None:
            print(json.dumps({"error": "本工位已有自驱实例在跑（单例锁被占用）",
                              "station": station,
                              "hint": "先确认另一个进程是否卡死；确属僵死可删 /tmp/fluxgroup-station-<id>.lock"},
                             ensure_ascii=False, indent=1))
            return 3
    if a.loop:
        while True:
            r = once(station, a.root, dry=a.dry, run_limit=a.run_limit, force=a.force)
            print(json.dumps(r, ensure_ascii=False))
            time.sleep(a.loop)
    r = once(station, a.root, dry=a.dry, run_limit=a.run_limit, force=a.force)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
