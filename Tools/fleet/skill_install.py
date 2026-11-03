#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把仓内 cph4/skills/ 同步进本机激活面 ~/.codely-cli/skills/。

为什么需要这一步：仓内 45 个技能里，本机只挂了 4 个（2026-11-03 实测），
技能写得再好，没装进激活面就等于不存在。本工具把"装"变成可重复的一步。

规则：
  - 只装 cph4/skills/<name>/ 顶层；ccgs/ 等外部包与 _quarantine/ 不自动装
  - 跳过 status: parked（CEO 令暂停）与 3D 城市族（CEO 2026-09-23 全部 2D 令）
  - **装之前先过 skill_check 闸**：FAIL 的不装（--force 可强装，慎用）
  - 只同步 SKILL.md 与同目录附加文件；不删本机独有技能（除非 --prune）
  - 先比对再写，只报"新增/更新/相同"，不静默覆盖

用法：
  python3 Tools/fleet/skill_install.py            # 安装/更新
  python3 Tools/fleet/skill_install.py --dry-run  # 只看差异
  python3 Tools/fleet/skill_install.py --prune    # 额外删除本机已无仓内来源的技能
  python3 Tools/fleet/skill_install.py --force    # 忽略质检闸（只用于排障）
"""

import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_check  # noqa: E402  同目录质检闸：装之前先过闸

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "cph4", "skills")
DST = os.path.expanduser("~/.codely-cli/skills")
FROZEN_PREFIX = ("city-3d", "lowpoly-city-3d")


def frontmatter(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    fm = {}
    for line in text[3:end if end > 0 else 0].splitlines():
        m = re.match(r"^([a-zA-Z_][\w\-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def main(argv):
    dry = "--dry-run" in argv
    prune = "--prune" in argv
    if not os.path.isdir(SRC):
        print("no source:", SRC)
        return 2
    os.makedirs(DST, exist_ok=True)
    added, updated, same, skipped = [], [], [], []
    want = set()
    for name in sorted(os.listdir(SRC)):
        sp = os.path.join(SRC, name)
        skill = os.path.join(sp, "SKILL.md")
        if not os.path.isfile(skill):
            continue
        fm = frontmatter(skill)
        status = fm.get("status", "").split("#")[0].strip()
        if status == "parked":
            skipped.append((name, "parked"))
            continue
        if name.startswith(FROZEN_PREFIX):
            skipped.append((name, "3d-frozen"))
            continue
        if "--force" not in argv:
            gate = skill_check.check_one(skill)
            if gate["fails"]:
                skipped.append((name, "gate:" + "+".join(gate["fails"][:2])))
                continue
        want.add(name)
        dp = os.path.join(DST, name)
        if not os.path.isdir(dp):
            added.append(name)
            if not dry:
                shutil.copytree(sp, dp)
            continue
        changed = False
        for f in os.listdir(sp):
            s, d = os.path.join(sp, f), os.path.join(dp, f)
            if os.path.isdir(s):
                continue
            if not os.path.exists(d) or open(s, "rb").read() != open(d, "rb").read():
                changed = True
                if not dry:
                    shutil.copy2(s, d)
        (updated if changed else same).append(name)
    orphans = []
    if prune:
        for name in sorted(os.listdir(DST)):
            if name not in want and os.path.isfile(os.path.join(DST, name, "SKILL.md")):
                orphans.append(name)
                if not dry:
                    shutil.rmtree(os.path.join(DST, name))
    print("source=%d  added=%d updated=%d same=%d skipped=%d%s" % (
        len(want) + len(skipped), len(added), len(updated), len(same), len(skipped),
        ("  pruned=%d" % len(orphans)) if prune else ""))
    for tag, items in (("ADD", added), ("UPD", updated)):
        if items:
            print("  %s: %s" % (tag, ", ".join(items)))
    if skipped:
        print("  SKIP: " + ", ".join("%s(%s)" % (n, r) for n, r in skipped))
    if orphans:
        print("  ORPHAN(local only): " + ", ".join(orphans))
    print("dry-run" if dry else "installed -> " + DST)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))