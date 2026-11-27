# -*- coding: utf-8 -*-
"""m-v1-globe · 自检：文件存在、含全部区域名、体积 < 15MB"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "dist", "globe.html")
REGIONS = os.path.join(ROOT, "modules", "m-w1-regions", "data", "regions.json")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not os.path.exists(OUT):
        print("✗ 没有 globe.html，先跑 build.py")
        return 1
    html = open(OUT, encoding="utf-8").read()
    regions = json.load(open(REGIONS, encoding="utf-8"))["regions"]
    missing = [r["name"] for r in regions if r["name"] not in html]
    mb = os.path.getsize(OUT) / 1048576.0
    if missing:
        print(f"✗ 缺区域：{missing}")
        return 1
    if mb > 15:
        print(f"✗ 文件过大 {mb:.1f}MB")
        return 1
    print(f"✓ globe.html 含 {len(regions)} 块区域 · {mb:.2f}MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
