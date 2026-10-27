#!/usr/bin/env python3
"""cocos_cfg.py — 从 Cocos Creator 资源目录直接抽取明文配置表

Cocos 的 `assets/assets/resources/import/**/*.json` 里 `cc.JsonAsset` 是明文，
不需要反编译。本脚本把其中的对象按表名导出为 JSON，并打印清单。

用法: python Tools/recon/cocos_cfg.py <extracted_apk_dir> <slug>
产出: media/recon/data/<slug>/<table>.json + _index.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def iter_json_assets(root: Path):
    for p in root.glob("**/*.json"):
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                head = f.read(400)
        except Exception:
            continue
        if '"cc.JsonAsset"' not in head:
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        # 结构: [ver..., types, ..., [idx, name, value], ...]
        for node in data:
            if not isinstance(node, list) or len(node) != 1:
                continue
            item = node[0]
            if isinstance(item, list) and len(item) >= 3 and isinstance(item[2], dict):
                yield p, item[1], item[2]


def main() -> int:
    src = Path(sys.argv[1])
    slug = sys.argv[2]
    out = ROOT / "media/recon/data" / slug
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{1,48}$")

    for path, name, cfg in iter_json_assets(src):
        for table, rows in cfg.items():
            if not isinstance(rows, (dict, list)) or not rows:
                continue
            if not NAME_RE.match(str(table)):      # 过滤纯数字资源 ID / 关卡名
                continue
            dst = out / f"{table}.json"
            dst.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            index[table] = len(rows) if hasattr(rows, "__len__") else 0
    (out / "_index.json").write_text(
        json.dumps(dict(sorted(index.items(), key=lambda kv: -kv[1])), ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(json.dumps({"slug": slug, "tables": len(index),
                      "top": list(sorted(index.items(), key=lambda kv: -kv[1]))[:8]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())