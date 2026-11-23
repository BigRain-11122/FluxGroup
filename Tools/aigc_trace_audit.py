#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aigc_trace_audit.py — 软著材料的「AI 痕迹」扫描（只读，零 LLM）。

为什么需要它
------------
2026-03-15 起软著审查从形式审查转为有限实质审查：纯 AI 一键生成、无人工二次开发，
按「无独创性」驳回；材料与代码不一致、说明书无实拍截图，同样是高频补正项。
被驳回后再猜「哪里像 AI」是浪费，本工具把常见痕迹变成可指认的条目。

判据
----
  D1 自曝句：说明书里出现「自动生成 / 由脚本生成 / 本模板」等
  D2 AI 文风：书面连接词密度（综上所述/值得注意的是/不仅…而且/首先其次最后/赋能/闭环）
  D3 模板结构：章节数 ≥8 且各节行数方差极小（机器排版特征）
  D4 缺人类证据：无截图引用、无日期、无数字来源、无失败尝试记录
  S1 注释模板化：同一注释前缀占比过高（如每个文件都以同一句 summary 开头）
  S2 无工程痕迹：全库没有 TODO/FIXME/HACK/临时/兼容/调试 等真实开发残留
  S3 行长度过窄：生成代码常见的均匀行宽
  S4 时间戳同源：同一批文件 mtime 全部相同（打包/一次性生成痕迹）

用法
----
  python Tools/aigc_trace_audit.py --doc <说明书.md> --src <源程序.txt> [--project <目录>]
  python Tools/aigc_trace_audit.py --self-test
退出码：0 无高危 / 1 有高危 / 2 参数错误
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

HIGH = {"D1", "D4", "S2", "S4"}

AI_PHRASES = ["综上所述", "值得注意的是", "总的来说", "总的来说", "不仅如此", "赋能", "闭环",
              "生态化", "本文将", "本模板", "自动生成", "由脚本生成", "一键生成",
              "首先", "其次", "最后，", "在当今", "随着人工智能"]
