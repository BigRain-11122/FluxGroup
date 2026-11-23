# -*- coding: utf-8 -*-
"""install_silence_hook.py - 把 sitecustomize.py 部署到指定 Python 环境的 site-packages。

用法：
  python Tools/fleet/silence-hook/install_silence_hook.py            # 自动找本机已知环境
  python Tools/fleet/silence-hook/install_silence_hook.py --python <python.exe 路径>
  python Tools/fleet/silence-hook/install_silence_hook.py --check    # 只检查不写

幂等：内容相同则跳过；内容不同则备份原文件为 .bak-<时间戳> 后再覆盖。
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sitecustomize.py")

DEFAULT_PYTHONS = [
    r"C:\Users\Dasheng\AppData\Local\Programs\Python\Python313\python.exe",
    r"D:\ComfyUI\python_embeded\python.exe",
]


def site_packages(python_exe):
    try:
        out = subprocess.run(
            [python_exe, "-c", "import site,sys;print(site.getsitepackages()[0])"],
            capture_output=True, text=True, timeout=30, creationflags=0x08000000)
        return (out.stdout or "").strip() or None
    except Exception:
        return None


def digest(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except Exception:
        return None


def install(python_exe, check_only=False):
    if not os.path.exists(python_exe):
        print("SKIP  (no such python) %s" % python_exe)
        return False
    sp = site_packages(python_exe)
    if not sp or not os.path.isdir(sp):
        print("SKIP  (no site-packages) %s" % python_exe)
        return False
    dst = os.path.join(sp, "sitecustomize.py")
    same = digest(dst) == digest(SRC)
    if same:
        print("OK    already installed: %s" % dst)
        return True
    if check_only:
        print("DIFF  would install: %s" % dst)
        return False
    if os.path.exists(dst):
        bak = dst + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(dst, bak)
        print("BACKUP %s" % bak)
    shutil.copy2(SRC, dst)
    ok = digest(dst) == digest(SRC)
    print(("OK    installed: %s" if ok else "FAIL  verify mismatch: %s") % dst)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", action="append", default=[])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    targets = a.python or DEFAULT_PYTHONS
    ok = 0
    for p in targets:
        if install(p, a.check):
            ok += 1
    print("installed_or_present=%d/%d" % (ok, len(targets)))
    return 0 if ok == len(targets) else 1


if __name__ == "__main__":
    sys.exit(main())
