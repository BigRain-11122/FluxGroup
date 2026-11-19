#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fan_boost.py - 直接通过 AppleSMC 设定风扇目标转速（需要 root）

为什么自己写（2026-11-19 CEO「提高风扇转速」）：
  Macs Fan Control 没有任何脚本/AppleScript/URL 接口，改它的 plist 会被
  App 启动时覆盖成 Predefined:0（实测）；brew 也没有现成 smc 命令行。
  而 SMC 写入本身是标准操作，用 IOKit 的 AppleSMC 服务几十行就能做。

用法：
  sudo python3 Tools/fleet/fan_boost.py --show          # 只读：当前/最小/最大转速
  sudo python3 Tools/fleet/fan_boost.py --max           # 拉到硬件最大
  sudo python3 Tools/fleet/fan_boost.py --pct 80        # 拉到最大转速的 80%
  sudo python3 Tools/fleet/fan_boost.py --rpm 5500      # 指定目标
  sudo python3 Tools/fleet/fan_boost.py --auto          # 交回系统自动（清强制位）

要点：
  - 写 F0Tg/F1Tg 设目标，再写 FS! 置强制位（bit0=风扇0，bit1=风扇1）
  - --auto 把 FS! 写 0，让 SMC 回到自动曲线（Macs Fan Control 也能接管）
  - 转速是 fpe2 编码（两字节大端 /4），别按整数写
