#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""go_live_preflight.py - 开服前的机器自检（go-live.sh 调用；也可单独跑）。

2026-11-12 立（批次6 准备）。原来 go-live.sh 的前置检查完全不看 STATIONS.json：
在一台被判 blocked/offline/未装的机器上执行 --apply，会把该机变成第二个主控，
开始往队列里造卡派单。go-live 必须知道"我这台机现在该不该跑"。

输出 JSON：
  {"station": "control", "status": "ready", "runnable": true,
   "checks": [{"name": "...", "ok": true, "detail": "..."}], "blockers": [...]}

返回码：0 可跑 / 2 有硬阻断（缺 python、身份判定不出、工位状态不可跑……）
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

RUNNABLE = ("ready", "online", "network_ok_not_registered")


def check(force=False):
    checks, blockers = [], []

    def add(name, ok, detail="", hard=True):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok and hard:
            blockers.append("%s：%s" % (name, detail))

    add("python", sys.version_info >= (3, 8), sys.version.split()[0])
    add("仓库", os.path.isdir(os.path.join(ROOT, "cph4", "fleet")), ROOT)
    add("自驱入口", os.path.isfile(os.path.join(ROOT, "Tools", "fleet", "station_drive.py")))

    station, status = None, "unknown"
    try:
        import fleet_identity as fid
        r = fid.resolve()
        station = r.get("station")
        add("身份", bool(station), "依据=%s" % r.get("mode"))
    except Exception as e:
        add("身份", False, str(e)[:120])

    if station:
        try:
            with open(os.path.join(ROOT, "cph4", "fleet", "STATIONS.json"), encoding="utf-8-sig") as f:
                d = json.load(f)
            rec = [x for x in d.get("stations") or [] if x.get("id") == station]
            status = (rec[0].get("status") if rec else "unknown")
        except Exception as e:
            status = "read-error"
            add("工位表", False, str(e)[:120])

    if station and status not in RUNNABLE:
        if force:
            add("工位状态", True, "%s=%s（--force 越过）" % (station, status), hard=False)
        else:
            add("工位状态", False,
                "%s=%s，不是 %s；要跑请先改 STATIONS.json 的 status 并留痕"
                % (station, status, "/".join(RUNNABLE)))

    # 模型与网关只作提示：没起也能跑纯规则工序
    add("本机模型服务", True, "未检查（提示项）", hard=False)
    return {"station": station, "status": status,
            "runnable": not blockers, "force": bool(force),
            "checks": checks, "blockers": blockers}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = check(a.force)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("工位：%s（status=%s）→ %s"
              % (r["station"] or "未判定", r["status"], "可跑" if r["runnable"] else "不可跑"))
        for c in r["checks"]:
            print("  %s %-12s %s" % ("ok  " if c["ok"] else "FAIL", c["name"], c["detail"]))
        for b in r["blockers"]:
            print("  阻断：%s" % b)
    return 0 if r["runnable"] else 2


if __name__ == "__main__":
    sys.exit(main())
