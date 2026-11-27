#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_library_check.py - 资产库体检：这个库现在能开片吗，还是攒了一堆垃圾。

为什么（2026-11-03 CEO：「做 AI 相关的 MV/短剧/漫剧/动画/有声小说/漫画等需要大量特色资产库，
要大量高质量的，不是垃圾库」）：
  资产库最典型的死法不是"没有"，是"很多但都不能用"——攒了几千张图，没有授权、没有规格、
  同一张脸换个背景当新角色。所以判据不是文件数，是：**数量够不够开片、规格达不达标、
  授权齐不齐、有没有重复凑数**。本工具只报这四件事，不给"看起来很多"的假绿。

数据来源：
  目录 = media/asset/<class>/（characters/voices/styles/typography 按目录算一条，其余按文件算）
  目标 = cph4/fleet/asset-lib-v1/LIBRARY-TARGETS.json（数字只在那里改）
  授权 = 每个 class 目录下的 RIGHTS.json（或每条资产的 RIGHTS.json）

用法：
  python3 asset_library_check.py [--tier p0|p1|p2] [--json] [--out receipts/x.json] [--sample 20]
Exit: 0 达到该档目标；1 有缺口（列出每类差多少）；2 读不到目标文件。
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1", "LIBRARY-TARGETS.json")
ASSET = os.path.join(ROOT, "media", "asset")
IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
VID = (".mp4", ".mov", ".m4v", ".webm", ".mkv")
AUD = (".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg")
OK_LICENSE = ("own", "public-domain", "cc0", "cc-by", "licensed")


