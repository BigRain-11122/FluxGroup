#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""practice_tick.py - 实战循环的一拍：每 90 分钟被 launchd 叫一次，干一件，永不收工。

CEO 2026-11-18「你创建自动化定时任务，不断循环啊，为什么我不看就不跑了」。

之前的问题：我挂的是 `RunAtLoad + KeepAlive=false` 的一次性批，跑完就没了。
现在改成 **StartInterval=5400（90 分钟）** 的循环作业，每一拍做这些事：

  1 读 FREQ-POLICY（每日上限 + 最小间隔），不满足就记一条"本拍跳过"并退出——**循环不中断**
  2 满足则：挑一个未用过的同领域视频 → 按字数带生成 → 双闸 → 发 → 回验 → 落账
  3 每次刷新 cph4/fleet/social/PRACTICE-ROLLING.md（滚动清单，不是一次性报告）
  4 止损：最近 7 条全不可见 → 停止发帖，写 BLOCKED-ACCOUNT 说明，只记账不再刷
     （对静默扣留的账号继续刷＝纯风险，不是勤奋）

设计原则：**每一拍都必须有产出（发出 / 跳过原因 / 止损原因），没有"什么都没做"的拍。**
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
LEDGER = os.path.join(SOCIAL, "practice-log.jsonl")
SCREEN = os.path.join(SOCIAL, "PRACTICE-ROLLING.md")
BLOCKED = os.path.join(ROOT, ".codely-cli", "state", "PRACTICE-BLOCKED.json")
PY = sys.executable

sys.path.insert(0, HERE)
NICHE = ("剪辑", "教程", "MV", "mv", "转场", "调色", "分镜", "短片", "拍摄", "剪映", "运镜")
ARMS = ("C", "A", "D", "C")          # 轮转：顶级短评 → 短回复 → 长回复 → 顶级短评
STOP_AFTER = 7                        # 连续不可见多少条就停


def rows_today():
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if str(r.get("ts", "")).startswith(today):
                    out.append(r)
    except FileNotFoundError:
        pass
    return out


