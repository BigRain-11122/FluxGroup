#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install_drive_agent.py - 生成（可选加载）v3 自驱的 LaunchAgent。

2026-11-12 立（批次6 准备）。背景：暂停目录里只有 v2 的 pulse / selfdrive /
statesync —— pulse 往已归档的 PRODUCTION-QUEUE 造卡，selfdrive 是旧执行器。
v3 的自驱（station_drive）**没有任何执行体**，所以 AUTOMATION-v1 那 19 条排班
永远只是纸面（校验器已改判 PLAN-ONLY，但纸不会自己动）。

本脚本只做一件事：把 com.fluxgroup.drive.plist 按本机实际路径写好。
默认 **只生成不加载**（CEO 2026-11-11「全部暂停，等我梳理工作流」仍在生效）；
要真启用必须显式 --load，且应先过 go_live_preflight.py。

用法：
  python3 Tools/fleet/install_drive_agent.py                 # 只生成，打印路径
  python3 Tools/fleet/install_drive_agent.py --interval 300   # 自定义周期（秒）
  python3 Tools/fleet/install_drive_agent.py --load           # 生成并 launchctl 加载
  python3 Tools/fleet/install_drive_agent.py --unload         # 卸载并保留 plist
  python3 Tools/fleet/install_drive_agent.py --print          # 打到 stdout 不落盘
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LABEL = "com.fluxgroup.drive"
LA = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents")
PLIST = os.path.join(LA, LABEL + ".plist")


def render(interval=300, station=None):
    station = station or _station()
    log = os.path.join(os.path.expanduser("~"), "Library", "Logs", "fluxgroup-drive.log")
    err = os.path.join(os.path.expanduser("~"), "Library", "Logs", "fluxgroup-drive.err")
    env = ""
    if station:
        env = ("  <key>EnvironmentVariables</key>\n  <dict>\n"
               "    <key>FLEET_STATION</key>\n    <string>%s</string>\n  </dict>\n" % station)
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>%s</string>
  <key>ProgramArguments</key>
  <array>
    <string>%s</string>
    <string>%s</string>
    <string>--once</string>
  </array>
  <key>StartInterval</key>
  <integer>%d</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>%s</string>
  <key>StandardErrorPath</key>
  <string>%s</string>
%s  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
""" % (LABEL, sys.executable, os.path.join(ROOT, "Tools", "fleet", "station_drive.py"),
       interval, log, err, env)


def _station():
    try:
        sys.path.insert(0, HERE)
        import fleet_identity as fid
        return fid.station_or_none()
    except Exception:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--load", action="store_true")
    ap.add_argument("--unload", action="store_true")
    ap.add_argument("--print", dest="to_stdout", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        import plistlib
        ok = tot = 0

        def chk(name, cond, detail=""):
            nonlocal ok, tot
            tot += 1
            ok += 1 if cond else 0
            print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

        for iv in (300, 60):
            d = plistlib.loads(render(iv).encode())
            chk("plist 可解析（interval=%d）" % iv, d.get("Label") == LABEL, d.get("Label"))
            chk("含 station_drive --once（interval=%d）" % iv,
                any("station_drive.py" in str(x) for x in d.get("ProgramArguments") or []),
                d.get("ProgramArguments"))
            chk("周期=%d" % iv, d.get("StartInterval") == iv, d.get("StartInterval"))
        chk("负控：周期<=0 不是本工具的合法输入", render(0).count("<integer>0</integer>") == 1)
        print("[install_drive_agent] %d/%d" % (ok, tot))
        return 0 if ok == tot else 1

    text = render(a.interval)
    if a.to_stdout:
        print(text)
        return 0
    if a.unload:
        try:
            subprocess.run(["launchctl", "bootout", "gui/%d/%s" % (os.getuid(), LABEL)],
                           capture_output=True, text=True, timeout=20)
        except Exception as e:
            print("unload 失败：%s" % e)
            return 1
        print("已卸载 %s（plist 保留在 %s）" % (LABEL, PLIST))
        return 0
    os.makedirs(LA, exist_ok=True)
    with open(PLIST, "w", encoding="utf-8") as f:
        f.write(text)
    print("已生成：%s" % PLIST)
    if not a.load:
        print("（未加载。要启用：先过 go_live_preflight.py，再 --load）")
        return 0
    try:
        subprocess.run(["launchctl", "bootout", "gui/%d/%s" % (os.getuid(), LABEL)],
                       capture_output=True, text=True, timeout=20)
        r = subprocess.run(["launchctl", "bootstrap", "gui/%d" % os.getuid(), PLIST],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print("加载失败（rc=%d）：%s" % (r.returncode, (r.stderr or "").strip()[:200]))
            return 1
        print("已加载 %s（每 %d 秒跑一次 station_drive --once）" % (LABEL, a.interval))
    except Exception as e:
        print("加载异常：%s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
