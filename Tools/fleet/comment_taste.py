#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comment_taste.py — 评论品味/人味判据闸（确定性，零 LLM，可复算）。

为什么要有这个闸：语料里"真实"和"好"是两件事。B站评论区大量是互相应答（回复@xxx）、
纯表情、接话、烂梗堆砌；而模型自己写出来的是另一种病——"狠狠破防""拿捏得死死的"
这种做作腔。两种都不该进训练集，也都不该发出去。

五维判据（CEO 口径 2026-11-17：逻辑要顺、语感要丰富、有人味、有品味、不做作无AI感）：
  1 逻辑   ：句子里要有"具体对象"或"转折/因果"，不能是名词堆和情绪喷发。
  2 语感   ：口语助词/语气词的种类数；书面连接词过多扣分。
  3 人味   ：有具体细节、第一人称经历、真实指代（不用"这条视频很好"这种空指）。
  4 品味   ：克制、有分寸（自嘲/让步/建议）；表情码、感叹号、脏话堆砌扣分。
  5 不做作 ：烂梗/夸张词/模板句命中即重罚——这是 AI 感与做作感的主要来源。

判定：REJECT（不许进训练集/不许发）、RISKY（要人改）、PASS。

用法：
  python3 Tools/fleet/comment_taste.py --text "下次可以试一下竖屏吗，实在太小了"   # 单句打分
  python3 Tools/fleet/comment_taste.py --corpus <jsonl> --out <jsonl>            # 筛训练语料
  python3 Tools/fleet/comment_taste.py --eval <AB.jsonl>                         # 基座 vs LoRA 同尺比分
  python3 Tools/fleet/comment_taste.py --self-test
