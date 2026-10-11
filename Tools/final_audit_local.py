#!/usr/bin/env python3
# final_audit_local.py -- 一次性本地审计（零 token）：
#   ① 三分类禁开方向闸（主张 / 执行禁令 / 声明例外）——修正"二分类过高估计"
#   ② 改名重提检测（用 LLM 而非嵌入——嵌入法已否证）
#   ③ 输出真实违规清单，供重发派工单
# 用法: python Tools/final_audit_local.py [--days 30] [--limit N]
import argparse, glob, json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "quant", "bigmoney", "research", "BANNED_DIRECTIONS.json")
OLLAMA = "http://127.0.0.1:11434/api/generate"
EMB = "http://127.0.0.1:11434/api/embed"
MODEL = "qwen3:8b"
BIG = "qwen3:14b"


def gen(prompt, model=MODEL, timeout=240):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0, "num_ctx": 8192}}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore")).get("response", "")


def load_dirs():
    d = json.load(open(REG, encoding="utf-8"))
    return [(x["id"], x["name"]) for x in d["directions"]]


TRI_PROMPT = """你是量化研究审计员。下面是一份 A 股量化研究文档的【片段】。

已被证伪、禁止再作为新主张提出的方向：
{lst}

请判断该片段属于哪一类（只回答一个词）：
- CLAIM   = 本片段在【提出/主张/打算使用】上述某个方向（例如"本批采用网格交易策略"）
- BAN     = 本片段在【禁止/已否证/勿再投入】上述方向（例如"已否证九方向禁再开"）
- EXEMPT  = 本片段在【声明自己不属某方向】或说某指标【不适用】（例如"本批非网格交易"）
- OTHER   = 都不像

如果判定为 CLAIM，再另起一行输出命中编号（BAN-xx，多个用逗号），否则第二行输出 NONE。

----- 片段 -----
{seg}
----- 结束 -----
类别："""


def classify_tri(text, dirs, chunk=3000, overlap=400):
    lst = "\n".join(f"{i}: {n}" for i, n in dirs)
    claims, modes = set(), set()
    step = max(1, chunk - overlap)
    for start in range(0, max(1, len(text)), step):
        seg = text[start:start + chunk]
        if len(seg) < 200:
            break
        out = gen(TRI_PROMPT.format(lst=lst, seg=seg)).strip()
        head = out.splitlines()[0].strip().upper() if out else "OTHER"
        m = re.search(r"\b(CLAIM|BAN|EXEMPT|OTHER)\b", head)
        mode = m.group(1) if m else "OTHER"
        modes.add(mode)
        if mode == "CLAIM":
            claims.update(re.findall(r"BAN-\d+", out))
        if len(text) <= chunk:
            break
    return modes, sorted(claims)


RENAME_PROMPT = """你是量化研究审计员。下面列出【已判负/已证伪】的研究方向，然后是某文档的标题与摘要。

已判负方向：
{seeds}

任务：该文档是否在【用不同说法重新提出】上述某个已判负方向（改名重提）？
只回答一行：YES <编号> 或 NO。不要解释。

文档：
{body}
"""


def rename_check(title, body, seeds, model=BIG):
    s = "\n".join(f"{k}: {v}" for k, v in seeds)
    out = gen(RENAME_PROMPT.format(seeds=s, body=f"{title}\n{body[:1200]}"), model).strip().upper()
    m = re.search(r"YES\s*(\S+)", out)
    return (m.group(1) if m else None), out[:40]


SEEDS = [
    ("NEG-动量", "追涨强者、买近期涨幅最大的、横截面动量"),
    ("NEG-反转", "买跌得最多的、超跌反转、横截面反转"),
    ("NEG-短线", "1-15天短线、隔日、日内反转"),
    ("NEG-网格", "网格交易、区间挂单、格距买卖"),
    ("NEG-水温", "大盘水温、市场广度择时、涨跌家数前置"),
    ("NEG-均线确认", "站上均线才买、前20日为正、确认型前置"),
    ("NEG-小市值", "小市值、微盘、低价股选股"),
    ("NEG-缓冲", "缓冲区、无交易带、降换手"),
    ("NEG-风格延续", "风格延续、追上年最强风格"),
    ("NEG-低PE", "低市盈率、低估值、价值因子"),
    ("NEG-低量", "低量选股、缩量、地量"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    dirs = load_dirs()

    cutoff = time.time() - a.days * 86400
    d = os.path.join(ROOT, "quant", "bigmoney", "research")
    files = [f for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True)
             if os.path.getmtime(f) > cutoff]
    if a.limit:
        files = files[:a.limit]
    print(f"文件 {len(files)} 件｜模型 {MODEL} / 改名用 {BIG}", flush=True)

    claims_rows, rename_rows = [], []
    stats = {"CLAIM": 0, "BAN": 0, "EXEMPT": 0, "OTHER": 0}

    for i, f in enumerate(files, 1):
        try:
            t = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        modes, claims = classify_tri(t, dirs)
        for m in modes:
            stats[m] = stats.get(m, 0) + 1
        if claims and "CLAIM" in modes:
            claims_rows.append({"file": os.path.relpath(f, ROOT).replace("\\", "/"),
                                "bans": claims, "modes": sorted(modes)})
        # 改名重提：只对含绩效表述或预注册件做，省算力
        base = os.path.basename(f)
        if ("PREREG" in base.upper()) or re.search(r"(年化|CAGR|Sharpe)", t):
            title = (re.search(r"^#\s*(.+)$", t, re.M).group(1)[:110]
                     if re.search(r"^#\s*(.+)$", t, re.M) else base)
            hit, raw = rename_check(title, t[:1500], SEEDS)
            if hit and hit != "NO":
                rename_rows.append({"file": os.path.relpath(f, ROOT).replace("\\", "/"),
                                    "title": title, "seed": hit})
        if i % 10 == 0:
            print(f"  ...{i}/{len(files)}  claim={len(claims_rows)} rename={len(rename_rows)}", flush=True)

    print(f"\n模式统计: {stats}")
    print(f"真主张(CLAIM)件数 = {len(claims_rows)}")
    for r in claims_rows[:20]:
        print(f"  CLAIM  {os.path.basename(r['file'])[:44]:<44} {','.join(r['bans'])}")
    print(f"\n疑似改名重提 = {len(rename_rows)}")
    for r in rename_rows[:20]:
        print(f"  RENAME {os.path.basename(r['file'])[:40]:<40} -> {r['seed']}")

    out = os.path.join(ROOT, "docs", "audits", "final-audit-local.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": MODEL,
                   "big_model": BIG, "files": len(files), "mode_stats": stats,
                   "claims": claims_rows, "renames": rename_rows}, fh, ensure_ascii=False, indent=1)
    print(f"-> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
