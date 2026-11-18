#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_comment_gen.py - 给"别人的视频"写养号评论：三条车道并发出稿，过闸才进队列。

为什么要有它（2026-11-18 实测后的执行动作）：
  · 8788 的 LoRA 是按「视频《X》…你在 B 站这条视频下面留评论」训的——它擅长写**观众评论**，
    并不擅长写"客服式回复"。拿它回私信是用错地方，用它去别人视频下留评论才是本职。
  · 本机实测：单条 4B 41 tok/s，三条车道（LoRA+4B+2B）56-62 tok/s 就到顶，第四条不涨。
    既然并行只在"不同模型"上有效，出稿就该按模型分车道并发，而不是同一模型堆请求。

出口纪律（一条都不能省）：
  1 `comment_taste` 五维闸 PASS 才算可用；WARN 只登记不进队列；
  2 `voice_gate` BLOCK 一律丢；
  3 与本批已选、与本机语料都不许有 8 字以上连续重合（"每条独写无模板"的机检口径）；
  4 产出只是**待发草稿**，发送权在 CEO——本工具永不发帖。

用法：
  python3 Tools/fleet/social_comment_gen.py --self-test
  python3 Tools/fleet/social_comment_gen.py --videos 15 --per 1     # 默认走全车道
  python3 Tools/fleet/social_comment_gen.py --lanes lora --videos 5  # 只验一条车道
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(DIR, "VIDEO-TITLES.json")
CORPUS = os.path.join(DIR, "corpus", "human", "own_collected.jsonl")
OUT = os.path.join(DIR, "comment-queue.jsonl")
SCREEN = os.path.join(DIR, "COMMENT-QUEUE.md")

sys.path.insert(0, HERE)
import comment_taste as ct          # noqa: E402
import llm_client as lc            # noqa: E402
import voice_gate as vg            # noqa: E402

# 车道：不同模型才涨吞吐（同模型堆请求不涨）。label 只用于落账归因。
# 车道：不同模型才涨吞吐（同模型堆请求不涨）。keep_alive 显式给 6h——
# 服务端默认 10m，不钉住的话跑完一批三条车道就掉回一条，"60 tok/s" 变成纸面数字。
KEEP = "6h"
LANES = {
    "lora": lambda p: lc.generate_lora(p, max_tokens=60, temperature=0.85),
    "4b": lambda p: lc.generate(p, model="qwen3.5:4b-mlx", think=False,
                                num_predict=60, keep_alive=KEEP),
    "2b": lambda p: lc.generate(p, model="qwen3.5:2b", think=False,
                                num_predict=60, keep_alive=KEEP),
}

# 站外导流/身份披露：机器不许碰，命中即丢（发送权与身份口径都在 CEO）
# 长度上限取语料 P95 而不是手感：3466 条 PASS 评论里中位 22 字、P90=70、P95=86、P99=111，
# 只有 14% 超过 60 字。第一版拍脑袋写 60，把 14% 的真评论连同模型正常输出一起判死，
# 失败原因里"太长"占了四分之一——这是尺子问题，不是模型啰嗦。
MAXLEN = 90

# 生成侧的硬红线（2026-11-18 实锚：队列里生成出「@漫泰视觉，你们这些大 V 太无耻了，
# 居然盗我的教程还能卖钱！」——冒充受害者 + 指控真实账号，发出去就是诽谤。
# 这类内容不能只靠发前拦，必须在生成时就判死，否则它会一直堆在队列里等人手滑。）
DEFAME = re.compile(r"(盗|抄|剽窃|骗|侵权|无耻|起诉|维权|律师|抄袭)")
AT_MENTION = re.compile(r"@[\w\u4e00-\u9fff]{1,20}")
MD_TELL = re.compile(r"(\*\*|##|```|\[.*\]\(.*\))")

REDLINE = re.compile(r"(加|扫)(微|V|v)|私信我|微信|公众号|企鹅|qq|QQ|vx|VX|"
                     r"我是(学生|老师|博主|up|UP)|本人是|学的?就是")


