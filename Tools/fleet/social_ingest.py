#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_ingest.py - 全平台/全行为统一入口：把各渠道原始事件归一成一个队列。

Why（2026-11-17 CEO 令「养号要包括所有的主流平台各个行为」）：草稿工具只认一种
inbox，平台一多就会各写一套；而真正决定"能不能做"的不是模型，是**平台×行为矩阵**
（官方接口 / 后台导出 / 只能人工 / 红线）。所以先把矩阵当判据落成机器件
（PLATFORM-MATRIX-v1.json），再由本工具做四件事：

  1 校验：平台/行为不在矩阵里、或命中 forbidden → 拒绝并计数（不静默丢）
  2 脱敏：手机号/微信号/邮箱/身份证一律打码后才进队列（抖音 2026-07-06 起私信
    留资号码强制脱敏，我们这边更不该存原文）
  3 去重：同平台同行为同 id，或同平台同作者同内容 → 只留一条
  4 冷却：同作者短时间多条的，标 HOLD_COOLDOWN 留痕（人工决定回哪条）

Input  : --raw <dir> 下的 <platform>.<behavior>.jsonl，每行 {id,author,text,thread?,ts?,meta?}
Output : <dir>/inbox.jsonl（统一 schema，可直接喂 social_drafts.py --dir <dir>）

Usage:
  python3 Tools/fleet/social_ingest.py --raw <dir> --out <dir>
  python3 Tools/fleet/social_ingest.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MATRIX = os.path.join(ROOT, "cph4", "fleet", "social", "PLATFORM-MATRIX-v1.json")

# 行为 -> 草稿通道（social_drafts 的 face）。新增平台不用改草稿工具。
BEHAVIOR_FACE = {
    "comment": "comment",
    "danmaku": "danmaku",
    "dm": "dm",
    "gift_thanks": "dm",
    "group_msg": "dm",
    "crisis": "comment",
    "topic": None,       # 交给 social_topics
    "data": None,        # 只做看板
    "publish": None,     # 决定权在 CEO
}

PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
WECHAT = re.compile(r"(?:微信|weixin|vx|v信|加V)\s*[:：]?\s*([A-Za-z][-_A-Za-z0-9]{5,19})", re.I)
IDCARD = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")


def mask(text):
    """PII 打码。返回 (masked, hits)。宁可多打，不可漏存。"""
    hits = []
    t = text or ""
    for pat, tag in ((IDCARD, "idcard"), (PHONE, "phone"), (EMAIL, "email")):
        if pat.search(t):
            hits.append(tag)
            t = pat.sub("〔%s〕" % tag, t)
    m = WECHAT.search(t)
    if m:
        hits.append("wechat")
        t = WECHAT.sub("〔wechat〕", t)
    return t, hits


def load_matrix(path=MATRIX):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def policy_of(matrix, platform, behavior):
    """返回 (mode, row)。未知平台/行为返回 ('unknown', None)。"""
    p = (matrix.get("platforms") or {}).get(platform)
    if not p:
        return "unknown", None
    row = (p.get("behaviors") or {}).get(behavior)
    if not row:
        return "unknown", None
    return str(row.get("mode") or "待核"), row


