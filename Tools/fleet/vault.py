#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vault.py - 资产库：文件进盘、台账进 git、一眼知道能不能商用。

原则（2026-11-02 定）：
  1. 文件按指纹取名，不按路径 → 换机器、改名、重复版本全都消失；
  2. 台账是唯一权威（cph4/fleet/vault/index.jsonl），文件丢了台账还在；
  3. 视频自动出 480p 代理片，给 CEO 抽查用（不占带宽、不等人）；
  4. 没有登记的东西不算存在（闸 I4/I5 依赖这个）。

用法：
  python3 vault.py add <文件或目录> [--kind mp4|img|audio|other] [--license cleared|unknown]
                                   [--line bigstream-mv] [--note "..."]
  python3 vault.py list [--kind mp4] [--limit 20]
  python3 vault.py find <关键词>
  python3 vault.py verify            # 台账说有的，盘上还在不在
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
VAULT_DIR = os.path.join(FLEET, "vault")
INDEX = os.path.join(VAULT_DIR, "index.jsonl")
STORE_ROOT = "/Volumes/移动硬盘/FluxAssets"
FFMPEG = shutil.which("ffmpeg") or "/Users/junsheng.sun/bin/ffmpeg"

VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
AUDIO_EXT = (".wav", ".mp3", ".flac", ".m4a", ".aac")


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def kind_of(path, given=""):
    if given and given != "auto":
        return given
    e = os.path.splitext(path)[1].lower()
    if e in VIDEO_EXT:
        return "mp4"
    if e in IMG_EXT:
        return "img"
    if e in AUDIO_EXT:
        return "audio"
    return "other"


def load():
    out = []
    if os.path.exists(INDEX):
        for l in open(INDEX, encoding="utf-8"):
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except Exception:
                    pass
    return out


def save(rows):
    os.makedirs(VAULT_DIR, exist_ok=True)
    tmp = INDEX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, INDEX)


def proxy(sha, src, kind):
    """视频出一条 480p 代理片，专供抽查。失败不阻断入库。"""
    if kind != "mp4":
        return ""
    outdir = os.path.join(STORE_ROOT, "proxy")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "%s-480p.mp4" % sha[:16])
    if os.path.exists(out):
        return out
    try:
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src,
                        "-vf", "scale=-2:480", "-c:v", "libx264", "-crf", "28",
                        "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", out],
                       check=True, timeout=1800)
        return out
    except Exception:
        return ""


def add_one(path, kind, license_, line, note):
    sha = sha256(path)
    e = os.path.splitext(path)[1].lower()
    rel = os.path.join(sha[:2], sha + e)
    dst = os.path.join(STORE_ROOT, "store", rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        shutil.copy2(path, dst)
    prox = proxy(sha, dst, kind)
    return {"sha256": sha, "kind": kind, "path": dst, "bytes": os.path.getsize(dst),
            "license": license_, "line": line, "note": note,
            "proxy": prox, "created_at": datetime.now().isoformat(timespec="seconds"),
            "origin": path,
            "provenance": {"line": line or "unassigned", "stage": "vault:add",
                           "card": "manual", "inputs": []},
            "gate_status": "pending"}


def cmd_add(a):
    targets = []
    for p in a.path:
        if os.path.isdir(p):
            for dirpath, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
                for f in files:
                    fp = os.path.join(dirpath, f)
                    if os.path.splitext(f)[1].lower() in VIDEO_EXT + IMG_EXT + AUDIO_EXT:
                        targets.append(fp)
        elif os.path.isfile(p):
            targets.append(p)
    rows = load()
    have = {r["sha256"] for r in rows}
    added, skipped = 0, 0
    for p in targets:
        k = kind_of(p, a.kind)
        sha = sha256(p)
        if sha in have:
            skipped += 1
            continue
        rows.append(add_one(p, k, a.license, a.line, a.note))
        have.add(sha)
        added += 1
    save(rows)
    print("入库 %d 个，跳过重复 %d 个（台账共 %d 条）" % (added, skipped, len(rows)))
    return 0


def cmd_list(a):
    rows = load()
    if a.kind:
        rows = [r for r in rows if r.get("kind") == a.kind]
    for r in rows[-a.limit:]:
        print("%-10s %-12s %-8s %s" % (r["sha256"][:10], r.get("kind"),
                                       "已清" if r.get("license") == "cleared" else "授权未知",
                                       (r.get("origin") or r.get("path"))[-60:]))
    print("共 %d 条" % len(rows))
    return 0


def cmd_find(a):
    rows = [r for r in load() if a.q.lower() in json.dumps(r, ensure_ascii=False).lower()]
    for r in rows[:30]:
        print("%s  %s  %s" % (r["sha256"][:12], r.get("kind"), r.get("path")))
    print("命中 %d 条" % len(rows))
    return 0


def _volume_of(path):
    m = re.match(r"^/Volumes/([^/]+)/", str(path or ""))
    return m.group(1) if m else None


def cmd_verify(a):
    rows = load()
    # 2026-11-07 实锚：移动硬盘没插时，旧口径把这 651 条全报「丢失」——「盘没挂载」
    # 和「资产真的没了」是两件事，混报一次就没人再信这个红。先判卷在不在，
    # 不在就明确说「不可判定」，赋 rc=3（UNREACHABLE），不冒充丢失。
    unmounted = sorted({v for v in (_volume_of(r.get("path")) for r in rows)
                        if v and not os.path.isdir("/Volumes/%s" % v)})
    if unmounted:
        print("台账 %d 条，卷未挂载：%s ⇒ 不可判定（不是丢失）"
              % (len(rows), "、".join("/Volumes/%s" % v for v in unmounted)))
        return 3
    missing = [r for r in rows if not os.path.exists(r.get("path") or "")]
    for r in missing[:20]:
        print("丢失：%s  %s" % (r["sha256"][:12], r.get("path")))
    print("台账 %d 条，盘上缺失 %d 条" % (len(rows), len(missing)))
    return 0 if not missing else 2


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    ad = sub.add_parser("add")
    ad.add_argument("path", nargs="+")
    ad.add_argument("--kind", default="auto")
    ad.add_argument("--license", default="unknown", choices=["cleared", "unknown"])
    ad.add_argument("--line", default="")
    ad.add_argument("--note", default="")
    ls = sub.add_parser("list")
    ls.add_argument("--kind", default="")
    ls.add_argument("--limit", type=int, default=20)
    fd = sub.add_parser("find")
    fd.add_argument("q")
    sub.add_parser("verify")
    a = ap.parse_args(argv)
    if a.cmd == "add":
        return cmd_add(a)
    if a.cmd == "list":
        return cmd_list(a)
    if a.cmd == "find":
        return cmd_find(a)
    if a.cmd == "verify":
        return cmd_verify(a)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))