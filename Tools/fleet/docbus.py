#!/usr/bin/env python3
"""docbus.py - 机队文档递送（走 NATS 总线，不走 git 推送）

用法:
  python Tools/fleet/docbus.py put <本地文件>            # key 默认=仓库相对路径点分化
  python Tools/fleet/docbus.py put <本地文件> <key>
  python Tools/fleet/docbus.py get <key> <输出文件>
  python Tools/fleet/docbus.py ls [前缀]
  python Tools/fleet/docbus.py verify <key> <本地文件>   # 比 sha256，不等则 exit 2

为什么: git push 成功不等于对方收到（分支分叉/未拉取时静默失败）；总线是「写即达」。
规则正身: cph4/fleet/DOC-DELIVERY-LAW-v1.md
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NATS = os.path.join(ROOT, "Tools", "nats", "bin", "nats.exe")
SERVER = os.environ.get("NATS_SERVER", "100.110.185.62:4222")
BUCKET = os.environ.get("DOCBUS_BUCKET", "FLEET_DOCS")


def _run(args, data=None):
    r = subprocess.run([NATS, "--server", SERVER] + args, input=data, capture_output=True)
    return r.returncode, r.stdout, r.stderr


def to_key(path):
    rel = os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
    return rel.replace("/", ".")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def cmd_put(path, key=None):
    data = open(path, "rb").read()
    key = key or to_key(path)
    rc, out, err = _run(["kv", "put", BUCKET, key], data=data)
    if rc != 0:
        print("PUT FAIL", rc, err.decode("utf-8", "replace")[-300:])
        return rc
    print(f"PUT ok key={key} bytes={len(data)} sha256={sha(data)}")
    return 0


def cmd_get(key, out_path):
    rc, out, err = _run(["kv", "get", BUCKET, key, "--raw"])
    if rc != 0 or not out:
        print("GET FAIL", rc, err.decode("utf-8", "replace")[-300:])
        return rc or 1
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    open(out_path, "wb").write(out)
    print(f"GET ok key={key} bytes={len(out)} sha256={sha(out)} -> {out_path}")
    return 0


def cmd_ls(prefix=""):
    rc, out, err = _run(["kv", "ls", BUCKET])
    if rc != 0:
        print("LS FAIL", rc, err.decode("utf-8", "replace")[-300:])
        return rc
    keys = [l.strip() for l in out.decode("utf-8", "replace").splitlines() if l.strip()]
    keys = [k for k in keys if k.startswith(prefix)]
    for k in keys:
        print(k)
    print(f"-- {len(keys)} keys")
    return 0


def cmd_verify(key, path):
    local = open(path, "rb").read()
    rc, out, err = _run(["kv", "get", BUCKET, key, "--raw"])
    if rc != 0:
        print("VERIFY FAIL: key 不存在或取不到")
        return 2
    same = sha(local) == sha(out)
    print(f"VERIFY {'MATCH' if same else 'MISMATCH'} key={key} "
          f"local={len(local)}B bus={len(out)}B")
    return 0 if same else 2


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "put" and len(sys.argv) >= 3:
        return cmd_put(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    if cmd == "get" and len(sys.argv) >= 4:
        return cmd_get(sys.argv[2], sys.argv[3])
    if cmd == "ls":
        return cmd_ls(sys.argv[2] if len(sys.argv) > 2 else "")
    if cmd == "verify" and len(sys.argv) >= 4:
        return cmd_verify(sys.argv[2], sys.argv[3])
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())