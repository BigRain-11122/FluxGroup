#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recon_analysis.py - 把拆解卡按九面结构化，并算出「这部我们到底测到了几成」（PROD-RECON-RECIPE 的「拆解」工序）。

Why（2026-11-14）：拆解这道工序一直没有命令。它的原料其实已在盘（recon-dept-v1/cards/*.md
的实测表格），缺的是"按九面归位 + 明说哪些面没测"。没有这一步，配方卡只能凭感觉挑事实，
而管理层也看不出对标到底做全了没有。

三条硬边界：
  * 只用卡里已有的数字，不做任何推演（没测的面一律写「未测」，不填建议值）。
  * 覆盖率是算出来的（有实测的面 / 九面），不是估的。
  * 一张卡实测项少于 5 条就判"证据不足"，不进 analysis（先补拆解）。

用法：
  python3 Tools/fleet/recon_analysis.py --cards cph4/fleet/recon-dept-v1/cards --out cph4/fleet/out/recon/analysis.md
  python3 Tools/fleet/recon_analysis.py --check cph4/fleet/out/recon/analysis.md --cards <dir>
  python3 Tools/fleet/recon_analysis.py --self-test
返回码：0 成功 · 1 输入不足 · 2 复核不过 · 3 自检失败
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

NUM = re.compile(r"(?<![0-9A-Za-z.])\d+(?:,\d{3})*(?:\.\d+)?%?(?![0-9A-Za-z])")
REF = re.compile(r"\[F(\d+)\]")
LIST_MARK = re.compile(r"^\s*\d{1,2}[.、)）]\s+")

# 九面：内容组 C1-C9 与游戏组 G1-G9 共用一张表（不同卡命中不同面）
FACES = [
    ("C1/G1 取源", ("来源", "平台", "样本", "URL", "下载", "包体", "APK")),
    ("C2/G2 钩子·引擎", ("钩子", "前 5 秒", "前5秒", "引擎", "il2cpp", "Unity", "Cocos",
                        "metadata", "运行时", "反编译")),
    ("C3/G3 结构·资源", ("结构", "集", "时长", "镜数", "资源", "assets", "AB", "AssetBundle",
                        "图集", "纹理", "字体")),
    ("C4/G4 节奏·UI", ("节奏", "镜长", "中位", "P90", "对白", "静场", "分辨率", "竖屏",
                      "按钮", "UI", "适配")),
    ("C5/G5 反转·循环", ("反转", "钩子", "循环", "30s", "3min", "30min", "关卡", "回合")),
    ("C6/G6 台词·数值", ("台词", "句式", "金句", "数值", "难度", "产出", "消耗", "金币",
                        "体力", "惩罚")),
    ("C7/G7 镜头·商业化", ("景别", "运镜", "机位", "广告", "激励", "插屏", "内购", "付费",
                          "穿山甲", "优量汇", "变现")),
    ("C8/G8 包装·留存", ("字幕", "字号", "描边", "花字", "封面", "片头", "留存", "签到",
                        "任务", "榜")),
    ("C9/G9 声音·性能", ("BGM", "音效", "响度", "LUFS", "性能", "内存", "启动", "帧率",
                        "FPS", "体积", "占比", "压缩", "解压", "ABI", "文件数")),
]
MIN_ITEMS = 5


def _nums(line):
    return set(NUM.findall(LIST_MARK.sub("", REF.sub("", str(line or "")))))


def measured_lines(text):
    """卡里带数字的实测行（标题/分隔线/纯形容词行不算）。"""
    out = []
    for ln in str(text or "").splitlines():
        raw = ln.strip()
        if not raw or raw.startswith("#") or set(raw) <= set("-|: "):
            continue
        if not _nums(raw):
            continue
        clean = re.sub(r"^[|\->\s]+", "", raw).replace("|", " ").strip()
        clean = re.sub(r"\s{2,}", " ", clean)
        clean = LIST_MARK.sub("", clean)
        if len(clean) > 200:
            continue
        out.append(clean)
    return out


def analyse(text):
    """返回 {face: [行]}、覆盖率、未测面。"""
    lines = measured_lines(text)
    buckets = {name: [] for name, _ in FACES}
    for ln in lines:
        for name, kws in FACES:
            if any(k in ln for k in kws):
                buckets[name].append(ln)
                break
    hit = [n for n, v in buckets.items() if v]
    miss = [n for n, v in buckets.items() if not v]
    return {"items": len(lines), "buckets": buckets, "hit": hit, "miss": miss,
            "coverage": round(len(hit) / float(len(FACES)), 3)}


def render(cards):
    """cards: [(name, path, result)] -> markdown"""
    out = ["# 竞品拆解·九面结构（自动生成）", ""]
    tot_c = 0.0
    for name, path, r in cards:
        out.append("## %s" % name)
        out.append("")
        out.append("- 实测项 %d 条｜九面覆盖 %d/9（%.0f%%）"
                   % (r["items"], len(r["hit"]), r["coverage"] * 100))
        if r["miss"]:
            out.append("- 未测：%s" % "、".join(x.split(" ")[0] for x in r["miss"]))
        out.append("")
        for face, _kws in FACES:
            rows = r["buckets"][face]
            if not rows:
                out.append("- **%s**：未测" % face)
                continue
            out.append("- **%s**（%d 条）" % (face, len(rows)))
            for ln in rows[:3]:
                out.append("  - %s" % ln)
        out.append("")
        tot_c += r["coverage"]
    avg = tot_c / len(cards) if cards else 0
    out.insert(1, "")
    out.insert(2, "> 共 %d 部｜平均九面覆盖 %.0f%%｜数字全部来自拆解卡原文，未测一律不填"
               % (len(cards), avg * 100))
    return "\n".join(out) + "\n"


def collect(cards_dir):
    res = []
    for p in sorted(glob.glob(os.path.join(cards_dir, "*.md"))):
        text = open(p, encoding="utf-8", errors="replace").read()
        r = analyse(text)
        if r["items"] < MIN_ITEMS:
            continue                     # 证据不足的卡不进结构表（先补拆解）
        res.append((os.path.basename(p)[:-3], p, r))
    return res


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %-40s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    card = ("# GAME-X\n\n| 项 | 值 |\n|---|---|\n"
            "| APK | 335 MB |\n| 引擎 | Unity IL2CPP |\n| assets | 284.2 MB 62.3% |\n"
            "| 激励视频 | 4 处 |\n| 签到 | 7 日 |\n| 响度 | -14 LUFS |\n"
            "| 钩子 | 第 3 秒反转 |\n| 镜长中位 | 2.23s |\n")
    r = analyse(card)
    # 卡里 8 行表格中「引擎 | Unity IL2CPP」没有数字，按设计不算实测行
    chk("实测行抽取（只收带数字的行）", r["items"] == 7, r["items"])
    chk("九面覆盖算得出来", 0 < r["coverage"] <= 1, r["coverage"])
    chk("未测面被单列", len(r["hit"]) + len(r["miss"]) == 9)
    chk("钩子进 C2", any("第 3 秒" in x for x in r["buckets"]["C2/G2 钩子·引擎"]))

    thin = "# 只有形容词\n画面很精致\n"
    chk("证据不足的卡不入表", analyse(thin)["items"] == 0)
    chk("渲染含未测字样", "未测" in render([("X", "/x", r)]))
    chk("渲染带覆盖率", "九面覆盖" in render([("X", "/x", r)]))
    print("\n[recon_analysis] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", default="", help="拆解卡目录")
    ap.add_argument("--out", default="", help="输出 analysis.md")
    ap.add_argument("--check", default="", help="复核已有 analysis.md")
    ap.add_argument("--json", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    cards_dir = a.cards or os.path.join(ROOT, "cph4", "fleet", "recon-dept-v1", "cards")
    if not os.path.isdir(cards_dir):
        print("[recon-analysis] 卡目录不存在：%s" % cards_dir)
        return 1
    cards = collect(cards_dir)
    if not cards:
        print("[recon-analysis] 没有可用拆解卡（实测项 ≥%d 条才算）" % MIN_ITEMS)
        return 1
    text = render(cards)
    if a.check:
        if not os.path.exists(a.check):
            print("[recon-analysis] 待复核文件不存在：%s" % a.check)
            return 2
        have = open(a.check, encoding="utf-8").read()
        # 判据：每张卡都在、每张都带覆盖率、未测面至少出现一次
        errs = []
        for name, _p, _r in cards:
            if ("## %s" % name) not in have:
                errs.append("缺卡：%s" % name)
        if "九面覆盖" not in have:
            errs.append("缺覆盖率")
        if "未测" not in have:
            errs.append("缺未测面")
        if a.json:
            open(a.json, "w", encoding="utf-8").write(
                json.dumps({"ok": not errs, "errs": errs}, ensure_ascii=False, indent=1))
        print("[recon-analysis] 复核 %s：%s" % (a.check, "通过" if not errs else "不通过"))
        for e in errs[:6]:
            print("  -", e)
        return 0 if not errs else 2
    if not a.out:
        print("[recon-analysis] 缺 --out")
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(json.dumps(
            {"cards": [{"name": n, "items": r["items"], "coverage": r["coverage"],
                        "miss": r["miss"]} for n, _p, r in cards]},
            ensure_ascii=False, indent=1))
    print("[recon-analysis] %d 部 -> %s（平均覆盖 %.0f%%）"
          % (len(cards), a.out, 100 * sum(c[2]["coverage"] for c in cards) / len(cards)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
