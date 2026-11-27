#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demand_gen.py - 需求生成器：把「盘上可机器判定的缺口」直接变成卡。

为什么（CEO 2026-11-05「如何保障一直能正常供给任务，不仅自己满负荷，机队也满负荷」）：
  实测主控派单返回 supply=[] —— backlog 已被跑空（DONE 212 / CANCELLED 347），
  只剩 6 条候选。缺的不是机器，也不是造卡器，而是**没有人持续把缺口翻译成活**。
  supply_batch 只覆盖软著/提审/资产三类；这里补上其余持续存在的需求源。

每条需求源都必须：输入可判（在盘上）、产物路径确定、可重复运行不重复造卡。

用法：
  python3 Tools/fleet/demand_gen.py [--dry] [--max-per-source 20]
Exit: 0 有产出或有充足存量；1 全部源都空且无存量；2 源本身不可判（缺工具/缺输入）
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault as _vault
VAULT = _vault.root()          # 未配置=""，依赖库根的卡会被跳过而不是指向死盘
IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def rows(path):
    out = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def active_deliverables():
    """活跃卡（RUNNING/OPEN/READY）占用的 deliverable，用于去重。"""
    out = set()
    for p in (QUEUE, BACKLOG):
        for r in rows(p):
            if str(r.get("state", "")).upper() in ("RUNNING", "OPEN", "READY"):
                d = r.get("deliverable")
                if d:
                    out.add(str(d))
    return out


def known_ids():
    ids = set()
    for p in (QUEUE, BACKLOG):
        for r in rows(p):
            if r.get("id"):
                ids.add(str(r["id"]))
    return ids


def walk(base, exts):
    out = []
    if not os.path.isdir(base):
        return out
    for d, _s, files in os.walk(base):
        for n in files:
            if n.lower().endswith(exts):
                out.append(os.path.join(d, n))
    return out


# ---------- 需求源 ----------
def src_caption(vault):
    """打标缺口：store 里有图但没有同名 .txt。产物=边车 .txt。"""
    items = []
    store = os.path.join(vault, "store")
    for p in walk(store, IMG):
        txt = os.path.splitext(p)[0] + ".txt"
        if not os.path.exists(txt):
            items.append({"rel": os.path.relpath(p, vault), "abs": p})
    return items


def src_asset_gap(vault=None):
    """素材库 P0 缺口类（缺的类别各出一张采集卡）。"""
    import subprocess
    tool = os.path.join(HERE, "asset_gap_audit.py")
    if not os.path.isfile(tool):
        return []
    try:
        p = subprocess.run([sys.executable, tool, "--quiet"], capture_output=True, text=True, timeout=180)
        data = json.load(open(os.path.join(F, "state", "asset-gap.json"), encoding="utf-8"))
    except Exception:
        return []
    return [{"class": r["class"], "gap": r["gap"], "p0": r["p0"]}
            for r in data.get("classes", []) if r.get("gap")]


def src_media_proxy():
    """代理缺口：media 下有源视频但没有 -720p 代理。"""
    base = os.path.join(ROOT, "media")
    out = []
    for p in walk(base, (".mp4", ".mov")):
        if "review-720p" in p:
            continue
        stem = os.path.splitext(os.path.basename(p))[0]
        cand = os.path.join(base, "review-720p", stem + "-720p.mp4")
        if not os.path.exists(cand):
            out.append({"src": os.path.relpath(p, ROOT), "dst": os.path.relpath(cand, ROOT)})
    return out


def src_game_docs():
    """提审缺口：产品目录缺隐私政策就派一张（标准件，机器可生成）。"""
    base = os.path.join(ROOT, "软著申请材料")
    out = []
    if not os.path.isdir(base):
        return out
    for n in sorted(os.listdir(base)):
        # 排除归档/临时目录：实测车道会挑到「已封存_xxx」「_报审提交区」这类无效活
        if n.startswith("_") or "封存" in n or "提交区" in n or "旧" in n:
            continue
        d = os.path.join(base, n)
        if not os.path.isdir(d):
            continue
        if not os.path.exists(os.path.join(d, "privacy-policy.md")):
            out.append({"product": n})
    return out


