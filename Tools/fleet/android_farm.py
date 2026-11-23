#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""android_farm.py - 本机 Android 模拟器（养号手机端）管理器。

为什么（2026-11-23 CEO「把本地的模拟器部署好，以后养号走多开的模拟器手机端」）：
  浏览器养号的最大破绽是"两套 profile 同一台设备指纹"。手机端要的是**每号一台独立机器**
  （独立 AVD、独立 Android ID、独立存储），所以这里管的是"实例生命周期"，不是"一个模拟器多开"。

三条设计约束（都是本机实锚换来的）：
  1) **进程必须 start_new_session=True**：`nohup ... &` 起的模拟器会被工具调用回收
     （2026-11-23 首试：boot 到 27s 成功，调用结束即 "Cancelling all calls"）。
  2) **按内存放行**：每实例约 2.5–3GB RSS。32GB 与训练/浏览器共用同一池，
     free+inactive 不足 max(3.5GB, 实例数×2.5GB) 时拒绝再开，宁可排队也不换页。
  3) **端口成对分配**：5554/5556/5558…（console 偶数, adb 奇数），避免多实例互相顶掉。

用法：
  python3 Tools/fleet/android_farm.py list
  python3 Tools/fleet/android_farm.py start acct1 [--headful]
  python3 Tools/fleet/android_farm.py stop acct1
  python3 Tools/fleet/android_farm.py shot acct1 /tmp/a.png
  python3 Tools/fleet/android_farm.py fp acct1          # 打印该实例的设备指纹
Exit: 0 正常；2 环境缺失/内存不足；1 操作失败
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "cph4", "fleet", "state", "android-farm")
SDK = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/android-sdk")
EMU = os.path.join(SDK, "emulator", "emulator")
ADB = os.path.join(SDK, "platform-tools", "adb")
MEM_PER_INSTANCE_MB = 2600
MIN_FREE_MB = 3500


def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           errors="replace")
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as e:
        return 1, "", str(e)


def mem_free_mb():
    """free + inactive（macOS 可立即回收的部分）。"""
    rc, out, _ = sh(["vm_stat"])
    page = 4096
    try:
        page = int(re.search(r"page size of (\d+) bytes", out).group(1))
    except Exception:
        pass
    def pages(key):
        m = re.search(r"%s:\s+(\d+)" % key, out)
        return int(m.group(1)) if m else 0
    return round((pages("Pages free") + pages("Pages inactive")) * page / 1048576)


def avd_home():
    return os.path.expanduser("~/.android/avd")


def instances():
    """已知实例清单（AVD 名 → 配置/pid/log）。"""
    out = []
    if not os.path.isdir(avd_home()):
        return out
    for f in sorted(os.listdir(avd_home())):
        if f.endswith(".ini"):
            out.append(f[:-4])
    return out


def running():
    rc, out, _ = sh([ADB, "devices"])
    res = {}
    for line in out.splitlines()[1:]:
        if "\t" in line:
            serial, st = line.split("\t", 1)
            res[serial] = st.strip()
    return res


def port_for(name):
    names = instances()
    if name in names:
        return 5554 + 2 * names.index(name)
    return None


def booted(serial, wait_s=120):
    deadline = time.time() + wait_s
    while time.time() < deadline:
        rc, out, _ = sh([ADB, "-s", serial, "shell", "getprop", "sys.boot_completed"], 10)
        if out.strip() == "1":
            return True
        time.sleep(3)
    return False


def cmd_list(a):
    os.makedirs(STATE, exist_ok=True)
    r = running()
    rows = []
    for name in instances():
        port = port_for(name)
        serial = "emulator-%d" % port if port else None
        st = r.get(serial, "absent")
        pidf = os.path.join(STATE, name + ".pid")
        pid = None
        if os.path.exists(pidf):
            try:
                pid = int(open(pidf).read().strip())
                os.kill(pid, 0)
            except Exception:
                pid = None
        rows.append({"avd": name, "serial": serial, "state": st, "pid": pid})
    rep = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "free_mb": mem_free_mb(),
           "instances": rows, "adb": r}
    print(json.dumps(rep, ensure_ascii=False, indent=1) if a.json else
          "\n".join("  %-8s %-16s %-8s pid=%s" % (x["avd"], x["serial"], x["state"], x["pid"]) for x in rows) +
          "\n  可用内存 %dMB" % rep["free_mb"])
    return 0


