#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_control.py - 群控面：一眼看五台，一次下发命令。

Why（2026-11-13 CEO「做好群控」）：现有能力是散的——station_status 只读本地分片、
notify 只能单发、看板在网页里。缺一个命令行群控面：**先看全部，再决定对谁下什么命令**。

三条设计约束：
  * 数据面只读：查 /status 不改任何机器状态；下发命令必须显式 --poke/--sync；
  * 事实与措辞分家：表里的每个数字都由规则算出；模型只允许把事实改写成一句话，
    且句中出现的事实里没有的数字一律作废（防 4B 加戏）；
  * 判读先规则后模型：规则能判的（离线/分叉/无产出）不交给模型。

用法：
    python3 Tools/fleet/fleet_control.py --status            # 群控表
    python3 Tools/fleet/fleet_control.py --status --brief    # 加一句模型判读
    python3 Tools/fleet/fleet_control.py --poke visual --task HQ-StationDrive --why sync
    python3 Tools/fleet/fleet_control.py --sync delivery
    python3 Tools/fleet/fleet_control.py --self-test
返回码：0 正常 / 1 有需处理的机器 / 2 参数或契约错误 / 3 自检失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

NODES = os.path.join(ROOT, "Tools", "fleet-nodes.json")
PORT = 8790
STATION_OF = {"bm-a": "delivery", "bm-b": "audio", "bm-c": "visual",
              "bm-d": "brain", "bm-m": "control"}


def load_nodes():
    try:
        with open(NODES, encoding="utf-8-sig") as f:
            return json.load(f).get("nodes") or []
    except Exception:
        return []


