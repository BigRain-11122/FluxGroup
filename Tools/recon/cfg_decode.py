#!/usr/bin/env python3
"""cfg_decode.py — 按 il2cpp schema 解码配置表二进制

格式依据（反汇编确认）：字段按声明顺序无条件读写；
  uint/int/float = 4 字节大端；byte = 1 字节；
  string = 4 字节长度 + UTF-8；数组 = 4 字节个数 + 元素。

用法: python Tools/recon/cfg_decode.py <schema.json> <Class> <bin> [--start N] [--limit N]
"""
from __future__ import annotations
import json
import struct
import sys
from pathlib import Path

SCALARS = {"byte": ("B", 1), "sbyte": ("b", 1), "short": ("h", 2), "ushort": ("H", 2),
           "int": ("i", 4), "uint": ("I", 4), "long": ("q", 8), "ulong": ("Q", 8),
           "float": ("f", 4), "double": ("d", 8), "bool": ("?", 1)}


class Reader:
    def __init__(self, buf: bytes, pos: int = 0):
        self.b, self.p = buf, pos

    def scalar(self, t: str):
        fmt, size = SCALARS[t]
        v = struct.unpack_from(">" + fmt, self.b, self.p)[0]
        self.p += size
        return v

    def string(self):
        n = struct.unpack_from(">I", self.b, self.p)[0]
        self.p += 4
        s = self.b[self.p:self.p + n].decode("utf-8", "replace")
        self.p += n
        return s


def decode_struct(r: Reader, fields: list[dict], schema: dict) -> dict:
    out = {}
    for f in fields:
        t, name = f["type"], f["name"]
        if t.endswith("[]"):
            base = t[:-2]
            n = r.scalar("uint")
            if base in SCALARS:
                out[name] = [r.scalar(base) for _ in range(n)]
            else:
                sub = schema.get(base)
                out[name] = [decode_struct(r, sub, schema) for _ in range(n)] if sub else [f"<{base}?>"] * n
        elif t == "string":
            out[name] = r.string()
        elif t in SCALARS:
            out[name] = r.scalar(t)
        else:
            sub = schema.get(t)
            out[name] = decode_struct(r, sub, schema) if sub else f"<{t}?>"
    return out


def main() -> int:
    schema_path, cls, bin_path = sys.argv[1], sys.argv[2], sys.argv[3]
    start = 16
    limit = 3
    if "--start" in sys.argv:
        start = int(sys.argv[sys.argv.index("--start") + 1], 0)
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    data = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    schema = {t["class"]: t["fields"] for t in data["tables"]}
    fields = schema[cls]
    buf = Path(bin_path).read_bytes()
    r = Reader(buf, start)
    rows = []
    for i in range(limit):
        before = r.p
        try:
            row = decode_struct(r, fields, schema)
        except Exception as e:
            print("decode error at record", i, "offset", before, e)
            break
        rows.append(row)
        print(f"--- record {i} @ {before} -> {r.p} ({r.p-before}B) ---")
        print(json.dumps(row, ensure_ascii=False)[:700])
    print(f"\nfile={len(buf)} end={r.p} left={len(buf)-r.p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())