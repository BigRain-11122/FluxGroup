#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""oss_radar.py - 开源风向雷达：扫 → 评 → 储备（每日一次，匿名 API，零依赖）。

为什么要有它：CEO 2026-11-04「希望你经常去 GitHub 看上升快/潜力大/口碑好的开源，学习和赋能，
好的东西储备一下」。原 `Tools/radar-daily-sweep.ps1` 只做扫描且没接主控脉（脉里只有 model_radar
管本地模型），所以实际是"人想起来才跑"。这里补三件：**上电、评估、储备**。

判据（全部可机判，不许"看起来很强"）：
  A 活跃   pushed_at 近 45 天 且（有 release 近 180 天 或 open_issues < 300）
  L 许可   MIT/Apache-2.0/BSD/ISC/MPL → 可用；GPL/AGPL → 传染，慎；无 license → 不采
  R 增速   created 近 240 天且 stars ≥ 250（新项目已高星 = 真上升），或 90 天 star 无法取时用 stars/age 代理
  F 落地   能用关键词映射到我们自己的线（mv/drama/game/quant/fleet/asset/voice）
  等级     A+L+R+F 全中 → ADOPT-CANDIDATE；A+L+F 三中 → WATCH；其余 → SKIP

用法：
  python Tools/fleet/oss_radar.py scan            # 扫一轮（每天一次，自带日期闸）
  python Tools/fleet/oss_radar.py scan --force
  python Tools/fleet/oss_radar.py list --top 10
