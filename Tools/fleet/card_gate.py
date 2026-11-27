#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_gate.py - 卡面体检闸：一张卡在"投出去"和"领下来"之前先验能不能跑。

Why this exists (2026-11-03):
  20xx-11-03 当天的队列里有 16 张 FAILED，其中 bm-b 名下 4 张在 4 秒内"失败"——
  它们其实一秒活都没干：卡片 cmd 指向 `media/drama-tts-batch`（这个目录根本不存在），
  而执行器所在的控制面克隆是稀疏的（只有 /AI.md），`Tools/fleet/tts_batch_check.py`
  在那边也不存在。执行器把"卡片写错了"报成"任务失败"，主控看到的是
  "bm-b 一直失败"，于是把 bm-b 降级、把活全自己扛——偏科不是因为机器不动，是因为
  卡片从生成那一刻就不可执行，而没有任何一道闸拦它。

  本闸只做一件事：把"可执行性"从**执行时的隐式假设**变成**卡面显式契约**。
  出卡端（workgen/planner/backlog_fill/主控派单）与领卡端（lane_agent）都可以调用，
  判据只有三条：
    1) cwd 必须在本机存在（或可回落到本机某个 work root）
    2) cmd 里的脚本路径必须在本机解析得到
    3) 输入目录参数（--dir/--in/--src 等）必须存在；--out/--deliverable 允许不存在
  不合格的卡不许执行，也不许记成 JOB-FAILED——它是 CARD-DEFECT，要回给发卡方改。

用法：
  python Tools/fleet/card_gate.py --queue cph4/fleet/PRODUCTION-QUEUE.jsonl --node bm-b
  python Tools/fleet/card_gate.py --queue ... --node bm-b --json --only OPEN,RUNNING
  python Tools/fleet/card_gate.py --card '{"id":"X","cmd":"python Tools/x.py --dir media/a"}'
  python Tools/fleet/card_gate.py --queue ... --node bm-b --roots "C:\\Fluxgroup\\FluxGroup"

