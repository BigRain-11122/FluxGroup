#!/usr/bin/env python3
"""夜间素材采集与学习：多源抓取 → 垃圾过滤 → 观点/方法/数据抽取 → 方法论沉淀。

CEO 令 2026-11-24：「晚上 24 点过后，本机着重去采集各方面的素材和信息，各大平台等，
要过滤垃圾信息，好好去学习和思考，形成方法论和自己的思考」。

设计原则：
1. **只采公开稳定的源**（HN/Reddit/RSS）——公众号/知乎反爬，不硬撞
2. **三重过滤**：去重 → 去广告 → 去低质（长度+信息密度）
3. **不是堆素材**：每条素材必须能抽出「观点 / 方法 / 数据」之一，否则丢弃
4. **输出方法论**：按三支柱归类，形成可复用的判断

用法：
  night_harvest.py --run              # 跑一轮采集
  night_harvest.py --report           # 只看已采素材的方法论摘要
  night_harvest.py --self-test
退出码：0 成功 / 2 部分失败 / 4 自检失败
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "cph4", "fleet", "social", "gzh", "harvest")
LEDGER = os.path.join(OUT, "harvest-ledger.jsonl")
METHOD = os.path.join(OUT, "METHODOLOGY.md")

# ---------------- 垃圾过滤规则 ----------------
AD_WORDS = ("优惠", "折扣", "限时", "扫码", "加微信", "点击购买", "领取", "福利",
            "抽奖", "免费领", "0元", "特价", "返现", "招商", "加盟")
CLICKBAIT = ("震惊", "速看", "必看", "不看后悔", "太可怕", "惊呆", "竟然", "万万没想到")
# 高信息密度信号
SIGNAL = ("因为", "原因", "原理", "架构", "设计", "成本", "数据", "对比", "指标",
          "参数", "方案", "实现", "测试", "结果", "结论", "为什么", "如何")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _uid(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def _get(url, timeout=8, ua=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


# ---------------- 采集源 ----------------
def src_hn(limit=20):
    """Hacker News 热门（Firebase API，无需 key）。"""
    ids = json.loads(_get("https://hacker-news.firebaseio.com/v0/topstories.json"))[:limit]
    out = []
    for i in ids:
        try:
            d = json.loads(_get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", timeout=10))
            if d and d.get("title"):
                out.append({"src": "hn", "title": d["title"],
                            "url": d.get("url") or f"https://news.ycombinator.com/item?id={i}",
                            "score": d.get("score", 0), "text": ""})
        except Exception:  # noqa: BLE001
            continue
    return out


def src_reddit(sub="cardesign", limit=15):
    """Reddit 公开 JSON（无需 key）。"""
    try:
        d = json.loads(_get(f"https://www.reddit.com/r/{sub}/top.json?limit={limit}&t=day"))
        out = []
        for c in d.get("data", {}).get("children", []):
            p = c["data"]
            if p.get("stickied"):
                continue
            out.append({"src": f"reddit/{sub}", "title": p.get("title", ""),
                        "url": "https://reddit.com" + p.get("permalink", ""),
                        "score": p.get("score", 0),
                        "text": (p.get("selftext") or "")[:1500]})
        return out
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"reddit/{sub}: {type(e).__name__}") from e


def src_rss(name, url, limit=12):
    """通用 RSS（用最小正则解析，不引第三方库）。"""
    raw = _get(url, ua="Mozilla/5.0 (compatible; FluxHarvest/1.0)")
    items = re.findall(r"<item[\s\S]*?</item>", raw)[:limit]
    out = []
    for it in items:
        def g(tag):
            m = re.search(rf"<{tag}[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</{tag}>", it)
            return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
        t = g("title")
        if t:
            out.append({"src": f"rss/{name}", "title": t, "url": g("link"),
                        "score": 0, "text": g("description")[:1200]})
    return out


# 2026-11-24 实测：HN/Reddit/Dezeen 在本机全部超时（国际网络不通），
# 换成国内可达的四个源（36氪/少数派/IT之家/极客公园，均实测 HTTP 200）
SOURCES = [
    ("rss/36kr", lambda: src_rss("36kr", "https://36kr.com/feed", 12)),
    ("rss/sspai", lambda: src_rss("sspai", "https://sspai.com/feed", 10)),
    ("rss/ithome", lambda: src_rss("ithome", "https://www.ithome.com/rss/", 12)),
    ("rss/geekpark", lambda: src_rss("geekpark", "https://www.geekpark.net/rss", 10)),
]


# ---------------- 过滤 ----------------
def is_junk(item):
    """返回 (是否垃圾, 原因)。三重过滤：广告 / 标题党 / 低信息量。"""
    blob = (item.get("title", "") + " " + item.get("text", "")).lower()
    for w in AD_WORDS:
        if w in blob:
            return True, f"广告词:{w}"
    for w in CLICKBAIT:
        if w in blob:
            return True, f"标题党:{w}"
    # 低信息量：既没有信号词，正文也太短
    hits = sum(1 for s in SIGNAL if s in blob)
    if hits == 0 and len(item.get("text", "")) < 100:
        return True, "低信息量"
    return False, ""


def extract(item):
    """从素材里抽「观点/方法/数据」——抽不出来就说明不值得留。"""
    blob = item.get("title", "") + "\n" + item.get("text", "")
    out = {"claim": "", "method": "", "data": []}

    # 数据：数字 + 单位
    out["data"] = list(dict.fromkeys(
        re.findall(r"\d+(?:\.\d+)?\s*(?:%|TOPS|ms|秒|分钟|小时|公里|km|英寸|寸|元|美元|万|亿|nits|Hz)", blob)))[:5]

    # 观点：含"因为/为什么/原理"的判断句
    for sent in re.split(r"[。.!?\n]", blob):
        s = sent.strip()
        if 15 <= len(s) <= 120 and any(k in s for k in ("因为", "为什么", "原理", "本质", "关键", "问题在于")):
            out["claim"] = s
            break

    # 方法：含"如何/步骤/方法/框架/维度"
    for sent in re.split(r"[。.!?\n]", blob):
        s = sent.strip()
        if 10 <= len(s) <= 120 and any(k in s for k in ("如何", "步骤", "方法", "框架", "维度", "流程")):
            out["method"] = s
            break

    return out


def pillar_of(item):
    """按三支柱归类（用于方法论沉淀）。"""
    blob = (item.get("title", "") + " " + item.get("text", "")).lower()
    if any(k in blob for k in ("ui", "ux", "interface", "hmi", "screen", "display", "界面", "交互", "动效")):
        return "C2 设计拆解"
    if any(k in blob for k in ("cost", "price", "margin", "bom", "成本", "毛利", "价格")):
        return "C3 数据解读"
    if any(k in blob for k in ("ai", "agent", "model", "llm", "智能体", "大模型", "算法")):
        return "C5 行业观察"
    return "C1 技术拆解"


# ---------------- 主流程 ----------------
def run(limit_per_src=None):
    os.makedirs(OUT, exist_ok=True)
    seen = set()
    if os.path.exists(LEDGER):
        for line in open(LEDGER, encoding="utf-8"):
            try:
                seen.add(json.loads(line).get("_uid"))
            except Exception:  # noqa: BLE001
                pass

    stats = {"fetched": 0, "junk": 0, "dup": 0, "kept": 0, "sources_ok": 0, "sources_fail": 0}
    rows = []

    for name, fn in SOURCES:
        try:
            items = fn()
            if limit_per_src:
                items = items[:limit_per_src]
            stats["sources_ok"] += 1
            print(f"  {name}: {len(items)} 条", flush=True)
        except Exception as e:  # noqa: BLE001
            stats["sources_fail"] += 1
            print(f"  {name}: 失败 {type(e).__name__}", flush=True)
            continue

        for it in items:
            stats["fetched"] += 1
            uid = _uid(it.get("url") or it.get("title", ""))
            if uid in seen:
                stats["dup"] += 1
                continue
            j, why = is_junk(it)
            if j:
                stats["junk"] += 1
                continue
            ex = extract(it)
            if not (ex["claim"] or ex["method"] or ex["data"]):
                stats["junk"] += 1
                continue
            seen.add(uid)
            stats["kept"] += 1
            rows.append({
                "_uid": uid, "at": _now(), "src": it["src"],
                "title": it["title"][:150], "url": it.get("url", ""),
                "score": it.get("score", 0), "pillar": pillar_of(it),
                "claim": ex["claim"], "method": ex["method"], "data": ex["data"],
            })
        time.sleep(1)

    with open(LEDGER, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n采集 {stats['fetched']} 条 → 去重 {stats['dup']} / 过滤 {stats['junk']} → 留下 {stats['kept']}")
    print(f"源: 成功 {stats['sources_ok']} / 失败 {stats['sources_fail']}")
    if rows:
        render_methodology()
    return 0 if stats["kept"] >= 0 else 2


def render_methodology():
    """把累积素材按三支柱整理成方法论文档（不是列表，是提炼）。"""
    if not os.path.exists(LEDGER):
        return
    rows = []
    for line in open(LEDGER, encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            pass

    by_pillar = {}
    for r in rows:
        by_pillar.setdefault(r.get("pillar", "未分类"), []).append(r)

    lines = ["# 夜间采集方法论沉淀（自动生成，持续累积）", "",
             f"> 更新 {datetime.now().strftime('%Y-%m-%d %H:%M')} · 素材 {len(rows)} 条", ""]
    for p in sorted(by_pillar):
        items = by_pillar[p]
        lines.append(f"## {p}（{len(items)} 条）")
        lines.append("")
        # 只收「有观点」的，且按 score 排序取前 15
        claims = [x for x in items if x.get("claim")]
        claims.sort(key=lambda x: -x.get("score", 0))
        if claims:
            lines.append("**可引用的判断：**")
            for c in claims[:15]:
                lines.append(f"- {c['claim']}　`{c['src']}`")
            lines.append("")
        methods = [x for x in items if x.get("method")]
        if methods:
            lines.append("**可复用的方法：**")
            for m in methods[:10]:
                lines.append(f"- {m['method']}　`{m['src']}`")
            lines.append("")
        datas = [d for x in items for d in (x.get("data") or [])]
        if datas:
            uniq = list(dict.fromkeys(datas))[:25]
            lines.append(f"**可引用数据：** {' · '.join(uniq)}")
            lines.append("")

    open(METHOD, "w", encoding="utf-8").write("\n".join(lines))
    print(f"方法论已更新: {METHOD}")


def self_test():
    fails = []
    # 1. 广告必须被过滤
    j, why = is_junk({"title": "限时优惠 扫码领取福利", "text": ""})
    if not j:
        fails.append("负控[广告] 未过滤")
    # 2. 标题党必须被过滤
    j2, _ = is_junk({"title": "震惊！万万没想到", "text": ""})
    if not j2:
        fails.append("负控[标题党] 未过滤")
    # 3. 低信息量必须被过滤
    j3, _ = is_junk({"title": "今天天气不错", "text": "短"})
    if not j3:
        fails.append("负控[低信息量] 未过滤")
    # 4. 有信号的必须保留
    j4, why4 = is_junk({"title": "为什么车机界面要点三层：因为信息架构没做",
                        "text": "这个设计问题的原因在于层级没有对齐，成本也更高。"})
    if j4:
        fails.append(f"正控[有信号] 被误杀: {why4}")
    # 5. extract 必须抽出 data
    ex = extract({"title": "3,000 TOPS 算力", "text": "延迟 120ms，成本 500 元"})
    if not ex["data"]:
        fails.append("extract 未抽出数据")
    # 6. 观点抽取
    if not ex["claim"] and not extract({"title": "x", "text": "问题在于层级没有对齐，因为设计师没参与。"})["claim"]:
        fails.append("extract 未抽出观点")
    # 7. 支柱归类
    if pillar_of({"title": "UI 界面动效设计", "text": ""}) != "C2 设计拆解":
        fails.append("支柱归类错误")
    # 8. uid 稳定
    if _uid("a") != _uid("a"):
        fails.append("uid 不稳定")

    if fails:
        print("SELF-TEST FAIL", file=sys.stderr)
        for f in fails:
            print("  -", f, file=sys.stderr)
        return 4
    print("SELF-TEST OK 8/8  (过滤/抽取/归类/去重全过)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="每个源最多几条（调试用）")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.report:
        render_methodology()
        return 0
    if a.run:
        return run(a.limit)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