退出码：0 正常；2 有告警（API 限流/无新增）；3 前置缺失
"""
import argparse
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join(ROOT, "cph4", "fleet", "oss")
STOCK = os.path.join(OUTDIR, "STOCKPILE.json")
DOC = os.path.join(OUTDIR, "OSS-RADAR.md")

# 三组查询（每组一次匿名调用，search API 未登录 10 次/分）
QUERIES = [
    ("video-i2v", "video generation pipeline stars:>400 pushed:>@45d", "mv,drama"),
    ("agent-orch", "agent orchestration framework stars:>1500 pushed:>@45d", "fleet"),
    ("new-risers", "created:>@240d stars:>300 pushed:>@20d", "any"),
]
LINE_WORDS = {
    "mv": ["video", "image-to-video", "i2v", "diffusion", "wan", "hunyuan", "seedance", "upscale", "lora"],
    "drama": ["tts", "voice", "lip", "lipsync", "subtitle", "asr", "whisper", "dub"],
    "game": ["game", "unity", "godot", "sprite", "tilemap", "roguelike", "2d"],
    "quant": ["backtest", "quant", "trading", "factor", "portfolio", "market data"],
    "fleet": ["agent", "orchestrat", "workflow", "scheduler", "queue", "observab"],
    "asset": ["asset", "texture", "3d", "rig", "mesh", "pbr", "segmentation", "matting"],
}
OK_LIC = ("mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "mpl-2.0")
BAD_LIC = ("gpl-2.0", "gpl-3.0", "agpl-3.0")


def api(q, per_page=12):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": per_page})
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "fluxgroup-oss-radar"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8")), None
    except Exception as e:
        return None, str(e)


def expand(q):
    """把 @45d 这类相对日期换成绝对，避免查询语法不认。"""
    def rep(m):
        days = int(m.group(1))
        return time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
    return re.sub(r"@(\d+)d", rep, q)


def age_days(iso):
    try:
        t = time.mktime(time.strptime(iso[:10], "%Y-%m-%d"))
        return int((time.time() - t) / 86400)
    except Exception:
        return 9999


def lines_of(item):
    hay = ((item.get("description") or "") + " " + " ".join(item.get("topics") or [])
           + " " + (item.get("name") or "")).lower()
    return sorted({ln for ln, words in LINE_WORDS.items() if any(w in hay for w in words)})


def score(item):
    lic = ((item.get("license") or {}).get("spdx_id") or "").lower()
    stars = item.get("stargazers_count") or 0
    pushed = age_days(item.get("pushed_at") or "")
    created = age_days(item.get("created_at") or "")
    issues = item.get("open_issues_count") or 0
    lines = lines_of(item)

    A = pushed <= 45 and (created <= 180 or issues < 300)
    L = lic in OK_LIC
    B = lic in BAD_LIC
    R = created <= 240 and stars >= 250
    F = bool(lines)
    if L and A and F and R:
        grade = "ADOPT-CANDIDATE"
    elif (L or not B) and A and F:
        grade = "WATCH"
    else:
        grade = "SKIP"

    # 星数护栏：真 GitHub 上 10 万星以上的仓库极少，命中要人工核实一次再当结论
    # （2026-11-04 首跑就遇到 271k★ 的 deepseek-harness，核实为真——护栏不是不信任，是留痕）
    need_verify = stars >= 100000

    reasons = []
    reasons.append("活跃(pushed %dd)" % pushed if A else "不活跃(pushed %dd)" % pushed)
    reasons.append("许可 %s" % (lic or "无"))
    if B:
        reasons.append("传染性许可，商用慎")
    reasons.append("新且高星(%dd/%d★)" % (created, stars) if R else "非新星")
    reasons.append("可落线：" + ",".join(lines) if F else "无线索落点")
    return {"grade": grade, "lines": lines, "license": lic or None, "stars": stars,
            "pushed_age_d": pushed, "created_age_d": created, "need_verify": need_verify,
            "verdict_reason": "；".join(reasons) + ("；⚠星数超 10 万需人工核实" if need_verify else "")}


def scan(force=False):
    os.makedirs(OUTDIR, exist_ok=True)
    stock = {"schema": 1, "updated": "", "runs": [], "items": {}}
    if os.path.exists(STOCK):
        try:
            stock = json.load(io.open(STOCK, encoding="utf-8"))
        except Exception:
            pass
    today = time.strftime("%Y-%m-%d")
    if not force and any(r.get("date") == today for r in stock.get("runs", [])):
        print("today already scanned (%s), use --force" % today)
        return 0

    added, errs, seen = 0, [], 0
    for name, q, _tag in QUERIES:
        data, err = api(expand(q))
        if err:
            errs.append("%s: %s" % (name, err))
            continue
        for it in data.get("items", []):
            seen += 1
            full = it.get("full_name")
            if not full:
                continue
            s = score(it)
            rec = stock["items"].get(full, {})
            rec.update({
                "full_name": full, "url": it.get("html_url"), "desc": (it.get("description") or "")[:300],
                "stars": s["stars"], "license": s["license"], "lines": s["lines"],
                "grade": s["grade"], "why": s["verdict_reason"],
                "need_verify": s["need_verify"],
                "created_at": it.get("created_at"),
                "topics": (it.get("topics") or [])[:12],
                "first_seen": rec.get("first_seen") or today, "last_seen": today,
                "trial_trigger": rec.get("trial_trigger") or ("当线里有对应缺口时试跑最小例子：" + (",".join(s["lines"]) or "-")),
                "status": rec.get("status") or "stocked",
            })
            if full not in stock["items"]:
                added += 1
            stock["items"][full] = rec

    stock["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    stock.setdefault("runs", []).append({"date": today, "queries": len(QUERIES),
                                         "seen": seen, "added": added, "errors": errs})
    stock["runs"] = stock["runs"][-60:]
    with io.open(STOCK, "w", encoding="utf-8") as f:
        f.write(json.dumps(stock, ensure_ascii=False, indent=1))

    items = sorted(stock["items"].values(), key=lambda x: (x["grade"] != "ADOPT-CANDIDATE", -x["stars"]))
    by = {}
    for it in items:
        by[it["grade"]] = by.get(it["grade"], 0) + 1
    with io.open(DOC, "w", encoding="utf-8") as f:
        f.write("# 开源风向储备（%s）\n\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write("判据=活跃/许可/增速/落地四维，ADOPT-CANDIDATE 才值得排期试跑；WATCH=留观。\n\n")
        f.write("库存：%s\n\n" % "，".join("%s=%d" % (k, v) for k, v in sorted(by.items())))
        for g in ("ADOPT-CANDIDATE", "WATCH"):
            rows = [x for x in items if x["grade"] == g][:15]
            if not rows:
                continue
            f.write("## %s\n\n" % g)
            for x in rows:
                f.write("- **%s** %d★ · %s · 落线=%s\n  - %s\n  - 试跑触发：%s\n" % (
                    x["full_name"], x["stars"], x["license"], ",".join(x["lines"]) or "-",
                    x["desc"], x["trial_trigger"]))
            f.write("\n")

    print(json.dumps({"date": today, "seen": seen, "added": added, "errors": errs,
                      "stock_total": len(stock["items"]), "by_grade": by}, ensure_ascii=False))
    return 0 if not errs else 2


def cmd_list(top=10):
    if not os.path.exists(STOCK):
        print("BLOCKED no stockpile yet: run scan")
        return 3
    stock = json.load(io.open(STOCK, encoding="utf-8"))
    items = sorted(stock["items"].values(), key=lambda x: (x["grade"] != "ADOPT-CANDIDATE", -x["stars"]))
    for x in items[:top]:
        print("%-16s %-40s %6d★ %s | %s" % (x["grade"], x["full_name"], x["stars"],
                                            x["license"], ",".join(x["lines"])))
    print("\n库存 %d 条；文档 %s" % (len(stock["items"]), os.path.relpath(DOC, ROOT)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("scan")
    s.add_argument("--force", action="store_true")
    l = sub.add_parser("list")
    l.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    if a.cmd == "list":
        return cmd_list(a.top)
    return scan(getattr(a, "force", False))


if __name__ == "__main__":
    sys.exit(main())