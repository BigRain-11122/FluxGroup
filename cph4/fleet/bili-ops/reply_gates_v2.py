# -*- coding: utf-8 -*-
# B站回复机械闸 v2.1 —— CEO 10-14 令「机械闸优于 prompt 自觉」的执法面
# v2.1 修订：+strip_think 生产剥离器（反引号形近围栏根治）·G4 纯梗豁免（troll/meme/超短句）·G9 emoji 禁·G10 波浪号频次
# 用法: python reply_gates_v2.py <replies.json>   (replies.json = [{tag,comment,reply}, ...])
# 每条回复跑 G1-G10 十道闸，fail=重摇信号（调用方重摇≤3 次→仍 fail 跳过不发送）
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

# G1 客服敬语/客服话术黑名单（B站语境最大 AI 感来源）
G1_FORBIDDEN = ["您", "非常感谢", "感谢您的", "期待您", "我们会继续", "持续关注",
                "敬请期待", "祝您", "愿你", "更多精彩", "继续支持", "多多支持", "您的支持",
                "非常抱歉", "亲爱的", "亲~", "祝您观看愉快"]

# G2 升华/总结收尾禁
G2_ENDING_BAN = ["希望未来", "带来更好的", "更好的作品", "继续努力", "不忘初心", "越做越好", "未来可期", "让我们", "一起期待"]

# G5 排比/对仗模板禁（AI 结构性口头禅）
G5_STRUCT = [r"既.{1,6}又", r"不仅.{1,8}还", r"既是.{1,6}又是", r"一方面.{1,10}另一方面"]

# G8 框架泄漏/引号残留
G8_LEAK = ['^[\'"]', '[\'"]$', "作为一名", "作为一个AI", "作为一个 ?ai", r"^回复[:：]", r"^UP主[:：]\s*回复"]

# G9 emoji/颜文字（真人 UP 回复基本不发·文字梗除外）
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")

STOPWORDS = set("这个 那个 什么 怎么 为什么 哪个 哪些 就是 还是 感觉 真的 可以 应该 但是 而且 然后 现在 以后 时候 东西 这样 那样 是不是 有没有 自己 大家 评论 视频 up主 UP主".split())

try:
    import jieba
except ImportError:
    jieba = None


def content_words(text):
    # v2.2：jieba 分词正身（G4 执法面）——旧版"整段连续汉字单词"bug 就地根治
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
    # G3 长度窗 6-45
    if n < 6: fails.append("G3太短:%d" % n)
    elif n > 45: fails.append("G3太长:%d" % n)
    # G4 具体性：与评论共享 ≥1 个实词（troll/meme 与 ≤12 字纯梗句豁免——punchline 是人味不是 AI 味）
    if tag not in ("troll", "meme") and n > 12 and not (content_words(r) & content_words(c)):
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
    # G8 框架泄漏
    for pat in G8_LEAK:
        if re.search(pat, r):
            fails.append("G8泄漏:" + pat); break
    # G9 emoji/颜文字
    if EMOJI_RE.search(r):
        fails.append("G9emoji")
    # G10 波浪号 ≥2（AI 招牌语气污染）
    if r.count("\uff5e") + r.count("~") >= 2:
        fails.append("G10波浪号")
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
