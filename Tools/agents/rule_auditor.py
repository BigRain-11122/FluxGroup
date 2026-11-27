#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规则审计员 v1（只读）。

检查流程/规则文档里的六类问题，输出 JSON + Markdown 到 cph4/fleet/game-v2/audits/。
不修改任何被审计文件。

用法:
    python Tools/agents/rule_auditor.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cph4" / "fleet" / "game-v2" / "audits"
TODAY = date.today()

SOURCES = [
    "cph4/fleet/game-v2/GAME-OPS-v2.md",
    "cph4/fleet/game-v2/INTENT-LINEAGE-v1.md",
    "cph4/fleet/game-v2/AGENT-SPEC-v1.md",
    "cph4/fleet/ri/game/CANON-v1.md",
    "cph4/fleet/company/biggame/TOP-DESIGN-v1.md",
    "cph4/fleet/products/game.yaml",
    "cph4/fleet/GAME-PARALLEL-START-20261018.md",
    "gaming/MiniGame/NORTHSTAR.md",
    "gaming/MiniGame/README.md",
    "gaming/MiniGame/_共享与总控/13_研发毕业标准.md",
    "gaming/MiniGame/_共享与总控/18_游戏标准体系与建立律.md",
    "gaming/MiniGame/_共享与总控/小游戏黄金前置律V1.md",
    "gaming/MiniGame/09_吸嘟嘟_GimmeAll_CAR/GimmeAll/docs/FAMILY-EDITION-MASTER-20261023.md",
    "gaming/MiniGame/09_吸嘟嘟_GimmeAll_CAR/GimmeAll/docs/FAMILY-EDITION-PRODUCTION-CHARTER.md",
    "gaming/MiniGame/09_吸嘟嘟_GimmeAll_CAR/GimmeAll/docs/FAMILY-EDITION-AI-PIPELINE.md",
    "gaming/MiniGame/09_吸嘟嘟_GimmeAll_CAR/GimmeAll/docs/FAMILY-EDITION-TOOLING-ADR.md",
    "docs/orders.md",
]

DOMAINS = {
    "毕业标准": ["毕业标准", "毕业判据", "研发毕业"],
    "测试验收": ["测试环节", "测试标准", "验收标准"],
    "资产验收": ["资产验收", "美术验收"],
    "音频验收": ["音频验收", "音频标准"],
    "提审合规": ["提审", "合规标准"],
    "组织治理": ["组织与治理", "组织总纲", "公司组织"],
    "开发链路": ["自动化开发链路", "开发工序", "生产管线"],
    "商业模型": ["商业模型", "收益模型", "付费模型"],
}

AUTHORITY = ["唯一权威", "唯一入口", "单一事实源", "唯一归纳面", "唯一载体", "唯一事实源"]
EXT = r"(?:md|json|py|ps1|html|ya?ml|csv|txt)"
PATH_RE = re.compile(r"[`\"']([A-Za-z0-9_\u4e00-\u9fa5][A-Za-z0-9_./\\\-\u4e00-\u9fa5]*\." + EXT + r")[`\"']")
DATE_RE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")


