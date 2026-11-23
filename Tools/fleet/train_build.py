#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_build.py — 把清洗过的自有语料转成 mlx_lm LoRA 能直接吃的 jsonl。

数据口径（与 human_corpus.py 一致，不在这里二次放宽）：
  - 只吃 use=train 的行（reference/许可不明的一律不进）。
  - 长度 4-60 字：太短没有语感可学，太长（>60）多是搬运文案。
  - 去广告/联系方式/链接：训练集里混进一条"加V"就够模型学会拉客。
  - 同一句只留一条（归一化后哈希）。

切分按句长分层，避免 valid 全是长句或全是短句——那样 loss 曲线会骗人。

用法：
  python3 Tools/fleet/train_build.py                 # 默认读 own_collected.jsonl
  python3 Tools/fleet/train_build.py --valid-ratio 0.05
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "cph4", "fleet", "social", "corpus", "human", "own_collected.jsonl")
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "social", "train")

BAD = re.compile(r"(加\s*[Vv微]|微信|qq群|QQ群|http|www\.|扫码|私信我|代做|接单|付费)")
MIN_LEN, MAX_LEN = 4, 60

# 三个指令轮换：训练时模型见到的"提问方式"要有多样性，但都只许写评论本身。
# {title} 会在有视频标题时填进去——没有上下文的训练只会让模型学会"短"，
# 学不会"针对这条视频说点相关的话"（2026-11-17 对拍实锚：LoRA 只吐零碎片段）。
# 2026-11-18：三条模板里只有一条写了字数，结果模型只在遇到那条时才收口，
# 另外两条照样写到 60-100 字，产线上"太长"占失败原因四分之一。三万字语料里
# PASS 评论中位 22 字、P75=42，所以统一写 8-35 字——训练与推理共用这批模板，
# 两边口径必须一致（推理侧走 llm_client.lora_comment_prompt 复用同一份）。
_LEN = "8-35 字，一到两句话"
# 2026-11-20：实测实投文案语感 0.5/20（闸按"口语助词种类"计分）、人味 10.6/20。
# 问题不在模型，在指令从没要求过这两件事。训练与推理共用这份文本，改这里等于同时改两边。
# 2026-11-20：18 条实采里 6 条以"绝了"收句——这不是模型坏，是语料里这个词占比高，
# 指令没禁它。烂梗词与空夸词一样，必须在指令里点名禁，否则闸只能一条条拒（通过率 67%）。
# 2026-11-20 二次校正：原句把"具体细节"列成（镜头/剪辑/台词/配乐），18 条实采里
# 19 条以"镜头/配乐"开头——模型照抄清单第一项，等于把提示词变成了模板。
# 改成不枚举的写法，只要求"一个具体的东西"。
# 2026-11-21 CEO「要有平台相关用户的人味」：真实 B 站评论 20% 带表情码（memer 段 72%），
# 而我们生成的 0%——因为指令里从没提过这件事。表情码是平台语汇不是装饰，必须写进指令。
_HUMAN = ("像随口说话：带一两个语气词（吧/啊/呢/嘛/啦，放句尾），"
          "说一个具体的、看得见听得见的东西，可以带一个 B 站表情码（比如 [doge]/[笑哭]/[打call]），"
          "别用空夸词，也别写绝了、破防、拿捏、谁懂、泪目、干货、保姆级、三连这类词。")
INSTRUCTIONS = [
    "视频《{title}》{hint}。你在 B 站这条视频下面留评论。只写评论本身，" + _LEN + "。" + _HUMAN,
    "用 B 站观众的口吻，给《{title}》{hint}写一句真实评论，" + _LEN + "。" + _HUMAN,
    "刚看完《{title}》{hint}，写一句你最想说的话。就像平时在评论区那样，" + _LEN + "。" + _HUMAN,
]
INSTRUCTIONS_NOCTX = [
    "你在 B 站一条视频下面留评论。只写评论本身，" + _LEN + "，不要解释，不要加引号。" + _HUMAN,
    "用 B 站观众的口吻写一句真实评论，" + _LEN + "。" + _HUMAN,
    "看完这个视频，写一句你最想说的话。就像平时在评论区那样，" + _LEN + "。" + _HUMAN]


def phrase_keep(rows, df_cap=0.02, min_distinct=0.5, n=4):
    """口头禅抑制：按 4-gram 文档频率判断"这句话有没有自己的信息"。

    2026-11-17 实锚：LoRA 会连续吐「老师，求工作流，求工作流，求工作流」「已三连 老师
    老师 老师」。根因不是采样温度，是训练集里这类高频短语被反复喂——真实评论区里
    「求素材/已三连」本来就占比极高。做法：算每个 4-gram 的文档频率，一句话里若
    超过 df_cap 的 n-gram 占多数（distinct 比例 < min_distinct），它就是"只由高频
    短语拼出来的"，丢掉。保留有具体对象/具体描述的句子。
    """
    grams = []
    for r in rows:
        t = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", r["text"])
        grams.append({t[i:i + n] for i in range(max(1, len(t) - n + 1))})
    df = {}
    for gs in grams:
        for g in gs:
            df[g] = df.get(g, 0) + 1
    cap = max(2, int(len(rows) * df_cap))
    kept, dropped = [], 0
    for r, gs in zip(rows, grams):
        if not gs:
            kept.append(r)
            continue
        distinct = sum(1 for g in gs if df.get(g, 0) <= cap) / len(gs)
        if distinct < min_distinct:
            dropped += 1
            continue
        kept.append(r)
    return kept, dropped