退出码：0 成功 / 2 需要 root / 3 读不到风扇（机型无风扇或键名不同）
"""
import argparse
import ctypes
import ctypes.util
import sys

KERNEL_INDEX_SMC = 2
SMC_CMD_READ_BYTES = 5
SMC_CMD_WRITE_BYTES = 6
SMC_CMD_READ_KEYINFO = 9


class SMCVers(ctypes.Structure):
    _fields_ = [("major", ctypes.c_ubyte), ("minor", ctypes.c_ubyte),
                ("build", ctypes.c_ubyte), ("reserved", ctypes.c_ubyte),
                ("release", ctypes.c_ushort)]


class SMCPLimit(ctypes.Structure):
    _fields_ = [("version", ctypes.c_ushort), ("length", ctypes.c_ushort),
                ("cpuPLimit", ctypes.c_uint32), ("gpuPLimit", ctypes.c_uint32),
                ("memPLimit", ctypes.c_uint32)]


class SMCKeyInfo(ctypes.Structure):
    _fields_ = [("dataSize", ctypes.c_uint32), ("dataType", ctypes.c_uint32),
                ("dataAttributes", ctypes.c_ubyte)]


class SMCKeyData(ctypes.Structure):
    _fields_ = [("key", ctypes.c_uint32), ("vers", SMCVers),
                ("pLimitData", SMCPLimit), ("keyInfo", SMCKeyInfo),
                ("result", ctypes.c_ubyte), ("status", ctypes.c_ubyte),
                ("data8", ctypes.c_ubyte), ("data32", ctypes.c_uint32),
                ("bytes", ctypes.c_ubyte * 32)]


def _fourcc(s):
    v = 0
    for ch in s.encode():
        v = (v << 8) | ch
    return v


def open_smc():
    iokit = ctypes.CDLL(ctypes.util.find_library("IOKit"))
    # 必须显式声明签名：默认 restype 是 int，AppleSMC 的指针会被截断成 32 位，
    # 表现为"能跑但一句都不打印"（2026-11-19 实测踩到）。
    iokit.IOServiceMatching.restype = ctypes.c_void_p
    iokit.IOServiceMatching.argtypes = [ctypes.c_char_p]
    iokit.IOServiceGetMatchingService.restype = ctypes.c_uint32
    iokit.IOServiceGetMatchingService.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
    iokit.IOServiceOpen.restype = ctypes.c_int
    iokit.IOServiceOpen.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                                    ctypes.POINTER(ctypes.c_uint32)]
    iokit.IOConnectCallStructMethod.restype = ctypes.c_int
    iokit.IOConnectCallStructMethod.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
    service = iokit.IOServiceGetMatchingService(0, iokit.IOServiceMatching(b"AppleSMC"))
    if not service:
        return None, None
    conn = ctypes.c_uint32(0)
    r = iokit.IOServiceOpen(service, ctypes.c_uint32(0), ctypes.c_uint32(0), ctypes.byref(conn))
    if r != 0:
        return None, None
    return iokit, conn


def _call(iokit, conn, data):
    out = SMCKeyData()
    size = ctypes.c_size_t(ctypes.sizeof(SMCKeyData))
    iokit.IOConnectCallStructMethod(conn, ctypes.c_uint32(KERNEL_INDEX_SMC),
                                    ctypes.byref(data), ctypes.sizeof(data),
                                    ctypes.byref(out), ctypes.byref(size))
    return out


def read_key(iokit, conn, key):
    d = SMCKeyData()
    d.key = _fourcc(key)
    d.data8 = SMC_CMD_READ_KEYINFO
    info = _call(iokit, conn, d)
    if info.result != 0:
        return None
    n = info.keyInfo.dataSize
    d2 = SMCKeyData()
    d2.key = d.key
    d2.keyInfo.dataSize = n
    d2.data8 = SMC_CMD_READ_BYTES
    b = _call(iokit, conn, d2)
    if b.result != 0:
        return None
    return bytes(b.bytes[:n])


def write_key(iokit, conn, key, data):
    d = SMCKeyData()
    d.key = _fourcc(key)
    d.data8 = SMC_CMD_WRITE_BYTES
    d.keyInfo.dataSize = len(data)
    for i, v in enumerate(data):
        d.bytes[i] = v
    return _call(iokit, conn, d).result


def fpe2_to_rpm(b):
    if not b or len(b) < 2:
        return None
    return ((b[0] << 8) | b[1]) / 4.0


def rpm_to_fpe2(rpm):
    v = int(round(rpm * 4)) & 0xFFFF
    return bytes([(v >> 8) & 0xFF, v & 0xFF])


def fans(iokit, conn):
    out = []
    for i in range(2):
        cur = read_key(iokit, conn, "F%dAc" % i)
        if cur is None:
            continue
        out.append({
            "idx": i,
            "cur": fpe2_to_rpm(cur),
            "min": fpe2_to_rpm(read_key(iokit, conn, "F%dMn" % i)),
            "max": fpe2_to_rpm(read_key(iokit, conn, "F%dMx" % i)),
            "tgt": fpe2_to_rpm(read_key(iokit, conn, "F%dTg" % i)),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--show", action="store_true")
    g.add_argument("--max", action="store_true")
    g.add_argument("--auto", action="store_true")
    g.add_argument("--pct", type=float)
    g.add_argument("--rpm", type=float)
    a = ap.parse_args()

    iokit, conn = open_smc()
    if not iokit:
        print("[fan] 打不开 AppleSMC（需要 root，或本机无 SMC）", file=sys.stderr)
        return 2

    fl = fans(iokit, conn)
    if not fl:
        print("[fan] 读不到风扇（键名不同或无风扇）", file=sys.stderr)
        return 3

    def show():
        for f in fl:
            print("  fan%d: 当前 %s / 目标 %s / 范围 %s-%s RPM" % (
                f["idx"], _r(f["cur"]), _r(f["tgt"]), _r(f["min"]), _r(f["max"])))

    if a.show or not any([a.max, a.auto, a.pct, a.rpm]):
        show()
        return 0

    if a.auto:
        rc = write_key(iokit, conn, "FS! ", bytes([0, 0]))
        print("[fan] 已交回系统自动（FS! = 0），写入 rc=%d" % rc)
        return 0 if rc == 0 else 1

    # 目标转速：统一按各风扇最大值比例算，避免超过硬件上限
    for f in fl:
        mx = f["max"] or f["cur"] or 0
        if a.max:
            tgt = mx
        elif a.pct is not None:
            tgt = mx * max(0.0, min(100.0, a.pct)) / 100.0
        else:
            tgt = a.rpm
        if not mx or tgt <= 0:
            continue
        tgt = min(tgt, mx)
        rc = write_key(iokit, conn, "F%dTg" % f["idx"], rpm_to_fpe2(tgt))
        print("[fan] fan%d 目标设为 %d RPM（上限 %d）写入 rc=%d"
              % (f["idx"], round(tgt), round(mx), rc))
    # 强制位：bit0=fan0, bit1=fan1
    bits = 0
    for f in fl:
        if f["idx"] < 8:
            bits |= (1 << f["idx"])
    rc = write_key(iokit, conn, "FS! ", bytes([0, bits]))
    print("[fan] 强制位 FS! = %d 写入 rc=%d" % (bits, rc))
    print("[fan] 完成后复查：")
    fl2 = fans(iokit, conn)
    for f in fl2:
        print("  fan%d: 当前 %s / 目标 %s RPM" % (f["idx"], _r(f["cur"]), _r(f["tgt"])))
    return 0


def _r(v):
    return "-" if v is None else str(int(round(v)))


if __name__ == "__main__":
    sys.exit(main())
