#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""review_packet.py - one page the director can sign from, built from evidence on disk.

Why: the MV line keeps stalling because the director seat is asked to "read the film"
with no packet. This turns the evidence that already exists (gate JSONs, conform,
harvest verdicts, boards) into a single dated markdown page, so signing is a read,
not an archaeology dig. Deterministic: no LLM, no network.

Usage:
  python Tools/fleet/review_packet.py --line kn  --root K:\\Fluxgroup\\FluxGroup
  python Tools/fleet/review_packet.py --line mv  --root ...
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime

LINE_SPECS = {
    "kn": {
        "title": "《可爱女人》KN PACK-A 复核卷",
        "dir": "media/mv-album-001-jay",
        "film": "media/mv-album-001-jay/assembly-packA/KN-PACKA-CONFORM-v1-c2171.mp4",
        "glob_gate": "media/mv-album-001-jay/logs/kn-film-gate-*.json",
        "glob_extra": [
            "cph4/fleet/mv-album-001-jay/KN21-HARVEST-*.json",
            "cph4/fleet/mv-album-001-jay/KN-*-RECEIPT-*.md",
            "cph4/fleet/mv-album-001-jay/DIRECTOR-REVIEW-KN-*.md",
        ],
        "boards": "media/mv-album-001-jay/qc-boards/KN-*.jpg",
    },
    "mv": {
        "title": "MV 41 曲 新流程卷",
        "dir": "cph4/fleet/mv-album-001-jay",
        "film": "",
        "glob_gate": "cph4/fleet/mv-album-001-jay/PROMPT-GATE-*.md",
        "glob_extra": [
            "cph4/fleet/mv-album-001-jay/*-D2-*.md",
            "cph4/fleet/mv-album-001-jay/*-立意案-*.md",
            "cph4/fleet/mv-album-001-jay/ALBUM-NEW-PROCESS-COMPLIANCE-*.md",
        ],
        "boards": "",
    },
}


def newest(pattern, root):
    hits = sorted(glob.glob(os.path.join(root, pattern)), key=os.path.getmtime, reverse=True)
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", required=True, choices=sorted(LINE_SPECS))
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    spec = LINE_SPECS[a.line]
    out = a.out or os.path.join(root, "cph4", "fleet", "queue-receipts",
                                "review-packet-%s-%s.md" % (a.line, datetime.now().strftime("%Y%m%d")))
    os.makedirs(os.path.dirname(out), exist_ok=True)

    L = []
    L.append("# %s" % spec["title"])
    L.append("")
    L.append("- 生成：%s · 机：bm-c · 脚本：Tools/fleet/review_packet.py" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    L.append("- 用途：导演席一次读完即可 PASS/REVISE，不必逐档翻找。")
    L.append("")

    film = os.path.join(root, spec["film"]) if spec["film"] else None
    L.append("## 一、成片")
    if film and os.path.exists(film):
        size_mb = os.path.getsize(film) / (1024.0 * 1024)
        L.append("- `%s`（%.2f MB，mtime %s）" % (
            film, size_mb, datetime.fromtimestamp(os.path.getmtime(film)).strftime("%Y-%m-%d %H:%M")))
    elif spec["film"]:
        L.append("- **缺件**：`%s` 不在盘上" % film)
    else:
        L.append("- 本卷为剧本/分镜面，无成片。")
    L.append("")

    L.append("## 二、机器闸（最近一次）")
    gate = newest(spec["glob_gate"], root)
    if gate:
        try:
            g = json.load(open(gate, encoding="utf-8"))
            keys = ["verdict", "frames", "dup_pairs", "duplicate_pairs", "luma_min", "audio_sec", "res"]
            got = {k: g.get(k) for k in keys if k in g}
            L.append("- `%s`" % os.path.relpath(gate, root))
            L.append("- %s" % (json.dumps(got, ensure_ascii=False) if got else "（见文件正文）"))
        except Exception:
            L.append("- `%s`（非 JSON 或无结构，需人读）" % os.path.relpath(gate, root))
    else:
        L.append("- 无闸档：**不可签**，先跑闸。")
    L.append("")

    L.append("## 三、证据件")
    found = 0
    for pat in spec["glob_extra"]:
        for p in sorted(glob.glob(os.path.join(root, pat)), key=os.path.getmtime, reverse=True)[:3]:
            L.append("- `%s`" % os.path.relpath(p, root))
            found += 1
    if not found:
        L.append("- 无")
    L.append("")

    if spec["boards"]:
        L.append("## 四、对照板")
        boards = sorted(glob.glob(os.path.join(root, spec["boards"])), key=os.path.getmtime, reverse=True)[:4]
        for b in boards:
            L.append("- `%s`" % os.path.relpath(b, root))
        if not boards:
            L.append("- 无")
        L.append("")

    L.append("## 五、签字位")
    L.append("")
    L.append("| 项 | 结论 | 备注 |")
    L.append("|---|---|---|")
    L.append("| 画面能否交付 | PASS / REVISE | |")
    L.append("| 叙事与表演是否成立 | PASS / REVISE | |")
    L.append("| 已知瑕疵是否可接受 | 接受 / 重烧 | |")
    L.append("")
    L.append("> 签完落 `DIRECTOR-REVIEW-<线>-<日期>.md`，verdict ∈ {PASS, REVISE}；REVISE 须逐条给可执行改法。")

    open(out, "w", encoding="utf-8", newline="").write("\n".join(L) + "\n")
    print("PACKET %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())