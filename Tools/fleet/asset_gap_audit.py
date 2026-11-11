#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_gap_audit.py - 素材库 P0 缺口审计（只数盘上真实文件，不认台账行数）。

输出 cph4/fleet/state/asset-gap.json，供 demand_gen.py 造采集卡。
Exit: 0 全部达 P0；1 有缺口；2 缺目标文件。
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGETS = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1", "LIBRARY-TARGETS.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault as _vault
VAULT = _vault.root()          # 未配置=""; 下面扫描前明确报错
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "asset-gap.json")
IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
VID = (".mp4", ".mov", ".mkv", ".webm")
AUD = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aif", ".aiff")
FONT = (".otf", ".ttf", ".woff", ".woff2")

RULES = {
    "characters": {"ext": IMG, "dir": True, "min_per_dir": 6},
    "scenes": {"ext": IMG + VID, "dir": False},
    "props": {"ext": IMG, "dir": False},
    "motions": {"ext": VID, "dir": False},
    "transitions": {"ext": VID, "dir": False},
    "styles": {"ext": IMG + (".cube",), "dir": True, "min_per_dir": 3},
    "voices": {"ext": AUD, "dir": True, "min_per_dir": 3},
    "audio-sfx": {"ext": AUD, "dir": False},
    "audio-bgm": {"ext": AUD, "dir": False},
    "typography": {"ext": FONT, "dir": True, "min_per_dir": 1},
}


def files_of(base):
    out = []
    if not os.path.isdir(base):
        return out
    for d, _s, fs in os.walk(base):
        for n in fs:
            p = os.path.join(d, n)
            try:
                if os.path.getsize(p) > 0:
                    out.append(p)
            except OSError:
                pass
    return out


def count_cls(cls, rule):
    bases = [os.path.join(ROOT, "media", "asset", cls),
             os.path.join(VAULT, "store", cls),
             os.path.join(VAULT, "incoming", cls)]
    stock = pending = 0
    for i, base in enumerate(bases):
        fs = [p for p in files_of(base) if p.lower().endswith(rule["ext"])]
        if rule["dir"]:
            units = {}
            for p in fs:
                u = os.path.relpath(p, base).split(os.sep)[0]
                units[u] = units.get(u, 0) + 1
            n = sum(1 for v in units.values() if v >= rule["min_per_dir"])
        else:
            n = len(fs)
        if i == 0:
            stock += n
        else:
            pending += n
    return stock, pending


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=OUT)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(TARGETS):
        print("[gap] 缺目标文件 %s（rc=2）" % TARGETS)
        return 2
    cfg = json.load(open(TARGETS, encoding="utf-8"))
    rows, gaps = [], []
    for cls, spec in (cfg.get("classes") or {}).items():
        rule = RULES.get(cls)
        if not rule:
            continue
        p0 = int(spec.get("p0") or 0)
        have, pending = count_cls(cls, rule)
        gap = max(0, p0 - have - pending)
        rows.append({"class": cls, "name": spec.get("name"), "p0": p0,
                     "have": have, "pending": pending, "gap": gap})
        if gap:
            gaps.append(cls)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "classes": rows, "gap_classes": gaps,
           "p0_done": sum(1 for r in rows if r["gap"] == 0), "p0_total": len(rows),
           "verdict": "PASS" if not gaps else "GAPS"}
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    if not a.quiet:
        print("[gap] P0 达标 %d/%d" % (rec["p0_done"], rec["p0_total"]))
        for r in rows:
            print("  %s%-12s 目标%-4d 已入%-4d 待入%-4d 缺%-4d %s"
                  % ("OK  " if r["gap"] == 0 else "GAP ", r["class"], r["p0"],
                     r["have"], r["pending"], r["gap"], r["name"] or ""))
        if gaps:
            print("[gap] 缺口类：%s" % ", ".join(gaps))
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())