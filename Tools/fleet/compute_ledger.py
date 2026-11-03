#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compute_ledger.py - BigCompute 的成本台账（定价的分母）。

为什么（2026-11-03 CEO「挨个执行」·COMPANY-DESIGN-PLAN 第 9 位）：
BigCompute 的设计第 3 问（第一件产物）写的是"成本台账"——每台机每小时的真实边际成本。
没有分母，19.9 的算力包就只能拍脑袋。本工具把**已实测的事实**落成台账，缺的照实写缺，
不拿"粗算"冒充会计：

  有证据：每台机的配置、实测占用小时（回执 seconds 求和）、完成的卡数、可再派槽位、
          机队每小时成本常数（COST-RATES.json，缺省 0.6 元/机时，来源默认值不是实测）
  没证据：电费单价、购入价/折旧年限、云端同规格租价 → 写 missing，并给出补法

用法：python3 Tools/fleet/compute_ledger.py [--json] [--out PATH]
Exit: 0 正常；1 车道表读不了。
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
RECEIPTS = os.path.join(FLEET, "queue-receipts")
COST = os.path.join(FLEET, "COST-RATES.json")
DEFAULT_OUT = os.path.join(FLEET, "company", "bigcompute", "CAPACITY-LEDGER-v1.json")
DEFAULT_RATE = 0.6  # 元/机器小时（粗算，非会计口径）

sys.path.insert(0, HERE)


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def jlines(p):
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


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)

    try:
        import fleet_lane as fl
    except Exception as e:
        print("车道表读不了：%s" % e, file=sys.stderr)
        return 1

    rate_cfg = jload(COST, {}) or {}
    rate = float(rate_cfg.get("cny_per_hour") or DEFAULT_RATE)
    rate_source = ("COST-RATES.json" if rate_cfg.get("cny_per_hour") else
                   "默认值 %.2f（非实测，仅为电费+折旧粗算）" % DEFAULT_RATE)

    # 实测占用：回执里的 seconds 是执行器自己报的墙上时间，按 node 汇总。
    secs = defaultdict(float)
    done = defaultdict(int)
    try:
        for n in os.listdir(RECEIPTS):
            if not n.endswith(".json"):
                continue
            d = jload(os.path.join(RECEIPTS, n), {}) or {}
            if not isinstance(d, dict):
                continue
            node = d.get("node")
            if not node:
                continue
            try:
                secs[node] += float(d.get("seconds") or 0)
            except (TypeError, ValueError):
                pass
            if str(d.get("outcome") or "").upper() == "OK":
                done[node] += 1
    except FileNotFoundError:
        pass

    # 在册配置 + 实测压榨度（复用 squeeze 的保底口径，不另立阈值）
    import squeeze
    rows = []
    for node, v in sorted(fl.LANES.items()):
        floor_gb = squeeze.reserve(node)
        st = {}
        ms = jload(os.path.join(FLEET, "dispatcher", "MASTER-STATE.json"), {}) or {}
        st = (ms.get("lanes") or {}).get(node, {}) or {}
        ram_free = st.get("ram_free_gb")
        online = st.get("hb_age_s") is not None and float(st.get("hb_age_s") or 1e9) <= 600
        slots = None
        if isinstance(ram_free, (int, float)):
            slots = max(0, int((float(ram_free) - floor_gb))) if online else 0
        hours = round(secs.get(node, 0.0) / 3600.0, 2)
        rows.append({
            "node": node,
            "name_cn": v.get("name_cn"),
            "enabled": bool(v.get("enabled")),
            "role_class": v.get("role_class") or "worker",
            "capacity": {"ram_gb": v.get("ram_gb"), "vram_gb": v.get("vram_gb"),
                         "cuda": bool(v.get("cuda")), "caps": v.get("caps") or []},
            "measured": {"occupied_hours": hours, "ok_cards": done.get(node, 0),
                         "ram_free_gb": ram_free, "spare_slots": slots},
            "cost_cny_at_rate": round(hours * rate, 2),
        })

    total_hours = round(sum(r["measured"]["occupied_hours"] for r in rows), 2)
    res = {
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "purpose": "BigCompute 定价分母：每台机每小时成本与实测占用（非会计口径）",
        "assumptions": {
            "rate_cny_per_machine_hour": rate,
            "rate_source": rate_source,
            "measured_window": "queue-receipts 全量（回执 seconds 求和），不是账单",
        },
        "nodes": rows,
        "totals": {
            "occupied_hours": total_hours,
            "cost_cny_at_rate": round(total_hours * rate, 2),
            "sellable_slots_now": sum(r["measured"]["spare_slots"] or 0 for r in rows),
        },
        "missing_evidence": [
            {"item": "电费单价", "why": "真边际成本的另一半，当前无任何实测账单",
             "how_to_fix": "读取本机/机队电表或按功率×电价估算，需 CEO 提供电价"},
            {"item": "购入价与折旧年限", "why": "机器折旧未入账，rate 只是粗算",
             "how_to_fix": "买机发票 + 按 3 年直线折旧"},
            {"item": "云端同规格租价", "why": "对外报价要有对照组，否则 19.9 无锚点",
             "how_to_fix": "取 3 家云厂商 4090/A100 按小时价，落一份对照表"},
        ],
        "pricing_note": "本台账只给分母；19.9 的售价与毛利在缺上述三项前不得对外承诺。",
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    print("%-6s %-10s %10s %8s %8s %10s" % ("node", "role", "占用h", "OK卡", "空槽", "成本¥"))
    for r in rows:
        print("%-6s %-10s %10.2f %8d %8s %10.2f" % (
            r["node"], r["role_class"][:10], r["measured"]["occupied_hours"],
            r["measured"]["ok_cards"],
            "-" if r["measured"]["spare_slots"] is None else r["measured"]["spare_slots"],
            r["cost_cny_at_rate"]))
    print("合计：占用 %.2f 机时 / ¥%.2f（费率 %.2f，来源：%s）；当前可售槽位 %d"
          % (total_hours, total_hours * rate, rate, rate_source, res["totals"]["sellable_slots_now"]))
    print("缺证据 %d 项（电费/折旧/云对照）——补齐前报价不得对外承诺"
          % len(res["missing_evidence"]))
    print("-> %s" % os.path.relpath(a.out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))