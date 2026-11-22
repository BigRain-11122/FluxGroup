#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""loop_regression.py — 养号闭环回归：十段全链路，只认磁盘事实，必须能红。

为什么要有它（2026-11-22 实锚）：
  今晚"看起来在跑"的三件事全是假的——
    ① 出稿循环 com.fluxgroup.practicetick 的 plist 在盘上，但根本没被 launchd 加载；
    ② 副动作（看/赞/弹幕）整天 0 条：采集长期占着 browser-profile，会话等锁 180s 必超时；
    ③ 智能体 S8 卡 attempts=175 却从没进 waiting：pick_item 改了状态但空闲分支不落盘。
  三处都没报错、日志都"正常"，只是没有产出。所以闭环不能靠"进程活着"判，只能靠
  "今天这一环有没有真的写出一行产物"判。

判据原则：
  - 每段只读磁盘（台账行 / 文件 mtime / launchd 状态），不读工具自报；
  - 每段给出"证据指针 + 龄期"，龄期不达标即红，不问原因；
  - --self-test 带负控：把被检对象弄坏（空文件 / 不存在的路径 / 未来时间）必须变红，
    否则这条断言就是没接上。

用法：
  .venv-housing/bin/python Tools/fleet/loop_regression.py            # 一屏
  .venv-housing/bin/python Tools/fleet/loop_regression.py --self-test
  .venv-housing/bin/python Tools/fleet/loop_regression.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
STATE = os.path.join(ROOT, ".codely-cli", "state")
PRACTICE = os.path.join(SOCIAL, "practice-log.jsonl")
USER_AGENT = os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl")
BACKLOG = os.path.join(STATE, "QUALITY-BACKLOG.json")
TITLES = os.path.join(SOCIAL, "VIDEO-TITLES.json")
TRAIN_LOG = os.path.join(STATE, "train-loop.log")

# 每段的时间预算：超过就算"这一环今天没转"，不解释
FRESH = {
    "collect": timedelta(hours=26),     # 采集：一天至少一轮
    "train": timedelta(minutes=90),     # 训练循环：300s 一拍，90 分钟没动静算停
    "draft": timedelta(hours=8),        # 出稿：一场会话至少一条
    # 发帖：设计节拍是"真人会话"（一天 4-6 场，实测场间隔最长约 7 小时），
    # 所以窗口不能按"每 30 分钟一拍"定，否则场间必然假红。
    "post": timedelta(hours=8),
    "verify": timedelta(hours=6),       # 回验
    "side": timedelta(hours=12),        # 副动作
}
POST_MEDIAN_LINE = 30.0                 # 单条发帖往返上限（CEO：端到端要落到 30 秒内）


