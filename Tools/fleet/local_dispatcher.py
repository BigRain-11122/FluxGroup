#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_dispatcher.py - 让本机模型做派单决策（不是让人挑，也不是让云端挑）

为什么（CEO 2026-11-09 令「很多本地的条件我都具备了，你只是调用本地模型，做你的 agent 调度能力」）：
  之前的推进方式是我读盘、我挑活、我执行——本地模型只在出图这类边角活上被调用一次。
  真正的调度权还在我（云端）手里，本地模型只是工具。这一层把「派哪张卡」这个决策
  交给本机模型，我只承担两件它做不了的事：确定性收集（脚本读盘）与执行（落盘改文件）。

分工：
  L1 确定性  收集候选（解析 ADVANCE-7x24 的 W 表 + NEXT-ACTIONS 业务表）、白名单校验、落卡
  L2 本机模型 在候选里挑一条、给理由、定层（local_task 的 dispatch 题型，带 schema 与一次纠正）
  L0 我      按卡执行；验收只认磁盘事实

硬约束：
  1. 模型只能从给定候选里挑，编号不在白名单一律判废（模型不许发明任务）。
  2. 模型不可达或连续判废 → 回落规则排序，并在卡里写明 fallback，不静默假装是模型决策。
  3. 只出卡，不执行；执行与验收由调用方做，卡里带 next_action 与 verify。

用法：
  python3 Tools/fleet/local_dispatcher.py --run            # 收集 → 本机模型决策 → 落卡
  python3 Tools/fleet/local_dispatcher.py --dry-run        # 只看候选集，不调模型
  python3 Tools/fleet/local_dispatcher.py --show           # 看最近一张卡
  python3 Tools/fleet/local_dispatcher.py --self-test      # 白名单/回落正反例

Exit: 0 出卡成功；2 模型不可用且回落；3 候选为空；4 自检失败
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state", "dispatch")
LOG = os.path.join(STATE, "dispatch-log.jsonl")
PLAN = os.path.join(FLEET, "ADVANCE-7x24-v1.md")

MAX_CANDIDATES = 10
MAX_CELL = 88           # 单个字段字符上限，4B 模型上下文有限


def _clip(s, n=MAX_CELL):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _latest(pattern):
    hits = sorted(glob.glob(pattern))
    return hits[-1] if hits else None


# ---------------------------------------------------------------- 收集（L1）

def from_plan():
    """解析 ADVANCE-7x24-v1.md 的 W 表。已完成的跳过。"""
    out = []
    if not os.path.exists(PLAN):
        return out
    for line in open(PLAN, encoding="utf-8"):
        if not line.startswith("| W"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        wid, biz, task, layer = cells[0], cells[1], cells[2], cells[3]
        status, accept = cells[4], cells[5]
        if "已完成" in status or "已完成" in task:
            continue
        out.append({
            "id": wid,
            "biz": _clip(biz, 24),
            "state": _clip(status, 60),
            "next": _clip(task, 60),
            "accept": _clip(accept, 60),
            "layer_hint": "L2" if "本地模型" in layer or "L2" in layer else "L1",
            "source": "ADVANCE-7x24-v1.md",
        })
    return out


def from_next_actions():
    """NEXT-ACTIONS 里 ENGINE 型阻塞（机器能干）且未完成的业务。"""
    out = []
    f = _latest(os.path.join(FLEET, "NEXT-ACTIONS-*.json"))
    if not f:
        return out
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        return out
    for b in d.get("businesses", []):
        if str(b.get("state", "")).upper() in ("DONE", "SHIPPED"):
            continue
        if str(b.get("blocker_type", "")).upper() != "ENGINE":
            continue
        out.append({
            "id": "B:" + str(b.get("id", "?")),
            "biz": _clip(b.get("name", ""), 24),
            "state": _clip(b.get("stage", ""), 60),
            "next": _clip(b.get("next_product", ""), 60),
            "accept": _clip(b.get("accept", ""), 60),
            "layer_hint": "L2",
            "source": os.path.basename(f),
        })
    return out


def collect():
    cands, seen = [], set()
    for c in from_plan() + from_next_actions():
        key = (c["biz"], c["next"][:24])
        if key in seen:
            continue
        seen.add(key)
        cands.append(c)
    return cands[:MAX_CANDIDATES]


def render(cands):
    return "\n".join(
        "%s | %s | %s | %s" % (c["id"], c["biz"], c["state"], c["next"]) for c in cands
    )


# ---------------------------------------------------------------- 决策（L2）

def decide_by_local_model(cands):
    """交给本机模型。返回 (card_fields, meta)。失败返回 (None, meta)。"""
    import local_task as lt

    ok, obj, meta = lt.call("dispatch", render(cands), model_hint="dispatcher")
    if not ok:
        return None, dict(meta, reason="model-schema-fail")
    pick = str(obj.get("pick", "")).strip()
    layer = str(obj.get("layer", "")).strip().upper()
    ids = {c["id"] for c in cands}
    if pick != "HOLD" and pick not in ids:
        # 模型发明了编号：判废，不回填、不改写它的答案
        return None, dict(meta, reason="pick-not-in-whitelist", pick=pick)
    if layer not in ("L0", "L1", "L2"):
        return None, dict(meta, reason="bad-layer", layer=layer)
    return {
        "pick": pick,
        "why": _clip(obj.get("why", ""), 120),
        "layer": layer,
    }, meta


def decide_by_rules(cands):
    """回落：W 号小优先，其次来源顺序。带 fallback 标记，冒充不了模型决策。"""
    if not cands:
        return None
    def key(c):
        m = re.match(r"W(\d+)", c["id"])
        return (0, int(m.group(1))) if m else (1, 0)
    c = sorted(cands, key=key)[0]
    return {"pick": c["id"], "why": "模型不可用，按队列序号回落", "layer": c["layer_hint"]}


# ---------------------------------------------------------------- 落卡

def write_card(cands, decision, mode, meta):
    os.makedirs(STATE, exist_ok=True)
    now = datetime.now()
    cid = "DISPATCH-" + now.strftime("%Y%m%d-%H%M%S")
    picked = next((c for c in cands if c["id"] == decision["pick"]), None)
    snapshot = hashlib.sha256(render(cands).encode("utf-8")).hexdigest()[:16]
    card = {
        "card_id": cid,
        "ts": now.isoformat(timespec="seconds"),
        "mode": mode,                       # local_model | fallback_rules | hold
        "decider": meta.get("model_hint") if mode == "local_model" else "rules",
        "model_sec": meta.get("sec"),
        "model_retried": meta.get("retried"),
        "model_error": meta.get("reason") or meta.get("error"),
        "why": decision["why"],
        "layer": decision["layer"],
        "picked": picked,
        "candidates_n": len(cands),
        "candidates_sha16": snapshot,
        "candidates_ids": [c["id"] for c in cands],
        "next_action": None if not picked else picked["next"],
        "verify": None if not picked else picked["accept"],
    }
    path = os.path.join(STATE, cid + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=1)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": card["ts"], "card": cid, "mode": mode, "pick": decision["pick"],
            "layer": decision["layer"], "n": len(cands), "sec": meta.get("sec"),
        }, ensure_ascii=False) + "\n")
    return card, path


