#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""集团雷达：按科学频率去公开源扫"最新、最酷、最能用"的东西，产出研学候选。

CEO 2026-11-03：实验室与各子公司研究部门要增设雷达与调研，高频但合理地搜网，
研判落地、科学测试、合理应用。

三条设计约束（都是踩过的）：
  1. **频率写在配置里**，不靠人记得：每个源有 min_interval_h，未到点直接跳过并说明
     （高频≠每轮扫；每天扫一次 GitHub、每周扫一次论文，才是"合理"）
  2. **源挂了就记 BLOCKED**，不编候选：本机实测 HF 直连 000、arXiv 需 https，
     这类必须如实写进 source_status，否则雷达会变成"看起来在扫"
  3. **候选必须能被研判**：每条给 相关性打分 + 能落到哪条线 + 最低验证成本（cmd 或证据），
     否则进不了 PROPOSALS——"看着厉害"不是采纳理由

产物：
  cph4/fleet/radar/SEEN.json          已见过的条目（去重，永久）
  cph4/fleet/radar/RADAR-<date>.json  本次扫结果（含 source_status）
  cph4/fleet/radar/RADAR.md           人读一页（前 N 条 + 每条一句话为什么可能有用）

用法：
  python3 Tools/fleet/radar.py             # 按频率跑（未到点的源跳过）
  python3 Tools/fleet/radar.py --force     # 忽略频率（人工复核用）
  python3 Tools/fleet/radar.py --source github
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RD = os.path.join(ROOT, "cph4", "fleet", "radar")
SEEN = os.path.join(RD, "SEEN.json")

# 与缺口对齐的关键词权重（改这里就等于改"什么算有用"）
WEIGHTS = [
    ("lora", 6), ("character consistency", 8), ("identity", 6), ("face", 4),
    ("tts", 7), ("voice clone", 7), ("speech synthesis", 6), ("asr", 4), ("whisper", 3),
    ("image-to-video", 7), ("i2v", 7), ("video generation", 6), ("keyframe", 5),
    ("comfyui", 8), ("diffusion", 4), ("sdxl", 5), ("controlnet", 4),
    ("agent", 3), ("orchestration", 3), ("workflow", 2), ("mcp", 3),
    ("backtest", 5), ("quant", 4), ("factor", 4),
    ("2d", 4), ("pixel", 3), ("unity", 3), ("game", 3),
    ("dataset", 3), ("caption", 3), ("segmentation", 4), ("matting", 5),
]

SOURCES = {
    "github": {
        "interval_h": 20, "timeout": 20,
        "url": "https://api.github.com/search/repositories?q=created:>{since}+stars:>{stars}"
               "&sort=stars&order=desc&per_page={n}",
        "stars": 60, "n": 20, "days": 7,
    },
    "arxiv": {
        "interval_h": 150, "timeout": 25,
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.CV+OR+cat:cs.CL"
               "&sortBy=submittedDate&sortOrder=descending&max_results={n}",
        "n": 15,
    },
}