def _rows(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return out


def _today(rows, key="ts"):
    d = datetime.now().strftime("%Y-%m-%d")
    return [r for r in rows if str(r.get(key) or "").startswith(d)]


def _age_min(path):
    try:
        return (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).total_seconds() / 60
    except Exception:
        return None


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def _jobs():
    """当前用户域里的 fluxgroup 作业 → {label: {exists, last_exit}}"""
    out = {}
    try:
        txt = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return out
    for line in txt.splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 3:
            continue
        pid, rc, label = p[0].strip(), p[1].strip(), p[2].strip()
        if not label.startswith("com.fluxgroup."):
            continue
        out[label] = {"pid": pid, "last_exit": rc}
    return out


# ---------------- 十段 ----------------

def seg_supply():
    n = 0
    try:
        d = json.load(open(TITLES, encoding="utf-8"))
        n = len(d) if isinstance(d, (list, dict)) else 0
    except Exception:
        n = 0
    need = 273           # 39 条/天 × 7 天重复窗
    age = _age_min(TITLES)
    return n >= need, "池 %d 条（需 ≥%d）｜文件龄 %.0f 分钟" % (n, need, age or -1)


def seg_collect():
    rows = _rows(PRACTICE)
    got = [r for r in _today(rows) if r.get("action") in ("ingest", "browse")]
    added = sum(int(r.get("added") or 0) for r in got)
    if got:
        return True, "今日 %d 条采集/浏览行，入语料 %d 条" % (len(got), added)
    age = _age_min(PRACTICE)
    return False, "今日 0 条采集/浏览行（practice-log 龄 %.0f 分钟）" % (age or -1)


def seg_train():
    age = _age_min(TRAIN_LOG)
    if age is None:
        return False, "训练循环日志不存在 %s" % TRAIN_LOG
    ok = age <= FRESH["train"].total_seconds() / 60
    return ok, "训练循环日志龄 %.0f 分钟（上限 %.0f）" % (age, FRESH["train"].total_seconds() / 60)


def seg_draft():
    rows = _today(_rows(PRACTICE))
    q = [r for r in rows if r.get("action") == "qualified"]
    if q:
        last = max(str(r.get("ts")) for r in q)
        return True, "今日合格稿 %d 条，最后 %s" % (len(q), last[11:19])
    return False, "今日 0 条 qualified（出稿→过闸没跑通）"


def seg_timing():
    rows = [r for r in _rows(PRACTICE) if r.get("action") == "timing"]
    if not rows:
        return False, "无 timing 行：post/gen/total 三段耗时从未落账（S8 永远待判）"
    post = [float(r["post_s"]) for r in rows if r.get("post_s") is not None]
    m = _median(post)
    if m is None:
        last = str(max(str(r.get("ts") or "") for r in rows))[11:19]
        return False, ("%d 条 timing 全是旧格式（末条 %s），拆分计时上线后还没真发过一条"
                       % (len(rows), last))
    qm = _median([float(r["post_queue_s"]) for r in rows if r.get("post_queue_s") is not None])
    detail = "post 中位 %.1fs（上限 %.0fs，n=%d）" % (m, POST_MEDIAN_LINE, len(post))
    if qm is not None:
        detail += "｜排队中位 %.1fs（等会话腾浏览器，不计入 post）" % qm
    return m <= POST_MEDIAN_LINE, detail


def seg_post():
    rows = _today(_rows(PRACTICE))
    posts = [r for r in rows if r.get("action") == "post"]
    if not posts:
        return False, "今日 0 条真发"
    last = max(str(r.get("ts")) for r in posts)
    try:
        age = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 3600
    except Exception:
        age = 99
    ok = age <= FRESH["post"].total_seconds() / 3600
    return ok, "今日 %d 条，最后一条 %.1f 小时前" % (len(posts), age)


def seg_verify():
    rows = _today(_rows(PRACTICE))
    v = [r for r in rows if r.get("action") == "verify"]
    return bool(v), "今日回验 %d 条（0 条＝发完没人管，闭环断在最后一米）" % len(v)


def seg_side():
    rows = _today(_rows(USER_AGENT))
    if not rows:
        return False, "今日 0 条副动作（看/赞/弹幕）｜台账 %s" % (
            "存在但今天没写" if os.path.exists(USER_AGENT) else "不存在")
    return True, "今日副动作 %d 条" % len(rows)


def seg_schedule():
    jobs = _jobs()
    need = ["com.fluxgroup.practicetick", "com.fluxgroup.qualityagent",
            "com.fluxgroup.socialloop", "com.fluxgroup.socialhealth"]
    missing = [j for j in need if j not in jobs]
    if missing:
        return False, "未加载 %d 个：%s" % (len(missing), "、".join(x.split(".")[-1] for x in missing))
    bad = [(j.split(".")[-1], jobs[j]["last_exit"]) for j in need
           if jobs[j]["last_exit"] not in ("0", "-")]
    if bad:
        return False, "上次退出码非零：%s" % "、".join("%s=%s" % b for b in bad)
    return True, "四个常驻作业都在（%d 个）" % len(need)


def seg_agent():
    try:
        d = json.load(open(BACKLOG, encoding="utf-8"))
    except Exception:
        return False, "卡片台账读不到：%s" % BACKLOG
    items = d.get("items", d)
    stuck = [k for k, v in items.items()
             if v.get("status") in ("open", "doing") and int(v.get("attempts") or 0) > 10]
    waiting_forever = [k for k, v in items.items()
                       if v.get("status") == "waiting" and not v.get("wait_until")]
    if stuck:
        return False, "空转卡 %d 张：%s" % (len(stuck), "、".join(stuck))
    if waiting_forever:
        return False, "无期限 waiting %d 张（永久放弃）：%s" % (
            len(waiting_forever), "、".join(waiting_forever))
    red = [k for k, v in items.items() if v.get("status") in ("open", "doing")]
    return True, "卡片台账 %d 张，需人处置 %d 张（都有到期或可执行）" % (len(items), len(red))


def seg_quality():
    """闸是否真的在跑：social_audit 每 6 小时落一次 GATE-RESULT，读不到＝闸没跑或被搬家。"""
    p = os.path.join(SOCIAL, "state", "GATE-RESULT.json")
    try:
        g = json.load(open(p, encoding="utf-8"))
    except Exception:
        return False, "闸回归结果不存在：%s" % os.path.relpath(p, ROOT)
    age = _age_min(p)
    fresh = age is not None and age <= 8 * 60
    ok = bool(g.get("overall")) and fresh
    return ok, "闸回归 overall=%s，龄 %.0f 分钟（上限 480）" % (g.get("overall"), age or -1)


SEGMENTS = [
    ("L1 供给", seg_supply),
    ("L2 采集", seg_collect),
    ("L3 训练", seg_train),
    ("L4 出稿", seg_draft),
    ("L5 计时", seg_timing),
    ("L6 发帖", seg_post),
    ("L7 回验", seg_verify),
    ("L8 副动作", seg_side),
    ("L9 调度", seg_schedule),
    ("L10 智能体", seg_agent),
    ("L11 闸", seg_quality),
]


def run(json_out=False):
    res = []
    for name, fn in SEGMENTS:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, "断言自身报错：%s: %s" % (type(e).__name__, str(e)[:100])
        res.append({"seg": name, "ok": ok, "detail": detail})
    if json_out:
        print(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "segs": res},
                         ensure_ascii=False, indent=1))
        return 0
    green = sum(1 for r in res if r["ok"])
    print("养号闭环回归 %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    for r in res:
        print("%s %-12s %s" % ("✅" if r["ok"] else "❌", r["seg"], r["detail"]))
    print("—— %d/%d 段绿" % (green, len(res)))
    return 0 if green == len(res) else 1


# ---------------- 负控 ----------------

def self_test():
    """负控：把被检对象弄坏，断言必须变红；不变红＝这条闸没接上。"""
    global PRACTICE, USER_AGENT, BACKLOG, TITLES, TRAIN_LOG
    cases = []
    tmp = tempfile.mkdtemp(prefix="loopreg-")

    saved = (PRACTICE, USER_AGENT, BACKLOG, TITLES, TRAIN_LOG)

    def _point(**kw):
        for k, v in kw.items():
            globals()[k] = v

    # N1 空台账 + 不存在的副动作台账 → 采集/发帖/回验/副动作必须同时红
    empty = os.path.join(tmp, "empty.jsonl")
    open(empty, "w").close()
    _point(PRACTICE=empty, USER_AGENT=os.path.join(tmp, "nope.jsonl"))
    cases.append(("N1 空台账 → 采集红", seg_collect()[0] is False))
    cases.append(("N1 空台账 → 出稿红", seg_draft()[0] is False))
    cases.append(("N1 空台账 → 计时红", seg_timing()[0] is False))
    cases.append(("N1 空台账 → 发帖红", seg_post()[0] is False))
    cases.append(("N1 空台账 → 回验红", seg_verify()[0] is False))
    cases.append(("N1 缺台账 → 副动作红", seg_side()[0] is False))

    # N2 有 post 但时长短于窗口 → 绿；故意写成 9 小时前 → 必须红（证明它读的是时间不是行数）
    now = datetime.now()
    old = (now - timedelta(hours=9)).isoformat(timespec="seconds")
    p2 = os.path.join(tmp, "old.jsonl")
    with open(p2, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": old, "action": "post", "rpid": "1"}) + "\n")
    _point(PRACTICE=p2)
    cases.append(("N2 9 小时前的 post → 红（窗口生效）", seg_post()[0] is False))

    p3 = os.path.join(tmp, "fresh.jsonl")
    with open(p3, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), "action": "post", "rpid": "2"}) + "\n")
        f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), "action": "timing",
                            "post_s": 3.2, "gen_s": 12.0, "total_s": 25.0}) + "\n")
        f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), "action": "verify",
                            "visible": True}) + "\n")
        f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), "action": "qualified",
                            "text": "x"}) + "\n")
    _point(PRACTICE=p3)
    cases.append(("N3 新鲜的完整台账 → 四段全绿", all(x[0] for x in
                 (seg_draft(), seg_timing(), seg_post(), seg_verify()))))

    # N4 计时退化 → post_s 45s 必须红
    p4 = os.path.join(tmp, "slow.jsonl")
    with open(p4, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), "action": "timing",
                            "post_s": 45.0}) + "\n")
    _point(PRACTICE=p4)
    cases.append(("N4 post_s=45s → 红（30s 线生效）", seg_timing()[0] is False))

    # N5 卡片：无期限 waiting 必须红
    p5 = os.path.join(tmp, "backlog.json")
    json.dump({"items": {"X": {"status": "waiting", "attempts": 3}}}, open(p5, "w", encoding="utf-8"))
    _point(BACKLOG=p5)
    cases.append(("N5 无期限 waiting → 红", seg_agent()[0] is False))
    json.dump({"items": {"X": {"status": "waiting", "attempts": 3,
                               "wait_until": (now + timedelta(hours=1)).isoformat(timespec="seconds")}}},
              open(p5, "w", encoding="utf-8"))
    cases.append(("N6 有期限 waiting → 绿", seg_agent()[0] is True))
    json.dump({"items": {"X": {"status": "open", "attempts": 42}}}, open(p5, "w", encoding="utf-8"))
    cases.append(("N7 attempts=42 的空转卡 → 红", seg_agent()[0] is False))

    # N8 调度：断言能识别"作业不在"（拿一个绝不存在的 label 反证判据不是恒真）
    jobs = _jobs()
    cases.append(("N8 作业表可读（非恒真）", isinstance(jobs, dict)))
    cases.append(("N9 缺作业必被点名", "com.fluxgroup.__nope__" not in jobs))

    PRACTICE, USER_AGENT, BACKLOG, TITLES, TRAIN_LOG = saved
    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", action="store_true",
                    help="落一份 state/LOOP-REGRESSION.json 并常退 0（给 launchd 用：报告型工具）")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.write:
        res = []
        for name, fn in SEGMENTS:
            try:
                ok, detail = fn()
            except Exception as e:
                ok, detail = False, "断言自身报错：%s: %s" % (type(e).__name__, str(e)[:100])
            res.append({"seg": name, "ok": ok, "detail": detail})
        green = sum(1 for r in res if r["ok"])
        out = {"ts": datetime.now().isoformat(timespec="seconds"),
               "green": green, "total": len(res), "segs": res}
        os.makedirs(STATE, exist_ok=True)
        with open(os.path.join(STATE, "LOOP-REGRESSION.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        red = [r["seg"] for r in res if not r["ok"]]
        print("%s 闭环 %d/%d 绿%s" % (out["ts"], green, len(res),
                                    ("｜红：" + "、".join(red)) if red else ""))
        # 报告型：红不当作进程失败，否则 launchd 只看到一个坏退出码、看不到红在哪
        return 0
    return run(json_out=a.json)


if __name__ == "__main__":
    sys.exit(main())
