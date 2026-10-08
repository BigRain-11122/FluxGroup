#!/usr/bin/env python3
# gate_fused.py -- 融合闸：正则（高召回） + 本地模型（高精确） 并联
#
# 架构依据（本会话实测）：
#   正则版     : 近 30 天 391 件报 15 命中，但上下文校准显示假阳 81%（"滚动窗口"/"DSR N/A"）
#   本地模型版 : 已知用例 5/5——3 个假阳全部正确排除，2 个真阳命中；但会过度触发、且易漏检（需滑窗）
#   ⇒ 并联：正则抓候选（宁可多），本地模型做语义裁决（去掉非主张），两者不一致的件标注供人工复核。
# 成本：本地推理零 token；外审只在最后读一行汇总。
#
# 用法: python Tools/gate_fused.py --selftest
#       python Tools/gate_fused.py --scan --days 30 [--limit N]
import argparse, glob, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import banned_direction_gate as rg
import local_gate_llm as llm

ROOT = rg.ROOT


def regex_hits(path):
    got, hits, _ = rg.verdict_for(path, rg.load_reg())
    return sorted({h["id"] for h in hits})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    dirs = llm.load_dirs()

    if a.selftest:
        cases = [
            ("quant/bigmoney/research/EXIT_OVERLAY_P1.md", True, "真阳：网格交易"),
            ("quant/bigmoney/research/FACTOR_BLEND.md", True, "真阳：横截面动量"),
            ("quant/bigmoney/research/AUDIT-20260923.md", False, "假阳：滚动窗口"),
            ("quant/bigmoney/research/INNOVATION_QUOTA_W10_PREREG.md", False, "假阳：DSR 不适用"),
        ]
        ok = 0
        for rel, is_true_positive, why in cases:
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                print(f"  SKIP  {rel}"); continue
            r = regex_hits(p)
            t = open(p, encoding="utf-8", errors="ignore").read()
            l = llm.classify(t, dirs)
            confirmed = [x for x in l if x in r] or l
            verdict = "CLAIM" if confirmed else "CLEAN"
            good = (verdict == "CLAIM") == is_true_positive
            ok += 1 if good else 0
            print(f"  {'ok ' if good else 'FAIL'} {verdict:<6} regex={','.join(r) or '-':<12} "
                  f"llm={','.join(l) or '-':<12} {why}")
        print(f"fused selftest {ok}/{len(cases)} 通过")
        return

    if a.scan:
        cutoff = time.time() - a.days * 86400
        d = os.path.join(ROOT, "quant", "bigmoney", "research")
        files = [f for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True)
                 if os.path.getmtime(f) > cutoff]
        if a.limit:
            files = files[:a.limit]
        both = only_re = only_llm = 0
        rows = []
        for i, f in enumerate(files, 1):
            r = set(regex_hits(f))
            if not r:
                continue                     # 正则没抓到 -> 按高召回前提，视为无候选
            t = open(f, encoding="utf-8", errors="ignore").read()
            l = set(llm.classify(t, dirs))
            inter = r & l
            if inter:
                both += 1
                rows.append(("BOTH", os.path.basename(f), sorted(inter)))
            elif l:
                only_llm += 1
                rows.append(("LLM", os.path.basename(f), sorted(l)))
            else:
                only_re += 1
                rows.append(("REGEX-ONLY(假阳)", os.path.basename(f), sorted(r)))
            if i % 20 == 0:
                print(f"  ...{i}/{len(files)}", flush=True)
        print(f"\n正则候选件={both+only_llm+only_re}｜双方确认={both}｜仅模型={only_llm}｜仅正则(判为假阳)={only_re}")
        for tag, name, ids in rows:
            print(f"  {tag:<18} {name[:44]:<44} {','.join(ids)}")


if __name__ == "__main__":
    main()
