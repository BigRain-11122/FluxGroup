#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_team.py - 每台机的智能体专家席运行器 + 本地模型通路体检。

CEO 2026-11-11：「每个机器都要有自己的智能体专家团队，非常细分，排好各自的模块，
走主控和算力大脑的本地大模型能力，要打通通路。」

三件事：
  1 列席位   python3 Tools/fleet/agent_team.py --station visual --list
  2 跑席位   python3 Tools/fleet/agent_team.py --station visual --run V-KF --input "..."
  3 验通路   python3 Tools/fleet/agent_team.py --probe      # 端点阶梯 + 各 cls 能不能落到模型

通路规则（不许绕）：
  * 一律经 `local_model.generate(cls=...)`，走 本机(0) → 算力大脑(1) → 主控(2) 阶梯。
  * 模型不可用时不编：输出带 degraded=true、ok=false，交回规则或人。
  * 每次调用写一行审计到 cph4/fleet/rt/<工位>/team.jsonl（座位/耗时/端点/是否降级）。

返回码：0 正常 / 1 有席位降级 / 2 通路断（无端点或无模型）/ 3 自检失败
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")

sys.path.insert(0, HERE)
import local_model as lm  # noqa: E402
import station_shards as ss  # noqa: E402

CLS_OK = ("triage", "review", "creative", "deep")


def teams(root=None):
    base = os.path.join(root, "cph4", "fleet") if root else F
    with open(os.path.join(base, "AGENT-TEAMS-v1.json"), encoding="utf-8") as f:
        return json.load(f)["teams"]


def seat_of(station, seat_id, root=None):
    for s in teams(root).get(station) or []:
        if s["id"] == seat_id:
            return s
    return None


def build_prompt(seat, payload):
    spec = seat.get("out") or {}
    want = ("只输出 JSON，键：%s" % ",".join(spec.get("keys") or [])) if spec.get("type") == "json" \
        else "只输出正文，不超过 %s 字" % spec.get("max", 200)
    return ("你是%s，只管一件事：%s。\n"
            "硬规矩：只用输入里的事实，不许编；不确定就写不确定，不要凑。\n"
            "%s\n\n输入：\n%s" % (seat["name"], seat["duty"], want, payload))


def judge(seat, text):
    """按席位声明验输出。返回 (ok, why)。"""
    spec = seat.get("out") or {}
    t = (text or "").strip()
    if not t:
        return False, "空输出"
    if spec.get("type") == "json":
        s, e = t.find("{"), t.rfind("}")
        if s < 0 or e <= s:
            return False, "不是 JSON"
        try:
            o = json.loads(t[s:e + 1])
        except Exception:
            return False, "JSON 解析失败"
        keys = spec.get("keys") or []
        miss = [k for k in keys if k not in o]
        if miss:
            return False, "缺键:" + ",".join(miss)
        if all(o.get(k) in (None, "", [], {}) for k in keys):
            return False, "全部为空（降级）"
        return True, "ok"
    n = spec.get("max") or 200
    if len(t) > n:
        return False, "超长 %d>%d" % (len(t), n)
    return True, "ok"


def audit(station, row, root=None):
    ss.append_log(station, {"kind": "agent-team", **row}, root)


def run_seat(station, seat_id, payload, root=None):
    seat = seat_of(station, seat_id, root)
    if not seat:
        return {"ok": False, "why": "席位不存在: %s" % seat_id, "degraded": True}
    t0 = time.time()
    endpoint = lm.endpoint()
    text = ""
    try:
        text = lm.generate(build_prompt(seat, payload), cls=seat.get("cls") or "triage",
                           timeout=120, why="agent-team:%s" % seat_id)
    except Exception as e:
        text = ""
        audit(station, {"seat": seat_id, "err": str(e)[:120]}, root)
    ok, why = judge(seat, text)
    row = {"ts": datetime.now().isoformat(timespec="seconds"), "station": station,
           "seat": seat_id, "cls": seat.get("cls"), "endpoint": endpoint,
           "ms": int((time.time() - t0) * 1000), "ok": ok, "why": why,
           "degraded": (not ok), "chars": len(text or "")}
    audit(station, row, root)
    return {**row, "text": (text or "").strip()}