def shared_run(a, b, k=8):
    """最长公共子串是否达到 k 字——防止照抄语料或两批之间撞句。"""
    if len(a) < k or len(b) < k:
        return ""
    win = {b[i:i + k] for i in range(len(b) - k + 1)}
    for i in range(len(a) - k + 1):
        s = a[i:i + k]
        if s in win:
            return s
    return ""


def corpus_texts(limit=6000):
    out = []
    try:
        for i, line in enumerate(open(CORPUS, encoding="utf-8")):
            if i >= limit:
                break
            if line.strip():
                t = json.loads(line).get("text") or ""
                if len(t) >= 8:
                    out.append(t)
    except Exception:
        pass
    return out


def gate(text, ctx="", taken=(), corpus=(), face="viewer"):
    """返回 (ok, 原因, 评分明细)。ok=False 时原因一句话，能直接看懂。

    face 决定用哪把尺子（2026-11-18 实锚，别再搞混）：
      · viewer = 我方以观众身份去别人视频下留评论 → 感叹号与 20-40 字都正常，
        只限量不批格式；质量交给 comment_taste（它是拿 3 万条真实评论标定的）。
      · reply  = 我方以创作者身份回复观众 → 才适用 voice_gate 那套（禁感叹号、≤40 字、
        不客服腔），因为那是人设口径。
    拿 reply 的规矩去量 viewer 稿子，会把"这雪配毛茸茸也太治愈了！！"这种真评论判死，
    那是尺子错，不是模型差。
    """
    t = (text or "").strip().strip("“”\"'")
    if len(t) < 6:
        return False, "太短", {}
    if REDLINE.search(t):
        return False, "踩红线（导流/身份）", {}
    if AT_MENTION.search(t):
        return False, "点名他人（@提及）", {}
    if DEFAME.search(t):
        return False, "指控/维权类（易构成诽谤）", {}
    if MD_TELL.search(t):
        return False, "带 Markdown 痕迹（一眼 AI）", {}
    if face == "reply":
        v = vg.check(t, "comment", ctx)
        if v["verdict"] == "BLOCK":
            return False, "语感闸:%s" % ",".join(v["hits"][:2]), {}
    else:
        if len(t) > MAXLEN:
            return False, "太长(%d>%d)" % (len(t), MAXLEN), {}
        if t.count("！") + t.count("!") > 2:
            return False, "感叹号堆砌", {}
    s = ct.score(t)
    if s["verdict"] != "PASS":
        return False, "品味闸 %s(%d)" % (s["verdict"], s["total"]), s
    for x in taken:
        hit = shared_run(t, x)
        if hit:
            return False, "与本批重复「%s」" % hit, s
    for x in corpus:
        hit = shared_run(t, x)
        if hit:
            return False, "照抄语料「%s」" % hit, s
    return True, "", s