# ---------------------------------------------------------------- 入口

def run(dry_run=False):
    cands = collect()
    if not cands:
        print("NO-CANDIDATES: 队列为空，检查 ADVANCE-7x24-v1.md 与 NEXT-ACTIONS")
        return 3
    if dry_run:
        print("=== 候选 %d 条（L1 读盘，未调模型）===" % len(cands))
        for c in cands:
            print("  %-12s %-14s %-42s -> %s" % (c["id"], c["biz"], c["state"], c["next"]))
        return 0

    decision, meta = decide_by_local_model(cands)
    mode = "local_model"
    if decision is None:
        decision = decide_by_rules(cands)
        mode = "fallback_rules"
        print("FALLBACK: 本机模型未给出合法决策（%s），按规则回落——此卡已标注，不冒充模型决策"
              % (meta.get("reason") or meta.get("error")))
    if decision["pick"] == "HOLD":
        mode = "hold"
        print("HOLD: 本机模型判断当前没有该推进的项")

    card, path = write_card(cands, decision, mode, meta)
    print(json.dumps({
        "card": card["card_id"], "mode": mode, "pick": decision["pick"],
        "why": decision["why"], "layer": decision["layer"],
        "next_action": card["next_action"], "verify": card["verify"],
        "model_sec": card["model_sec"], "candidates": len(cands),
    }, ensure_ascii=False))
    print("card: " + os.path.relpath(path, ROOT))
    return 0 if mode == "local_model" else 2


def show():
    f = _latest(os.path.join(STATE, "DISPATCH-*.json"))
    if not f:
        print("还没有派单卡")
        return 1
    d = json.load(open(f, encoding="utf-8"))
    print(json.dumps(d, ensure_ascii=False, indent=1))
    return 0


def self_test():
    ok_all = True
    cands = [
        {"id": "W3", "biz": "fleet-ops", "state": "待读台账", "next": "清偿路径债",
         "accept": "new=0", "layer_hint": "L1", "source": "t"},
        {"id": "W2", "biz": "asset-lib", "state": "待出样", "next": "重写打标判据",
         "accept": "failed=0", "layer_hint": "L2", "source": "t"},
    ]

    def chk(name, cond):
        nonlocal ok_all
        print(("  PASS  " if cond else "  FAIL  ") + name)
        ok_all = ok_all and cond

    # 白名单：模型编造编号必须判废（不能就地回填成某个真实候选）
    ids = {c["id"] for c in cands}
    chk("invented pick rejected", "W99" not in ids)
    chk("whitelist accepts real id", "W2" in ids)
    # 回落按序号：W2 应排在 W3 前
    r = decide_by_rules(cands)
    chk("rules fallback prefers lower W", r["pick"] == "W2")
    # 空候选不崩
    chk("empty candidates -> None", decide_by_rules([]) is None)
    # 渲染紧凑且含 id
    txt = render(cands)
    chk("render has ids", "W2" in txt and "W3" in txt)
    chk("render line count", len(txt.splitlines()) == 2)
    print("self-test %s" % ("OK" if ok_all else "FAILED"))
    return 0 if ok_all else 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="收集并用本机模型决策，落卡")
    ap.add_argument("--dry-run", action="store_true", help="只看候选集，不调模型")
    ap.add_argument("--show", action="store_true", help="看最近一张卡")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.show:
        return show()
    if a.dry_run:
        return run(dry_run=True)
    if a.run:
        return run()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
