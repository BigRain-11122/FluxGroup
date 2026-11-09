#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""icon_art_director.py - 让本机模型当美术指导，产出每款游戏图标的美术规格。

CEO 2026-11-09 令：「我要求你使用本地大模型和机队的本地模型能力去调度和解决」。
出图不碰云端，但"选什么图元、配什么色"是需要判断的活——这一层交给本机 4B 模型
（走机队既有 local_task.art_spec 题型：schema 校验 + 一次纠正 + 日上限账），
图形由 icon_render_local.py 确定性绘制。分工：模型做判断，代码做像素。

用法：
  python3 Tools/fleet/icon_art_director.py --run [--limit 34] [--resume]
  python3 Tools/fleet/icon_art_director.py --show
Exit: 0 全部有规格；2 有款无规格（模型不可达/校验失败，已回落默认）
"""
import argparse
import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "game-v1")
KINDS = {"tower", "watch", "merge", "arrow", "farm", "mask",
         "coin", "shield", "car", "pet", "store", "puzzle", "ghost", "crown",
         "bag", "food", "flower", "card", "fish", "gem"}
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def luma(hexs):
    h = hexs.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


ALIAS = {"schoolbag": "bag", "backpack": "bag", "briefcase": "bag", "bags": "bag",
         "cards": "card", "deck": "card", "flowers": "flower", "gems": "gem",
         "foods": "food", "fishes": "fish", "coins": "coin", "cars": "car"}


def normalize(spec):
    """模型爱自造词（schoolbag/deck/flowers）。先归一到词表，再判合法性。"""
    if not isinstance(spec, dict):
        return spec
    k = str(spec.get("kind") or "").strip().lower()
    if k in KINDS:
        spec["kind"] = k
        return spec
    if k in ALIAS and ALIAS[k] in KINDS:
        spec["kind"] = ALIAS[k]
        return spec
    for known in sorted(KINDS, key=len, reverse=True):
        if known in k:
            spec["kind"] = known
            return spec
    return spec


def valid(spec):
    if not isinstance(spec, dict):
        return False, "not-object"
    if spec.get("kind") not in KINDS:
        return False, "kind:%s" % spec.get("kind")
    bg = spec.get("bg")
    if not (isinstance(bg, list) and len(bg) == 2 and all(isinstance(x, str) and HEX.match(x) for x in bg)):
        return False, "bg"
    if not (isinstance(spec.get("fg"), str) and HEX.match(spec["fg"])):
        return False, "fg"
    bgavg = (luma(bg[0]) + luma(bg[1])) / 2
    if abs(luma(spec["fg"]) - bgavg) < 70:
        return False, "low-contrast"
    return True, "ok"


def out_path():
    return os.path.join(OUTDIR, "ARTEXT-%s.json" % time.strftime("%Y%m%d"))


def load_jobs():
    packs = sorted(glob.glob(os.path.join(OUTDIR, "ICON-JOBS-*.json")))
    if not packs:
        raise SystemExit("no ICON-JOBS; run icon_supply.py --manifest")
    return json.load(open(packs[-1], encoding="utf-8"))


def run(limit, resume):
    import local_task as lt
    jobs = load_jobs()
    path = out_path()
    state = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "engine": "local_model+deterministic_render",
             "task": "art_spec", "items": {}, "fails": {}}
    if resume and os.path.exists(path):
        state = json.load(open(path, encoding="utf-8"))
    todo = [j for j in jobs["jobs"] if j["dir"] not in state["items"]]
    if limit:
        todo = todo[:limit]
    print("jobs=%d todo=%d" % (len(jobs["jobs"]), len(todo)))
    for j in todo:
        text = "%s：%s" % (j["product"], (j.get("theme") or "")[:160])
        ok, obj, meta = lt.call("art_spec", text, model_hint="local-4b")
        if ok:
            obj = normalize(obj)
            good, why = valid(obj)
        else:
            good, why = False, meta.get("error", "model-fail")
        if not good:
            # 一次带约束的自我修复：明确告诉它只能从词表选、且主色要压得住背景
            fix = ("%s\n\n只能从这些图元里选一个：%s。主图形色与背景的明度差必须很大。"
                   "只输出 JSON。" % (text, "、".join(sorted(KINDS))))
            ok2, obj2, meta2 = lt.call("art_spec", fix, model_hint="local-4b-repair")
            if ok2:
                obj2 = normalize(obj2)
                good2, why2 = valid(obj2)
                if good2:
                    obj, good, why, meta = obj2, True, "repaired", meta2
        if good:
            state["items"][j["dir"]] = {"kind": obj["kind"], "bg": obj["bg"], "fg": obj["fg"],
                                        "src": "local_model", "sec": meta.get("sec")}
            state.get("fails", {}).pop(j["dir"], None)
            print("  OK  %-30s %-8s %s/%s" % (j["dir"], obj["kind"], obj["bg"][0], obj["bg"][1]))
        else:
            state["fails"][j["dir"]] = why
            print("  BAD %-30s %s" % (j["dir"], why))
        json.dump(state, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n_ok = len(state["items"])
    print("specs=%d fails=%d wrote %s" % (n_ok, len(state["fails"]), os.path.relpath(path, ROOT)))
    return 0 if not state["fails"] else 2


def show():
    path = out_path()
    if not os.path.exists(path):
        print("no spec file today")
        return 2
    d = json.load(open(path, encoding="utf-8"))
    print("items=%d fails=%d" % (len(d.get("items", {})), len(d.get("fails", {}))))
    for k, v in list(d["items"].items())[:10]:
        print("  %-30s %-8s %s" % (k, v["kind"], v["bg"]))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args(argv)
    if a.show:
        return show()
    if a.run:
        return run(a.limit, a.resume)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