def cmd_start(a):
    if not os.path.exists(EMU):
        print("emulator 缺失: " + EMU, file=sys.stderr)
        return 2
    name = a.avd
    if name not in instances():
        print("AVD 不存在: %s（avdmanager list avd 看可用）" % name, file=sys.stderr)
        return 1
    port = port_for(name)
    serial = "emulator-%d" % port
    if running().get(serial) == "device":
        print("%s 已在运行 (%s)" % (name, serial))
        return 0
    free = mem_free_mb()
    if free < MIN_FREE_MB:
        print("内存不足：free+inactive=%dMB < %dMB，拒绝启动（宁排队不换页）"
              % (free, MIN_FREE_MB), file=sys.stderr)
        return 2
    os.makedirs(STATE, exist_ok=True)
    log = os.path.join(STATE, name + ".log")
    args = [EMU, "-avd", name, "-port", str(port), "-no-audio", "-no-boot-anim",
            "-memory", str(a.memory), "-gpu", a.gpu]
    if not a.headful:
        args.insert(3, "-no-window")
    if a.wipe:
        args.append("-wipe-data")
    with open(log, "ab") as lf:
        p = subprocess.Popen(args, stdout=lf, stderr=lf, start_new_session=True)
    open(os.path.join(STATE, name + ".pid"), "w").write(str(p.pid))
    print("已启动 %s（pid=%d, port=%d），等待开机…" % (name, p.pid, port))
    ok = booted(serial, a.wait)
    print("%s: %s（free=%dMB）" % (serial, "boot_completed" if ok else "启动超时",
                                   mem_free_mb()))
    return 0 if ok else 1


def cmd_stop(a):
    port = port_for(a.avd)
    if port is None:
        print("AVD 不存在: " + a.avd, file=sys.stderr)
        return 1
    serial = "emulator-%d" % port
    rc, out, err = sh([ADB, "-s", serial, "emu", "kill"], 20)
    pidf = os.path.join(STATE, a.avd + ".pid")
    if os.path.exists(pidf):
        try:
            os.kill(int(open(pidf).read().strip()), 0)
            print("adb emu kill 已发；进程仍在，建议稍后复查 list")
        except Exception:
            os.remove(pidf)
    print("%s 停止指令已发（%s）" % (a.avd, out or err or "ok"))
    return 0


def cmd_shot(a):
    port = port_for(a.avd)
    serial = "emulator-%d" % port
    with open(a.out, "wb") as f:
        r = subprocess.run([ADB, "-s", serial, "exec-out", "screencap", "-p"],
                           stdout=f, stderr=subprocess.PIPE)
    size = os.path.getsize(a.out) if os.path.exists(a.out) else 0
    print("截图 %s %dB %s" % (a.out, size, "ok" if size > 1000 else "（疑似失败）"))
    return 0 if size > 1000 else 1


def cmd_fp(a):
    port = port_for(a.avd)
    serial = "emulator-%d" % port
    keys = ["ro.serialno", "ro.product.model", "ro.product.brand", "ro.build.version.release"]
    kv = {}
    for k in keys:
        rc, out, _ = sh([ADB, "-s", serial, "shell", "getprop", k], 10)
        kv[k] = out
    rc, out, _ = sh([ADB, "-s", serial, "shell", "settings", "get", "secure", "android_id"], 10)
    kv["android_id"] = out
    print(json.dumps(kv, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("start"); s.add_argument("avd"); s.add_argument("--headful", action="store_true")
    s.add_argument("--memory", type=int, default=2048); s.add_argument("--gpu", default="swiftshader_indirect")
    s.add_argument("--wait", type=int, default=150); s.add_argument("--wipe", action="store_true")
    s.set_defaults(fn=cmd_start)
    s = sub.add_parser("stop"); s.add_argument("avd"); s.set_defaults(fn=cmd_stop)
    s = sub.add_parser("shot"); s.add_argument("avd"); s.add_argument("out"); s.set_defaults(fn=cmd_shot)
    s = sub.add_parser("fp"); s.add_argument("avd"); s.set_defaults(fn=cmd_fp)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
