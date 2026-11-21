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


# 分段判据（颗粒度对齐）：同一个尺子量所有人群会得出假结论——玩梗/浅层本来就该 6-12 字、
# 没有"逻辑主干"，用通用线量它们必然 0 分，看着像模型差，其实是尺子不对。
SEG_TUNE = {
    # seg: (PASS 线, 逻辑分下限, 是否允许"短促接话"算完整)
    "memer": (42, 0, True),
    "shallow": (40, 0, True),
    "music_seeker": (55, 0, True),
    "beginner": (55, 20, False),
    "tech_nerd": (62, 30, False),
    "ai_creator": (60, 30, False),
    "critic": (58, 20, False),
    "feeler": (58, 20, False),
}


REPLY_PREFIX = re.compile(r"^\s*回复\s*@?[^:：]{0,20}[:：]\s*")


def strip_reply_prefix(text):
    """剥掉「回复 @某人 :」前缀。

    2026-11-17 实测：critic 段被丢弃的 5/6 都是这个前缀造成的，而前缀后面往往是
    很好的技术讨论（"为什么录出来的声音卡顿""生化危机不如魔兽和GTA"）。@前缀只是
    指向关系，不是内容噪音——剥掉比整条扔掉信息量高得多。
    """
    return REPLY_PREFIX.sub("", text or "").strip()


# ── 人味分（0-40）：语感之外单独量"像不像一个具体的人在说话" ──
TURN = ["不过", "但是", "其实", "就是", "倒是", "反而", "所以", "因为", "本来", "结果"]
EXPERIENCE = ["剪过", "试过", "学过", "看了", "做过", "搞过", "弄过", "练过", "试了", "学了"]
SELF_KNOCK = ["哈哈", "笑死", "别骂了", "菜", "笨", "翻车", "手残", "不会", "搞不懂"]


def human_feel(text):
    """人味 = 有转折/因果 + 有具体经历 + 口语助词多样 + 有克制自嘲 - 做作扣分。

    为什么单独一把尺子：品味闸量的是"能不能发"（防做作、防跑题），但它管不了
    "有没有人味"——一条完全合格的中性陈述也能过闸。人味要靠具体、有起伏、有自我。
    """
    t = strip_reply_prefix(text)
    if not t:
        return 0
    f = 0
    f += min(6, 2 * sum(1 for w in TURN if w in t))
    f += min(6, 2 * len({c for c in t if c in ORAL}))
    if any(w in t for w in SELF) and any(w in t for w in EXPERIENCE):
        f += 6
    elif any(w in t for w in SELF):
        f += 2
    f += min(6, 2 * sum(1 for w in CONCRETE if w in t))
    if any(w in t for w in SELF_KNOCK):
        f += 4
    if 8 <= len(t) <= 32:
        f += 4
    f -= 6 * sum(1 for w in CLICHE if w in t)
    # 病句/碎片风险：没有动词性成分且很短
    if len(t) < 12 and not any(w in t for w in ("是", "有", "觉得", "感觉", "看", "剪", "做")):
        f -= 4
    return max(0, min(40, f))


def awkward_particles(text):
    """语气词塞错位置的检测（不改分，只给调用方一个可拒稿的信号）。

    2026-11-20 实锚：把"带口语助词"写进指令后，模型开始硬塞——
    「结尾那声鸣叫哈挺带感的」——语感分从 0 冲到 16，中文却不像人说的。
    判据：语气词后面必须紧跟标点或句尾；塞在词中间就算生硬。
    """
    t = strip_reply_prefix(text or "")
    bad = []
    for i, ch in enumerate(t):
        if ch not in ORAL:
            continue
        nxt = t[i + 1] if i + 1 < len(t) else ""
        if nxt and nxt not in "，。！？、；：…~～ ":
            bad.append("%s@%d" % (ch, i))
    return bad


