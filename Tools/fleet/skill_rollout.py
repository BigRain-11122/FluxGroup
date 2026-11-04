# -*- coding: utf-8 -*-
"""skill_rollout.py - 一台机上的技能对齐（质检 → 安装 → 回执）。

为什么要有它：技能源在 cph4/skills/（随 git 分发），但只有装进本机激活面
（~/.codely-cli/skills/）才会被真正激活——"仓里写得再好，没装=不存在"。
机队每台机都要能自己跑这一步，并且留下**远端可验的回执**（state/ 是 gitignore，
写在那里等于远端永远看不到）。

用法：
  python Tools/fleet/skill_rollout.py --node bm-a
  python Tools/fleet/skill_rollout.py            # 节点名取主机名

退出码：0 完成；2 质检有 fail（装了也不认）；3 前置缺失
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
DST = os.path.expanduser("~/.codely-cli/skills")


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")


def parse_check(out):
    m = re.search(r"skills=(\d+)\s+A=(\d+)\s+B=(\d+)\s+frozen=(\d+)\s+external=(\d+)\s+parked=(\d+)\s+fail=(\d+)", out)
    if not m:
        return None
    k = ("total", "A", "B", "frozen", "external", "parked", "fail")
    return {n: int(v) for n, v in zip(k, m.groups())}


def parse_install(out):
    m = re.search(r"source=(\d+)\s+added=(\d+)\s+updated=(\d+)\s+same=(\d+)\s+skipped=(\d+)", out)
    if not m:
        return {"raw": out.strip()[:400]}
    k = ("source", "added", "updated", "same", "skipped")
    d = {n: int(v) for n, v in zip(k, m.groups())}
    skip = re.search(r"SKIP:\s*(.+)", out)
    d["skipped_names"] = skip.group(1).strip()[:400] if skip else ""
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default=os.environ.get("COMPUTERNAME", "unknown").lower())
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--out", default="", help="回执路径（默认带日期；派单时用固定名便于验交付物）")
    a = ap.parse_args()

    src = os.path.join(ROOT, "cph4", "skills")
    if not os.path.isdir(src):
        print(json.dumps({"verdict": "BLOCKED", "error": "no cph4/skills"}, ensure_ascii=False))
        return 3

    py = sys.executable
    rc1, out1 = run([py, os.path.join(ROOT, "Tools", "fleet", "skill_check.py")])
    check = parse_check(out1)
    if check is None:
        print(json.dumps({"verdict": "BLOCKED", "error": "skill_check output unparsable",
                          "tail": out1[-300:]}, ensure_ascii=False))
        return 3

    inst = {}
    if not a.no_install:
        rc2, out2 = run([py, os.path.join(ROOT, "Tools", "fleet", "skill_install.py")])
        inst = parse_install(out2)
        inst["rc"] = rc2
    else:
        inst = {"skipped": "no-install"}

    body = {
        "card": "SKILL-ROLLOUT-%s-%s" % (a.node, time.strftime("%Y%m%d")),
        "node": a.node,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "skills_source": "cph4/skills",
        "activation_dir": DST,
        "check": check,
        "install": inst,
        "check_rc": rc1,
        "verdict": "BLOCKED" if check["fail"] > 0 else "OK",
        "note": "A=可进无人值守工序；B=只能人点名调用；fail>0 装了也不认",
    }
    os.makedirs(RECEIPTS, exist_ok=True)
    if a.out:
        p = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    else:
        p = os.path.join(RECEIPTS, "skill-rollout-%s-%s.json" % (a.node, time.strftime("%Y%m%d")))
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(body, ensure_ascii=False, indent=1))
    print(json.dumps({k: body[k] for k in ("node", "verdict", "check", "install")},
                     ensure_ascii=False))
    print("receipt -> " + os.path.relpath(p, ROOT))
    return 0 if check["fail"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())