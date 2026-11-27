#!/usr/bin/env python3
"""bus_land.py - 落地不依赖 git push（给主控与各执行机用）

用途：跑完活之后，产物不再等 git 推送，直接落到总线：
  回执/结果  -> FLEET_ORDERS, 键 receipt.<order-id>.<node>
  交付文档    -> FLEET_DOCS,   键 <仓库相对路径点分化>

用法:
  python3 bus_land.py receipt <order-id> <node> <本地文件>
  python3 bus_land.py doc <本地文件>
  python3 bus_land.py check                      # 看自己能不能连上 hub

规则正身: cph4/fleet/DOC-DELIVERY-LAW-v1.md
"""
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NATS = os.environ.get("NATS_BIN", os.path.join(ROOT, "Tools", "nats", "bin", "nats.exe"))
if not os.path.exists(NATS):
    NATS = "nats"  # macOS: brew install nats-io/nats-tools/nats
SERVER = os.environ.get("NATS_SERVER", "100.110.185.62:4222")


def _kv_put(bucket, key, data: bytes):
    r = subprocess.run([NATS, "--server", SERVER, "kv", "put", bucket, key],
                       input=data, capture_output=True)
    return r.returncode, (r.stdout or b"").decode("utf-8", "replace"), \
        (r.stderr or b"").decode("utf-8", "replace")


def land(bucket, key, payload: dict):
    payload = dict(payload)
    payload["sha256"] = hashlib.sha256(
        json.dumps(payload.get("body", ""), ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]
    payload.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    rc, out, err = _kv_put(bucket, key, data)
    print(f"{'OK' if rc == 0 else 'FAIL'} {bucket}/{key} bytes={len(data)}")
    if rc:
        print(err[-300:])
    return rc


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 1
    if a[0] == "check":
        rc, out, err = subprocess.run(
            [NATS, "--server", SERVER, "kv", "ls", "FLEET_ORDERS"],
            capture_output=True).returncode, "", ""
        print("hub", SERVER, "reachable" if rc == 0 else f"FAIL rc={rc}")
        return rc
    if a[0] == "receipt" and len(a) >= 4:
        order, node, path = a[1], a[2], a[3]
        body = open(path, encoding="utf-8", errors="replace").read()[:20000]
        return land("FLEET_ORDERS", f"receipt.{order}.{node}",
                    {"order": order, "node": node, "body": body,
                     "path": os.path.relpath(path, ROOT).replace("\\", "/"),
                     "landed": "bus"})
    if a[0] == "doc" and len(a) >= 2:
        path = a[1]
        rel = os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
        key = rel.replace("/", ".")
        body = open(path, encoding="utf-8", errors="replace").read()
        return land("FLEET_DOCS", key,
                    {"path": rel, "body": body, "landed": "bus"})
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())