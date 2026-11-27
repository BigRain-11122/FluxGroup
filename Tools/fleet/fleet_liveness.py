#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_liveness.py - 一台机器「活不活」的唯一判据：合并三条证据通道。

为什么（2026-11-27 实测）：机队不是没通，是「三条腿各走各的，主控只认一条」——
  * bm-a（公司生产力机）每 60 秒往 NATS 发心跳（hb.bm-a / $KV.FLEET_STATE.state.bm-a），
    但主控侧接收端 com.fluxgroup.fleetbus 从 11-15 掉线，落盘冻结，于是判成「70 小时没回执」；
  * bm-c（传家宝）不发 NATS，靠 bmc_chain_publish 每轮把 _last_lane_bm-c.json /
    autodrive-hb-bm-c.json 提交上 git，主控却只看本地 rt/<工位>/receipts 的 mtime，
    于是把 15:36 刚推过提交的机器判成 offline；
  * STATIONS.json 里的 status 是静态申报值（visual 写着 offline），从没人按实况改过。
结果同一天三份结论互相矛盾，主控据此派单就是错的。

判据纪律：
  * 只认「机器自己写的时间戳」，不认本机 checkout 的 mtime——git pull 会把 mtime 刷成
    现在，用 mtime 判活等于给死机器续命。
  * 每条证据都带来源（nats / git-receipt / local-rt / self），主控能复核是哪条腿活着。
  * 缺证据就是缺证据：不猜、不用静态申报值兜底成 alive。

时间口径：机队在同一个时区（Asia/Shanghai）。带 Z 或 ts_utc_ms 的按 UTC 算；
裸时间戳（bm-a/bm-c 的 Windows 侧写法）按本机挂钟（+08:00）算。

用法：
  python3 Tools/fleet/fleet_liveness.py            # 人读一屏
  python3 Tools/fleet/fleet_liveness.py --json     # 机读（落 state/fleet-liveness.json）
  python3 Tools/fleet/fleet_liveness.py --self-test
返回码：0 全部有新鲜证据 / 1 有 DARK 或 STALE（需主控过问）
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "cph4", "fleet", "state")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")

# 阈值（小时）。不是拍脑袋：bm-a/bm-c 的心跳节拍实测 60s~15min，
# 1 小时没证据 = 至少漏了 4 个节拍；24 小时以上按「没人管」处理。
ALIVE_H = 1.0
WARM_H = 6.0
STALE_H = 24.0

# 工位 → 机队代号。OS-MATRIX / AUTONOMY-CONFIG / STATIONS 三份件的键都是工位名，
# 而心跳与回执只用 bm-x 代号，两边必须在这儿对上，否则 NATS/git 两条腿永远读空。
# 依据：OS-MATRIX machines[].hostname（DASHENG/FLUXGROUP/BIGMONEY）+ tailscale 实测 IP；
# brain=bm-d 取自 AUTONOMY-CONFIG capacity.blocked_active.bigcompute「bm-d 未入网」。
STATION_NODE = {"control": "bm-m", "delivery": "bm-a", "visual": "bm-c",
                "audio": "bm-b", "brain": "bm-d"}

# 代号 → 尾网设备名（2026-11-27 实锚）：MacBook 的 Tailscale 设备名是 bm-m-1，
# 因为 bm-m 被一台 10-29 遗留、离线 29 天的旧节点占着，改不了别人的设备只能让位。
# 代号 bm-m 仍是逻辑 id（心跳 hb.bm-m、回执 _last_lane_bm-m、队列都按它），
# 所以别名只在这一层用；设备名再变也只改这一行。
TAILNET_ALIAS = {"bm-m": "bm-m-1"}


def _now():
    return time.time()


def _parse_ts(text):
    """把各种写法的时间戳变成 epoch 秒；解析不了返回 None。"""
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    if s.endswith("Z"):
        try:
            return datetime.strptime(s[:-1].split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=timezone.utc).timestamp()
        except Exception:
            return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            # 裸时间戳按本机挂钟（机队同为 Asia/Shanghai），不用 UTC 解释，
            # 否则每台 Windows 都会凭空年轻 8 小时。
            return time.mktime(time.strptime(s.split("+")[0].strip(), fmt))
        except Exception:
            continue
    return None


def _read_json(p):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return None


def _nats_evidence(node):
    """NATS 心跳落盘（fleet_bus 写的 node-state/<node>.json）。"""
    d = _read_json(os.path.join(STATE, "node-state", node + ".json"))
    if not d:
        return None
    ep = None
    if d.get("ts_utc_ms"):
        ep = float(d["ts_utc_ms"]) / 1000.0
    else:
        ep = _parse_ts(d.get("ts"))
    if ep is None:
        return None
    return {"source": "nats", "epoch": ep, "seq": d.get("seq"),
            "host": d.get("host"), "path": "state/node-state/%s.json" % node}


