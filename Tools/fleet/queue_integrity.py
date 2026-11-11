#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""queue_integrity.py - 主控事实面的完整性闸：队列/积压/台账不许带着冲突标记或坏行运行。

为什么（2026-11-04 实测抓到的真事故）：
  cph4/fleet/PRODUCTION-QUEUE.jsonl 与 PRODUCTION-BACKLOG.jsonl 曾有 12 + 4 行
  git 冲突标记（<<<<<<< HEAD / ======= / >>>>>>>）被**提交进 git**。所有解析器
  （next_actions / master_agent / lane_agent / ops_metrics）都是逐行 json.loads 后
  try/except 跳过坏行，于是主控少看 21 行卡片却一切"正常"：供给看起来不足、
  判定线看起来迟到、卡片账对不上，没有一处会报错。假绿里最贵的一种是**看不见**。

  更阴的是：脉冲下一轮 write_jsonl 会把坏行直接写没（文件变干净、行数变少），
  事故痕迹也随之消失——所以只查工作区不够，必须同时查 git 里的存量 blob。

它查五件（都是可判定的，不猜）：
  C1 冲突标记（工作区）        critical
  C2 坏行：非空行 json.loads 失败  critical
  C3 冲突标记（git HEAD blob）   critical —— 已提交的脏账本会随 git 分发到其它机器
  C4 重复 id（merge_jsonl 会 collapsing，重复行可能遮蔽后写）  warn
  C5 缺 state / 非法 state 词    warn

用法：
  python3 Tools/fleet/queue_integrity.py                # 一屏 + 落 state/queue-integrity.json
  python3 Tools/fleet/queue_integrity.py --json         # 只输出 JSON
  python3 Tools/fleet/queue_integrity.py --no-git       # 跳过 C3（无 git 环境时）
Exit: 0 全绿；2 有 critical（坏账本必须当轮处理，不许继续跑派单）
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(FLEET, "state", "queue-integrity.json")

MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
# 队列/积压/判定/回执台账：这些文件被逐行解析，坏一行就少一张卡
# 2026-11-11 修正：原为裸文件名（在仓库根下不存在），而 main() 传进来的是
# "cph4/fleet/..." 相对路径，于是 check_state 恒为 False——STATE 词表校验
# 从未在生产队列上生效。改为仓库相对路径，与 glob 出来的 rel 一致。
KEY_FILES = ("cph4/fleet/PRODUCTION-QUEUE.jsonl", "cph4/fleet/PRODUCTION-BACKLOG.jsonl",
             "cph4/fleet/dispatcher/JUDGMENT-QUEUE.jsonl",
             "cph4/fleet/dispatcher/DISPATCH-REQUESTS.jsonl")
STATES = {"OPEN", "READY", "RUNNING", "CLAIMED", "DONE", "FAILED", "CANCELLED",
          "PROMOTED", "ARCHIVED", "UNVERIFIED", "BLOCKED", "PENDING"}
MAX_BYTES = 8 * 1024 * 1024


def scan_file(path, rel):
    if rel.lower().endswith(".json"):
        # 单对象 JSON（MASTER-STATE/PULSE/STAGE-CACHE 等）不是 jsonl：只查冲突标记，
        # 不做逐行解析（否则每个漂亮的 JSON 都会被当成坏行）。
        try:
            text = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except FileNotFoundError:
            return {"file": rel, "missing": True}
        hits = [i for i, l in enumerate(text, 1) if l.strip().startswith(MARKERS)]
        return {"file": rel, "kind": "json", "rows": len(text), "conflict_marker_lines": hits}
    # state 词表只对"卡片队列"成立：LANE-REGISTRY / events / 各种台账各有自己的词，
    # 拿卡片词表去拦它们只会制造噪声（实测 5 个文件误报 40+ 行），闸一吵就没人看。
    check_state = rel in KEY_FILES
    bad_marker, bad_json, dup_ids, bad_state, no_state = [], [], [], [], []
    n = 0
    seen = {}
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return {"file": rel, "skipped": "too-large"}
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                s = line.strip()
                if not s:
                    continue
                if s.startswith(MARKERS):
                    bad_marker.append(i)
                    continue
                n += 1
                try:
                    r = json.loads(s)
                except Exception:
                    bad_json.append(i)
                    continue
                if not isinstance(r, dict):
                    bad_json.append(i)
                    continue
                k = r.get("id") or r.get("key")
                if k is not None:
                    seen[k] = seen.get(k, 0) + 1
                st = r.get("state")
                if not check_state:
                    continue
                if st is None:
                    no_state.append(i)
                elif str(st).upper() not in STATES:
                    bad_state.append({"line": i, "state": st})
    except FileNotFoundError:
        return {"file": rel, "missing": True}
    dup_ids = sorted(k for k, c in seen.items() if c > 1)
    return {"file": rel, "rows": n, "conflict_marker_lines": bad_marker,
            "bad_json_lines": bad_json, "dup_ids": dup_ids[:20],
            "dup_id_count": len(dup_ids), "missing_state_lines": no_state[:10],
            "unknown_state": bad_state[:10]}


