#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_loop.py - 自评分→自动修→再评分的闭环（CEO 2026-11-11「你自己循环跑」）。

它不发明分数：分数完全来自 quality_score.py（六维可复算），本工具只做两件事：
  1) 把"能靠脚本自己修的"扣分项修掉（修法登记在 FIXERS 里，没登记的一律不假装会修）
  2) 把每轮的分数与残余阻塞写进 cph4/fleet/state/quality-history.jsonl（趋势可查）

修法只收确定性、可逆、不对外、不花钱的动作：重生成文档、刷新本机探针、补指针。
外部阻塞（服务暂停/机器离线/未装机）单列，不许算成"已修"。

用法：
  python3 Tools/fleet/self_loop.py                 # 默认最多 3 轮
  python3 Tools/fleet/self_loop.py --rounds 5 --json
  python3 Tools/fleet/self_loop.py --self-test
Exit: 0 无自动可修项；1 修完仍有自动项（说明修法失效）
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
TOOLS = os.path.join(ROOT, "Tools", "fleet")
HIST = os.path.join(FLEET, "state", "quality-history.jsonl")

sys.path.insert(0, TOOLS)


def _sh(script, *args, timeout=180):
    try:
        p = subprocess.run([sys.executable, os.path.join(TOOLS, script)] + [a for a in args if a],
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 124, str(e)[:120]


def fix_doc_drift():
    """配置与文档漂移 → 重新生成 FLEET-SPEC（生成物，安全可重跑）。"""
    rc, out = _sh("fleet_doc.py", "--check")
    if "漂移 0 处" in out:
        return False, "文档无漂移"
    rc2, out2 = _sh("fleet_doc.py", "--write")
    return (rc2 == 0), (out2.strip().splitlines() or ["已重生成"])[-1]


def fix_env_stale():
    """本机探针过期/缺失 → 重采一次（只采本机，不伪造别机）。"""
    p = os.path.join(FLEET, "env", "control.json")
    age_h = None
    try:
        with open(p, encoding="utf-8") as f:
            ts = json.load(f).get("ts")
        age_h = (time.time() - time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S"))) / 3600.0
    except Exception:
        age_h = None
    if age_h is not None and age_h < 24:
        return False, "本机探针 %.1fh 新鲜" % age_h
    rc, out = _sh("env_probe.py", "--write")
    return (rc in (0, 2)), (out.strip().splitlines() or ["已重采"])[-1]


FIXERS = [
    ("文档漂移", fix_doc_drift),
    ("本机探针陈旧", fix_env_stale),
]


def run_round(rounds=3, verbose=True):
    import quality_score as qs
    hist = []
    rep = qs.compute()
    hist.append(rep)
    for i in range(1, rounds + 1):
        acts = []
        for name, fn in FIXERS:
            try:
                changed, note = fn()
            except Exception as e:
                changed, note = False, "修法异常：%s" % str(e)[:80]
            acts.append({"fixer": name, "changed": bool(changed), "note": note})
        rep2 = qs.compute()
        grew = rep2["total"] > rep["total"] + 0.001
        if verbose:
            print("轮 %d：%s → %s%s" % (i, rep["total"], rep2["total"], "（有提升）" if grew else ""))
            for a in acts:
                if a["changed"]:
                    print("   修了 %s：%s" % (a["fixer"], a["note"]))
        rep2["round"] = i
        rep2["fixers"] = acts
        hist.append(rep2)
        rep = rep2
        if not grew and not any(a["changed"] for a in acts):
            break
    return hist


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    hist = run_round(a.rounds, verbose=not a.json)
    last = hist[-1]
    try:
        os.makedirs(os.path.dirname(HIST), exist_ok=True)
        with open(HIST, "a", encoding="utf-8") as f:
            for h in hist:
                f.write(json.dumps({"ts": h["ts"], "round": h.get("round", 0),
                                    "total": h["total"],
                                    "deductions": len(h.get("deductions") or [])},
                                   ensure_ascii=False) + "\n")
    except Exception:
        pass

    if a.json:
        print(json.dumps(last, ensure_ascii=False, indent=1))
    else:
        print("\n最终 %s / 100（%d 轮，记录已追加 %s）"
              % (last["total"], len(hist) - 1, os.path.relpath(HIST, ROOT)))
        auto = last.get("auto_fixable") or []
        ext = last.get("external_blocked") or []
        print("我该自己修的：%s" % ("无（全部已修）" if not auto else "%d 项" % len(auto)))
        for x in auto:
            print("   - %s" % (x if isinstance(x, str) else x.get("item")))
        print("外部阻塞（要 CEO 令/机器在线/装机，不许算已修）：%d 项" % len(ext))
        for x in ext:
            item = x if isinstance(x, str) else x.get("item")
            why = "" if isinstance(x, str) else ("  ← %s" % x.get("why"))
            print("   - %s%s" % (item, why))
    return 1 if (last.get("auto_fixable") or []) else 0


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    chk("修法登记非空且都可调用", FIXERS and all(callable(f) for _, f in FIXERS))
    changed, note = fix_doc_drift()
    chk("文档修法能返回 (bool, str)", isinstance(changed, bool) and isinstance(note, str), (changed, note))
    changed2, note2 = fix_env_stale()
    chk("探针修法能返回 (bool, str)", isinstance(changed2, bool) and isinstance(note2, str), (changed2, note2))
    import quality_score as qs
    rep = qs.compute()
    chk("评分能跑且含 auto/external 两类", "auto_fixable" in rep and "external_blocked" in rep, list(rep))
    print("[self_loop] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


if __name__ == "__main__":
    sys.exit(main())
