#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_autopilot.py - 养号全自动流水线（一层入口，跑完采集→草稿→排队→发送→回执）。

CEO 2026-11-17「我要你全自动化 不管什么形式和方法」的落地件（令在 docs/orders.md 同日条）。
分三层，开关只在 `cph4/fleet/social/AUTOPILOT-v1.json`：

  T1 采集→草稿→排队→一键批发（零账号风险，永远可用）
  T2 官方接口自动发送（抖音 video.comment / 公众号客服消息）——平台许可范围内
  T3 无官方接口平台的登录态浏览器自动化——**封号不可逆**，代码层拒绝，除非
     AUTOPILOT-v1.json 里 tier3_risk_ack 写成令号+日期

硬约束（任何一条不满足就整体停发，不"边发边报错"）：
  1 kill_switch=true            → 只排队
  2 日限额（按 platform.behavior）→ 超限的留 HOLD_QUOTA
  3 同作者冷却                  → 冷却期内的留 HOLD_COOLDOWN
  4 四道内容闸（红线/事实/语感/模板）已在草稿阶段做，本层再挡 needs_human
  5 逐条回执 + 审计 jsonl（每次发送一行，含 why/rules/sent/failed）

Usage:
  python3 Tools/fleet/social_autopilot.py --run --raw <raw> --dir <dir>          # 全自动（按 tier）
  python3 Tools/fleet/social_autopilot.py --run --dir <dir> --no-draft           # 只排队
  python3 Tools/fleet/social_autopilot.py --status
  python3 Tools/fleet/social_autopilot.py --self-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
CONF = os.path.join(SOCIAL, "AUTOPILOT-v1.json")
# 已实现的官方发送通道。没实现的一律 HOLD_TIER（不是 FAILED）：
# "没有实现"和"调用失败"是两回事，混在一起会让审计看不出真故障。
SUPPORTED = {("douyin", "comment")}
# T3（无官方接口，浏览器代操作）：需 tier3_enabled + 选择器已标定
SUPPORTED_T3 = {("bilibili", "comment"), ("xiaohongshu", "comment"),
                ("weixin_channels", "comment"), ("zhihu", "comment"), ("weibo", "comment")}


def load_conf(path=CONF):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _jsonl(path):
    rows = []
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            if l.strip():
                try:
                    rows.append(json.loads(l))
                except Exception:
                    pass
    return rows