def _git_receipt_evidence(node):
    """git 回执通道（bm-c 的节拍脚本写、随提交上链）。取最新一条。"""
    best = None
    for name in ("_last_lane_%s.json" % node, "autodrive-hb-%s.json" % node):
        p = os.path.join(RECEIPTS, name)
        d = _read_json(p)
        if not d:
            continue
        ep = _parse_ts(d.get("ts"))
        if ep is None:
            continue
        if best is None or ep > best["epoch"]:
            best = {"source": "git-receipt", "epoch": ep, "state": d.get("state"),
                    "note": d.get("note"), "path": "queue-receipts/" + name}
    return best


def _local_rt_evidence(station):
    """本机 rt/<工位>/receipts 的 mtime（老判据，保留但降级为「本机视角」）。"""
    pat = os.path.join(ROOT, "cph4", "fleet", "rt", station, "receipts", "*")
    ts = [os.path.getmtime(p) for p in glob.glob(pat) if os.path.exists(p)]
    if not ts:
        return None
    return {"source": "local-rt", "epoch": max(ts),
            "path": "rt/%s/receipts/" % station}


def verdict_of(age_h):
    if age_h is None:
        return "NO-EVIDENCE"
    if age_h <= ALIVE_H:
        return "ALIVE"
    if age_h <= WARM_H:
        return "WARM"
    if age_h <= STALE_H:
        return "STALE"
    return "DARK"


def _tailnet_map(timeout=3.0):
    """尾网在线表。键 = 小写设备名 或 "ip:<地址>"，另带 "__self__" = 本机设备名。

    注意：在线 ≠ 活着。bm-b 实测 online=True 却 249 小时零证据，说明网络层通了、
    应用层没人干活——这两种故障的处理办法完全不同（一个要通电，一个要起任务），
    所以这里只当旁证，绝不参与 verdict 的 ALIVE 判定。
    """
    try:
        out = subprocess.run(
            ["curl", "-s", "--max-time", str(int(timeout)),
             "--unix-socket", "/var/run/tailscaled.socket",
             "http://local-tailscaled.sock/localapi/v0/status"],
            capture_output=True, text=True, timeout=timeout + 2).stdout
        d = json.loads(out or "{}")
    except Exception:
        return {}

    def _ips(v):
        return [str(i).split("/")[0] for i in (v.get("TailscaleIPs") or []) if i]

    selfd = d.get("Self") or {}
    m = {"__self__": (selfd.get("HostName") or "").strip().lower()}
    for ip in _ips(selfd):
        m["ip:" + ip] = True
    for v in (d.get("Peer") or {}).values():
        name = (v.get("HostName") or "").strip().lower()
        online = bool(v.get("Online"))
        if name:
            m[name] = online
        for ip in _ips(v):
            m["ip:" + ip] = online
    return m


def _roster_ip(node, root=ROOT):
    """花名册里的尾网 IP（Tools/fleet-nodes.json）。解析不到返回 None。"""
    d = _read_json(os.path.join(root, "Tools", "fleet-nodes.json")) or {}
    for r in d.get("nodes") or []:
        if str(r.get("id") or "").strip().lower() == (node or "").lower():
            ip = str(r.get("tailnet_ip") or "").strip()
            return ip if ip and "PENDING" not in ip.upper() else None
    return None


def _tailnet_online(node, m, root=ROOT):
    """代号 → 尾网在线（True/False/None=尾网表里查不到，不等于离线）。

    三级解析：自保 → 设备名（含 TAILNET_ALIAS）→ 花名册 IP。
    为什么不写成 `node == m["__self__"]`：代号是逻辑 id，设备名可能因重名被尾网
    去重成 <id>-1；两者不相等时本机会被读成「尾网离线」（2026-11-27 实锚：
    设备名 bm-m-1、代号 bm-m，主控在判活屏上显示离线，而心跳是好的）。
    """
    if not m:
        return None
    node = (node or "").strip().lower()
    names = [n for n in {node, TAILNET_ALIAS.get(node, node)} if n]
    if m.get("__self__") in names:
        return True                      # 本机不在 Peer 表里，别把自己读成离线
    for n in names:
        if n in m:
            return m[n]
    ip = _roster_ip(node, root)
    if ip and ("ip:" + ip) in m:
        return m["ip:" + ip]
    return None