def src_bm_a_preview(vault=None):
    """bm-a 装配：竖屏素材已齐 → 拼一条 30s 预览片（真产物，不是清单）。"""
    vdir = os.path.join(vault, "incoming", "motions-vertical")
    out = os.path.join(vault, "incoming", "preview-30s.mp4")
    if not os.path.isdir(vdir) or os.path.exists(out):
        return []
    clips = sorted(f for f in os.listdir(vdir) if f.endswith(".mp4"))[:6]
    if not clips:
        return []
    return [{"clips": clips, "out": out, "dir": vdir}]


def src_bm_b_asr():
    """bm-b 声音：成片没有字幕就出字幕（输入在仓内，无需外拉）。"""
    base = os.path.join(ROOT, "media", "drama-out")
    out = []
    if not os.path.isdir(base):
        return out
    for n in sorted(os.listdir(base)):
        if not n.endswith(".mp4"):
            continue
        srt = os.path.join(ROOT, "cph4", "fleet", "state", "asr",
                           os.path.splitext(n)[0] + ".srt")
        if not os.path.exists(srt):
            out.append({"src": os.path.join("media", "drama-out", n),
                        "srt": os.path.relpath(srt, ROOT)})
    return out


def src_bm_c_dedupe(vault=None):
    """bm-c 质检：整库感知哈希去重（纯 CPU，重活，适合算力机）。"""
    if not os.path.isdir(vault):
        return []
    return [{"dir": vault}]


