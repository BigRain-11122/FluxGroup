#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tailnet_audit.py - 机队 tailnet 体检（在线/直连/密钥到期），把"策略"变成可判据。

为什么（2026-11-22 CEO「tailscal 给我设置好并做好最科学的策略，整个机队」）：
  以前没有任何一环在看 tailnet —— bm-b 掉线 11 天没人报、节点密钥 2027-03 统一到期
  （到期当天全机队同时断连且不会自愈）、bm-a 一直走 DERP 中继 391ms 也没人量。
  这份工具只回答三个可核事实，不讲故事：
    1) 每台机在不在线（online + last_seen）
    2) 连接质量（直连 or 中继，中继名与延迟）
    3) 密钥还有几天到期（<30 天判 WARN，<7 天判 CRIT）

用法：python3 Tools/fleet/tailnet_audit.py [--json] [--no-ping]
判据：rc=0 全绿；rc=1 有 WARN/CRIT（报告型，不是故障）。
落盘：cph4/fleet/state/tailnet-audit.json
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "tailnet-audit.json")
EXPIRY_WARN_DAYS = 30
EXPIRY_CRIT_DAYS = 7
OFFLINE_WARN_HOURS = 24
STALE_REMOVE_DAYS = 7


def ts_bin():
    p = shutil.which("tailscale")
    if p:
        return p
    for c in ("/Applications/Tailscale.app/Contents/MacOS/Tailscale",
              r"C:\Program Files\Tailscale\tailscale.exe"):
        if os.path.exists(c):
            return c
    return None


