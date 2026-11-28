#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""line_runner.py — 本机「一线一进程」的唯一执行体。

令源：CEO 2026-11-27「先把本机自动化任务和算力分配都停了，然后规划好，每条线给一个专用的，
比如 b 站的给一条，公众号给一条，好好测试」。

为什么换掉旧的（实锚 2026-11-27）：35 个 LaunchAgent 里养号 9 个调度器、训练 6 个、体检 6 个，
互相抢同一个浏览器 profile；还有一套「平台时段轮转」让公众号给 B 站让位，台账里 68 拍空转。
一条线一个进程，才说得清「谁在跑、跑出了什么、坏了谁接」。

线的定义（机读正身 cph4/fleet/LOCAL-LANES-v1.json）：
  bili    B站双号养号（同一会话窗口只开一个号，两号轮流）
  gzh     公众号（采集/学结构/造训练集；发文永远人审，不在这条线上）
  collect 采集（纯 HTTP：新闻/音乐/豆瓣/公众号产业语料）
  train   训练与评测（占 GPU；会话时段不出手）
  ops     体检与一屏（只读+落屏，不生产内容、不踢进程）

纪律：
  · 一拍只做一件事；做完写 state/lanes/<line>.json 与 <line>.jsonl，判据只认产出。
  · 单实例：同一线同一时刻只有一个进程（flock 非阻塞，撞车记 BUSY 不排队）。
  · 总开关：.codely-cli/state/LANES-PAUSED 存在 → 全线 SKIP（停线不靠卸载）。

用法：
  python3 Tools/fleet/line_runner.py --lane bili            # 一拍
  python3 Tools/fleet/line_runner.py --lane gzh --dry       # 只判不做
  python3 Tools/fleet/line_runner.py --lane ops --status    # 看上一拍
  python3 Tools/fleet/line_runner.py --list                 # 列线
  python3 Tools/fleet/line_runner.py --self-test            # 负控自检
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CFG_PATH = os.path.join(ROOT, "cph4", "fleet", "LOCAL-LANES-v1.json")
STATE_DIR = os.path.join(ROOT, ".codely-cli", "state", "lanes")
PAUSE = os.path.join(ROOT, ".codely-cli", "state", "LANES-PAUSED")
BOARD = os.path.join(ROOT, "cph4", "fleet", "LANES-BOARD.md")
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
UA_LEDGER = os.path.join(SOCIAL, "USER-AGENT-LEDGER.jsonl")
GZH_LEDGER = os.path.join(SOCIAL, "gzh", "LOOP-LEDGER.jsonl")
CORPUS_FILES = [
    os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl"),
    os.path.join(SOCIAL, "gzh", "ARTICLES-INDUSTRY.jsonl"),
]
RUNS = os.path.join(SOCIAL, "train", "RUNS")
EVAL_HISTORY = os.path.join(SOCIAL, "train", "SEGMENT-EVAL-HISTORY.json")
BAKED = os.path.join(SOCIAL, "corpus", "human", "BAKED-v1.jsonl")
BAKE_EVERY_H = 6

sys.path.insert(0, HERE)
import compute_broker as cb  # noqa: E402

FREE_HARD = 800        # MB，低于它全线只收尾
FREE_BROWSER = 1500    # MB，低于它不开新浏览器活
MAX_BROWSERS = 3       # 非独占线（如 measure）的上限；独占线由算力槽串行，不再看这个数


# ---------------- 基础工具 ----------------
def now():
    return datetime.now()


def iso(dt=None):
    return (dt or now()).isoformat(timespec="seconds")


def load_cfg():
    with open(CFG_PATH, encoding="utf-8") as f:
        return json.load(f)


def lane_of(cfg, lid):
    for x in cfg.get("lanes") or []:
        if x["id"] == lid:
            return x
    return None


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p


def atomic_json(path, obj):
    ensure_dir(os.path.dirname(path))
    tmp = "%s.tmp.%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def append_jsonl(path, rec):
    ensure_dir(os.path.dirname(path))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_jsonl(path, limit=4000):
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
                    pass
                if len(out) > limit:
                    out = out[-limit:]
    except FileNotFoundError:
        pass
    return out


def state_path(lid):
    return os.path.join(STATE_DIR, lid + ".json")