def _tags(url, timeout=1.5):
    try:
        with urllib.request.urlopen(url + "/api/tags", timeout=timeout) as r:
            d = json.loads(r.read() or b"{}")
        return [m.get("name") for m in (d.get("models") or []) if m.get("name")]
    except Exception:
        return []


def probe(root=None):
    """通路体检：端点阶梯 + 每个 cls 能不能落到已装模型。"""
    here = lm.local_station()
    gs = lm.gateways()
    print("本机工位: %s" % here)
    print("端点阶梯（本地优先）:")
    alive, models_any = [], []
    for i, u in enumerate(gs):
        tags = _tags(u)
        print("  %d. %-32s %s%s" % (i, u, "可用" if tags else "不通",
                                    ("（%d 个模型）" % len(tags)) if tags else ""))
        if tags:
            alive.append(u)
            models_any.extend(tags)
    print("\n席位 → 模型档 → 能否落地:")
    duties = lm._duties() or {}
    rc = 0
    station = here or "control"
    for seat in teams(root).get(station) or []:
        cls = seat.get("cls") or "triage"
        want_seat = lm.seat_of(cls)
        cfg = duties.get(want_seat) or {}
        model = cfg.get("model") or "(未配置)"
        hit = any(model.split(":")[0] in (m or "") for m in models_any)
        print("  %-10s cls=%-8s seat=%-6s model=%-22s %s" % (
            seat["id"], cls, want_seat, model, "OK" if hit else "缺"))
        if not hit:
            rc = max(rc, 2)
    if not alive:
        rc = max(rc, 2)
    print("\n结论：%s" % ("通路可用" if rc == 0 else "通路不完整（缺端点或缺模型）"))
    return rc


def self_test():
    import tempfile
    ok = total = 0

    def chk(name, cond):
        nonlocal ok, total
        total += 1
        ok += 1 if cond else 0
        print("%s %s" % ("ok  " if cond else "FAIL", name))

    t = teams()
    chk("五台机都有团队", set(t) == set(ss.STATIONS))
    chk("席位不重复且 id 唯一",
        all(len({s["id"] for s in v}) == len(v) for v in t.values()))
    chk("所有 cls 合法",
        all(s.get("cls") in CLS_OK for v in t.values() for s in v))
    chk("json 席位都给了 keys",
        all((s["out"].get("keys") or []) for v in t.values() for s in v
            if s["out"].get("type") == "json"))
    chk("text 席位都给了 max",
        all(s["out"].get("max") for v in t.values() for s in v
            if s["out"].get("type") == "text"))

    seat = {"id": "X", "name": "x", "duty": "d", "cls": "triage",
            "out": {"type": "json", "keys": ["a", "b"]}, "judge": {"type": "json"}}
    chk("judge 接受合法 JSON", judge(seat, '{"a":1,"b":2}')[0] is True)
    chk("judge 拒空输出", judge(seat, "")[0] is False)
    chk("judge 拒缺键", judge(seat, '{"a":1}')[0] is False)
    chk("judge 拒全空（降级不冒充）", judge(seat, '{"a":null,"b":""}')[0] is False)
    chk("judge 会从噪声里取 JSON", judge(seat, '好的\n{"a":1,"b":2}\n完')[0] is True)

    tseat = {"out": {"type": "text", "max": 5}}
    chk("text 超长拒", judge(tseat, "123456")[0] is False)

    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "cph4", "fleet"))
        json.dump({"teams": t}, open(os.path.join(td, "cph4", "fleet", "AGENT-TEAMS-v1.json"), "w"),
                  ensure_ascii=False)
        chk("临时根可读团队", len(teams(td)) == 5)

    print("[agent_team] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", choices=list(ss.STATIONS))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run")
    ap.add_argument("--input", default="")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.probe:
        return probe()
    station = a.station or lm.local_station() or "control"
    if a.list or not a.run:
        ts = teams().get(station) or []
        print("== %s 智能体团队（%d 席）==" % (station, len(ts)))
        for s in ts:
            print("  %-10s %-8s cls=%-9s %s" % (s["id"], s["name"], s.get("cls"), s["duty"][:34]))
        return 0
    r = run_seat(station, a.run, a.input)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
