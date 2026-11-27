#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""voice_gate.py - 中文语感机检闸（正身判据见 cph4/fleet/VOICE-V1.md）。

为什么要有它：本地 4B 写中文不是"不会写字"，是会被提示词逼成客服。
2026-11-11 实测旧提示词产出：

    感谢喜爱！具体手法已整理在置顶笔记中，欢迎查阅。   ← 编造 + 客服腔
    抱歉，这首歌的具体名称需要进一步确认后才能提供准确信息。 ← 公文腔
    感谢喜爱！是否真人为后续确认中。                    ← 病句 + 客服腔
    具体哪一集？我会尽快确认更新计划。                    ← 反问用户

这些都是可机检的，不需要人一条条看。闸只做两件事：拦住不像人话的，标出可疑的。

五个面（face）：
  comment  评论回复     ≤40 字、不反问、不空承诺、事实类不许下结论
  title    标题文案     ≤20 字、禁震惊体
  line     台词         ≤18 字、禁书面语
  subtitle 字幕         单行 ≤17 字
  script   口播草稿     禁 AI 腔与公文连接词

用法：
  python3 Tools/fleet/voice_gate.py --selftest
  python3 Tools/fleet/voice_gate.py --text "哈哈谢谢" --face comment
  echo '{"text":"...","face":"comment","ctx":"评论原文"}' | python3 Tools/fleet/voice_gate.py --stdin

返回码：0 全部通过 / 1 有 BLOCK 或 WARN（--strict 时 WARN 也返 1）/ 2 自检失败
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# ---------------------------------------------------------------- 词表
# 客服/公文/电商腔：真人不会这样跟人说话
SERVICE = (
    "感谢喜爱", "感谢支持", "感谢您的", "感谢关注", "感谢理解", "谢谢支持",
    "欢迎查阅", "欢迎关注", "欢迎点赞", "欢迎收看", "敬请", "请您", "如有疑问",
    "一键三连", "多多支持", "持续关注", "为您", "予以", "希望对您有帮助",
)
OFFICIAL = (
    "进一步确认", "准确信息", "相关信息", "具体名称需要", "进行确认", "后续确认",
    "后续会", "将在", "将会", "我们会尽快", "稍后回复", "已收到您的",
)
AI_TONE = (
    "作为一个", "总的来说", "希望能帮到你", "让我们", "首先", "其次", "最后一点",
    "值得注意的是", "某种程度上", "可以说", "在这个", "不难看出",
)
# 空承诺：说"会/将"却不给时间点
EMPTY_PROMISE = re.compile(r"(会|将)(尽快|后续|稍后|及时|第一时间)|稍后回复|回头再说")
# 指向未经授权的具体内容 = 编造（置顶/简介/下期这些东西账号上到底有没有，模型不知道）
FABRICATION = (
    "置顶", "笔记", "简介", "主页", "下期", "预告", "明天", "下周", "上架",
    "已经整理", "详见", "链接在",
)
# 书面连接词：台词与口播里出现就不是人话
CONNECTIVES = ("因此", "此外", "然而", "总之", "综上", "并且", "而且", "所以")

# 事实类问句：这类评论模型不许自己给答案（歌名/软件/时间/身份它都不知道）
# 用正则而不是词表：中文问法太散，"叫什么名字"里没有"歌名"两个字，词表必漏。
FACT_PAT = re.compile(
    r"(叫什么|什么名字|什么歌|啥歌|哪首歌|哪首|哪一集|第几集|什么时候|多久|多少钱"
    r"|是不是真|真人吗|真人\?|怎么做的|怎么剪|用什么|啥软件|什么软件|谁唱|在哪拍"
    r"|什么型号|多少集|几时|更新吗|啥时候)"
)
FACT_WORDS = ("bgm", "BGM", "歌名", "配乐", "插件", "软件", "工具")
# 允许的"延后"说法：诚实的不确定，不算空承诺
# 事实类评论的合格回应只有两类：真的去查（翻/查/问/找），或**诚实说不确定**。
# 2026-11-13 实测：原白名单只认"查/翻/问/确认"，把"说不准/还没定/看情况"这类同样
# 诚实的表达也判成"下了确定结论"——判据方向对，词面太窄，会把好话术逼成公式。
DEFER = ("翻一下", "查一下", "问一下", "确认一下", "找一下", "翻翻", "问问", "查查",
         "不知道", "说不准", "不确定", "说不好", "还没定", "没定", "看情况",
         "回头说", "等我确认", "我再看看")

