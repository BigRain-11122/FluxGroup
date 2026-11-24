#!/usr/bin/env python3
"""BMC 守望：每轮扫两段网段，一旦出现「新设备」立刻深入探测并打印。

用途：插线时人不在电脑前，不用反复手动扫。
判据：新出现的地址若 623/UDP 回 ASF pong，或 80 端口网页像 BMC，即报「找到了」。
"""
import socket
import subprocess
import sys
import time

SEGS = ["192.168.31", "192.168.0"]
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 60   # 60 轮 ≈ 8 分钟
PING = bytes.fromhex("060000ff06000011be80000000000000")


def sweep(seg):
    try:
        r = subprocess.run(["fping", "-a", "-q", "-t", "250", "-r", "1", "-g", seg + ".0/24"],
                           capture_output=True, text=True, timeout=60)
        return set(x for x in r.stdout.split() if x)
    except Exception:
        return set()


def asf(ip, t=0.6):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(t)
    try:
        s.sendto(PING, (ip, 623))
        d, _ = s.recvfrom(2048)
        return d.hex()
    except Exception:
        return None
    finally:
        s.close()


def tcp(ip, port, t=0.8):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(t)
    try:
        return s.connect_ex((ip, port)) == 0
    except Exception:
        return False
    finally:
        s.close()


def web_title(ip):
    try:
        r = subprocess.run(["curl", "-s", "-m", "3", "http://%s/" % ip],
                           capture_output=True, text=True, timeout=6)
        for ln in r.stdout.splitlines():
            if "<title>" in ln.lower():
                return ln.strip()[:80]
    except Exception:
        pass
    return ""


base = set()
for s in SEGS:
    base |= sweep(s)
print("[基线] 已有设备 %d 台：%s" % (len(base), " ".join(sorted(base))), flush=True)
print("[守望开始] 每轮约 8 秒，共 %d 轮。插好线就会在这里报出来。" % ROUNDS, flush=True)

for n in range(1, ROUNDS + 1):
    seen = set()
    for s in SEGS:
        seen |= sweep(s)
    new = seen - base
    if new:
        for ip in sorted(new):
            pong = asf(ip)
            p80 = tcp(ip, 80)
            title = web_title(ip) if p80 else ""
            verdict = "★ BMC 候选（ASF 有应答）" if pong else ("网页设备" if p80 else "仅 ICMP 可达")
            print("[第%d轮 新设备] %s  623pong=%s 80=%s %s  %s"
                  % (n, ip, bool(pong), p80, title, verdict), flush=True)
        print("[建议] 若是 BMC：浏览器开 http://%s ，默认 ADMIN/ADMIN" % sorted(new)[0], flush=True)
        base |= new
    else:
        print("[第%d轮] %s 无新增（已见 %d 台）" % (n, time.strftime("%H:%M:%S"), len(seen)), flush=True)
    time.sleep(8)

print("[守望结束] 共 %d 轮，未发现新设备。" % ROUNDS, flush=True)
