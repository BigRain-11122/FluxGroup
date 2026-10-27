#!/usr/bin/env python3
"""ab_text.py — 从指定 AssetBundle 中导出 TextAsset（配置表）文本

用法:
  python Tools/recon/ab_text.py <out_dir> <ab_file> [ab_file...]

只读：不修改原始包；仅供理解配置结构。
"""
from __future__ import annotations
import sys
from pathlib import Path

import UnityPy


def dump(ab: Path, outdir: Path) -> list[dict]:
    rows = []
    try:
        env = UnityPy.load(str(ab))
    except Exception as e:
        return [{"ab": ab.name, "error": f"load: {type(e).__name__}: {e}"}]
    idx = 0
    for obj in env.objects:
        if obj.type.name not in ("TextAsset", "MonoBehaviour"):
            continue
        try:
            data = obj.read()
        except Exception as e:
            rows.append({"ab": ab.name, "error": f"read: {e}"})
            continue
        name = getattr(data, "m_Name", None) or f"obj{idx}"
        raw = getattr(data, "m_Script", None)
        if raw is None:
            script = getattr(data, "m_Script", None)
            raw = script
        if isinstance(raw, str):
            text = raw
        elif isinstance(raw, (bytes, bytearray)):
            try:
                text = bytes(raw).decode("utf-8")
            except UnicodeDecodeError:
                text = None
        else:
            text = None
        if not text:
            continue
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)[:80]
        ext = ".json" if text.lstrip()[:1] in "{[" else ".txt"
        dst = outdir / f"{ab.stem}__{safe}{ext}"
        dst.write_text(text, encoding="utf-8", errors="replace")
        rows.append({"ab": ab.name, "asset": name, "bytes": len(text), "out": dst.name,
                     "head": text[:120].replace("\n", " ")})
        idx += 1
    return rows


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    outdir = Path(sys.argv[1]); outdir.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[2:]:
        ab = Path(p)
        for r in dump(ab, outdir):
            print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())