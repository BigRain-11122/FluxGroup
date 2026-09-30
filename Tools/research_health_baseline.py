#!/usr/bin/env python3
# research_health_baseline.py -- 研究轨道健康度基线快照（D-41 §4 验收判据）
# 生成八项指标，供 2026-10-30 首验对照。判据全部机器可算，输出 JSON + 一行摘要。
# 用法: python Tools/research_health_baseline.py [--days 30]
import argparse, glob, json, os, re, sys, time, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BM = os.path.join(ROOT, "quant", "bigmoney")
RESEARCH = os.path.join(BM, "research")
OUT = os.path.join(ROOT, "docs", "audits", "research-health-baseline.json")

CITE = re.compile(r"(申万|东方证券|私募排排|S&P|AQR|Harvey|Lopez|Fama|引用机构|机构结论)")
PERF = re.compile(r"(年化|CAGR|Sharpe|回撤)")
XS = re.compile(r"(跨起点|滚动|全起点|rolling|cross.?start|全分布)")
DSR = re.compile(r"(DSR|PBO|deflated|CSCV|多重检验|deflation)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    cutoff = time.time() - a.days * 86400

    files = [f for f in glob.glob(os.path.join(RESEARCH, "**", "*.md"), recursive=True)
             if os.path.getmtime(f) > cutoff]

    m = {"window_days": a.days, "files": len(files)}
    perf = xs = dsr = cite = 0
    for f in files:
        try:
            t = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        has_perf = bool(PERF.search(t))
        if has_perf:
            perf += 1
            if XS.search(t):
                xs += 1
            if DSR.search(t):
                dsr += 1
        if CITE.search(t):
            cite += 1
    m["perf_claims"] = perf
    m["with_cross_start"] = xs
    m["with_search_discount"] = dsr
    m["with_institution_citation"] = cite
    m["pct_cross_start"] = round(xs / perf * 100, 1) if perf else 0.0
    m["pct_search_discount"] = round(dsr / perf * 100, 1) if perf else 0.0
    m["pct_citation"] = round(cite / len(files) * 100, 1) if files else 0.0

    # 禁开方向闸
    gate = os.path.join(ROOT, "Tools", "banned_direction_gate.py")
    try:
        p = subprocess.run([sys.executable, gate, "--scan", "--days", str(a.days)],
                           capture_output=True, text=True, timeout=600)
        last = [l for l in p.stdout.strip().splitlines() if l.startswith("scanned=")]
        m["banned_gate"] = last[-1] if last else "n/a"
    except Exception as e:
        m["banned_gate"] = "error:" + str(e)[:40]

    # 账本口径
    try:
        d = json.load(open(os.path.join(BM, "results", "gate_attrition.json"), encoding="utf-8"))
        e = d.get("entries") or []
        m["ledger_entries"] = len(e)
        m["ledger_increment_cells"] = sum(int(x.get("cells_ledger_delta") or 0) for x in e)
        m["ledger_cumulative_cells"] = max((int(x.get("ledger_total_after") or 0) for x in e), default=0)
    except Exception as e:
        m["ledger_error"] = str(e)[:50]

    # 数据缺口
    gaps = {"PE/PB": "derivable", "point_in_time_NP": "MISSING", "delist_quotes": "MISSING",
            "daily_ST": "MISSING", "index_membership": "MISSING", "pre2016_ETF": "MISSING",
            "real_fills": "paper_only"}
    m["data_gaps_missing"] = sum(1 for v in gaps.values() if v == "MISSING")
    m["data_gaps_total"] = len(gaps)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)

    print(f"[health baseline {time.strftime('%Y-%m-%d %H:%M')} window={a.days}d]")
    print(f"files={m['files']} perf_claims={perf} cross_start={xs}({m['pct_cross_start']}%) "
          f"search_discount={dsr}({m['pct_search_discount']}%) cite={m['pct_citation']}%")
    print(f"banned_gate: {m.get('banned_gate')}")
    print(f"ledger: entries={m.get('ledger_entries')} incr={m.get('ledger_increment_cells')} "
          f"cum={m.get('ledger_cumulative_cells')}")
    print(f"data_gaps_missing={m['data_gaps_missing']}/{m['data_gaps_total']}")
    print(f"-> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
