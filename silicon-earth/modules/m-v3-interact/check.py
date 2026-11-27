# -*- coding: utf-8 -*-
"""m-v3-interact · 自检：任取一人，输出必须含身份、未了的事与记忆段。"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PEOPLE = os.path.join(ROOT, "modules", "m-p1-census", "data", "people.json")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with open(PEOPLE, encoding="utf-8") as f:
        people = json.load(f)["people"]
    pid = people[0]["id"]
    p = subprocess.run([sys.executable, os.path.join(HERE, "show.py"), pid],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = p.stdout or ""
    need = ["未了的事", "记忆", people[0]["called"]]
    miss = [x for x in need if x not in out]
    if p.returncode != 0 or miss:
        print(f"✗ 输出缺：{miss} rc={p.returncode}")
        return 1
    print(f"✓ show.py 正常（{pid} · {len(out.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
