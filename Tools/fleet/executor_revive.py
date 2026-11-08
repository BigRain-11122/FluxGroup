#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""executor_revive.py - 巡检查到「机器不干活」就自己把它拉起来，不再等人转命令。

为什么（2026-11-08 实锚）：
  · 三台 Windows 的 `/status` 全部 `wakes=[]`：FleetLink 活着、能拉代码，但没有
    任何任务被唤醒 → 队列有卡也跑不动，一下午 DONE 只前进 9 张。
  · 这类停摆此前只能靠会话发现、再让 CEO 转命令给操作员；巡检看见了却不动作，
    就是"只报不修的红"，比不报更糟。
  · 通道其实早就存在：FleetLink `/poke` 的契约是
        {"reason": "<ASCII，必须含 enable-tasks>", "tasks": ["<白名单任务名>"]}
    任务名必须先在该节点 roster 的 `enable_tasks` 里（越界会被 off-skip，这是冻结面保护）。
    我第一次发的是 {"action":"enable-tasks"}（不存在的字段）→ accepted 但 wakes 空，
    看起来"已经叫过了"，实际一次都没叫。

三种判定（纯函数 decide，可离线自证）：
  offline  探不到 /status          → 不动（另有 OFFLINE 类负责）
  closeout 拉取报 '.:fail'（分叉） → 发一张自包含收口卡（remote_closeout_card.py）
  wake     wakes 为空或全是失败项  → poke 显式启用 HQ-ProductionClaim
  healthy  有成功 wake             → 不动

用法：
  python3 Tools/fleet/executor_revive.py --check     # 只诊断（回归/巡检用）
  python3 Tools/fleet/executor_revive.py --apply     # 真动作（脉快批调用）
退出码：0 全部健康 / 1 本轮做了动作 / 2 仍有节点拉不起来（需人工）
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NODES = os.path.join(ROOT, "Tools", "fleet-nodes.json")
STATE = os.path.join(ROOT, "cph4", "fleet", "state", "executor-revive.json")
COOLDOWN_S = 240        # 同一台机多久内不重复唤醒（避免每轮刷 poke）
# busy-skip = 任务正在跑（还有一个实例），这是健康不是失败；只有"没唤醒"和"启用失败"才算病。
FAIL_WAKES = (":off-skip", ":enable-fail")


def roster():
    try:
        d = json.load(open(NODES, encoding="utf-8-sig"))
    except Exception:
        return [], 8790
    return [n for n in (d.get("nodes") or []) if isinstance(n, dict)], int(d.get("port") or 8790)


def http_json(url, data=None, timeout=20):
    try:
        req = urllib.request.Request(
            url, data=(json.dumps(data).encode() if data is not None else None),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"err": type(e).__name__}


def decide(status):
    """纯函数：由 /status 返回判定该节点该怎么办。夹具可离线自证。"""
    if not status:
        return "offline", "探不到 /status"
    lp = status.get("last_pull") or {}
    pulls = [str(x) for x in (lp.get("pulls") or [])]
    wakes = [str(x) for x in (lp.get("wakes") or [])]
    if any(p.endswith(":fail") for p in pulls):
        return "closeout", "拉取失败：%s（仓库分叉，ff-only 拉不动）" % ",".join(pulls)
    good = [w for w in wakes if not any(w.endswith(f) for f in FAIL_WAKES)]
    if not wakes:
        return "wake", "wakes 为空：没有任何任务被唤醒（FleetLink 活着但执行者不在）"
    if not good:
        return "wake", "唤醒全部失败：%s" % ",".join(wakes)
    return "healthy", "唤醒正常：%s" % ",".join(wakes[:3])


def base_url(node, port):
    ip = str(node.get("tailnet_ip") or "").strip()
    if ip:
        return "http://%s:%d" % (ip, port)
    host = str(node.get("host") or "").strip()
    return "http://%s:%d" % (host, port) if host else ""


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(st):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass


def poke(base, tasks, reason):
    """显式启用请求：tasks 必须是该节点 enable_tasks 里的名字，reason 必须含 enable-tasks。"""
    code, j = http_json(base + "/poke", {"reason": reason[:120], "tasks": tasks}, timeout=45)
    return code, j


def closeout_card(node_id, base):
    """分叉节点：生成一张自包含收口卡（执行端不依赖任何新文件）。"""
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "remote_closeout_card.py"),
                            "--nodes", node_id, "--apply"], capture_output=True, text=True, timeout=180)
        return r.returncode, (r.stdout or r.stderr or "")[-160:].replace("\n", " ")
    except Exception as e:
        return 1, "%s: %s" % (type(e).__name__, str(e)[:80])


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    nodes, port = roster()
    st = load_state()
    now = time.time()
    out, acted, stuck = [], False, []
    for n in nodes:
        nid = str(n.get("id") or "")
        if not nid or n.get("enabled") is False:
            continue
        allow = [str(x) for x in (n.get("enable_tasks") or [])]
        if not allow:
            continue                      # 没白名单的机器（主控/备用）不在此判
        base = base_url(n, port)
        if not base:
            continue
        code, status = http_json(base + "/status", timeout=12)
        verdict, why = decide(status if code == 200 else None)
        row = {"node": nid, "verdict": verdict, "why": why}
        if verdict in ("wake", "closeout") and (a.apply or False):
            last = float((st.get(nid) or {}).get("ts") or 0)
            if now - last < COOLDOWN_S:
                row["action"] = "cooldown(%ds)" % int(COOLDOWN_S - (now - last))
            elif verdict == "closeout":
                rc, tail = closeout_card(nid, base)
                row["action"] = "closeout-card rc=%d %s" % (rc, tail[:80])
                st[nid] = {"ts": now, "action": "closeout"}
                acted = True
            else:
                c2, j2 = poke(base, allow, "executor-dead:enable-tasks (patrol)")
                row["action"] = "poke http=%d accepted=%s" % (c2, (j2 or {}).get("accepted"))
                st[nid] = {"ts": now, "action": "wake"}
                acted = True
        elif verdict in ("wake", "closeout"):
            row["action"] = "would-act"
            stuck.append(nid)
        if verdict == "offline":
            stuck.append(nid)
        out.append(row)

    save_state(st) if a.apply else None
    if a.json:
        print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "rows": out}, ensure_ascii=False))
    else:
        for r in out:
            print("[revive] %-5s %-9s %s%s" % (r["node"], r["verdict"], r["why"],
                                               (" | " + r["action"]) if r.get("action") else ""))
        print("[revive] %s 检查 %d 台 · 动作 %d · 待人工 %d"
              % ("APPLY" if a.apply else "CHECK", len(out), int(acted), len(stuck)))
    if a.apply and acted:
        return 1
    return 2 if (stuck and not a.apply) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))