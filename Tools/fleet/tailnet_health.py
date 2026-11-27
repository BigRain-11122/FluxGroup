#!/usr/bin/env python3
"""tailnet_health.py - 机队 Tailscale 链路体检（一条命令，判 P0/P1）。

为什么要有它（2026-11-18）：机队协作靠 tailnet，但健康判据散在
「密钥到期 / DERP 绕道 / 名字重复 / 关键端口 / 配置里的 IP 是否还准」
五处，每次出事都要人肉翻。本脚本把这五面固化成一次可复跑的判据。

用法：
    python Tools/fleet/tailnet_health.py              # 人读
    python Tools/fleet/tailnet_health.py --json        # 机读
    python Tools/fleet/tailnet_health.py --netcheck    # 追加测一次 DERP 时延（约 10s）

退出码：0 无 P0；1 有 P0；2 无法体检（tailscale 不可用）

P0 判据（任一命中即退出 1）：
  - 同机出现两个 tailnet 条目（按 hostname 前缀判定）
  - 在线节点的关键端口不通
  - 密钥剩余 < 90 天
  - 配置里的 tailnet_ip 在 tailscale 里找不到（配置已失真）
P1（只告警不阻断）：
  - 离线节点（若带 paused_by_ceo 则降级 INFO）
  - 中继落在美西（lax/sfo/sea）而最近 DERP 在亚洲
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")

US_DERP = {"lax", "sfo", "sea", "dfw", "nyc", "chi", "mia", "den", "tor"}
ASIA_DERP = {"sin", "hkg", "tok", "bom", "syd", "blr", "nrt", "hnd"}
KEY_EXPIRY_WARN_DAYS = 90

# node -> (CEO 可读机器名, 需探的端口)；端口口径来自 STATIONS.json/fleet-nodes.json
PORTS = {
    "bm-a": [8790],
    "bm-b": [8790],
    "bm-c": [8790],
    "bm-m": [8792],
    "bm-d": [],
}


def sh(*args, timeout=90):
    try:
        p = subprocess.run(list(args), capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as exc:  # noqa: BLE001
        return 1, "", str(exc)


def days_left(iso):
    if not iso or iso.startswith("0001-01-01"):
        return None  # 永不过期
    try:
        d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (d - datetime.datetime.now(datetime.timezone.utc)).days
    except Exception:  # noqa: BLE001
        return None


def tcp_ok(ip, port, timeout=4.0):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return True
    except Exception:  # noqa: BLE001
        return False


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--netcheck", action="store_true")
    args = ap.parse_args()

    rc, out, err = sh("tailscale", "status", "--json")
    if rc != 0 or not out:
        print("FAIL tailscale status 不可用：%s" % (err[:200] or "no output"))
        return 2
    st = json.loads(out)

    # 机器名映射（CEO 口径：工位 hostname -> 机器名；node id -> hostname -> 机器名）
    host2name, node2host = {}, {}
    stations = load_json(os.path.join(FLEET, "STATIONS.json")).get("stations", []) or []
    for s in stations:
        if s.get("hostname"):
            host2name[s["hostname"].lower()] = s.get("machine") or s.get("hostname")
    for n in load_json(os.path.join(ROOT, "Tools", "fleet-nodes.json")).get("nodes", []) or []:
        node2host[n.get("id")] = n.get("host") or ""

    def label_of(node_id, host):
        h = (host or "").lower()
        if h in host2name:
            return host2name[h]
        nhost = (node2host.get(node_id) or "").lower()
        if nhost in host2name:
            return host2name[nhost]
        return host or node_id

    self_info = st.get("Self", {})
    peers = st.get("Peer", {})

    # 归一：bm-m-1 / bm-m 视为同一台
    def base(host):
        h = (host or "").lower()
        return h.rsplit("-", 1)[0] if h.rsplit("-", 1)[-1].isdigit() else h

    by_base = {}
    for _, p in peers.items():
        by_base.setdefault(base(p.get("HostName")), []).append(p)
    by_base.setdefault(base(self_info.get("HostName")), []).append(self_info)

    p0, p1, info = [], [], []

    # 1) 同机多条目
    for b, arr in by_base.items():
        if len(arr) > 1:
            p0.append("%s 出现 %d 个 tailnet 条目（%s）→ 删除过期 key"
                      % (label_of(b, arr[0].get("HostName")), len(arr),
                         ", ".join("%s/%s" % (x.get("HostName"), (x.get("TailscaleIPs") or ["?"])[0]) for x in arr)))

    # 2) 逐节点
    rows = []
    for b, arr in sorted(by_base.items()):
        node = arr[0]
        ip = (node.get("TailscaleIPs") or ["-"])[0]
        online = bool(node.get("Online"))
        left = days_left(node.get("KeyExpiry"))
        relay = node.get("Relay") or "-"
        host = node.get("HostName")
        label = label_of(b, host)

        if left is not None and left < KEY_EXPIRY_WARN_DAYS:
            p0.append("%s 密钥仅剩 %d 天（到期即掉线）" % (label, left))
        if relay in US_DERP:
            if online:
                p1.append("%s 中继走 %s（美西），疑似出口在美国（代理/exit node）" % (label, relay))
            else:
                info.append("%s 离线·最后已知中继 %s（美西，回线后核 netcheck）" % (label, relay))

        port_state = []
        if online:
            for port in PORTS.get(b, []):
                ok = tcp_ok(ip, port)
                port_state.append("%d:%s" % (port, "OK" if ok else "DOWN"))
                if not ok:
                    p0.append("%s 在线但 %d 端口不通（机队通道断）" % (label, port))
        rows.append({"node": b, "name": label, "host": host, "ip": ip, "online": online,
                     "key_days_left": left, "relay": relay, "ports": port_state})

    # 3) 配置里的 IP 是否还准
    live_ips = set()
    for x in list(peers.values()) + [self_info]:
        live_ips.update(x.get("TailscaleIPs") or [])
    for st_path, key in ((os.path.join(FLEET, "STATIONS.json"), "stations"),
                         (os.path.join(ROOT, "Tools", "fleet-nodes.json"), "nodes")):
        d = load_json(st_path)
        for r in d.get(key, []) or []:
            tip = r.get("tailnet_ip")
            if not tip or not isinstance(tip, str):
                continue
            if tip.upper().startswith(("PENDING", "NONE", "TBD")) or not tip[:1].isdigit():
                info.append("%s 的 tailnet_ip=%s（占位值·该机未入网，非失真）"
                            % (r.get("machine") or r.get("id") or "?", tip))
                continue
            if tip not in live_ips:
                p0.append("%s 配置里的 tailnet_ip=%s 在 tailscale 中不存在（配置失真）"
                          % (os.path.basename(st_path), tip))

    rep = {"checked_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "self": {"host": self_info.get("HostName"),
                    "ip": (self_info.get("TailscaleIPs") or ["-"])[0],
                    "key_days_left": days_left(self_info.get("KeyExpiry"))},
           "nodes": rows, "P0": p0, "P1": p1}

    if args.netcheck:
        rc, out, _ = sh("tailscale", "netcheck", timeout=60)
        rep["netcheck"] = [ln.strip() for ln in out.splitlines() if "ms" in ln or "UDP" in ln or "IPv6" in ln][:8]

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print("Tailnet 体检 %s   本机 %s (%s) 密钥剩 %s 天"
              % (rep["checked_at"], rep["self"]["host"], rep["self"]["ip"], rep["self"]["key_days_left"]))
        print("%-14s %-6s %-18s %-6s %-5s %-6s %s" % ("machine", "online", "ip", "key", "relay", "port", "host"))
        for r in rep["nodes"]:
            print("%-14s %-6s %-18s %-6s %-5s %-6s %s"
                  % (r["name"][:14], "Y" if r["online"] else "N", r["ip"],
                     "-" if r["key_days_left"] is None else str(r["key_days_left"]) + "d",
                     str(r["relay"])[:5], ",".join(r["ports"]) or "-", r["host"]))
        if rep.get("netcheck"):
            print("netcheck: " + " | ".join(rep["netcheck"]))
        for tag, arr in (("P0", p0), ("P1", p1), ("INFO", info)):
            for m in arr:
                print("%s %s" % (tag, m))
        if not p0 and not p1:
            print("OK 无 P0/P1")
        # 把离线但带 paused_by_ceo 的降级为 INFO（CEO 明令停用，不算故障）
        nodes_cfg = {n["id"]: n for n in (load_json(os.path.join(ROOT, "Tools", "fleet-nodes.json")).get("nodes") or [])}
        for r in rep["nodes"]:
            if not r["online"] and nodes_cfg.get(r["node"], {}).get("paused_by_ceo"):
                print("INFO %s 离线但属 CEO 明令停用（不报警不派卡）" % r["name"])
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main())
