#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_index.py - 给一个产物目录生成索引（清单+大小+哈希），供自驱的"索引"工序使用。

为什么要有它：`T-DOC-INDEX`（索引）一直是 TOOL-PENDING——契约有、命令没有，
所以自驱动不了。索引本身是确定性活（扫目录、算哈希、写 JSON），最适合交给机器。

用法：
  python3 Tools/fleet/make_index.py --root cph4/fleet/out/asset-pack --out cph4/fleet/out/asset-pack/index.json
  python3 Tools/fleet/make_index.py --self-test
退出码：0 有产物（至少一条）/ 1 目录不存在或为空 / 3 自检失败
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _sha(p, limit=256 * 1024 * 1024):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            n += len(b)
            if n > limit:
                break
    return h.hexdigest()


def build(root_dir, out_path, rel_base=None):
    if not os.path.isdir(root_dir):
        return {"ok": False, "why": "目录不存在: %s" % root_dir, "count": 0}
    items = []
    for d, _, xs in sorted(os.walk(root_dir)):
        for x in sorted(xs):
            fp = os.path.join(d, x)
            if os.path.abspath(fp) == os.path.abspath(out_path):
                continue
            try:
                items.append({"path": os.path.relpath(fp, root_dir),
                              "bytes": os.path.getsize(fp),
                              "sha256": _sha(fp)})
            except OSError:
                continue
    if not items:
        return {"ok": False, "why": "目录为空: %s" % root_dir, "count": 0}
    idx = {"generated_at": datetime.now().isoformat(timespec="seconds"),
           "root": os.path.relpath(root_dir, rel_base or ROOT) if os.path.isabs(root_dir) else root_dir,
           "count": len(items),
           "total_bytes": sum(i["bytes"] for i in items),
           "items": items}
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    return {"ok": True, "count": len(items), "out": out_path,
            "total_bytes": idx["total_bytes"]}


def self_test():
    ok = total = 0

    def chk(n, c):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s" % ("ok  " if c else "FAIL", n))

    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "src")
        os.makedirs(os.path.join(src, "sub"))
        open(os.path.join(src, "a.txt"), "w").write("aaa")
        open(os.path.join(src, "sub", "b.bin"), "wb").write(b"bbbb")
        out = os.path.join(src, "index.json")
        r = build(src, out, rel_base=td)
        chk("有产物时成功", r["ok"] and r["count"] == 2)
        idx = json.load(open(out))
        chk("索引含路径/大小/哈希三件", all({"path", "bytes", "sha256"} <= set(i) for i in idx["items"]))
        chk("索引自身不被计入", all(i["path"] != "index.json" for i in idx["items"]))
        # 内容变化 -> 哈希变化
        open(os.path.join(src, "a.txt"), "w").write("changed")
        r2 = build(src, out, rel_base=td)
        idx2 = json.load(open(out))
        h1 = [i for i in idx["items"] if i["path"] == "a.txt"][0]["sha256"]
        h2 = [i for i in idx2["items"] if i["path"] == "a.txt"][0]["sha256"]
        chk("内容变化哈希随之变化", h1 != h2)
        chk("空目录判失败（不许生成空索引冒充完成）",
            build(os.path.join(td, "none"), out)["ok"] is False)

    print("[make_index] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root")
    ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.root or not a.out:
        ap.error("需要 --root 与 --out")
    r = build(a.root, a.out)
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
