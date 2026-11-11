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
STORE_CFG = os.path.join(FLEET, "ASSET-STORE.json")


def store_roots():
    """资产库根按 ASSET-STORE.json 的顺序解析。以前这里写死 /Volumes/移动硬盘/FluxAssets，
    盘一拔整个资产面（台账 651 条 + asset_share 服务）一起失效（2026-11-07 实锚）。"""
    try:
        cfg = json.load(open(STORE_CFG, encoding="utf-8"))
        rs = [os.path.expanduser(str(r.get("path"))) for r in (cfg.get("roots") or [])]
    except Exception:
        rs = []
    return rs or [os.path.expanduser("~/FluxAssets")]


STORE_ROOT = store_roots()[0]
REL_RE = re.compile(r"/FluxAssets/(store/.+)$")


def rel_of(path):
    """绝对路径 → 相对路径 store/<xx>/<file>（换根后照样能认）。"""
    m = REL_RE.search(str(path or "").replace("\\", "/"))
    return m.group(1) if m else None


def resolve(row):
    """按 roots 顺序找这条台账的真身；找不到返回 None。"""
    rel = row.get("store") or rel_of(row.get("path"))
    if not rel:
        return None
    for r in store_roots():
        p = os.path.join(r, rel)
        if os.path.exists(p):
            return p
    return None
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
    return {"sha256": sha, "kind": kind, "path": dst, "store": rel_of(dst) or
            os.path.join("store", rel), "bytes": os.path.getsize(dst),
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
    roots = store_roots()
    found, rebuildable, missing, snapshots = [], [], [], []
    for r in rows:
        p = resolve(r)
        if p:
            found.append((r, p))
            continue
        if r.get("snapshot_only"):
            snapshots.append(r)
            continue
        o = r.get("origin") or ""
        if o and (os.path.exists(os.path.join(ROOT, o)) or os.path.exists(o)):
            rebuildable.append(r)
        else:
            missing.append(r)
    print("台账 %d 条 · 可达 %d（根 %s）· 可从 origin 重建 %d · 历史快照 %d · 真缺失 %d"
          % (len(rows), len(found), "、".join(roots), len(rebuildable),
             len(snapshots), len(missing)))
    by_root = {}
    for r, p in found:
        by_root[os.path.dirname(os.path.dirname(os.path.dirname(p)))] = \
            by_root.get(os.path.dirname(os.path.dirname(os.path.dirname(p))), 0) + 1
    for k, v in sorted(by_root.items(), key=lambda kv: -kv[1]):
        print("  根 %s：%d 条" % (k, v))
    for r in missing[:10]:
        print("  缺失：%s  %s" % (r["sha256"][:12], r.get("path")))
    rc = 2 if missing else (3 if rebuildable else 0)
    if rc == 3:
        # 有派生物没落地：不是丢失，但也没到"齐"，用 rc=3 与"不可判定"区分开
        print("  提示：跑 `vault.py rebuild` 把这 %d 条从仓内 origin 落地到 primary 根"
              % len(rebuildable))
    out = getattr(a, "json", "")
    if out:
        report = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "roots": roots, "rows": len(rows), "reachable": len(found),
            "rebuildable": len(rebuildable), "snapshots": len(snapshots),
            "missing": [{"sha256": r.get("sha256"), "path": r.get("path")}
                        for r in missing],
            "missing_count": len(missing),
            "by_root": {k: v for k, v in by_root.items()},
            "rc": rc,
        }
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print("  回执：%s" % out)
    return rc


def cmd_rebuild(a):
    """从 origin（仓内原始路径）把缺件落地到 primary 根，校验 sha 一致才写入。"""
    rows = load()
    primary = store_roots()[0]
    made = skipped = failed = drifted = 0
    changed = False
    for r in rows:
        if resolve(r):
            skipped += 1
            continue
        o = r.get("origin") or ""
        src = o if os.path.isabs(o) else os.path.join(ROOT, o)
        if not o or not os.path.exists(src):
            failed += 1
            continue
        h = sha256(src)
        if h != r.get("sha256"):
            # origin 是「活的文档」，入库后又被改过：仓里这份是新版，台账记的是旧快照。
            # 不是丢失，也不能拿新版冒充旧版——标成历史快照，只存在于当时的存储根。
            r["snapshot_only"] = True
            r["snapshot_note"] = ("origin 内容已漂移（现 sha %s），本行是入库时快照" % h[:12])
            changed = True
            drifted += 1
            continue
        ext = r.get("store") or rel_of(r.get("path")) or ""
        rel = ext if ext.startswith("store/") else os.path.join(
            "store", h[:2], h + os.path.splitext(src)[1].lower())
        dst = os.path.join(primary, rel)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        r["store"] = rel
        r["path"] = dst
        r["rebuilt_at"] = datetime.now().isoformat(timespec="seconds")
        changed = True
        made += 1
    if changed and not a.dry:
        save(rows)
    print("重建 %d 条（已可达跳过 %d，历史快照 %d，无法重建 %d）→ 根 %s"
          % (made, skipped, drifted, failed, primary))
    return 0 if not failed else 2


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
    vf = sub.add_parser("verify")
    vf.add_argument("--json", default="", help="把核验结果写成 JSON 回执到该路径")
    rb = sub.add_parser("rebuild")
    rb.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "add":
        return cmd_add(a)
    if a.cmd == "list":
        return cmd_list(a)
    if a.cmd == "find":
        return cmd_find(a)
    if a.cmd == "verify":
        return cmd_verify(a)
    if a.cmd == "rebuild":
        return cmd_rebuild(a)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


# ---------------------------------------------------------------- 兼容口（2026-11-11）
# 背景：为了清掉 5 处写死的 /Volumes 默认值，artifact_status / asset_gap_audit /
# asset_incoming_verify / demand_gen / mac_farm 统一走这三个函数。它们必须先看
# ASSET-VAULT.json（新的落点正身），再退到 ASSET-STORE 的 roots，最后才是空。
def root(cfg_path=None):
    """素材库根：FLUX_VAULT > ASSET-VAULT.vault.path > ASSET-STORE 第一根 > ""。"""
    v = os.environ.get("FLUX_VAULT")
    if v:
        return v.rstrip("/")
    try:
        with open(cfg_path or os.path.join(FLEET, "ASSET-VAULT.json"), encoding="utf-8-sig") as f:
            p = ((json.load(f) or {}).get("vault") or {}).get("path")
        if p:
            return str(p).rstrip("/")
    except Exception:
        pass
    rs = store_roots()
    return rs[0].rstrip("/") if rs else ""


def require(what="素材库", cfg_path=None):
    """拿不到根就明确报错：绝不回落到某个写死的 /Volumes（旧盘 2026-11-11 已清空）。"""
    p = root(cfg_path)
    if p:
        return p
    raise SystemExit(
        "未配置%s：设环境变量 FLUX_VAULT，或在 cph4/fleet/ASSET-VAULT.json 写 vault.path。"
        "移动盘已于 2026-11-11 清空退出，不再回落到 /Volumes。" % what)


def sub(*parts, cfg_path=None):
    p = root(cfg_path)
    return os.path.join(p, *parts) if p else ""
