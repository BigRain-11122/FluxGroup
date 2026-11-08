#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_brain.py - 常驻大模型的高频机队决策席：规则给事实与候选，模型只做选择。

CEO 2026-11-08：「你常驻的大模型就负责每天高频率的管理机队和派发任务什么的」。

为什么这样分工（不是让模型自己算）：
  · 4B 级算术实测两次全错（220-116-6 答成 100/104）——数字一律由规则算；
  · 模型擅长的是「在已算好的几件事里挑最该做的那一件」，以及给一句为什么。
  · 所以：**候选集合由规则生成、动作由代码白名单执行、模型只在候选里排序**。
    模型返回任何不认识的 id 一律视为无效，回落规则首选——它没有发明动作的权力。

每一轮做四步：
  1. 采集事实（车道/队列/停摆线/闭环命中）——全部是数出来的，不是模型说的；
  2. 生成候选动作（每条带 id、做什么、为什么现在可做、代价）；
  3. 问常驻模型挑一个 + 一句话理由（think=false，超时即回落）；
  4. 执行（白名单），记账 state/fleet-brain.jsonl，出一屏 FLEET-BRAIN.md。

用法：
  python3 Tools/fleet/fleet_brain.py            # 只决策不执行
  python3 Tools/fleet/fleet_brain.py --apply    # 决策并执行
  python3 Tools/fleet/fleet_brain.py --selftest # 用假模型验证"越权/乱答必须回落"
退出码：0 正常（含回落）/ 2 无候选（无事可做，也算正常，但要说清）
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BOARD = os.path.join(F, "FLEET-BRAIN.md")
LEDGER = os.path.join(STATE, "fleet-brain.jsonl")
sys.path.insert(0, HERE)

COOLDOWN_S = 600          # 同一动作 10 分钟内不重复执行，除非候选理由变了


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def jl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8-sig"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


# ------------------------------------------------------------------ 事实
def facts():
    import fleet_lane as fl
    rows = jl(QUEUE)
    opens = [r for r in rows if str(r.get("state") or "").upper() == "OPEN"]
    running = [r for r in rows if str(r.get("state") or "").upper() == "RUNNING"]
    lanes = {}
    for n in fl.ACTIVE_LANES:
        d = jload(fl.lane_file(ROOT, n), {})
        lanes[n] = {"jobs": len(d.get("jobs") or []),
                    "idle_reason": (d.get("idle_reason") or "")[:40]}
    lines = (jload(os.path.join(STATE, "lines.json"), {}) or {}).get("lines") or []
    stalled = [{"id": l.get("id"), "age_h": l.get("age_h"),
                "declared": l.get("declared")}
               for l in lines
               if str(l.get("declared") or "ACTIVE").upper() == "ACTIVE"
               and float(l.get("age_h") or 0) >= 72]
    bl = jload(os.path.join(STATE, "blocker-loop.json"), {}) or {}
    return {
        "ts": now(),
        "lanes": lanes,
        "idle_nodes": [n for n, v in lanes.items() if v["jobs"] == 0],
        "open": len(opens), "running": len(running),
        "stalled_lines": stalled,
        "blocker_hits": int(bl.get("hits") or 0),
        "blocker_escalate": len(bl.get("escalate") or []),
        "unowned": [r.get("id") for r in rows
                    if str(r.get("state") or "").upper() in ("OPEN", "RUNNING")
                    and not r.get("owner")][:5],
        # 坏账本：带冲突标记或坏行时主控会静默少看卡（2026-11-08 下午就是这么停摆的）
        "queue_dirty": _queue_dirty(),
        # 重复活卡：并发供给铺重，两台机跑同一交付物，回执互相覆盖
        "dup_live": _dup_live(rows),
        # 执行者停摆：FleetLink 活着但 wakes 为空（机器在"能连但不能干"的状态）
        "dead_exec": _dead_exec(),
    }


def _queue_dirty():
    """队列/备队列里冲突标记或坏行的总行数（0 = 干净）。"""
    try:
        import queue_sanitize as qs
        n = 0
        for rel in qs.TARGETS:
            p = os.path.join(ROOT, rel)
            if os.path.isfile(p):
                b, nj, _ = qs.scan(p)
                n += b * 3 + nj
        return n
    except Exception:
        return 0


