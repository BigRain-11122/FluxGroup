#!/usr/bin/env python3
"""彻底扫一遍：逐个 IP 发 ASF ping(UDP/623) + 并行探 TCP 80/443/22。

为什么要逐个发：路由器的广播（192.168.31.255）可能被 AP 隔离或访客网络挡住，
而逐地址单播不受这个影响。
"""
import concurrent.futures as cf
import socket
import sys
import time

NET = sys.argv[1] if len(sys.argv) > 1 else "192.168.31"
PING = bytes.fromhex("060000ff06000011be80000000000000")
HOSTS = ["%s.%d" % (NET, i) for i in range(1, 255)]


def udp_ping(ip, timeout=0.35):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(PING, (ip, 623))
        data, peer = s.recvfrom(2048)
        return (ip, "ASF_PONG", len(data), data.hex()[:40])
    except socket.timeout:
        return None
    except OSError:
        return None
    finally:
        s.close()


def tcp_probe(ip, port, timeout=0.4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        if s.connect_ex((ip, port)) == 0:
            return (ip, port)
    except OSError:
        pass
    finally:
        s.close()
    return None


print("=== 1) 逐地址 ASF ping (UDP/623) ===")
hits = []
with cf.ThreadPoolExecutor(max_workers=64) as ex:
    for r in ex.map(udp_ping, HOSTS):
        if r:
            hits.append(r)
print("\n".join("%s  %s %dB %s" % h for h in hits) if hits else "无应答")

print("\n=== 2) 逐地址 TCP 80/443/22 ===")
open_ports = []
tasks = [(ip, p) for ip in HOSTS for p in (80, 443, 22)]
with cf.ThreadPoolExecutor(max_workers=128) as ex:
    for r in ex.map(lambda a: tcp_probe(*a), tasks):
        if r:
            open_ports.append(r)
for ip, p in sorted(open_ports):
    print("%s:%d open" % (ip, p))
if not open_ports:
    print("无开放端口")

print("\n=== 结论 ===")
if hits:
    print("BMC 候选（ASF 应答）：" + ", ".join(h[0] for h in hits))
else:
    print("全部 254 个地址都没有 BMC 应答。")
