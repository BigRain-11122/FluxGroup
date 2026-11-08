#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资产与经验库归集器（传家宝 bm-c 的常设活）。

CEO 2026-11-03 令：实际生产完成的东西和形成的底层技术（音色/工作流/技能等）
都要形成经验和资产库，由传家宝机器做整理归集与 git 备份。

本工具只做三件确定性的事，不做判断、不调模型：
  1. 扫盘：把六类东西数清（技能 / 音色 / 工作流 / 经验台账 / 产物 / 内容寻址资产）
  2. 对账：已产出但没登记的、登记了但文件不在的，逐条列出
  3. 落盘：机读索引 cph4/fleet/lib/ASSET-INDEX.json + 人读一页 LIB-STATUS.md

为什么归集必须是"索引+指针"而不是"搬文件"：
  二进制（母版/LoRA/音频）在 media/ 与外置盘，入 git 会撑爆仓；能进 git 的是
  sha256+路径+血缘。git 备份由主控脉的 git_publish 负责（只跳过 media/gaming/quant），
  所以索引放 cph4/ 就等于自动进备份。

用法：
  python3 Tools/fleet/lib_consolidate.py            # 扫盘 + 写索引 + 打一页
  python3 Tools/fleet/lib_consolidate.py --check    # 只报缺口，rc=2 有缺口
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
OUTDIR = os.path.join(FLEET, "lib")


def rd(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def newest(paths):
    t = 0
    for p in paths:
        try:
            t = max(t, os.path.getmtime(p))
        except OSError:
            pass
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(t)) if t else "-"


def scan_skills():
    files = glob.glob(os.path.join(ROOT, "cph4", "skills", "**", "SKILL.md"), recursive=True)
    lv = {}
    try:
        d = json.load(open(os.path.join(FLEET, "state", "skills-check.json"), encoding="utf-8"))
        for r in d.get("rows") or []:
            lv[r.get("level") or "?"] = lv.get(r.get("level") or "?", 0) + 1
    except Exception:
        pass
    eval_specs = glob.glob(os.path.join(ROOT, "cph4", "skills", "*", "eval.json"))
    return {"count": len(files), "levels": lv, "with_eval": len(eval_specs),
            "newest": newest(files)}


def scan_voice():
    dirs = ["cph4/fleet/voicebank", "media/asset/voice", "media/asset/inbox"]
    files, blocked = [], 0
    for d in dirs:
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        for dirpath, _, names in os.walk(p):
            for n in names:
                if n.lower().endswith((".wav", ".mp3", ".flac", ".m4a")):
                    files.append(os.path.join(dirpath, n))
    receipts = glob.glob(os.path.join(FLEET, "queue-receipts", "asset-*voice*"))
    for r in receipts:
        try:
            if json.load(open(r, encoding="utf-8")).get("status") == "BLOCKED":
                blocked += 1
        except Exception:
            pass
    return {"audio_files": len(files), "blocked_receipts": blocked,
            "dirs_present": [d for d in dirs if os.path.isdir(os.path.join(ROOT, d))],
            "newest": newest(files) if files else "-"}


