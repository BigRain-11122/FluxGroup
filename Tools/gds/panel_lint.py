#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""立项评审卡校验器（GREENLIGHT-PANEL-v1 的机器面）。

用法:
    python Tools/gds/panel_lint.py                    # 校验 panels/*.yaml
    python Tools/gds/panel_lint.py --self-test        # 负控自检（坏卡必须被抓）
    python Tools/gds/panel_lint.py --render <card>    # 生成一页纸 <card 同名>.md

只做确定性判定，零 LLM：
  - 权重预注册且和=1；七席必须齐
  - 4-5 分必须挂 E1/E2 证据，且文件真实存在
  - E4（假设）不得出现在任何支撑 GO 的判据里
  - 否决项必须逐条 checked；触发即只能 NO-GO
  - 证据日期不得晚于评审日，且不超过卡上声明的 max_age_days
  - 覆盖率 = 已评估权重占比；GO 需 >=0.85，CONDITIONAL 需 >=0.60
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cph4" / "fleet" / "game-v2"
PANELS = BASE / "panels"

sys.path.insert(0, str(ROOT / "Tools" / "agents"))
from contract_lint import contract_hash, load_yaml  # noqa: E402

SEATS = {"S1": 0.15, "S2": 0.15, "S3": 0.10, "S4": 0.15, "S5": 0.20, "S6": 0.15, "S7": 0.10}
SEAT_NAMES = {
    "S1": "市场", "S2": "竞品/差异化", "S3": "受众",
    "S4": "设计/内容", "S5": "工程", "S6": "商业", "S7": "独立审计",
}
LEVELS = {"E1", "E2", "E3", "E4"}
VETO_IDS = {"V1", "V2", "V3", "V4"}
MIN_CRITERIA = 3
GO_SCORE, GO_COVERAGE = 4.0, 0.85
COND_SCORE, COND_COVERAGE = 3.0, 0.60
DECISIONS = {"GO", "CONDITIONAL", "NO-GO"}