"""
import argparse
import json
import os
import re
import sys

# 做作/AI 腔：命中一个就重罚，两个以上直接 REJECT。这类词不是语病，
# 是"别人这么说过所以我也这么说"的模板，真人只在反讽时用。
CLICHE = ["破防", "拿捏", "狠狠", "绝了", "泪目", "救命", "谁懂", "封神",
          "氛围感拉", "磕到", "硬控", "暴击", "沦陷", "杀我", "yyds", "懂的都懂",
          "好看到", "太顶了", "封神了", "美到", "帅到", "甜到", "虐到", "土拨鼠"]
# 空洞夸张：单独出现不算，密集出现就是文案腔
PUFF = ["真的", "必须", "超级", "简直", "绝对", "完全", "极其", "特别", "非常", "瞬间"]
ORAL = set("吧啊呀呢嘛啦咩咯诶嗷嗯哦哈嘿诶")
CONNECT = ["但", "不过", "其实", "就是", "倒是", "反而", "要不", "建议", "觉得",
           "所以", "因为", "如果", "虽然", "要是", "本来", "结果", "而且", "实在",
           "严格来说", "感觉", "好像", "应该", "不如", "有点", "至少"]
CONCRETE = ["画面", "剪辑", "镜头", "结尾", "开头", "台词", "配乐", "bgm", "BGM",
            "运镜", "剧情", "表演", "节奏", "字幕", "调色", "光影", "构图", "转场",
            "教程", "教学", "软件", "素材", "分镜", "剧本", "主题曲", "片尾", "音效",
            "画质", "前奏", "副歌", "广告", "文案", "配音", "剪辑师", "摄影师", "导演",
            "up主", "UP主", "老师", "这集", "这期", "这条", "这段", "这个视频",
            "竖屏", "横屏", "分辨率", "收音", "对白", "演法", "眼神"]
SELF = ["我", "咱", "我们"]
REPLY = re.compile(r"^\s*(回复\s*@|@\S+\s*:|@)")
CJK = re.compile(r"[\u4e00-\u9fff]")
BRACKET_EMOJI = re.compile(r"\[[^\]]{1,6}\]")
BARE_EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
DIRTY = ["傻逼", "妈的", "卧槽", "草泥马", "操你"]
# 纯助兴/接话：真人会说，但学不到东西
FILLER = re.compile(r"^(哈+|呵+|牛+|好+|妙+|顶+|赞+|打卡|前排|来了|沙发|已看|[?？!！.。,，~～\s]+)$")


def score(text):
    t = (text or "").strip()
    d = {"len": len(t), "logic": 0, "voice": 0, "human": 0, "taste": 0, "natural": 0,
         "flags": []}
    if not CJK.search(t):
        d["flags"].append("无中文（纯符号/表情）")
        return dict(d, total=0, verdict="REJECT")
    # 去掉 [表情码] 和标点后如果几乎没字，就是纯刷表情/纯助兴，学不到任何东西
    bare = BRACKET_EMOJI.sub("", t)
    bare = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", bare)
    if len(bare) < 4:
        d["flags"].append("表情/符号占满（有效文字 %d 字）" % len(bare))
        return dict(d, total=0, verdict="REJECT")

    if REPLY.match(t):
        d["flags"].append("互相应答（回复@某人，脱离上下文没意义）")

    # 1 逻辑：有具体对象或转折因果 = 有主干；否则是名词/情绪堆
    obj = any(w in t for w in CONCRETE)
    con = any(w in t for w in CONNECT)
    d["logic"] = 30 if obj else 0
    if con:
        d["logic"] += 20
    if obj and con:
        d["logic"] = 45

    # 2 语感：口语助词种类（不是数量——同一句"啊啊啊"只有一种）
    kinds = len({c for c in t if c in ORAL})
    d["voice"] = min(20, kinds * 8)

    # 3 人味：第一人称 + 具体细节
    d["human"] = 10 if any(w in t for w in SELF) else 0
    if obj:
        d["human"] += 10

    # 4 品味：克制加分；装饰过载扣分
    d["taste"] = 15
    emo_n = len(BRACKET_EMOJI.findall(t)) + len(BARE_EMOJI.findall(t))
    bang = t.count("！") + t.count("!")
    if emo_n >= 3:
        d["taste"] -= 10
        d["flags"].append("表情堆砌 %d 个" % emo_n)
    if bang >= 2:
        d["taste"] -= 8
        d["flags"].append("感叹号 %d 个" % bang)
    if any(w in t for w in DIRTY):
        d["taste"] -= 15
        d["flags"].append("脏话")
    if not t.rstrip("。！？!?~～") == t:      # 有收尾标点=写完整了
        d["taste"] += 5
    d["taste"] = max(0, min(20, d["taste"]))

    # 5 不做作：烂梗命中即重罚
    cli = [w for w in CLICHE if w in t]
    puff_n = sum(1 for w in PUFF if w in t)
    d["natural"] = 20 - 10 * len(cli) - 4 * puff_n
    if cli:
        d["flags"].append("做作/AI 腔：%s" % "/".join(cli[:3]))
    if puff_n >= 2:
        d["flags"].append("空洞夸张词 %d 个" % puff_n)
    d["natural"] = max(0, min(20, d["natural"]))

    total = d["logic"] + d["voice"] + d["human"] + d["taste"] + d["natural"]
    if REPLY.match(t) or len(cli) >= 2 or FILLER.match(t) or len(t) < 6:
        verdict = "REJECT"
    elif total >= 60 and d["logic"] >= 30 and not cli:
        verdict = "PASS"
    else:
        verdict = "RISKY"
    return dict(d, total=total, verdict=verdict)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--corpus")
    ap.add_argument("--out")
    ap.add_argument("--eval", dest="eval")
    ap.add_argument("--min", type=int, default=60, help="PASS 线（总分）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        good = ["下次可以试一下竖屏教学吗，实在太小了，可以出个2P",
                "里面有一些严格来说不能算爱情吧",
                "有推荐的电脑剪辑入门软件咩叔叔，除了pr"]
        bad = ["这段视频真的绝了，狠狠破防，氛围感拉满！",
               "回复 @小琦宝啊哈 :搜到啦谢谢",
               "[高考加油][高考加油][高考加油]",
               "哈哈哈哈哈哈哈哈"]
        cases = []
        for g in good:
            s = score(g)
            cases.append(("好句要 PASS/至少不 REJECT：%s" % g[:12],
                          s["verdict"] in ("PASS", "RISKY")))
        for b in bad:
            cases.append(("坏句要拦：%s" % b[:12], score(b)["verdict"] == "REJECT"))
        cases.append(("做作词必扣分", score("真的绝了")["natural"] < 20))
        cases.append(("具体对象给逻辑分", score("结尾那个转场")["logic"] >= 30))
        ok = sum(1 for _, v in cases if v)
        for n, v in cases:
            if not v:
                print("  FAIL %s" % n)
        print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
        return 0 if ok == len(cases) else 1

    if a.text:
        s = score(a.text)
        print("[taste] %s 总分 %d | 逻辑%d 语感%d 人味%d 品味%d 不做作%d"
              % (s["verdict"], s["total"], s["logic"], s["voice"], s["human"],
                 s["taste"], s["natural"]))
        for f in s["flags"]:
            print("  - %s" % f)
        return 0

    if a.corpus:
        rows = [json.loads(l) for l in open(a.corpus, encoding="utf-8") if l.strip()]
        keep, stat = [], {"REJECT": 0, "RISKY": 0, "PASS": 0}
        for r in rows:
            s = score(r.get("text"))
            stat[s["verdict"]] += 1
            if s["verdict"] == "PASS":
                keep.append(dict(r, taste=s["total"]))
        out = a.out or os.path.join(os.path.dirname(a.corpus), "QUALITY-PASS.jsonl")
        with open(out, "w", encoding="utf-8") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("[taste] %d 条 → PASS %d / RISKY %d / REJECT %d → %s"
              % (len(rows), stat["PASS"], stat["RISKY"], stat["REJECT"], out))
        return 0

    if a.eval:
        rows = [json.loads(l) for l in open(a.eval, encoding="utf-8") if l.strip()]
        agg = {"base": [], "lora": []}
        for r in rows:
            if r.get("side") not in agg:
                continue
            for t in r.get("outputs") or []:
                s = score(t)
                agg[r["side"]].append((s["total"], s["verdict"]))
        for side in ("base", "lora"):
            v = agg[side]
            if not v:
                continue
            art = sum(x[0] for x in v) / len(v)
            ok = sum(1 for x in v if x[1] == "PASS") / len(v) * 100
            print("[taste] %-4s %d 条 均分 %.1f · PASS率 %.0f%%" % (side, len(v), art, ok))
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