def _paused_map(root=ROOT):
    """CEO 让路/暂停标记（fleet-control.json 的 paused_by_ceo）。

    纪律（2026-11-07 实锚）：机器停了先找当天的 CEO 令，再谈根因。bm-b 自 11-14
    起就是 CEO 令「未开机」暂停，11-27 尾网已在线但任务未恢复——把它报成故障，
    等于拿 CEO 的决定当机器缺陷。
    """
    d = _read_json(os.path.join(root, "cph4", "fleet", "state", "fleet-control.json")) or {}
    out = {}
    for r in d.get("rows") or []:
        if r.get("node"):
            out[r["node"]] = bool(r.get("paused_by_ceo"))
    return out


def snapshot(root=ROOT):
    matrix = _read_json(os.path.join(root, "cph4", "fleet", "OS-MATRIX-v1.json")) or {}
    machines = matrix.get("machines") or {}
    stations = (_read_json(os.path.join(root, "cph4", "fleet", "STATIONS.json")) or {}).get("stations") or []
    by_station = {s["id"]: s for s in stations}
    here = os.uname().nodename if hasattr(os, "uname") else ""

    rows = []
    tailnet = _tailnet_map()
    paused = _paused_map(root)
    for key, m in machines.items():
        station = m.get("station") or key
        st = by_station.get(station) or {}
        node = STATION_NODE.get(station) or m.get("node") or key
        ev = []
        if node == "bm-m":
            ev.append({"source": "self", "epoch": _now(), "path": "本机"})
        for fn in (_nats_evidence, _git_receipt_evidence):
            e = fn(node)
            if e:
                ev.append(e)
        e = _local_rt_evidence(station)
        if e:
            ev.append(e)
        # 同一时刻多条证据时取最新那条，但把所有来源都留下供复核
        best = max(ev, key=lambda x: x["epoch"]) if ev else None
        age_h = round((_now() - best["epoch"]) / 3600.0, 2) if best else None
        declared = m.get("os") == "unverified" and "NOT-INSTALLED" or (st.get("status") or "unknown")
        verdict = "NOT-INSTALLED" if (st.get("status") == "not_installed") else verdict_of(age_h)
        net = _tailnet_online(node, tailnet, root)
        if net and verdict in ("STALE", "DARK", "NO-EVIDENCE"):
            # 网通了但没人干活：不是断电，是任务没起/心跳没开，处置办法完全不同。
            verdict = "ONLINE-NO-AGENT"
        if paused.get(node) and verdict in ("STALE", "DARK", "NO-EVIDENCE", "ONLINE-NO-AGENT"):
            verdict = "PAUSED-BY-CEO"
        rows.append({
            "node": node, "station": station,
            "machine": m.get("name") or st.get("machine") or node,
            "hostname": m.get("hostname"),
            "declared_status": declared,
            "tailnet_online": net,
            "age_h": age_h,
            "verdict": verdict,
            "best_source": best["source"] if best else None,
            "evidence": [{k: v for k, v in e.items() if k != "epoch"} for e in ev],
        })
    order = {"ALIVE": 0, "WARM": 1, "PAUSED-BY-CEO": 2, "STALE": 3, "DARK": 4,
             "ONLINE-NO-AGENT": 5, "NO-EVIDENCE": 6, "NOT-INSTALLED": 7}
    rows.sort(key=lambda r: (order.get(r["verdict"], 9), r["station"]))
    return {"ts": datetime.now().isoformat(timespec="seconds"),
            "thresholds_h": {"alive": ALIVE_H, "warm": WARM_H, "stale": STALE_H},
            "nodes": rows}