# 病句：4B 的高频写法，"是否…为…中"这种主谓宾都塌了
BROKEN = (
    re.compile(r"(是否|是不是)[^，。！？]{0,8}为[^，。！？]{0,6}中"),
    re.compile(r"为(后续|进一步)[^，。！？]{0,4}中"),
)

LIMITS = {"comment": 40, "title": 20, "line": 18, "subtitle": 17, "script": 120}


def _sentences(text):
    return [s for s in re.split(r"[。！？!?\n]+", text or "") if s.strip()]


def check(text, face="comment", ctx=""):
    """返回 {verdict, hits, score}。verdict: PASS / WARN / BLOCK。"""
    t = (text or "").strip()
    hits = []

    if not t:
        return {"verdict": "BLOCK", "hits": ["空文本"], "score": 0}

    lim = LIMITS.get(face, 40)
    if len(t) > lim:
        hits.append("超长 %d>%d" % (len(t), lim))

    for w in SERVICE:
        if w in t:
            hits.append("客服腔:" + w)
            break
    for w in OFFICIAL:
        if w in t:
            hits.append("公文腔:" + w)
            break
    for w in AI_TONE:
        if w in t:
            hits.append("AI腔:" + w)
            break
    for w in FABRICATION:
        if w in t:
            hits.append("编造指向:" + w)
            break
    for r in BROKEN:
        if r.search(t):
            hits.append("病句:" + r.pattern[:12])
            break

    if face in ("comment", "title", "line", "script"):
        if EMPTY_PROMISE.search(t):
            hits.append("空承诺")

    warns = []
    if face == "comment":
        if t.count("！") + t.count("!") >= 1:
            warns.append("感叹号（创作者口吻基本不用）")
        if "？" in t or "?" in t:
            warns.append("反问用户（回复不该把球踢回去）")
        for w in CONNECTIVES:
            if w in t:
                warns.append("书面连接词:" + w)
                break
        # 事实类评论：模型不许自己给答案
        is_fact = bool(FACT_PAT.search(ctx or "")) or any(w in (ctx or "") for w in FACT_WORDS)
        if is_fact and not any(w in t for w in DEFER) and len(t) >= 6:
            hits.append("事实类评论下了确定结论（模型不知道答案）")
    if face in ("line", "script"):
        for w in CONNECTIVES:
            if w in t:
                hits.append("台词书面语:" + w)
                break
    if face == "title":
        for w in ("震惊", "竟然", "万万没想到", "绝对想不到", "速看", "必看"):
            if w in t:
                hits.append("震惊体:" + w)
                break
        if t.count("！") + t.count("!") > 1:
            warns.append("叹号堆叠")
    if face in ("comment", "line"):
        long_s = [s for s in _sentences(t) if len(s) > (18 if face == "line" else 25)]
        if long_s:
            warns.append("单句过长:%d字" % len(long_s[0]))
    if sum(1 for ch in t if ord(ch) > 0x1F000) > 1:
        warns.append("emoji 过多")

    hits.extend(warns)
    score = max(0, 100 - 20 * len([h for h in hits if h not in warns]) - 5 * len(warns))
    verdict = "BLOCK" if any(h not in warns for h in hits) else ("WARN" if warns else "PASS")
    return {"verdict": verdict, "hits": hits, "score": score}