def recent_visibility(n=STOP_AFTER):
    """最近 n 条已回验的结果（True/False）。用于止损判断。"""
    v = []
    try:
        for line in open(LEDGER, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if r.get("action") == "verify" and "visible" in r:
                    v.append(bool(r["visible"]))
    except FileNotFoundError:
        pass
    return v[-n:]


def used_videos():
    s = set()
    for line in (open(LEDGER, encoding="utf-8") if os.path.exists(LEDGER) else []):
        if line.strip():
            r = json.loads(line)
            if r.get("video"):
                s.add(r["video"])
    return s


def blocked():
    try:
        d = json.load(open(BLOCKED, encoding="utf-8"))
        return d if d.get("active") else None
    except Exception:
        return None


def set_blocked(why):
    os.makedirs(os.path.dirname(BLOCKED), exist_ok=True)
    json.dump({"active": True, "why": why, "since": datetime.now().isoformat(timespec="seconds")},
              open(BLOCKED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def log(rec):
    rec.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def refresh_screen(note=""):
    posts, vis = {}, {}
    for r in rows_today():
        # 没有 rpid 的历史行也要进表，否则"今日已发 N 条"与表格行数对不上（11-18 实锚 10 vs 9）
        key = r.get("rpid") or ("norp-%s" % r.get("ts", ""))
        if r.get("action") == "post":
            posts[key] = r
        elif r.get("action") == "verify" and r.get("rpid"):
            vis[r["rpid"]] = bool(r.get("visible"))
    L = ["# 实战滚动清单 %s" % datetime.now().strftime("%m-%d %H:%M"), "",
         "- 今日已发 %d 条 ｜ 公开可见 %d 条 ｜ 最近 %d 条可见率 %s"
         % (len(posts), sum(vis.values()), len(recent_visibility()),
            "%.0f%%" % (100.0 * sum(recent_visibility()) / max(len(recent_visibility()), 1))),
         "- 本拍：%s" % (note or "-"), "",
         "| # | 时间 | 动作 | 文案 | rpid | 可见 |", "|---|---|---|---|---|---|"]
    for i, (rp, r) in enumerate(sorted(posts.items(), key=lambda kv: kv[1]["ts"]), 1):
        L.append("| %d | %s | post | %s | %s | %s |"
                 % (i, r["ts"][11:16], (r.get("text") or "")[:28].replace("|", "/"), rp,
                    "✅" if vis.get(rp) else ("❌" if rp in vis else "…")))
    b = blocked()
    if b:
        L += ["", "> ⛔ 已止损：%s（自 %s）" % (b["why"], b["since"])]
    open(SCREEN, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main():
    # 1 止损闸
    b = blocked()
    if b:
        refresh_screen("止损中，不发帖")
        print("[tick] 已止损：%s" % b["why"])
        return 0
    rv = recent_visibility()
    if len(rv) >= STOP_AFTER and not any(rv):
        why = "最近 %d 条全部公开不可见，判定账号被静默扣留，停止刷帖" % len(rv)
        set_blocked(why)
        log({"action": "blocked", "why": why})
        refresh_screen(why)
        print("[tick] 止损：%s" % why)
        return 0
    # 2 政策闸
    sys.path.insert(0, HERE)
    import freq_policy as fp
    import arm_probe as ap
    pol = fp.load_policy()
    mx, gap = int(pol.get("max_per_day", 2)), int(pol.get("min_gap_min", 90))
    n = len([r for r in rows_today() if r.get("action") == "post"])
    if n >= mx:
        refresh_screen("今日已达上限 %d 条，本拍跳过" % mx)
        log({"action": "skip", "why": "daily cap %d/%d" % (n, mx)})
        print("[tick] 跳过：今日 %d/%d" % (n, mx))
        return 0

    # 3 挑目标（同领域优先、未用过）
    try:
        vids = json.load(open(TITLES, encoding="utf-8"))
    except Exception:
        refresh_screen("无视频清单")
        return 2
    used = used_videos()
    cand = [(k, v) for k, v in vids.items()
            if (v or {}).get("title") and k not in used]
    cand.sort(key=lambda kv: -sum(1 for w in NICHE if w in (kv[1]["title"] or "")))
    if not cand:
        refresh_screen("没有未用过的视频")
        log({"action": "skip", "why": "no target"})
        return 0
    url, meta = cand[0]
    title = meta["title"]
    arm = ARMS[n % len(ARMS)]

    # 4 生成（按臂字数带）
    lo, hi = (10, 20) if arm in ("A", "B", "C") else (25, 90)
    import llm_client as lc
    import comment_taste as ct
    import social_practice as sp
    rng = random.Random(int(time.time()))
    text = ""
    for k in range(8):
        p = lc.lora_comment_prompt(title, meta.get("desc") or "", i=k)
        p += "只写 %d-%d 字，一句话。" % (lo, hi)
        r = lc.generate(p, model="qwen3.5:4b-mlx", think=False,
                        num_predict=max(20, hi + 6), keep_alive="6h")
        t = (r.get("text") or "").strip().strip("“”\"'").split("\n")[0].strip()
        if not t or not (lo <= len(t) <= hi):
            continue
        if ct.score(t)["verdict"] != "PASS":
            continue
        if not sp.safe_to_send(t, title)[0]:
            continue
        text = t
        break
    if not text:
        refresh_screen("本拍无文案过闸（不硬发）")
        log({"action": "skip", "why": "no text passed gates", "arm": arm, "video": url})
        print("[tick] 跳过：无文案过闸")
        return 0

    # 5 发 + 回验
    res = ap.run(arm, url, text, dry=False, wait_s=25, ctx=title)
    if res.get("stage") != "posted":
        refresh_screen("发帖未成：%s" % str(res.get("why"))[:60])
        log({"action": "fail", "why": str(res.get("why"))[:120], "arm": arm})
        print("[tick] 未成：%s" % str(res.get("why"))[:80])
        return 0
    refresh_screen("本轮 %s 臂已发：%s" % (arm, text[:20]))
    print("[tick] 发出 rpid=%s 可见=%s" % (res.get("rpid"), res.get("visible")))
    return 0


def unblock():
    """解除止损。人工确认账号已恢复（实名/手机号/可见率回升）后才可调用。"""
    if os.path.exists(BLOCKED):
        os.remove(BLOCKED)
        log({"action": "unblock"})
    refresh_screen("已人工解除止损")
    return 0


def status():
    b = blocked()
    rv = recent_visibility()
    n = len([r for r in rows_today() if r.get("action") == "post"])
    print("[tick] 今日已发 %d 条 ｜ 最近 %d 条可见 %d ｜ 止损 %s"
          % (n, len(rv), sum(rv), ("中(%s)" % b["why"]) if b else "未触发"))
    return 0


def self_test():
    """负控自检：三个闸都必须能拦住，且**任何路径都不许真发帖**。

    2026-11-18 教训：llm_client.lora_comment_prompt 被别的机器提交整段覆盖，
    4 个工具同时失效却没人发现——所以自检里必须包含"依赖完整性"这一项。
    """
    import tempfile
    global LEDGER, SCREEN, BLOCKED, STOP_AFTER
    saved = (LEDGER, SCREEN, BLOCKED, STOP_AFTER)
    d = tempfile.mkdtemp(prefix="ptick-")
    LEDGER, SCREEN, BLOCKED = (os.path.join(d, n) for n in
                               ("log.jsonl", "screen.md", "blocked.json"))
    now = datetime.now().isoformat(timespec="seconds")
    ok, bad = [], []

    def check(name, cond):
        (ok if cond else bad).append(name)
        print("  %s %s" % ("PASS" if cond else "FAIL", name))

    def write(rows):
        with open(LEDGER, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def posts():
        try:
            return sum(1 for l in open(LEDGER, encoding="utf-8")
                       if l.strip() and json.loads(l).get("action") == "post")
        except FileNotFoundError:
            return 0

    try:
        # A 七连不可见 → 必须止损，且不发帖
        write([{"action": "verify", "rpid": str(i), "visible": False, "ts": now}
               for i in range(STOP_AFTER)])
        rc = main()
        check("A 七连不可见→止损且零发帖", rc == 0 and blocked() and posts() == 0)

        # B 已止损 → 再跑也不发帖（幂等）
        rc = main()
        check("B 止损后静默不重复发", rc == 0 and posts() == 0)

        # C 解除止损 → 状态回到未触发
        unblock()
        check("C --unblock 可解除", blocked() is None)

        # D 负控：阈值未到（STOP_AFTER+1）就**不许**止损。
        #    必须同时把日限占满，否则会走到真生成路径（自检绝不许触发真发帖）。
        import freq_policy as fp
        mx = int(fp.load_policy().get("max_per_day", 2))
        STOP_AFTER = 8
        write([{"action": "verify", "rpid": str(i), "visible": False, "ts": now}
               for i in range(7)]
              + [{"action": "post", "rpid": "d%d" % i, "ts": now} for i in range(mx)])
        main()
        check("D 负控：未到阈值不误判止损", blocked() is None)
        STOP_AFTER = 7

        # E 已达日限 → 走政策闸跳过，不发帖
        write([{"action": "post", "rpid": "p%d" % i, "ts": now} for i in range(mx)])
        rc = main()
        check("E 日限已满→跳过零发帖", rc == 0 and posts() == mx)

        # F 依赖完整性（本次事故的回归位）
        import llm_client as lc
        check("F llm_client 三件与训练哨兵齐备",
              all(hasattr(lc, n) for n in
                  ("lora_comment_prompt", "generate_lora", "TRAIN_SENTINEL")))
        import social_collect as sc
        check("G social_collect 内存闸齐备",
              all(hasattr(sc, n) for n in ("workers_by_mem", "unload_models", "set_mode")))
    finally:
        LEDGER, SCREEN, BLOCKED, STOP_AFTER = saved
        import shutil
        shutil.rmtree(d, ignore_errors=True)

    print("[tick] self-test %d/%d" % (len(ok), len(ok) + len(bad)))
    if bad:
        print("[tick] 失败项：" + "；".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--unblock", action="store_true", help="人工解除止损")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if a.unblock:
        sys.exit(unblock())
    if a.status:
        sys.exit(status())
    sys.exit(main())