def _ai_smell_words():
    """我们自己**真发出去过、被 CEO 判 AI 味**的词骨架（单一源=BAN-PHRASES-v1.json）。

    2026-11-20 实锚：「教程太干货了，必须三连支持！」「保姆级教程太实用了，已收藏！」
    这类句子 CLICHE 一个都不命中（它们不是烂梗而是"营销腔"），于是 8 条候选里能过闸
    的全是这个形状。所以把骨架收进硬拒表：空夸（干货/保姆级/三连）、文案腔
    （氛围感/质感/很到位）、作文腔（不仅/综上/展现了）、客服腔（宝子/同学/感谢支持）。
    表在文件里不在代码里：以后发现新的坏句子，改 JSON 不用改代码。

    分两级用（2026-11-21 CEO「不是只靠拦着，而是从根本上训练好」）：
      · 输出级（AI_SMELL）= 全部，严一点没关系，拒了只是少发一条；
      · 语料级（AI_SMELL_CORPUS）= 只留"真人基本不会说"的那几组。
        作文连接词（不仅/而且/从而）真人也会用，从训练集里删掉是过度清洗——
        实测会多删 700+ 条正常句子。
    """
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "cph4", "fleet", "social", "BAN-PHRASES-v1.json")
    CORPUS_GROUPS = ("空夸词", "营销词", "客服腔")
    try:
        d = json.load(open(p, encoding="utf-8"))
        groups = d.get("words") or {}
        allw, corpusw = [], []
        for k, v in groups.items():
            allw.extend([w for w in v if w and len(w) >= 2])
            if k in CORPUS_GROUPS:
                corpusw.extend([w for w in v if w and len(w) >= 2])
        if allw:
            return (sorted(set(allw), key=len, reverse=True),
                    sorted(set(corpusw), key=len, reverse=True))
    except Exception:
        pass
    allw = ["干货", "保姆级", "三连", "已收藏", "氛围感", "质感", "很到位",
            "不仅", "综上", "值得一提", "展现了", "赋能", "维度", "宝子", "同学", "感谢支持"]
    corpusw = ["干货", "保姆级", "三连", "已收藏", "氛围感", "质感", "很到位",
               "赋能", "维度", "宝子", "同学", "感谢支持"]
    return allw, corpusw


AI_SMELL, AI_SMELL_CORPUS = _ai_smell_words()
# 语料级还要剔这些：真人偶尔也说，但一个"按风格挑过"的训练集不该把模型往这儿带
CLICHE_CORPUS = ["绝了", "破防", "拿捏", "yyds", "封神", "土拨鼠", "懂的都懂", "硬控"]


def copied_sample(text, n=5):
    """是否整句抄了提示词里的亲笔样句。

    2026-11-20 实锚：把 6 条亲笔样句放进提示词后，模型直接吐出「封面是范伟老师是吧」——
    和样句一字不差。抄得越像越糟：老号的朋友一眼认出来这是自己说过的话。
    判据：与任一样句的最长公共子串 ≥ n 个汉字。
    """
    t = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", strip_reply_prefix(text or ""))
    if len(t) < n:
        return ""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "cph4", "fleet", "social", "HUMAN-PERSONA-v1.json")
    try:
        few = json.load(open(p, encoding="utf-8")).get("fewshot") or []
    except Exception:
        return ""
    for s in few:
        s2 = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s)
        for i in range(len(t) - n + 1):
            if t[i:i + n] in s2:
                return "抄样句：%s" % t[i:i + n]
    return ""


def hard_block(text, context=""):
    """硬拒（不扣分，直接不收）：这三类是"发出去就露馅"的，不该靠总分盖过去。

    2026-11-20 读样本实锚：
      · 「那配乐一响我瞬间泪目…」——"泪目"在 CLICHE 表里却拿了 84 分（只扣分不拒稿）；
      · 「我完全没听出 CONTENT。」——4-bit 模型幻觉出英文占位符；
      · 12 条里有 9 条用"那个/那"开头——单条看不出，连着发就是模板。
    """
    t = strip_reply_prefix(text or "")
    cli = [w for w in CLICHE if w in t]
    if cli:
        return "烂梗：%s" % "/".join(cli[:2])
    smell = [w for w in AI_SMELL if w in t]
    if smell:
        return "AI 腔：%s" % "/".join(smell[:2])
    # 引号包裹：只拦"整句被引号包起来"（模型抄样句格式的特征）。
    # 2026-11-21 回归实测：真人会引歌词（方文山写"天青色等烟雨"的时候…），
    # 一刀切"句内有引号就拒"会把他的话毙掉——判据必须窄到只抓格式。
    if re.match(r'^\s*[「“\"]', t) and re.search(r'[」”\"]\s*$', t):
        return "引号包裹/抄格式"
    # 表情码里的拉丁字母不算幻觉：2026-11-21 实测 [doge_金箍] 被当成"英文幻觉"，
    # 把真人句「这也是说唱 rap r&b[doge_金箍]」整句毙掉。先剥掉 [xxx] 再查。
    bare = re.sub(r"\[[^\]]{1,12}\]", "", t)
    latin = re.findall(r"[A-Za-z]{3,}", bare)
    # 正常内容里的英文：类型名/平台名/常见缩写，不许当幻觉（rap/BGM/MV/IPhone/CS…）
    ok_latin = {"BGM", "bgm", "MV", "mv", "UP", "up", "B站", "PR", "AI", "Vlog", "vlog",
                "rap", "RAP", "CS", "cs", "PS", "ps", "APP", "app", "V社", "GDP",
                "iPhone", "iPad", "PC", "pc", "TV", "DLC", "Steam", "steam", "LOL"}
    # 上下文白名单：标题/简介/简报里出现的英文词是内容不是幻觉。
    # 2026-11-21 实锚：「15 号比了嘛，16 号支持 BLG 啊！」被判"英文幻觉 BLG"，
    # 而 BLG 就是这条视频标题里的队名——闸没有上下文就会把专有名词当乱码。
    ctx = (context or "").lower()
    bad = [w for w in latin if w not in ok_latin and w.lower() not in ctx]
    if bad:
        return "英文幻觉：%s" % "/".join(bad[:2])
    # 非中文字符混入：2026-11-20 实测「镜头构图虽 Европы 但配乐还挺带感嘛」过了闸——
    # 拉丁字母检查只管 [A-Za-z]，西里尔/希腊/阿拉伯整段漏过去。
    foreign = re.findall(r"[\u0400-\u04FF\u0370-\u03FF\u0600-\u06FF\u0590-\u05FF]", t)
    if foreign:
        return "外文幻觉：%s" % "".join(foreign[:3])
    # 表情码破损：2026-11-21 实测模型写「[打 call]」「[doge ]」——发出去是裸文本，
    # 比不带表情更露馅（真人的表情码永远是紧贴的 [打call]）。
    for m in re.findall(r"\[[^\[\]]{1,12}\]", t):
        if re.search(r"\s", m):
            return "表情码破损：%s" % m
    cp = copied_sample(t)
    if cp:
        return cp
    return ""