def norm(t):
    return re.sub(r"\s+", " ", str(t or "")).strip()


def simhash(text, bits=64):
    """字符 3-gram SimHash。用于抓"换个标点/错别字再说一遍"的近重复。"""
    t = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text or "")
    if len(t) < 3:
        t = t or " "
    v = [0] * bits
    for i in range(max(1, len(t) - 2)):
        sh = t[i:i + 3]
        h = int(hashlib.md5(sh.encode("utf-8")).hexdigest()[:16], 16)
        for b in range(bits):
            v[b] += 1 if (h >> b) & 1 else -1
    return sum(1 << b for b in range(bits) if v[b] > 0)


def near_dedup(rows, hamming=6):
    """SimHash + 分带 LSH：同带相同再比汉明距，避免 O(n²) 全比。"""
    bands = 4
    width = 64 // bands
    seen_buckets = [{} for _ in range(bands)]
    kept, sigs, dropped = [], [], 0
    for r in rows:
        s = simhash(r["text"])
        hit = False
        for bi in range(bands):
            key = (s >> (bi * width)) & ((1 << width) - 1)
            for j in seen_buckets[bi].get(key, ()):
                if bin(sigs[j] ^ s).count("1") <= hamming:
                    hit = True
                    break
            if hit:
                break
        if hit:
            dropped += 1
            continue
        idx = len(sigs)
        sigs.append(s)
        for bi in range(bands):
            key = (s >> (bi * width)) & ((1 << width) - 1)
            seen_buckets[bi].setdefault(key, []).append(idx)
        kept.append(r)
    return kept, dropped


def self_test():
    """离线判据：去重/口头禅/长度/段位配额/切分。任何一条不过就是造集坏了。"""
    cases = []
    # 1 近重复：换个标点同一句必须被判重
    rows = [{"text": "这段转场真的很顺，学到了", "len": 12, "thread": "v1"},
            {"text": "这段转场真的很顺 学到了", "len": 12, "thread": "v1"},
            {"text": "结尾那个眼神我看了三遍", "len": 12, "thread": "v1"}]
    kept, dropped = near_dedup(rows, 6)
    cases.append(("近重复去掉 1 条", dropped == 1 and len(kept) == 2))
    # 2 不相似的两句都要留
    cases.append(("不同内容不误杀", any("眼神" in r["text"] for r in kept)))
    # 3 口头禅：高频短语拼出来的句子要丢
    dull = [{"text": "已三连"} for _ in range(20)] + [{"text": "老师求工作流呀"} for _ in range(20)]
    keep2, cut = phrase_keep(dull + [{"text": "这个抠像边缘处理得很干净"}], df_cap=0.1,
                             min_distinct=0.5)
    cases.append(("口头禅句被去掉", cut >= 1))
    cases.append(("有信息的句子保留", any("抠像" in r["text"] for r in keep2)))
    # 4 长度过滤：太短太长都不进
    ap_ = argparse.Namespace(src="", out="", valid_ratio=0.05, seed=1, danmaku_max=1.0,
                             danmaku_min_len=6, min_taste=0, near_dup_hamming=0,
                             per_video_max=0, seg_cap=0, min_distinct=0, df_cap=0.02)
    cases.append(("长度上下界合理", MIN_LEN == 4 and MAX_LEN == 60))
    # 5 SimHash 稳定性：同一文本签名必须一致
    cases.append(("SimHash 稳定", simhash("同一句话") == simhash("同一句话")))
    # 6 反 AI 腔：真发出去被否的句子必须被剔，真人句必须留下（负控）
    cases.append(("AI 腔被剔", bool(ai_smell("教程太干货了，必须三连支持！"))))
    cases.append(("烂梗被剔", bool(ai_smell("那个转场绝了，氛围感拿捏得死死的"))))
    cases.append(("真人句放行", ai_smell("封面是范伟老师是吧") == ""))
    cases.append(("拉丁词不误杀", ai_smell("CS 那版手感比这个好") == ""))
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