def read(path: Path, cap=900_000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(cap)
    except OSError:
        return ""


def load_sources():
    out = []
    for rel in SOURCES:
        p = ROOT / rel
        if p.exists():
            out.append((rel, p, read(p)))
    return out


def check_authority(sources):
    hits = []
    by_domain = {}
    for rel, p, text in sources:
        for i, line in enumerate(text.splitlines(), 1):
            if not any(k in line for k in AUTHORITY):
                continue
            domains = [d for d, keys in DOMAINS.items() if any(k in line for k in keys)]
            rec = {"file": rel, "line": i, "domains": domains,
                   "text": line.strip()[:180]}
            hits.append(rec)
            for d in domains:
                by_domain.setdefault(d, set()).add(rel)
    conflicts = [{"domain": d, "files": sorted(fs)}
                 for d, fs in by_domain.items() if len(fs) > 1]
    return {"claims": len(hits), "conflicts": conflicts, "sample": hits[:40]}


def check_broken_paths(sources):
    missing = []
    checked = 0
    for rel, p, text in sources:
        for m in PATH_RE.finditer(text):
            cand = m.group(1).replace("\\", "/").strip()
            if any(x in cand for x in ("*", "<", ">", "{", "}", "://", "...")):
                continue
            checked += 1
            cand_norm = cand.lstrip("./")
            options = [ROOT / cand_norm, p.parent / cand_norm, p.parent.parent / cand_norm]
            if cand_norm.startswith("docs/"):
                options.append(p.parent / cand_norm[5:])
                options.append(p.parent.parent / cand_norm)
            if not any(o.exists() for o in options):
                line_no = text[:m.start()].count("\n") + 1
                missing.append({"file": rel, "line": line_no, "ref": cand})
    # 去重
    seen, uniq = set(), []
    for item in missing:
        key = (item["file"], item["ref"])
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return {"checked": checked, "missing": len(uniq), "sample": uniq[:60]}


def check_stale_authority(sources):
    stale = []
    for rel, p, text in sources:
        authority_lines = [l for l in text.splitlines() if any(k in l for k in AUTHORITY)]
        if not authority_lines:
            continue
        dates = []
        for m in DATE_RE.finditer(text):
            try:
                dates.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
            except ValueError:
                pass
        if not dates:
            continue
        last = max(dates)
        age = (TODAY - last).days
        if age > 30:
            stale.append({"file": rel, "last_date": last.isoformat(), "age_days": age,
                          "authority_lines": len(authority_lines)})
    stale.sort(key=lambda x: x["age_days"], reverse=True)
    return {"stale": len(stale), "items": stale}


def _collect(text, pattern):
    out = []
    for m in re.finditer(pattern, text):
        g = m.group(1)
        try:
            v = float(g)
        except (TypeError, ValueError):
            continue
        out.append(v)
    return out


def check_numeric(sources):
    # 只比"同类上限"：主包、整包、单局、冷启动各自独立，避免把实测值当红线。
    concepts = {
        "主包上限MB": (r"主包[^\n]{0,14}?(?:≤|<=|<)\s*(\d+(?:\.\d+)?)\s*MB", 1.5),
        "整包上限MB": (r"(?:整包|总包)[^\n]{0,14}?(?:≤|<=|<)\s*(\d+(?:\.\d+)?)\s*MB", 1.5),
        "单局秒": (r"(?:单局|会话时长)[^\n]{0,16}?(\d+)\s*(?:[-–~至]\s*(\d+)\s*)?秒", 2.0),
        "冷启动上限秒": (r"冷启动[^\n]{0,14}?(?:≤|<=|<)\s*(\d+(?:\.\d+)?)", 2.0),
    }
    result = {}
    for name, (pattern, spread) in concepts.items():
        values = {}
        for rel, p, text in sources:
            for m in re.finditer(pattern, text):
                v = m.group(1)
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                values.setdefault(fv, set()).add(rel)
                if m.lastindex and m.lastindex >= 2 and m.group(2):
                    try:
                        values.setdefault(float(m.group(2)), set()).add(rel)
                    except ValueError:
                        pass
        if len(values) >= 2:
            lo, hi = min(values), max(values)
            if hi / lo >= spread:
                result[name] = {
                    "distinct": len(values),
                    "values": sorted(values.keys()),
                    "files": {str(k): sorted(v) for k, v in sorted(values.items())},
                }
    return {"conflicts": len(result), "detail": result}


def check_gate_bloat():
    prod = ROOT / "gaming/MiniGame/09_吸嘟嘟_GimmeAll_CAR/GimmeAll"
    tools = prod / "Tools"
    assets = prod / "Assets"
    if not tools.exists():
        return {"status": "NOT_RUN"}
    py = [p for p in tools.glob("*.py")]
    gate = [p for p in py if re.search(r"check|readiness|negctl|audit", p.name, re.I)]
    cs = list(assets.rglob("*.cs")) if assets.exists() else []
    ratio = (len(gate) / len(cs)) if cs else None
    return {"status": "OK" if ratio is not None else "NOT_RUN",
            "py": len(py), "gate_scripts": len(gate), "cs": len(cs),
            "ratio": round(ratio, 3) if ratio is not None else None,
            "flag": bool(ratio and ratio > 0.15)}


def check_automation():
    cmd = ("Get-ScheduledTask | Where-Object {$_.TaskName -like 'MiniGame*'} | "
           "Select-Object TaskName,@{n='State';e={[string]$_.State}} | ConvertTo-Json -Compress")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                           capture_output=True, text=True, timeout=40)
        raw = (r.stdout or "").strip()
        if not raw:
            return {"status": "NOT_RUN", "reason": "no output"}
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        total = len(data)
        off = [d["TaskName"] for d in data if str(d.get("State")) not in ("Ready", "Running")]
        return {"status": "OK", "total": total, "disabled": len(off),
                "ratio": round(len(off) / total, 2) if total else None,
                "flag": bool(total and len(off) / total > 0.5),
                "disabled_names": off}
    except Exception as exc:  # noqa: BLE001
        return {"status": "NOT_RUN", "reason": str(exc)[:120]}


