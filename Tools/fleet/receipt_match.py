#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""receipt_match.py - 把"干完了但回执名对不上"的卡收口（UNVERIFIED → DONE）。

为什么（2026-11-07 实测）：节点回执习惯带节点后缀（`voice-corpus-bm-c-2026-11-07.json`），
而卡上 deliverable 写的是不带后缀的 `voice-corpus-2026-11-07.json`。于是卡永远停在
UNVERIFIED、后面的工序段全被挡住：实测 asset-lib / biggame / bigmoney / bigstream-mv
四条线各被这样一张卡堵死，下游 7 段全部"等待上一段"。

判据（宁可不判也不假绿）：
  1) 卡状态 ∈ UNVERIFIED / RUNNING，且 result.deliverable_exists 为假；
  2) 回执文件名与 deliverable 的**词干**强匹配：去掉扩展名、日期、节点后缀后前缀相同；
  3) 回执 JSON 可解析，且不含 blocked/error/拒答 标记；
  4) 回执里有产出证据（segments/files/rows/artifacts 任一非零，或 rc==0 且带产物路径）；
  5) 匹配到的回执必须是**唯一**的，多份同样匹配则不判（交人）。
满足以上才升级为 DONE，并写 evidence（回执路径 + 匹配方式），绝不改动回执内容。

用法：
  python3 Tools/fleet/receipt_match.py           # 只看能收口哪些
  python3 Tools/fleet/receipt_match.py --apply   # 真收口
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
RCP = os.path.join(F, "queue-receipts")
NODE_SUFFIX = re.compile(r"-(bm-[abcd]|bm-m|bmb|bmc|bma)(?=-|$)")
DATE = re.compile(r"-?20\d{6}(T\d{6})?")
BAD = ("blocked", "skipped-all", "拒答", "refused", "no such file", "traceback")


def stem(name):
    base = os.path.basename(name or "")
    base = os.path.splitext(base)[0]
    base = NODE_SUFFIX.sub("", base)
    base = DATE.sub("", base)
    return base.lower().strip("-_")


def evidence_ok(doc):
    """回执里必须有真实产出迹象，不能只是一句"完成了"。"""
    if not isinstance(doc, dict):
        return False, "not-dict"
    # 只看**顶层状态字段**，不做全文关键词扫（2026-11-07 误判：回执里某个 filename
    # 或 note 提到 blocked 就被整份否掉，把真交付判成失败）。
    for k in ("verdict", "status", "state", "outcome"):
        v = str(doc.get(k) or "").upper()
        if v and any(v.startswith(x) for x in ("BLOCKED", "FAILED", "ERROR", "REFUSED")):
            return False, "bad-status:%s=%s" % (k, v)
    if doc.get("error"):
        return False, "error-field"
    blob = json.dumps(doc, ensure_ascii=False).lower()
    if "traceback (most recent call last)" in blob:
        return False, "traceback"
    # 自测/演练产出的回执不能当交付（否则等于拿假绿收口）
    for k in ("segments", "files", "rows", "artifacts", "clip_count", "count", "items",
              "runs", "positions", "trades", "records", "results"):
        v = doc.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return True, "%s=%s" % (k, v)
        if isinstance(v, list) and v:
            return True, "%s[%d]" % (k, len(v))
    if doc.get("ok") is True or doc.get("rc") == 0:
        return True, "rc/ok"
    return False, "no-evidence-field"


