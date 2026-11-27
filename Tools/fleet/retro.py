#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""retro.py - 复盘席：把失败与返工变成经验，并且要求每条经验都有可核验落点。

CEO 2026-11-07：「也要复盘总结并推广经验的智能体」。

问题：机队每天都在踩坑，坑修完就忘；写进报告的教训没人读、也没人核验，
于是同一个坑换个形态复发（实测：假绿五型各自复发过、按 id 去重改了两次才真改）。

本席只做三件事：
  1. **抽取**：从队列失败卡（error_class）与撤销原因（cancel_reason 前缀）里找
     「同一类反复出现」的簇（>= min_occurrences），生成经验候选。
  2. **并要求落点**：每条经验必须挂 rg / symbol / doc / card 之一。
     **没有落点的不算已推广**，只能进「待落点」，一屏上一直挂着。
  3. **核验**：声称有落点但核验不到 = 假绿（rc=2），比没有落点更严重。

去重：按 (class, 症状前 24 字) 归一后比对台账，旧条保留、新条只并证据。

用法：
  python3 Tools/fleet/retro.py            # 只读：出候选与核验结果
  python3 Tools/fleet/retro.py --apply    # 落 RETRO.md / state/retro.json 并追加台账
  python3 Tools/fleet/retro.py --verify   # 只核验落点（脉里用这个，快）
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
SPEC = os.path.join(F, "RETRO-SPEC-v1.json")
SEED = os.path.join(F, "LESSONS-SEED-v1.json")
LEDGER = os.path.join(F, "LESSONS-LEDGER.jsonl")
BOARD = os.path.join(F, "RETRO.md")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def jl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8-sig"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def spec():
    return jload(SPEC, {})


# ---------------------------------------------------------------- 落点核验
def landing_ok(landing):
    """落点是不是真的存在。返回 (ok, 说明)。"""
    if not landing or not landing.get("kind"):
        return False, "没有落点"
    kind = landing.get("kind")
    ref = str(landing.get("ref") or "")
    if not ref:
        return False, "落点为空"
    if kind == "rg":
        p = os.path.join(ROOT, "Tools", "fleet", "regression.py")
        if not os.path.exists(p):
            return False, "regression.py 不存在"
        src = open(p, encoding="utf-8").read()
        if ('@case("%s"' % ref) in src:
            return True, "断言在册"
        return False, "断言 %s 不在 regression.py" % ref
    if kind == "symbol":
        if ":" not in ref:
            return False, "symbol 落点要写成 <path>:<symbol>"
        path, sym = ref.rsplit(":", 1)
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            return False, "%s 不存在" % path
        src = open(p, encoding="utf-8", errors="replace").read()
        if ("def %s(" % sym) in src or ("def %s(" % sym.split()[0]) in src or sym in src:
            return True, "判据在码里"
        return False, "%s 里找不到 %s" % (path, sym)
    if kind in ("doc", "card"):
        p = os.path.join(ROOT, ref)
        if os.path.exists(p):
            return True, "正身件在盘"
        return False, "%s 不存在" % ref
    return False, "未知落点类型 %s" % kind


# ---------------------------------------------------------------- 抽取
def _prefix(reason):
    r = str(reason or "").strip()
    m = re.match(r"^([a-zA-Z][\w-]{2,20}):", r)
    if m:
        return m.group(1)
    m = re.match(r"^([\u4e00-\u9fa5]{2,8})[：:，,]", r)
    return m.group(1) if m else ""