SELF_REVEAL = ["自动生成", "由脚本生成", "本模板", "代码树自动生成", "生成于", "本文件由"]
HUMAN_TRACES = ["TODO", "FIXME", "HACK", "XXX", "临时", "兼容", "调试", "debug",
                "wtf", "坑", "凑合", "老版本", "历史原因", "先这样"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig", errors="replace")


def audit_doc(text: str) -> list[dict]:
    out = []
    lowered = text

    hits = [w for w in SELF_REVEAL if w in lowered]
    if hits:
        out.append({"id": "D1", "level": "high",
                    "msg": f"自曝 AI 生成：{hits}（这句话本身就是驳回证据）"})

    ph = {w: lowered.count(w) for w in AI_PHRASES if lowered.count(w) > 0}
    if sum(ph.values()) >= 6:
        out.append({"id": "D2", "level": "mid",
                    "msg": f"AI 文风词频偏高 {sum(ph.values())} 次：{sorted(ph.items(), key=lambda x: -x[1])[:5]}"})

    lines = [l for l in text.splitlines() if l.strip()]
    sections = [l for l in lines if l.startswith("#")]
    if len(sections) >= 8:
        sizes, cur = [], 0
        for l in lines:
            if l.startswith("#"):
                if cur: sizes.append(cur)
                cur = 0
            else:
                cur += 1
        if len(sizes) >= 6:
            sd = statistics.pstdev(sizes)
            mean = statistics.mean(sizes)
            if mean > 0 and sd / mean < 0.35:
                out.append({"id": "D3", "level": "mid",
                            "msg": f"章节长度过于均匀（{len(sizes)} 节，均值 {mean:.0f} 行，变异系数 {sd/mean:.2f}）"})

    evidence = []
    # 截图必须是真引用：markdown 图片、图 N 标题或 img 标签；「屏幕」「界面」这类词不算。
    if not re.search(r"!\[[^\]]*\]\(|<img|如图\s*\d|图\s*\d+\s*[:：]", text):
        evidence.append("无截图/图引用")
    dates = re.findall(r"(?:20\d\d年\d+月\d+日|20\d\d-\d\d-\d\d)", text)
    if len(dates) < 2:
        evidence.append("无开发日期记录")
    if not re.search(r"(失败|排查|返工|踩坑|试玩发现|调优|改回|推翻)", text):
        evidence.append("无失败/排查记录")
    if "无截图/图引用" in evidence or len(evidence) >= 2:
        out.append({"id": "D4", "level": "high", "msg": "缺少人类证据：" + "、".join(evidence)})

    return out


def audit_src(text: str) -> list[dict]:
    out = []
    lines = [l.rstrip("\n") for l in text.splitlines() if l.strip()]
    if not lines:
        return out

    heads = [l.strip() for l in lines if l.strip().startswith("///") or l.strip().startswith("//")]
    prefixes = {}
    for h in heads:
        key = re.sub(r"[\u4e00-\u9fffA-Za-z0-9]+", "W", h)[:14]
        prefixes[key] = prefixes.get(key, 0) + 1
    if heads:
        top = max(prefixes.values())
        if top / len(heads) > 0.5 and len(heads) > 40:
            out.append({"id": "S1", "level": "mid",
                        "msg": f"注释高度模板化：{top}/{len(heads)} 条共用同一前缀"})

    joined = "\n".join(lines)
    if not any(t in joined for t in HUMAN_TRACES):
        out.append({"id": "S2", "level": "high",
                    "msg": "全库没有任何工程痕迹（TODO/FIXME/临时/兼容/调试/踩坑）"})

    lens = [len(l) for l in lines]
    mean = statistics.mean(lens)
    sd = statistics.pstdev(lens)
    if mean > 0 and sd / mean < 0.45:
        out.append({"id": "S3", "level": "low",
                    "msg": f"行宽过于均匀（均值 {mean:.0f}，变异系数 {sd/mean:.2f}）"})

    return out


def audit_mtime(project: Path) -> list[dict]:
    files = [p for p in project.rglob("*.cs") if p.is_file()][:200]
    if len(files) < 20:
        return []
    stamps = {}
    for p in files:
        stamps[round(p.stat().st_mtime)] = stamps.get(round(p.stat().st_mtime), 0) + 1
    top = max(stamps.values())
    if top / len(files) > 0.5:
        return [{"id": "S4", "level": "high",
                 "msg": f"{top}/{len(files)} 个 .cs 的修改时间完全相同（打包或一次性生成痕迹）"}]
    return []


def self_test() -> int:
    import tempfile

    fails = 0
    ai_doc = ("# 说明书\n## 1 概述\n本文档由代码树自动生成。\n"
              "综上所述，本系统赋能业务闭环，值得注意的是生态化。\n"
              "首先其次最后不仅如此。\n") + "\n".join(f"## {i} 节\n段落\n" for i in range(2, 12))
    r = audit_doc(ai_doc)
    if not any(x["id"] == "D1" for x in r):
        fails += 1
        print("FAIL D1 未抓")
    else:
        print("PASS 抓到自曝句")
    if not any(x["id"] == "D2" for x in r):
        fails += 1
        print("FAIL D2 未抓")
    else:
        print("PASS 抓到 AI 文风")

    human_doc = ("# 说明书\n## 1 概述\n2026-09-12 第一次试玩时发现吸力场在 40fps 下迟滞，\n"
                 "见图 3 截图。排查后改为帧率无关 lerp，问题消失。\n"
                 "## 2 截图\n图 4 为 1080p 实机画面。\n")
    r2 = audit_doc(human_doc)
    if any(x["id"] == "D1" for x in r2):
        fails += 1
        print("FAIL 人写文档被误判 D1")
    else:
        print("PASS 人写文档不误报 D1")

    ai_src = "\n".join("// summary of the class\n    public void M%d() { }" % i for i in range(80))
    if not any(x["id"] == "S2" for x in audit_src(ai_src)):
        fails += 1
        print("FAIL S2 未抓")
    else:
        print("PASS 抓到无工程痕迹")

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for i in range(30):
            p = d / f"F{i}.cs"
            p.write_text("class A{}", encoding="utf-8")
        if not any(x["id"] == "S4" for x in audit_mtime(d)):
            fails += 1
            print("FAIL S4 未抓")
        else:
            print("PASS 抓到同源时间戳")

    print(json.dumps({"self_test": "PASS" if not fails else "FAIL", "failures": fails},
                     ensure_ascii=False))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc")
    ap.add_argument("--src")
    ap.add_argument("--project")
    ap.add_argument("--json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not (args.doc or args.src or args.project):
        ap.error("need --doc / --src / --project (or --self-test)")

    findings = []
    if args.doc:
        findings += audit_doc(read(Path(args.doc)))
    if args.src:
        findings += audit_src(read(Path(args.src)))
    if args.project:
        findings += audit_mtime(Path(args.project))

    highs = [f for f in findings if f["level"] == "high"]
    report = {"files": {"doc": args.doc, "src": args.src, "project": args.project},
              "findings": findings,
              "high": len(highs),
              "verdict": "HIGH_RISK" if highs else ("NOTICE" if findings else "CLEAN")}
    text = json.dumps(report, ensure_ascii=False, indent=1)
    print(text)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    return 0 if not highs else 1


if __name__ == "__main__":
    raise SystemExit(main())
