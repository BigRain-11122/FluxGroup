# -*- coding: utf-8 -*-
"""
setup · 运行时状态初始化（状态已移出 git，新克隆需要它）

只补齐缺失的文件，不动已有的：
  events.jsonl  空文件
  time.json     {"day":0,"seq":0}
然后跑 derive + settle，让世界自洽。

运行：python tools/setup.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CLOCK = os.path.join(ROOT, "modules", "m-w2-clock", "data", "events.jsonl")
TIME = os.path.join(ROOT, "modules", "m-w2-clock", "data", "time.json")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    made = []

    os.makedirs(os.path.dirname(CLOCK), exist_ok=True)
    if not os.path.exists(CLOCK):
        open(CLOCK, "w").close()
        made.append("events.jsonl")
    if not os.path.exists(TIME):
        with open(TIME, "w", encoding="utf-8") as f:
            json.dump({"version": "1.1", "day": 0, "seq": 0}, f, ensure_ascii=False, indent=2)
        made.append("time.json")

    for script in ("tools/census_merge.py", "modules/m-p2-memory/derive.py", "modules/m-w3-settle/settle.py"):
        p = subprocess.run([sys.executable, script], cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            print(f"✗ {script} 失败：{(p.stderr or p.stdout)[-200:]}")
            return 1

    if made:
        print("✓ 已初始化：" + "、".join(made))
    else:
        print("✓ 运行时状态齐全，无需初始化")
    return 0


if __name__ == "__main__":
    sys.exit(main())
