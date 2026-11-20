#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""契约渲染器（W2）：YAML → 人读一页。只写 _render/，不改 YAML。

用法:
    python Tools/agents/contract_render.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "cph4" / "fleet" / "game-v2"
OUT = BASE / "contracts" / "_render"


def load(p: Path):
    with open(p, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def chash(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def check_text(chk) -> str:
    if not chk:
        return "—"
    kind = chk.get("kind")
    if kind == "manual":
        return f"人门 {chk.get('gate')}"
    if kind == "receipt":
        return "回执 " + ",".join(chk.get("gates", []))
    if kind == "enum":
        return f"{chk.get('field')} ∈ {chk.get('values')}"
    if kind == "range_map":
        return "；".join(f"{k} [{v[0]},{v[1]}]" for k, v in (chk.get("fields") or {}).items())
    if kind == "bool":
        return "；".join(f"{k}={v}" for k, v in (chk.get("fields") or {}).items())
    return str(chk)


def render_constitution(c):
    lines = [
        f"# 游戏子公司宪法 v{c.get('version')}",
        "",
        f"> 生效 {c.get('effective')} ｜ 所有者 {c.get('owner')} ｜ 生成于 {datetime.now():%Y-%m-%d %H:%M}",
        "> 本文件由 `contract_render.py` 从 `constitution.yaml` 生成，**勿手改**；改 YAML。",
        "",
        c.get("summary", ""),
        "",
        "| 编号 | 条款 | 内容 | 类型 | 判定 | 失败动作 |",
        "|---|---|---|---|---|---|",
    ]
    for a in c.get("articles", []):
        lines.append("| {id} | {title} | {statement} | {type} | {check} | {fail} |".format(
            id=a.get("id"), title=a.get("title"), statement=a.get("statement"),
            type=a.get("type"), check=check_text(a.get("check")), fail=a.get("on_fail")))
    lines.append("")
    return "\n".join(lines)


def render_classes(cs):
    lines = [
        f"# 类别契约 v{cs.get('version')}",
        "",
        f"> 继承宪法 {cs.get('extends_constitution')} ｜ 生成于 {datetime.now():%Y-%m-%d %H:%M}",
        "> 本文件由 `contract_render.py` 生成，勿手改。",
        "",
        "| 类别 | 名称 | 主平台 | 壳 | 价格 USD | 广告 | 周期 | 附加闸 | 资源 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for k, v in (cs.get("classes") or {}).items():
        cycle = v.get("cycle_weeks") or v.get("cycle_days")
        unit = "周" if v.get("cycle_weeks") else "天"
        lines.append("| {k} | {name} | {p} | {s} | {price} | {ads} | {cycle}{unit} | {g} | {r} |".format(
            k=k, name=v.get("name"), p=",".join(v.get("primary_platforms", [])),
            s=",".join(v.get("allowed_shells", [])),
            price=f"{v.get('price_usd', [0,0])[0]}–{v.get('price_usd', [0,0])[1]}",
            ads=v.get("ads"), cycle=cycle, unit=unit,
            g=",".join(v.get("gates_add", [])), r=v.get("resource_share")))
    lines.append("")
    return "\n".join(lines)


def render_project(p, path: Path):
    h = chash(p)
    lines = [
        f"# 项目契约：{p.get('name')}",
        "",
        f"> `{p.get('project_id')}` ｜ 类别 {p.get('class')} ｜ 契约哈希 `{h}`",
        f"> 宪法 {p.get('constitution_version')} ｜ 类别 {p.get('class_version')} ｜ 生成于 {datetime.now():%Y-%m-%d %H:%M}",
        "> 本文件由 `contract_render.py` 生成，勿手改；改 `" + path.name + "`。",
        "",
        "## 十行",
        "",
        "| 项 | 值 |",
        "|---|---|",
        f"| 玩家 | {p.get('player')} |",
        f"| 场景 | {p.get('scene')} |",
        f"| 核心动词 | {p.get('core_verb')} |",
        f"| 一局 | {p.get('session_seconds')} 秒 |",
        f"| 一次会话 | {p.get('session_minutes')} 分钟 |",
        f"| 最强一秒 | {p.get('strongest_second_what')}（第 {p.get('strongest_second_at')} 秒） |",
        f"| 主平台 | {','.join(p.get('primary_platforms', []))} |",
        f"| 壳 | {','.join(p.get('shells', [])) or '—'} |",
        f"| 价格 | ${p.get('price_usd')} |",
        f"| 复用度 | {p.get('reuse_ratio')} |",
        f"| 周期 | {p.get('cycle_weeks')} 周 |",
        f"| 阶段 | {p.get('phase')}（{p.get('experiment_id')}） |",
        f"| 内容小时 | {p.get('content_hours')} |",
        f"| 愿望单目标 | {p.get('wishlist_target')} |",
        f"| 退款上限 | {p.get('refund_max')} |",
        f"| 税率假设 | {p.get('tax_rate_assumed')} |",
        f"| 净收入目标 | ¥{p.get('net_target_cny')} |",
        "",
        "## 约束",
        "",
        "- 广告：{a} ｜ 服务器：{s} ｜ 换皮：{r} ｜ 多指必需：{m}".format(
            a="是" if p.get("ads") else "否",
            s="是" if p.get("server") else "否",
            r="是" if p.get("reskin_only") else "否",
            m="是" if p.get("multi_touch_required") else "否"),
        f"- 完成闸：{','.join(p.get('done_gates', []))}",
        f"- 类别附加：{','.join(p.get('done_addenda', [])) or '—'}",
        "",
        "## 不做",
        "",
    ]
    lines += [f"- {x}" for x in p.get("not_doing", [])]
    lines += ["", "## Kill", ""]
    lines += [f"- {x}" for x in p.get("kill", [])]
    lines += ["", f"状态：`{p.get('status')}`", ""]
    return "\n".join(lines), h


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    const = load(BASE / "constitution.yaml")
    classes = load(BASE / "classes.yaml")

    (OUT / "CONSTITUTION.md").write_text(render_constitution(const), encoding="utf-8")
    (OUT / "CLASSES.md").write_text(render_classes(classes), encoding="utf-8")

    rows = []
    for f in sorted((BASE / "contracts").glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        p = load(f)
        md, h = render_project(p, f)
        out = OUT / f"{p.get('project_id', f.stem)}.md"
        out.write_text(md, encoding="utf-8")
        rows.append({"file": f.name, "project_id": p.get("project_id"), "hash": h, "render": str(out)})

    print(json.dumps({"out": str(OUT), "rendered": rows}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