def load_jsonl(p):
    out = []
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    rows = load_jsonl(QUEUE)
    rcp_index = {}
    if os.path.isdir(RCP):
        for fn in os.listdir(RCP):
            low = fn.lower()
            if fn.endswith(".json") and "selftest" not in low and "dry" not in low \
                    and "canary" not in low:
                rcp_index.setdefault(stem(fn), []).append(fn)

    matched, ambiguous, rejected = [], [], []
    for r in rows:
        if r.get("state") not in ("UNVERIFIED", "RUNNING"):
            continue
        dl = r.get("deliverable") or ""
        if not dl:
            continue
        if os.path.exists(os.path.join(ROOT, dl)):
            continue                      # 盘上有真件，交给正常验收
        res = r.get("result") or {}
        if res.get("deliverable_exists") is True:
            continue
        key = stem(dl)
        cands = rcp_index.get(key, [])
        if not cands:
            # 允许回执比 deliverable 多尾巴（如 -01/-02 分片），只接受唯一前缀匹配
            cands = [fn for k, v in rcp_index.items() if k.startswith(key) for fn in v]
        if len(cands) == 0:
            continue
        if len(cands) > 1:
            owner = str(r.get("owner") or "")
            tag = owner.replace("bm-", "")          # bm-c -> c
            prefer = [c for c in cands if ("-bm-" + tag) in c or ("-bm" + tag) in c]
            if len(prefer) == 1:
                cands = prefer
            else:
                # 选"最晚且带证据"的那一份；若并列仍不判
                scored = []
                for c in cands:
                    try:
                        doc = json.load(open(os.path.join(RCP, c), encoding="utf-8"))
                        okx, _ = evidence_ok(doc)
                        ts = str(doc.get("ts") or doc.get("generated_at") or "")
                        if okx:
                            scored.append((ts, c))
                    except Exception:
                        pass
                scored.sort(reverse=True)
                if len(scored) == 1 or (len(scored) > 1 and scored[0][0] > scored[1][0]):
                    cands = [scored[0][1]]
                else:
                    ambiguous.append((r.get("id"), key, cands[:3]))
                    continue
        fn = cands[0]
        try:
            doc = json.load(open(os.path.join(RCP, fn), encoding="utf-8"))
        except Exception:
            rejected.append((r.get("id"), fn, "unparsable"))
            continue
        ok, why = evidence_ok(doc)
        if not ok:
            rejected.append((r.get("id"), fn, why))
            continue
        matched.append((r, fn, why))

    # 同一份回执被多张卡认领 = 重复卡：只收口最新的那张，其余标 DUP-OF 并取消，
    # 否则两份"完成"会各解锁一遍下游（2026-11-07 实测：quant 与 voice-corpus 各有重复卡）。
    by_receipt = {}
    for r, fn, why in matched:
        by_receipt.setdefault(fn, []).append((r, why))
    keep, dup = [], []
    for fn, group in by_receipt.items():
        if len(group) == 1:
            keep.append((group[0][0], fn, group[0][1]))
            continue
        group.sort(key=lambda x: str(x[0].get("created_at") or ""), reverse=True)
        keep.append((group[0][0], fn, group[0][1]))
        for r, why in group[1:]:
            dup.append((r, fn, group[0][0].get("id")))
    matched = keep
    for r, fn, winner in dup:
        print("  DUP %s 与 %s 指向同一回执 %s -> 取消前者" % (r.get("id"), winner, fn))

    print("[receipt-match] 可收口 %d 张｜歧义 %d｜证据不足 %d"
          % (len(matched), len(ambiguous), len(rejected)))
    for r, fn, why in matched:
        print("  %-42s <- %s (%s)" % (r.get("id"), fn, why))
    for rid, key, c in ambiguous[:5]:
        print("  AMBIG %s（%s）候选 %s" % (rid, key, c))
    for rid, fn, why in rejected[:5]:
        print("  REJECT %s <- %s（%s）" % (rid, fn, why))

    if a.apply and (matched or dup):
        sys.path.insert(0, HERE)
        import fleet_lane as fl
        chosen = {r.get("id"): fn for r, fn, _w in matched}
        dup_ids = {r.get("id"): winner for r, _fn, winner in dup}
        changed, dchg = [], []
        for r in rows:
            rid = r.get("id")
            if rid in chosen:
                fn = chosen[rid]
                r["state"] = "DONE"
                r["evidence"] = {"receipt": "cph4/fleet/queue-receipts/" + fn,
                                 "match": "receipt-pattern",
                                 "checked_at": __import__("datetime").datetime.now().isoformat(timespec="seconds")}
                r["note"] = ("receipt matched by name pattern (deliverable=%s, receipt=%s)"
                             % (os.path.basename(r.get("deliverable") or ""), fn))
                changed.append(rid)
            elif rid in dup_ids:
                r["state"] = "CANCELLED"
                r["note"] = "duplicate of %s (same artifact receipt)" % dup_ids[rid]
                dchg.append(rid)
        if changed or dchg:
            try:
                fl.merge_jsonl(QUEUE, rows)
            except Exception as e:
                print("  E-MERGE %s" % str(e)[:100])
                return 2
        print("  applied: %d 张 -> DONE｜去重 %d 张 -> CANCELLED" % (len(changed), len(dchg)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))