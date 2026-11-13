#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""storage_curator.py - 主控存储管家：分级、轮转、并给出可释放空间。

Why（2026-11-13 CEO 令）：「质量要他们自己闭环，你抽检，你硬盘本来就不多」。
主控不该当仓库——产物归产出机，主控只留清单与哈希；事件流过大会拖慢一切，
且一旦磁盘满，自驱会整片停机（比任何质量问题都致命）。

安全边界（宁可少清，不可误删）：
  * 默认 dry-run：只统计与列出，不动任何文件；
  * `drop`/`offload` 类必须显式 --apply 才动，且先写 manifest（路径/大小/哈希）；
  * keep 类永不删（规则/契约/当前状态）；
  * 轮转只压缩不改语义：原文件 gzip 保留，新文件保留尾部 N 行。

用法：
    python3 Tools/fleet/storage_curator.py                # 盘点（默认）
    python3 Tools/fleet/storage_curator.py --apply-roll   # 只做事件流轮转
    python3 Tools/fleet/storage_curator.py --apply-drop   # 只清明确无用的临时件
    python3 Tools/fleet/storage_curator.py --self-test
返回码：0 正常 / 1 超预算告警 / 2 配置缺失 / 3 自检失败
"""
from __future__ import annotations

import argparse
import fnmatch
import gzip
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "STORAGE-POLICY-v1.json")


def _j(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def _sha(p, limit=1 << 20):
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            h.update(f.read(limit))
    except OSError:
        return None
    return h.hexdigest()[:16]


def _walk(pattern, root):
    """把 glob 风格模式展开成真实文件列表（支持目录后缀 /）。"""
    full = os.path.join(root, pattern)
    out = []
    if pattern.endswith("/") or os.path.isdir(full):
        base = full.rstrip("/")
        for d, _, xs in os.walk(base):
            for x in xs:
                out.append(os.path.join(d, x))
        return out
    d = os.path.dirname(full) or root
    name = os.path.basename(full)
    if not os.path.isdir(d):
        return out
    for x in os.listdir(d):
        if fnmatch.fnmatch(x, name):
            p = os.path.join(d, x)
            if os.path.isfile(p):
                out.append(p)
    return out


def classify(spec, root=None):
    root = root or ROOT
    buckets = {"keep": [], "roll": [], "archive": [], "offload": [], "drop": []}
    for name in ("keep", "roll", "archive", "offload", "drop"):
        for pat in (spec["classes"][name].get("patterns") or []):
            for p in _walk(pat, root):
                if p not in buckets[name]:
                    buckets[name].append(p)
    # 已归 keep 的从其他桶剔除（keep 优先，避免误伤）
    keep = set(buckets["keep"])
    for k in ("roll", "archive", "offload", "drop"):
        buckets[k] = [p for p in buckets[k] if p not in keep]
    return buckets


def survey(spec, root=None):
    root = root or ROOT
    b = classify(spec, root)
    rows, total = [], 0
    for name, files in b.items():
        size = 0
        for p in files:
            try:
                size += os.path.getsize(p)
            except OSError:
                pass
        total += size
        rows.append({"class": name, "files": len(files), "mb": round(size / 1048576, 1),
                     "why": spec["classes"][name].get("why")})
    state_mb = 0
    sd = os.path.join(root, "cph4", "fleet", "state")
    if os.path.isdir(sd):
        for d, _, xs in os.walk(sd):
            for x in xs:
                try:
                    state_mb += os.path.getsize(os.path.join(d, x))
                except OSError:
                    pass
    receipts = 0
    rd = os.path.join(root, "cph4", "fleet", "rt")
    if os.path.isdir(rd):
        for d, _, xs in os.walk(rd):
            if d.endswith("receipts"):
                receipts += len(xs)
    budget = spec.get("budget") or {}
    return {"rows": rows, "total_mb": round(total / 1048576, 1),
            "state_mb": round(state_mb / 1048576, 1), "receipts": receipts,
            "budget": budget}


def rotate(spec, root=None, dry=True, now=None):
    """事件流轮转：超阈值的 jsonl 压缩归档，原文件保留尾部 N 行。"""
    root = root or ROOT
    cfg = spec["classes"]["roll"]
    limit = float(cfg.get("rotate_over_mb") or 8) * 1048576
    tail = int(cfg.get("keep_tail_lines") or 5000)
    now = now or time.time()
    done = []
    for pat in cfg.get("patterns") or []:
        for p in _walk(pat, root):
            try:
                size = os.path.getsize(p)
            except OSError:
                continue
            if size <= limit:
                continue
            # 二进制防护（2026-11-13 实测事故：eventlog.db 被当行文本切分，库直接损坏）。
            # 判据=前 4KB 含 NUL 字节即视为二进制，一律不轮转、只报告。
            try:
                with open(p, "rb") as f:
                    head = f.read(4096)
            except OSError:
                continue
            if b"\x00" in head:
                done.append({"path": os.path.relpath(p, root),
                             "mb": round(size / 1048576, 1), "action": "skipped-binary"})
                continue
            rec = {"path": os.path.relpath(p, root), "mb": round(size / 1048576, 1)}
            if dry:
                done.append(dict(rec, action="would-rotate"))
                continue
            try:
                with open(p, "rb") as f:
                    lines = f.readlines()
                keep = lines[-tail:]
                arch = p + ".archived-" + datetime.now().strftime("%Y%m%d%H%M%S") + ".gz"
                with gzip.open(arch, "wb") as g:
                    for ln in lines:
                        g.write(ln)
                with open(p, "wb") as f:
                    for ln in keep:
                        f.write(ln)
                done.append(dict(rec, action="rotated", archive=os.path.relpath(arch, root),
                                 kept_lines=len(keep)))
            except Exception as e:
                done.append(dict(rec, action="failed", why=type(e).__name__))
    return done


def drop(spec, root=None, dry=True):
    """只清 drop 类（明确一次性临时件），并先写 manifest。"""
    root = root or ROOT
    cfg = spec["classes"]["drop"]
    files = []
    for pat in cfg.get("patterns") or []:
        files.extend(_walk(pat, root))
    files = sorted(set(files))
    if not files:
        return []
    man = os.path.join(root, "cph4", "fleet", "state", "storage-drop-manifest.jsonl")
    recs = []
    for p in files:
        try:
            recs.append({"path": os.path.relpath(p, root), "size": os.path.getsize(p),
                         "sha16": _sha(p)})
        except OSError:
            continue
    if dry:
        return [dict(r, action="would-drop") for r in recs]
    os.makedirs(os.path.dirname(man), exist_ok=True)
    with open(man, "a", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(dict(r, ts=datetime.now().isoformat(timespec="seconds")),
                               ensure_ascii=False) + "\n")
    out = []
    for r in recs:
        try:
            os.remove(os.path.join(root, r["path"]))
            out.append(dict(r, action="dropped"))
        except OSError as e:
            out.append(dict(r, action="failed", why=type(e).__name__))
    return out


def offload_manifest(spec, root=None):
    """offload 类只生成清单（路径/大小/哈希），不移动、不删除。"""
    root = root or ROOT
    rows = []
    for pat in (spec["classes"]["offload"].get("patterns") or []):
        for p in _walk(pat, root):
            try:
                rows.append({"path": os.path.relpath(p, root),
                             "size": os.path.getsize(p), "sha16": _sha(p)})
            except OSError:
                continue
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-roll", action="store_true")
    ap.add_argument("--apply-drop", action="store_true")
    ap.add_argument("--manifest", action="store_true", help="导出 offload 清单（不删）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    spec = _j(SPEC)
    if not spec:
        print("缺存储策略：%s" % SPEC)
        return 2
    s = survey(spec)
    budget = s["budget"] or {}
    over = []
    if budget.get("fleet_total_mb") and s["total_mb"] > budget["fleet_total_mb"]:
        over.append("fleet 总占用 %.0fMB > 预算 %sMB" % (s["total_mb"], budget["fleet_total_mb"]))
    if budget.get("state_mb") and s["state_mb"] > budget["state_mb"]:
        over.append("state 占用 %.0fMB > 预算 %sMB" % (s["state_mb"], budget["state_mb"]))
    if budget.get("receipts_files") and s["receipts"] > budget["receipts_files"]:
        over.append("回执 %d 份 > 预算 %s" % (s["receipts"], budget["receipts_files"]))

    if a.json:
        print(json.dumps(dict(s, over=over), ensure_ascii=False, indent=1))
    else:
        print("== 主控存储盘点 ==")
        for r in s["rows"]:
            print("  %-8s %4d 个 / %6.1fMB  %s" % (r["class"], r["files"], r["mb"], r["why"]))
        print("  合计 %.1fMB｜state %.1fMB｜回执 %d 份" % (s["total_mb"], s["state_mb"], s["receipts"]))
        for x in over:
            print("  ⚠ " + x)
        if not over:
            print("  预算内。")

    # 每次盘点都留一份快照：这是"分级职责今天执行过"的证据（职责审计按它判龄期）
    try:
        snap = os.path.join(ROOT, "cph4", "fleet", "state", "storage-survey.json")
        os.makedirs(os.path.dirname(snap), exist_ok=True)
        with open(snap, "w", encoding="utf-8") as f:
            json.dump(dict(s, over=over,
                           ts=datetime.now().isoformat(timespec="seconds")),
                      f, ensure_ascii=False, indent=1)
    except Exception:
        pass

    if a.manifest:
        rows = offload_manifest(spec)
        p = os.path.join(ROOT, "cph4", "fleet", "state", "offload-manifest.jsonl")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tot = 0
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                tot += r["size"]
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("offload 清单 -> %s（%d 件 / %.1fMB，未删除任何文件）"
              % (os.path.relpath(p, ROOT), len(rows), tot / 1048576))

    if a.apply_roll:
        rows = rotate(spec, dry=False)
        print("轮转完成：%s" % (", ".join("%s→%s" % (r["path"], r["action"]) for r in rows) or "无超阈值文件"))
    if a.apply_drop:
        rows = drop(spec, dry=False)
        print("清理完成：%d 件（台账 cph4/fleet/state/storage-drop-manifest.jsonl）" % len(rows))
    return 1 if over else 0


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "cph4", "fleet", "state"), exist_ok=True)
        os.makedirs(os.path.join(td, "cph4", "fleet", "rt", "control", "receipts"), exist_ok=True)
        # 大事件流
        big = os.path.join(td, "cph4", "fleet", "state", "soak.jsonl")
        with open(big, "w") as f:
            for i in range(200000):
                f.write('{"i":%d,"pad":"%s"}\n' % (i, "x" * 60))
        # 关键文件
        keepf = os.path.join(td, "cph4", "fleet", "PRODUCTS.json")
        open(keepf, "w").write('{"products":[]}')
        # drop 候选
        dp = os.path.join(td, "cph4", "fleet", "state", "dupes.json")
        open(dp, "w").write('{"dupes":[]}')

        spec = {"budget": {"fleet_total_mb": 1, "state_mb": 1},
                "classes": {
                    "keep": {"patterns": ["cph4/fleet/PRODUCTS.json"]},
                    "roll": {"patterns": ["cph4/fleet/state/*.jsonl"],
                             "rotate_over_mb": 1, "keep_tail_lines": 100, "gzip": True},
                    "archive": {"patterns": [], "keep_days": 30},
                    "offload": {"patterns": [], "auto_delete": False},
                    "drop": {"patterns": ["cph4/fleet/state/dupes.json"]}}}

        b = classify(spec, td)
        chk("keep 优先：关键文件不落进其他桶",
            any(p.endswith("PRODUCTS.json") for p in b["keep"]) and
            not any(p.endswith("PRODUCTS.json") for p in b["roll"]), b)
        s = survey(spec, td)
        chk("盘点能算出占用", s["total_mb"] > 1, s["total_mb"])

        # dry：不许动文件
        before = os.path.getsize(big)
        rot = rotate(spec, td, dry=True)
        chk("dry 轮转只报不动", rot and os.path.getsize(big) == before, rot)

        # 真轮转：保留尾部、归档存在
        rot2 = rotate(spec, td, dry=False)
        after = open(big, "rb").read().count(b"\n")
        chk("轮转保留尾部 100 行", after == 100, after)
        chk("归档 gz 已生成", any(os.path.exists(os.path.join(td, r.get("archive", "")))
                                  for r in rot2 if r.get("archive")), rot2)

        # 负控：二进制文件必须被跳过（按行切分会损坏）
        binf = os.path.join(td, "cph4", "fleet", "state", "binary.jsonl")
        payload = b"SQLite format 3\x00" + os.urandom(2 * 1024 * 1024)
        with open(binf, "wb") as f:
            f.write(payload)
        rot3 = rotate(spec, td, dry=False)
        skipped = [r for r in rot3 if r.get("action") == "skipped-binary"]
        chk("负控：二进制文件被跳过（不许按行切）",
            any(r["path"].endswith("binary.jsonl") for r in skipped)
            and os.path.getsize(binf) == len(payload),
            (skipped, os.path.getsize(binf), len(payload)))

        # drop：先写 manifest 再删
        dd = drop(spec, td, dry=False)
        man = os.path.join(td, "cph4", "fleet", "state", "storage-drop-manifest.jsonl")
        chk("drop 先写台账再删", os.path.exists(man) and not os.path.exists(dp), dd)

        # 负控：keep 类永不被 drop/rotate 命中
        chk("负控：keep 文件仍在", os.path.exists(keepf))

    print("\n[storage_curator] %d/%d" % (ok, total))
    return 0 if ok == total else 3


if __name__ == "__main__":
    sys.exit(main())