def render(snap):
    out = ["== 机队判活（三通道合并：NATS / git 回执 / 本机 rt）==",
           "%-6s %-10s %-14s %-11s %-8s %-7s %-7s %s" % (
               "节点", "工位", "机器", "判定", "证据龄", "来源", "尾网", "静态申报")]
    for r in snap["nodes"]:
        age = "-" if r["age_h"] is None else "%.2fh" % r["age_h"]
        net = "-" if r.get("tailnet_online") is None else ("在线" if r["tailnet_online"] else "离线")
        out.append("%-6s %-10s %-14s %-11s %-8s %-7s %-7s %s" % (
            r["node"], r["station"], (r["machine"] or "")[:14], r["verdict"], age,
            r["best_source"] or "-", net, r["declared_status"]))
        for e in r["evidence"]:
            out.append("        └ %-12s %s" % (e["source"], e.get("path") or ""))
    bad = [r for r in snap["nodes"] if r["verdict"] in ("STALE", "DARK", "NO-EVIDENCE",
                                                        "ONLINE-NO-AGENT")]
    out.append("")
    if bad:
        out.append("需主控过问：")
        for r in bad:
            hint = {"ONLINE-NO-AGENT": "网通但无 agent/心跳：要起任务，不是通电",
                    "DARK": "连网都不通或久无任何证据：先确认电源/网络"}.get(r["verdict"], "")
            out.append("  - %s（%s）：%s，证据龄 %s，最佳来源 %s%s" % (
                r["station"], r["node"], r["verdict"],
                "-" if r["age_h"] is None else "%.1fh" % r["age_h"], r["best_source"] or "无",
                ("；" + hint) if hint else ""))
    else:
        out.append("除按令暂停者外，全部节点有 6 小时内的证据。")
    paused_rows = [r for r in snap["nodes"] if r["verdict"] == "PAUSED-BY-CEO"]
    if paused_rows:
        out.append("按 CEO 令暂停（不算故障，恢复要人/开机后起任务）：")
        for r in paused_rows:
            out.append("  - %s（%s）证据龄 %s" % (
                r["station"], r["node"],
                "-" if r["age_h"] is None else "%.1fh" % r["age_h"]))
    return "\n".join(out)


def self_test():
    # 负控：三条通道各造一份「刚写的」和「很老的」，必须分出 ALIVE/DARK；
    # 再验证「mtime 新鲜但时间戳很老」不会被判活（这正是 git pull 造假的老坑）。
    ok = True
    fakes = {
        "nats": {"node": "t1", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                 "ts_utc_ms": int(_now() * 1000), "seq": 1},
        "git": {"node": "t2", "ts": "2026-01-01T00:00:00", "state": "IDLE"},
    }
    e = _parse_ts(fakes["nats"]["ts"])
    if e is None or abs(e - _now()) > 300:
        print("FAIL nats 裸时间戳解析"); ok = False
    e2 = _parse_ts(fakes["git"]["ts"])
    if e2 is None or e2 > _now() - 86400 * 30:
        print("FAIL 老时间戳应解析成很久以前"); ok = False
    if verdict_of(0.1) != "ALIVE" or verdict_of(30) != "DARK":
        print("FAIL 判等阈值"); ok = False
    if _parse_ts("2026-11-27T07:33:09.734Z") is None:
        print("FAIL UTC Z 格式"); ok = False
    # 同一个时刻，UTC 写法与裸写法必须指向同一 epoch（相差 8 小时才是对的：
    # 07:33Z == 15:33 +08:00）
    a = _parse_ts("2026-11-27T07:33:09Z")
    b = _parse_ts("2026-11-27T15:33:09")
    if a is None or b is None or abs(a - b) > 2:
        print("FAIL 时区口径不一致：%s vs %s" % (a, b)); ok = False
    # 尾网代号解析（2026-11-27 实锚）：设备名因重名被去重成 <id>-1 时，本机不许读成离线；
    # 查不到必须是 None（未知），不能伪装成 False（离线）——两者处置办法不同。
    if _tailnet_online("bm-m", {"__self__": "bm-m-1"}) is not True:
        print("FAIL 设备名与代号不一致时本机应判在线"); ok = False
    if _tailnet_online("bm-a", {"__self__": "bm-m-1", "bm-a": False}) is not False:
        print("FAIL 对端离线应读成 False"); ok = False
    if _tailnet_online("bm-z", {"__self__": "bm-m-1"}) is not None:
        print("FAIL 查不到应为 None"); ok = False
    # IP 兜底：名字与别名都查不到时按花名册 tailnet_ip 认（临时目录，不绑真实文件）
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "Tools"))
        with open(os.path.join(td, "Tools", "fleet-nodes.json"), "w", encoding="utf-8") as f:
            json.dump({"nodes": [{"id": "bm-q", "tailnet_ip": "100.64.0.9"}]}, f)
        if _tailnet_online("bm-q", {"__self__": "s", "ip:100.64.0.9": True}, td) is not True:
            print("FAIL 花名册 IP 兜底失效"); ok = False
    print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    snap = snapshot()
    os.makedirs(STATE, exist_ok=True)
    tmp = os.path.join(STATE, "fleet-liveness.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(STATE, "fleet-liveness.json"))
    print(json.dumps(snap, ensure_ascii=False, indent=1) if a.json else render(snap))
    return 1 if any(r["verdict"] in ("STALE", "DARK", "NO-EVIDENCE", "ONLINE-NO-AGENT")
                    for r in snap["nodes"]) else 0


if __name__ == "__main__":
    sys.exit(main())
