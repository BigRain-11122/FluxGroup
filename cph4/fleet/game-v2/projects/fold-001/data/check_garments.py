# -*- coding: utf-8 -*-
"""garments.json 自检。用法：python check_garments.py   （退出码 0 = 全通过）

检查项与 WARDROBE-CONTENT.md / DECISIONS（D-013 / D-015）对齐：
条数、类别分布、折法家族、房间 4 件、难度分布、字段取值、编码、运营钩子词。
钩子词与失败态词在源码里用拼接写法，避免本文件自己命中静态扫描。
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "garments.json")

CATEGORIES = {"T恤": 12, "衬衫": 12, "裤": 12, "裙": 11, "毛衣": 10,
              "外套": 10, "毛巾": 11, "袜子": 11, "床品": 11}
FAMILIES = {"对折", "三折", "卷", "立式", "挂"}
MATERIALS = {"棉", "麻", "丝", "羊毛", "绒", "混纺"}
FIELDS = ["id", "name", "category", "fold_family", "folds", "slots",
          "difficulty", "material", "room_ids", "codex"]

# 拼接写，避免源码中出现完整钩子词
HOOKS = ["每" + "日", "签" + "到", "stre" + "ak", "dai" + "ly",
         "check" + "in", "Fai" + "l", "Game" + "Over"]

problems = []


def check(ok, label, detail=""):
    if ok:
        print(f"PASS  {label}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"NG    {label}" + (f"  ({detail})" if detail else ""))
        problems.append(label)
    return ok


def main():
    raw = open(PATH, "rb").read()
    check(not raw.startswith(b"\xef\xbb\xbf"), "UTF-8 无 BOM", f"{len(raw)} bytes")

    try:
        doc = json.loads(raw.decode("utf-8"))
        check(True, "JSON 可解析")
    except Exception as e:  # noqa: BLE001
        check(False, "JSON 可解析", repr(e))
        return 1

    items = doc["garments"]
    check(doc.get("count") == len(items) == 100, "条数 = 100",
          f"count={doc.get('count')}, len={len(items)}")

    # id 连续
    ids = [g["id"] for g in items]
    expect = [f"G{i:03d}" for i in range(1, 101)]
    check(ids == expect, "id = G001–G100 连续且唯一")

    # 字段齐 + 取值合法
    missing = [(g.get("id"), f) for g in items for f in FIELDS if f not in g]
    check(not missing, "每条 10 个字段齐全", str(missing[:3]))
    extra = [(g["id"], k) for g in items for k in g if k not in FIELDS]
    check(not extra, "无多余字段", str(extra[:3]))

    bad = []
    for g in items:
        fs = g["folds"]
        if not (1 <= len(fs) <= 3):
            bad.append((g["id"], "folds 数量"))
        for f in fs:
            if f["axis"] not in ("x", "y") or not (0 <= f["at"] <= 1):
                bad.append((g["id"], "fold 轴/位置"))
            ok_dir = ("up", "down") if f["axis"] == "x" else ("left", "right")
            if f["dir"] not in ok_dir:
                bad.append((g["id"], f"dir 与 axis 不匹配 {f['axis']}/{f['dir']}"))
        if g["slots"] not in (1, 2):
            bad.append((g["id"], "slots"))
        if not (1 <= g["difficulty"] <= 5):
            bad.append((g["id"], "difficulty"))
        if g["material"] not in MATERIALS:
            bad.append((g["id"], "material"))
        if not (isinstance(g["room_ids"], list) and len(g["room_ids"]) == 1
                and 1 <= g["room_ids"][0] <= 25):
            bad.append((g["id"], "room_ids"))
        if not (1 <= len(g["codex"]) <= 20):
            bad.append((g["id"], f"codex 长度 {len(g['codex'])}"))
        if g["fold_family"] not in FAMILIES:
            bad.append((g["id"], "fold_family"))
        if g["category"] not in CATEGORIES:
            bad.append((g["id"], "category"))
    check(not bad, "字段取值合法（folds/slots/difficulty/material/room_ids/codex）", str(bad[:5]))

    # 类别分布
    cat = Counter(g["category"] for g in items)
    check(dict(cat) == CATEGORIES, "类别分布 12/12/12/11/10/10/11/11/11",
          " ".join(f"{k}{cat[k]}" for k in CATEGORIES))

    # 折法家族
    fam = Counter(g["fold_family"] for g in items)
    check(set(fam) == FAMILIES, "五个折法家族都有",
          " ".join(f"{k}{fam[k]}" for k in ["对折", "三折", "卷", "立式", "挂"]))

    # 房间
    room = Counter(g["room_ids"][0] for g in items)
    check(set(room) == set(range(1, 26)) and all(v == 4 for v in room.values()),
          "25 个房间各 4 件", f"rooms={len(room)}, min={min(room.values())}, max={max(room.values())}")

    # 难度分布
    d = Counter(g["difficulty"] for g in items)
    low = d[1] + d[2]
    mid = d[3]
    high = d[4] + d[5]
    check((low, mid, high) == (40, 35, 25), "难度分布 40 / 35 / 25",
          f"1-2级={low}, 3级={mid}, 4-5级={high}")

    # 名称唯一
    names = [g["name"] for g in items]
    check(len(set(names)) == 100, "name unique", f"{len(set(names))} 个不同名称")

    # 钩子词（手写断言，不依赖外部 grep）
    text = raw.decode("utf-8")
    hit = [h for h in HOOKS if h in text]
    check(not hit, "无运营钩子词 / 失败态词", str(hit))

    print()
    print("难度直方图: " + " ".join(f"{k}级={d[k]}" for k in range(1, 6)))
    print("折法家族: " + " ".join(f"{k}={fam[k]}" for k in ["对折", "三折", "卷", "立式", "挂"]))
    print()
    print(("ALL PASS" if not problems else f"{len(problems)} 项未通过") + f"  ({len(items)} 条)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
