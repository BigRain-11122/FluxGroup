#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_contingency.py - 主控预案引擎（stdlib only·bm-m 专用）

由 fleet_dashboard.py 每 20 秒调用（独立于主控脉 launchd——就算主控卡死，预案环还活着）。
职责：检测场景 -> 自动处置 -> 记录 -> 只把「需要人」的升级进台账。
所有创建/升级按 场景+日期 去重，绝不重复轰炸。

场景表：
 S1 SVC_MEMBER  主控脉停摆（日志>5min未更新/服务退出码非0）-> kickstart 自愈
 S2 SVC_DASH    看板服务退出码非0 -> kickstart 自愈
 S3 GIT_SYNC    与 origin 分叉>5 提交 -> fetch+rebase+push 修复，失败升级
 S4 NATS_DOWN   总线 4222 不可达 -> 标记降级（bm-m 仅本地活），升级一次/日
 S5 NODE_OFF    曾在线节点心跳>30min -> 升级人工（禁 poke 轰炸·判例：poke 治不了机器关机）
 S6 SUPPLY_DRY  队列 OPEN+RUNNING=0 连续>=3 轮 -> 自动给 bm-m 造一条真实自检诊断活
 S7 JOB_FAIL    当日出现 FAILED -> 升级（附 failure 原因），已终态不自动重派
 S8 STALL_48H   积压 READY 超48h无人认领 -> 升级（多半输入路径不在目标机·需核对）
