# -*- coding: utf-8 -*-
# B站回复 v4.1 生产管线（bm-b 2026-10-20）
# v4 教训：评分函数奖励"语气词数量"→模型学会堆"吧啊哈哈"。v4.1 改为「模板惩罚 + 锚词覆盖 + 长度窗」，
# 语气词只作轻微惩罚（>1 个扣分）。择优点=过闸候选里分最高者。
import json, re, sys, time, urllib.request

sys.path.insert(0, r"E:\Fluxgroup\.codely-cli")
from reply_gates_v2 import sanitize, check, content_words

API = "http://127.0.0.1:11434/api/generate"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
MODEL = sys.argv[1] if len(sys.argv) > 1 else "bili-reply-v32"
COMMENTS = r"E:\Fluxgroup\.codely-cli\bili_test_comments.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"E:\Fluxgroup\.codely-cli\bili_sim_out_v41.json"
TEMPS = [0.8, 0.9, 1.0, 1.1]
ROUNDS = 2  # 最多 8 候选/条（7B GPU 约 1.5s/次，多采样＝更高上限）

AI_TEMPLATES = ["确实", "其实", "感谢支持", "谢谢夸奖", "期待你的", "希望未来"]
# v4.2 空话表：只表态不给具体信息的套句（Goodhart 教训：只奖锚词复述会养出"X确实挺Y"）
HOLLOW = ["技术活", "很重要", "挺专业", "挺有意思", "提升不少", "进步了不少", "效果提升",
          "挺方便的", "挺常用", "挺好用", "加油", "厉害", "挺不错", "行之有效", "多练"]
CREATOR = ["参数", "卡点", "节奏", "帧率", "导出", "渲染", "音轨", "素材", "模板", "剪辑",
           "调", "录", "拍", "改", "熬夜", "翻车", "手滑", "重录", "死磕", "剪"]
SELF_DEP = ["其实我", "我当时", "我一般", "我是", "我那", "我这", "我手", "我懒", "我菜"]
TONE = "吧啊嘛呗哈呀呢哦咯"


def gen(comment, temp):
    payload = {"model": MODEL, "prompt": comment, "stream": False, "think": False,
               "options": {"num_ctx": 2048, "temperature": temp, "top_p": 0.9,
                           "top_k": 30, "repeat_penalty": 1.12}}
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with OPENER.open(req, timeout=300) as r:
        out = json.loads(r.read().decode("utf-8"))
    return out.get("response", ""), round(time.time() - t0, 1)


def score(reply, comment, prev):
    """v5 口径：不再奖励任何特定词（Goodhart 教训：奖励"熬到凌晨"就句句熬到凌晨）。
    只保留：锚词覆盖 + 模板/空话惩罚 + 语气词上限 + 长度窗 + 跨条新颖度。"""
    n = len(reply)
    s = 0.0
    s += 0.6 * min(2, len(content_words(reply) & content_words(comment)))
    s -= 1.2 * sum(1 for w in AI_TEMPLATES if w in reply)
    s -= 1.0 * sum(1 for w in HOLLOW if w in reply)
    tones = sum(reply.count(ch) for ch in TONE)
    if tones > 1:
        s -= 0.6 * (tones - 1)
    if n < 12:
        s -= 0.8
    elif n > 38:
        s -= (n - 38) * 0.08
    if reply.startswith("哈哈"):
        s -= 1.5
    # 跨条新颖度：与前 5 条已发回复的 3-gram 重合率（复读=最强 AI 感信号）
    if prev:
        def grams(t):
            t = re.sub(r"\s+", "", t)
            return set(t[i:i + 3] for i in range(len(t) - 2))
        g = grams(reply)
        if g:
            worst = max(len(g & grams(p)) / len(g) for p in prev[-5:])
            s -= 3.0 * worst
    return round(s, 2)


def main():
    comments = json.load(open(COMMENTS, encoding="utf-8"))
    results, prev = [], []
    n_pass = 0
    for i, c in enumerate(comments, 1):
        rec = dict(c)
        rec["attempts"] = []
        cands = []
        for rnd in range(ROUNDS):
            for temp in TEMPS:
                try:
                    raw, sec = gen(c["comment"], temp)
                except Exception as e:
                    rec["attempts"].append({"temp": temp, "reply": "", "fails": ["GEN_ERROR:%s" % e], "sec": 0})
                    continue
                reply = sanitize(raw)
                fails = check({"tag": c.get("tag", ""), "comment": c["comment"], "reply": reply}, prev)
                sc = None if fails else score(reply, c["comment"], prev)
                rec["attempts"].append({"temp": temp, "round": rnd + 1, "reply": reply,
                                        "fails": fails, "sec": sec, "score": sc})
                print("[%d/%d] %s r%d t=%.2f %s %r %s" % (
                    i, len(comments), c.get("tag"), rnd + 1, temp, sc, reply, fails or ""), flush=True)
                if not fails:
                    cands.append((sc, reply))
            if cands:
                break
        if cands:
            best = max(cands)
            rec.update({"reply": best[1], "passed": True, "final_fails": [], "best_score": best[0],
                        "n_pass_cands": len(cands)})
            prev.append(best[1])
            n_pass += 1
        else:
            last = rec["attempts"][-1] if rec["attempts"] else {"reply": "", "fails": ["no_attempt"]}
            rec.update({"reply": last["reply"], "passed": False, "final_fails": last["fails"]})
        results.append(rec)
        json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nSIM_DONE pass=%d/%d model=%s" % (n_pass, len(comments), MODEL), flush=True)


if __name__ == "__main__":
    main()

