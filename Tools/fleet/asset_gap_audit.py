#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_gap_audit.py - 素材库 P0 缺口审计（按台账 class 计数，只认已入库）。

判据（2026-11-19 修）：缺口 = p0 - 已入库。已入库 = 台账里 class==该类、且盘上真身可达
（vault.resolve() 成功）的行。incoming 里的"待入"不再抵扣缺口——那是假绿来源：
10 条 bgm 躺 incoming 从未入库，旧公式却报「达标」。

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


def count_cls(cls, rule, rows):
    """按台账数"已入库"：class 命中 + 真身可达 + 扩展名合规。

    目录型类别（characters/styles/voices/typography）以 origin 所在目录为一个单元，
    单元内文件数 ≥ min_per_dir 才算 1 个单位——沿用旧口径，不降低门槛。
    """
    units = {}
    n = 0
    for r in rows:
        if (r.get("class") or "") != cls:
            continue
        p = _vault.resolve(r)
        if not p or not p.lower().endswith(rule["ext"]):
            continue
        n += 1
        if rule["dir"]:
            u = os.path.basename(os.path.dirname(r.get("origin") or p))
            units[u] = units.get(u, 0) + 1
    if rule["dir"]:
        return sum(1 for v in units.values() if v >= rule["min_per_dir"])
    return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=OUT)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(TARGETS):
        print("[gap] 缺目标文件 %s（rc=2）" % TARGETS)
        return 2
    cfg = json.load(open(TARGETS, encoding="utf-8"))
    ledger = [r for r in _vault.load() if r.get("status") != "retired"]
    rows, gaps = [], []
    for cls, spec in (cfg.get("classes") or {}).items():
        rule = RULES.get(cls)
        if not rule:
            continue
        p0 = int(spec.get("p0") or 0)
        have = count_cls(cls, rule, ledger)
        gap = max(0, p0 - have)
        rows.append({"class": cls, "name": spec.get("name"), "p0": p0,
                     "have": have, "gap": gap})
        if gap:
            gaps.append(cls)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "classes": rows, "gap_classes": gaps,
           "p0_done": sum(1 for r in rows if r["gap"] == 0), "p0_total": len(rows),
           "basis": "ledger.class + vault.resolve(); incoming 不抵扣缺口",
           "verdict": "PASS" if not gaps else "GAPS"}
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    if not a.quiet:
        print("[gap] P0 达标 %d/%d（按台账 class 计数，incoming 不抵扣）"
              % (rec["p0_done"], rec["p0_total"]))
        for r in rows:
            print("  %s%-12s 目标%-4d 已入%-4d 缺%-4d %s"
                  % ("OK  " if r["gap"] == 0 else "GAP ", r["class"], r["p0"],
                     r["have"], r["gap"], r["name"] or ""))
        if gaps:
            print("[gap] 缺口类：%s" % ", ".join(gaps))
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())