RECIPE = "v5-shape-quota"     # 造集配方版本：变了就该重训（train_forever 认这个）
# 2026-11-21 v5 理由：句式配额（短评补到 45%，贴近真实 38%）+ 语感配额；
# 旧数据集陈述句占 76–80%、短评只 7%，模型因此只会写整句——这是"样本都一样"的根。
# v4 理由：语料级反 AI 腔硬筛（4.0% 行）+ 自举语料并入 + 亲笔长度分布。
# 配方一变，train_forever 会把每一段都当成"新的一课"重训，这是有意为之：
# 拿旧配方训出来的件不能证明新配方没用，留着它反而会让"已训过"挡住重训。

KIND_SHARE = {"question": 0.25, "critique": 0.20, "experience": 0.30, "praise": 0.25}


def _kind(text):
    t = text or ""
    if "？" in t or "?" in t:
        return "question"
    praise_only = any(w in t for w in ("感谢", "已三连", "太干货", "收藏", "学到了"))
    if any(w in t for w in ("不", "没", "别", "差", "烂", "难", "踩", "浪费", "没必要")) and not praise_only:
        return "critique"
    if "我" in t and any(w in t for w in ("剪过", "试过", "看了", "做过", "学了", "用过", "卡在", "搞不懂")):
        return "experience"
    return "praise"


def _ask_floor():
    """提问+挑刺的下限，来自 TUNE-PARAMS.json（单源），取不到用 0.20。

    CEO 令是"每 10 条要 2-3 条提问或挑刺"；真实语料本身 27.4%，
    所以这只是下限保护，不是重配比目标——默认仍复刻真实分布。
    """
    try:
        p = json.load(open(os.path.join(ROOT, "cph4", "fleet", "social", "TUNE-PARAMS.json"),
                           encoding="utf-8"))
        return float((p.get("ask_floor") or {}).get("value") or 0.20)
    except Exception:
        return 0.20


def balance_kinds(rows, rnd, quota=False):
    """话语类型配比 + "开头"配额。

    2026-11-20 决策：**默认不再人工重配比**（只做开头配额）。实测真实语料
    提问 25.1% / 挑刺 2.3% / 夸奖 15.1%，而旧的重配比把训练集做成
    提问 9% / 挑刺 36% / 夸奖 55% —— 模型"只会泛夸"是我们自己喂出来的，
    不是模型能力问题。训练分布必须复刻真实分布，否则越训越像水军。
    只保留 CEO 定的一条下限：提问+挑刺合计 ≥20%，低于就吼出来。
    quota=True 时恢复旧的按配额重配（仅供对照实验，不是默认路径）。
    """
    if quota:
        pools = {}
        for r in rows:
            pools.setdefault(_kind(r["text"]), []).append(r)
        total = len(rows)
        out, leftover = [], []
        for kind, share in KIND_SHARE.items():
            pool = pools.get(kind) or []
            rnd.shuffle(pool)
            quota_n = int(total * share)
            take = min(quota_n, len(pool))
            out.extend(pool[:take])
            leftover.extend(pool[take:])
        slots = total - len(out)
        if slots > 0:
            rnd.shuffle(leftover)
            out.extend(leftover[:slots])
    else:
        out = list(rows)
    total = len(out)

    # 开头配额：任何"前两个字"不得超过 2%（上限 8 条），否则满屏"那个/这个"
    cap = max(8, int(total * 0.02))
    seen, kept = {}, []
    rnd.shuffle(out)
    for r in out:
        k = re.sub(r"[^\u4e00-\u9fff]", "", r["text"])[:2]
        if seen.get(k, 0) >= cap:
            continue
        seen[k] = seen.get(k, 0) + 1
        kept.append(r)
    rnd.shuffle(kept)
    return kept


def ai_smell(text):
    """**语料级**反 AI 腔判据：这句话本身是不是我们不想让模型学会的腔调。

    2026-11-21 CEO「你不是只靠拦着，而是从根本上训练好」——闸只能一条条拒，
    语料里留着这类句子等于把 AI 腔当正样本教。两个来源都要清：
      · own_practice.jsonl 里我们自己发过、后来被否的句子（标注还写着"已过全部闸"）；
      · 爬来的评论里本来就有的营销腔/客服腔。
    注意用 AI_SMELL_CORPUS 而不是 AI_SMELL：作文连接词（而且/不仅）真人也在用，
    拿输出级的严表洗语料会多删 700+ 条正常句子（实测）。
    返回命中原因，空串=可进训练集。
    """
    try:
        sys.path.insert(0, HERE)
        import comment_taste as ct
    except Exception:
        return ""
    t = text or ""
    smell = [w for w in ct.AI_SMELL_CORPUS if w in t]
    if smell:
        return "AI 腔：" + "/".join(smell[:2])
    cli = [w for w in ct.CLICHE_CORPUS if w in t]
    if cli:
        return "烂梗：" + "/".join(cli[:2])
    return ""