def probe(node, timeout=15):
    """查一台机的 /status；不可达不判死，只报事实。"""
    ip = node.get("tailnet_ip")
    base = {"node": node.get("id"), "station": STATION_OF.get(node.get("id"), "?"),
            "ip": ip, "reachable": False}
    if not ip or str(ip).startswith("PENDING"):
        base.update({"state": "未入网", "why": "tailnet IP 未分配"})
        return base
    try:
        t0 = time.time()
        with urllib.request.urlopen("http://%s:%d/status" % (ip, PORT), timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8", "replace") or "{}")
        ms = int((time.time() - t0) * 1000)
    except Exception as e:
        base.update({"state": "不可达", "why": type(e).__name__})
        return base
    lp = d.get("last_pull") or {}
    head = (lp.get("repo_heads") or {}).get(".") or (d.get("repo_heads") or {}).get(".")
    origin = lp.get("origin_main")
    fork = str((lp.get("fork") or {}).get(".") or "")
    base.update({
        "reachable": True, "ms": ms, "version": d.get("version") or d.get("node"),
        "ram_free_gb": d.get("ram_free_gb"), "cpu_pct": d.get("cpu_load_pct"),
        "head": (head or "")[:9], "origin": (origin or "")[:9],
        "fork": fork.replace("\t", " "), "tasks": lp.get("task_states") or {},
        "last_pull_ts": lp.get("ts"),
    })
    # 快照龄期：/status 里的 last_pull 可能是几小时前的，用它下判断会误判。
    # 2026-11-13 实测：bm-c 的分叉数字来自 15:18 的快照，7 小时后仍被当成"现在"。
    try:
        _t = datetime.fromisoformat(str(lp.get("ts"))[:19])
        base["pull_age_min"] = round((datetime.now() - _t).total_seconds() / 60)
    except Exception:
        base["pull_age_min"] = None
    # 代码是否真的到了最新：只认 head==origin 且 fork 为 0
    if head and origin:
        same = head == origin
        zero = re.match(r"^0\s+0", fork) is not None or fork in ("", "0  0")
        base["code"] = "最新" if (same and zero) else ("分叉 %s" % fork if fork else "落后")
    else:
        base["code"] = "未知"
    return base


def model_endpoints(timeout=6):
    """检查主控模型服务：本机与 tailnet 两个地址都要通（赋能机队的前提）。"""
    out = {}
    for tag, url in (("local", "http://127.0.0.1:11434/api/tags"),
                     ("tailnet", "http://100.75.133.10:11434/api/tags")):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                d = json.loads(r.read().decode("utf-8", "replace") or "{}")
            out[tag] = {"ok": True, "models": len(d.get("models") or [])}
        except Exception as e:
            out[tag] = {"ok": False, "why": type(e).__name__}
    return out


def survey(timeout=15):
    nodes = [n for n in load_nodes() if n.get("enabled")]
    with ThreadPoolExecutor(max_workers=5) as ex:
        return list(ex.map(lambda n: probe(n, timeout), nodes))


def judge(row):
    """规则判读：能由事实判定的，不交给模型。

    2026-11-13 实测：bm-c 已能推提交（远端有它的 commit），但 /status 的 last_pull
    还是 7.6 小时前的，判读仍写"拉不到新代码"——**拿陈旧快照下的结论是错的**。
    快照超过 60 分钟时，判读必须先声明"结论不可信"，再谈状态。
    """
    if row.get("state") == "未入网":
        return "未入网，等装机"
    if not row.get("reachable"):
        return "不可达（关机/断网/服务没起）"
    age = row.get("pull_age_min")
    if age is not None and age > 60:
        return "快照 %d 分钟前，结论不可信——发 --sync 刷新后再判" % age
    code = row.get("code") or ""
    if code.startswith("分叉") or code == "落后":
        return "拉不到新代码，产出会停"
    tasks = row.get("tasks") or {}
    running = [k for k, v in tasks.items() if str(v).lower() == "running"]
    if not running:
        return "代码已同步但没任务在跑"
    return "在跑：%s" % running[0]


def brief(rows):
    """把事实交给本地模型改写一句话；数字必须来自事实，否则作废。

    模型只做措辞，不做判断——判断已经在 judge() 里由规则给出。
    """
    facts = []
    for r in rows:
        facts.append("%s：%s，代码 %s" % (r.get("node"), judge(r), r.get("code")))
    text = "；".join(facts)
    try:
        import local_model as lm
        out = lm.generate(
            "把下面的事实改写成一句不超过 60 字的中文现状说明，只许复述，不许添加任何数字或结论：\n"
            + text, cls="triage", timeout=30, why="fleet-brief")
    except Exception:
        return text, "规则兜底（模型不可用）"
    out = (out or "").strip()
    if not out:
        return text, "规则兜底（模型空输出）"
    # 数字校验：句子里出现的数字必须都能在事实里找到
    nums_fact = set(re.findall(r"\d+", text))
    nums_out = set(re.findall(r"\d+", out))
    if not nums_out.issubset(nums_fact):
        return text, "规则兜底（模型引入了事实外的数字：%s）" % (nums_out - nums_fact)
    return out, "本地模型改写（数字已校验）"


def poke(node_id, task, why):
    """下发唤醒：契约必须合法（reason 含 enable-tasks，任务在白名单里）。"""
    node = next((n for n in load_nodes() if n.get("id") == node_id), None)
    if not node:
        return False, "没有这个节点：%s" % node_id
    allow = set(node.get("enable_tasks") or [])
    if task and task not in allow:
        return False, ("任务 %s 不在该机 enable_tasks 白名单（%s）——越界只会被 off-skip"
                       % (task, ", ".join(sorted(allow)) or "空"))
    ip = node.get("tailnet_ip")
    if not ip:
        return False, "无 tailnet IP"
    payload = {"reason": "enable-tasks: %s" % (why or "fleet-control"),
               "tasks": [task] if task else []}
    try:
        req = urllib.request.Request("http://%s:%d/poke" % (ip, PORT),
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8", "replace") or "{}")
        return bool(d.get("accepted")), json.dumps(d, ensure_ascii=False)
    except Exception as e:
        return False, type(e).__name__


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--poke", default=None, metavar="NODE")
    ap.add_argument("--task", default=None)
    ap.add_argument("--sync", default=None, metavar="NODE")
    ap.add_argument("--why", default="fleet-control")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    if a.poke:
        ok, info = poke(a.poke, a.task, a.why)
        print(("下发成功：" if ok else "下发失败：") + info)
        return 0 if ok else 2

    if a.sync:
        node = next((n for n in load_nodes() if n.get("id") == a.sync), None)
        if not node or not node.get("tailnet_ip"):
            print("没有这个节点或未入网：%s" % a.sync)
            return 2
        try:
            req = urllib.request.Request(
                "http://%s:%d/poke" % (node["tailnet_ip"], PORT),
                data=json.dumps({"reason": "enable-tasks: refresh origin ref (sync only)",
                                 "repos": ["."]}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                print(r.read().decode("utf-8", "replace"))
            return 0
        except Exception as e:
            print("同步失败：%s" % type(e).__name__)
            return 2

    rows = survey()
    # 落盘快照：这是"群控职责今天执行过"的证据（职责审计按它判龄期）
    try:
        sp = os.path.join(ROOT, "cph4", "fleet", "state", "fleet-control.json")
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        with open(sp, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds"), "rows": rows},
                      f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        print("== 群控（%s）==" % datetime.now().strftime("%m-%d %H:%M"))
        print("%-6s %-9s %-7s %-12s %-6s %s" % ("节点", "状态", "代码", "内存/CPU", "延迟", "判读"))
        for r in rows:
            st = "在线" if r.get("reachable") else r.get("state", "?")
            _pa = r.get("pull_age_min")
            if r.get("reachable") and _pa is not None and _pa > 60:
                st = "在线·陈旧"     # 状态面活着但代码很久没动：不能当成"正常在线"
            mem = "%.0fG/%.0f%%" % (r.get("ram_free_gb") or 0, r.get("cpu_pct") or 0) \
                if r.get("reachable") else "-"
            age = r.get("pull_age_min")
            tag = "" if age is None else ("（快照 %d 分钟前）" % age if age > 20 else "")
            print("%-6s %-9s %-7s %-12s %-6s %s%s" % (
                r.get("node"), st, r.get("code", "-"), mem,
                ("%dms" % r["ms"]) if r.get("ms") else "-", judge(r), tag))
        me = model_endpoints()
        print("模型端点：本机 %s｜tailnet %s"
              % ("通(%d 模型)" % me["local"]["models"] if me["local"].get("ok")
                 else "不通 " + str(me["local"].get("why")),
                 "通(%d 模型)" % me["tailnet"]["models"] if me["tailnet"].get("ok")
                 else "不通 " + str(me["tailnet"].get("why"))))
        if a.brief:
            txt, how = brief(rows)
            print("\n判读（%s）：%s" % (how, txt))
    bad = [r for r in rows if (not r.get("reachable"))
           or str(r.get("code", "")).startswith(("分叉", "落后"))]
    return 1 if bad else 0


def self_test():
    ok = total = 0

    def chk(n, c, d=""):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s %s" % ("ok  " if c else "FAIL", n, "" if c else d))

    # 判读规则
    chk("未入网 -> 等装机", "装机" in judge({"state": "未入网"}))
    chk("不可达 -> 说明原因", "不可达" in judge({"reachable": False}))
    chk("分叉 -> 拉不到新代码",
        "拉不到" in judge({"reachable": True, "code": "分叉 222 35"}))
    chk("同步但无任务在跑",
        "没任务" in judge({"reachable": True, "code": "最新", "tasks": {}}))
    chk("有 Running 任务 -> 指出",
        "在跑" in judge({"reachable": True, "code": "最新",
                        "tasks": {"HQ-ProductionClaim": "Running"}}))

    # 契约：白名单外的任务必须拒
    fake_nodes = {"nodes": [{"id": "bm-x", "tailnet_ip": None,
                             "enabled_tasks": [], "enable_tasks": ["HQ-ProductionClaim"]}]}
    global NODES
    old = NODES
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "n.json")
        json.dump(fake_nodes, open(p, "w"), ensure_ascii=False)
        NODES = p
        good, _ = poke("bm-x", "HQ-ProductionClaim", "t")
        chk("负控：白名单内但无 IP -> 拒", good is False)
        bad, why = poke("bm-x", "NotAllowlisted", "t")
        chk("负控：白名单外任务必须拒且说明", bad is False and "白名单" in why, why)
        none, why2 = poke("nope", "X", "t")
        chk("不存在的节点 -> 拒", none is False and "没有这个节点" in why2)
    NODES = old

    # 数字校验：模型引入事实外数字必须被拦（用纯函数复算同一规则）
    text = "bm-a：分叉 222 35，代码 分叉 222 35"
    out_bad = "有 999 台机器在线"
    nums_fact = set(re.findall(r"\d+", text))
    nums_out = set(re.findall(r"\d+", out_bad))
    chk("负控：事实外数字必须被识别", not nums_out.issubset(nums_fact), nums_out - nums_fact)

    print("\n[fleet_control] %d/%d" % (ok, total))
    return 0 if ok == total else 3


if __name__ == "__main__":
    sys.exit(main())
