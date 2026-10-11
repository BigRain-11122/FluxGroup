#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hot_scan.py - 短视频部 站0 热点扫描器（DailyHotApi 本地 :6688 聚合源）
用法: python hot_scan.py [--repo K:/Fluxgroup/FluxGroup] [--api http://127.0.0.1:6688] [--top 10]
产出: cph4/fleet/meme-daily-v1/topics/POOL-YYYYMMDD-HHMM.md（选题池·带评分两问占位·编辑部后判）
律=PIPELINE 站0：评分两问（反差可视觉化？嘴替空间？）+时效窗（24-72h 上升期）——机器只抓取与占位，两问由编辑部/AI 席后判
"""
import argparse, datetime, json, urllib.request, os, sys

BOARDS = ["weibo", "zhihu", "baidu", "douyin", "bilibili", "toutiao"]
BOARD_CN = {"weibo": "微博", "zhihu": "知乎", "baidu": "百度", "douyin": "抖音",
            "bilibili": "B站", "toutiao": "今日头条"}

def fetch(api, board, timeout=15):
    req = urllib.request.Request(api.rstrip("/") + "/" + board,
                                  headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    if isinstance(d, dict) and d.get("code") == 200:
        return d.get("data") or []
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="K:/Fluxgroup/FluxGroup")
    ap.add_argument("--api", default="http://127.0.0.1:6688")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    out_dir = os.path.join(a.repo, "cph4", "fleet", "meme-daily-v1", "topics")
    os.makedirs(out_dir, exist_ok=True)
    now = datetime.datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M")
    out = os.path.join(out_dir, "POOL-%s.md" % stamp)
    lines = ["# 选题池 %s（站0 扫描·机器抓取层）" % now.strftime("%Y-%m-%d %H:%M"), "",
             "> 评分两问（反差可视觉化？/嘴替空间？）与时效窗=编辑部后判位；本页只做抓取与占位。",
             "> 消费律=PIPELINE.md 站0-1：两问 ≥1 通过进 J-M15 梗链深研；车圈连载线另走固定宇宙（速成汽车）不占本池。", ""]
    ok_boards, total = 0, 0
    for b in BOARDS:
        try:
            items = fetch(a.api, b)[: a.top]
        except Exception as e:
            lines.append("## %s（%s）\n\n- [源故障] %s\n" % (BOARD_CN[b], b, e))
            continue
        if not items:
            lines.append("## %s（%s）\n\n- [空返回]\n" % (BOARD_CN[b], b))
            continue
        ok_boards += 1
        total += len(items)
        lines.append("## %s（%s）\n" % (BOARD_CN[b], b))
        lines.append("| # | 标题 | 热度 | 评分两问（后判） | 时效窗 |")
        lines.append("|---|------|------|------------------|--------|")
        for i, it in enumerate(items, 1):
            t = (it.get("title") or "").replace("|", "/").strip()
            h = it.get("hot") or "-"
            u = it.get("url") or ""
            lines.append("| %d | %s | %s | ①反差可视觉化? ②嘴替空间? | 待判 |" % (i, t[:60], h))
            if u:
                lines[len(lines) - 1] += " [%s](%s)" % ("链", u[:80])
        lines.append("")
    lines.append("---")
    lines.append("扫描源故障容忍：任一榜失败不阻塞其余榜。本轮 %d/%d 榜成功·%d 条入池。" % (ok_boards, len(BOARDS), total))
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("POOL WRITTEN %s boards=%d/%d items=%d" % (out, ok_boards, len(BOARDS), total))
    if ok_boards == 0:
        print("API DOWN: %s 全源失败——查 DailyHotApi 服（K:/Fluxgroup/.tools/DailyHotApi npm start）")
        sys.exit(1)

if __name__ == "__main__":
    main()
