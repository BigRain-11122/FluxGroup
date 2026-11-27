#!/usr/bin/env python3
# local_gate_llm.py -- 用本地模型替代正则，做【语义】禁开方向判定
#
# 动机：正则版假阳率 81%（"滚动"指滚动窗口、"DSR N/A"被当成做了检验）。
#       本地模型可以判断"是否在【声称/主张】该机制"，而非"是否出现该词"——零 token 成本。
# 用法: python Tools/local_gate_llm.py --selftest
#       python Tools/local_gate_llm.py --scan --days 30
import argparse, glob, json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "quant", "bigmoney", "research", "BANNED_DIRECTIONS.json")
OLLAMA = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:8b"


def ask(prompt, model=MODEL, timeout=180):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0, "num_ctx": 8192}}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "ignore")).get("response", "")


def load_dirs():
    d = json.load(open(REG, encoding="utf-8"))
    return [(x["id"], x["name"]) for x in d["directions"]]


def classify(text, dirs, model=MODEL, chunk=3000, overlap=400):
    """分块扫描全文（滑窗），合并各块判定。
    修正：v1 只读前 6000 字，漏掉了位于 6643 字的真实主张（EXIT_OVERLAY_P1）。
    截断 bug 提醒：任何"读前 N 字"的做法都会漏检，长文档必须滑窗。"""
    lst = "\n".join(f"{i}: {n}" for i, n in dirs)
    found = set()
    n = len(text)
    step = max(1, chunk - overlap)
    for start in range(0, max(1, n), step):
        seg = text[start:start + chunk]
        if len(seg) < 200:
            break
        prompt = (
            "你是量化研究审计员。下面是一份 A 股量化研究的预注册文档【片段】。\n"
            "已知以下研究方向【已被证伪】，禁止再作为新主张提出：\n"
            f"{lst}\n\n"
            "任务：判断该【片段】是否在【声称或主张使用】上述任一方向——而不是仅仅提到这些词、"
            "不是在列举禁止事项、也不是说某指标'不适用'、也不是说某旧件已收线。\n"
            "只输出命中的编号，用逗号分隔；一个都没有就输出 NONE。不要解释。\n\n"
            "----- 片段 -----\n"
            f"{seg}\n"
            "----- 结束 -----\n"
            "命中编号："
        )
        out = ask(prompt, model).strip()
        if "NONE" not in out.upper():
            found.update(re.findall(r"BAN-\d+", out))
        if n <= chunk:
            break
    return sorted(found)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    dirs = load_dirs()

    if a.selftest:
        # 真阳 / 假阳用例（真阳=确实主张；假阳=词出现但非主张）
        cases = [
            ("quant/bigmoney/research/EXIT_OVERLAY_P1.md", "BAN-04", "真阳：ETF 网格交易执行引擎"),
            ("quant/bigmoney/research/FACTOR_BLEND.md", "BAN-01", "真阳：横截面动量"),
            ("quant/bigmoney/research/AUDIT-20260923.md", None, "假阳：'滚动无 min_periods' 指滚动窗口"),
            ("quant/bigmoney/research/INNOVATION_QUOTA_W10_PREREG.md", None, "假阳：'DSR/PBO 不适用'"),
            ("quant/bigmoney/research/ACCOUNT_COST_TRADE_TAX.md", None, "假阳：'DSR N/A'"),
        ]
        ok = 0
        for rel, want, why in cases:
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                print(f"  SKIP  {rel}"); continue
            t = open(p, encoding="utf-8", errors="ignore").read()
            got = classify(t, dirs)
            if want is None:
                good = (len(got) == 0)
            else:
                good = (want in got)
            ok += 1 if good else 0
            print(f"  {'ok ' if good else 'FAIL'} got={','.join(got) or 'NONE':<14} want={want or 'NONE':<8} {why}")
        print(f"selftest {ok}/{len(cases)} 通过")
        return

    if a.scan:
        cutoff = time.time() - a.days * 86400
        d = os.path.join(ROOT, "quant", "bigmoney", "research")
        files = [f for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True)
                 if os.path.getmtime(f) > cutoff]
        if a.limit:
            files = files[:a.limit]
        hits = 0
        for i, f in enumerate(files, 1):
            t = open(f, encoding="utf-8", errors="ignore").read()
            got = classify(t, dirs)
            if got:
                hits += 1
                print(f"CLAIM  {os.path.basename(f)}  -> {','.join(got)}")
            if i % 25 == 0:
                print(f"  ...{i}/{len(files)}", flush=True)
        print(f"scanned={len(files)} claim_hits={hits}")


if __name__ == "__main__":
    main()
