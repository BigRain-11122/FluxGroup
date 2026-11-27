#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ship_ledger.py - 发布只有一条路：先清授权，再记一条，再等数据。

为什么：2026-11-02 全链条俯瞰发现两个洞——
  1) 48 包素材授权没签就上线 = 侵权雷（线上一条片子可能带雷）；
  2) 发完就断线，没有数据回填，选题全靠感觉。
本工具把"发布"变成可查的一条记录，并自动排两张数据卡（+24 小时、+7 天）。

一条内容只有一个"当前版"，其余进 history（解决 40 多个版本说不清谁最新）。

用法：
  python3 ship_ledger.py add --work mv0001 --version v718 --platform bilibili \
      --url https://... --license-cleared yes --note "封面用第3张"
  python3 ship_ledger.py data --work mv0001 --at 24h --views 1200 --finish 31 --comments 12
  python3 ship_ledger.py show [--work mv0001]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
SHIP = os.path.join(FLEET, "ship")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8-sig"))
    except Exception:
        return d


def save(work, obj):
    os.makedirs(SHIP, exist_ok=True)
    tmp = os.path.join(SHIP, ".%s.tmp" % work)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(SHIP, "%s.json" % work))


def append_backlog(cards):
    """积压只有一个写入口（2026-11-02）：交给 fleet_lane 加锁按 id 合并，
    不再自己 open(...,'a') 追加（并发追加会写出重复 id，状态被先写的那行吃掉）。"""
    if not cards:
        return
    import fleet_lane as _fl
    return _fl.merge_jsonl(BACKLOG, cards)


def cmd_add(a):
    if a.license_cleared.lower() not in ("yes", "y", "true", "cleared"):
        print("拒绝：授权未清算。48 包/素材授权没签，不许上线（旧素材一并替换后再发）。")
        return 3
    obj = jload(os.path.join(SHIP, "%s.json" % a.work), {}) or {}
    now = datetime.now()
    versions = obj.get("versions") or []
    versions.append({"version": a.version, "ts": now.isoformat(timespec="seconds"),
                     "platform": a.platform, "url": a.url,
                     "license_cleared": True, "note": a.note or ""})
    obj.update({"work": a.work, "current_version": a.version,
                "published_at": now.isoformat(timespec="seconds"),
                "platform": a.platform, "url": a.url, "versions": versions,
                "license_cleared": True})
    # 排两张数据卡：+24h、+7d
    d1, d7 = now + timedelta(hours=24), now + timedelta(days=7)
    cards = []
    for tag, due in (("24H", d1), ("7D", d7)):
        cid = "P-DATA-%s-%s" % (a.work.upper(), tag)
        cards.append({"id": cid, "title": "%s 发布后%s数据回填" % (a.work, tag),
                      "line": "bigstream-mv" if a.work.startswith("mv") else "recon",
                      "stage": "data", "state": "READY",
                      "due_at": due.isoformat(timespec="seconds"),
                      "cmd": "python3 Tools/fleet/ship_ledger.py data --work %s --at %s"
                             % (a.work, tag.lower()),
                      "deliverable": "cph4/fleet/ship/%s.json" % a.work,
                      "accept": ["写入该时段的播放/完播/评论数"],
                      "created_by": "ship_ledger:auto"})
        obj.setdefault("data_cards", []).append(cid)
    save(a.work, obj)
    append_backlog(cards)
    print("已记发布：%s %s → %s" % (a.work, a.version, a.platform))
    print("已排数据卡：%s（%s）、%s（%s）" % (cards[0]["id"], d1.strftime("%m-%d %H:%M"),
                                        cards[1]["id"], d7.strftime("%m-%d")))
    return 0


def cmd_data(a):
    obj = jload(os.path.join(SHIP, "%s.json" % a.work), {})
    if not obj:
        print("没有这条发布记录：%s" % a.work)
        return 3
    data = obj.setdefault("data", {})
    data[a.at] = {"ts": datetime.now().isoformat(timespec="seconds"),
                  "views": a.views, "finish": a.finish, "comments": a.comments}
    save(a.work, obj)
    print("已回填 %s %s：播放 %s / 完播 %s / 评论 %s" % (a.work, a.at, a.views, a.finish, a.comments))
    return 0


def cmd_show(a):
    if a.work:
        print(json.dumps(jload(os.path.join(SHIP, "%s.json" % a.work), {}) or {}, ensure_ascii=False, indent=1))
        return 0
    if not os.path.isdir(SHIP):
        print("还没有任何发布记录")
        return 0
    for n in sorted(os.listdir(SHIP)):
        if n.endswith(".json"):
            o = jload(os.path.join(SHIP, n), {}) or {}
            d = o.get("data") or {}
            print("%-14s 当前版 %-8s %-10s 播放24h=%s 完播24h=%s" % (
                o.get("work"), o.get("current_version"), o.get("platform"),
                (d.get("24h") or {}).get("views", "-"), (d.get("24h") or {}).get("finish", "-")))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    ad = sub.add_parser("add")
    ad.add_argument("--work", required=True)
    ad.add_argument("--version", required=True)
    ad.add_argument("--platform", required=True)
    ad.add_argument("--url", default="")
    ad.add_argument("--license-cleared", dest="license_cleared", required=True,
                    help="yes = 素材授权已清算；其它值一律拒绝")
    ad.add_argument("--note", default="")
    da = sub.add_parser("data")
    da.add_argument("--work", required=True)
    da.add_argument("--at", required=True, choices=["24h", "7d"])
    da.add_argument("--views", type=int, default=0)
    da.add_argument("--finish", type=int, default=0, help="完播率百分比")
    da.add_argument("--comments", type=int, default=0)
    sh = sub.add_parser("show")
    sh.add_argument("--work", default="")
    a = ap.parse_args(argv)
    if a.cmd == "add":
        return cmd_add(a)
    if a.cmd == "data":
        return cmd_data(a)
    return cmd_show(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))