def propose_patches(authority, broken, stale):
    out = []
    for c in authority["conflicts"]:
        out.append({"risk": "low", "action": "加 CONFLICT 注记",
                    "target": c["files"], "why": f"{c['domain']} 出现多个唯一权威"})
    if broken["sample"]:
        out.append({"risk": "low", "action": "修断链指针",
                    "target": [b["ref"] for b in broken["sample"][:10]],
                    "why": f"{broken['missing']} 处引用不存在"})
    for s in stale["items"][:5]:
        out.append({"risk": "low", "action": "加 SUPERSEDED 头",
                    "target": [s["file"]], "why": f"自称权威但停更 {s['age_days']} 天"})
    return out


def main():
    sources = load_sources()
    if not sources:
        print("NO SOURCES", file=sys.stderr)
        return 2

    authority = check_authority(sources)
    broken = check_broken_paths(sources)
    stale = check_stale_authority(sources)
    numeric = check_numeric(sources)
    bloat = check_gate_bloat()
    automation = check_automation()

    result = {
        "schema": "rule-audit/1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sources": [s[0] for s in sources],
        "authority": authority,
        "broken_paths": broken,
        "stale_authority": stale,
        "numeric": numeric,
        "gate_bloat": bloat,
        "automation": automation,
        "patch_proposals": propose_patches(authority, broken, stale),
        "severity": {
            "high": len(authority["conflicts"]) + len(stale["items"]) + numeric["conflicts"]
                    + (1 if automation.get("flag") else 0),
            "medium": broken["missing"] + (1 if bloat.get("flag") else 0),
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    jpath = OUT / f"RULE-AUDIT-{stamp}.json"
    jpath.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        f"# 规则审计 {result['generated_at']}",
        "",
        f"- 审计源：{len(sources)} 份",
        f"- 高危：{result['severity']['high']} ｜ 中危：{result['severity']['medium']}",
        "",
        "## 1. 权威冲突",
        "",
    ]
    if authority["conflicts"]:
        for c in authority["conflicts"]:
            lines.append(f"- **{c['domain']}**：{len(c['files'])} 份都自称唯一 → " +
                         "、".join(f"`{f}`" for f in c["files"]))
    else:
        lines.append("- 无")
    lines += ["", "## 2. 断链指针", "", f"- 检查 {broken['checked']} 条，缺失 {broken['missing']} 条"]
    for b in broken["sample"][:15]:
        lines.append(f"- `{b['file']}:{b['line']}` → `{b['ref']}`")
    lines += ["", "## 3. 停更的权威件", ""]
    if stale["items"]:
        for s in stale["items"]:
            lines.append(f"- `{s['file']}`：最后内容日期 {s['last_date']}，已 {s['age_days']} 天")
    else:
        lines.append("- 无")
    lines += ["", "## 4. 数值冲突", ""]
    if numeric["detail"]:
        for name, d in numeric["detail"].items():
            lines.append(f"- **{name}**：{d['distinct']} 个不同值 → {d['values']}")
    else:
        lines.append("- 无")
    lines += ["", "## 5. 闸膨胀", ""]
    if bloat.get("status") == "OK":
        lines.append(f"- 工具 {bloat['py']} 个，其中检查类 {bloat['gate_scripts']} 个；"
                     f"产品 C# {bloat['cs']} 个；比值 **{bloat['ratio']}**"
                     f"（阈值 0.15，{'超标' if bloat['flag'] else '正常'}）")
    else:
        lines.append("- 未运行")
    lines += ["", "## 6. 自动化停摆", ""]
    if automation.get("status") == "OK":
        lines.append(f"- MiniGame 任务 {automation['total']} 个，禁用 {automation['disabled']} 个"
                     f"（{automation['ratio']}）")
    else:
        lines.append(f"- 未运行：{automation.get('reason', '')}")
    lines += ["", "## 7. 建议补丁（低风险，待批）", ""]
    if result["patch_proposals"]:
        for p in result["patch_proposals"]:
            t = "、".join(p["target"]) if isinstance(p["target"], list) else p["target"]
            lines.append(f"- [{p['risk']}] {p['action']}：{p['why']} → {t}")
    else:
        lines.append("- 无")
    lines += ["", "> 本报告只读生成；不修改任何被审计文件。"]

    mpath = OUT / f"RULE-AUDIT-{stamp}.md"
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "json": str(jpath), "md": str(mpath),
        "sources": len(sources),
        "high": result["severity"]["high"], "medium": result["severity"]["medium"],
        "authority_conflicts": len(authority["conflicts"]),
        "broken": broken["missing"], "stale": len(stale["items"]),
        "numeric": numeric["conflicts"], "gate_ratio": bloat.get("ratio"),
        "tasks_disabled": f"{automation.get('disabled')}/{automation.get('total')}"
        if automation.get("status") == "OK" else "n/a",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
