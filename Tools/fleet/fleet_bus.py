#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_bus.py - 主控侧常驻订阅：把机队发上总线的状态落成本机可读文件。

为什么（2026-11-05 实测）：机队每 45 秒确实在发（60 秒窗口收到 8 条
$KV.FLEET_STATE.lane.result.* 与 state.*），但主控侧读回（JetStream DIRECT.GET）
是坏的——写进去不落库、读出来为空。于是"机队在报"和"主控收不到"同时成立，
主控只能看到卡标 RUNNING。正法不是修那条坏读腿，而是让主控自己订阅：
普通 pub/sub 实测可用，收到即落盘。

落盘：
  state/lane-status/<node>.json   ← lane.result.<node>   (job/elapsed/out_bytes)
  state/node-state/<node>.json    ← state.<node>          (机器自身状态)

用法：
  python3 Tools/fleet/fleet_bus.py            # 常驻（launchd KeepAlive）
  python3 Tools/fleet/fleet_bus.py --once 30  # 只订 30 秒（自检用）
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ST = os.path.join(ROOT, "cph4", "fleet", "state")
sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

BUCKET = fl.KV_BUCKET
RECV_LOG = os.path.join(ST, "fleet-bus.jsonl")


def _write(subject, payload):
    key = subject.split("$KV.%s." % BUCKET, 1)[-1] if BUCKET in subject else subject
    try:
        data = json.loads(payload.decode("utf-8", "replace"))
    except Exception:
        return None
    ts = datetime.now().isoformat(timespec="seconds")
    data.setdefault("received_at", ts)
    if key.startswith("lane.result."):
        node = key.split(".", 2)[-1]
        d = os.path.join(ST, "lane-status")
        os.makedirs(d, exist_ok=True)
        data["node"] = data.get("node") or node
        p = os.path.join(d, node + ".json")
    elif key.startswith("state."):
        node = key.split(".", 1)[-1]
        d = os.path.join(ST, "node-state")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, node + ".json")
    else:
        return None
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, p)
    return p


def run(seconds=None):
    s = fl._nats_connect(fl.HUB_DEFAULT, fl.PORT_DEFAULT, 10.0)
    s.sendall(("SUB $KV.%s.> 200\r\nPING\r\n" % BUCKET).encode())
    deadline = time.time() + seconds if seconds else None
    buf = b""
    n = 0
    while True:
        if deadline and time.time() > deadline:
            break
        try:
            s.settimeout(5)
            chunk = s.recv(65536)
        except Exception:
            continue
        if not chunk:
            s.close()
            if deadline:
                break
            time.sleep(2)
            s = fl._nats_connect(fl.HUB_DEFAULT, fl.PORT_DEFAULT, 10.0)
            s.sendall(("SUB $KV.%s.> 200\r\nPING\r\n" % BUCKET).encode())
            buf = b""
            continue
        buf += chunk
        # 拆 MSG <subject> <sid> <bytes>\r\n<payload>\r\n
        while True:
            i = buf.find(b"MSG ")
            if i < 0:
                buf = b""
                break
            j = buf.find(b"\r\n", i)
            if j < 0:
                break
            head = buf[i:j].split()
            if len(head) < 4:
                buf = buf[j + 2:]
                continue
            subj, size = head[1].decode("utf-8", "replace"), int(head[3])
            start = j + 2
            if len(buf) < start + size + 2:
                break
            payload = buf[start:start + size]
            buf = buf[start + size + 2:]
            try:
                if _write(subj, payload):
                    n += 1
            except Exception:
                pass
    s.close()
    return n


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", type=float, default=None)
    a = ap.parse_args(argv)
    n = run(a.once)
    print("[fleet-bus] wrote %d status file(s)%s" % (n, "" if a.once else " (resident)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))