def run(cmd, timeout=25):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def run_json(cmd, timeout=25):
    """只要 stdout：status --json 的报文没有结尾换行，混入 stderr 会让 json 解析炸
    （2026-11-22 首跑实锚：'Extra data: line 273'）。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           errors="replace")
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except Exception as e:
        return 1, "", str(e)


def parse_ts(s):
    """tailscale time -> aware datetime"""
    if not s or s.startswith("0001"):
        return None
    s = s.replace("Z", "+00:00")
    m = re.match(r"^(.*?)(\.\d+)?([+-]\d\d:\d\d)?$", s)
    base = s
    if m and m.group(2):
        base = s.replace(m.group(2), "")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(base, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def peer_link(ts, ip, do_ping):
    """直连 or 中继。ping 失败返回 unknown（不冒充坏）。"""
    if not do_ping:
        return {"kind": "unprobed"}
    rc, out = run([ts, "ping", "-c", "1", ip], timeout=12)
    if rc != 0 and "pong" not in out:
        return {"kind": "unknown", "raw": out.strip()[:120]}
    if "via DERP" in out:
        m = re.search(r"via DERP\(([^)]+)\)", out)
        lat = re.search(r" in ([\d.]+)\s*ms", out)
        return {"kind": "relay", "relay": m.group(1) if m else "?",
                "ms": float(lat.group(1)) if lat else None}
    m = re.search(r"via ([0-9.]+):(\d+)", out)
    lat = re.search(r" in ([\d.]+)\s*ms", out)
    return {"kind": "direct", "addr": m.group(0)[4:] if m else "?",
            "ms": float(lat.group(1)) if lat else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-ping", action="store_true")
    a = ap.parse_args()

    ts = ts_bin()
    if not ts:
        print("tailscale CLI 缺失", file=sys.stderr)
        return 2
    rc, out, err = run_json([ts, "status", "--json"])
    if rc != 0:
        print("tailscale status 失败: " + (err or out)[:200], file=sys.stderr)
        return 2
    try:
        d = json.loads(out)
    except Exception as e:
        print("status json 解析失败: %s" % e, file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    self_ = d.get("Self") or {}
    names = [ (p.get("HostName") or "") for p in (d.get("Peer") or {}).values() ]
    self_name = self_.get("HostName") or ""
    dup_names = {n for n in names if names.count(n) > 1 or (n and n == self_name)}
    rows, flags = [], []

    def expiry_note(exp):
        dt = parse_ts(exp)
        if not dt:
            return None, "never"
        days = round((dt - now).total_seconds() / 86400, 1)
        return days, dt.date().isoformat()

    sd, sdate = expiry_note(self_.get("KeyExpiry", ""))
    rows.append({"node": self_.get("HostName"), "ip": (self_.get("TailscaleIPs") or [None])[0],
                 "os": self_.get("OS"), "online": True, "self": True,
                 "expiry_days": sd, "expiry_date": sdate, "link": {"kind": "self"}})

    for p in (d.get("Peer") or {}).values():
        ip = (p.get("TailscaleIPs") or [""])[0]
        days, date = expiry_note(p.get("KeyExpiry", ""))
        last = parse_ts(p.get("LastSeen", ""))
        off_h = round((now - last).total_seconds() / 3600, 1) if (last and not p.get("Online")) else 0
        row = {"node": p.get("HostName"), "ip": ip, "os": p.get("OS"),
               "online": bool(p.get("Online")), "offline_hours": off_h,
               "expiry_days": days, "expiry_date": date,
               "tags": p.get("Tags") or [], "link": {"kind": "offline"}}
        if p.get("Online"):
            row["link"] = peer_link(ts, ip, not a.no_ping)
        rows.append(row)

    # 判据
    for r in rows:
        if r.get("self"):
            continue
        if r["online"]:
            lk = r["link"]
            if lk.get("kind") == "relay":
                flags.append({"node": r["node"], "level": "WARN", "code": "RELAY",
                              "why": "走中继 DERP(%s) %sms，无直连" % (lk.get("relay"), lk.get("ms"))})
            elif lk.get("kind") == "unknown":
                flags.append({"node": r["node"], "level": "WARN", "code": "UNPROBED",
                              "why": "在线但 ping 未证实（不冒充直连）"})
        else:
            # 只有"与本机同名/与在线节点重名"的才算废弃节点可删；
            # 真机器停机是 OFFLINE（要去找人开机），不能建议删除（2026-11-22 首跑把 bm-b 误判成可删）
            dup = r["node"] in dup_names
            if dup and r["offline_hours"] >= STALE_REMOVE_DAYS * 24:
                flags.append({"node": r["node"], "level": "WARN", "code": "STALE-NODE",
                              "why": "与在线节点重名的旧节点，离线 %.0f 天，可在管理台删除"
                                     % (r["offline_hours"] / 24)})
            elif r["offline_hours"] >= STALE_REMOVE_DAYS * 24:
                flags.append({"node": r["node"], "level": "CRIT", "code": "OFFLINE-DOWN",
                              "why": "真机停机 %.0f 天（不是废弃节点，要查开机/服务）"
                                     % (r["offline_hours"] / 24)})
            elif r["offline_hours"] >= OFFLINE_WARN_HOURS:
                flags.append({"node": r["node"], "level": "WARN", "code": "OFFLINE",
                              "why": "离线 %.1f 小时" % r["offline_hours"]})
        if r["expiry_days"] is not None:
            if r["expiry_days"] <= EXPIRY_CRIT_DAYS:
                flags.append({"node": r["node"], "level": "CRIT", "code": "EXPIRY",
                              "why": "密钥 %.1f 天后到期（到期即断连且不自愈）" % r["expiry_days"]})
            elif r["expiry_days"] <= EXPIRY_WARN_DAYS:
                flags.append({"node": r["node"], "level": "WARN", "code": "EXPIRY",
                              "why": "密钥 %.1f 天后到期" % r["expiry_days"]})

    report = {"ts": now.isoformat(timespec="seconds"), "nodes": rows, "flags": flags,
              "magicdns": d.get("MagicDNSSuffix"),
              "tailnet_magicdns_enabled": (d.get("CurrentTailnet") or {}).get("MagicDNSEnabled")}
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
    except Exception:
        pass

    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print("== tailnet 体检 · MagicDNS=%s ==" % report["magicdns"])
        for r in rows:
            lk = r["link"]
            if lk.get("kind") == "self":
                link = "本机"
            elif lk.get("kind") == "direct":
                link = "直连 %sms" % lk.get("ms")
            elif lk.get("kind") == "relay":
                link = "中继%s %sms" % (lk.get("relay"), lk.get("ms"))
            elif lk.get("kind") == "offline":
                link = "离线 %.0fh" % r["offline_hours"]
            else:
                link = "未证实"
            exp = "永不过期" if r["expiry_days"] is None else "%.0f天后到期" % r["expiry_days"]
            print("  %-8s %-15s %-7s %-16s %s" % (r["node"], r["ip"], r["os"],
                                                  "在线" if r["online"] else "离线", link + " | " + exp))
        if flags:
            print("-- 判据命中 --")
            for f in sorted(flags, key=lambda x: (x["level"] != "CRIT", x["node"])):
                print("  [%s] %-8s %-12s %s" % (f["level"], f["node"], f["code"], f["why"]))
        else:
            print("  全部在线、全直连、密钥充裕")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
