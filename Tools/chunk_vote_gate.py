# ===== 不适用·外审实测否证（2026-09-30）=====
# 本工具经实测【判定不可靠】，保留仅为留存证据，请勿用于生产判定。
# 详见 docs/audits/LOCAL-MODEL-PLAIN-20260930.md
# ==========================================
#!/usr/bin/env python3
# chunk_vote_gate.py -- 片段投票闸（最终方案·全本地·零 token）
#
# 为什么是这个形态（三步实证）：
#   ① 三分类提示词（CLAIM/BAN/EXEMPT/OTHER）失败——模型对所有件都答 BAN（无区分度）
#   ② 二选一提示词（用 / 禁）成功——模型能分："用"=主张用该方向，"禁"=禁止或否证该方向
#   ③ 但文档是混合的（清单里有"禁"、声明里有"非"），故必须按片段投票，不能整篇判一类
# 判据（跑前写死）：
#   claim_chunks >= 2 且 claim 多于 ban -> FLAG（真主张，重发派工单）
#   claim_chunks == 1                    -> WATCH（单点，人工看）
#   否则                                  -> CLEAN（清单/声明/否证类，排除）
# 用法: python Tools/chunk_vote_gate.py --candidates docs/audits/fused-scan-30d.log
#       python Tools/chunk_vote_gate.py --dir research --days 30 --limit 36
import argparse, glob, json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "qwen3:8b"
OLLAMA = "http://127.0.0.1:11434/api/generate"

# 每个禁开方向一条"最直白"的描述（越短越准，实测二选一形式有效）
DIRS = {
    "BAN-01": "买近期涨幅最大的、追涨强者（横截面动量）",
    "BAN-02": "买跌得最多的、超跌反转（横截面反转）",
    "BAN-03": "1-15天短线、隔日或日内反转动量",
    "BAN-04": "网格交易：按价格阶梯挂单、格距买卖",
    "BAN-05": "大盘水温/市场广度作为择时前置",
    "BAN-06": "站上均线才买、前20日为正等确认型前置",
    "BAN-07": "小市值/低价股选股",
    "BAN-08": "缓冲区/无交易带以降换手",
    "BAN-09": "风格延续、追上年最强风格",
}

PROMPT = """下面文字是在【提出要用】{desc}，还是在【禁止/已否证】它？

文字：{seg}

只回答一个字：用 或 禁。"""


def gen(prompt, model=MODEL, timeout=240):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0, "num_ctx": 4096}}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore")).get("response", "").strip()


def vote(path, chunk=1200, step=900):
    t = open(path, encoding="utf-8", errors="ignore").read()
    res = {}
    for bid, desc in DIRS.items():
        use = ban = 0
        for s in range(0, max(1, len(t)), step):
            seg = t[s:s + chunk]
            if len(seg) < 150:
                break
            out = gen(PROMPT.format(desc=desc, seg=seg))[:4]
            if "用" in out:
                use += 1
            elif "禁" in out:
                ban += 1
        if use or ban:
            res[bid] = {"use": use, "ban": ban}
    return res


def verdict(res):
    flagged = [b for b, v in res.items() if v["use"] >= 2 and v["use"] > v["ban"]]
    watch = [b for b, v in res.items() if v["use"] == 1 and v["use"] >= v["ban"]]
    if flagged:
        return "FLAG", flagged
    if watch:
        return "WATCH", watch
    return "CLEAN", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    files = []
    if a.candidates:
        p = os.path.join(ROOT, a.candidates)
        for line in open(p, encoding="utf-8", errors="ignore"):
            m = re.match(r"\s*\S+\s+(\S+\.md)", line)
            if m:
                g = glob.glob(os.path.join(ROOT, "quant", "bigmoney", "research", "**", m.group(1)),
                              recursive=True)
                if g:
                    files.append(g[0])
        files = list(dict.fromkeys(files))
    else:
        cutoff = time.time() - a.days * 86400
        d = os.path.join(ROOT, "quant", "bigmoney", "research")
        files = [f for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True)
                 if os.path.getmtime(f) > cutoff]
    if a.limit:
        files = files[:a.limit]
    print(f"待判文件 {len(files)} 件｜模型 {MODEL}", flush=True)

    rows = []
    for i, f in enumerate(files, 1):
        res = vote(f)
        v, ids = verdict(res)
        if v != "CLEAN":
            rows.append({"file": os.path.relpath(f, ROOT).replace("\\", "/"),
                         "verdict": v, "bans": ids, "votes": {k: res[k] for k in ids}})
        print(f"  [{i}/{len(files)}] {v:<6} {os.path.basename(f)[:44]:<44} {','.join(ids)}", flush=True)

    flag = [r for r in rows if r["verdict"] == "FLAG"]
    watch = [r for r in rows if r["verdict"] == "WATCH"]
    print(f"\nFLAG={len(flag)}  WATCH={len(watch)}  CLEAN={len(files)-len(rows)}")
    out = os.path.join(ROOT, "docs", "audits", "chunk-vote-verdicts.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": MODEL,
                   "files": len(files), "flag": flag, "watch": watch}, fh, ensure_ascii=False, indent=1)
    print(f"-> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