# ---------------------------------------------------------------- 自检
# 造闸纪律：1 正例 + N 反例，反例必须覆盖"擦边"（正常长度的客服腔、看起来礼貌的公文腔）。
# 契约两条：①正例只要求不误杀（PASS 或 WARN 都算过，WARN 是建议不是判决）
#          ②反例必须 BLOCK（不许放过）
CASES = [
    # (face, ctx, text, 期望：PASS=正例不许拦 / BLOCK=反例必须拦)
    ("comment", "这段剪辑太顺了", "谢谢，剪了好几遍", "PASS"),
    ("comment", "女主好美", "被你说得有点飘", "PASS"),
    ("comment", "女主好美", "谢啦，这夸我收下了", "PASS"),
    ("comment", "这歌叫什么名字 找好久了", "这首我得翻一下工程文件", "PASS"),
    ("comment", "up主这个转场怎么做的啊", "谢谢，具体参数我翻一下再回你", "PASS"),
    ("comment", "第三集啥时候更啊", "", "BLOCK"),  # 空文本必须拦
    ("comment", "up主这个转场怎么做的啊，太丝滑了",
     "感谢喜爱！具体手法已整理在置顶笔记中，欢迎查阅。", "BLOCK"),
    ("comment", "这歌叫什么名字 找好久了",
     "抱歉，这首歌的具体名称需要进一步确认后才能提供准确信息。", "BLOCK"),
    ("comment", "女主好美，是真人吗", "感谢喜爱！是否真人为后续确认中。", "BLOCK"),
    ("comment", "第三集啥时候更啊", "具体哪一集？我会尽快确认更新计划。", "BLOCK"),
    ("comment", "这歌叫什么名字 找好久了", "这首歌叫《夜航》。", "BLOCK"),
    ("comment", "第三集啥时候更啊", "下期预告里会说", "BLOCK"),
    ("comment", "up主这个转场怎么做的啊", "转场是硬切加叠化", "BLOCK"),
    ("title", "", "我妈把相亲对象P成了她初恋", "PASS"),
    ("title", "", "震惊！AI漫剧竟然这么好看，你绝对想不到的结局", "BLOCK"),
    ("line", "", "你签也得签", "PASS"),
    ("line", "", "我认为这份协议对我们双方而言都是有利的", "BLOCK"),
    ("subtitle", "", "这是我在这个城市里生活了整整七年的全部记忆和证据", "BLOCK"),
    ("script", "", "作为一个创作者，首先我要说的是，其次我想说，最后希望大家喜欢。",
     "BLOCK"),
]


def selftest():
    bad = 0
    for i, (face, ctx, text, want) in enumerate(CASES, 1):
        r = check(text, face, ctx)
        ok = r["verdict"] == "BLOCK" if want == "BLOCK" else r["verdict"] != "BLOCK"
        if not ok:
            bad += 1
        print("%s %2d %-8s want=%-5s got=%-5s %s" % (
            "ok " if ok else "FAIL", i, face, want, r["verdict"], ",".join(r["hits"])))
    print("[voice_gate] %d/%d" % (len(CASES) - bad, len(CASES)))
    return 0 if bad == 0 else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--text")
    ap.add_argument("--face", default="comment")
    ap.add_argument("--ctx", default="")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.stdin:
        rows = [json.loads(l) for l in sys.stdin if l.strip()]
        rc = 0
        for r in rows:
            res = check(r.get("text", ""), r.get("face", "comment"), r.get("ctx", ""))
            print(json.dumps(dict(r, **res), ensure_ascii=False))
            if res["verdict"] == "BLOCK" or (a.strict and res["verdict"] == "WARN"):
                rc = 1
        return rc
    if a.text is None:
        ap.error("需要 --text 或 --stdin 或 --selftest")
    res = check(a.text, a.face, a.ctx)
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res["verdict"] == "PASS" or (res["verdict"] == "WARN" and not a.strict) else 1


if __name__ == "__main__":
    sys.exit(main())