def scan_workflow():
    lines, stages = [], 0
    for p in glob.glob(os.path.join(FLEET, "ri", "*", "lines", "*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        st = d.get("stages") or []
        stages += len(st)
        lines.append({"line": d.get("line") or os.path.basename(p), "stages": len(st),
                      "parallel": bool(d.get("parallel"))})
    recipes = [os.path.basename(p) for p in glob.glob(os.path.join(FLEET, "products", "*.yaml"))]
    return {"line_tables": len(lines), "stage_rows": stages, "recipes": recipes,
            "detail": sorted(lines, key=lambda x: str(x["line"]))}


def scan_experience():
    pats = ["cph4/fleet/*LEDGER*", "cph4/fleet/*/*LEDGER*", "cph4/fleet/*/canon/*.md",
            "cph4/fleet/asset-lib-v1/*.md"]
    files = []
    for pat in pats:
        files += glob.glob(os.path.join(ROOT, pat))
    files = sorted(set(files))
    cases = sum(len(re.findall(r"^#{2,3} ", rd(p), re.M)) for p in files)
    return {"docs": len(files), "sections": cases,
            "top": [os.path.relpath(p, ROOT) for p in files[:8]], "newest": newest(files)}


def scan_vault():
    p = os.path.join(FLEET, "vault", "index.jsonl")
    rows, kinds, missing = [], {}, 0
    for line in rd(p).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        rows.append(r)
        kinds[r.get("kind") or "?"] = kinds.get(r.get("kind") or "?", 0) + 1
        path = r.get("path") or ""
        if path and not os.path.exists(path):
            missing += 1
    return {"entries": len(rows), "kinds": kinds, "missing_on_disk": missing,
            "index": os.path.relpath(p, ROOT)}


def scan_produced():
    """已产出的交付物：DONE 卡里有交付物路径的，逐条判在不在盘。"""
    q = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
    total = exist = 0
    absent = []
    for line in rd(q).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("state") != "DONE":
            continue
        dp = r.get("deliverable") or ""
        if not dp:
            continue
        total += 1
        full = dp if os.path.isabs(dp) else os.path.join(ROOT, dp)
        if os.path.exists(full):
            exist += 1
        else:
            absent.append({"id": r.get("id"), "deliverable": dp})
    return {"done_with_deliverable": total, "on_disk": exist,
            "absent": absent[:20], "absent_count": len(absent)}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--receipt", default="",
                    help="额外写一份带日期的回执（给机队卡用，避免固定路径被'产物已在盘'跳过）")
    a = ap.parse_args(argv)
    data = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "owner": "bm-c（传家宝）· 归集与 git 备份",
        "skills": scan_skills(),
        "voice": scan_voice(),
        "workflow": scan_workflow(),
        "experience": scan_experience(),
        "vault": scan_vault(),
        "produced": scan_produced(),
    }
    # 缺口判据（只有这三条算缺口，其余是统计）
    gaps = []
    if data["produced"]["absent_count"]:
        gaps.append("%d 张 DONE 卡的交产物不在盘" % data["produced"]["absent_count"])
    if data["vault"]["missing_on_disk"]:
        gaps.append("%d 条 vault 登记指向不存在的文件" % data["vault"]["missing_on_disk"])
    if data["voice"]["audio_files"] == 0:
        gaps.append("音色库 0 个音频文件（等投料，不算故障但不算资产）")
    data["gaps"] = gaps
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "ASSET-INDEX.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    md = ["# 资产与经验库状态（%s）" % data["ts"], "",
          "> 由 Tools/fleet/lib_consolidate.py 生成，禁手改。索引进 git，二进制留盘。", "",
          "| 面 | 数 | 最新 |", "|---|---|---|",
          "| 技能 | %d（A%d/B%d/冻结%d/外部%d/暂停%d） | %s |" % (
              data["skills"]["count"],
              data["skills"]["levels"].get("A", 0), data["skills"]["levels"].get("B", 0),
              data["skills"]["levels"].get("frozen", 0), data["skills"]["levels"].get("external", 0),
              data["skills"]["levels"].get("parked", 0), data["skills"]["newest"]),
          "| 技能成对评测 | %d 份 eval | - |" % data["skills"]["with_eval"],
          "| 音色 | %d 个音频（BLOCKED 回执 %d） | %s |" % (
              data["voice"]["audio_files"], data["voice"]["blocked_receipts"], data["voice"]["newest"]),
          "| 工作流 | %d 张工序表 / %d 段 / 配方 %d | - |" % (
              data["workflow"]["line_tables"], data["workflow"]["stage_rows"],
              len(data["workflow"]["recipes"])),
          "| 经验台账 | %d 份 / %d 节 | %s |" % (
              data["experience"]["docs"], data["experience"]["sections"], data["experience"]["newest"]),
          "| 内容寻址资产 | %d 条（缺盘 %d） | - |" % (
              data["vault"]["entries"], data["vault"]["missing_on_disk"]),
          "| 已产出交付物 | %d/%d 在盘 | - |" % (
              data["produced"]["on_disk"], data["produced"]["done_with_deliverable"]),
          "", "## 缺口", ""]
    md += (["- " + g for g in gaps] if gaps else ["- 无"])
    with open(os.path.join(OUTDIR, "LIB-STATUS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("skills=%d voice=%d flows=%d/%d docs=%d vault=%d produced=%d/%d gaps=%d" % (
        data["skills"]["count"], data["voice"]["audio_files"],
        data["workflow"]["line_tables"], data["workflow"]["stage_rows"],
        data["experience"]["docs"], data["vault"]["entries"],
        data["produced"]["on_disk"], data["produced"]["done_with_deliverable"], len(gaps)))
    for g in gaps:
        print("  GAP", g)
    print("wrote cph4/fleet/lib/ASSET-INDEX.json + LIB-STATUS.md")
    if a.receipt:
        rp = a.receipt if os.path.isabs(a.receipt) else os.path.join(ROOT, a.receipt)
        os.makedirs(os.path.dirname(rp), exist_ok=True)
        with open(rp, "w", encoding="utf-8") as f:
            json.dump({"rc": 2 if gaps else 0, "verdict": "GAPS" if gaps else "PASS",
                       "error_class": "E-BLOCKED-INPUT" if (a.check and gaps) else None,
                       "summary": data, "gaps": gaps}, f, ensure_ascii=False, indent=1)
        print("receipt", os.path.relpath(rp, ROOT))
    return 2 if (a.check and gaps) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))