def train_floor(t):
    """训练语料的**合规底线**——不是出稿闸。

    为什么分开（2026-11-23 实证）：短评补齐原用 ct.gen_gate()（出稿闸），而 shallow 段
    REJECT 里 95% 是短评 → 短评补不进来（只到 25%，真实 B 站 37%）。根因=拿"我们敢发的
    标准"去筛"真人怎么说话"。底线只拦：AI 腔/烂梗、纯表情数字、广告导流、单字废话。
    """
    t = (t or "").strip()
    if len(t) < 3 or ai_smell(t):
        return False
    core = re.sub(r"\[[^\]]{1,10}\]", "", t)          # 去 [doge] 这类表情码
    core = re.sub(r"[\s\W_]+", "", core)
    if len(core) < 2 or re.fullmatch(r"\d+", core):
        return False
    for w in ("关注我", "加我", "私信", "微信", "扫码", "领券", "返现"):
        if w in t:
            return False
    return True


def top_up_short(rows, seg, quota, src, spec=None, max_len=10):
    """把"短评"（≤10 字）补到 quota 占比。

    2026-11-21 实测（CEO「训练样本各种行为都要不一样」）：真实 B 站评论句式分布是
    陈述 49% / **短评 38%** / 疑问 8% / 感叹 5%，而我们的数据集陈述 76–80%、短评只有 5–15%。
    原因是过滤链（长度≥4、品味≥60、人味≥5）把短句系统性筛掉了，模型于是只会写整句。
    这里按真实比例回补短评，只补过得出稿闸、非 AI 腔、同段、未重复的行。
    """
    import comment_taste as ct
    import segments as sg
    def _short(t):
        return len(re.sub(r"\[[^\]]{1,10}\]", "", t or "")) <= max_len
    cur = sum(1 for r in rows if _short(r["text"]))
    need = int(len(rows) * max(0.0, quota) - cur)
    if need <= 0:
        return rows, 0
    seen = {r.get("h") for r in rows}
    spec = spec or sg.load_spec()
    picked = []
    for line in open(src, encoding="utf-8"):
        if len(picked) >= need:
            break
        if not line.strip():
            continue
        r = json.loads(line)
        h, t = r.get("h"), (r.get("text") or "").strip()
        if not h or h in seen or not t or r.get("dup_of") or r.get("use") != "train":
            continue
        if not (MIN_LEN <= len(t) <= MAX_LEN) or not _short(t):
            continue
        # 优先补"平铺短句"：带 ！/? 的短句会被句式统计算成感叹/疑问，
        # 补一堆"好家伙！"并不能改善句式分布（2026-11-21 实测：补 130 条，短评只涨 6pp）
        if ("！" in t or "!" in t or "？" in t or "?" in t):
            continue
        if not train_floor(t):
            continue
        if seg and sg.classify(t, spec)["primary"] != seg:
            continue
        seen.add(h)
        picked.append({"h": h, "text": t, "len": len(t), "kind": r.get("kind"),
                       "origin": r.get("origin") or "comment", "thread": r.get("thread")})
    return rows + picked, len(picked)


