#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_relay.py - 纯 TCP 转发：把内网 8790 接到回环 8791。

为什么要拆两层（2026-11-05 实测）：
  读 /Volumes 需要「完全磁盘访问」（只授予了 pyenv python）；
  而 macOS 应用防火墙按二进制路径放行（只有 /usr/bin/python3 被放行）。
  两个条件无法同时满足 → 有权限的解释器读盘，被放行的解释器只转发字节。

用法：/usr/bin/python3 Tools/fleet/asset_relay.py --listen 8790 --target 127.0.0.1:8791
"""
import argparse
import socket
import threading


def pump(src, dst):
    try:
        while True:
            b = src.recv(1 << 16)
            if not b:
                break
            dst.sendall(b)
    except OSError:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                s.close()
            except OSError:
                pass


def handle(conn, target):
    try:
        up = socket.create_connection(target, timeout=30)
    except OSError as e:
        print("[relay] 上游不可达 %s: %s" % (target, e))
        conn.close()
        return
    threading.Thread(target=pump, args=(conn, up), daemon=True).start()
    pump(up, conn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", type=int, default=8790)
    ap.add_argument("--target", default="127.0.0.1:8791")
    a = ap.parse_args()
    host, port = a.target.rsplit(":", 1)
    target = (host, int(port))
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", a.listen))
    srv.listen(64)
    print("[relay] 0.0.0.0:%d -> %s" % (a.listen, a.target))
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn, target), daemon=True).start()


if __name__ == "__main__":
    main()