def _dup_live(rows):
    """同交付物的活卡组数（>0 说明有重复劳动）。"""
    import collections
    LIVE = ("OPEN", "READY", "RUNNING", "CLAIMED", "PENDING")
    by = collections.Counter()
    for r in rows:
        if str(r.get("state") or "").upper() in LIVE and (r.get("deliverable") or "").strip():
            by[r["deliverable"].strip()] += 1
    return sum(1 for d, c in by.items() if c > 1)


def _dead_exec():
    """执行者停摆的机器数（/status 的 wakes 为空且不在冷却）。"""
    try:
        import executor_revive as er
        nodes, port = er.roster()
        n = 0
        for nd in nodes:
            if not nd.get("enable_tasks") or not nd.get("tailnet_ip"):
                continue
            code, st = er.http_json(er.base_url(nd, port) + "/status", timeout=8)
            v, _ = er.decide(st if code == 200 else None)
            if v in ("wake", "closeout"):
                n += 1
        return n
    except Exception:
        return 0


# ------------------------------------------------------------------ 候选
def candidates(fx):
    """规则生成候选：每条都有 id / 做什么 / 现在为什么可做 / 代价。模型只能从这里挑。"""
    c = []
    if fx["idle_nodes"] and fx["open"] < 2 * max(len(fx["lanes"]), 1):
        c.append({"id": "A_FILL", "do": "补供给：night_fill + workgen + supply_batch",
                  "why": "%d 台空转而待派只有 %d 张" % (len(fx["idle_nodes"]), fx["open"]),
                  "cost": 2})
    if fx["open"] and any(v["jobs"] == 0 for v in fx["lanes"].values()):
        c.append({"id": "A_DISPATCH", "do": "派单：master_agent 把队列里的卡装进空车道",
                  "why": "有 %d 张待派且有机器空着" % fx["open"], "cost": 1})
    if fx["blocker_hits"]:
        c.append({"id": "A_CLOSE_LOOP", "do": "跑堵点闭环：按分类表检测并自动解",
                  "why": "闭环上次报 %d 项命中" % fx["blocker_hits"], "cost": 2})
    if fx["unowned"]:
        c.append({"id": "A_ASSIGN", "do": "定责：给无主活卡按 nodes 指定承办机",
                  "why": "%d 张活卡没有 owner" % len(fx["unowned"]), "cost": 1})
    if fx["stalled_lines"]:
        c.append({"id": "A_NIGHT_PLAN", "do": "按声明补卡：night_plan 派各线唯一下一步",
                  "why": "%d 条 ACTIVE 线已停 ≥72h" % len(fx["stalled_lines"]), "cost": 2})
    if fx.get("queue_dirty"):
        c.append({"id": "A_SANITIZE", "do": "修坏账本：清冲突标记与坏行（取两侧并集，不丢卡）",
                  "why": "队列/备队列有 %d 行污染，主控正在静默少看卡" % fx["queue_dirty"],
                  "cost": 1})
    if fx.get("dup_live"):
        c.append({"id": "A_DEDUPE", "do": "按交付物撤重复活卡（保留跑得最远的那张）",
                  "why": "%d 组同交付物多张活卡，两台机在互相覆盖回执" % fx["dup_live"],
                  "cost": 1})
    if fx.get("dead_exec"):
        c.append({"id": "A_REVIVE", "do": "唤醒停摆执行者：poke 显式启用 / 发收口卡",
                  "why": "%d 台机器 FleetLink 活着但不唤醒任务" % fx["dead_exec"],
                  "cost": 1})
    c.append({"id": "A_NOOP", "do": "什么都不做，保持现状",
              "why": "没有值得动的事，别为动而动", "cost": 0})
    return c


# ------------------------------------------------------------------ 模型选择
PROMPT = """你是机队调度台。下面是**已经由程序算好**的事实和候选动作，你只能从候选里挑一个。

事实：
{facts}

候选：
{cands}

只输出一行 JSON，键必须是 action 和 reason：
{{"action": "<候选里的某个 id>", "reason": "<不超过20字，说为什么先做它>"}}
不许输出候选以外的 id，不许解释，不许换行。"""