GB_JUDGEMENTS = 12   # GREENLIGHT-BOUNDARY §三 12 个边界判例
AR_ENTRIES = 22      # ARCHIVED-RULES §二 22 条


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def parse_date(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(v[:19], fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(v).date()
        except ValueError:
            return None
    return None


def article_ids() -> set[str]:
    try:
        const = load_yaml(BASE / "constitution.yaml")
        return {a.get("id") for a in const.get("articles", []) if a.get("id")}
    except Exception:  # noqa: BLE001
        return {f"C-{i:02d}" for i in range(1, 15)}


def rule_ref_ok(ref: str, arts: set[str]) -> bool:
    if not isinstance(ref, str) or not ref.strip():
        return False
    if ref in {"G-A", "G-B", "G-C", "G-D"}:
        return True
    if ref in arts:
        return True
    import re
    if m := re.fullmatch(r"GB-(\d{1,2})", ref):
        return 1 <= int(m.group(1)) <= GB_JUDGEMENTS
    if m := re.fullmatch(r"AR-(\d{1,2})", ref):
        return 1 <= int(m.group(1)) <= AR_ENTRIES
    if ref in VETO_IDS:
        return True
    if re.fullmatch(r"(RPB|AEP|PANEL)-§\d+(\.\d+)?", ref):
        return True
    return False


def resolve_evidence(path: str) -> Path | None:
    if not isinstance(path, str) or not path.strip():
        return None
    p = Path(path)
    if p.is_absolute():
        return p if p.exists() else None
    for base in (ROOT, BASE):
        cand = base / p
        if cand.exists():
            return cand
    return None


def validate(card: dict) -> tuple[list[str], dict]:
    fails: list[str] = []
    arts = article_ids()
    metrics = {"coverage": 0.0, "score": 0.0, "decision": "NO-GO",
               "veto_hits": [], "not_assessed": [], "e4_in_go": 0}

    # --- 顶层字段 ---
    for k in ("schema", "version", "project_id", "panel", "phase",
              "contract_file", "run_at", "weights", "seats", "veto", "decision", "signed_by"):
        if k not in card:
            fails.append(f"缺字段: {k}")
    if fails:
        return fails, metrics
    if card["schema"] != "fluxgame/panel":
        fails.append(f"schema 应为 fluxgame/panel，实际 {card['schema']}")

    run_at = parse_date(card["run_at"])
    if run_at is None:
        fails.append(f"run_at 无法解析: {card['run_at']!r}")
        run_at = date.today()
    max_age = int(card.get("max_age_days", 60))

    # --- 权重与席位 ---
    weights = card.get("weights") or {}
    if set(weights) != set(SEATS):
        fails.append(f"权重席位不齐: 缺 {sorted(set(SEATS) - set(weights))} 多 {sorted(set(weights) - set(SEATS))}")
    else:
        total = sum(float(v) for v in weights.values())
        if abs(total - 1.0) > 1e-9:
            fails.append(f"权重和={total:.6f}，必须为 1")
        for sid, v in weights.items():
            if float(v) != SEATS[sid]:
                fails.append(f"{sid} 权重 {v} 与预注册 {SEATS[sid]} 不一致（改动需升版重跑）")

    seats = card.get("seats") or {}
    if set(seats) != set(SEATS):
        fails.append(f"席位不齐: 缺 {sorted(set(SEATS) - set(seats))} 多 {sorted(set(seats) - set(SEATS))}")

    # --- 契约哈希 ---
    cpath = ROOT / str(card.get("contract_file", ""))
    if cpath.exists():
        try:
            live = contract_hash(load_yaml(cpath))
            if live != card.get("contract_hash"):
                fails.append(f"契约哈希漂移: 卡={card.get('contract_hash')} 现={live}（旧卡作废）")
        except Exception as exc:  # noqa: BLE001
            fails.append(f"契约读取失败: {exc}")
    else:
        fails.append(f"契约文件不存在: {card.get('contract_file')}")

    # --- 逐席判据 ---
    authors: dict[str, str] = {}
    w_sum = 0.0
    w_score = 0.0
    for sid in SEATS:
        seat = seats.get(sid)
        if not isinstance(seat, dict):
            continue
        authors[sid] = str(seat.get("author") or "")
        crit = seat.get("criteria") or []
        if not isinstance(crit, list) or len(crit) < MIN_CRITERIA:
            fails.append(f"{sid} 判据少于 {MIN_CRITERIA} 条")
            continue
        seen: set[str] = set()
        scores: list[float] = []
        for c in crit:
            cid = c.get("id", "?")
            if cid in seen:
                fails.append(f"判据 id 重复: {cid}")
            seen.add(cid)
            if not str(cid).startswith(sid + "."):
                fails.append(f"判据 {cid} 前缀应为 {sid}.")
            if not rule_ref_ok(c.get("rule_ref"), arts):
                fails.append(f"判据 {cid} 引用不存在的法条: {c.get('rule_ref')!r}")

            score = c.get("score", None)
            ev = c.get("evidence") or []
            if score is None:
                scores.append(None)
                metrics["not_assessed"].append(cid)
            else:
                if not isinstance(score, int) or isinstance(score, bool) or not (0 <= score <= 5):
                    fails.append(f"判据 {cid} 分数非法: {score!r}（0-5 或 null）")
                    scores.append(None)
                    metrics["not_assessed"].append(cid)
                    continue
                scores.append(float(score))
                lv = [e.get("level") for e in ev if isinstance(e, dict)]
                bad = [x for x in lv if x not in LEVELS]
                if bad:
                    fails.append(f"判据 {cid} 证据级别非法: {bad}")
                if score >= 4 and not any(x in {"E1", "E2"} for x in lv):
                    fails.append(f"判据 {cid} 给 {score} 分但没有 E1/E2 证据")
                if score >= 4 and "E4" in lv:
                    metrics["e4_in_go"] += 1
                    fails.append(f"判据 {cid} 用 E4 假设支撑 {score} 分")
                if score <= 3 and not ev:
                    fails.append(f"判据 {cid} 无证据（低分也要写为什么）")

            for e in ev:
                if not isinstance(e, dict):
                    fails.append(f"判据 {cid} 证据项不是对象")
                    continue
                if resolve_evidence(e.get("path")) is None:
                    fails.append(f"判据 {cid} 证据路径不存在: {e.get('path')!r}")
                ed = parse_date(e.get("at"))
                if ed is None:
                    fails.append(f"判据 {cid} 证据日期无法解析: {e.get('at')!r}")
                elif ed > run_at:
                    fails.append(f"判据 {cid} 证据日期晚于评审日: {ed} > {run_at}")
                elif (run_at - ed).days > max_age:
                    fails.append(f"判据 {cid} 证据过期: {ed} 超过 {max_age} 天")

        assessed = [s for s in scores if s is not None]
        ratio = len(assessed) / len(scores) if scores else 0.0
        w = SEATS[sid]
        w_sum += w * ratio
        if assessed:
            w_score += w * (sum(assessed) / len(assessed))

    # --- 独立性 ---
    s7 = authors.get("S7", "")
    if s7 and s7 == str(card.get("signed_by")):
        fails.append("S7 审计席作者不得与签字人同一人")
    for sid in ("S1", "S2", "S3", "S4", "S5", "S6"):
        if s7 and authors.get(sid) and authors[sid] == s7:
            fails.append(f"S7 审计席作者与 {sid} 同一人，评审不独立")

    # --- 否决项 ---
    veto = card.get("veto") or []
    vids = {v.get("id") for v in veto if isinstance(v, dict)}
    if not VETO_IDS <= vids:
        fails.append(f"否决项不齐: 缺 {sorted(VETO_IDS - vids)}")
    for v in veto:
        if not isinstance(v, dict):
            continue
        if v.get("checked") is not True:
            fails.append(f"否决项 {v.get('id')} 未核（checked 必须为 true）")
        if not rule_ref_ok(v.get("rule_ref"), arts):
            fails.append(f"否决项 {v.get('id')} 引用不存在的法条: {v.get('rule_ref')!r}")
        if v.get("triggered"):
            metrics["veto_hits"].append(v.get("id"))

    # --- 重算决策 ---
    coverage = round(w_sum, 4)
    score = round(w_score / w_sum, 4) if w_sum > 0 else 0.0
    metrics["coverage"] = coverage
    metrics["score"] = score
    if metrics["veto_hits"]:
        computed = "NO-GO"
    elif coverage >= GO_COVERAGE and score >= GO_SCORE and metrics["e4_in_go"] == 0:
        computed = "GO"
    elif coverage >= COND_COVERAGE and score >= COND_SCORE:
        computed = "CONDITIONAL"
    else:
        computed = "NO-GO"
    metrics["decision"] = computed

    declared = card.get("decision")
    if declared not in DECISIONS:
        fails.append(f"decision 非法: {declared!r}")
    elif declared != computed:
        fails.append(f"决策与判据不符: 卡写 {declared}，重算 {computed} "
                     f"(score={score}, coverage={coverage}, veto={metrics['veto_hits'] or 'none'})")
    if declared == "GO" and metrics["not_assessed"]:
        fails.append(f"GO 不允许有未评估判据: {metrics['not_assessed']}")

    # --- 缺测必须被补测动作覆盖（不允许「先记着」） ---
    all_ids = {c.get("id") for s in seats.values() if isinstance(s, dict)
               for c in (s.get("criteria") or [])}
    covered: set[str] = set()
    for a in card.get("actions") or []:
        if not isinstance(a, dict):
            fails.append("actions 项不是对象")
            continue
        for cid in a.get("covers") or []:
            if cid not in all_ids:
                fails.append(f"动作 {a.get('id')} 覆盖了不存在的判据 {cid}")
            covered.add(cid)
        if not a.get("due"):
            fails.append(f"动作 {a.get('id')} 缺截止日期")
    uncovered = [c for c in metrics["not_assessed"] if c not in covered]
    if uncovered:
        fails.append(f"未评估判据没有补测动作覆盖: {uncovered}")

    return fails, metrics


def render(card: dict, metrics: dict) -> str:
    lines = [
        f"# 立项评审 · {card.get('project_id')}（{card.get('phase')}）",
        "",
        f"- 评审日：{card.get('run_at')}　签字：{card.get('signed_by')}",
        f"- 契约哈希：`{card.get('contract_hash')}`",
        f"- **结论：{metrics['decision']}**　加权均分 {metrics['score']}/5　覆盖率 {metrics['coverage']:.0%}",
        "",
        "| 席 | 权重 | 均分 | 判据 | 缺测 |",
        "|---|---:|---:|---:|---:|",
    ]
    seats = card.get("seats") or {}
    for sid in SEATS:
        seat = seats.get(sid) or {}
        crit = seat.get("criteria") or []
        vals = [c.get("score") for c in crit if c.get("score") is not None]
        mean = f"{sum(vals) / len(vals):.2f}" if vals else "—"
        miss = sum(1 for c in crit if c.get("score") is None)
        lines.append(f"| {sid} {SEAT_NAMES.get(sid, '')} | {SEATS[sid]:.2f} | {mean} | {len(crit)} | {miss} |")
    missing = metrics.get("not_assessed") or []
    if missing:
        lines += ["", "## 缺测判据（不补不能 GO）", ""]
        for cid in missing:
            lines.append(f"- `{cid}`")
    findings = card.get("findings") or []
    if findings:
        lines += ["", "## 关键发现", ""]
        for f in findings:
            lines.append(f"- **[{f.get('severity', '?')}] {f.get('id', '')}** {f.get('text', '')}")
    actions = card.get("actions") or []
    if actions:
        lines += ["", "## 补测动作", ""]
        lines.append("| # | 动作 | 谁 | 截止 |")
        lines.append("|---|---|---|---|")
        for a in actions:
            lines.append(f"| {a.get('id', '')} | {a.get('text', '')} | {a.get('owner', '')} | {a.get('due', '')} |")
    hits = metrics.get("veto_hits") or []
    lines += ["", "## 否决项", ""]
    if hits:
        for v in hits:
            lines.append(f"- **{v} 触发 → NO-GO**")
    else:
        lines.append("- V1–V4 全部已核，未触发")
    return "\n".join(lines) + "\n"


def self_test() -> int:
    import copy
    import tempfile

    good = {
        "schema": "fluxgame/panel", "version": 1, "project_id": "SELFTEST",
        "panel": "greenlight", "phase": "G-B",
        "contract_file": "cph4/fleet/game-v2/contracts/fold-001.yaml",
        "contract_hash": contract_hash(load_yaml(BASE / "contracts" / "fold-001.yaml")),
        "run_at": date.today().isoformat(), "max_age_days": 60,
        "weights": dict(SEATS),
        "seats": {
            sid: {
                "name": SEAT_NAMES[sid], "author": f"author-{sid}",
                "criteria": [
                    {"id": f"{sid}.{i}", "rule_ref": "RPB-§1", "score": 4,
                     "evidence": [{"level": "E1", "path": "cph4/fleet/game-v2/CURRENT-RULES-v1.md",
                                   "at": date.today().isoformat()}]}
                    for i in (1, 2, 3)
                ],
            } for sid in SEATS
        },
        "veto": [
            {"id": v, "rule_ref": "RPB-§4", "checked": True, "triggered": False}
            for v in ("V1", "V2", "V3", "V4")
        ],
        "decision": "GO", "signed_by": "producer",
    }

    cases: list[tuple[str, dict]] = []
    c = copy.deepcopy(good); c["weights"]["S1"] = 0.9; cases.append(("权重和≠1", c))
    c = copy.deepcopy(good); c["seats"].pop("S7"); cases.append(("缺席位", c))
    c = copy.deepcopy(good)
    c["seats"]["S1"]["criteria"][0]["evidence"] = [{"level": "E4", "path": "cph4/fleet/game-v2/CURRENT-RULES-v1.md", "at": date.today().isoformat()}]
    cases.append(("4分靠E4", c))
    c = copy.deepcopy(good); c["seats"]["S1"]["criteria"][0]["evidence"] = []; cases.append(("4分无证据", c))
    c = copy.deepcopy(good)
    c["seats"]["S1"]["criteria"][0]["evidence"] = [{"level": "E1", "path": "no/such/file.md", "at": date.today().isoformat()}]
    cases.append(("证据路径不存在", c))
    c = copy.deepcopy(good); c["seats"]["S1"]["criteria"][0]["rule_ref"] = "C-99"; cases.append(("引用假法条", c))
    c = copy.deepcopy(good); c["veto"][0]["checked"] = False; cases.append(("否决未核", c))
    c = copy.deepcopy(good); c["veto"][0]["triggered"] = True; cases.append(("否决触发仍GO", c))
    c = copy.deepcopy(good)
    for i in range(3):
        c["seats"]["S3"]["criteria"][i]["score"] = None
    cases.append(("覆盖率不足仍GO", c))
    c = copy.deepcopy(good); c["seats"]["S7"]["author"] = c["signed_by"]; cases.append(("审计不独立", c))
    c = copy.deepcopy(good); c["seats"]["S1"]["criteria"][0]["score"] = 6; cases.append(("分数越界", c))
    c = copy.deepcopy(good); c["seats"]["S1"]["criteria"][1]["id"] = "S1.1"; cases.append(("判据重复", c))
    c = copy.deepcopy(good)
    for i in range(3):
        c["seats"]["S3"]["criteria"][i]["score"] = None
    for cr in c["seats"]["S1"]["criteria"]:
        cr["score"] = 3
    c["decision"] = "CONDITIONAL"
    cases.append(("缺测无补测动作", c))

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        failures = 0
        f, m = validate(good)
        if f:
            failures += 1
            print(f"FAIL 好卡应通过，实际报 {len(f)} 条: {f[:3]}")
        else:
            print(f"PASS 好卡通过（score={m['score']} cov={m['coverage']} decision={m['decision']}）")
        for name, bad in cases:
            f, _ = validate(bad)
            if not f:
                failures += 1
                print(f"FAIL 坏卡未被抓: {name}")
            else:
                print(f"PASS 抓到: {name}（{f[0]}）")
    print(json.dumps({"self_test": "PASS" if failures == 0 else "FAIL", "failures": failures},
                     ensure_ascii=False))
    return 0 if failures == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--render", metavar="CARD")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if args.render:
        path = Path(args.render)
        if not path.is_absolute():
            path = (ROOT / path) if (ROOT / path).exists() else (PANELS / path)
        card = load_yaml(path)
        fails, metrics = validate(card)
        out = path.with_suffix(".md")
        out.write_text(render(card, metrics), encoding="utf-8")
        print(json.dumps({"rendered": rel(out), "decision": metrics["decision"],
                          "score": metrics["score"], "coverage": metrics["coverage"],
                          "fails": fails[:10]}, ensure_ascii=False, indent=1))
        return 0 if not fails else 1

    cards = sorted(PANELS.glob("*.yaml")) if PANELS.exists() else []
    report = []
    bad = 0
    for f in cards:
        card = load_yaml(f)
        fails, metrics = validate(card)
        bad += 1 if fails else 0
        report.append({
            "file": rel(f), "project": card.get("project_id"), "phase": card.get("phase"),
            "decision": metrics["decision"], "score": metrics["score"],
            "coverage": metrics["coverage"], "not_assessed": metrics["not_assessed"],
            "veto": metrics["veto_hits"], "fails": fails,
        })
    print(json.dumps({"cards": len(cards), "invalid": bad, "report": report},
                     ensure_ascii=False, indent=1))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