SOURCES = [
    ("caption", src_caption, "bm-m"),
    ("asset-gap", src_asset_gap, "bm-m"),
    # 同一批缺口按机型分工：装配活派给 bm-a（白天让路由车道时段控制），
    # 产物落 media/review-720p，谁跑都可复算。这是「按机型分源」的样板。
    ("media-proxy", src_media_proxy, "bm-a"),
    ("media-proxy-local", src_media_proxy, "bm-m"),
    ("game-docs", src_game_docs, "bm-m"),
    ("bm-a-preview", src_bm_a_preview, "bm-a"),
    ("bm-b-asr", src_bm_b_asr, "bm-b"),
    ("bm-c-dedupe", src_bm_c_dedupe, "bm-c"),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--max-per-source", type=int, default=20)
    a = ap.parse_args(argv)

    ids = known_ids()
    busy = active_deliverables()
    made, summary = [], []
    for name, fn, node in SOURCES:
        try:
            # 各源签名不一致（有的要 vault，有的不要）：先带参试，TypeError 再退回无参。
            try:
                gaps = fn(VAULT)
            except TypeError:
                gaps = fn()
        except Exception as e:
            summary.append({"source": name, "error": str(e)[:120]})
            continue
        made_here = 0
        for g in gaps[: a.max_per_source]:
            if name == "caption":
                cid = "CAP-%s" % os.path.basename(g["rel"]).split(".")[0][:16]
                card = {
                    "id": cid, "title": "打标 %s" % os.path.basename(g["rel"])[:40],
                    "needs": "gpu", "nodes": [node], "prio": "P2",
                    "cmd": "python3 Tools/fleet/asset_caption.py --dir %s --kind auto --limit 1"
                           % os.path.dirname(g["abs"]),
                    "cwd": "", "requires": ["Tools/fleet/asset_caption.py"],
                    "deliverable": os.path.splitext(g["abs"])[0] + ".txt",
                    "why": "素材库训练 caption 缺口（机检：图片无同名 .txt）",
                }
            elif name == "asset-gap":
                cid = "GAP-%s-20261105" % g["class"]
                card = {
                    "id": cid, "title": "补素材 %s（缺 %d）" % (g["class"], g["gap"]),
                    "needs": "net", "nodes": [node], "prio": "P2",
                    "cmd": "python3 Tools/fleet/asset_gap_audit.py",
                    "cwd": "", "requires": ["Tools/fleet/asset_gap_audit.py"],
                    "deliverable": os.path.join(F, "state", "asset-gap.json"),
                    "why": "P0 缺口 %d 件（目标 %d），需按 collectors 补" % (g["gap"], g["p0"]),
                }
            elif name == "game-docs":
                cid = "DOCS-%s" % g["product"][:24]
                card = {
                    "id": cid, "title": "隐私政策 %s" % g["product"][:26],
                    "needs": "cpu", "nodes": [node], "prio": "P3",
                    "cmd": "python3 Tools/fleet/submit_docs.py --only %s" % g["product"],
                    "cwd": "", "requires": ["Tools/fleet/submit_docs.py"],
                    "deliverable": os.path.join("软著申请材料", g["product"], "privacy-policy.md"),
                    "why": "提审包缺隐私政策（机检：产品目录无 privacy-policy.md）",
                }
            elif name == "bm-a-preview":
                cid = "PREVIEW-30S-20261105"
                lst = os.path.join(F, "state", "preview-clips.txt")
                card = {
                    "id": cid, "title": "竖屏素材拼 30s 预览片",
                    "needs": "gpu", "nodes": [node], "prio": "P2",
                    "cmd": "python3 Tools/fleet/preview_concat.py --dir %s --out %s"
                           % (g["dir"], g["out"]),
                    "cwd": "", "requires": ["Tools/fleet/preview_concat.py"],
                    "deliverable": os.path.relpath(g["out"], VAULT) if VAULT else g["out"],
                    "why": "装配线产线验证：竖屏素材齐了，拼一条能看的 30s 预览",
                }
            elif name == "bm-b-asr":
                cid = "ASR-%s" % os.path.basename(g["src"]).split(".")[0][:18].upper()
                card = {
                    "id": cid, "title": "ASR 字幕 %s" % os.path.basename(g["src"])[:30],
                    "needs": "cpu", "nodes": [node], "prio": "P2",
                    "cmd": "python3 Tools/fleet/subs_asr.py --in %s --out %s"
                           % (g["src"], g["srt"]),
                    "cwd": "", "requires": ["Tools/fleet/subs_asr.py"],
                    "deliverable": g["srt"],
                    "why": "成片无字幕（机检：state/asr 下无同名 .srt）",
                }
            elif name == "bm-c-dedupe":
                cid = "DEDUPE-BMC-20261105"
                card = {
                    "id": cid, "title": "素材库感知哈希去重",
                    "needs": "cpu", "nodes": [node], "prio": "P3",
                    "cmd": "python3 Tools/fleet/asset_dedupe.py --dir %s --recursive --jobs 8 --json %s"
                           % (g["dir"], os.path.join(F, "state", "asset-dedupe-bmc.json")),
                    "cwd": "", "requires": ["Tools/fleet/asset_dedupe.py"],
                    "deliverable": os.path.join(F, "state", "asset-dedupe-bmc.json"),
                    "why": "训练前去重（感知哈希），纯 CPU 重活，适合算力机",
                }
            else:
                cid = "PROXY-%s" % os.path.basename(g["src"]).split(".")[0][:20]
                card = {
                    "id": cid, "title": "720p 代理 %s" % os.path.basename(g["src"])[:36],
                    "needs": "cpu", "nodes": [node], "prio": "P3",
                    "cmd": "ffmpeg -y -i %s -vf scale=-2:720 -c:v libx264 -crf 23 -an %s"
                           % (g["src"], g["dst"]),
                    "cwd": "", "requires": [], "deliverable": g["dst"],
                    "why": "审片代理缺口（机检：源视频无 -720p 成片）",
                }
            if cid in ids or (card.get("deliverable") in busy):
                continue
            card["state"] = "READY"
            card["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            card["created_by"] = "demand_gen"
            made.append(card)
            ids.add(cid)
            made_here += 1
        summary.append({"source": name, "gaps": len(gaps), "cards": made_here})

    if made and not a.dry:
        with open(BACKLOG, "a", encoding="utf-8") as f:
            for c in made:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
    for s in summary:
        print("[demand] %-12s 缺口=%-4s 造卡=%-3s %s"
              % (s.get("source"), s.get("gaps", "-"), s.get("cards", "-"), s.get("error", "")))
    print("[demand] 本轮造卡 %d 张%s" % (len(made), "（dry，未写入）" if a.dry else ""))
    return 0 if made or any(s.get("gaps") for s in summary) else 1


if __name__ == "__main__":
    sys.exit(main())