#!/usr/bin/env python3
"""dump_schema.py — 从 Il2CppDumper 的 dump.cs 导出全部配置表结构

用法: python Tools/recon/dump_schema.py <dump.cs> <out.json>
产出: 每个继承 ProtoBaseStruct 的类 = 一张配置表；含字段名/类型/顺序。
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

CLASS_RE = re.compile(r"^(?:public|internal|private|protected)?\s*(?:sealed\s+)?class\s+(\w+)\s*:\s*([\w\.]+)", re.M)
FIELD_RE = re.compile(r"^\s*public\s+([\w\.\[\]<>]+)\s+(\w+);", re.M)


def main() -> int:
    src = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    out = Path(sys.argv[2])
    tables = []
    for m in CLASS_RE.finditer(src):
        name, base = m.group(1), m.group(2)
        if base != "ProtoBaseStruct":
            continue
        end = src.find("\n}", m.start())
        body = src[m.start():end if end > 0 else m.start() + 4000]
        fields = [{"type": t, "name": n} for t, n in FIELD_RE.findall(body)]
        tables.append({"class": name, "fields": fields})

    tables.sort(key=lambda t: t["class"])
    out.write_text(json.dumps({"count": len(tables), "tables": tables}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"tables={len(tables)} fields={sum(len(t['fields']) for t in tables)} -> {out}")
    for t in tables[:5]:
        print(" -", t["class"], len(t["fields"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())