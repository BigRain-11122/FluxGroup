# -*- coding: utf-8 -*-
"""sitecustomize.py - 全局静默钩子（bm-c，2026-11-23）

CEO 令：「所有任务都自动化，不要弹窗」。

问题：
  计划任务用 pythonw 承载（pythonw 无控制台，任务本身不弹窗），但脚本里调用的
  git / nvidia-smi / powershell / tasklist 都是控制台程序。**父进程没有控制台时，
  Windows 会为每一个子进程新建一个控制台窗口**，于是「任务静默」变成「每个子进程
  闪一下黑窗」。逐个脚本补 creationflags 既慢又必然漏（2026-11-23 实测：补了 8 处
  之后仍剩 nvidia-smi 漏网）。

做法：
  在 subprocess.Popen 上加一层包装——**仅当本进程没有控制台时**自动补
  CREATE_NO_WINDOW。父进程有控制台时行为完全不变（子进程本来继承父控制台，
  不会新建窗口），因此交互式 python 不受影响。无需修改任何业务脚本。

验证（2026-11-23 双对照组）：
  有钩子：pythonw 跑 ping 5s / nvidia-smi，可见控制台窗口 peak=0 → NO-FLASH
  无钩子：同两命令 peak=1 且 flashed=true → FLASH
  即「有钩子零窗口、没钩子必闪一个」的因果成立。

逃生阀：
  FLUX_ALLOW_CONSOLE=1 时整个钩子不生效。
"""
import os
import sys

if os.name == "nt" and not os.environ.get("FLUX_ALLOW_CONSOLE"):
    try:
        import ctypes
        import subprocess

        CREATE_NO_WINDOW = 0x08000000

        # 本进程有控制台则什么都不做（子进程继承，本来就不弹）。
        if ctypes.windll.kernel32.GetConsoleWindow() == 0:
            _orig_init = subprocess.Popen.__init__

            def _silent_init(self, *args, **kwargs):
                if "creationflags" not in kwargs and "startupinfo" not in kwargs:
                    kwargs["creationflags"] = CREATE_NO_WINDOW
                return _orig_init(self, *args, **kwargs)

            subprocess.Popen.__init__ = _silent_init
    except Exception:
        # 钩子失败绝不允许影响业务：静默放弃，由各脚本自己的 creationflags 兜底。
        pass
