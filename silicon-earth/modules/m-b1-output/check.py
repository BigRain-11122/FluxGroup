# -*- coding: utf-8 -*-
"""m-b1-output · 自检：日报单行、≤100 字、含天数"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = subprocess.run([sys.executable, os.path.join(HERE, "make.py")],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "").strip()
    lines = out.splitlines()
    if p.returncode != 0 or len(lines) != 1:
        print(f"✗ 日报应为一句话（实际 {len(lines)} 行，rc={p.returncode}）")
        return 1
    if len(out) > 100:
        print(f"✗ 超 100 字（{len(out)}）")
        return 1
    if "第" not in out or "天" not in out:
        print("✗ 缺天数")
        return 1
    print(f"✓ 日报 {len(out)} 字：{out[:40]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