def render_prompt(fx, cands):
    f_lines = [
        "- 车道：" + "，".join("%s %d 张%s" % (n, v["jobs"],
                                            ("（%s）" % v["idle_reason"]) if v["idle_reason"] else "")
                              for n, v in fx["lanes"].items()),
        "- 队列：待派 %d，在飞 %d" % (fx["open"], fx["running"]),
        "- 空转机：%s" % (",".join(fx["idle_nodes"]) or "无"),
        "- 停摆线（ACTIVE≥72h）：%s" % (",".join("%s/%.0fh" % (s["id"], s["age_h"] or 0)
                                              for s in fx["stalled_lines"]) or "无"),
        "- 堵点闭环上次：命中 %d，待升级 %d" % (fx["blocker_hits"], fx["blocker_escalate"]),
        "- 无主活卡：%s" % (",".join(map(str, fx["unowned"])) or "无"),
    ]
    c_lines = ["- %s：%s（%s；代价%d）" % (c["id"], c["do"], c["why"], c["cost"])
               for c in cands]
    return PROMPT.format(facts="\n".join(f_lines), cands="\n".join(c_lines))


def choose(fx, cands, model_fn):
    """返回 (action_id, reason, source)。模型越权/乱答/超时一律回落规则首选。"""
    ids = [c["id"] for c in cands]
    rule_pick = next((i for i in ids if i != "A_NOOP"), "A_NOOP")
    if not model_fn:
        return rule_pick, "规则首选（未接模型）", "rule"
    try:
        raw = model_fn(render_prompt(fx, cands)) or ""
    except Exception:
        return rule_pick, "模型调用异常，回落规则首选", "rule"
    txt = raw.strip()
    a = r = None
    for line in reversed(txt.splitlines()):
        line = line.strip().strip("`")
        if line.startswith("{"):
            try:
                d = json.loads(line)
                a, r = str(d.get("action") or ""), str(d.get("reason") or "")[:40]
                break
            except Exception:
                continue
    if a not in ids:
        # 模型越权或答不出：不许执行它说的东西，回落规则首选
        return rule_pick, "模型未给出合法候选（%s），回落规则首选" % (a or "空"), "fallback"
    return a, r or "模型选择", "model"


# ------------------------------------------------------------------ 执行
def _run(argv, timeout=420):
    try:
        r = subprocess.run([sys.executable] + argv, cwd=ROOT, capture_output=True,
                           text=True, timeout=timeout,
                           env=dict(os.environ, FLUX_AUTOMATION="1"))
        tail = ((r.stdout or "").strip().splitlines() or [""])[-1][:120]
        return r.returncode, tail
    except Exception as e:
        return 99, str(e)[:100]


ACTIONS = {
    "A_FILL": lambda: _run(["Tools/fleet/night_fill.py", "--target", "6"])[0:2],
    "A_DISPATCH": lambda: _run(["Tools/fleet/master_agent.py", "--node", "bm-m",
                                "--root", "."])[0:2],
    "A_CLOSE_LOOP": lambda: _run(["Tools/fleet/blocker_loop.py", "--apply"])[0:2],
    "A_ASSIGN": lambda: _run(["Tools/fleet/blocker_loop.py", "--apply", "--force"])[0:2],
    "A_NIGHT_PLAN": lambda: _run(["Tools/fleet/night_plan.py"])[0:2],
    "A_SANITIZE": lambda: _run(["Tools/fleet/queue_sanitize.py", "--fix",
                                "--report", "cph4/fleet/QUEUE-CONFLICT-RESOLVE.md"])[0:2],
    "A_DEDUPE": lambda: _run(["Tools/fleet/queue_sanitize.py", "--check", "--dedupe"])[0:2],
    "A_REVIVE": lambda: _run(["Tools/fleet/executor_revive.py", "--apply"])[0:2],
    "A_NOOP": lambda: (0, "保持现状"),
}


