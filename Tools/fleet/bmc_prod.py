#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bmc_prod.py — bm-c 生产总控（收口 / 播种 / 自省 / 状态）

为什么要有它（2026-11-21）：
  既有 `cph4/fleet/idle-guard-kit/bmc_idleguard.py` 已经负责「闲置≥10min → 从
  `cph4/fleet/work-bank/bmc-c-gpu-bank.json` 认领一条 pending 活 → Popen 点火」。
  但它**只点火不收口**：claimed 之后没有任何环节把它变成 done/failed，
  于是一条活烧完也被永久跳过。本文件补三个缺口，不自建执行器：

    seed     把生产计划写进既有工作银行（幂等·只补不改）
    finalize 对账 claimed → done / pending(重试) / blocked(判死)，写台账
    iterate  夜间自省：读台账与闸回执，算指标、找重复缺陷、出迭代建议
    status   一屏看生产面

纪律：
  - 不改 bmc_idleguard.py / bmc_autodrive_guard.py / ComfyGuard（既有职责边界）
  - 尊重让路旗标（machine-state.flag 含 paused = 零动作）
  - 一机一 GPU 活（由 idleguard 的忙闲两跳保证；本文件不并发点火）

用法：
  python Tools/fleet/bmc_prod.py seed [--eps 2-10] [--assume-done 1]
  python Tools/fleet/bmc_prod.py finalize
  python Tools/fleet/bmc_prod.py iterate
  python Tools/fleet/bmc_prod.py status
Exit: 0 正常；2 参数/环境问题
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