def ingest(raw_dir, out_dir, cooldown_min=30, matrix_path=MATRIX):
    matrix = load_matrix(matrix_path)
    stats = {"read": 0, "ok": 0, "rejected_forbidden": 0, "rejected_unknown": 0,
             "dupe": 0, "cooldown": 0, "masked": 0, "need_manual": 0}
    seen_ids, seen_hash, last_author = set(), set(), {}
    out = []
    for fn in sorted(os.listdir(raw_dir)):
        if not fn.endswith(".jsonl") or "." not in fn[:-6]:
            continue
        platform, behavior = fn[:-6].split(".", 1)
        mode, _row = policy_of(matrix, platform, behavior)
        with open(os.path.join(raw_dir, fn), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                stats["read"] += 1
                try:
                    r = json.loads(line)
                except Exception:
                    stats["rejected_unknown"] += 1
                    continue
                if mode == "forbidden":
                    stats["rejected_forbidden"] += 1
                    continue
                if mode == "unknown":
                    stats["rejected_unknown"] += 1
                    continue
                text, hits = mask(str(r.get("text") or r.get("comment") or ""))
                if hits:
                    stats["masked"] += 1
                key = "%s|%s|%s" % (platform, behavior, r.get("id"))
                if key in seen_ids:
                    stats["dupe"] += 1
                    continue
                seen_ids.add(key)
                h = hashlib.sha256(("%s|%s|%s" % (platform, r.get("author"), text)).encode()).hexdigest()[:16]
                if h in seen_hash:
                    stats["dupe"] += 1
                    continue
                seen_hash.add(h)
                face = BEHAVIOR_FACE.get(behavior)
                row = {
                    "id": "%s-%s-%s" % (platform, behavior, r.get("id")),
                    "platform": platform,
                    "behavior": behavior,
                    "face": face or "comment",
                    "author": r.get("author"),
                    "video": r.get("thread") or r.get("video"),
                    "comment": text,
                    "comment_id": str(r.get("id") or ""),   # 发送时要定位平台侧评论
                    "ts": r.get("ts") or datetime.now().isoformat(timespec="seconds"),
                    "policy": mode,
                    "needs_approval": mode in ("api_write", "export"),
                    "pii_masked": bool(hits),
                }
                # 冷却：同平台同作者在窗口内已有条目 -> 标 HOLD，人来决定回哪条
                akey = (platform, str(r.get("author") or ""))
                prev = last_author.get(akey)
                if prev and cooldown_min > 0:
                    try:
                        gap = (datetime.fromisoformat(row["ts"]) - datetime.fromisoformat(prev)).total_seconds() / 60
                        if gap < cooldown_min:
                            row["state"] = "HOLD_COOLDOWN"
                            stats["cooldown"] += 1
                    except Exception:
                        pass
                last_author[akey] = row["ts"]
                if mode in ("manual", "待核"):
                    stats["need_manual"] += 1
                out.append(row)
                stats["ok"] += 1
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "inbox.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return stats, path


def self_test():
    cases = []
    tmp = tempfile.mkdtemp(prefix="social-ingest-")
    raw = os.path.join(tmp, "raw")
    os.makedirs(raw)
    # 1 正常评论
    open(os.path.join(raw, "douyin.comment.jsonl"), "w", encoding="utf-8").write(
        json.dumps({"id": "1", "author": "阿岚", "text": "用什么软件剪的", "thread": "v1"}, ensure_ascii=False) + "\n")
    # 2 同内容重复（不同 id）
    open(os.path.join(raw, "douyin.comment.jsonl"), "a", encoding="utf-8").write(
        json.dumps({"id": "2", "author": "阿岚", "text": "用什么软件剪的", "thread": "v1"}, ensure_ascii=False) + "\n")
    # 3 红线组合：B站主动发弹幕
    open(os.path.join(raw, "bilibili.danmaku_send.jsonl"), "w", encoding="utf-8").write(
        json.dumps({"id": "9", "author": "x", "text": "来啦"}, ensure_ascii=False) + "\n")
    # 4 未知平台
    open(os.path.join(raw, "myspace.comment.jsonl"), "w", encoding="utf-8").write(
        json.dumps({"id": "8", "author": "y", "text": "hi"}, ensure_ascii=False) + "\n")
    # 5 PII 必须打码
    open(os.path.join(raw, "douyin.dm.jsonl"), "w", encoding="utf-8").write(
        json.dumps({"id": "3", "author": "买家", "text": "我手机13800138000 加V:abc12345 联系"},
                   ensure_ascii=False) + "\n")
    # 6 作品/选题这类没有草稿通道的行为要能进来（face 回落到 comment）
    open(os.path.join(raw, "wechat_mp.publish.jsonl"), "w", encoding="utf-8").write(
        json.dumps({"id": "4", "author": "me", "text": "待发图文"}, ensure_ascii=False) + "\n")

    stats, path = ingest(raw, tmp)
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    by_id = {r["id"]: r for r in rows}
    cases.append(("红线组合必须拒绝", stats["rejected_forbidden"] == 1 and "bilibili-danmaku_send-9" not in by_id))
    cases.append(("未知平台必须拒绝", stats["rejected_unknown"] == 1))
    cases.append(("同内容必须去重", stats["dupe"] == 1 and len([r for r in rows if r["platform"] == "douyin" and r["behavior"] == "comment"]) == 1))
    cases.append(("手机号必须打码", "13800138000" not in open(path, encoding="utf-8").read()))
    cases.append(("微信号必须打码", "abc12345" not in open(path, encoding="utf-8").read()))
    cases.append(("脱敏行必须留痕", any(r.get("pii_masked") for r in rows)))
    cases.append(("写行为必须标待批", by_id["douyin-dm-3"]["needs_approval"] is True))
    cases.append(("选题/发布无草稿通道回落 comment", by_id["wechat_mp-publish-4"]["face"] == "comment"))
    # 冷却：同作者 30 分钟内第二条（下面用独立沙箱真跑，不做恒真断言）
    raw2 = os.path.join(tmp, "raw2")
    os.makedirs(raw2)
    open(os.path.join(raw2, "douyin.comment.jsonl"), "w", encoding="utf-8").write(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in [
            {"id": "a", "author": "同一人", "text": "第一条", "ts": "2026-11-17T10:00:00"},
            {"id": "b", "author": "同一人", "text": "第二条", "ts": "2026-11-17T10:05:00"}]) + "\n")
    st2, p2 = ingest(raw2, os.path.join(tmp, "out2"))
    rows2 = [json.loads(l) for l in open(p2, encoding="utf-8") if l.strip()]
    cases.append(("同作者冷却期标 HOLD", st2["cooldown"] == 1 and rows2[1].get("state") == "HOLD_COOLDOWN"))
    ok = sum(1 for _, v in cases if v)
    for name, v in cases:
        if not v:
            print("  FAIL %s" % name)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    print("[self-test] 沙箱=%s" % tmp)
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=None, help="原始事件目录（<platform>.<behavior>.jsonl）")
    ap.add_argument("--out", default=None, help="输出目录（写 inbox.jsonl）")
    ap.add_argument("--cooldown", type=int, default=30, help="同作者冷却分钟（默认 30）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.raw or not a.out:
        print("[ingest] 需要 --raw 与 --out（或用 --self-test）")
        return 2
    stats, path = ingest(a.raw, a.out, cooldown_min=a.cooldown)
    print("[ingest] 读%d 入队%d | 红线拒%d 未知拒%d 去重%d 冷却%d 脱敏%d 待批%d -> %s"
          % (stats["read"], stats["ok"], stats["rejected_forbidden"], stats["rejected_unknown"],
             stats["dupe"], stats["cooldown"], stats["masked"], stats["need_manual"], path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
