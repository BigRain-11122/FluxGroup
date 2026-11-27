# -*- coding: utf-8 -*-
"""kf_pack_extract.py - machine-truth extractor for MV KF packs.

Loads a <song>-shots-v2.py module by path, walks the NEW tuple list, and reports
per-frame: id, window, duration, speed, note, kf word count, t2i lint issues,
detected light block and texture block (matched against the module's own
LX.LIGHT / LX.TEXTURE entries so nothing is guessed).

Usage:
    python Tools/kf_pack_extract.py <shots.py> [--json out.json] [--md out.md]
"""
import argparse
import importlib.util
import json
import os
import sys


def load_module(path):
    name = "shots_" + os.path.basename(path).replace("-", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def detect_block(prompt, table):
    """Return the first table key whose text appears verbatim (case-insensitive)."""
    low = prompt.lower()
    for key, val in table.items():
        if isinstance(val, str) and val and val.lower() in low:
            return key
    return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots")
    ap.add_argument("--json")
    ap.add_argument("--md")
    args = ap.parse_args()

    mod = load_module(args.shots)
    LX = mod.LX
    rows = []
    for item in mod.NEW:
        sid, t0, t1, speed, note, kfp = item[0], item[1], item[2], item[3], item[4], item[5]
        words = len(kfp.split())
        issues = LX.lint(kfp, mode="t2i") if hasattr(LX, "lint") else []
        rows.append({
            "id": sid,
            "t0": t0,
            "t1": t1,
            "dur": round(float(t1) - float(t0), 2),
            "speed": speed,
            "note": note,
            "words": words,
            "lint": list(issues) if issues else [],
            "light": detect_block(kfp, LX.LIGHT),
            "tex": detect_block(kfp, LX.TEXTURE),
            "lens": detect_block(kfp, LX.LENS),
        })

    over = [r["id"] for r in rows if r["words"] > 200]
    dirty = [r["id"] for r in rows if r["lint"]]
    summary = {
        "shots_file": os.path.basename(args.shots),
        "frames": len(rows),
        "words_min": min(r["words"] for r in rows),
        "words_max": max(r["words"] for r in rows),
        "over_200": over,
        "lint_dirty": dirty,
        "duration_sum": round(sum(r["dur"] for r in rows), 2),
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print()
    print("| id | window | dur | speed | light | tex | lens | words | lint | note |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| %s | %.2f-%.2f | %.2f | %.2f | %s | %s | %s | %d | %s | %s |" % (
            r["id"], r["t0"], r["t1"], r["dur"], r["speed"],
            r["light"], r["tex"], r["lens"], r["words"],
            "CLEAN" if not r["lint"] else ",".join(map(str, r["lint"])),
            r["note"]))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=2)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("| id | window | dur | speed | light | tex | lens | words | lint | note |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|\n")
            for r in rows:
                f.write("| %s | %.2f-%.2f | %.2f | %.2f | %s | %s | %s | %d | %s | %s |\n" % (
                    r["id"], r["t0"], r["t1"], r["dur"], r["speed"],
                    r["light"], r["tex"], r["lens"], r["words"],
                    "CLEAN" if not r["lint"] else ",".join(map(str, r["lint"])),
                    r["note"]))


if __name__ == "__main__":
    main()