def derive():
    """从队列里找「同一类反复出现」的失败/撤销，生成经验候选（没有落点）。"""
    sp = spec()
    min_n = int(((sp.get("sources") or {}).get("queue_failures") or {})
                .get("min_occurrences") or 2)
    rows = jl(QUEUE)
    fails = [r for r in rows if r.get("state") in ("FAILED", "CARD-DEFECT")]
    by_class = defaultdict(list)
    for r in fails:
        by_class[str(r.get("error_class") or "E-UNCLASSIFIED")].append(r)
    cancels = [r for r in rows if r.get("state") == "CANCELLED"]
    by_prefix = defaultdict(list)
    for r in cancels:
        p = _prefix(r.get("cancel_reason"))
        if p:
            by_prefix[p].append(r)

    out = []
    for cls, rs in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
        if len(rs) < min_n:
            continue
        if cls == "E-UNCLASSIFIED":
            # 没有 error_class 的失败聚成一堆，不是"同一类失败重复 N 次"，
            # 而是"失败根本没归类"——这两种结论的修法完全不同，不许混为一谈。
            out.append({
                "id": "L-D-noclass",
                "class": "data",
                "symptom": "有 %d 张失败卡没有 error_class，复盘无从下手" % len(rs),
                "root": "失败落卡时不写归类，事后只能靠人逐张看",
                "fix": "失败卡必须带 error_class（落卡侧强制字段）",
                "landing": {},
                "evidence": [str(r.get("id")) for r in rs[:3]],
                "derived": True,
            })
            continue
        lines = Counter(str(r.get("line") or "-") for r in rs).most_common(3)
        out.append({
            "id": "L-D-%s" % cls.replace("E-", "").lower(),
            "class": "dispatch",
            "symptom": "%s 类失败已重复 %d 次（涉及 %s）" % (
                cls, len(rs), "、".join("%s×%d" % (a, b) for a, b in lines)),
            "root": "重复出现说明不是偶发环境问题，是这类卡/这条链的结构缺陷",
            "fix": "给这类失败定一个专属判据或拦在派单前",
            "landing": {},
            "evidence": [str(r.get("id")) for r in rs[:3]],
            "derived": True,
        })
    for p, rs in sorted(by_prefix.items(), key=lambda kv: -len(kv[1])):
        if len(rs) < min_n:
            continue
        out.append({
            "id": "L-C-%s" % re.sub(r"\W+", "", p.lower())[:12],
            "class": "supply",
            "symptom": "撤销原因「%s」重复 %d 次" % (p, len(rs)),
            "root": "同一类卡被反复铺出来又反复撤销 = 铺卡侧缺前置校验",
            "fix": "把这条撤销原因变成铺卡前的一次检查",
            "landing": {},
            "evidence": [str(r.get("id")) for r in rs[:3]],
            "derived": True,
        })
    return out


def stem(lesson):
    s = re.sub(r"\s+", "", str(lesson.get("symptom") or ""))[:24]
    return (str(lesson.get("class") or ""), s)


def collect():
    """种子 + 台账 + 派生候选，按 (class, 症状词干) 去重；种子的落点优先。"""
    seed = (jload(SEED, {}) or {}).get("lessons") or []
    led = jl(LEDGER)
    # 已被某条经验覆盖的撤销原因：派生候选不该再报一遍
    # （例：「零新增信息」这类撤销是 L-20261107-09 按交付物去重的直接后果）
    covered = []
    for it in (seed + led):
        for m in (it.get("also_matches") or []):
            covered.append((str(m), it.get("id")))
    seen, out = {}, []
    for src, items in (("seed", seed), ("ledger", led), ("derived", derive())):
        for it in items:
            it = dict(it)
            it.setdefault("source", src)
            if src in ("derived", "ledger"):
                hit = next((cid for m, cid in covered if m in str(it.get("symptom"))), None)
                if hit:
                    # 已被某条更完整的经验覆盖（例：「零新增信息」是去重落地后的自然结果），
                    # 不再单列成一条待落点，否则同一件事在盘上永远挂在"没推广"。
                    it["covered_by"] = hit
                    continue
            k = stem(it)
            if k in seen:
                old = seen[k]
                # 同类经验只留一条：有落点的胜过没落点的，种子胜过派生
                if len(old.get("landing") or {}) == 0 and it.get("landing"):
                    idx = out.index(old)
                    it["evidence"] = sorted(set((old.get("evidence") or []) +
                                                (it.get("evidence") or [])))[:6]
                    out[idx] = it
                    seen[k] = it
                else:
                    old["evidence"] = sorted(set((old.get("evidence") or []) +
                                                 (it.get("evidence") or [])))[:6]
                continue
            seen[k] = it
            out.append(it)
    for it in out:
        ok, why = landing_ok(it.get("landing"))
        it["landing_ok"] = ok
        it["landing_why"] = why
    return out


