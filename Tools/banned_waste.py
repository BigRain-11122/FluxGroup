# banned_waste.py —— 量化"命中禁开清单的预注册"所消耗的算力（本地跑·输出≤12行）
# 目的：给 CEO 一个数字——按 D-20260930-41 §1.2 禁开清单，历史上有多少试验白花在已证伪方向。
import json, os, re, glob

BM = r"C:\Users\sjs20\Desktop\FluxGroup\quant\bigmoney"
RES = os.path.join(BM, "results")
PREREG = os.path.join(BM, "research")

BANNED = {
    "横截面动量": r"横截面.*动量|cross.?section.*momentum",
    "横截面反转": r"横截面.*反转|cross.?section.*reversal",
    "网格": r"网格|grid\s*trad",
    "水温/广度择时": r"水温|广度|breadth",
    "站上MA20/均线确认": r"站上\s*MA|MA20\s*确认|均线确认",
    "小市值": r"小市值|small.?cap",
    "低价因子": r"低价因|低价格|low.?price",
    "缓冲降换手": r"缓冲|buffer",
    "1-15天短线": r"日内|短线|intraday|short.?term\s*reversal",
}

def main():
    # 1) 账本里逐批试验数
    ledger = os.path.join(RES, "gate_attrition.json")
    rows = []
    if os.path.exists(ledger):
        try:
            data = json.load(open(ledger, encoding="utf-8"))
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                for k in ("rows", "entries", "batches", "records"):
                    if k in data and isinstance(data[k], list):
                        rows = data[k]; break
                if not rows:
                    rows = [data]
        except Exception as e:
            print(f"[warn] ledger parse: {str(e)[:60]}")

    def pick(row, *names):
        for n in names:
            if n in row and row[n] is not None:
                return row[n]
        return None

    total_trials = 0
    hit_trials = 0
    hit_batches = 0
    hit_names = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = str(pick(r, "batch_name", "batch", "name", "id", "claim") or "")
        n = pick(r, "batch_trials", "trials", "n_trials", "n_eff", "cells")
        try:
            n = int(n) if n is not None else 0
        except Exception:
            n = 0
        total_trials += n
        for label, pat in BANNED.items():
            if re.search(pat, name, re.I):
                hit_trials += n
                hit_batches += 1
                hit_names[label] = hit_names.get(label, 0) + n
                break

    # 2) 预注册件里命中禁开清单的文件数（按文件名+首 200 行）
    files = glob.glob(os.path.join(PREREG, "**", "*.md"), recursive=True)
    file_hits = {k: 0 for k in BANNED}
    scanned = 0
    for f in files:
        try:
            head = open(f, encoding="utf-8", errors="ignore").read(3000)
        except Exception:
            continue
        scanned += 1
        for label, pat in BANNED.items():
            if re.search(pat, os.path.basename(f) + head, re.I):
                file_hits[label] += 1

    print(f"ledger_batches={len(rows)} ledger_trials={total_trials}")
    print(f"banned_batches={hit_batches} banned_trials={hit_trials} "
          f"share={(hit_trials/total_trials*100 if total_trials else 0):.1f}%")
    print(f"prereg_files_scanned={scanned}")
    top = sorted(file_hits.items(), key=lambda kv: -kv[1])[:6]
    print("prereg_files_by_banned_direction: " + ", ".join(f"{k}={v}" for k, v in top))

if __name__ == "__main__":
    main()