def probe(path):
    """(w,h,dur)；ffprobe 缺失时退回 ffmpeg。"""
    fp = shutil.which("ffprobe")
    if fp:
        try:
            r = subprocess.run([fp, "-v", "error", "-show_streams", "-show_format",
                                "-of", "json", path], capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                d = json.loads(r.stdout)
                v = next((s for s in d.get("streams") or [] if s.get("codec_type") == "video"), {})
                fmt = d.get("format") or {}
                return (int(v.get("width") or 0), int(v.get("height") or 0),
                        float(fmt.get("duration") or 0))
        except Exception:
            pass
    ff = shutil.which("ffmpeg") or os.path.join(os.path.expanduser("~"), "bin", "ffmpeg")
    try:
        r = subprocess.run([ff, "-hide_banner", "-i", path], capture_output=True,
                           text=True, errors="replace", timeout=60)
        t = (r.stdout or "") + (r.stderr or "")
        d = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", t)
        dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
        m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", t)
        return (int(m.group(1)) if m else 0, int(m.group(2)) if m else 0, dur)
    except Exception:
        return (0, 0, 0.0)


def rights_ok(paths):
    """授权是否齐：目录级或条目级 RIGHTS.json，license 必须在白名单。"""
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            d = json.load(open(p, encoding="utf-8-sig"))
        except Exception:
            continue
        if str(d.get("license") or "").lower() in OK_LICENSE:
            if d.get("real_person") is True and d.get("consent") is not True:
                continue
            return True
    return False


def entries_for(cls, spec):
    d = os.path.join(ASSET, cls)
    if not os.path.isdir(d):
        return [], d
    if spec.get("layout") == "dir":
        # 一个子目录 = 一条资产（角色包/音色/风格包/字体包）
        items = [os.path.join(d, n) for n in sorted(os.listdir(d))
                 if os.path.isdir(os.path.join(d, n)) and not n.startswith(("_", "."))]
    else:
        exts = IMG + VID + AUD
        items = [p for p in sorted(glob.glob(os.path.join(d, "*"))) if p.lower().endswith(exts)]
    return items, d


def check_class(cls, spec, tier, sample):
    items, d = entries_for(cls, spec)
    target = int(spec.get(tier) or 0)
    empty, dups = [], []
    if spec.get("layout") == "dir":
        # 2026-11-11 两个假绿（实测）：空目录被算成一条资产（characters 五个空壳仍报 8/8 OK）；
        # 同一份语料每天复制成新批次目录也被算成多条（voices 4 份逐字节相同的 sliced 语料报 9/6 OK）。
        # 目录数不是可用件数——只留「有文件且互不重复」的目录，其余写进 issues。
        kept, seen = [], {}
        for p in items:
            inside = [x for x in glob.glob(os.path.join(p, "**", "*"), recursive=True)
                      if x.lower().endswith(IMG + VID + AUD)]
            if not inside:
                empty.append(os.path.basename(p))
                continue
            sig = tuple(sorted((os.path.basename(x), os.path.getsize(x)) for x in inside))
            if sig in seen:
                dups.append("%s=%s 的副本" % (os.path.basename(p), seen[sig]))
                continue
            seen[sig] = os.path.basename(p)
            kept.append(p)
        items = kept
    detail = {"count": len(items), "target": target,
              "pct": round(len(items) / target * 100, 1) if target else None,
              "license_ok": 0, "spec_ok": 0, "issues": []}
    if empty:
        detail["issues"].append("空目录（无可用文件·不计入）：%s" % ",".join(empty[:8]))
    if dups:
        detail["issues"].append("重复副本（不计入）：%s" % "; ".join(dups[:5]))
    if not items:
        detail["issues"].append("空目录（目标 %d）" % target)
        return detail
    if not rights_ok([os.path.join(d, "RIGHTS.json")]):
        # 条目级也算：只要每条自己有 RIGHTS 就放行
        per_item = [p if os.path.isdir(p) else os.path.splitext(p)[0] for p in items]
        lic_n = sum(1 for p in per_item
                    if rights_ok([os.path.join(p, "RIGHTS.json")] if os.path.isdir(p) else []))
        detail["license_ok"] = lic_n
        if lic_n == 0:
            detail["issues"].append("整类没有授权声明（目录级 RIGHTS.json 缺失，条目级也没有）")
    else:
        detail["license_ok"] = len(items)

    sp = spec.get("spec") or {}
    min_side = sp.get("min_side")
    dr = sp.get("dur")
    bad = []
    for p in items[:sample]:
        f = p
        if os.path.isdir(p):
            inner = [x for x in glob.glob(os.path.join(p, "**", "*"), recursive=True)
                     if x.lower().endswith(IMG + VID + AUD)]
            if not inner:
                bad.append([os.path.basename(p), "目录里没有可用文件"])
                continue
            f = inner[0]
        w, h, dur = probe(f)
        if min_side and min(w, h) and min(w, h) < min_side:
            bad.append([os.path.basename(f), "短边 %d < %d" % (min(w, h), min_side)])
        if dr and dur and not (dr[0] <= dur <= dr[1]):
            bad.append([os.path.basename(f), "时长 %.1fs 不在 %s" % (dur, dr)])
    detail["spec_ok"] = len(items[:sample]) - len(bad)
    if bad:
        detail["issues"].extend(["%s：%s" % (b[0], b[1]) for b in bad[:5]])
    return detail


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="p0", choices=["p0", "p1", "p2"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--sample", type=int, default=20)
    a = ap.parse_args(argv)
    try:
        spec = json.load(open(SPEC, encoding="utf-8-sig"))
    except Exception as e:
        print("读不到目标文件 %s：%s" % (SPEC, e))
        return 2

    rows, gaps, total_have, total_need = [], [], 0, 0
    for cls, s in (spec.get("classes") or {}).items():
        d = check_class(cls, s, a.tier, a.sample)
        d["class"] = cls
        d["name"] = s.get("name")
        rows.append(d)
        total_have += d["count"]
        total_need += int(s.get(a.tier) or 0)
        if d["count"] < int(s.get(a.tier) or 0):
            gaps.append("%s 差 %d（%d/%d）" % (s.get("name") or cls,
                                              int(s.get(a.tier) or 0) - d["count"],
                                              d["count"], int(s.get(a.tier) or 0)))

    ready = [r["class"] for r in rows if r["count"] >= r["target"] and r["target"]]
    out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "spec": "ASSET-LIBRARY-v1",
           "tier": a.tier, "classes": rows,
           "totals": {"have": total_have, "need": total_need,
                      "fill_pct": round(total_have / total_need * 100, 1) if total_need else None},
           "classes_ready": ready,
           "verdict": "PASS" if not gaps else ("EMPTY" if total_have == 0 else "GAPS"),
           "gaps": gaps,
           "note": "PASS 只代表数量达标；质量看 issues 与 SOP，特色只能人看人听"}
    out["status"] = out["verdict"]
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("资产库体检 tier=%s  合计 %d/%d（%.0f%%）  %s"
              % (a.tier, total_have, total_need,
                 (total_have / total_need * 100) if total_need else 0, out["verdict"]))
        for r in rows:
            mark = "OK " if r["count"] >= r["target"] and r["target"] else "缺 "
            print("  %s%-10s %4d/%-4d %s" % (mark, r["class"], r["count"], r["target"],
                                             ("授权 %d" % r["license_ok"]) if r["count"] else ""))
            for i in r["issues"][:3]:
                print("      - %s" % i)
        if gaps:
            print("缺口：%s" % "; ".join(gaps[:6]))
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))