def gen_gate(text, ctx=""):
    """**出稿闸**：只拦"发出去会露馅"的，不拿品味分当及格线。

    2026-11-21 回归实测（GATE-REGRESSION：亲笔 20 句 + 坏句 17 句）：
    用 `score(...)["verdict"] == "PASS"` 当出稿闸，亲笔句只有 **12% 能过**——
    「太喜欢这首歌了，没有之一。」「髮你哦」这种真话被判"逻辑不够"，
    而这是真人最自然的样子。反过来我们的坏句有 9/17 漏网（「别累着自己！」这类
    空心关心，词表永远抓不到）。所以：
      · 出稿闸 = 安全闸（AI 腔/烂梗/外文/抄样句）＋ 最低完整性（有汉字、不是纯表情/纯助兴）；
      · 品味分只用来**排序**（best-of-8 挑最好的一条），不再当一票否决。
    这就是 CEO 说的"不是只靠拦着"：闸管"不许烂"，排序管"尽量好"。
    """
    t = strip_reply_prefix(text or "")
    if not t:
        return False, "空"
    hb = hard_block(t, context=ctx)
    if hb:
        return False, hb
    if not CJK.search(t):
        return False, "无中文"
    bare = BRACKET_EMOJI.sub("", t)
    bare = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", bare)
    if len(bare) < 2:
        return False, "纯表情/纯符号"
    if FILLER.match(t):
        return False, "纯助兴"
    # 真人会写长句（回归集里有一条 81 字的说唱评论），60 字太窄；只防模型跑飞。
    if len(t) > 120:
        return False, "过长 %d" % len(t)
    return True, ""


def opening_key(text, n=2):
    """开头两个字：用来做"连发同款开头"的多样性检查（那个/那配/镜头…）。"""
    t = re.sub(r"[^\u4e00-\u9fff]", "", strip_reply_prefix(text or ""))
    return t[:n]


def score(text, seg=None):
    t = strip_reply_prefix(text)
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

    if REPLY.match(t) or len(t) < 4:
        d["flags"].append("剥掉@前缀后没剩下内容")

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
    pass_line, logic_line, short_ok = SEG_TUNE.get(seg, (60, 30, False))
    if short_ok and len(t) <= 16:
        # 该短的段：长度合适本身就是合格，不因为没有"具体对象"扣到不及格
        d["taste"] = min(20, d["taste"] + 5)
        total = d["logic"] + d["voice"] + d["human"] + d["taste"] + d["natural"]
    if len(cli) >= 2 or FILLER.match(t) or len(t) < 6:
        verdict = "REJECT"
    elif total >= pass_line and d["logic"] >= logic_line and not cli:
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
        # 批量筛选必须按段用段位判据——否则玩梗/浅层/挑刺这些"该短、该直"的段
        # 会被通用线误杀（实测 critic 27 条只剩 14 条）。颗粒度对齐就在这一行。
        try:
            sys.path.insert(0, HERE)
            import segments as _sg
            _spec = _sg.load_spec()
        except Exception:
            _spec = None
        for r in rows:
            seg = _sg.classify(r.get("text"), _spec)["primary"] if _spec else None
            s = score(r.get("text"), seg=seg)
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