def gen_one(lane, title, desc, i):
    """一条车道出一稿；失败返回 None（不抛，缺一条车道不该拖垮整批）。"""
    prompt = lc.lora_comment_prompt(title, desc, i=i)
    try:
        r = LANES[lane](prompt)
    except Exception as e:
        return {"lane": lane, "ok": False, "why": "%s: %s" % (type(e).__name__, str(e)[:60])}
    if not r.get("ok"):
        return {"lane": lane, "ok": False, "why": r.get("why") or "空"}
    return {"lane": lane, "ok": True, "text": r["text"].strip()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", type=int, default=15, help="取多少条视频")
    ap.add_argument("--per", type=int, default=1, help="每条视频最终留几条")
    ap.add_argument("--lanes", default=",".join(LANES))
    ap.add_argument("--offset", type=int, default=0, help="切片起点（多进程并行用）")
    ap.add_argument("--limit", type=int, default=0, help="切片长度（0=不限）")
    ap.add_argument("--workers", type=int, default=0,
                    help="CPU 闸工位数（0=自动 ncpu-2）；GPU 侧按车道数并发")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    lanes = [x for x in a.lanes.split(",") if x in LANES]
    try:
        vids = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        print("[comment] 没有 VIDEO-TITLES.json，先跑采集")
        return 2
    # 跨批不重复：已进队列的句子算"已选"，已出过稿的视频默认跳过（重跑同一批
    # 只会产近重复，白烧算力——这是第二轮起才补的，第一轮靠 taken 只在本批内生效）。
    done_v, taken = set(), []
    try:
        for line in open(OUT, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                taken.append(r.get("text") or "")
                done_v.add(r.get("video") or "")
    except FileNotFoundError:
        pass
    items = [(k, v) for k, v in vids.items()
             if (v or {}).get("title") and k not in done_v]
    if a.offset or a.limit:
        items = items[a.offset:(a.offset + a.limit) if a.limit else None]
    else:
        items = items[:a.videos]
    corpus = corpus_texts()
    print("[comment] 已完成视频 %d 条（跳过）· 本批新视频 %d 条" % (len(done_v), len(items)))
    print("[comment] 视频 %d 条 · 车道 %s · 语料 %d 条" % (len(items), lanes, len(corpus)))

    # ---- 三段流水 ----
    # 为什么：原来是一个 for 循环里"出稿(GPU)→过闸(CPU)→下一条"，两边轮流空转。
    # 实测 CPU 空闲 68%、GPU 85%，说明它们本来可以重叠。这里拆成：
    #   生产者线程(=车道数)：只做出稿请求（占 GPU）
    #   消费者线程池(=ncpu-2)：只做 gate/去重/打分（占 CPU）
    import queue as _q
    from concurrent.futures import ThreadPoolExecutor
    workers = a.workers or max(2, (os.cpu_count() or 4) - 2)
    gen_q, gate_q = _q.Queue(maxsize=max(8, workers * 2)), _q.Queue()
    rows, t0 = [], time.time()
    taken_lock = threading.Lock()

    def producer():
        for n, (url, meta) in enumerate(items):
            got = {}

            def work(lane, u=url, m=meta, idx=n):
                got[lane] = gen_one(lane, m["title"], m.get("desc") or "", idx)

            ths = [threading.Thread(target=work, args=(x,)) for x in lanes]
            [x.start() for x in ths]
            [x.join() for x in ths]
            gen_q.put((n, url, meta, dict(got)))
        gen_q.put(None)

    def consumer():
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while True:
                item = gate_q.get()
                if item is None:
                    return
                n, url, meta, got = item
                ctx = (meta["title"] or "")[:40]
                futs = []
                for lane in lanes:
                    r = got.get(lane) or {}
                    if not r.get("ok"):
                        continue
                    futs.append((lane, pool.submit(gate, r["text"], ctx, (), corpus)))
                cands = []
                for lane, fu in futs:
                    ok, why, s = fu.result()
                    cands.append({"lane": lane, "text": got[lane]["text"], "ok": ok,
                                  "why": why, "score": (s or {}).get("total", 0)})
                with taken_lock:                      # 跨视频去重是顺序语义，只在这一步串行
                    good = sorted([c for c in cands if c["ok"]],
                                  key=lambda c: -c["score"])[:a.per]
                    for c in good:
                        if any(shared_run(c["text"], x) for x in taken):
                            continue
                        taken.append(c["text"])
                        rows.append({"ts": datetime.now().isoformat(timespec="seconds"),
                                     "video": url, "title": ctx, "text": c["text"],
                                     "lane": c["lane"], "taste": c["score"],
                                     "needs_human": True})
                print("  [%d/%d] %s → %s" % (n + 1, len(items), ctx[:24],
                                             "留「%s」(%s/%d)" % (good[0]["text"][:20],
                                                                 good[0]["lane"], good[0]["score"])
                                             if good else
                                             "全不过：" + "；".join(
                                                 "%s=%s" % (c["lane"], c["why"][:14])
                                                 for c in cands)[:70]))

    pt = threading.Thread(target=producer, daemon=True)
    ct_ = threading.Thread(target=consumer, daemon=True)
    pt.start(); ct_.start()
    while True:
        item = gen_q.get()
        if item is None:
            gate_q.put(None)
            break
        gate_q.put(item)
    ct_.join()
    print("[comment] 流水线：车道 %d ｜ CPU 闸工位 %d" % (len(lanes), workers))

    for n, (url, meta) in enumerate([]):
        title, desc = meta["title"], meta.get("desc") or ""
        ctx = title[:40]
        res = {}

        def work(lane):
            res[lane] = gen_one(lane, title, desc, i=n)

        th = [threading.Thread(target=work, args=(x,)) for x in lanes]
        [t.start() for t in th]
        [t.join() for t in th]

        cands = []
        for lane in lanes:
            r = res.get(lane) or {}
            if not r.get("ok"):
                continue
            ok, why, s = gate(r["text"], ctx=ctx, taken=taken, corpus=corpus)
            cands.append({"lane": lane, "text": r["text"], "ok": ok, "why": why,
                          "score": (s or {}).get("total", 0)})
        good = sorted([c for c in cands if c["ok"]], key=lambda c: -c["score"])[:a.per]
        for c in good:
            taken.append(c["text"])
            rows.append({"ts": datetime.now().isoformat(timespec="seconds"),
                         "video": url, "title": ctx, "text": c["text"],
                         "lane": c["lane"], "taste": c["score"], "needs_human": True})
        print("  [%d/%d] %s → %s" % (n + 1, len(items), ctx[:24],
                                     "留「%s」(%s/%d)" % (good[0]["text"][:20], good[0]["lane"],
                                                          good[0]["score"]) if good else
                                     "全不过：" + "；".join(
                                         "%s=%s" % (c["lane"], c["why"]) for c in cands)[:80]))

    os.makedirs(DIR, exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    by_lane = {}
    for r in rows:
        by_lane[r["lane"]] = by_lane.get(r["lane"], 0) + 1
    write_screen(rows, len(items), lanes, by_lane, time.time() - t0)
    print("[comment] 可用 %d 条（%d 视频，车道 %s）→ %s"
          % (len(rows), len(items), by_lane, os.path.relpath(OUT, ROOT)))
    return 0 if rows else 1


def write_screen(rows, n_videos, lanes, by_lane, secs):
    L = ["# 养号评论待发队列 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), "",
         "- 视频 %d 条 · 车道 %s · 可用 %d 条 · 用时 %.0fs"
         % (n_videos, ",".join(lanes), len(rows), secs),
         "- 归因（哪条车道出稿）：%s" % (by_lane or "无"),
         "- 纪律：只是草稿，发送权在 CEO；站外导流/身份披露/照抄语料一律已挡", "",
         "| # | 视频 | 评论 | 车道 | 品味分 |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows[:40], 1):
        L.append("| %d | %s | %s | %s | %d |"
                 % (i, r["title"][:18], r["text"][:44].replace("|", "/"), r["lane"], r["taste"]))
    open(SCREEN, "w", encoding="utf-8").write("\n".join(L) + "\n")


def self_test():
    """判据必须能红：造三条坏样例，闸不放行才算有闸。"""
    cases = [
        ("照抄语料", "这一期剪映的知识点比较密集，真正的干货", ["这一期剪映的知识点比较密集，真正的干货，要多嚼几遍"], False),
        ("导流红线", "加微信看更多精彩内容", [], False),
        ("空/表情", "🌨️👀👀", [], False),
        ("短", "好看", [], False),
    ]
    ok = 0
    for name, text, corpus, want in cases:
        got, why, _ = gate(text, corpus=corpus)
        good = (got == want)
        ok += 1 if good else 0
        print("  [%s] %s → %s（%s）" % ("PASS" if good else "FAIL", name,
                                       "放行" if got else "拦下", why))
    # 正向：必须拿**品味闸自己认过的语料**当样例（手写"好句子"不算数——
    # 本轮实锚：我自拟的那句被判 RISKY(60)，说明尺子量的是人味不是文采）。
    real, got, why = "", False, "语料里取不到 PASS 样例"
    try:
        for line in open(os.path.join(DIR, "corpus", "human", "QUALITY-PASS.jsonl"),
                         encoding="utf-8"):
            if not line.strip():
                continue
            cand = (json.loads(line).get("text") or "").strip()
            if 12 <= len(cand) <= 40:
                real = cand
                break
    except Exception:
        pass
    if real:
        got, why, _ = gate(real)            # corpus=[]：样例本身就在语料里，别自我撞车
    print("  [%s] 正向样例 → %s（%s）" % ("PASS" if got else "FAIL",
                                          "放行" if got else "拦下", why))
    ok += 1 if got else 0
    total = len(cases) + 1
    print("[self-test] %d/%d" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
