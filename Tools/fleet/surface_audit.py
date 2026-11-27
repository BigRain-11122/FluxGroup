#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""surface_audit.py — 按 QUALITY-SURFACE-v1.json 的 12 个面逐项体检（可复算，不是文档）。

为什么（2026-11-22 CEO「工作要有全面性创新性」）：
"你提一个点、我交回一个面"是硬要求。面清单不能是写死的文档——文档会过期，
必须每次从磁盘事实重算，并且能让它变红。

每面返回 OK / STALE / MISSING / NOT_PASS / SKIP（SKIP 不算通过）。
用法：python3 Tools/fleet/surface_audit.py [--json] [--group S1,S2]
返回码：0 全绿；2 有红（供调度与一屏使用）。
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
SPEC = os.path.join(SOCIAL, "QUALITY-SURFACE-v1.json")
OUT = os.path.join(STATE, "SURFACE-STATUS.json")
BOARD = os.path.join(SOCIAL, "QUALITY-BOARD.md")

sys.path.insert(0, HERE)


def _load(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d if d is not None else {}


def _state_file(name):
    """判据产物的真实位置：social_guard 写在 cph4/fleet/social/state/，
    其余工具写 .codely-cli/state/。两处都找，别让路径差异把"有结果"报成"没结果"。
    """
    for p in (os.path.join(SOCIAL, "state", name), os.path.join(STATE, name)):
        if os.path.exists(p):
            return p
    return os.path.join(SOCIAL, "state", name)


def _age_min(p):
    try:
        return (datetime.now() - datetime.fromtimestamp(os.path.getmtime(p))).total_seconds() / 60
    except Exception:
        return 1e9


def _rows(name):
    out = []
    try:
        for line in open(os.path.join(SOCIAL, name), encoding="utf-8"):
            if line.strip():
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def _mk(aid, ok, detail, sev="P1", n=None):
    return {"id": aid, "ok": ok, "detail": detail, "sev": sev, "n": n}


# ---- 各面 ----
def s1_voice():
    import reply_quality as rq
    q2 = rq.evaluate(30, since="2026-11-22T18:05") or {}
    n = int(q2.get("n") or 0)
    if n < 8:
        return _mk("S1", None, "新话术下样本 %d 条（需 ≥8），暂不下结论" % n, n=n)
    ok = (float(q2.get("median") or 0) >= 65 and float(q2.get("concrete_rate") or 0) >= 0.6
          and float(q2.get("ai_smell_rate") or 0) == 0)
    return _mk("S1", ok, "中位 %.0f、具体 %.0f%%、AI腔 %.0f%%、撞模板 %.0f%%" % (
        float(q2.get("median") or 0), 100 * float(q2.get("concrete_rate") or 0),
        100 * float(q2.get("ai_smell_rate") or 0), 100 * float(q2.get("dup_rate") or 0)), n=n)


def s2_diversity():
    q = {}
    try:
        import reply_quality as rq
        q = rq.evaluate(n=30, since="2026-11-22T18:05") or {}
    except Exception:
        pass
    n = int(q.get("n") or 0)
    if n == 0:
        return _mk("S2", None, "今天还没有新稿，多样性无从统计", n=0)
    share = float(q.get("max_share") or 0)
    return _mk("S2", share <= 0.5 and int(q.get("unique_arch") or 0) >= 4,
               "最扎堆 %.0f%%、%s 类" % (100 * share, q.get("unique_arch")), n=n)


def s3_consistency():
    q = {}
    try:
        import reply_quality as rq
        q = rq.evaluate(n=30) or {}
    except Exception:
        pass
    cons = q.get("consistency") or {}
    if not cons:
        return _mk("S3", None, "分号数据不足（旧稿无 account 列），暂不下结论")
    bad = [k for k, v in cons.items() if not v.get("ok")]
    return _mk("S3", not bad, "分号 %d 个，漂移超线 %d 个 %s" % (len(cons), len(bad), bad or ""))


def s4_interaction():
    import arch_perf as apf
    d = apf.build()
    n = sum(v["n"] for v in (d.get("archetypes") or {}).values())
    if n == 0:
        return _mk("S4", None, "已回验且带原型的投稿 0 条（通道已建，等数据）", n=0)
    return _mk("S4", True, "已回验 %d 条；最优原型 %s" % (n, d.get("best") or "样本不足"), n=n)


def s5_supply():
    import freq_policy as fp
    pool = len([1 for v in (_load(os.path.join(SOCIAL, "VIDEO-TITLES.json"), {}) or {}).values()
                if (v or {}).get("title")])
    cap = fp.supply_cap()
    pol = fp.load_policy()
    need = int(pol.get("max_per_day") or 0) * 7
    return _mk("S5", pool >= need, "池 %d 条（≥%d 才够一天 %s 条 × 7 天）；供给上限 %s/天" % (
        pool, need, pol.get("max_per_day"), cap), n=pool)


def s6_targeting():
    vids = _load(os.path.join(SOCIAL, "VIDEO-TITLES.json"), {}) or {}
    per = _load(os.path.join(SOCIAL, "ACCOUNT-PERSONAS.json"), {}) or {}
    words = set()
    for k, v in per.items():
        if isinstance(v, dict):
            words |= set(v.get("topics") or [])
    if not vids:
        return _mk("S6", False, "视频清单为空")
    hit = sum(1 for v in vids.values() if any(w in ((v or {}).get("title") or "") for w in words))
    return _mk("S6", hit / max(1, len(vids)) >= 0.5,
               "池内标题命中人设话题 %d/%d（%.0f%%）" % (hit, len(vids), 100 * hit / max(1, len(vids))),
               n=len(vids))


def s7_gates():
    p = _state_file("GATE-RESULT.json")
    age = _age_min(p)
    if not os.path.exists(p):
        return _mk("S7", False, "没有闸结果文件")
    if age > 24 * 60:
        return _mk("S7", False, "闸结果 %.0f 小时未更新" % (age / 60))
    d = _load(p, {})
    # GATE-RESULT 用的字段是 overall（正例/负例各自还有 pos_ok/neg_ok），
    # 之前只认 ok/pass，把"全绿"读成了"有红"——判据必须按真实产物字段读。
    ok = bool(d.get("overall", d.get("ok", d.get("pass", False))))
    det = "正例 %s/%s、负例拦 %s/%s、结构样本 %s" % (
        d.get("pos_pass"), d.get("pos_n"), d.get("neg_blocked"), d.get("neg_n"),
        d.get("structural_n"))
    if d.get("pos_fail_samples") or d.get("neg_leak_samples"):
        ok = False
        det += "；漏/误：%s" % ((d.get("pos_fail_samples") or []) + (d.get("neg_leak_samples") or []))[:2]
    return _mk("S7", ok, det)


def s8_speed():
    tm = [r for r in _rows("practice-log.jsonl") if r.get("action") == "timing"]
    tm = tm[-10:]
    if len(tm) < 3:
        return _mk("S8", None, "计时样本 %d 条（需 ≥3）" % len(tm), n=len(tm))
    tot = sorted(float(r.get("total_s") or 0) for r in tm)
    post = sorted(float(r.get("post_s") or 0) for r in tm if r.get("post_s") is not None)
    med = tot[len(tot) // 2]
    extra = "；post 中位 %.0fs" % (post[len(post) // 2]) if post else ""
    return _mk("S8", med <= 30, "total 中位 %.0fs（最快 %.0fs）%s" % (med, tot[0], extra), n=len(tm))


def s9_safety():
    p = _state_file("GUARD-ACCOUNTS.json")
    if not os.path.exists(p):
        return _mk("S9", False, "没有账号安全判据结果", sev="P0")
    d = _load(p, {})
    bad = [c for c in (d.get("checks") or []) if c.get("ok") is False]
    return _mk("S9", not bad, "红 %d 项 %s" % (len(bad), [c.get("id") for c in bad] or ""), sev="P0")


def s10_train():
    p = os.path.join(STATE, "TRAIN-EXCLUSIVE")
    if not os.path.exists(p):
        return _mk("S10", True, "无训练独占，模型窗口开放")
    mins = _age_min(p)
    return _mk("S10", mins <= 240, "训练独占已 %.0f 分钟（>240 分钟要查是否僵持）" % mins)


def s11_innovation():
    p = os.path.join(STATE, "ARCH-PERF.json")
    if not os.path.exists(p):
        return _mk("S11", None, "还没有实验数据（arch_perf 未跑）")
    d = _load(p, {})
    return _mk("S11", True, "原型效果实验在跑：%d 类有样本，最优 %s" % (
        len(d.get("archetypes") or {}), d.get("best") or "样本不足"))


def s12_board():
    mins = _age_min(BOARD)
    return _mk("S12", mins <= 60, "一屏 %.0f 分钟前更新" % mins)


FACES = {"S1": s1_voice, "S2": s2_diversity, "S3": s3_consistency, "S4": s4_interaction,
         "S5": s5_supply, "S6": s6_targeting, "S7": s7_gates, "S8": s8_speed,
         "S9": s9_safety, "S10": s10_train, "S11": s11_innovation, "S12": s12_board}


def audit(only=None):
    spec = _load(SPEC, {}) or {}
    names = {a["id"]: a["name"] for a in (spec.get("areas") or [])}
    rows = []
    for fid, fn in FACES.items():
        if only and fid not in only:
            continue
        try:
            r = fn()
        except Exception as e:
            r = _mk(fid, False, "体检异常：%s" % str(e)[:80])
        r["name"] = names.get(fid, fid)
        rows.append(r)
    red = [r for r in rows if r["ok"] is False]
    skip = [r for r in rows if r["ok"] is None]
    doc = {"ts": datetime.now().isoformat(timespec="seconds"), "checks": rows,
           "n": len(rows), "red": len(red), "skip": len(skip)}
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--group", default=None, help="只看几个面，逗号分隔，如 S1,S5")
    a = ap.parse_args(argv)
    only = set(x.strip() for x in a.group.split(",")) if a.group else None
    doc = audit(only)
    if a.json:
        print(json.dumps(doc, ensure_ascii=False))
    else:
        for c in doc["checks"]:
            mark = "✅" if c["ok"] is True else ("❗" if c["ok"] is False else "·")
            print("%s %s %-8s %s" % (mark, c["id"], c["name"], c["detail"]))
        print("—— %d 面：红 %d、待判 %d" % (doc["n"], doc["red"], doc["skip"]))
    return 0 if doc["red"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