def git_blob_markers(rel):
    """已提交版本里的冲突标记——工作区干净也拦不住它随 git 分发出去。"""
    try:
        out = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=ROOT,
                             capture_output=True, text=True, timeout=30)
    except Exception as e:
        return {"file": rel, "git": "ERROR:%s" % e}
    if out.returncode != 0:
        return {"file": rel, "git": "NOT-IN-HEAD"}
    lines = out.stdout.splitlines()
    hits = [i for i, l in enumerate(lines, 1) if l.strip().startswith(MARKERS)]
    return {"file": rel, "git_marker_lines": hits, "git_rows": len(lines)}


def _cap_infra():
    """机制卡每机不许超上限（CEO 2026-11-05 产能配额）。

    实测：bm-m 上堆了 5 张 fleet-ops 卡（上限 2），业务线却缺卡。
    保留优先级：RUNNING > 新创建；超出的归档，并写明原因。
    """
    try:
        cfg = json.load(open(os.path.join(FLEET, "AUTONOMY-CONFIG.json"), encoding="utf-8"))
    except Exception:
        return 0
    cap = cfg.get("capacity") or {}
    infra = set(cap.get("infra_lines") or ["fleet-ops"])
    limit = int(cap.get("infra_max_cards_per_node") or 2)
    if not infra:
        return 0
    touched = []
    for name in ("PRODUCTION-QUEUE.jsonl", "PRODUCTION-BACKLOG.jsonl"):
        pth = os.path.join(FLEET, name)
        try:
            rows = [json.loads(l) for l in open(pth, encoding="utf-8") if l.strip()]
        except Exception:
            continue
        per = {}
        for r in rows:
            if r.get("state") not in ("OPEN", "RUNNING"):
                continue
            if (r.get("line") or "") not in infra:
                continue
            for n in (r.get("nodes") or ["?"]):
                per.setdefault(n, []).append(r)
        for node, lst in per.items():
            if len(lst) <= limit:
                continue
            # 先保 RUNNING，其余按创建时间新→旧保留
            lst.sort(key=lambda r: (r.get("state") != "RUNNING",
                                    str(r.get("created_at") or "")))
            for r in lst[limit:]:
                if r.get("state") == "RUNNING":
                    continue
                r["state"] = "ARCHIVED"
                r["note"] = "infra-cap: 机制卡每机上限 %d，本机超额归档" % limit
                r["closed_at"] = datetime.now().isoformat(timespec="seconds")
                touched.append((name, r))
    if touched:
        try:
            import fleet_lane as fl
            by = {}
            for name, r in touched:
                by.setdefault(name, []).append(r)
            for name, rs in by.items():
                fl.merge_jsonl(os.path.join(FLEET, name), rs)
        except Exception:
            pass
    return len(touched)


def _reconcile():
    """QUEUE 是状态权威，BACKLOG 只保存声明（2026-11-05：同 id 状态冲突实测 118 处，
    导致做过的重做、停掉的复活）。冲突时把 QUEUE 的状态写回 BACKLOG。"""
    qp = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
    bp = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")

    def load(p):
        out = []
        try:
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
        except FileNotFoundError:
            pass
        return out

    q, b = load(qp), load(bp)
    qm = {r.get("id"): r for r in q if r.get("id")}
    fix = []
    for r in b:
        qr = qm.get(r.get("id"))
        if not qr or r.get("state") == qr.get("state"):
            continue
        r["state"] = qr.get("state")
        for k in ("note", "closed_at", "error_class", "retries", "owner"):
            if k in qr:
                r[k] = qr[k]
        fix.append(r)
    if fix:
        try:
            import fleet_lane as fl
            fl.merge_jsonl(bp, fix)
        except Exception:
            with open(bp, "w", encoding="utf-8") as f:
                for r in b:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(fix)


