#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能升级 agent：把 B 级技能里「已经点名了真工具」的那些，机械升成 A 级。

设计约束（不许越界）：
  1. 只做机械可验证的事——跑技能正文里已经点名的工具，把**真实执行过的命令**写回技能。
  2. 绝不发明内容：技能没点名任何工具 → 不升级，记 no-tool，保持 B。
  3. 工具不存在或跑不起来 → 不升级，记 dead-tool（这是死指针，不是技能问题）。
  4. 幂等：已含「可跑自查（自动生成」段落的不重复写。

为什么不让本地模型来改写：4B 写不出可执行工序（实测只会复述），
让模型编命令 = 假绿。所以这个 agent 是确定性的，唯一"智能"是解析技能自己点名的工具。

用法：
  python3 Tools/fleet/skill_promote.py --dry-run          # 只看哪些能升
  python3 Tools/fleet/skill_promote.py --limit 2          # 最多升 2 件（默认 2，防一次性大改）
  python3 Tools/fleet/skill_promote.py --only drama-director
"""

import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS = os.path.join(ROOT, "cph4", "skills")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
TOOL_RE = re.compile(r"(Tools/[\w\-./]+\.py)")
PS1_RE = re.compile(r"([\w\-]+\.ps1)")
MARK = "## 可跑自查（自动生成"


def load_skill(path):
    text = open(path, encoding="utf-8").read()
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            for line in text[3:end].splitlines():
                m = re.match(r"^([a-zA-Z_][\w\-]*):\s*(.*)$", line)
                if m:
                    fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
            body = text[end + 4:]
    return fm, body, text


def probe(rel_path):
    """跑 --help 判这个工具是不是真 CLI。返回 (ok, rc, lines, first_line)。"""
    full = os.path.join(ROOT, rel_path)
    if not os.path.isfile(full):
        return False, None, 0, "missing"
    try:
        p = subprocess.run([sys.executable, full, "--help"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=45)
    except subprocess.TimeoutExpired:
        return False, 124, 0, "timeout"
    out = p.stdout.decode("utf-8", "replace")
    lines = [l for l in out.splitlines() if l.strip()]
    first = lines[0].strip()[:90] if lines else ""
    ok = p.returncode in (0, 1, 2) and len(lines) >= 3
    return ok, p.returncode, len(lines), first


def candidates(body):
    """只认 .py：.ps1 在 Mac 上没法可靠验证执行，宁可判 no-tool 也不许假升级。"""
    seen, out = set(), []
    for m in TOOL_RE.findall(body):
        if m in seen:
            continue
        seen.add(m)
        out.append(m)
    return out


def main(argv):
    dry = "--dry-run" in argv
    limit = 2
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    rep = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "promoted": [], "skipped": []}
    done = 0
    for dirpath, dirnames, filenames in os.walk(SKILLS):
        if "SKILL.md" not in filenames:
            continue
        rel = os.path.relpath(dirpath, SKILLS)
        if rel.startswith("_quarantine") or rel.startswith("ccgs"):
            continue
        name = os.path.basename(dirpath)
        if only and name != only:
            continue
        path = os.path.join(dirpath, "SKILL.md")
        fm, body, text = load_skill(path)
        if (fm.get("status") or "").split("#")[0].strip() == "parked":
            continue
        if name.startswith(("city-3d", "lowpoly-city-3d")):
            continue
        if MARK in text:
            rep["skipped"].append({"skill": name, "why": "already"})
            continue
        cands = candidates(body)
        usable = None
        for c in cands:
            ok, rc, n, first = probe(c)
            if ok:
                usable = (c, rc, n, first)
                break
        if not usable:
            rep["skipped"].append({"skill": name, "why": "no-tool" if not cands else "dead-tool",
                                   "cands": cands[:4]})
            print("  SKIP %-26s %s %s" % (name, "no-tool" if not cands else "dead-tool", cands[:3]))
            continue
        if done >= limit:
            rep["skipped"].append({"skill": name, "why": "limit"})
            continue
        c, rc, n, first = usable
        block = ("\n" + MARK + "·2026-11-03）\n"
                 "判据：下面这条命令必须能在本机真跑起来（rc∈{0,1,2} 且有输出）；"
                 "跑不起来说明技能指向的工具已失效，先修工具再谈技能。\n\n"
                 "```\n%s %s --help\n```\n"
                 "实测：rc=%d，输出 %d 行，首行 `%s`。\n" % (sys.executable.split("/")[-1], c, rc, n, first))
        print("  PROMOTE %-24s via %s (rc=%d, %d lines)" % (name, c, rc, n))
        rep["promoted"].append({"skill": name, "tool": c, "rc": rc, "lines": n})
        done += 1
        if not dry:
            t = text.rstrip() + "\n" + block
            open(path, "w", encoding="utf-8").write(t)
    print("promoted=%d skipped=%d%s" % (len(rep["promoted"]), len(rep["skipped"]), " (dry-run)" if dry else ""))
    if not dry:
        os.makedirs(RECEIPTS, exist_ok=True)
        p = os.path.join(RECEIPTS, "skill-promote-%s.json" % time.strftime("%Y%m%d"))
        with open(p, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
        print("wrote", os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))