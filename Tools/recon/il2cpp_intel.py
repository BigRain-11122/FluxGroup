#!/usr/bin/env python3
"""il2cpp_intel.py — 从 IL2CPP global-metadata.dat 还原业务系统结构（只读）

用途：不反编译代码，先枚举类名/方法名/字段名，拿到"他们有哪些系统、怎么分层"的骨架。
用法：python Tools/recon/il2cpp_intel.py <global-metadata.dat> [--out out.json]

注意：仅用于理解实现与结构，不得搬运代码。
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

CATS = {
    "关卡/波次": ["level", "wave", "stage", "chapter", "round", "spawn", "monster", "enemy", "boss"],
    "战斗": ["battle", "combat", "damage", "hp", "attack", "bullet", "weapon", "gun", "fire", "hit", "crit", "dodge"],
    "技能/构筑": ["skill", "buff", "talent", "upgrade", "card", "affix", "effect", "attr"],
    "经济": ["coin", "gold", "diamond", "currency", "shop", "store", "price", "cost", "reward", "drop", "loot"],
    "广告/变现": ["advert", "ad_", "rewarded", "interstitial", "iap", "purchase", "billing", "order", "pay"],
    "成长/任务": ["task", "quest", "mission", "daily", "sign", "achievement", "pass", "battlepass", "chest"],
    "存档/账号": ["save", "user", "account", "login", "profile", "playerdata", "localdata"],
    "UI/流程": ["panel", "popup", "window", "screen", "ui", "loading", "guide", "tutorial", "tips"],
    "关卡生成": ["map", "grid", "path", "tile", "obstacle", "barrier", "spawner", "generator", "seed"],
    "性能/资源": ["pool", "asset", "bundle", "loader", "cache", "atlas", "texture", "audio", "sound"],
}

IDENT = re.compile(rb"[A-Za-z_][A-Za-z0-9_<>`\[\],\. ]{3,80}")


def extract_strings(blob: bytes) -> set[str]:
    out = set()
    for m in IDENT.finditer(blob):
        s = m.group(0).decode("ascii", "ignore").strip()
        if 3 < len(s) <= 80 and re.search(r"[A-Za-z]", s):
            out.add(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    p = Path(args.metadata)
    if not p.exists():
        print("not found", p, file=sys.stderr)
        return 2
    blob = p.read_bytes()
    strings = extract_strings(blob)

    buckets: dict[str, list[str]] = defaultdict(list)
    for s in strings:
        low = s.lower()
        for cat, keys in CATS.items():
            if any(k in low for k in keys):
                buckets[cat].append(s)
                break

    # 只保留"像类型名"的（首字母大写、非全大写、含驼峰）
    def looks_type(x: str) -> bool:
        return bool(re.match(r"^[A-Z][A-Za-z0-9_]{2,}$", x)) and not x.isupper()

    result = {"metadata": str(p), "total_strings": len(strings), "categories": {}}
    for cat, items in buckets.items():
        types = sorted({x for x in items if looks_type(x)})
        result["categories"][cat] = {
            "count": len(items),
            "types_sample": types[:80],
            "types_total": len(types),
        }

    out = Path(args.out) if args.out else p.with_suffix(".intel.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v["types_total"] for k, v in result["categories"].items()}, ensure_ascii=False))
    print("->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())