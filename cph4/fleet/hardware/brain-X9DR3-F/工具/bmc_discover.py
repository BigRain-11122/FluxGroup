#!/usr/bin/env python3
"""BMC 发现器（超微 X9 / AMI BMC 通用）—— 不依赖 IPMIView，不依赖已知 IP。

两种手段：
  1. ASF Presence Ping 广播（UDP/623）：与本机同二层广播域内的 BMC 会回 Pong，
     **即使 BMC 的 IP 在别的网段也能被发现**。
  2. ICMP 扫描：覆盖「BMC 已从本段 DHCP 拿到地址」的正常情况。

用法：
    python3 bmc_discover.py                # 自动取本机所有网段的广播地址
    python3 bmc_discover.py 192.168.31.255 # 指定广播地址

判据：看到 Pong 的 IP 就是管理口地址；随后用浏览器 http://<IP> 或 ipmitool 登录（默认 ADMIN/ADMIN）。
"""
import socket
import struct
import subprocess
import sys
import time

# RMCP Presence Ping (ASF): ver6, seq=0xFF(无应答), class=ASF(6), IANA 0x000011BE, type=0x80
PING = bytes.fromhex("060000ff06000011be80000000000000")
PORT = 623


def local_broadcasts():
    """取本机所有非回环、非链路本地网段的定向广播地址。"""
    out = []
    try:
        txt = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return out
    for line in txt.splitlines():
        if not line.startswith("\tinet ") or "127.0.0.1" in line:
            continue
        parts = line.split()
        ip, mask = parts[1], parts[3] if len(parts) > 3 else None
        if not mask or mask == "0xffffffff":
            continue
        try:
            i = struct.unpack("!I", socket.inet_aton(ip))[0]
            m = int(mask, 16)
        except Exception:
            continue
        b = socket.inet_ntoa(struct.pack("!I", (i & m) | (~m & 0xFFFFFFFF)))
        if not b.startswith("127."):
            out.append(b)
    return sorted(set(out))


def asf_ping(targets, window):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(0.3)
    for t in targets:
        try:
            s.sendto(PING, (t, PORT))
            print("[发出] ASF presence ping -> %s:%d" % (t, PORT))
        except OSError as e:
            print("[跳过] %s -> %s" % (t, e))
    hits = {}
    end = time.time() + window
    while time.time() < end:
        try:
            data, peer = s.recvfrom(2048)
        except socket.timeout:
            continue
        hits.setdefault(peer[0], 0)
        hits[peer[0]] += 1
        print("[应答] %s  %dB  %s" % (peer[0], len(data), data.hex()))
    return hits


def icmp_sweep(cidrs):
    """用 fping 快速扫存活（macOS 自带）。"""
    alive = []
    for c in cidrs:
        try:
            r = subprocess.run(["fping", "-a", "-q", "-t", "200", "-r", "0", "-g", c],
                               capture_output=True, text=True, timeout=90)
            alive += [x for x in r.stdout.split() if x]
        except Exception as e:
            print("[跳过] ICMP %s -> %s" % (c, e))
    return alive


def local_ips():
    """本机自己的地址，结论里要排除掉，否则会把自己报成『待确认设备』。"""
    try:
        txt = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return set()
    return {ln.split()[1] for ln in txt.splitlines() if ln.startswith("\tinet ")}


if __name__ == "__main__":
    bcast = sys.argv[1:] or local_broadcasts()
    if not bcast:
        bcast = ["255.255.255.255"]
    print("=== 广播目标 ===")
    hits = asf_ping(bcast, window=6.0)

    cidrs = sorted({".".join(b.split(".")[:3]) + ".0/24" for b in bcast if b.count(".") == 3})
    print("\n=== ICMP 存活 ===")
    alive = icmp_sweep(cidrs)
    print(" ".join(alive) if alive else "无")

    print("\n=== 结论 ===")
    if hits:
        for ip, n in hits.items():
            print("BMC 候选：%s（Pong %d 次）→ http://%s" % (ip, n, ip))
    else:
        print("ASF：0 个 BMC 应答。")
        # ASF 无应答时，ICMP 结果只能说明「本网段有哪些设备」，不能证明其中没有 BMC
        mine = local_ips()
        unknown = [a for a in alive if not a.endswith(".1") and a not in mine]
        if unknown:
            print("待人工确认的设备：%s（逐个看 80/443/623 与网页标题）" % " ".join(unknown))
        else:
            print("本网段除网关外没有其它设备 → BMC 不在这一层：先查网线是否插在 IPMI_LAN、是否插在同一个路由器的 LAN 口、板子是否通电。")