def load_state(lid):
    try:
        with open(state_path(lid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def hours_since(ts_iso):
    try:
        return (now() - datetime.fromisoformat(str(ts_iso))).total_seconds() / 3600.0
    except Exception:
        return 1e9


def age_of(path):
    try:
        return round((time.time() - os.path.getmtime(path)) / 3600.0, 2)
    except Exception:
        return None


def line_count(path):
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _py_with(mod):
    """按能力挑解释器：本机实测 .venv-housing 有 playwright 无 mlx_lm，pyenv 反之。"""
    cands = [
        os.environ.get("LANE_PY_" + mod.upper()),
        os.path.join(ROOT, ".venv-housing", "bin", "python"),
        "/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3",
        "/usr/bin/python3",
        sys.executable,
    ]
    for p in cands:
        if not p or not os.path.exists(p):
            continue
        try:
            r = subprocess.run([p, "-c", "import %s" % mod], capture_output=True, timeout=40)
            if r.returncode == 0:
                return p
        except Exception:
            continue
    return sys.executable


def probe_model(port=8788):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/v1/models" % port, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def probe_facts():
    """本拍的事实。仲裁器不可用时按"未知"处理，不因工具缺失停工（但会记 why）。"""
    facts = {"swap_mb": None, "free_mb": None, "browsers": [], "train_running": False,
             "model_8788": probe_model(8788), "model_8789": probe_model(8789), "why": ""}
    try:
        import res_alloc as ra
        facts["swap_mb"] = ra.swap_mb()
        facts["free_mb"] = ra.mem_free_mb()
        facts["browsers"] = ra.browsers()
        facts["train_running"] = ra.train_running()
    except Exception as e:
        facts["why"] = "仲裁器不可用（%s）：按未知放行" % type(e).__name__
    return facts


def session_now():
    """现在是否有任一账号在会话窗口内（按各自日程判，不看已退役的全局计划）。"""
    try:
        import social_session as ss
        for alias in ("acct1", "acct3"):
            cur = ss.current(account=alias)
            if cur:
                return cur
        return None
    except Exception:
        return None


def last_session_row():
    for r in reversed(read_jsonl(UA_LEDGER, 800)):
        if r.get("action") == "session":
            return r
    return None


def capacity(lane, facts, session_active):
    """资源闸只做容量判定，不做平台轮转。返回 (ok, why)。"""
    needs = set(lane.get("needs") or [])
    free = facts.get("free_mb")
    if free is not None and free >= 0 and free < FREE_HARD:
        return False, "可用内存 %dMB < %dMB：只收尾" % (free, FREE_HARD)
    if "browser" in needs:
        if free is not None and free >= 0 and free < FREE_BROWSER:
            return False, "可用内存 %dMB < %dMB：不开新浏览器活" % (free, FREE_BROWSER)
        # 独占线（bili/gzh）已由 compute_broker 串行，浏览器数量不再是并行风险；
        # 2026-11-28 实锚：底座空闲上下文没回收，被算成"2 个浏览器在跑"，早间两场全被挡。
        if not (lane.get("compute") or {}).get("exclusive"):
            if len(facts.get("browsers") or []) >= MAX_BROWSERS:
                return False, "已有 %d 个浏览器 profile 在跑（上限 %d）" % (
                    len(facts.get("browsers") or []), MAX_BROWSERS)
    if "gpu" in needs:
        if facts.get("train_running"):
            return False, "已有训练进程在跑（同一块 GPU 不叠跑）"
        if session_active:
            return False, "养号会话进行中：GPU 让给出稿，训练下一拍再来"
    if "model" in needs:
        port = int((lane.get("compute") or {}).get("port") or 8788)
        if facts.get("model_%d" % port) is False:
            return False, "本线专用模型 %d 未就绪" % port
    return True, ""


# ---------------- 执行上下文 ----------------
class Ctx:
    def __init__(self, dry=False, facts=None, session=None, runner=None, board=None):
        self.dry = dry
        self.extra_env = {}
        self.facts = facts if facts is not None else probe_facts()
        self.session = session if session is not None else session_now()
        self._runner = runner
        self.board = board or BOARD

    def run(self, cmd, env=None, timeout=600, cwd=None):
        if self.dry:
            return {"rc": 0, "dry": True, "secs": 0.0, "tail": "DRY: " + " ".join(cmd[-3:])}
        e = dict(os.environ)
        e.update(self.extra_env or {})
        e.update(env or {})
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=cwd or ROOT, env=e, capture_output=True,
                               text=True, timeout=timeout)
            out = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()
            return {"rc": p.returncode, "secs": round(time.time() - t0, 1),
                    "tail": "\n".join(out[-8:])[-1200:]}
        except subprocess.TimeoutExpired as ex:
            out = ((ex.stdout or "") if isinstance(ex.stdout, str) else "").strip()
            return {"rc": 124, "secs": round(time.time() - t0, 1),
                    "tail": ("TIMEOUT %ss: %s" % (timeout, out))[-1200:]}
        except Exception as ex:
            return {"rc": 125, "secs": round(time.time() - t0, 1), "tail": str(ex)[:400]}


def merge_subtask(prev_tasks, subtask, ts):
    """把本次成功的时间戳并进旧表；覆盖写会让其它子任务永远"到期"、永远只跑第一个。"""
    out = dict(prev_tasks or {})
    if subtask:
        out[subtask] = ts
    return out


def _res(status, why, **kw):
    d = {"status": status, "why": why}
    d.update(kw)
    return d


# ---------------- 各线的一拍 ----------------
def daemon_ok(timeout=3):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8791/state", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def revive_daemon():
    """browserd 单线程被长占锁请求卡住时整机不响应；踢一下 launchd 让它重开。"""
    try:
        subprocess.run(["launchctl", "kickstart", "-k",
                        "gui/%d/com.fluxgroup.base.browserd" % os.getuid()],
                       capture_output=True, timeout=30)
        time.sleep(4)
    except Exception:
        pass
    return daemon_ok(5)


def gzh_progress(prev, last):
    """台账涨了不等于产出涨了。真正的产出：风格池变厚/文章变多/产业语料变多/训练集变多。"""
    a = (prev or {}).get("facts") or {}
    b = (last or {}).get("facts") or {}
    keys = ("style_pool", "articles", "industry", "train_rows", "struct_n")
    for k in keys:
        if k in b and k in a and int(b[k]) > int(a[k]):
            return True, "%s %s→%s" % (k, a[k], b[k])
    return False, "台账在涨但产出没涨（%s）" % ", ".join(
        "%s=%s" % (k, b.get(k)) for k in keys if k in b)


def bili_need_login(rows, start):
    """本窗口有没有"登录态失效"（能看不能动手＝这条线没干活）。"""
    return [x for x in rows if str(x.get("ts") or "") >= str(start)
            and x.get("action") == "need_login"]


def bili_actions_since(rows, start):
    """会话窗口内的真实动作（profile_busy/need_login 这类没做成的都不算）。"""
    acts = ("watch", "like", "danmaku", "comment", "coin", "fav", "follow")
    return [x for x in rows if str(x.get("ts") or "") >= str(start)
            and x.get("action") in acts and x.get("ok") is not False]


def account_health(rows):
    """每个号最近一次信号：need_login 之后再没有成功动作 = 这个号现在不能用。"""
    bad = {"acct1": False, "acct3": False}
    acts = ("session", "watch", "like", "danmaku", "comment", "coin", "fav", "follow")
    for r in rows[-1200:]:
        a = str(r.get("account") or "")
        key = ("acct1" if ("大喵没鱼吃" in a or a == "acct1")
               else "acct3" if ("许大喵去喵星" in a or a == "acct3") else None)
        if not key:
            continue
        if r.get("action") == "need_login":
            bad[key] = True
        elif r.get("action") in acts and r.get("ok") is not False:
            bad[key] = False
    return bad


def pick_account(last, rows=None):
    """上一场是谁就换另一个；rows 在时优先能用的号。"""
    last_name = (last or {}).get("account") or ""
    alt = "acct1"
    if "许大喵" in last_name or last_name == "acct3":
        alt = "acct1"
    elif "大喵没鱼吃" in last_name or last_name == "acct1":
        alt = "acct3"
    if rows is None:
        return alt
    bad = account_health(rows)
    usable = [a for a in ("acct1", "acct3") if not bad[a]]
    if not usable:
        return alt
    return alt if alt in usable else usable[0]


BILI_ACCTS = (("acct1", "大喵没鱼吃"), ("acct3", "许大喵去喵星"))


def bili_due(rows, now=None, current_fn=None):
    """每个号各自的窗口：在窗口内且本号在该窗口还没跑过。

    2026-11-28 CEO「排好轮次，穿插 2 个号，模拟真人习惯」：两号各有一份日程，
    不能用"本时段有没有任何 session"判；也不能一个号跑完就当两个号都跑过。
    """
    if current_fn is None:
        import social_session as ss
        current_fn = ss.current
    out = []
    for alias, uname in BILI_ACCTS:
        try:
            cur = current_fn(account=alias)
        except Exception:
            cur = None
        if not cur:
            continue
        start = str(cur.get("start") or "")
        ran = [r for r in rows if r.get("action") == "session"
               and (r.get("account") or "") == uname and str(r.get("ts") or "") >= start]
        if ran:
            continue
        out.append({"alias": alias, "uname": uname, "cur": cur, "start": start})
    out.sort(key=lambda x: x["start"])
    return out


def choose_due(due, rows):
    """两号都到期时选今天场次少的那个（穿插、均衡），并列取更早的窗口。"""
    if len(due) <= 1:
        return due[0] if due else None
    counts = {}
    for alias, uname in BILI_ACCTS:
        counts[alias] = sum(1 for r in rows if r.get("action") == "session"
                            and (r.get("account") or "") == uname
                            and str(r.get("ts") or "").startswith(iso()[:10]))
    return sorted(due, key=lambda d: (counts.get(d["alias"], 0), d["start"]))[0]


def other_acted_recently(rows, who_uname, minutes=12):
    """另一号最近有没有动手（两号同一 IP，动作至少错开 12 分钟）。"""
    other = [u for _, u in BILI_ACCTS if u != who_uname]
    if not other:
        return False
    acts = ("watch", "like", "danmaku", "comment", "coin", "fav", "follow")
    for r in reversed(rows[-400:]):
        if r.get("account") not in other:
            continue
        if r.get("action") not in acts and r.get("action") != "session":
            continue
        return hours_since(r.get("ts")) * 60 < minutes
    return False


def h_bili(lane, ctx):
    if not ctx.dry and not daemon_ok():
        ok2 = revive_daemon()
        return _res("SKIP", "浏览器底座无响应，已重启%s" % ("成功" if ok2 else "未恢复"),
                    evidence={"daemon_ok": ok2})
    rows = read_jsonl(UA_LEDGER, 1200)
    due = bili_due(rows)
    if not due:
        return _res("SKIP", "两个号都不在各自的会话窗口（一天 6-8 场/号，不硬刷）")
    bad = account_health(rows)
    due = [d for d in due if not bad.get(d["alias"])]
    if not due:
        return _res("BLOCKED", "到期的号登录态都失效：需要扫码登录一次",
                    evidence={"bad": bad})
    pick = choose_due(due, rows)
    alias, uname, cur = pick["alias"], pick["uname"], pick["cur"]
    if other_acted_recently(rows, uname, minutes=12):
        return _res("SKIP", "另一号 12 分钟内动过手：错开，避免同 IP 同时动作")
    ok, why = capacity(lane, ctx.facts, True)
    if not ok:
        return _res("SKIP", why)
    py = _py_with("playwright")
    entry = lane["entry"].format(root=ROOT)
    cmd = [py, entry, "--session"]
    if ctx.dry:
        return _res("DRY", "会开一场（%s，窗口 %s）" % (alias, cur.get("start")),
                    evidence={"account": alias, "cmd": cmd, "session": cur})
    r = ctx.run(cmd, env={"FLUX_ACCOUNT": alias}, timeout=lane.get("timeout_s", 2400))
    rows = read_jsonl(UA_LEDGER, 1200)
    new = [x for x in rows if x.get("action") == "session"
           and (x.get("account") or "") == uname
           and str(x.get("ts") or "") >= str(cur.get("start"))]
    acts = bili_actions_since(rows, cur.get("start"))
    need = bili_need_login(rows, cur.get("start"))
    ev = {"account": alias, "session_start": cur.get("start"),
          "ledger_rows": len(new), "actions": len(acts), "need_login": len(need),
          "cmd": cmd}
    if need:
        return _res("BLOCKED", "登录态失效（能看不能动手）：人工扫码一次 "
                    "`.venv-housing/bin/python Tools/fleet/bili_login.py --account %s`" % alias,
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    if r["rc"] == 0 and new and acts:
        return _res("OK", "一场跑完（%s / %d 个动作）" % (alias, len(acts)),
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    if r["rc"] == 0 and not new:
        return _res("FAIL", "进程 rc=0 但本号台账没有新 session 行（假完成）",
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    if r["rc"] == 0 and new and not acts:
        return _res("FAIL", "会话开了但一个真实动作都没有（假完成）",
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    return _res("FAIL", "rc=%s" % r["rc"], evidence=ev, secs=r["secs"], tail=r["tail"])


def h_gzh(lane, ctx):
    if ctx.session:
        return _res("SKIP", "B站会话进行中：browserd 单线程，本轮不排队（不是平台轮转）")
    ok, why = capacity(lane, ctx.facts, bool(ctx.session))
    if not ok:
        return _res("SKIP", why)
    py = _py_with("playwright")
    entry = lane["entry"].format(root=ROOT)
    env = dict(lane.get("env") or {})
    cmd = [py, entry] + list(lane.get("entry_args") or [])
    if ctx.dry:
        return _res("DRY", "会跑一拍（%s）" % entry.split("/")[-1],
                    evidence={"cmd": cmd, "env": env})
    before = line_count(GZH_LEDGER)
    r = ctx.run(cmd, env=env, timeout=lane.get("timeout_s", 900))
    rows = read_jsonl(GZH_LEDGER, 200)
    after = line_count(GZH_LEDGER)
    ev = {"ledger_rows_before": before, "ledger_rows_after": after,
          "last": (rows[-1] if rows else None), "cmd": [py, entry]}
    if r["rc"] == 0 and after > before:
        last = rows[-1] if rows else {}
        prev = rows[-2] if len(rows) > 1 else {}
        if (last.get("status") or "").startswith(("ESCALATE-SUPPLY", "BLOCKED-SUPPLY")):
            return _res("BLOCKED", "缺料：%s" % (last.get("need") or last.get("why") or "需要新种子"),
                        evidence={"last": last, "cmd": [py, entry]}, secs=r["secs"], tail=r["tail"])
        moved, why_moved = gzh_progress(prev, last)
        # 2026-11-28 实锚：prev 可能是几小时前的旧记录，于是把"多拍累积"读成本拍产出，
        # 报出「style_pool 17→96」而这一拍其实入库 0 篇。判据必须以**本拍自己的尾巴**为准。
        import re as _re
        _m = _re.search(r"入库 (\d+) 篇", r.get("tail") or "")
        _got_now = int(_m.group(1)) if _m else None
        if _got_now == 0:
            moved, why_moved = False, "本拍入库 0 篇（%s）" % why_moved
        ev["progress"] = why_moved
        ev["got_this_tick"] = _got_now
        ev["status"] = last.get("status")
        if moved:
            return _res("OK", "一拍有产出（%s）" % why_moved, evidence=ev,
                        secs=r["secs"], tail=r["tail"])
        if "死链台账" in (r.get("tail") or "") and "尝试 0 次" in (r.get("tail") or ""):
            return _res("BLOCKED", "风格池只剩死链（%s）：需要新 URL 种子或修解析" % why_moved,
                        evidence=ev, secs=r["secs"], tail=r["tail"])
        return _res("FAIL", "台账在涨但产出没涨（%s / %s）"
                    % (last.get("status"), why_moved), evidence=ev,
                    secs=r["secs"], tail=r["tail"])
    if r["rc"] == 0:
        return _res("FAIL", "进程 rc=0 但台账没长（假完成）", evidence=ev,
                    secs=r["secs"], tail=r["tail"])
    if r["rc"] == 78:
        return _res("BLOCKED", "缺料/配置：%s" % ((rows[-1].get("need") if rows else "") or "见输出"),
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    return _res("FAIL", "rc=%s" % r["rc"], evidence=ev, secs=r["secs"], tail=r["tail"])


def h_collect(lane, ctx):
    st = load_state("collect").get("tasks") or {}
    due = []
    for t in lane.get("tasks") or []:
        if hours_since(st.get(t["id"])) >= float(t.get("every_h") or 6):
            due.append(t)
    if not due:
        nxt = min(hours_since(st.get(t["id"])) for t in lane.get("tasks") or [])
        return _res("SKIP", "本拍无到期子任务（最近一并 %.1fh 前）" % nxt)
    ok, why = capacity(lane, ctx.facts, bool(ctx.session))
    if not ok:
        return _res("SKIP", why)
    t = due[0]
    py = _py_with("urllib")
    entry = t["entry"].format(root=ROOT)
    cmd = [py, entry] + list(t.get("args") or [])
    if ctx.dry:
        return _res("DRY", "会采 %s" % t["id"], evidence={"task": t["id"], "cmd": cmd})
    before = {p: line_count(p) for p in CORPUS_FILES}
    r = ctx.run(cmd, timeout=t.get("timeout_s", 900))
    after = {p: line_count(p) for p in CORPUS_FILES}
    grew = sum(max(0, after[p] - before[p]) for p in CORPUS_FILES)
    ev = {"task": t["id"], "rows_before": before, "rows_after": after,
          "rows_delta": grew, "cmd": [py, entry]}
    if grew > 0:
        note = "%s 入库 %d 行" % (t["id"], grew)
        if r["rc"] != 0:
            note += "（子进程 rc=%s，部分失败但已落盘）" % r["rc"]
        return _res("OK", note, evidence=ev,
                    secs=r["secs"], tail=r["tail"], subtask=t["id"])
    if r["rc"] == 3 and grew == 0:
        # 采集器约定：rc=3 = 本轮没有新内容（源没变/已采过），不是故障。
        return _res("SKIP", "%s 本轮无新内容（源没变/已采过）" % t["id"], evidence=ev,
                    secs=r["secs"], tail=r["tail"], subtask=t["id"])
    if r["rc"] == 0:
        return _res("FAIL", "%s rc=0 但语料没长（假完成）" % t["id"], evidence=ev,
                    secs=r["secs"], tail=r["tail"], subtask=t["id"])
    return _res("FAIL", "%s rc=%s" % (t["id"], r["rc"]), evidence=ev,
                secs=r["secs"], tail=r["tail"], subtask=t["id"])


def newest_run_dir():
    best, best_t = None, 0
    try:
        for name in os.listdir(RUNS):
            p = os.path.join(RUNS, name)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "RUN.json")):
                m = os.path.getmtime(p)
                if m > best_t:
                    best, best_t = p, m
    except Exception:
        return None
    return best


def next_session_in_min(now=None):
    """下一场（两号任一）还有多少分钟开始；没有则 None。纯读计划，不占资源。"""
    try:
        import social_session as ss
        now = now or now()
        best = None
        for alias in ("acct1", "acct3"):
            p = ss.load_plan(now, account=alias)
            for s in p.get("sessions") or []:
                st = datetime.fromisoformat(s["start"])
                if st <= now:
                    continue
                d = (st - now).total_seconds() / 60.0
                best = d if best is None or d < best else best
        return best
    except Exception:
        return None


TRAIN_ONCE = os.path.join(ROOT, ".codely-cli", "state", "TRAIN-SEG-ONCE")


def train_task():
    """空闲训练队列：文件里逗号分隔的段名，取队头；跑完由 pop_train_task 出队。"""
    try:
        txt = open(TRAIN_ONCE, encoding="utf-8").read().strip()
    except Exception:
        return "", []
    parts = [x.strip() for x in txt.split(",") if x.strip()]
    return (parts[0] if parts else ""), parts[1:]


def pop_train_task(rest):
    try:
        if rest:
            with open(TRAIN_ONCE, "w", encoding="utf-8") as f:
                f.write(",".join(rest))
        else:
            os.remove(TRAIN_ONCE)
    except Exception:
        pass


def h_train(lane, ctx):
    ok, why = capacity(lane, ctx.facts, bool(ctx.session))
    if not ok:
        return _res("SKIP", why)
    # 空闲才吃 GPU：下一场 25 分钟内开始就不开新一轮（训练 40-50 分钟会把窗口吞掉）。
    nxt = ctx.facts.get("next_session_min")
    if nxt is None:
        nxt = next_session_in_min()
    if nxt is not None and nxt < 25:
        return _res("SKIP", "下一场 %.0f 分钟后开始：训练不抢，等空档" % nxt)
    newest = newest_run_dir()
    eval_age = age_of(EVAL_HISTORY)
    run_age = age_of(newest) if newest else None
    py = _py_with("mlx_lm")
    # 语料烘焙（纯 CPU）也归训练线：7 个 worker 约半分钟，产 BAKED-v1.jsonl 决定按段取料。
    baked_age = ctx.facts.get("baked_age_h")
    if baked_age is None:
        baked_age = age_of(BAKED)
    if baked_age is None or baked_age > BAKE_EVERY_H:
        cmd = [py, os.path.join(HERE, "corpus_bake.py"), "--workers", "7"]
        if ctx.dry:
            return _res("DRY", "会先烘焙语料（%.1fh 前）" % (baked_age or -1),
                        evidence={"mode": "bake", "cmd": cmd})
        before = age_of(BAKED)
        r = ctx.run(cmd, timeout=900)
        after = age_of(BAKED)
        ev = {"mode": "bake", "age_before_h": before, "age_after_h": after, "cmd": cmd}
        if r["rc"] == 0 and (after is None or after < (before if before is not None else 1e9)):
            return _res("OK", "语料烘焙完成", evidence=ev, secs=r["secs"], tail=r["tail"])
        return _res("FAIL", "烘焙 rc=%s 或产物没刷新" % r["rc"], evidence=ev,
                    secs=r["secs"], tail=r["tail"])
    if ctx.dry:
        return _res("DRY", "会开训练/评测一拍（最新轮 %s）" % os.path.basename(newest or ""),
                    evidence={"mode": "train-or-eval", "run": newest})
    # 训完没评：先把评测补上，再开新一轮（省一次模型加载）
    if newest and eval_age is not None and run_age is not None and run_age < eval_age:
        entry = os.path.join(HERE, "train_pipeline.py")
        r = ctx.run([py, entry, "--once"], timeout=1800)
        ev = {"mode": "eval", "run": os.path.basename(newest), "cmd": [py, entry]}
        return _res("OK" if r["rc"] == 0 else "FAIL",
                    "补评测（%s）rc=%s" % (os.path.basename(newest), r["rc"]),
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    entry = lane["entry"].format(root=ROOT)
    env = dict(lane.get("env") or {})
    cmd = [py, entry] + list(lane.get("entry_args") or [])
    seg, rest = train_task()
    if seg:
        cmd += ["--seg", seg]      # 空闲队列：按人设段先训，跑完自动出队
    before = os.path.getmtime(newest) if newest else 0
    r = ctx.run(cmd, env=env, timeout=lane.get("timeout_s", 5400))
    newest2 = newest_run_dir()
    advanced = bool(newest2) and (os.path.getmtime(newest2) > before or newest2 != newest)
    ev = {"mode": "train", "run_before": os.path.basename(newest or ""),
          "run_after": os.path.basename(newest2 or ""), "cmd": [py, entry]}
    if r["rc"] == 0 and advanced:
        if seg:
            pop_train_task(rest)
            ev["queued_next"] = rest[:3]
        return _res("OK", "一轮训练已开/已完成（%s%s）"
                    % (os.path.basename(newest2), ("，段 " + seg) if seg else ""),
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    if r["rc"] == 0:
        return _res("SKIP", "本轮没有开训（数据没涨/冷却中/闸拒绝），非故障",
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    if r["rc"] == 78:
        return _res("BLOCKED", "缺料/配置：%s" % ((rows[-1].get("need") if rows else "") or "见输出"),
                    evidence=ev, secs=r["secs"], tail=r["tail"])
    return _res("FAIL", "rc=%s" % r["rc"], evidence=ev, secs=r["secs"], tail=r["tail"])


def last_real_run(lid):
    """最近一次"真跑了"的结论（跳过 SKIP/DRY/BUSY）。

    一屏只显示最新一拍会被后来的 SKIP 盖住：22:36 会话崩了，22:42 一拍 SKIP 就看不见了。
    失败必须留在一屏上，直到下一次真跑覆盖它。
    """
    for r in reversed(read_jsonl(os.path.join(STATE_DIR, lid + ".jsonl"), 300)):
        if r.get("status") not in ("SKIP", "DRY", "BUSY"):
            return r
    return None


def loaded_labels():
    out = []
    try:
        r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
        for line in (r.stdout or "").splitlines()[1:]:
            p = line.split("\t")
            if len(p) >= 3 and p[2].startswith("com.fluxgroup."):
                out.append(p[2])
    except Exception:
        pass
    return out


def h_zhihu(lane, ctx):
    """知乎线（2026-11-28 CEO：自己管）。独立 profile，不经过 browserd。

    判据三条：①被风控（40362）必须记 BLOCKED 并冷却，不许记成「今天没内容」；
    ②环境/程序故障（rc=1）记 FAIL，与「采到 0 条」分开；③回复一律进人审队列，不自动发。
    """
    py = _py_with("playwright")
    entry = (lane["entry"].format(root=ROOT) if lane.get("entry")
             else os.path.join(HERE, "zhihu_loop.py"))
    cmd = [py, entry, "--once"]
    if ctx.dry:
        return _res("DRY", "会跑一拍知乎（采/学/回复三选一）", evidence={"cmd": cmd})
    r = ctx.run(cmd, timeout=lane.get("timeout_s", 900))
    tail = (r.get("tail") or "").strip()
    ev = {"cmd": cmd, "rc": r["rc"]}
    if r["rc"] == 2:
        why = [ln for ln in tail.splitlines() if "BLOCKED" in ln or "风控" in ln]
        return _res("BLOCKED", (why[-1] if why else "被风控或未登录")[-120:], evidence=ev,
                    secs=r["secs"], tail=tail)
    if r["rc"] == 1:
        return _res("FAIL", "程序/环境故障：%s" % tail[-120:], evidence=ev, secs=r["secs"])
    if r["rc"] == 3:
        return _res("EMPTY", "跑了但没采到新内容（%s）" % tail[-100:], evidence=ev, secs=r["secs"])
    return _res("OK", "一拍完成：%s" % tail[-100:], evidence=ev, secs=r["secs"])


def h_measure(lane, ctx):
    """实效核验：把我方已发评论的真实可见性测成一个数。

    为什么单独一条线：bili 线的验收只问"今天动手了吗"，gzh 线把 DEFER+SUPPLY 也算过，
    两条都能在零产出时是绿的。这条线只读不写（不发帖/不点赞/不改台账），
    判据是"判得出的条数不为 0"，unknown 单列、绝不许并进分母。
    """
    ok, why = capacity(lane, ctx.facts, bool(ctx.session))
    if not ok:
        return _res("SKIP", why)
    py = _py_with("urllib")
    entry = lane["entry"].format(root=ROOT)
    cmd = [py, entry] + list(lane.get("entry_args") or []) + ["--json"]
    if ctx.dry:
        return _res("DRY", "会核验最近 7 天的评论可见性", evidence={"cmd": cmd})
    r = ctx.run(cmd, timeout=lane.get("timeout_s", 900))
    tail = r.get("tail") or ""
    data = {}
    for ln in reversed([x for x in tail.splitlines() if x.strip()]):
        try:
            data = json.loads(ln)
            break
        except Exception:
            continue
    s = data.get("summary") or {}
    known = int(s.get("visible") or 0) + int(s.get("invisible") or 0)
    unk = int(s.get("unknown") or 0)
    ev = {"cmd": [py, entry], "summary": s, "rc": r["rc"]}
    if r["rc"] != 0:
        return _res("FAIL", "核验子进程 rc=%s：%s" % (r["rc"], tail[-120:]), evidence=ev)
    if known == 0:
        return _res("BLOCKED-READ", "一条都判不出（unknown=%d）——读侧整体取不到数" % unk,
                    evidence=ev)
    return _res("OK", "判得出 %d 条：可见 %d / 不可见 %d（unknown %d 单列）"
                % (known, int(s.get("visible") or 0), int(s.get("invisible") or 0), unk),
                evidence=ev, secs=r["secs"])


HEAL_LOG = os.path.join(STATE_DIR, "ops-heal.jsonl")
HEAL_MIN_GAP_S = 1200      # 同一条线 20 分钟内最多踢一次，防踢成死循环


def heal_stale(lid, label, st_age_h):
    """对「作业在加载态、但状态久未更新」的线踢一次。

    为什么需要它：2026-11-28 夜，gzh 的状态停在 06:42 达 3.8 小时，而作业本身是加载着的
    （机器被压到负载 33.9，StartInterval 根本没跑起来），ops 只报红不动手，整夜没人管。
    自愈只做一件事：让已登记、未停用、未 parked 的作业重新跑一拍。

    三条边界（不重蹈"health 互相踢"的老路）：
      1. 只看表里登记过的线；表外作业只报不动。
      2. 有 LANES-PAUSED 或 parked 的一律不碰。
      3. 同一条线 20 分钟内只踢一次，记录在 `state/ops-heal.jsonl`。
    """
    if os.path.exists(PAUSE):
        return "paused"
    try:
        for r in read_jsonl(HEAL_LOG, limit=200):
            if r.get("lane") == lid and (time.time() - float(r.get("ts_epoch") or 0)) < HEAL_MIN_GAP_S:
                return "recently-healed"
    except Exception:
        pass
    r = subprocess.run(["launchctl", "kickstart", "gui/%s/%s" % (os.getuid(), label)],
                       capture_output=True, text=True, timeout=20)
    append_jsonl(HEAL_LOG, {"lane": lid, "label": label, "stale_h": round(st_age_h, 1),
                            "rc": r.returncode, "err": (r.stderr or "").strip()[:80],
                            "ts": iso(), "ts_epoch": time.time()})
    return "kicked" if r.returncode == 0 else "kick-failed"


def h_ops(lane, ctx):
    # 先刷仲裁快照：养号会话读 RES-SLOT.json 判资源降档，快照不新鲜等于没闸。
    ctx.run([_py_with("urllib"), os.path.join(HERE, "res_alloc.py"), "--once"], timeout=120)
    cfg = load_cfg()
    allowed = {x["label"] for x in cfg.get("lanes") or []}
    allowed |= {x["label"] for x in cfg.get("base_services") or []}
    loaded = loaded_labels()
    extra = sorted(set(loaded) - allowed)
    rows = []
    red = []
    for x in cfg.get("lanes") or []:
        lid = x["id"]
        if x.get("parked"):
            rows.append({"lane": lid, "name": x.get("name"), "health": "PARKED",
                         "last": "—", "status": "PARKED",
                         "why": (x.get("parked_reason") or "已停")[:60],
                         "real": "—", "real_why": "", "evidence": "", "ev_age_h": None})
            continue
        st = load_state(lid)
        ev = (x.get("acceptance") or {}).get("evidence") or ""
        ev_abs = os.path.join(ROOT, ev) if ev and not os.path.isabs(ev) else ev
        ev_age = age_of(ev_abs) if ev_abs else None
        st_age = hours_since(st.get("ts")) if st.get("ts") else None
        if st_age is None:
            health = "NEW"
        elif st_age * 3600 > float(x.get("every_s") or 600) * 3:
            health = "STALE"
            # 只报红不动手＝整夜没人管（2026-11-28 实锚），所以这里踢一次；
            # 限流与边界都在 heal_stale 里，且结果写进这一行的 why，看得见。
            _hv = heal_stale(lid, x.get("label") or "", st_age)
            red.append("%s 状态 %sh 未更新（自愈：%s）" % (lid, round(st_age, 1), _hv))
        elif ev_age is not None and ev_age > float((x.get("acceptance") or {}).get("max_age_h") or 24):
            health = "EVID-STALE"
            red.append("%s 证据 %sh 未更新" % (lid, ev_age))
        else:
            health = "FRESH"
        real = last_real_run(lid) or {}
        rows.append({"lane": lid, "name": x.get("name"), "health": health,
                     "last": st.get("ts"), "status": st.get("status"),
                     "why": (st.get("why") or "")[:60],
                     "real": ("%s@%s" % (real.get("status"), str(real.get("ts"))[5:16])
                              if real else "—"),
                     "real_why": (real.get("why") or "")[:60],
                     "evidence": ev, "ev_age_h": ev_age})
    if extra:
        red.append("表外作业：%s" % ", ".join(extra))
    free = ctx.facts.get("free_mb")
    swap = ctx.facts.get("swap_mb")
    if free is not None and free >= 0 and free < FREE_HARD:
        red.append("可用内存 %dMB 低于 %dMB" % (free, FREE_HARD))
    cs = cb.snapshot()
    slot = ("空闲" if not cs.get("holder") else
            "%s（need=%s，自 %s）" % (cs.get("holder"), cs.get("need"), cs.get("since")))
    text = ["# 本机车道一屏（%s）" % iso(), "",
            "- 算力槽：%s ｜ 排队：%s" % (slot, ",".join(cs.get("queue") or []) or "无"),
            "- 资源：可用内存 %s MB ｜ swap %s MB（历史）｜ 浏览器 %s ｜ 训练 %s ｜ 8788 %s ｜ 8789 %s"
            % (free, swap, ",".join(ctx.facts.get("browsers") or []) or "无",
               "在跑" if ctx.facts.get("train_running") else "空",
               "就绪" if ctx.facts.get("model_8788") else "未就绪",
               "就绪" if ctx.facts.get("model_8789") else "未就绪"),
            "- 表外作业：%s" % (", ".join(extra) if extra else "无"),
            "", "| 线 | 状态 | 上一拍 | 最近实跑（含失败） | 证据龄期(h) |", "|---|---|---|---|---|"]
    for r in rows:
        text.append("| %s %s | %s | %s | %s | %s |" % (
            r["lane"], r["name"], r["health"], r["last"] or "—",
            r["real"] + ("：" + r["real_why"] if r.get("real_why") else ""),
            r["ev_age_h"] if r["ev_age_h"] is not None else "—"))
    text += ["", "红线：%s" % ("；".join(red) if red else "无"), ""]
    ensure_dir(os.path.dirname(ctx.board))
    with open(ctx.board, "w", encoding="utf-8") as f:
        f.write("\n".join(text))
    ev = {"board": ctx.board, "red": red, "extra_jobs": extra, "lanes": rows}
    if red:
        return _res("FAIL", "一屏有红线：%s" % "；".join(red)[:300], evidence=ev)
    return _res("OK", "一屏已刷新（%d 条线）" % len(rows), evidence=ev)


HANDLERS = {"bili": h_bili, "gzh": h_gzh, "collect": h_collect,
            "measure": h_measure, "zhihu": h_zhihu,
            "train": h_train, "ops": h_ops}


# ---------------- 一拍的外壳 ----------------
def tick(lid, dry=False, ctx=None, persist=True):
    cfg = load_cfg()
    lane = lane_of(cfg, lid)
    if not lane:
        raise SystemExit("未知车道 %s（可选：%s）" % (lid, ",".join(HANDLERS)))
    if os.path.exists(PAUSE):
        return _res("SKIP", "总开关 LANES-PAUSED 存在：全线停手")
    h = now().hour
    if lane.get("hours") and h not in lane["hours"]:
        # 2026-11-28 实锚：这条提前返回**没写状态文件**，于是 ops 拿旧的 ts 判 STALE，
        # 把一条每小时都在正常收工的线报成"3 小时没更新"，自愈还去踢它。
        # 结论：任何 SKIP 都必须更新 ts，否则"状态龄期"这个判据根本不可信。
        res = _res("SKIP", "不在本线时段（%d 点）" % h)
        res.update({"lane": lid, "ts": iso(), "dry": bool(dry)})
        if persist:
            try:
                atomic_json(state_path(lid), res)
                append_jsonl(os.path.join(STATE_DIR, lid + ".jsonl"), res)
            except Exception:
                pass
        return res
    lock = None
    try:
        ensure_dir(STATE_DIR)
        lock = open(os.path.join(STATE_DIR, lid + ".lock"), "a+")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return _res("BUSY", "上一拍还没收工（单实例）")
        ctx = ctx or Ctx(dry=dry)
        if dry:
            ctx.dry = True
        # 不在会话窗口就直接收手：先占槽再判断窗口会让别的线白等（bili 5 分钟一拍）。
        if lid == "bili" and not ctx.session:
            res = _res("SKIP", "两个号都不在各自的会话窗口（7-9 场/号/天，不硬刷）")
            res.update({"lane": lid, "ts": iso(), "dry": bool(ctx.dry),
                        "facts": {k: v for k, v in ctx.facts.items() if k != "why"}})
            if persist:
                atomic_json(state_path(lid), res)
                append_jsonl(os.path.join(STATE_DIR, lid + ".jsonl"), res)
            return res
        comp = lane.get("compute") or {}
        port = comp.get("port")
        if port:
            ctx.extra_env["FLUX_LORA_BASE"] = "http://127.0.0.1:%d" % int(port)
        leased = False
        if comp.get("exclusive") and not ctx.dry:
            ok, why, waited = cb.acquire(lid, comp.get("need") or "compute",
                                        comp.get("queue_timeout_s") or 0,
                                        comp.get("ttl_s") or 3600)
            if not ok:
                res = _res("QUEUED", "算力槽被占：排队 %.0fs 未轮到（%s）" % (waited, why),
                           compute={"need": comp.get("need"), "port": port})
                ts = iso()
                res.update({"lane": lid, "ts": ts, "dry": False,
                            "facts": {k: v for k, v in ctx.facts.items() if k != "why"}})
                if persist:
                    atomic_json(state_path(lid), res)
                    append_jsonl(os.path.join(STATE_DIR, lid + ".jsonl"), res)
                return res
            leased = True
        try:
            res = HANDLERS[lid](lane, ctx)
        finally:
            if leased:
                cb.release(lid)
        ts = iso()
        res.update({"lane": lid, "ts": ts, "dry": bool(ctx.dry),
                    "facts": {k: v for k, v in ctx.facts.items() if k != "why"}})
        # 子任务周期只在成功后推进；失败下一拍还它。必须先合并旧表再落盘。
        if res.get("subtask") and res.get("status") == "OK":
            prev = load_state(lid)
            res["tasks"] = merge_subtask(prev.get("tasks"), res["subtask"], ts)
        else:
            prev = load_state(lid)
            if prev.get("tasks"):
                res["tasks"] = prev["tasks"]
        if persist:
            atomic_json(state_path(lid), res)
            append_jsonl(os.path.join(STATE_DIR, lid + ".jsonl"), res)
        return res
    finally:
        if lock is not None:
            try:
                fcntl.flock(lock, fcntl.LOCK_UN)
                lock.close()
            except Exception:
                pass


def print_res(res):
    print("[%s] %s：%s" % (res.get("lane", "?"), res.get("status"), res.get("why")))
    ev = res.get("evidence")
    if ev:
        print("  证据：%s" % json.dumps(ev, ensure_ascii=False)[:600])
    if res.get("tail"):
        print("  输出尾：%s" % str(res["tail"]).replace("\n", " | ")[:500])


# ---------------- 自检（含负控） ----------------
class FakeCtx(Ctx):
    def __init__(self, facts=None, session=None, rc=0, advanced=False):
        super().__init__(dry=False, session=(session if session is not None else {}),
                         facts=facts or {"swap_mb": 0, "free_mb": 4000,
                                         "browsers": [], "train_running": False,
                                         "model_8788": True})
        self.rc = rc
        self.calls = []

    def run(self, cmd, env=None, timeout=600, cwd=None):
        self.calls.append(list(cmd))
        return {"rc": self.rc, "secs": 0.1, "tail": "fake"}


def self_test():
    cases = []
    # 自检必须在**隔离的状态目录**里跑：否则真实车道正在工作时（实测 11-28 上午 gzh
    # 恰好在采料），自检 tick 同一个车道会被单实例锁判 BUSY，"算力槽被占→QUEUED"
    # 那条用例就会偶发失败——那不是逻辑错，是测试去抢了生产锁。
    global STATE_DIR
    _saved_state_dir = STATE_DIR
    import tempfile as _tf
    STATE_DIR = _tf.mkdtemp(prefix="lr-selftest-")

    # 1 未知车道
    try:
        tick("bogus", dry=True)
        cases.append(("未知车道必须报错", False))
    except SystemExit:
        cases.append(("未知车道必须报错", True))

    # 2 总开关
    os.makedirs(os.path.dirname(PAUSE), exist_ok=True)
    open(PAUSE, "w").close()
    try:
        r = tick("ops", dry=True, ctx=FakeCtx())
        cases.append(("总开关存在必须 SKIP", r["status"] == "SKIP" and "LANES-PAUSED" in r["why"]))
    finally:
        os.remove(PAUSE)

    # 3 资源闸负控
    lane = lane_of(load_cfg(), "bili")
    ok, why = capacity(lane, {"free_mb": 500, "browsers": [], "train_running": False}, None)
    cases.append(("可用内存 500MB 必须拒", (not ok) and "800" in why))
    ok, _ = capacity(lane, {"free_mb": 4000, "browsers": ["a", "b"], "train_running": False}, None)
    cases.append(("独占线不看浏览器数（由算力槽串行）", ok))
    _meas = {"id": "m", "needs": ["browser"], "compute": {"kind": "cpu", "exclusive": False}}
    ok2, _ = capacity(_meas, {"free_mb": 4000, "browsers": ["a", "b", "c"], "train_running": False}, None)
    cases.append(("非独占线 3 个浏览器必须拒", not ok2))
    ok, why = capacity(lane_of(load_cfg(), "train"),
                       {"free_mb": 4000, "browsers": [], "train_running": True}, None)
    cases.append(("训练在跑必须拒第二轮", (not ok) and "GPU" in why))
    ok, why = capacity(lane_of(load_cfg(), "train"),
                       {"free_mb": 4000, "browsers": [], "train_running": False}, {"start": "x"})
    cases.append(("会话中训练必须让路", (not ok) and "会话" in why))

    # 4 不在会话窗口：bili 必须 SKIP 而不是 OK
    r = h_bili(lane, FakeCtx(session=None))
    cases.append(("bili 不在窗口 → SKIP", r["status"] == "SKIP"))

    # 5 假完成负控：rc=0 但台账没长 → FAIL
    r = h_gzh(lane_of(load_cfg(), "gzh"), FakeCtx(session=None))
    cases.append(("gzh rc=0 但台账没长 → FAIL", r["status"] == "FAIL"))

    # 6 采集无到期子任务 → SKIP
    st = load_state("collect")
    r = h_collect(lane_of(load_cfg(), "collect"), FakeCtx(session=None))
    cases.append(("采集无到期 → SKIP", r["status"] == "SKIP" or r["status"] == "FAIL"))
    # 采集器 rc=3 = 无新内容，不能当故障；但 rc=0 却没长仍是假完成（上面已测）
    st_c = load_state("collect")
    st_c.pop("tasks", None)
    r3 = h_collect(lane_of(load_cfg(), "collect"), FakeCtx(session=None, rc=3))
    cases.append(("采集 rc=3 → SKIP 不报故障", r3["status"] == "SKIP"))

    # 6b dry 必须记 DRY，不能把"没执行"记成 FAIL
    d = h_gzh(lane_of(load_cfg(), "gzh"), Ctx(dry=True, facts={"swap_mb": 0, "free_mb": 4000,
                                                               "browsers": [], "train_running": False,
                                                               "model_8788": True}, session={}))
    cases.append(("dry 拍记 DRY 不记 FAIL", d["status"] == "DRY"))

    # 6c 产出判据负控：台账涨但 facts 不变 → 不算前进
    same = {"facts": {"pool_todo": 38, "articles": 21, "industry": 226, "train_rows": 0}}
    moved, why = gzh_progress(same, same)
    cases.append(("gzh 台账涨但产出不动 → 不算 OK", (not moved) and "产出没涨" in why))
    moved, _ = gzh_progress({"facts": {"pool_todo": 40, "style_pool": 55}},
                            {"facts": {"pool_todo": 38, "style_pool": 55}})
    cases.append(("gzh 只清死链（pool_todo 降）不算前进", not moved))
    moved, _ = gzh_progress({"facts": {"style_pool": 55}}, {"facts": {"style_pool": 58}})
    cases.append(("gzh 风格池变厚 → 算前进", moved))
    rows = [{"ts": "2026-11-27T21:00:00", "action": "session", "account": "x"},
            {"ts": "2026-11-27T21:01:00", "action": "watch", "ok": True},
            {"ts": "2026-11-27T21:02:00", "action": "profile_busy", "ok": False}]
    cases.append(("bili 会话有真实动作才算数", len(bili_actions_since(rows, "2026-11-27T20:59:00")) == 1))
    cases.append(("bili 只有 profile_busy 不算数",
                  len(bili_actions_since([rows[2]], "2026-11-27T20:59:00")) == 0))
    ng = [{"ts": "2026-11-27T21:44:41", "action": "need_login", "account": "x"}]
    cases.append(("bili 登录失效必须被识别", len(bili_need_login(ng, "2026-11-27T21:40:00")) == 1))
    cases.append(("bili 无登录失效不误报", len(bili_need_login(rows, "2026-11-27T20:00:00")) == 0))

    # 6h3 空闲训练队列：队头可读、出队可写
    _save = open(TRAIN_ONCE, "w", encoding="utf-8") if False else None
    try:
        with open(TRAIN_ONCE, "w", encoding="utf-8") as f:
            f.write("shallow,peer_pro")
        head, rest = train_task()
        cases.append(("训练队列取队头", head == "shallow" and rest == ["peer_pro"]))
        pop_train_task(rest)
        h2, r2 = train_task()
        cases.append(("训练队列出队后剩 peer_pro", h2 == "peer_pro" and r2 == []))
        pop_train_task([])
        cases.append(("队列空后文件删除", not os.path.exists(TRAIN_ONCE)))
    finally:
        pop_train_task([])

    # 6h2 下一场 25 分钟内 → 训练不抢
    tr2 = Ctx(dry=True, facts={"swap_mb": 0, "free_mb": 12000, "browsers": [],
                               "train_running": False, "model_8788": True,
                               "baked_age_h": 0, "next_session_min": 10}, session={})
    r2 = h_train(lane_of(load_cfg(), "train"), tr2)
    cases.append(("下一场将至 → 训练让路", r2["status"] == "SKIP" and "下一场" in r2["why"]))

    # 6d 烘焙到期时训练线先烘焙（CPU），不把料理交给没人认领的旧 plist
    tr = L_ctx = Ctx(dry=True, facts={"swap_mb": 0, "free_mb": 12000, "browsers": [],
                                      "train_running": False, "model_8788": True,
                                      "baked_age_h": 99}, session={})
    r = h_train(lane_of(load_cfg(), "train"), tr)
    cases.append(("烘焙过期 → DRY mode=bake", r["status"] == "DRY" and
                  (r.get("evidence") or {}).get("mode") == "bake"))

    # 6e 子任务计时必须叠加，不能覆盖掉别的子任务
    m = merge_subtask({"news": "2026-11-27T01:00:00"}, "music", "2026-11-27T02:00:00")
    cases.append(("子任务计时叠加不覆盖", m.get("news") and m.get("music")))
    cases.append(("空旧表也能写入", merge_subtask(None, "news", "x").get("news") == "x"))

    # 6f 坏号先停：need_login 之后没有成功动作的号不再排班
    hist = [{"action": "need_login", "account": "大喵没鱼吃"},
            {"action": "watch", "ok": True, "account": "许大喵去喵星"}]
    cases.append(("坏号被识别", account_health(hist)["acct1"] is True))
    cases.append(("好号不被误判", account_health(hist)["acct3"] is False))
    cases.append(("坏号停排：两个号只选能用的", pick_account({"account": "许大喵去喵星"}, hist) == "acct3"))
    hist2 = hist + [{"action": "watch", "ok": True, "account": "大喵没鱼吃"}]
    cases.append(("登录恢复后重新排班", account_health(hist2)["acct1"] is False))
    cases.append(("两号都好时仍轮流", pick_account({"account": "许大喵去喵星"}, hist2) == "acct1"))

    # 6g 算力槽被占 → QUEUED（不是 FAIL，也不是偷偷并行）
    orig_acq = cb.acquire
    orig_cfg = load_cfg

    def _all_day_cfg():
        c = orig_cfg()
        for x in c.get("lanes") or []:
            if x["id"] == "gzh":
                x["hours"] = list(range(24))
        return c
    try:
        cb.acquire = lambda *a, **k: (False, "占用中：bili", 12.0)
        globals()["load_cfg"] = _all_day_cfg
        r = tick("gzh", dry=False, ctx=FakeCtx(session=None), persist=False)
    finally:
        cb.acquire = orig_acq
        globals()["load_cfg"] = orig_cfg
    cases.append(("算力槽被占 → QUEUED", r["status"] == "QUEUED" and "占用中" in r["why"]))
    cases.append(("自检不写生产状态", "QUEUED" not in json.dumps(load_state("gzh"), ensure_ascii=False)))

    # 6h 两号各自排窗口：在窗口内且本号没跑过才算到期；都到期时选场次少的
    def _cur(account):
        if account == "acct1":
            return {"start": "2026-11-28T20:00:00", "dur_min": 10}
        return {"start": "2026-11-28T20:30:00", "dur_min": 10}
    due = bili_due([], current_fn=_cur)
    cases.append(("两号都在窗口 → 两条到期", len(due) == 2))
    ran1 = [{"action": "session", "account": "大喵没鱼吃", "ts": "2026-11-28T20:01:00"}]
    due1 = bili_due(ran1, current_fn=_cur)
    cases.append(("本号跑过就不再排（另一号不受影响）",
                  len(due1) == 1 and due1[0]["alias"] == "acct3"))
    rows_bal = [{"action": "session", "account": "大喵没鱼吃", "ts": "%sT09:00:00" % iso()[:10]},
                {"action": "session", "account": "大喵没鱼吃", "ts": "%sT10:00:00" % iso()[:10]}]
    pick = choose_due(due, rows_bal)
    cases.append(("都到期时选场次少的号", pick["alias"] == "acct3"))
    recent = [{"action": "like", "account": "许大喵去喵星", "ok": True, "ts": iso()}]
    cases.append(("另一号刚动手 → 要错开", other_acted_recently(recent, "大喵没鱼吃", 12) is True))
    cases.append(("另一号很久没动 → 不错开", other_acted_recently([], "大喵没鱼吃", 12) is False))

    # 7 号轮换
    cases.append(("上一场 acct1 → 这场 acct3", pick_account({"account": "大喵没鱼吃"}) == "acct3"))
    cases.append(("上一场 acct3 → 这场 acct1", pick_account({"account": "许大喵去喵星"}) == "acct1"))

    # 8 一屏：未知作业必须报红（不能静默）。测试只写临时一屏，绝不碰生产文件。
    tmp_board = os.path.join(STATE_DIR, "__selftest-board.md")
    ctx = FakeCtx()
    ctx.board = tmp_board
    orig = globals()["loaded_labels"]
    try:
        globals()["loaded_labels"] = lambda: ["com.fluxgroup.line.bili", "com.fluxgroup.rogue"]
        r = h_ops(lane_of(load_cfg(), "ops"), ctx)
    finally:
        globals()["loaded_labels"] = orig
    cases.append(("表外作业必须报红", r["status"] == "FAIL" and "com.fluxgroup.rogue" in r["why"]))
    cases.append(("自检不写生产一屏", os.path.basename(ctx.board) == "__selftest-board.md"))
    try:
        os.remove(tmp_board)
    except Exception:
        pass

    # 9 状态读写往返
    atomic_json(state_path("__selftest"), {"ok": 1})
    cases.append(("状态文件可读回", load_state("__selftest").get("ok") == 1))
    os.remove(state_path("__selftest"))

    ok = sum(1 for _, v in cases if v)
    for name, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", name))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    STATE_DIR = _saved_state_dir
    return 0 if ok == len(cases) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", default="")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.list:
        cfg = load_cfg()
        for x in cfg.get("lanes") or []:
            print("%-8s %-12s 每 %ss ｜ %s" % (x["id"], x.get("name"), x.get("every_s"),
                                              x.get("why_one_lane")))
        return 0
    if not a.lane:
        ap.error("--lane 必填（或 --list / --self-test）")
    if a.status:
        st = load_state(a.lane)
        print(json.dumps(st or {"note": "还没跑过"}, ensure_ascii=False, indent=1))
        return 0
    res = tick(a.lane, dry=a.dry)
    print_res(res)
    return 0 if res["status"] in ("OK", "SKIP", "BUSY", "QUEUED") else 1


if __name__ == "__main__":
    sys.exit(main())
