# -*- coding: utf-8 -*-
"""advance · 推进 N 天，并刷新派生与总览（循环用的一条命令）

运行：python tools/advance.py 1
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PY = sys.executable


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    n = sys.argv[1] if len(sys.argv) > 1 else "1"
    for cmd in (["modules/m-w2-clock/engine.py", n],
                ["modules/m-p2-memory/derive.py"],
                ["modules/m-w3-settle/settle.py"],
                ["tools/status.py"]):
        p = subprocess.run([PY] + cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode != 0:
            print(f"✗ {cmd[0]} 失败")
            print((p.stdout or "")[-400:] + (p.stderr or "")[-400:])
            return 1
    print(f"✓ 推进 {n} 天，派生与总览已刷新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