REPO = r"K:\Fluxgroup\FluxGroup"
BANK = os.path.join(REPO, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")
PROD = os.path.join(REPO, "cph4", "fleet", "production")
LEDGER = os.path.join(PROD, "LEDGER.jsonl")
PLAN = os.path.join(PROD, "bmc-plan.json")
LOGDIR = os.path.join(PROD, "logs")
FLAG = r"K:\Fluxgroup\.codely-cli\machine-state.flag"
PY = sys.executable
NO_WIN = 0x08000000 if os.name == "nt" else 0
CHAIN = os.path.join(REPO, "Tools", "fleet", "drama_ep_chain.py")
EP_DIR = os.path.join(REPO, "cph4", "fleet", "drama-001-stockera", "episodes")
MAX_RETRIES = 3


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def rj(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def wj(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def paused():
    try:
        return "paused" in open(FLAG, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        return False


def ledger(rec):
    os.makedirs(PROD, exist_ok=True)
    rec["ts"] = now()
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def alive(marker):
    """按命令行匹配活进程（排除探针自身）。"""
    try:
        ps = ("Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match '%s' "
              "-and $_.Name -match 'python'} | Select-Object -First 1 | ForEach-Object {$_.ProcessId}") % marker
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, creationflags=NO_WIN, timeout=30).stdout.strip()
        return bool(out)
    except Exception:
        return True  # 探针失败→保守判在跑


# ---------------------------------------------------------------- seed
def cmd_seed(a):
    bank = rj(BANK, {"node": "bm-c", "kind": "gpu", "jobs": []})
    have = {j.get("id") for j in bank.get("jobs", [])}
    eps = []
    if "-" in a.eps:
        lo, hi = a.eps.split("-")
        eps = list(range(int(lo), int(hi) + 1))
    else:
        eps = [int(x) for x in a.eps.split(",") if x.strip()]

    added = 0
    for ep in eps:
        jid = "PROD-DRAMA-EP%03d" % ep
        base = "cph4/fleet/out/drama/EP%03d" % ep
        mp4 = base + "/ep%03d.mp4" % ep
        if ep <= a.assume_done:
            continue
        if jid in have:
            continue
        bank.setdefault("jobs", []).append({
            "id": jid,
            "title": "漫剧 EP%03d 全链（plan→kf→i2v→配音→装配→闸）" % ep,
            "cmd": '"%s" "%s" --ep %d --stages all' % (PY, CHAIN, ep),
            "needs": "gpu",
            "prio": "P1",
            "why": "60 集正典剧本在库；本机可全链自产（EP001 已验 PASS）",
            "deliverable": mp4,
            "accept": "cph4/fleet/out/drama/EP%03d/ep%03d-gate.json 内 verdict=PASS" % (ep, ep),
            "log_out": "cph4/fleet/production/logs/%s.out.log" % jid,
            "log_err": "cph4/fleet/production/logs/%s.err.log" % jid,
            "status": "pending",
            "retries": 0,
            "seeded": now(),
        })
        added += 1
    os.makedirs(LOGDIR, exist_ok=True)
    wj(BANK, bank)
    plan = {"ts": now(), "node": "bm-c", "line": "bigstream-drama",
            "policy": "漫剧 60 集本地闭环：单集 480P 验证档 → 过闸即收口；正片 768P 另批",
            "episodes": eps, "seeded_now": added}
    wj(PLAN, plan)
    print("SEED added=%d total_jobs=%d bank=%s" % (added, len(bank.get("jobs", [])), BANK))
    return 0


# ---------------------------------------------------------------- finalize
def cmd_finalize(a):
    if paused():
        print("FINALIZE skip: paused window")
        return 0
    bank = rj(BANK, {"jobs": []})
    changed = done = requeued = blocked = running = 0
    for job in bank.get("jobs", []):
        if job.get("status") != "claimed":
            continue
        deliverable = job.get("deliverable") or ""
        full = os.path.join(REPO, deliverable.replace("/", os.sep)) if deliverable else ""
        ok = bool(full) and os.path.isfile(full) and os.path.getsize(full) > 200 * 1024
        # 闸回执（accept 指向的 json）
        gate_ok, gate_note = True, ""
        acc = job.get("accept") or ""
        if ok and acc.endswith(".json 内 verdict=PASS"):
            gp = acc.split(" ")[0]
            g = rj(os.path.join(REPO, gp.replace("/", os.sep)), {})
            gate_ok = (g.get("verdict") or g.get("status") or "").upper() == "PASS"
            gate_note = "%s=%s" % (gp, g.get("verdict") or g.get("status"))
        if ok and gate_ok:
            job["status"] = "done"
            job["done_ts"] = now()
            done += 1
            changed += 1
            ledger({"ev": "done", "id": job["id"], "deliverable": deliverable,
                    "bytes": os.path.getsize(full), "gate": gate_note})
            continue
        # 没产物：看在不在跑
        marker = job["id"]
        if alive(marker):
            running += 1
            continue
        # 死了没产物 → 重试梯
        job["retries"] = int(job.get("retries") or 0) + 1
        job["last_error"] = "no-deliverable" if not ok else "gate-fail:%s" % gate_note
        # 2026-11-21：把"哪一站挂的"记进台账——只写 no-deliverable 等于把人推回原始日志里捞。
        if not ok:
            epn = (job.get("id") or "").split("EP")[-1]
            cs = rj(os.path.join(REPO, "cph4", "fleet", "out", "drama", "EP%s" % epn,
                                 "chain-state.json"), {})
            failed_stages = [k for k, v in (cs.get("stages") or {}).items() if v.get("rc") not in (0, 3)]
            if failed_stages:
                job["last_error"] = "fail:" + ",".join(failed_stages)
        if job["retries"] <= MAX_RETRIES:
            job["status"] = "pending"
            job["requeued_ts"] = now()
            requeued += 1
            ledger({"ev": "requeue", "id": job["id"], "attempt": job["retries"],
                    "why": job["last_error"]})
        else:
            job["status"] = "blocked"
            job["blocked_ts"] = now()
            blocked += 1
            ledger({"ev": "blocked", "id": job["id"], "attempts": job["retries"],
                    "why": job["last_error"]})
        changed += 1
    if changed:
        wj(BANK, bank)
    print("FINALIZE done=%d requeued=%d blocked=%d running=%d" % (done, requeued, blocked, running))
    return 0


# ---------------------------------------------------------------- iterate
def cmd_iterate(a):
    """夜间自省：读台账，算指标，找重复缺陷，出建议。只写建议，不自动立法。"""
    os.makedirs(PROD, exist_ok=True)
    rows = []
    if os.path.isfile(LEDGER):
        for line in open(LEDGER, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    bank = rj(BANK, {"jobs": []})
    jobs = bank.get("jobs", [])
    st = {}
    for j in jobs:
        st[j.get("status")] = st.get(j.get("status"), 0) + 1
    done_ids = [j["id"] for j in jobs if j.get("status") == "done"]
    blocked_jobs = [j for j in jobs if j.get("status") == "blocked"]

    # 失败原因聚类
    cause = {}
    for r in rows:
        if r.get("ev") in ("requeue", "blocked"):
            cause[r.get("why", "?")] = cause.get(r.get("why", "?"), 0) + 1

    # 单集耗时（从 chain-state 读）
    durs = []
    for j in done_ids:
        epn = j.split("EP")[-1]
        cs = rj(os.path.join(REPO, "cph4", "fleet", "out", "drama", "EP%s" % epn, "chain-state.json"), {})
        secs = sum(v.get("sec", 0) for v in (cs.get("stages") or {}).values())
        if secs:
            durs.append((j, round(secs / 60.0, 1)))

    lines = ["# bm-c 生产自省 · %s" % time.strftime("%Y-%m-%d %H:%M"), "",
             "## 一、面", "",
             "| 项 | 值 |", "|---|---|",
             "| 银行总活 | %d |" % len(jobs),
             "| 状态分布 | %s |" % json.dumps(st, ensure_ascii=False),
             "| 已完成 | %d |" % len(done_ids),
             "| 判死 | %d |" % len(blocked_jobs), "",
             "## 二、指标", ""]
    if durs:
        avg = sum(d for _, d in durs) / len(durs)
        lines.append("- 单集耗时（已完成 %d 集）：均值 %.1f 分钟，明细 %s" % (
            len(durs), avg, ", ".join("%s=%.1f" % x for x in durs)))
        lines.append("- 24h 理论产能（单机）：约 %.1f 集/天（按均值，不含让路窗）" % (24 * 60 / avg))
    else:
        lines.append("- 尚无完成集，指标待首批收口后生成")
    lines.append("")

    lines += ["## 三、失败聚类（近全量台账）", ""]
    if cause:
        for k, v in sorted(cause.items(), key=lambda x: -x[1]):
            lines.append("- `%s` × %d" % (k, v))
    else:
        lines.append("- 无失败记录")
    lines.append("")

    lines += ["## 四、迭代建议（建议，不是法）", ""]
    # 硬阻断：ComfyUI 僵尸（进程活但不监听）会让整夜零产出，必须顶到最前面
    wedge = rj(os.path.join(REPO, "media", "comfy-wedged.json"), {})
    if wedge:
        lines.append("0. **【硬阻断】ComfyUI 僵尸** pid=%s（%s）→ %s。清掉它之前所有 GPU 活都起不来。"
                     % (wedge.get("pids"), wedge.get("why"), wedge.get("action")))
    if cause.get("no-deliverable", 0) >= 2:
        lines.append("1. **重复「无产物」** ≥2 次 → 先查 SKIP 判据与旧件归档（10-24 判例：旧帧不归档=命令秒过零产出）。")
    if any("gate-fail" in k for k in cause):
        lines.append("2. **闸失败** → 病灶多半在提示词层（否定句/场景词/伪文字），走 `drama_prompt_critic.py` 先筛再烧。")
    if not cause:
        lines.append("1. 无失败样本，本轮无建议——继续放量观察。")
    lines += ["", "## 五、下一步（自动）", "",
              "- 本报告只落档；**判死件需人工或主控裁定**（禁自动放宽闸）。",
              "- 重试梯已在 finalize 内（≤%d 次自动重排）。" % MAX_RETRIES]

    out = os.path.join(PROD, "ITERATION-%s.md" % time.strftime("%Y%m%d"))
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    ledger({"ev": "iterate", "report": os.path.relpath(out, REPO).replace("\\", "/"),
            "done": len(done_ids), "blocked": len(blocked_jobs)})
    print("ITERATE -> %s" % out)
    return 0


# ---------------------------------------------------------------- status
def cmd_status(a):
    bank = rj(BANK, {"jobs": []})
    st = {}
    for j in bank.get("jobs", []):
        st[j.get("status")] = st.get(j.get("status"), 0) + 1
    print("BANK %s" % BANK)
    print("  jobs=%d  %s" % (len(bank.get("jobs", [])), json.dumps(st, ensure_ascii=False)))
    for j in bank.get("jobs", [])[:12]:
        print("  - %-22s %-8s retries=%s %s" % (j.get("id"), j.get("status"),
                                                 j.get("retries"), (j.get("last_error") or "")[:40]))
    try:
        u = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
                            "--format=csv,noheader"], capture_output=True, text=True,
                           creationflags=NO_WIN, timeout=15).stdout.strip()
        print("GPU %s" % u)
    except Exception:
        print("GPU probe failed")
    print("PAUSED=%s" % paused())
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["seed", "finalize", "iterate", "status"])
    ap.add_argument("--eps", default="2-10")
    ap.add_argument("--assume-done", type=int, default=1, help="≤该集号视为已完成（不播种）")
    a = ap.parse_args(argv)
    return {"seed": cmd_seed, "finalize": cmd_finalize,
            "iterate": cmd_iterate, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
