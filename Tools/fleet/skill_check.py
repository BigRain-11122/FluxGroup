#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能库质量闸：SKILL.md 结构 + 可跑自检命令 + 死指针。

判据（缺一即 FAIL。判据来源：2026-11-03 CEO 令「做好底层搭建与研发」）
  1. frontmatter 有 name 与 description
  2. description 写清"什么时候用"（含 Use when / 触发 / 当…时），>=60 字符
  3. 正文有可跑命令块（含 python / Tools/ / ffprobe / grep / ls）或显式写「无命令」
  4. 正文 >= 1200 字节（低于此多为口号，不是工序）
  5. 引用的仓库路径存在（死指针=技能指向已不存在的文件）
  6. 技能名全局唯一（重名=激活面二选一，永远只能中一个）

用法：
  python3 Tools/fleet/skill_check.py                # 汇总 + 落 state/skills-check.json
  python3 Tools/fleet/skill_check.py --strict       # 有 FAIL 时 rc=2（接线进闸后用）
  python3 Tools/fleet/skill_check.py --only ship-ops
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS_DIR = os.path.join(ROOT, "cph4", "skills")
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "skills-check.json")
QUARANTINE = "_quarantine"

CMD_HINTS = ("python", "python3", "Tools/", "ffprobe", "grep ", "ls ", "pwsh", "/bin/bash")
PATH_RE = re.compile(r"(?<![\w/])((?:Tools|docs|cph4|GimmeAll|gaming|media)/[\w\-./]+?\.(?:py|ps1|sh|md|json|ya?ml))")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    lines = text[3:end].splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^([a-zA-Z_][\w\-]*):\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">", "|", ">-", "|-"):
            buf = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                buf.append(lines[i].strip())
                i += 1
            val = " ".join(x for x in buf if x)
            fm[key] = val
            continue
        fm[key] = val.strip('"').strip("'")
        i += 1
    return fm


def has_checklist(text):
    """非命令行类技能（审美/表演/拆解）的合法自检：标题含自查/判据/检查，且下面至少 3 条编号项。"""
    for m in re.finditer(r"^#+.*(自查|判据|检查|核对|速查|硬律|清单|门槛|checklist|Check).*$", text, re.M | re.I):
        tail = text[m.end():m.end() + 1200]
        n = len(re.findall(r"^\s*(?:\d+[.、)]|[-*]\s)", tail, re.M))
        if n >= 3:
            return True
    return False


def check_one(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    fails = []
    warns = []
    fm = parse_frontmatter(text)
    # 激活身份=frontmatter 的 name（不是目录名）：目录可以另起，重名判定必须按激活名
    name = (fm.get("name") or "").strip() or os.path.basename(os.path.dirname(path))
    if not fm.get("name"):
        fails.append("no-name")
    desc = fm.get("description", "")
    if not desc:
        fails.append("no-description")
    else:
        if len(desc) < 60:
            fails.append("description-too-short(%d)" % len(desc))
        low = desc.lower()
        if not ("use when" in low or "触发" in desc or "当" in desc):
            fails.append("description-no-trigger")
    body = text
    blocks = re.findall(r"```([\s\S]*?)```", text)
    has_cmd = any(any(h in b for h in CMD_HINTS) for b in blocks)
    if not has_cmd and not has_checklist(text) and "无命令" not in text:
        fails.append("no-runnable-check")
    if len(text) < 1200:
        fails.append("thin(%d字)" % len(text))
    dead = []
    for p in set(PATH_RE.findall(text)):
        if any(c in p for c in "{*}<>"):
            continue
        if not os.path.exists(os.path.join(ROOT, p)):
            dead.append(p)
    if dead:
        warns.append("dead-pointer:" + ",".join(sorted(dead)[:3]))
    return {"skill": name, "path": os.path.relpath(path, ROOT), "bytes": len(text),
            "fails": fails, "warns": warns, "desc_len": len(desc)}


def main(argv):
    strict = "--strict" in argv
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        if i + 1 < len(argv):
            only = argv[i + 1]
    rows = []
    for dirpath, dirnames, filenames in os.walk(SKILLS_DIR):
        if "SKILL.md" not in filenames:
            continue
        rel = os.path.relpath(dirpath, SKILLS_DIR)
        if rel.startswith(QUARANTINE):
            continue
        row = check_one(os.path.join(dirpath, "SKILL.md"))
        if only and only not in (row["skill"], os.path.basename(dirpath)):
            continue
        rows.append(row)
    dup = {}
    for r in rows:
        dup[r["skill"]] = dup.get(r["skill"], 0) + 1
    for r in rows:
        if dup[r["skill"]] > 1:
            r["fails"].append("dup-name(%d)" % dup[r["skill"]])
    rows.sort(key=lambda r: (len(r["fails"]), r["skill"]))
    total = len(rows)
    failn = sum(1 for r in rows if r["fails"])
    warnn = sum(1 for r in rows if r["warns"])
    print("skills=%d fail=%d warn=%d pass=%d" % (total, failn, warnn, total - failn))
    for r in rows:
        if r["fails"] or r["warns"]:
            print("  %-28s %5d字  %s%s" % (r["skill"], r["bytes"],
                  ("FAIL:" + "+".join(r["fails"])) if r["fails"] else "ok",
                  ("  WARN:" + "+".join(r["warns"])) if r["warns"] else ""))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"ts": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
                   "total": total, "fail": failn, "warn": warnn, "rows": rows},
                  f, ensure_ascii=False, indent=1)
    print("wrote", os.path.relpath(OUT, ROOT))
    return 2 if (strict and failn) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))