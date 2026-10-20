# -*- coding: utf-8 -*-
# B站回复机械闸 v2.3 —— CEO 10-14 令「机械闸优于 prompt 自觉」的执法面
# v2.1 修订：+strip_think 生产剥离器（反引号形近围栏根治）·G4 纯梗豁免（troll/meme/超短句）·G9 emoji 禁·G10 波浪号频次
# v2.3 修订：+sanitize 生产净化器（整体引号包裹直接脱壳）·G8 成对包裹检·G11 引用一致性（引号内文字必须能在评论里找到·防编造）
# v2.4 修订：G4 加具体回答词表豁免（被问软件直接答剪映/PR 是好人味不是万能回复）·G12 分段禁·G13 反问逃避禁·G14 文艺鸡汤词禁
# v2.6 修订：G7b 长片段复读（6 字片段跨条重合即判）·G15 中英混杂·G1 补客服承诺语/谢谢开场
# 用法: python reply_gates_v2.py <replies.json>   (replies.json = [{tag,comment,reply}, ...])
# 每条回复跑 G1-G11 十一道闸，fail=重摇信号（调用方重摇≤3 次→仍 fail 跳过不发送）
import json, re, sys

# ---- 思考剥离器（生产端生成后必跑；qwen3 思考闭合标签 </think> 实测定谳·反引号形近围栏留兜底） ----
THINK_END_RE = re.compile(r"</\s*think\s*>", re.I)
FENCE_RE = re.compile("[`\u0060\u02cb\u02cc\u02cd\u02ce\u02cf\u1fef\uff40]{2,}")
def strip_think(text):
    t = (text or "").strip()
    if THINK_END_RE.search(t):
        t = THINK_END_RE.split(t)[-1].strip()
    else:
        m = list(FENCE_RE.finditer(t))
        if m:
            t = t[m[-1].end():].strip()
    return t

QUOTE_PAIRS = {"\"": "\"", "'": "'", "“": "”", "‘": "’", "「": "」", "『": "』"}
QUOTED_RE = re.compile(r"[“\"「『‘']([^”\"」』’']{2,})[”\"」』’']")


def unwrap_quotes(text):
    # 模型爱把整句回复用引号包一层（v2 #10 实锚）；生产端直接脱壳，别靠重摇
    t = (text or "").strip()
    while len(t) >= 2 and t[0] in QUOTE_PAIRS and t[-1] == QUOTE_PAIRS[t[0]]:
        t = t[1:-1].strip()
    return t


def sanitize(text):
    # 生产端生成后统一走这里：剥思考段 → 脱整句引号壳 → 去 emoji → 去单句句末句号
    # 句末句号=强 AI 信号：真人语料 78% 不带（bilibot 12951 条），本地生成 90% 都带
    t = strip_think(text)
    t = unwrap_quotes(t)
    t = EMOJI_RE.sub("", t)
    t = re.sub(r"\s+$", "", t).strip()
    if t.endswith("。") and "。" not in t[:-1]:
        t = t[:-1]
    return t

# G4 同义归一：字面不重合但语义接住的真人话不该被判万能回复（v3.1 #7 实锚「确实比那期强点」vs「比之前那个强多了」）
SYN_GROUPS = [
    ("之前", ["那期", "上一期", "前一期", "上次那", "前一部", "原来的", "之前那"]),
    ("完整", ["完整版", "全片", "成片", "整段"]),
    ("强", ["强多", "更猛", "更炸", "厉害了", "更顶", "好多了"]),
    ("软件", ["工具", "app", "什么软件"]),
]


def canon(text):
    t = text
    for head, alts in SYN_GROUPS:
        for w in alts:
            t = t.replace(w, head)
    return t

# G1 客服敬语/客服话术黑名单（B站语境最大 AI 感来源）
G1_FORBIDDEN = ["您", "非常感谢", "感谢您的", "期待您", "我们会继续", "持续关注",
                "敬请期待", "祝您", "愿你", "更多精彩", "继续支持", "多多支持", "您的支持",
                "非常抱歉", "亲爱的", "亲~", "祝您观看愉快",
                "争取早日", "早日上线", "尽快上线", "感谢支持", "谢谢夸奖",
                "谢谢！", "谢谢，", "感谢！", "感谢，"]