"""
import json, os, socket, subprocess, sys, time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

STATE_REL = "cph4/fleet/dispatcher/CONTINGENCY-STATE.json"
ESC_REL = "cph4/fleet/dispatcher/CONTINGENCY-ESCALATIONS.md"
QUEUE_REL = "cph4/fleet/PRODUCTION-QUEUE.jsonl"
BACKLOG_REL = "cph4/fleet/PRODUCTION-BACKLOG.jsonl"
NATS_HOST, NATS_PORT = fl.HUB_DEFAULT, fl.PORT_DEFAULT
UID = os.getuid()
WATCH_NODES = ("bm-a", "bm-b", "bm-c", "bm-m")  # bm-d 未装机，不参与离线判定


def _ts():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _sh(cmd, timeout=90):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as e:
        return 125, "", str(e)[:200]


def _mtime_age(path):
    try:
        return time.time() - os.path.getmtime(path)
    except OSError:
        return None


def _nats_ok(timeout=3):
    try:
        with socket.create_connection((NATS_HOST, NATS_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def _load(p, default=None):
    try:
        with open(os.path.join(ROOT, p.replace("/", os.sep)), encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    now_d = datetime.now()
    today = now_d.strftime("%Y%m%d")
    st = _load(STATE_REL, {}) or {}
    marks = st.get("marks", {})  # 场景key(含日期) -> 上次处置时间戳
    prev_seen = set(st.get("prev_online", []))
    actions, escalations = [], []

    def mark(key, cooldown_s=0):
        last = marks.get(key)
        if last and (time.time() - last) < cooldown_s:
            return False
        marks[key] = time.time()
        return True

    # ---- S1 主控脉停摆 -> 自愈
    age = _mtime_age("/tmp/fluxgroup-member.log")
    if age is None or age > 300:
        if mark("S1:" + today, 900):
            rc, out, err = _sh("launchctl kickstart -k gui/%d/com.fluxgroup.member" % UID)
            actions.append("S1 主控脉日志 %ss 未更新 -> kickstart %s"
                           % (int(age) if age is not None else -1,
                              "ok" if rc == 0 else "fail:" + err[:80]))

    # ---- S2 看板服务异常 -> 自愈（服务在跑才说明这条环活着，双保险）
    rc, out, _ = _sh("launchctl list com.fluxgroup.dashboard")
    if "could not find" in (out or "").lower():
        if mark("S2:" + today, 900):
            _sh("launchctl bootstrap gui/%d %s"
                % (UID, os.path.expanduser("~/Library/LaunchAgents/com.fluxgroup.dashboard.plist")))
            actions.append("S2 看板服务丢失 -> 重新 bootstrap")

    # ---- S3 传导阻塞 -> 修复
    rc_a, ahead, _ = _sh("git -C %s rev-list --count origin/main..HEAD" % ROOT)
    rc_b, behind, _ = _sh("git -C %s rev-list --count HEAD..origin/main" % ROOT)
    try:
        n_ahead, n_behind = int(ahead or 0), int(behind or 0)
    except ValueError:
        n_ahead = n_behind = 0
    if (n_ahead > 5 or n_behind > 5) and mark("S3:" + today, 600):
        rc, out, err = _sh("git -C %s fetch origin main -q && "
                           "git -C %s pull --rebase --autostash origin main 2>&1 | tail -1 && "
                           "git -C %s push origin main 2>&1 | tail -1" % (ROOT, ROOT, ROOT))
        ok = "up to date" in (out or "") or "->" in (out or "")
        actions.append("S3 分叉 ahead=%d behind=%d -> rebase修复 %s" % (n_ahead, n_behind, "ok" if ok else "需人工"))
        if not ok:
            escalations.append("S3 GIT_SYNC: 分叉 ahead=%d behind=%d 且自动修复失败，需人工处理仓库同步"
                               % (n_ahead, n_behind))

    # ---- S4 总线断连 -> 降级+升级一次/日
    if not _nats_ok() and mark("S4:" + today, 3600):
        actions.append("S4 NATS 4222 不可达 -> bm-m 转本地模式")
        escalations.append("S4 NATS_DOWN: 状态总线(bm-a:4222)不可达，机队失去心跳总线，bm-m 只能产本地活；需在公司生产力机(bm-a)重启 NATS")

    # ---- 在线节点快照（S5 用）
    online = set()
    now_ms = int(time.time() * 1000)
    for n in WATCH_NODES:
        s = fl.kv_get("state." + n)
        if s and (now_ms - int(s.get("ts_utc_ms") or 0)) / 1000 <= 900:
            online.add(n)

    # ---- S5 曾在线节点消失>30min -> 升级（不 poke 轰炸）
    gone = (prev_seen & set(WATCH_NODES)) - online
    for n in sorted(gone):
        s = fl.kv_get("state." + n)
        age_s = (now_ms - int((s or {}).get("ts_utc_ms") or 0)) / 1000 if s else None
        if age_s and age_s > 1800 and mark("S5:" + n + ":" + today, 21600):
            escalations.append("S5 NODE_OFF: %s 失联超30min（最后心跳 %s）——需该机器主检查电源/联网/NATS 客户端"
                               % (n, ("%ss前" % int(age_s)) if age_s else "无记录"))

    # ---- S6 供给干涸 -> 给 bm-m 造一条真实自检活（当日仅一条）
    rows = fl.read_jsonl(os.path.join(ROOT, QUEUE_REL.replace("/", os.sep)))
    open_n = len([r for r in rows if r.get("state") == "OPEN"])
    run_n = len([r for r in rows if r.get("state") == "RUNNING"])
    dry = st.get("dry_rounds", 0) + 1 if (open_n + run_n) == 0 else 0
    if open_n + run_n == 0 and dry >= 3 and mark("S6:" + today, 86000):
        jid = "R-CHECK-" + today
        out_path = os.path.join(ROOT, "cph4", "fleet", "queue-receipts", "bm-m-selfcheck-" + today + ".md")
        rows.append({
            "id": jid, "title": "主控自检：本轮队列供给与堵点（bm-m 本地35B）",
            "cmd": None, "cwd": ROOT, "needs": "cpu",
            "deliverable": out_path, "nodes": ["bm-m"], "model": "local-small",
            "prompt": ("依据本文件与同目录 MASTER-STATE.json：①今日完成/失败/在队各多少；②最优先要解的1个堵点与步骤；"
                       "③给 bm-b/bm-c 各一条可立即执行的具体活（只能引用 backlog 中已声明的工具名与产物路径）。≤20行，不编造。"),
            "when_all": ["cph4/fleet/dispatcher/MASTER-STATE.json"],
            "llm": {"out": out_path},
            "prio": "P1", "state": "OPEN", "route": "local",
            "created_by": "fleet_contingency:S6", "created_at": _ts(),
        })
        fl.write_jsonl(os.path.join(ROOT, QUEUE_REL.replace("/", os.sep)), rows)
        actions.append("S6 供给干涸%d轮 -> 已造自检真活 %s" % (dry, jid))

    # ---- S7 当日 FAILED -> 升级（附原因）
    today_str = now_d.strftime("%Y-%m-%d")
    failed_today = [r for r in rows if r.get("state") == "FAILED"
                    and str(r.get("finished_at") or "").startswith(today_str)]
    if failed_today and mark("S7:" + today, 21600):
        det = "; ".join("%s(%s)" % (r.get("id"), (r.get("failure") or "?")[:30]) for r in failed_today[:3])
        escalations.append("S7 JOB_FAIL: 当日失败任务 -> %s —— 已终态不自动重派，需人工定夺（重试/改道/撤销）" % det)

    # ---- S8 活源 48h 无人认领 -> 升级
    try:
        bl = fl.read_jsonl(os.path.join(ROOT, BACKLOG_REL.replace("/", os.sep)))
        stale = [r for r in bl if r.get("state") in (None, "READY")
                 and (now_ms - int(r.get("created_ts_ms") or 0)) / 1000 > 172800
                 and r.get("created_by", "").startswith("bm-m")]
        if stale and mark("S8:" + today, 43200):
            ids = ", ".join(r.get("id", "?") for r in stale[:4])
            escalations.append("S8 STALL_48H: 我注入的活源 48h 未被认领 -> %s（大概率输入路径不在目标机盘上，需核对真实路径）" % ids)
    except Exception:
        pass

    # ---- 写升级台账 + 状态
    if escalations:
        esc_path = os.path.join(ROOT, ESC_REL.replace("/", os.sep))
        os.makedirs(os.path.dirname(esc_path), exist_ok=True)
        with open(esc_path, "a", encoding="utf-8") as f:
            for e in escalations:
                f.write("- [%s] %s\n" % (_ts(), e))
    out = {"ts": _ts(), "marks": marks, "prev_online": sorted(online),
           "dry_rounds": dry, "actions": actions[-12:], "escalations_today": today,
           "nats_ok": _nats_ok() if mark("probe", 55) else st.get("nats_ok")}
    fl.write_json(os.path.join(ROOT, STATE_REL.replace("/", os.sep)), out)
    line = "contingency %s | 动作 %d | 新升级 %d | 在线%s%s" % (
        _ts(), len(actions), len(escalations), sorted(online),
        " | " + " ;; ".join(actions) if actions else "")
    print(line)
    return escalations


if __name__ == "__main__":
    main()
