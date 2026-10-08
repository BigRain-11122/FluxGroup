#!/usr/bin/env python3
# rename_resubmit_detector.py -- "改名重提"语义检测器（bge-m3 本地嵌入·零 token）
#
# 依据：该司律「已判负族禁改名重提」（STRATEGY_LIBRARY 判负线 + 各预注册 §1）。
#       关键词匹配抓不到改名（例："低量选股"→"缩量蓄势"，词不同语义同）。
#       本地 bge-m3 可做中文语义相似度，成本 0。
#
# 判据（跑前写死）：
#   相似度 >= 0.82 -> 高度疑似改名重提（须人工裁决）
#   0.70 ~ 0.82    -> 关注区
#   < 0.70         -> 视为新方向
# 用法: python Tools/rename_resubmit_detector.py [--days 30] [--thresh 0.82]
import argparse, glob, json, math, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH = os.path.join(ROOT, "quant", "bigmoney", "research")
EMB = "http://127.0.0.1:11434/api/embed"
MODEL = "bge-m3:latest"

# 已判负/已证伪的"方向种子"（来自 STRATEGY_LIBRARY 判负线 + D-41 禁开清单 + 本会话否证）
SEEDS = [
    ("NEG-动量", "ETF横截面动量 追涨强者 强势延续"),
    ("NEG-反转", "ETF横截面反转 买跌得最多的 超跌反转"),
    ("NEG-短线", "1到15天短线 日内反转 隔日动量"),
    ("NEG-网格", "网格交易 区间挂单 格距 隔格买卖"),
    ("NEG-水温", "大盘水温 市场广度 涨跌家数 择时前置"),
    ("NEG-均线确认", "站上MA20 MA60 均线确认后才买 前20日为正"),
    ("NEG-小市值", "小市值因子 低价股 微盘 低价格选股"),
    ("NEG-缓冲", "缓冲区 无交易带 降换手 缓冲带"),
    ("NEG-风格延续", "风格延续 风格轮动押注 追上年最强风格"),
    ("NEG-CTAWave", "商品期货CTA 时序动量 波动率目标"),
    ("NEG-WILD", "野路子涨停 打板 连板 情绪溢价"),
    ("NEG-CN五族", "CN原生 反转倾斜 红利低波轮动 市场中性 板块龙头"),
    ("NEG-LHB", "龙虎榜 席位 资金流 热度因子"),
    ("NEG-两融", "两融余额 融资融券 大宗交易 股东户数"),
    ("NEG-低PE", "低市盈率 低估值 价值因子 便宜股"),
    ("NEG-低量选股", "低量选股 成交额萎缩 缩量 地量选股"),
]


def embed(texts):
    body = json.dumps({"model": MODEL, "input": texts}).encode()
    req = urllib.request.Request(EMB, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8", "ignore")).get("embeddings", [])


def cos(a, b):
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return s / (na * nb) if na and nb else 0.0


def title_of(path, text):
    m = re.search(r"^#\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip()[:120]
    return os.path.basename(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--thresh", type=float, default=0.82)
    a = ap.parse_args()

    seed_vecs = embed([s[1] for s in SEEDS])
    if not seed_vecs:
        print("嵌入失败：请确认 ollama serve 在跑且已拉取 bge-m3"); return
    print(f"种子 {len(SEEDS)} 条已嵌入（{MODEL}）")

    cutoff = time.time() - a.days * 86400
    files = [f for f in glob.glob(os.path.join(RESEARCH, "**", "*.md"), recursive=True)
             if os.path.getmtime(f) > cutoff]
    print(f"窗口 {a.days} 天文件 {len(files)} 件｜阈值 {a.thresh}")

    items = []
    for f in files:
        try:
            t = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        head = t[:1500]
        items.append((f, title_of(f, t), head))
    if not items:
        print("无文件"); return

    B = 16
    flags = []
    for i in range(0, len(items), B):
        batch = items[i:i + B]
        vecs = embed([x[1] + "。" + x[2][:600] for x in batch])
        if len(vecs) != len(batch):
            continue
        for (f, title, _), v in zip(batch, vecs):
            best = max(((cos(v, sv), SEEDS[k][0], SEEDS[k][1]) for k, sv in enumerate(seed_vecs)),
                       key=lambda x: x[0])
            if best[0] >= a.thresh:
                flags.append((best[0], os.path.basename(f), title[:60], best[1]))
            elif best[0] >= 0.70:
                flags.append((best[0], os.path.basename(f), title[:60], best[1] + " [关注区]"))
        print(f"  ...{min(i+B, len(items))}/{len(items)}", flush=True)

    flags.sort(reverse=True)
    print(f"\n疑似改名重提/关注 = {len(flags)} 件")
    for s, name, title, seed in flags[:25]:
        print(f"  {s:.3f}  {name[:40]:<40} -> {seed:<14} | {title}")

    out = os.path.join(ROOT, "docs", "audits", "rename-resubmit-flags.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": MODEL,
                   "threshold": a.thresh, "seeds": [s[0] for s in SEEDS],
                   "flags": [{"sim": round(s, 4), "file": n, "title": t, "seed": sd}
                             for s, n, t, sd in flags]}, fh, ensure_ascii=False, indent=1)
    print(f"-> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
