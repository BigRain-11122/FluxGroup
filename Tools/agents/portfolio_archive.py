#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组合归位：把在册产品按 CEO 2026-11-20 令分为 候选 / 入库 / 线外。

规则（确定性，可复跑）：
- 唯一有真包且内容完整的吸嘟嘟 → CANDIDATE（须按新规重评，不自动保留）
- FluxVerse 城市线 → OUT-OF-LINE（不属小游戏组合）
- 其余 → ARCHIVED-LIBRARY（只读、可复用资产、不再维护、不占队列）

输出：
  cph4/fleet/game-v2/PORTFOLIO-ARCHIVE-v1.json
  cph4/fleet/game-v2/PORTFOLIO-ARCHIVE-v1.md
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "cph4/fleet/game-v1/SUBMIT-PACK-20261120.json"
OUT_JSON = ROOT / "cph4/fleet/game-v2/PORTFOLIO-ARCHIVE-v1.json"
OUT_MD = ROOT / "cph4/fleet/game-v2/PORTFOLIO-ARCHIVE-v1.md"


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    items = data.get("items", [])

    rows = []
    for it in items:
        name = it.get("product") or it.get("dir") or ""
        d = it.get("dir") or ""
        lacks = it.get("lacks") or []
        has_build = not any("可运行包" in x for x in lacks)

        if "GimmeAll" in name or "GimmeAll" in d:
            status, reason = "CANDIDATE", "唯一有真包与完整内容；须按六信号重评，不自动保留"
        elif "FluxVerse" in name or "FluxVerse" in d:
            status, reason = "OUT-OF-LINE", "城市/3D 线，不属小游戏组合"
        else:
            status = "ARCHIVED-LIBRARY"
            reason = ("有包但无商业化与爆款证据" if has_build
                      else "无真包、无商业化验证、无爆款证据")
        rows.append({
            "product": name, "dir": d, "status": status, "reason": reason,
            "has_build": has_build, "verdict": it.get("verdict"),
            "lacks": lacks, "assets_reusable": True,
            "restore": "须重新走 G-A 入池 + 3 天原型 + G-B 开工，不继承旧立项",
        })

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    result = {
        "schema": "portfolio-archive/1",
        "date": date.today().isoformat(),
        "order": "CEO 2026-11-20：完成度不高、无商业化潜质、无爆款潜质的都入库，不做了；从头开始。",
        "counts": counts,
        "items": rows,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        f"# 组合归位（{result['date']}）",
        "",
        f"- 在册 {len(rows)} 款：候选 {counts.get('CANDIDATE',0)} ｜ 入库 {counts.get('ARCHIVED-LIBRARY',0)} ｜ 线外 {counts.get('OUT-OF-LINE',0)}",
        "",
        "> 入库 = 只读封存：不维护、不排期、不占队列；资产与系统可复用；恢复须重新立项。",
        "",
        "## 候选（仅 1 款）",
        "",
    ]
    for r in rows:
        if r["status"] == "CANDIDATE":
            lines.append(f"- **{r['product']}**：{r['reason']}")
    lines += ["", "## 入库", ""]
    for r in rows:
        if r["status"] == "ARCHIVED-LIBRARY":
            lines.append(f"- {r['product']}（{r['dir']}）— {r['reason']}")
    lines += ["", "## 线外", ""]
    for r in rows:
        if r["status"] == "OUT-OF-LINE":
            lines.append(f"- {r['product']}（{r['dir']}）— {r['reason']}")
    lines += ["", "## 恢复规则", "",
              "1. 先过机会卡 G-A（主源信号 + 差异假设 + 三端可行）。",
              "2. 再过 3 天原型（10 秒爽 / 反向测试 / 单指）。",
              "3. 最后过 G-B 开工评审；不继承任何旧立项与旧排期。"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"json": str(OUT_JSON), "md": str(OUT_MD), "counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
