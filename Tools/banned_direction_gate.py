#!/usr/bin/env python3
# banned_direction_gate.py -- fail-closed hard gate against falsified research directions
# Authority: D-20260930-41 section 1.2 ; registry: quant/bigmoney/research/BANNED_DIRECTIONS.json
#
# Why Python and not PowerShell: PS -match does NOT decode \uXXXX escapes inside the
# pattern, so the earlier PS gate silently matched nothing for CJK patterns (EXIT_OVERLAY_P1
# with "ETF grid trading engine" passed as ADMIT). Python decodes natively.
#
# Usage:
#   python Tools/banned_direction_gate.py --prereg <path>
#   python Tools/banned_direction_gate.py --scan [--days 7]
#   python Tools/banned_direction_gate.py --selftest
# Exit 0 = ADMIT, 1 = REJECT, 2 = error.
import argparse, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "quant", "bigmoney", "research", "BANNED_DIRECTIONS.json")

# Trade-semantic patterns (v1.2). Bare technical vocabulary is deliberately NOT matched:
# the firm uses "grid" for a PARAMETER grid and "intraday" inside a FEATURE name.
TIGHT = {
    "BAN-01": r"(横截面.{0,8}动量|cross.?section.{0,10}momentum)",
    "BAN-02": r"(横截面.{0,8}反转|cross.?section.{0,10}reversal)",
    "BAN-03": r"(1.?15\s*交易日|持有\s*1.?15\s*天|日内交易|intraday\s*(trad|strateg|signal|revers))",
    "BAN-04": r"(网格交易|网格策略|网格挂单|网格法|网格盈利|网格叠代|grid\s*trad|grid\s*strateg)",
    "BAN-05": r"(水温.{0,10}(前置|闸|择时|filter)|(市场|大盘).{0,6}广度.{0,10}(择时|闸|前置)|breadth\s*(tim|filter|gate))",
    "BAN-06": r"(站上\s*MA\d+.{0,12}(确认|过滤|前置|才买)|MA20\s*确认|前\s*20\s*日为正|均线确认)",
    "BAN-07": r"(小市值.{0,10}(因子|策略|倾斜|选股)|small.?cap.{0,10}(factor|strateg|tilt)|低价因子|低价股策略)",
    "BAN-08": r"(缓冲区|无交易带|no.?trade.?band|buffer\s*zone.{0,12}(降|减)换手)",
    "BAN-09": r"(风格延续|追(上年|去年).{0,6}(最强|领涨)|style\s*persist|风格轮动押注)",
}
# Negation guard: "do not / already falsified / forbidden" in the preceding window means
# the text is DECLARING the direction avoided, not claiming it.
NEG = re.compile(r"(不做|禁止|已否证|已判负|不采用|never|do not|forbidden)")
EXC = r"{id}[\s\S]{{0,400}}?(new_data|new_mechanism|new data|new mechanism|新数据|新机制)"


def load_reg():
    with open(REG, encoding="utf-8") as f:
        return json.load(f)


def check_text(text, reg):
    hits = []
    for d in reg["directions"]:
        pat = TIGHT.get(d["id"], "|".join(d.get("patterns", [])))
        m = re.search(pat, text, re.I)
        if not m:
            continue
        prefix = text[max(0, m.start() - 12):m.start()]
        if NEG.search(prefix):
            continue
        has_exc = re.search(EXC.format(id=re.escape(d["id"])), text, re.I) is not None
        hits.append({"id": d["id"], "name": d["name"], "exception_stated": has_exc})
    return hits


def verdict_for(path, reg):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        return "ERROR", [], str(e)[:80]
    hits = check_text(text, reg)
    blocking = [h for h in hits if not h["exception_stated"]]
    return ("REJECT" if blocking else "ADMIT"), hits, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    reg = load_reg()

    if a.selftest:
        cases = [
            ("quant/bigmoney/research/EXIT_OVERLAY_P1.md", "REJECT", "real grid-trading engine claim"),
            ("quant/bigmoney/research/FACTOR_BLEND.md", "REJECT", "real cross-sectional momentum claim"),
            ("quant/bigmoney/research/STRATEGY_SYSTEM_V3.md", "REJECT", "strategy table lists cross-sectional momentum as candidate E5"),
        ]
        ok = True
        for rel, want, why in cases:
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                print(f"  SKIP  {rel} (missing)"); continue
            got, hits, err = verdict_for(p, reg)
            mark = "ok " if got == want else "FAIL"
            if got != want:
                ok = False
            ids = ",".join(h["id"] for h in hits) or "-"
            print(f"  {mark} {got:<7} want={want:<7} {os.path.basename(rel):<32} hits={ids:<14} ({why})")
        print("selftest PASS" if ok else "selftest FAIL")
        return 0 if ok else 1

    if a.scan:
        import time
        cutoff = time.time() - a.days * 86400
        d = os.path.join(ROOT, "quant", "bigmoney", "research")
        files = [f for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True)
                 if os.path.getmtime(f) > cutoff]
        rej = adm = 0
        for f in files:
            got, hits, _ = verdict_for(f, reg)
            if got == "REJECT":
                rej += 1
                print(f"REJECT  {os.path.basename(f)}  -> " + ",".join(h["id"] for h in hits))
            else:
                adm += 1
        print(f"scanned={len(files)} admit={adm} reject={rej}")
        return 1 if rej else 0

    if a.prereg:
        p = a.prereg if os.path.isabs(a.prereg) else os.path.join(ROOT, a.prereg)
        got, hits, err = verdict_for(p, reg)
        if err:
            print("ERROR " + err); return 2
        ids = ",".join(h["id"] for h in hits) or "-"
        print(f"{got}  {os.path.basename(p)}  -> {ids}")
        return 1 if got == "REJECT" else 0

    print(__doc__ or "usage: --prereg | --scan | --selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