# G2 升华/总结收尾禁
G2_ENDING_BAN = ["希望未来", "带来更好的", "更好的作品", "继续努力", "不忘初心", "越做越好", "未来可期", "让我们", "一起期待"]

# G5 排比/对仗模板禁（AI 结构性口头禅）
G5_STRUCT = [r"既.{1,6}又", r"不仅.{1,8}还", r"既是.{1,6}又是", r"一方面.{1,10}另一方面"]

# G8 框架泄漏/引号残留
G8_LEAK = ['^[\'"]', '[\'"]$', "作为一名", "作为一个AI", "作为一个 ?ai", r"^回复[:：]", r"^UP主[:：]\s*回复",
           r"/\s*[A-Za-z]{2,}\s*$", r"\bsoftware\b", r"<\|", r"\[/?INST\]"]

# G9 emoji/颜文字（真人 UP 回复基本不发·文字梗除外）
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")

STOPWORDS = set("这个 那个 什么 怎么 为什么 哪个 哪些 就是 还是 感觉 真的 可以 应该 但是 而且 然后 现在 以后 时候 东西 这样 那样 是不是 有没有 自己 大家 评论 视频 up主 UP主".split())

# G4 豁免词表：被问「什么软件/工具/设备」时直接点名具体软件=真回答（v3 #4 实锚：剪映/PR/达芬奇被判万能回复）
ANSWER_LEXICON = ["剪映", "pr", "ae", "ps", "达芬奇", "davinci", "blender", "ffmpeg", "fcp", "final cut",
                  "obs", "au", "达芬奇", "喵影", "必剪", "秀米", "c4d", "nuke", "houdini", "comfyui"]
# G13 反问逃避（AI 最典型的接不住就跑）
G13_ECHO_ASK = [r"你猜", r"你信不信", r"你也试试", r"你觉不觉得", r"你觉得呢", r"你说是吧", r"对不对\?", r"是吧\?"]
# G14 文艺鸡汤词（真人深夜回评论不这么说话）
G14_SOUP = ["灵魂摆渡", "碳基生物", "情绪价值", "人间清醒", "守护初心", "岁月静好", "治愈"]

try:
    import jieba
except ImportError:
    jieba = None


def content_words(text):
    # v2.5：先同义归一，再 jieba 分词（G4 执法面）
    text = canon(text)
    if jieba is not None:
        return set(w for w in jieba.lcut(text) if len(w) >= 2 and w not in STOPWORDS)
    words = set()
    for run in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", text):
        for L in range(2, min(6, len(run)) + 1):
            for i in range(0, len(run) - L + 1):
                w = run[i:i + L]
                if w not in STOPWORDS:
                    words.add(w)
    return words

def three_grams(text):
    t = re.sub(r"\s+", "", text)
    return set(t[i:i+3] for i in range(len(t) - 2))