退出码：0=全部可执行；1=存在缺陷（--json 时缺陷明细在 stdout）。
"""
import argparse
import json
import os
import re
import sys

# --- 什么算"脚本路径"：以这些后缀结尾的相对 token ---
SCRIPT_EXT = (".py", ".ps1", ".psm1", ".sh", ".bat", ".cmd", ".exe", ".js", ".mjs")
# --- 输入型参数：后面的值必须是已存在的目录/文件 ---
IN_FLAGS = {"--dir", "--dirs", "--in", "--input", "--src", "--source", "--from", "-d"}
# --- 输出型参数：允许不存在 ---
OUT_FLAGS = {"--out", "--output", "--dst", "--dest", "--to", "--report", "-o"}

_TOKEN_RE = re.compile(r"[^\s\"']+")


def _norm(p):
    return p.replace("\\", "/").rstrip("/")


def _abs(cwd, p):
    p = p.replace("\\", os.sep).replace("/", os.sep)
    return os.path.normpath(p if os.path.isabs(p) else os.path.join(cwd, p))


def _under(root, abspath):
    try:
        r = os.path.normcase(os.path.abspath(root))
        a = os.path.normcase(os.path.abspath(abspath))
        return os.path.commonpath([r, a]) == r
    except Exception:
        return False


def _tokens(cmd):
    return [t.strip("\"'`") for t in _TOKEN_RE.findall(cmd or "")]


def check(card, roots, node=None):
    """返回 dict：ok / issues[list] / cwd / resolved。

    roots: 本机可用的工作根（第一个通常是控制面克隆，其次可带主工作树）。
    判定只读文件系统，不改任何东西。
    """
    roots = [r for r in (roots or []) if r]
    issues = []
    cmd = card.get("cmd") or ""
    raw_cwd = card.get("cwd") or ""
    deliverable = card.get("deliverable") or ""

    # ---- 0) 跨平台可执行性（2026-11-11 实锚）----
    # 我把 `timeout 60 find ... | wc -l` 派给 Windows 的 bm-a：cmd 里的 timeout 是"等待按键"，
    # 那张卡一直挂着等键盘，18 分钟不返回，看起来像车道坏了。GNU 工具在 Windows 上不是缺失
    # 就是同名异义，出卡端必须拦，不能等到执行端挂死再排查。
    WIN_NODES = ("bm-a", "bm-b", "bm-c", "bm-d")
    GNU_ONLY = ("timeout", "find", "grep", "sed", "awk", "head", "tail", "wc", "xargs",
                "basename", "dirname", "chmod", "chown", "tee", "tr", "sort", "uniq")
    if node in WIN_NODES and cmd:
        import re as _re
        segs = _re.split(r"&&|\|\||;|\||&", cmd)
        for seg in segs:
            seg = seg.strip().lstrip("(").strip()
            tok = (seg.split() or [""])[0].strip('"\'')
            if tok in GNU_ONLY:
                issues.append({"code": "WIN-TOOL", "fatal": True,
                               "detail": ("Windows 节点 %s 上不能用 GNU 工具 `%s`（cmd 里同名命令行为不同，"
                                          "会挂住）；改用 python -c 或 PowerShell 等价写法" % (node, tok))})
                break

    # ---- 1) cwd 解析 ----
    cwd = None
    if raw_cwd:
        cand = raw_cwd if os.path.isabs(raw_cwd) else os.path.join(roots[0] if roots else os.getcwd(), raw_cwd)
        if os.path.isdir(cand):
            cwd = os.path.normpath(cand)
        else:
            issues.append({"code": "CWD-MISSING", "fatal": True,
                           "detail": "卡片 cwd 在本机不存在：%s" % raw_cwd})
    if cwd is None:
        for r in roots:
            if r and os.path.isdir(r):
                cwd = os.path.normpath(r)
                break
    if cwd is None:
        issues.append({"code": "NO-WORK-ROOT", "fatal": True, "detail": "本机没有可用工作根"})
        return {"ok": False, "issues": issues, "cwd": None, "node": node}

    # ---- 2) 脚本 / 输入路径 ----
    search = [cwd] + [r for r in roots if r and os.path.normpath(r) != cwd]
    toks = _tokens(cmd)
    for i, t in enumerate(toks):
        low = t.lower()
        last = toks[i - 1] if i else ""

        # 输入型参数：值必须存在（相对值依次在 cwd / 各 root 下找）
        if last in IN_FLAGS:
            if t.startswith("-") or not t:
                continue
            hit = t if os.path.isabs(t) else None      # 绝对路径：存在即视为命中
            if os.path.isabs(t):
                if not os.path.exists(t):
                    hit = None
                    issues.append({"code": "INPUT-MISSING", "fatal": True,
                                   "detail": "%s 指向的路径不存在：%s" % (last, t)})
            else:
                hit = None
                for base in search:
                    if os.path.exists(os.path.join(base, t)):
                        hit = os.path.join(base, t)
                        break
                if hit is None:
                    issues.append({"code": "INPUT-MISSING", "fatal": True,
                                   "detail": "%s 指向的相对路径在本机各工作根下都不存在：%s" % (last, t)})
            # 2026-11-11 实锚：目录存在但是空的，闸放行、工具 rc=3、卡记 FAILED，
            # 一晚反复重派同一张（media/asset/faces 空目录 → asset_caption 必失败）。
            # 输入为空 = 这张卡在本机没有可处理对象，属于卡面缺陷，不该拿去执行端试。
            if hit and os.path.isdir(hit):
                try:
                    if not os.listdir(hit):
                        issues.append({"code": "INPUT-EMPTY", "fatal": True,
                                       "detail": "%s 指向的目录是空的（没有可处理输入）：%s" % (last, t)})
                except Exception:
                    pass
            continue

        if last in OUT_FLAGS:
            continue

        # 脚本/可执行：相对路径必须能被解析
        if low.endswith(SCRIPT_EXT) and not t.startswith("-"):
            if os.path.isabs(t):
                if not os.path.exists(t):
                    issues.append({"code": "SCRIPT-MISSING", "fatal": True,
                                   "detail": "脚本不存在：%s" % t})
            else:
                if not any(os.path.exists(os.path.join(base, t)) for base in search):
                    issues.append({"code": "SCRIPT-MISSING", "fatal": True,
                                   "detail": "脚本在本机各工作根下都不存在：%s（搜索根：%s）"
                                             % (t, ", ".join(search))})

    # ---- 3) 交付物必须落在本机某工作根内，否则主控永远收不到 ----
    if deliverable:
        if os.path.isabs(deliverable):
            if not any(_under(r, deliverable) for r in search):
                issues.append({"code": "DELIVERABLE-FOREIGN", "fatal": False,
                               "detail": "交付物写在所有工作根之外，回执无法上链：%s" % deliverable})
        else:
            if not any(_under(r, os.path.join(r, deliverable)) for r in search):
                issues.append({"code": "DELIVERABLE-UNROOTED", "fatal": False,
                               "detail": "交付物不是相对某工作根的路径：%s" % deliverable})

    if not cmd:
        issues.append({"code": "NO-CMD", "fatal": True, "detail": "卡片没有 cmd"})

    fatal = any(i["fatal"] for i in issues)
    return {"ok": not fatal, "issues": issues, "cwd": cwd, "node": node}


def default_roots(root):
    """本机工作根：控制面克隆优先，其次同级的全量工作树（有就带上）。"""
    roots = [root]
    guess = r"C:\Fluxgroup\FluxGroup"
    if os.path.normcase(os.path.abspath(guess)) != os.path.normcase(os.path.abspath(root)) and os.path.isdir(guess):
        roots.append(guess)
    return roots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", help="队列 jsonl 路径（相对 root）")
    ap.add_argument("--card", help="直接体检一张卡的 JSON 字符串")
    ap.add_argument("--node", default=None, help="只体检 nodes 里含该机的卡")
    ap.add_argument("--root", default=None, help="工作根（默认本文件上两级）")
    ap.add_argument("--roots", default=None, help="额外工作根，逗号分隔")
    ap.add_argument("--only", default="OPEN,RUNNING",
                    help="只看这些状态，逗号分隔；ALL=全部")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = args.root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    roots = default_roots(root)
    if args.roots:
        for p in args.roots.split(","):
            if p.strip():
                roots.append(p.strip())

    cards = []
    if args.card:
        cards = [json.loads(args.card)]
    else:
        if not args.queue:
            ap.error("需要 --queue 或 --card")
        path = args.queue if os.path.isabs(args.queue) else os.path.join(root, args.queue)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    cards.append(json.loads(line))
                except Exception:
                    pass

    only = None if (args.only or "").upper() == "ALL" else {s.strip().upper() for s in args.only.split(",")}
    bad = []
    checked = 0
    for c in cards:
        if only and (c.get("state") or "").upper() not in only:
            continue
        nodes = c.get("nodes") or []
        if args.node and nodes and args.node not in nodes:
            continue
        checked += 1
        r = check(c, roots, args.node)
        if not r["ok"]:
            bad.append({"id": c.get("id"), "state": c.get("state"),
                        "cwd": c.get("cwd"), "cmd": c.get("cmd"),
                        "nodes": nodes, "issues": r["issues"]})

    out = {"checked": checked, "defective": len(bad), "cards": bad, "roots": roots}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("检查 %d 张卡，缺陷 %d 张；工作根 = %s" % (checked, len(bad), ", ".join(roots)))
        for b in bad:
            print("  [%s] %s" % (b["state"], b["id"]))
            for i in b["issues"]:
                print("      %-20s %s" % (i["code"], i["detail"]))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())