def last_run(action):
    for row in reversed(jl(LEDGER)):
        if row.get("action") == action:
            try:
                return datetime.strptime(row["ts"], "%Y-%m-%dT%H:%M:%S").timestamp()
            except Exception:
                return 0
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    fx = facts()
    cands = candidates(fx)
    ids = [c["id"] for c in cands]

    if a.selftest:
        # 三种假模型：越权 / 乱码 / 合法——只有第三种可以被采纳
        bad1 = lambda p: '{"action":"A_DELETE_EVERYTHING","reason":"放大招"}'
        bad2 = lambda p: "我觉得应该先补货"
        good = lambda p: '{"action":"%s","reason":"先补供给"}' % ids[0]
        r1 = choose(fx, cands, bad1)
        r2 = choose(fx, cands, bad2)
        r3 = choose(fx, cands, good)
        ok = (r1[2] == "fallback" and r1[0] in ids
              and r2[2] == "fallback" and r2[0] in ids
              and r3[0] == ids[0] and r3[2] == "model")
        print(json.dumps({"verdict": "PASS" if ok else "FAIL",
                          "beyond_scope": r1[0], "garbage": r2[0], "legal": r3},
                         ensure_ascii=False))
        return 0 if ok else 1

    model_fn = None
    try:
        import local_model as lm
        model_fn = lambda p: lm.generate(p, cls="master", timeout=45,
                                         why="fleet_brain:pick")
    except Exception:
        model_fn = None

    action, reason, source = choose(fx, cands, model_fn)
    acted, rc, tail = False, 0, ""
    if a.apply and action != "A_NOOP":
        if datetime.now().timestamp() - last_run(action) < COOLDOWN_S:
            tail, rc = "冷却中（%ds 内已执行过同一动作）" % COOLDOWN_S, 0
        else:
            rc, tail = ACTIONS[action]()
            acted = True

    row = {"ts": now(), "action": action, "reason": reason, "source": source,
           "acted": acted, "rc": rc, "tail": tail,
           "facts": {"open": fx["open"], "running": fx["running"],
                     "idle": fx["idle_nodes"], "stalled": len(fx["stalled_lines"])},
           "candidates": ids}
    if a.apply:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    L = ["# 机队决策（常驻模型在候选里挑）%s" % now(), "",
         "分工：**事实与候选由规则算，动作由代码白名单执行，模型只做选择**"
         "（4B 级算术不可信，所以数字从不交给模型）。", "",
         "## 本轮", "",
         "- 决策：**%s**（%s）" % (action, {"model": "模型选择",
                                          "fallback": "模型越权/乱答→回落规则",
                                          "rule": "规则首选"}.get(source, source)),
         "- 理由：%s" % reason]
    if a.apply:
        L += ["- 执行：%s rc=%s %s" % ("已执行" if acted else "未执行", rc, tail)]
    L += ["", "## 事实（规则算出来的）", "",
          "- 队列：待派 %d / 在飞 %d" % (fx["open"], fx["running"]),
          "- 车道：" + "，".join("%s %d" % (n, v["jobs"]) for n, v in fx["lanes"].items()),
          "- 停摆线：%s" % (",".join(s["id"] for s in fx["stalled_lines"]) or "无"),
          "- 堵点命中 %d / 待升级 %d" % (fx["blocker_hits"], fx["blocker_escalate"]),
          "", "## 候选（模型只能从这里挑）", ""]
    L += ["- `%s` %s — %s" % (c["id"], c["do"], c["why"]) for c in cands]
    recent = jl(LEDGER)[-8:]
    if recent:
        L += ["", "## 最近决策", "", "| 时间 | 决策 | 来源 | 执行 |", "|---|---|---|---|"]
        for r in recent:
            L.append("| %s | %s | %s | %s |" % (r["ts"][11:19], r["action"],
                                                r["source"], "是" if r.get("acted") else "否"))
    L += ["", "---", "_模型没有发明动作的权力：候选外的 id 一律回落规则首选_"]
    open(BOARD, "w", encoding="utf-8").write("\n".join(L) + "\n")

    print("[brain] %s (%s) %s · %s" % (action, source, reason, tail))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))