def top_up_voice(rows, seg, quota, src, spec=None):
    """把带口语语气词的样本补到 quota 占比。

    2026-11-21 实测：shallow 数据 voice 均分 3.0/20、69% 的行一个语气词都没有，
    而 CEO 要的"人味和自然"主要落在这一维。真人不是每句都带（他亲笔只有 22% 带），
    所以目标不是拉满，而是**保底三成**——模型才会学到"什么时候该带"。
    只补过得出稿闸、非 AI 腔、长度合规的行，且与现有行不重复。
    """
    import comment_taste as ct
    import segments as sg
    cur = sum(1 for r in rows if ct.score(r["text"]).get("voice", 0) >= 8)
    need = int(len(rows) * max(0.0, quota) - cur)
    if need <= 0:
        return rows, 0
    seen = {r.get("h") for r in rows}
    spec = spec or sg.load_spec()
    picked = []
    for line in open(src, encoding="utf-8"):
        if len(picked) >= need:
            break
        if not line.strip():
            continue
        r = json.loads(line)
        h = r.get("h")
        t = (r.get("text") or "").strip()
        if not h or h in seen or not t or r.get("dup_of"):
            continue
        if r.get("use") != "train" or ai_smell(t):
            continue
        if not (MIN_LEN <= len(t) <= MAX_LEN):
            continue
        if seg and sg.classify(t, spec)["primary"] != seg:
            continue
        if not ct.gen_gate(t)[0] or ct.score(t).get("voice", 0) < 8:
            continue
        seen.add(h)
        picked.append({"h": h, "text": t, "len": len(t), "kind": r.get("kind"),
                       "origin": r.get("origin") or "comment", "thread": r.get("thread")})
    return rows + picked, len(picked)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUTDIR)
    ap.add_argument("--valid-ratio", type=float, default=0.05)
    ap.add_argument("--ban-ai", type=int, default=1,
                    help="语料级反 AI 腔硬筛（1=开，默认）。关掉只为做对照实验")
    ap.add_argument("--short-quota", type=float, default=0.45,
                    help="短评（≤10 字）至少占比。真实 B 站评论 38% 是短评，"
                         "而过滤链会把短句筛掉，导致模型只会写整句")
    ap.add_argument("--voice-quota", type=float, default=0.30,
                    help="带口语语气词（voice>=8）的样本至少占比。2026-11-21 实测："
                         "数据里 voice 均分只有 3.0/20、69% 为 0，而这一维就是'像人说话'；"
                         "但全改会做作，所以只保三成")
    ap.add_argument("--target-rows", type=int, default=0,
                    help="目标行数：硬阈值砍太狠时，从'没硬伤但分不够'的池里按分回填到该数"
                         "（0=不补）。2026-11-21 实测 shallow 只剩 293/4396，必须回填")
    ap.add_argument("--danmaku-max", type=float, default=0.35,
                    help="弹幕最多占训练集的比例（弹幕多是碎片，比例过高会把模型教成半句）")
    ap.add_argument("--danmaku-min-len", type=int, default=6,
                    help="弹幕短于此长度不进训练集（真人评论一般 6 字以上）")
    ap.add_argument("--min-taste", type=int, default=60,
                    help="品味判据线（comment_taste.py 总分，0=不筛）")
    ap.add_argument("--near-dup-hamming", type=int, default=6,
                    help="SimHash 近重复阈值（汉明距 ≤ 该值即视为重复；0=关闭）")
    ap.add_argument("--per-video-max", type=float, default=0.2,
                    help="单个视频最多占总样本比例（防一条爆火视频盖住全部语气）")
    ap.add_argument("--seg-cap", type=float, default=0.3,
                    help="单个人群段最多占训练集比例（0=不限）")
    ap.add_argument("--seg", default="",
                    help="只保留该人群段的行（万人万面用）。不传=全集。"
                         "2026-11-18 实锚：不给这个开关时，--out train-craft_learner 里"
                         "craft_learner 只占 18%，训出来仍是平均嗓")
    ap.add_argument("--min-human", type=int, default=0,
                    help="人味分下限（comment_taste.human_feel；0=不筛）")
    ap.add_argument("--min-distinct", type=float, default=0.5,
                    help="句内 4-gram 里低频（有信息）占比下限；低于此值视为口头禅句，0=关闭")
    ap.add_argument("--df-cap", type=float, default=0.02,
                    help="4-gram 文档频率高于该比例视为高频短语")
    ap.add_argument("--seed", type=int, default=20261117)
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    if not os.path.exists(a.src):
        print("[build] 找不到语料 %s（先跑 human_corpus.py --from-dir）" % a.src)
        return 2

    seen, rows, dropped = set(), [], {"dup": 0, "len": 0, "bad": 0, "use": 0}
    pool = []          # 回填候选：没硬伤、只是分不够高的行（见 --target-rows）
    for line in open(a.src, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("use") != "train":
            dropped["use"] += 1
            continue
        t = norm(r.get("text"))
        if not (MIN_LEN <= len(t) <= MAX_LEN):
            dropped["len"] += 1
            continue
        if BAD.search(t):
            dropped["bad"] += 1
            continue
        h = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
        if h in seen:
            dropped["dup"] += 1
            continue
        seen.add(h)
        if a.ban_ai:
            why = ai_smell(t)
            if why:
                dropped.setdefault("ai_smell", 0)
                dropped["ai_smell"] += 1
                dropped.setdefault("ai_smell_why", {})
                k = why.split("：")[0]
                dropped["ai_smell_why"][k] = dropped["ai_smell_why"].get(k, 0) + 1
                continue
        if a.min_human > 0:
            try:
                import comment_taste as _ct2
                hv = _ct2.human_feel(t)
                if hv < a.min_human:
                    dropped.setdefault("human", 0)
                    dropped["human"] += 1
                    # 留作回填候选：没硬伤，只是分数不够高。**两个分都记**，
                    # 否则回填门槛只能看一半（2026-11-21 踩过：只记 _hf 时品味下限失效）。
                    try:
                        _tt = int(_ct2.score(t).get("total") or 0)
                    except Exception:
                        _tt = 0
                    pool.append({"h": h, "text": t, "len": len(t), "kind": r.get("kind"),
                                 "origin": r.get("origin") or "comment",
                                 "thread": r.get("thread"), "_score": int(hv),
                                 "_hf": int(hv), "_tt": _tt})
                    continue
            except Exception:
                a.min_human = 0
        origin = r.get("origin") or "comment"
        if origin == "danmaku" and len(t) < a.danmaku_min_len:
            dropped.setdefault("danmaku_short", 0)
            dropped["danmaku_short"] += 1
            continue
        # 品味判据：真实≠好。只学"逻辑顺、有语感、有人味、有品味、不做作"的样本，
        # 否则模型会同时学会两种病——AI 文案腔和评论区碎片腔（2026-11-17 两轮实锚）。
        if a.min_taste > 0:
            try:
                sys.path.insert(0, HERE)
                import comment_taste as ct
                s = ct.score(t)
                if s["total"] < a.min_taste or s["verdict"] == "REJECT":
                    dropped.setdefault("taste", 0)
                    dropped["taste"] += 1
                    pool.append({"h": h, "text": t, "len": len(t), "kind": r.get("kind"),
                                 "origin": origin, "thread": r.get("thread"),
                                 "_score": int(s.get("human") or 0) + int(s.get("voice") or 0),
                                 "_hf": None, "_tt": int(s.get("total") or 0)})
                    continue
            except Exception as e:
                print("[build] 品味闸不可用（%s），本次不筛" % str(e)[:60])
                a.min_taste = 0
        rows.append({"h": h, "text": t, "len": len(t), "kind": r.get("kind"),
                     "origin": origin, "thread": r.get("thread")})

    # 按来源分层抽样：弹幕只占 danmaku_max。弹幕是"看片时脱口而出的半句"，
    # 评论才是"看完之后能说完整一句话"，两者比例失控，模型就会只学碎片
    # （2026-11-17 实锚：全量混合训练后 LoRA 输出「也许是这种在数字世界中」「虽然超4K」）。
    dm = [r for r in rows if r["origin"] == "danmaku"]
    cm = [r for r in rows if r["origin"] != "danmaku"]
    if a.danmaku_max < 1.0 and dm:
        cap = int(len(cm) * a.danmaku_max / max(1e-6, 1 - a.danmaku_max))
        if len(dm) > cap:
            rows = cm + sorted(dm, key=lambda r: -r["len"])[:cap]
            dropped["danmaku_over"] = len(dm) - cap
        else:
            rows = cm + dm
    print("[build] 来源 评论 %d 条 / 弹幕 %d 条（弹幕上限 %.0f%%）"
          % (len(cm), min(len(dm), max(0, len(rows) - len(cm))), a.danmaku_max * 100))

    # 近重复去重（社区通行做法：MinHash/SimHash + LSH，精确哈希挡不住"换个错别字再说一遍"）。
    # B站评论区实际大量"求素材""已三连""哈哈哈哈"的同义改写，留着就会训成口头禅。
    if a.near_dup_hamming > 0:
        rows, nd = near_dedup(rows, a.near_dup_hamming)
        dropped["near_dup"] = nd
        print("[build] 近重复去掉 %d 条（SimHash 汉明距 ≤%d）→ 剩 %d"
              % (nd, a.near_dup_hamming, len(rows)))

    # 口头禅抑制（放在近重复之后、单源上限之前：先把"只由高频短语拼成"的句子剔掉）
    if a.min_distinct > 0 and rows:
        rows, dull = phrase_keep(rows, df_cap=a.df_cap, min_distinct=a.min_distinct)
        dropped["phrase_dull"] = dull
        print("[build] 口头禅抑制去掉 %d 条（4-gram 高频占多数）→ 剩 %d" % (dull, len(rows)))

    # 单视频上限：一条爆火视频能给上千条评论，不设上限就会让一个视频的语气
    # 盖住全部（DEITA 的 diversity 那一维，落到我们这里就是"别让单源主导"）。
    # 2026-11-18 实锚：这一行原来被上一行注释吞掉（`）。    if ...`），
    # 上限从未生效，日志里只有"单段上限"没有"单视频上限"——整份训练集可能被一条爆款主导。
    if a.per_video_max and rows:
        cap = max(20, int(len(rows) * a.per_video_max))
        by = {}
        for r in rows:
            by.setdefault(r.get("thread") or "", []).append(r)
        kept, drop_v = [], 0
        for th, items in by.items():
            items.sort(key=lambda r: -r["len"])
            kept += items[:cap]
            drop_v += max(0, len(items) - cap)
        if drop_v:
            rows = kept
            dropped["per_video_over"] = drop_v
            print("[build] 单视频上限 %d 条（%.0f%%）→ 去掉 %d 条，剩 %d"
                  % (cap, a.per_video_max * 100, drop_v, len(rows)))


    # 段位打标 + 单段配额（颗粒度对齐：语料/训练/生成/评测用同一套段位）
    if a.seg_cap:
        sys.path.insert(0, HERE)
        try:
            import segments as sg
            spec = sg.load_spec()
            # 2026-11-21：优先用 corpus_classify.py 产出的 seg2（嵌入聚类 + 本地模型命名）。
            # 关键词分类器把 71% 的行判成 generic，等于每段都在用"平均嗓"的数据训练；
            # seg2 只覆盖判过的行，没判到的照旧用关键词结果。
            seg2 = {}
            p2 = os.path.join(ROOT, "cph4", "fleet", "social", "corpus", "human", "SEG2.jsonl")
            if os.path.exists(p2):
                for line in open(p2, encoding="utf-8"):
                    if line.strip():
                        o = json.loads(line)
                        if o.get("h") and o.get("seg2"):
                            seg2[o["h"]] = o["seg2"]
            n2 = 0
            for r in rows:
                if r.get("h") in seg2:
                    r["seg"] = seg2[r["h"]]
                    n2 += 1
                else:
                    r["seg"] = sg.classify(r["text"], spec)["primary"]
            # 回填池也要打段标，否则过滤后补不进来
            for r in pool:
                if r.get("h") in seg2:
                    r["seg"] = seg2[r["h"]]
                else:
                    r["seg"] = sg.classify(r["text"], spec)["primary"]
            if n2:
                print("[build] 用 seg2（嵌入聚类）覆盖 %d 行分段" % n2)
            cap_seg = max(20, int(len(rows) * a.seg_cap))
            byseg = {}
            for r in rows:
                byseg.setdefault(r["seg"], []).append(r)
            kept, cut = [], 0
            for s_, items in byseg.items():
                items.sort(key=lambda r: -r["len"])
                kept += items[:cap_seg]
                cut += max(0, len(items) - cap_seg)
            if cut:
                rows = kept
                dropped["seg_over"] = cut
            print("[build] 段位分布 %s" % dict(sorted(
                ((k, len(v)) for k, v in byseg.items()), key=lambda kv: -kv[1])))
            if a.seg:
                before = len(rows)
                rows = [r for r in rows if r.get("seg") == a.seg]
                print("[build] 只留段 %s：%d → %d 行（该段原占 %.0f%%）"
                      % (a.seg, before, len(rows), 100.0 * len(rows) / max(before, 1)))
            if cut:
                print("[build] 单段上限 %d 条（%.0f%%）→ 去掉 %d 条，剩 %d"
                      % (cap_seg, a.seg_cap * 100, cut, len(rows)))

        except Exception as e:
            print("[build] 段位打标不可用（%s），本跳过" % str(e)[:60])

    # 回填放在**分段过滤之后**：--seg 会把别的段剔掉，回填必须在剩下这一段里补，
    # 否则补进来的还是别的段（2026-11-21 第一次实现踩的坑：回填跑在过滤前，一行没补上）。
    # 硬阈值砍太狠时按 (人味+语感) 从"没硬伤但分不够"的池里补到目标行数；
    # 安全闸（AI 腔/硬拒/长度/广告）一律不吃回填。
    if a.target_rows and len(rows) < a.target_rows and pool:
        # 回填也要看质量：2026-11-21 实测——严格集 278 条总分均 78.9，无门槛回填到
        # 1,006 条掉到 52.7，训练学的是均值，于是 lora 只比基座 +4.4（前一次严格集是 +21.1）。
        # 所以只从"人味 ≥4 且品味 ≥55"的次优里补，宁可少也不要稀。
        cand = [r for r in pool if not a.seg or r.get("seg") == a.seg]
        cand = [r for r in cand if (r.get("_hf") is None or r.get("_hf") >= 4)
                and (r.get("_tt") is None or r.get("_tt") >= 55)]
        need = min(len(cand), a.target_rows - len(rows))
        cand.sort(key=lambda r: -r.get("_score", 0))
        add = cand[:need]
        for r in add:
            r.pop("_score", None)
        rows.extend(add)
        dropped["backfill"] = len(add)
        print("[build] 回填 %d 条（目标 %d）：只从没硬伤、但人味/品味分不够的池里按分取"
              % (len(add), a.target_rows))

    if len(rows) < 100:
        print("[build] 只有 %d 条可用，太少（至少 100 才有意义）" % len(rows))
        return 2

    if a.short_quota > 0 and rows:
        rows, added_s = top_up_short(rows, a.seg, a.short_quota, a.src)
        if added_s:
            dropped["short_topup"] = added_s
            print("[build] 补短评 %d 条（短句补到 %.0f%%，真实分布 38%%）"
                  % (added_s, a.short_quota * 100))

    if a.voice_quota > 0 and rows:
        rows, added_v = top_up_voice(rows, a.seg, a.voice_quota, a.src)
        if added_v:
            dropped["voice_topup"] = added_v
            print("[build] 补语感样本 %d 条（带语气词的行补到 %.0f%%）"
                  % (added_v, a.voice_quota * 100))

    rnd = random.Random(a.seed)
    quota = (os.environ.get("FLUX_BUILD_KIND_QUOTA") == "1"
             and os.environ.get("FLUX_BUILD_NO_BALANCE") != "1")
    if os.environ.get("FLUX_BUILD_NO_BALANCE") != "1":
        rows = balance_kinds(rows, rnd, quota=quota)
        kinds = {}
        for r in rows:
            # 优先用烘焙侧的 kind（8 类，单一事实来源）；没有才退回本文件的 4 分类
            k = r.get("kind") or _kind(r["text"])
            kinds[k] = kinds.get(k, 0) + 1
        tot = max(len(rows), 1)
        print("[build] 配比（%s）：%s（共 %d 行）" % (
            "配额重配" if quota else "复刻真实",
            " ".join("%s %.0f%%" % (k, 100.0 * v / tot) for k, v in
                     sorted(kinds.items(), key=lambda x: -x[1])), len(rows)))
        ask = 100.0 * (kinds.get("提问", 0) + kinds.get("挑刺", 0)) / tot
        floor = _ask_floor() * 100
        if ask < floor:
            print("[build] ⚠ 提问+挑刺只占 %.0f%%（CEO 门槛 ≥%.0f%%），这批训出来会偏泛夸"
                  % (ask, floor))

    # 按句长分桶后层内切分，valid 的长度分布跟着 train 走
    buckets = {}
    for r in rows:
        key = "s" if r["len"] < 10 else ("m" if r["len"] < 25 else "l")
        buckets.setdefault(key, []).append(r)
    train, valid = [], []
    for key, items in buckets.items():
        rnd.shuffle(items)
        k = max(1, int(len(items) * a.valid_ratio))
        valid += items[:k]
        train += items[k:]
    rnd.shuffle(train)
    rnd.shuffle(valid)

    os.makedirs(a.out, exist_ok=True)
    # 视频标题表：由 sweep 侧取一次落盘（VIDEO-TITLES.json），这里只做 join。
    # 简介也要进来——只给标题，模型只能猜内容，猜就是幻觉（实锚：「黄渤你拍啥呢」）。
    titles = {}
    tp = os.path.normpath(os.path.join(os.path.dirname(a.src), "..", "..", "VIDEO-TITLES.json"))
    if os.path.exists(tp):
        try:
            titles = json.load(open(tp, encoding="utf-8"))
        except Exception:
            titles = {}
    n_ctx = 0
    for name, group in (("train.jsonl", train), ("valid.jsonl", valid)):
        p = os.path.join(a.out, name)
        with open(p, "w", encoding="utf-8") as f:
            for i, r in enumerate(group):
                meta = titles.get(r.get("thread") or "") or {}
                title = (meta.get("title") or "").strip()
                desc = (meta.get("desc") or "").strip()
                if title:
                    n_ctx += 1
                    hint = "（简介：%s）" % desc[:50] if desc else ""
                    ins = INSTRUCTIONS[i % len(INSTRUCTIONS)].format(
                        title=title[:40], hint=hint)
                    if r.get("seg"):
                        try:
                            import segments as _sg
                            ins += " " + _sg.style_block(r["seg"])
                        except Exception:
                            pass
                else:
                    ins = INSTRUCTIONS_NOCTX[i % len(INSTRUCTIONS_NOCTX)]
                # 224 的序列上限里，user 太长会把 assistant 整个挤掉；
                # 配合 --mask-prompt 就是"没有可学的 token"→ loss nan（2026-11-20 实锚）。
                MAX_USER = 240   # 训练侧 max-seq-length 已提到 320；这里留出 assistant 的空间
                if len(ins) > MAX_USER:
                    ins = INSTRUCTIONS[i % len(INSTRUCTIONS)].format(
                        title=title[:20], hint="")
                    if r.get("seg"):
                        try:
                            import segments as _sg
                            ins += " " + _sg.style_block(r["seg"])
                        except Exception:
                            pass
                if len(ins) > MAX_USER:
                    ins = "视频《%s》。写一句真人评论：带一个语气词、用「我」+具体细节，8-35 字。" % title[:20]
                msg = {"messages": [
                    {"role": "user", "content": ins},
                    {"role": "assistant", "content": r["text"]},
                ]}
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        print("[build] %s %d 条 → %s" % (name, len(group), p))
    print("[build] 带视频上下文的样本 %d / %d（含简介 %d）"
          % (n_ctx, len(train) + len(valid),
             sum(1 for r in train + valid
                 if (titles.get(r.get("thread") or "") or {}).get("desc"))))

    src_sha = hashlib.sha256(open(a.src, "rb").read()).hexdigest()[:16]
    stat = {"src": os.path.relpath(a.src, ROOT), "src_sha": src_sha,
            "train": len(train), "valid": len(valid),
            "avg_len": round(sum(r["len"] for r in rows) / len(rows), 1),
            "dropped": dropped, "seed": a.seed, "valid_ratio": a.valid_ratio,
            "by_len": {k: len(v) for k, v in buckets.items()}}
    json.dump(stat, open(os.path.join(a.out, "STATS.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[build] 可用 %d 条（丢掉 重复%d/长度%d/广告%d/非train%d）均值 %.1f 字"
          % (len(rows), dropped["dup"], dropped["len"], dropped["bad"], dropped["use"],
             stat["avg_len"]))
    if dropped.get("ai_smell"):
        print("[build] 反 AI 腔剔除 %d 条（%s）——这些句子是教会模型说腔调的源头，"
              "不是一个一个拦得住的"
              % (dropped["ai_smell"],
                 "/".join("%s %d" % (k, v) for k, v in (dropped.get("ai_smell_why") or {}).items())))
    print("[build] 语料指纹 %s" % src_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