# ---------------------------------------------------------------- 输出
def board(items):
    landed = [i for i in items if i["landing_ok"]]
    pending = [i for i in items if not i["landing_ok"] and not (i.get("landing") or {}).get("kind")]
    broken = [i for i in items if not i["landing_ok"] and (i.get("landing") or {}).get("kind")]
    L = ["# 复盘（经验与落点）%s" % now(), "",
         "判据：**没有落点的不算已推广**。落点四类＝断言(rg) / 码里判据(symbol) / 正身件(doc) / 卡模板(card)。",
         "已落点 %d 条 · 待落点 %d 条 · 声称有落点但核验不到 %d 条（这一栏最严重）" % (
             len(landed), len(pending), len(broken)), ""]
    if broken:
        L += ["## 假绿：声称有落点但核验不到", "",
              "| 经验 | 落点 | 问题 |", "|---|---|---|"]
        for i in broken:
            L.append("| %s %s | %s | %s |" % (
                i["id"], i["symptom"][:34], (i.get("landing") or {}).get("ref"),
                i["landing_why"]))
        L.append("")
    if pending:
        L += ["## 待落点：复盘了但还没推广", "",
              "| 经验 | 症状 | 建议落点 |", "|---|---|---|"]
        for i in pending:
            L.append("| %s | %s | %s |" % (i["id"], i["symptom"][:44],
                                           i.get("fix", "")[:40]))
        L.append("")
    if landed:
        L += ["## 已落点：下次会被机器拦住", "",
              "| 经验 | 症状 | 落点 |", "|---|---|---|"]
        for i in landed:
            L.append("| %s | %s | %s `%s` |" % (
                i["id"], i["symptom"][:40], (i["landing"] or {}).get("kind"),
                (i["landing"] or {}).get("ref")))
        L.append("")
    L += ["---", "_复盘只提候选与核验；改阈值、写记忆都归各自的席，不在这里自动做_"]
    return "\n".join(L) + "\n", landed, pending, broken


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)

    items = collect()
    txt, landed, pending, broken = board(items)

    if broken:
        rc = int((spec().get("rc") or {}).get("claimed_but_missing", 2))
    elif pending:
        rc = int((spec().get("rc") or {}).get("has_pending_landing", 1))
    else:
        rc = 0

    if a.verify:
        print("[retro] 已落点 %d · 待落点 %d · 核验不到 %d -> rc=%d" % (
            len(landed), len(pending), len(broken), rc))
        for i in broken:
            print("  !! %s %s: %s" % (i["id"], (i.get("landing") or {}).get("ref"),
                                      i["landing_why"]))
        return rc

    print(txt)
    if not a.apply:
        print("[retro] 干跑；加 --apply 才落 RETRO.md 与台账")
        return rc

    os.makedirs(STATE, exist_ok=True)
    open(BOARD, "w", encoding="utf-8").write(txt)
    with open(os.path.join(STATE, "retro.json"), "w", encoding="utf-8") as f:
        json.dump({"ts": now(), "total": len(items), "landed": len(landed),
                   "pending": len(pending), "broken": len(broken),
                   "items": items, "rc": rc}, f, ensure_ascii=False, indent=1)

    # 台账只追加新经验（已有 id 或同词干的不再写）
    have_ids = {r.get("id") for r in jl(LEDGER)}
    have_stems = {stem(r) for r in jl(LEDGER)}
    new = [i for i in items
           if i["id"] not in have_ids and stem(i) not in have_stems]
    if new:
        with open(LEDGER, "a", encoding="utf-8") as f:
            for i in new:
                row = dict(i)
                row["ts"] = now()
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # 台账里已被覆盖的行清出去（保留一条真相，不保留三个说法）
    try:
        cov = set()
        for it in (jload(SEED, {}) or {}).get("lessons") or []:
            for m in (it.get("also_matches") or []):
                cov.add((str(m), it.get("id")))
        kept, dropped = [], 0
        for r in jl(LEDGER):
            if any(m in str(r.get("symptom")) and r.get("id") != cid for m, cid in cov):
                dropped += 1
                continue
            kept.append(r)
        if dropped:
            with open(LEDGER, "w", encoding="utf-8") as f:
                for r in kept:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception as e:
        print("[retro] W-LEDGER-PRUNE %s" % str(e)[:60])
    print("[retro] board -> %s · 台账新增 %d 条 · rc=%d" % (BOARD, len(new), rc))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))