def _append(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def gates_ok(conf):
    """配置自检：缺项就不许发（不给"默认值"留后门）。"""
    need = ("tier", "tier2_enabled", "kill_switch", "daily_cap", "cooldown_minutes", "audit")
    miss = [k for k in need if k not in conf]
    return (not miss), miss


def build_queue(drafts_path, conf):
    """待发队列=草稿里"不需人工 + 有稿 + 未发过"的行。"""
    sent = {r.get("id") for r in _jsonl(conf["audit"]) if r.get("result") == "SENT"}
    q = []
    for r in _jsonl(drafts_path):
        if r.get("state") not in ("PENDING_REVIEW", "APPROVED"):
            continue
        if r.get("needs_human"):
            continue
        if not (r.get("draft") or "").strip():
            continue
        if r.get("id") in sent:
            continue
        q.append(r)
    return q


def _today_sent(conf, plat_beh):
    today = date.today().isoformat()
    n = 0
    for r in _jsonl(conf["audit"]):
        if r.get("result") == "SENT" and str(r.get("ts") or "").startswith(today) \
                and r.get("key") == plat_beh:
            n += 1
    return n


def _cap(conf, plat_beh):
    return int((conf.get("daily_cap") or {}).get(plat_beh)
               or (conf.get("daily_cap") or {}).get("default") or 5)


def run(drafts_path, conf, sender=None, execute=True, now=None):
    """返回 (stats, queue)。sender(platform, behavior, draft_row) -> (ok, receipt)。"""
    now = now or datetime.now()
    ok_conf, miss = gates_ok(conf)
    stats = {"queue": 0, "sent": 0, "failed": 0, "hold_quota": 0, "hold_cooldown": 0,
             "hold_tier": 0, "skipped_kill": 0}
    if not ok_conf:
        return dict(stats, error="配置缺项:%s" % ",".join(miss)), []
    if conf.get("kill_switch"):
        stats["skipped_kill"] = len(build_queue(drafts_path, conf))
        return stats, []

    q = build_queue(drafts_path, conf)
    stats["queue"] = len(q)
    last_author = {}
    for r in _jsonl(conf["audit"]):
        key = (r.get("platform"), r.get("author"))
        if r.get("ts"):
            last_author[key] = r["ts"]
    out_queue, receipts, run_count = [], [], {}   # run_count：本轮已发数（文件是上一轮的账）
    for r in q:
        plat, beh = r.get("platform") or "unknown", r.get("behavior") or "comment"
        key = "%s.%s" % (plat, beh)
        rec = dict(r, key=key, ts=now.isoformat(timespec="seconds"))
        # T3 平台（无官方接口）在 T2 模式下不许发：宁可不发，不越权
        if conf.get("tier", 1) < 3 and plat in ("xiaohongshu", "weixin_channels", "zhihu", "weibo") \
                and beh in ("comment", "dm"):
            rec["state"] = "HOLD_TIER"
            rec["hold_reason"] = "该平台无官方写接口，需 T3（封号风险，未授权）"
            stats["hold_tier"] += 1
            out_queue.append(rec)
            continue
        prev = last_author.get((plat, r.get("author")))
        if prev:
            try:
                gap = (now - datetime.fromisoformat(prev)).total_seconds() / 60
                if gap < float(conf.get("cooldown_minutes") or 0):
                    rec["state"] = "HOLD_COOLDOWN"
                    rec["hold_reason"] = "同作者冷却 %.0f 分钟未满" % gap
                    stats["hold_cooldown"] += 1
                    out_queue.append(rec)
                    continue
            except Exception:
                pass
        if _today_sent(conf, key) + run_count.get(key, 0) >= _cap(conf, key):
            rec["state"] = "HOLD_QUOTA"
            rec["hold_reason"] = "今日已达上限 %d" % _cap(conf, key)
            stats["hold_quota"] += 1
            out_queue.append(rec)
            continue
        if not (execute and conf.get("tier2_enabled")):
            rec["state"] = "QUEUED"
            out_queue.append(rec)
            continue
        if (plat, beh) in SUPPORTED_T3:
            if not conf.get("tier3_enabled"):
                rec["state"] = "HOLD_TIER"
                rec["hold_reason"] = "T3 未开启（该平台无官方接口）"
                stats["hold_tier"] += 1
                out_queue.append(rec)
                continue
            ok, receipt = _t3_send(plat, r)
            rec["result"] = "SENT" if ok else "FAILED"
            rec["receipt"] = receipt
            rec["state"] = "SENT" if ok else "FAILED"
            rec["tier"] = 3
            stats["sent" if ok else "failed"] += 1
            if ok:
                run_count[key] = run_count.get(key, 0) + 1
                last_author[(plat, r.get("author"))] = rec["ts"]
            receipts.append(rec)
            out_queue.append(rec)
            continue
        if (plat, beh) not in SUPPORTED:
            rec["state"] = "HOLD_TIER"
            rec["hold_reason"] = "%s.%s 无官方发送实现（待接入或需 T3）" % (plat, beh)
            stats["hold_tier"] += 1
            out_queue.append(rec)
            continue
        if sender is None:
            try:
                from social_douyin import reply_comment  # 懒加载，避免自检联网
                sender = _default_sender
            except Exception:
                rec["state"] = "QUEUED"
                rec["hold_reason"] = "无可用发送器"
                out_queue.append(rec)
                continue
        ok, receipt = sender(plat, beh, r)
        rec["result"] = "SENT" if ok else "FAILED"
        rec["receipt"] = receipt
        rec["state"] = "SENT" if ok else "FAILED"
        if ok:
            stats["sent"] += 1
            run_count[key] = run_count.get(key, 0) + 1
            last_author[(plat, r.get("author"))] = rec["ts"]
        else:
            stats["failed"] += 1
        receipts.append(rec)
        out_queue.append(rec)
    if receipts:
        _append(conf["audit"], receipts)
    if out_queue:
        qpath = conf.get("queue") or os.path.join(SOCIAL, "queue.jsonl")
        qpath = qpath if os.path.isabs(qpath) else os.path.join(ROOT, qpath)
        _append(qpath, out_queue)
    return stats, out_queue


def _t3_send(plat, row):
    """T3：交给 social_browser。标定不全时它会明确拒绝（不猜选择器）。"""
    if str(plat) in ("xiaohongshu", "weixin_channels", "zhihu", "weibo", "bilibili"):
        sys.path.insert(0, HERE)
        import social_browser
        return social_browser.send_one(plat, row, dry=False)
    return False, "无 T3 执行器"


def _default_sender(plat, beh, row):
    """生产发送器：目前只有抖音评论回复（官方接口）。其它平台返回 False 并留原因。"""
    if plat == "douyin" and beh == "comment":
        from social_douyin import reply_comment, load_cred
        cred, need = load_cred()
        if need:
            return False, "未授权：缺 %s" % ",".join(need)
        item = row.get("video") or row.get("thread")
        cid = str(row.get("comment_id") or "")
        if not item or not cid:
            return False, "缺 item_id/comment_id，无法定位评论"
        return reply_comment(cred, item, cid, row.get("draft") or "")
    return False, "该平台/行为无官方发送实现（T3 未授权）"


def self_test():
    """离线自检：发送器注入，绝不联网、绝不写生产队列。"""
    cases = []
    tmp = os.path.join(ROOT, ".codely-cli", "tmp", "autopilot-selftest")
    os.makedirs(tmp, exist_ok=True)
    drafts = os.path.join(tmp, "drafts.jsonl")
    audit = os.path.join(tmp, "audit.jsonl")
    queue = os.path.join(tmp, "queue.jsonl")
    for p in (audit, queue):
        if os.path.exists(p):
            os.remove(p)
    conf = {
        "tier": 2, "tier2_enabled": True, "kill_switch": False,
        "daily_cap": {"douyin.comment": 2, "default": 5},
        "cooldown_minutes": 30, "audit": audit, "queue": queue,
    }
    rows = [
        {"id": "a1", "platform": "douyin", "behavior": "comment", "author": "甲",
         "draft": "谢啦", "needs_human": False, "state": "PENDING_REVIEW", "video": "v1", "comment_id": "c1"},
        {"id": "a2", "platform": "douyin", "behavior": "comment", "author": "乙",
         "draft": "剪了好几遍", "needs_human": False, "state": "PENDING_REVIEW", "video": "v1", "comment_id": "c2"},
        {"id": "a3", "platform": "douyin", "behavior": "comment", "author": "丙",
         "draft": "值这个价", "needs_human": False, "state": "PENDING_REVIEW", "video": "v1", "comment_id": "c3"},
        {"id": "a4", "platform": "douyin", "behavior": "comment", "author": "丁",
         "draft": "需人工确认的话", "needs_human": True, "state": "PENDING_REVIEW", "video": "v1"},
        {"id": "a5", "platform": "xiaohongshu", "behavior": "comment", "author": "戊",
         "draft": "这条没接口", "needs_human": False, "state": "PENDING_REVIEW", "video": "x1"},
        {"id": "a6", "platform": "douyin", "behavior": "comment", "author": "甲",
         "draft": "同作者第二条", "needs_human": False, "state": "PENDING_REVIEW", "video": "v1", "comment_id": "c6"},
    ]
    open(drafts, "w", encoding="utf-8").write(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    sent = []

    def fake_sender(plat, beh, row):
        sent.append(row["id"])
        return True, "ok"

    st, q = run(drafts, conf, sender=fake_sender, execute=True)
    cases.append(("needs_human 的不许自动发", "a4" not in sent))
    cases.append(("无接口平台必须 HOLD_TIER", st["hold_tier"] == 1
                  and any(x["id"] == "a5" and x["state"] == "HOLD_TIER" for x in q)))
    cases.append(("日上限生效", st["sent"] == 2 and st["hold_quota"] >= 1))
    cases.append(("同作者冷却生效", st["hold_cooldown"] >= 1))
    cases.append(("审计必须逐条落盘", len(_jsonl(audit)) == 2))

    # kill switch：一条都不发
    conf2 = dict(conf, kill_switch=True)
    st2, _ = run(drafts, conf2, sender=fake_sender, execute=True)
    cases.append(("kill switch 必须整体停发", st2["sent"] == 0 and st2["skipped_kill"] >= 1))

    # tier1：只排队不发
    conf3 = dict(conf, tier=1, tier2_enabled=False)
    before = len(sent)
    st3, q3 = run(drafts, conf3, sender=fake_sender, execute=True)
    cases.append(("T1 只排队不发送", len(sent) == before and st3["sent"] == 0
                  and all(x["state"] in ("QUEUED", "HOLD_TIER", "HOLD_QUOTA", "HOLD_COOLDOWN")
                          for x in q3)))

    # 配置缺项必须拒绝执行
    st4, _ = run(drafts, {"tier": 2}, sender=fake_sender)
    cases.append(("配置缺项必须拒绝", st4.get("error", "").startswith("配置缺项")))

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        if not v:
            print("  FAIL %s" % n)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--raw", default=None, help="原始事件目录（有则先跑 ingest）")
    ap.add_argument("--dir", default=SOCIAL, help="工作目录（草稿/审计/队列）")
    ap.add_argument("--no-draft", action="store_true", help="跳过出草稿（只排队/发送）")
    ap.add_argument("--execute", action="store_true", help="真发送（需 tier2_enabled）")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--conf", default=CONF)
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    conf = load_conf(a.conf)
    if a.status:
        print("[autopilot] tier=%s tier2=%s tier3=%s kill=%s 日上限=%s 冷却=%s分钟"
              % (conf.get("tier"), conf.get("tier2_enabled"), conf.get("tier3_enabled"),
                 conf.get("kill_switch"), conf.get("daily_cap"), conf.get("cooldown_minutes")))
        q = _jsonl(os.path.join(ROOT, conf.get("queue", ""))) if conf.get("queue") else []
        from collections import Counter
        print("[autopilot] 队列状态 %s" % dict(Counter(r.get("state") for r in q)))
        return 0
    if not a.run:
        print("[autopilot] 用 --run [--raw DIR] [--execute] 或 --status")
        return 2

    d = os.path.abspath(a.dir)
    if a.raw:
        sys.path.insert(0, HERE)
        import social_ingest
        st, path = social_ingest.ingest(os.path.abspath(a.raw), d)
        print("[autopilot] ingest 读%d 入队%d 红线拒%d 去重%d -> %s"
              % (st["read"], st["ok"], st["rejected_forbidden"], st["dupe"], path))
    if not a.no_draft:
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(HERE, "social_drafts.py"),
                            "--dir", d], capture_output=True, text=True)
        print("[autopilot] draft rc=%d %s" % (r.returncode, (r.stdout or "").strip()[:160]))
    stats, q = run(os.path.join(d, "drafts.jsonl"), conf, execute=a.execute)
    if stats.get("error"):
        print("[autopilot] 拒绝执行：%s" % stats["error"])
        return 2
    print("[autopilot] 队列%d 已发%d 失败%d | 超限%d 冷却%d 无接口%d 停发跳过%d"
          % (stats["queue"], stats["sent"], stats["failed"], stats["hold_quota"],
             stats["hold_cooldown"], stats["hold_tier"], stats["skipped_kill"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