def check(rec, prev_replies):
    r = rec.get("reply", "").strip()
    c = rec.get("comment", "")
    tag = rec.get("tag", "")
    fails = []
    if not r:
        return ["empty"]
    n = len(re.sub(r"\s+", "", r))
    # G1 客服话术
    for w in G1_FORBIDDEN:
        if w in r:
            fails.append("G1客服腔:" + w); break
    # G2 升华收尾（末 12 字窗内命中即判）
    tail = r[-12:]
    for w in G2_ENDING_BAN:
        if w in tail:
            fails.append("G2升华结尾:" + w); break
    # G3 长度窗 6-70（真人语料 p75=75 字·中位 38，原 45 上限把真人感的长回复全判死）
    if n < 6: fails.append("G3太短:%d" % n)
    elif n > 70: fails.append("G3太长:%d" % n)
    # G4 具体性：与评论共享 ≥1 个实词（troll/meme 与 ≤12 字纯梗句豁免）；被问软件答具体软件名视同接梗
    if tag not in ("troll", "meme") and n > 12 and not (content_words(r) & content_words(c)):
        low = r.lower()
        answered = any(k in low for k in ANSWER_LEXICON)
        if not answered:
            fails.append("G4零接梗(万能回复)")
    # G5 排比结构
    for pat in G5_STRUCT:
        if re.search(pat, r):
            fails.append("G5排比:" + pat); break
    # G6 近 5 条同头复读
    if prev_replies:
        head = re.sub(r"\s+", "", r)[:2]
        for p in prev_replies[-5:]:
            if head and re.sub(r"\s+", "", p)[:2] == head:
                fails.append("G6同头复读:" + head); break
    # G7 近 30 条 3-gram 重复率（防口头禅吸引子，10-14 "DNA动了"×3 根治面）
    if prev_replies:
        hist = set()
        for p in prev_replies[-30:]:
            hist |= three_grams(p)
        g = three_grams(r)
        if g:
            overlap = len(g & hist) / len(g)
            if overlap > 0.35:
                fails.append("G7口头禅复读:%.0f%%" % (overlap * 100))
    # G7b 长片段复读：任 6 字片段与前 10 条已发回复重合即判（"熬到凌晨两点"跨条复现实锚）
    if prev_replies:
        body = lambda t: re.sub(r"[\s。，！？,.!?～~…]", "", t)
        rb = body(r)
        for p in prev_replies[-10:]:
            pb = body(p)
            hit = next((rb[i:i + 6] for i in range(len(rb) - 5) if rb[i:i + 6] in pb), None)
            if hit:
                fails.append("G7b长片段复读:" + hit); break
    # G8 框架泄漏 / 成对引号包裹
    for pat in G8_LEAK:
        if re.search(pat, r):
            fails.append("G8泄漏:" + pat); break
    if len(r) >= 2 and r[0] in QUOTE_PAIRS and r[-1] == QUOTE_PAIRS[r[0]]:
        fails.append("G8整句引号包裹")
    # G11 引用一致性：引号内的文字必须能在评论里找到（防编造台词/歌词·v2 #6 实锚）
    cn = re.sub(r"\s+", "", c)
    for m in QUOTED_RE.finditer(r):
        seg = re.sub(r"\s+", "", m.group(1))
        if len(seg) >= 3 and seg not in cn:
            fails.append("G11疑似编造引用:" + seg[:8]); break
    # G9 emoji/颜文字
    if EMOJI_RE.search(r):
        fails.append("G9emoji")
    # G10 波浪号 ≥2（AI 招牌语气污染）
    if r.count("\uff5e") + r.count("~") >= 2:
        fails.append("G10波浪号")
    # G12 分段/换行（回复是一条弹幕式短句，不是小作文）
    if "\n" in r.strip():
        fails.append("G12分段")
    # G13 反问逃避
    for pat in G13_ECHO_ASK:
        if re.search(pat, r):
            fails.append("G13反问逃避:" + pat); break
    # G14 文艺鸡汤
    for w in G14_SOUP:
        if w in r:
            fails.append("G14鸡汤词:" + w); break
    # G15 中英混入（7B 实锚：dozen/feel/software 这类英文词混进中文口语）
    latin = re.findall(r"[A-Za-z]{3,}", r)
    if latin and not all(x.lower() in ("davinci", "comfyui", "blender", "houdini", "ffmpeg") for x in latin):
        fails.append("G15中英混杂:" + latin[0])
    return fails

def main():
    path = sys.argv[1]
    data = json.load(open(path, encoding="utf-8"))
    prev = []
    passed = 0
    for rec in data:
        fails = check(rec, prev)
        rec["gates"] = fails
        if not fails: passed += 1
        print("[%s] %s -> %s" % ("PASS" if not fails else "FAIL", rec.get("tag", "?"), rec.get("reply", "")))
        if fails: print("        闸点: %s" % "; ".join(fails))
        prev.append(rec.get("reply", ""))
    print("\n通过率: %d/%d" % (passed, len(data)))

if __name__ == "__main__":
    main()