def _purge_meta():
    """自检/分诊/盘点卡不是产物，不许占生产车道。

    2026-11-05 实测：清掉 36 张后，night_plan/backlog_fill/canary/bank_autofill 四个
    生成点下一轮又把它们造回来。与其逐个改生成器，不如在唯一的读口做一轮清洗——
    生成端没拦住，读口必须兜住。
    """
    import re as _re
    try:
        cfg = json.load(open(os.path.join(FLEET, "AUTONOMY-CONFIG.json"), encoding="utf-8"))
    except Exception:
        cfg = {}
    pre = [str(p).upper() for p in
           ((cfg.get("supply") or {}).get("meta_card_prefixes") or [])]
    if not pre:
        return 0

    def is_meta(cid):
        u = str(cid or "").upper()
        return any(u.startswith(p) for p in pre)

    touched = []
    for name in ("PRODUCTION-QUEUE.jsonl", "PRODUCTION-BACKLOG.jsonl"):
        p = os.path.join(FLEET, name)
        try:
            lines = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        except Exception:
            continue
        for r in lines:
            if r.get("state") in ("OPEN", "READY", "PROMOTED", "RUNNING") and is_meta(r.get("id")):
                r["state"] = "ARCHIVED"
                r["note"] = "meta-card purged: 自检/分诊只在主控脉跑，不占生产车道"
                r["closed_at"] = datetime.now().isoformat(timespec="seconds")
                touched.append((name, r))
    if touched:
        try:
            import fleet_lane as fl
            by = {}
            for name, r in touched:
                by.setdefault(name, []).append(r)
            for name, rows in by.items():
                fl.merge_jsonl(os.path.join(FLEET, name), rows)
        except Exception:
            pass
    return len(touched)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--cap-infra", action="store_true",
                    help="机制卡每机超额部分归档（产能配额）")
    ap.add_argument("--purge-meta", action="store_true",
                    help="把自检/分诊/盘点卡从活跃队列里归档（它们只该在主控脉跑）")
    ap.add_argument("--reconcile", action="store_true",
                    help="以 PRODUCTION-QUEUE 为准回写 PRODUCTION-BACKLOG 的状态")
    a = ap.parse_args(argv)
    if a.cap_infra:
        n = _cap_infra()
        if n:
            print("[queue-integrity] infra-cap: archived %d card(s)" % n)
    if a.purge_meta:
        n = _purge_meta()
        if n:
            print("[queue-integrity] purged %d meta card(s) from the production lane" % n)
    if a.reconcile:
        n = _reconcile()
        if n:
            print("[queue-integrity] reconciled %d row(s) from QUEUE" % n)

    files = list(KEY_FILES)
    # 其余队列类台账也扫（回执/事件/账本），但只在 fleet 一层与 dispatcher 一层，避免扫进大归档
    for p in sorted(glob.glob(os.path.join(FLEET, "*.jsonl")) +
                    glob.glob(os.path.join(FLEET, "dispatcher", "*.jsonl")) +
                    glob.glob(os.path.join(FLEET, "dispatcher", "*.json"))):
        rel = os.path.relpath(p, ROOT)
        if rel not in files:
            files.append(rel)

    report, critical = [], 0
    for rel in files:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        r = scan_file(path, rel)
        if not a.no_git and r.get("rows"):
            g = git_blob_markers(rel)
            if g.get("git_marker_lines"):
                r["git_conflict_marker_lines"] = g["git_marker_lines"]
        if r.get("conflict_marker_lines") or r.get("bad_json_lines") \
                or r.get("git_conflict_marker_lines"):
            critical += 1
        report.append(r)

    state = {"ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
             "critical_files": critical, "files": report}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(state, ensure_ascii=False))
        return 2 if critical else 0

    print("[queue-integrity] files=%d critical=%d" % (len(report), critical))
    for r in report:
        if r.get("missing") or r.get("skipped"):
            continue
        flags = []
        if r.get("conflict_marker_lines"):
            flags.append("CONFLICT(marker@%d)" % len(r["conflict_marker_lines"]))
        if r.get("git_conflict_marker_lines"):
            flags.append("CONFLICT-IN-GIT(@%d)" % len(r["git_conflict_marker_lines"]))
        if r.get("bad_json_lines"):
            flags.append("BAD-JSON(%d)" % len(r["bad_json_lines"]))
        if r.get("dup_id_count"):
            flags.append("DUP-ID(%d)" % r["dup_id_count"])
        if r.get("unknown_state"):
            flags.append("BAD-STATE(%d)" % len(r["unknown_state"]))
        if r.get("missing_state_lines"):
            flags.append("NO-STATE(%d)" % len(r["missing_state_lines"]))
        if flags:
            print("  %-52s rows=%-5s %s" % (r["file"], r.get("rows"), " ".join(flags)))
    if critical:
        print("[queue-integrity] VERDICT=RED 坏账本会让主控静默少看卡，先修文件再派单")
    else:
        print("[queue-integrity] VERDICT=GREEN 逐行可解析、无冲突标记、无提交态脏账本")
    return 2 if critical else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))