def load(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def get(url, timeout):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "fluxgroup-radar/1.0",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# 与我们无关的领域词，命中即扣分（否则雷达会被医学/遥感论文占满——
# 2026-11-03 首跑实测：foot ulcer segmentation 冲到第一，属纯噪声）
NEGATIVE = [("ulcer", 12), ("clinical", 8), ("patient", 8), ("medical", 6), ("tumor", 8),
            ("remote sensing", 8), ("satellite", 8), ("seismic", 6), ("traffic flow", 6),
            ("stock price prediction", 6), ("recommendation system", 5)]



SEATS = os.path.join(RD, "SEATS-v1.json")


def assign_seat(c):
    """按命中词把候选分给研究席；分不到就归实验室（跨线兜底）。"""
    try:
        cfg = json.load(open(SEATS, encoding="utf-8")).get("seats") or {}
    except Exception:
        return "labs"
    text = ((c.get("title") or "") + " " + (c.get("desc") or "")).lower()
    best, best_n = "labs", 0
    for sid, sdef in cfg.items():
        n = sum(1 for k in (sdef.get("keywords") or []) if k in text)
        if n > best_n:
            best, best_n = sid, n
    return best

def score(text):
    t = (text or "").lower()
    s, hits = 0, []
    for k, w in WEIGHTS:
        if k in t:
            s += w
            hits.append(k)
    for k, w in NEGATIVE:
        if k in t:
            s -= w
            hits.append("-" + k)
    return s, hits


def scan_github(cfg, force):
    since = time.strftime("%Y-%m-%d", time.localtime(time.time() - cfg["days"] * 86400))
    url = cfg["url"].format(since=since, stars=cfg["stars"], n=cfg["n"])
    raw = json.loads(get(url, cfg["timeout"]))
    out = []
    for it in raw.get("items") or []:
        desc = "%s %s" % (it.get("full_name"), it.get("description") or "")
        s, hits = score(desc)
        out.append({"source": "github", "id": it.get("full_name"), "url": it.get("html_url"),
                    "title": it.get("full_name"), "desc": (it.get("description") or "")[:200],
                    "stars": it.get("stargazers_count"), "license": (it.get("license") or {}).get("spdx_id"),
                    "lang": it.get("language"), "score": s, "hits": hits,
                    "created": it.get("created_at")})
    return out


def scan_arxiv(cfg, force):
    xml = get(cfg["url"].format(n=cfg["n"]), cfg["timeout"])
    out = []
    for m in re.finditer(r"<entry>([\s\S]*?)</entry>", xml):
        e = m.group(1)
        t = re.search(r"<title>([\s\S]*?)</title>", e)
        i = re.search(r"<id>([\s\S]*?)</id>", e)
        sm = re.search(r"<summary>([\s\S]*?)</summary>", e)
        title = re.sub(r"\s+", " ", (t.group(1) if t else "?")).strip()
        summ = re.sub(r"\s+", " ", (sm.group(1) if sm else "")).strip()
        s, hits = score(title + " " + summ)
        out.append({"source": "arxiv", "id": (i.group(1) if i else title)[:120],
                    "url": (i.group(1) if i else ""), "title": title[:180], "desc": summ[:240],
                    "score": s, "hits": hits})
    return out


SCANNERS = {"github": scan_github, "arxiv": scan_arxiv}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--source", default="")
    ap.add_argument("--min-score", type=int, default=7)
    a = ap.parse_args(argv)
    os.makedirs(RD, exist_ok=True)
    seen = load(SEEN, {}) or {}
    status, fresh = {}, []
    for name, cfg in SOURCES.items():
        if a.source and name != a.source:
            continue
        last = float(seen.get("_last", {}).get(name) or 0)
        age_h = (time.time() - last) / 3600.0
        if not a.force and age_h < cfg["interval_h"]:
            status[name] = "SKIP(next in %.1fh)" % (cfg["interval_h"] - age_h)
            continue
        try:
            rows = SCANNERS[name](cfg, a.force)
            status[name] = "OK(%d)" % len(rows)
            seen.setdefault("_last", {})[name] = time.time()
            fresh.extend(rows)
        except Exception as e:
            status[name] = "BLOCKED(%s)" % str(e)[:80]
    # 去重：见过的不再进候选，但分数与命中保留在 SEEN 里便于复盘
    new = []
    for r in fresh:
        k = r.get("id") or r.get("title")
        if k in seen:
            continue
        seen[k] = {"first_seen": time.strftime("%Y-%m-%d"), "score": r.get("score")}
        new.append(r)
    ranked = sorted(new, key=lambda x: -x["score"])
    picked = [x for x in ranked if x["score"] >= a.min_score][:12]
    for c in picked:
        c["seat"] = assign_seat(c)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "source_status": status,
           "scanned": len(fresh), "new": len(new), "picked": len(picked),
           "candidates": picked}
    day = time.strftime("%Y%m%d")
    json.dump(rec, open(os.path.join(RD, "RADAR-%s.json" % day), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(seen, open(SEEN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# 雷达（%s）" % rec["ts"], "",
          "源状态：%s" % " · ".join("%s=%s" % (k, v) for k, v in status.items()), "",
          "本周新见 %d 条，够格进研判 %d 条（阈值 score≥%d）" % (len(new), len(picked), a.min_score), ""]
    for i, c in enumerate(picked, 1):
        md.append("%d. **[%d] %s**（归席：%s）  ——  命中：%s" % (
            i, c["score"], c["title"], c.get("seat", "labs"), ",".join(c["hits"]) or "-"))
        md.append("   - %s" % (c.get("desc") or "")[:160])
        md.append("   - %s" % (c.get("url") or ""))
    open(os.path.join(RD, "RADAR.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("radar: %s" % " · ".join("%s=%s" % (k, v) for k, v in status.items()))
    print("new=%d picked=%d -> cph4/fleet/radar/RADAR.md" % (len(new), len(picked)))
    for c in picked[:6]:
        print("  [%d] %-42s %s" % (c["score"], c["title"][:42], ",".join(c["hits"])[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))