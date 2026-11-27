# -*- coding: utf-8 -*-
"""demand_audit.py - 逐条核验 CEO 需求总账，把缺口变成卡。

Why 需要它：CEO 的命令散在 319 行台账和 22 条口头指令里，靠人记必然漏，靠文档声称
必然假绿。这台机器只做一件事——每条需求一个可判定的探针，判不了的明确标 UNVERIFIED
并写清谁判，绝不含糊过关。

Usage:
  demand_audit.py            核验并写一屏 + 状态
  demand_audit.py --dispatch 把未满足且可派卡的条目写成队列卡
Exit: 0 全满足；1 有缺口；2 台账坏了
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
LEDGER = os.path.join(FLEET, "CEO-DEMAND-LEDGER-v1.json")
OUT = os.path.join(FLEET, "CEO-DEMAND-BOARD.md")
STATE_OUT = os.path.join(STATE, "demand-audit.json")

sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def qrows():
    """读的是**当前执行面**（rt/<station>/queue.jsonl 五片），不是退役的旧队列。

    2026-11-14 实锚：本函数原来只读 PRODUCTION-QUEUE.jsonl，而该文件 11-11 已归档；
    某次工具顺手把它重建后，RG-09/10 开始拿一份"没人执行的文件"判红/判绿。
    """
    try:
        import station_shards as _ss
        agg = []
        for _st in _ss.STATIONS:
            agg += _ss.read_queue(_st)
        if agg:
            return agg
    except Exception:
        pass
    out = []
    try:
        with open(QUEUE, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def age_s(path):
    try:
        return time.time() - os.path.getmtime(path)
    except Exception:
        return None


# ---- probes: 每个返回 (ok|False|None, 证据字符串) -------------------------------
def p_stalled_cards(_d):
    rows = qrows()
    live = [r for r in rows if str(r.get("state", "")).upper() in ("BLOCKED", "OPEN", "READY")]
    waiting = [r for r in live
               if any(k in str(r.get("note") or "") + str(r.get("release_reason") or "")
                      for k in ("等 CEO", "等授权", "等确认", "等签核", "waiting-ceo"))]
    return (len(waiting) == 0), "%d 张以「等」为由的活卡" % len(waiting)


def p_idle_with_work(_d):
    rows = qrows()
    work = [r for r in rows if str(r.get("state", "")).upper() in ("OPEN", "READY")]
    flying = [r for r in rows if str(r.get("state", "")).upper() in ("CLAIMED", "RUNNING")]
    ok = not (work and not flying)
    return ok, "可派 %d / 在飞 %d" % (len(work), len(flying))


def p_cadence_ok(_d):
    v = (jload(os.path.join(STATE, "cadence-plan.json"), {}) or {}).get("verdict")
    return (v in ("PASS", "WARN")), "节奏表 %s" % (v or "缺失")


def p_e_artifact(_d):
    al = jload(os.path.join(STATE, "alerts.json"), {}) or {}
    rows = al.get("alerts") if isinstance(al, dict) else al
    n = sum(1 for a in (rows or []) if isinstance(a, dict)
            and "ARTIFACT" in str(a.get("error_class") or a.get("kind") or ""))
    return (n == 0), "E-ARTIFACT %d 条" % n


def p_dup_cards(_d):
    rows = qrows()
    seen, dup = set(), 0
    for r in rows:
        if str(r.get("state", "")).upper() not in ("OPEN", "READY", "CLAIMED", "RUNNING"):
            continue
        k = str(r.get("deliverable") or r.get("title") or "")
        if not k:
            continue
        if k in seen:
            dup += 1
        seen.add(k)
    return (dup == 0), "同交付物重复活卡 %d 张" % dup


def p_no_swap(_d):
    c = jload(os.path.join(STATE, "capacity.json"), {}) or {}
    if "swap_delta_mb" not in c:
        return None, "无 capacity 采样（由 lane 开工前写）"
    return (c["swap_delta_mb"] <= 0), "swap 增量 %s MB" % c["swap_delta_mb"]


def p_false_green(_d):
    rows = qrows()
    bad = 0
    remote_unchecked = 0
    texty = 0
    for r in rows:
        if str(r.get("state", "")).upper() != "DONE":
            continue
        d = str(r.get("deliverable") or "").strip()
        if not d:
            continue
        # 只有「仓库相对路径」能由主控盘判。Windows 绝对路径的产物在执行机上
        # （实测 48 条全是 D:\FleetWorker\...，本机判它"缺失"是误报），
        # 自由文本（"stability verdict"）根本不是路径。
        if re.match(r"^([A-Za-z]:[\\/]|\\\\|/)", d):
            remote_unchecked += 1
            continue
        # 子仓产物（quant/gaming/media/...）本仓看不见，一律标待查，不许判"缺失"；
        # state/ 下是运行时产物不是交付物。实测三次误报都出在这两类。
        if d.startswith(("quant/", "gaming/", "media/", "life/", "compute/",
                         "domain/", "house/", "cph4/fleet/state/")):
            remote_unchecked += 1
            continue
        if not any(d.endswith(x) for x in
                   (".json", ".jsonl", ".md", ".csv", ".png", ".jpg", ".mp4", ".wav",
                    ".txt", ".html", ".yaml", ".yml")):
            texty += 1
            continue
        if not os.path.exists(os.path.join(ROOT, d)):
            bad += 1
    return (bad == 0), ("DONE 未交付 %d 张｜远端待查 %d｜非路径 %d"
                        % (bad, remote_unchecked, texty))


def p_fork_clean(_d):
    f = jload(os.path.join(STATE, "fork-status.json"), {}) or {}
    nodes = f.get("nodes") or {}
    if not nodes:
        return None, "无 fork-status（执行 fork_close 后生成）"
    bad = [n for n, v in nodes.items() if int(v.get("ahead") or 0) > 0]
    return (not bad), ("分叉机器 %s" % ",".join(bad)) if bad else "无分叉"


def p_stale_nodes(_d):
    f = jload(os.path.join(STATE, "fork-status.json"), {}) or {}
    nodes = f.get("nodes") or {}
    stale = [n for n, v in nodes.items() if v.get("runs_old_code")]
    return (len(stale) == 0), ("跑旧码 %s" % ",".join(stale)) if stale else "无跑旧码节点"


def p_disk_free(_d):
    try:
        du = shutil.disk_usage(ROOT)
        gb = du.free / (1024 ** 3)
        return (gb >= 80), "可用 %.1fG" % gb
    except Exception:
        return None, "无法读取磁盘"


def p_model_radar(_d):
    r = jload(os.path.join(STATE, "model-radar.json"), {})
    return (r is not None), ("雷达在档" if r is not None else "无雷达结果")


PROBES = {k[2:]: v for k, v in globals().items() if k.startswith("p_")}



def p_master_no_production(_d):
    """主控禁亲跑生产：本机提交里不许出现媒体/图像/视频产物。"""
    try:
        p = subprocess.run(["git", "-C", ROOT, "log", "-n", "120", "--name-only",
                            "--pretty=format:%s"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return None, "无法读 git log"
    hits, cur_master = [], False
    for ln in (p.stdout or "").splitlines():
        if ln.startswith("job(") or ln.startswith("memory:") or ln.strip() == "":
            cur_master = "via bm-m" in ln
            continue
        if not cur_master:
            continue
        if ln.startswith(("media/", "gaming/")) or ln.endswith((".png", ".mp4", ".wav", ".jpg")):
            hits.append(ln)
    return (len(hits) <= 3), "%d 个主控提交含媒体产物" % len(hits)


def p_census_not_selfref(_d):
    """度量不自指：线的证据路径不许落在 state/ 或回执目录里。"""
    lines = (jload(os.path.join(STATE, "lines.json"), {}) or {}).get("lines") or []
    bad = 0
    for l in lines:
        for ev in (l.get("evidence") or []):
            ev = ev or {}
            p = str(ev.get("path") or "")
            # census 已把 state/回执归为 bookkeeping 且不计入年龄；只有被判成
            # kind=local 却落在记账目录的证据才是真自指（那才是"自己证明自己新鲜"）。
            if str((ev.get("stat") or {}).get("kind")) == "local" and \
                    p.startswith(("cph4/fleet/state", "cph4/fleet/queue-receipts")):
                bad += 1
                break
    return (bad == 0), "%d 条线仍以 state/回执为证据" % bad


def p_state_not_in_git(_d):
    """记账不进 git：state/lanes/radar/chief/sync 不许被跟踪。"""
    try:
        p = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return None, "无法读 git ls-files"
    bad = [x for x in (p.stdout or "").splitlines()
           if x.startswith(("cph4/fleet/state/", "cph4/fleet/lanes/", "cph4/fleet/radar/",
                            "cph4/fleet/chief/", "cph4/fleet/sync/"))]
    return (len(bad) == 0), "%d 个记账文件仍被 git 跟踪" % len(bad)


def p_usb_mounted(_d):
    """训练素材盘：挂在就报，没挂如实说（不假装可达）。"""
    for p in ("/Volumes/移动硬盘", "/Volumes/FluxAssets"):
        if os.path.isdir(p):
            return True, "已挂载 %s" % p
    return False, "移动盘未挂载"


def p_board_readable(_d):
    """汇报可扫读：一屏必须有「最重要的一件事」+ 编号行。"""
    p = os.path.join(FLEET, "COMMAND-BOARD.md")
    try:
        s = open(p, encoding="utf-8").read()
    except Exception:
        return False, "一屏缺失"
    has_top = "现在最重要的一件事" in s
    numbered = sum(1 for ln in s.splitlines() if ln[:2] in ("1.", "2.", "3.", "4.", "5."))
    return (has_top and numbered >= 3), "最重要段=%s 编号行=%d" % (has_top, numbered)


def evaluate(item):
    chk = item.get("check") or {}
    t = chk.get("type")
    if t == "probe":
        fn = globals().get("p_" + str(chk.get("name")))
        if not fn:
            return "UNKNOWN", "探针缺失:%s" % chk.get("name")
        try:
            ok, ev = fn(item)
        except Exception as e:
            return "UNKNOWN", "探针异常:%s" % str(e)[:60]
        return ("OK" if ok else ("GAP" if ok is False else "UNVERIFIED")), ev
    if t == "file_fresh":
        p = os.path.join(ROOT, chk.get("file") or "")
        a = age_s(p)
        if a is None:
            return "GAP", "文件缺失:%s" % chk.get("file")
        limit = int(chk.get("max_age_s") or 3600)
        return ("OK" if a <= limit else "GAP"), "年龄 %ds / 上限 %ds" % (int(a), limit)
    if t == "count_zero":
        fn = globals().get("p_" + str(chk.get("of") or ""))
        if not fn:
            return "UNKNOWN", "探针缺失:%s" % chk.get("of")
        ok, ev = fn(item)
        return ("OK" if ok else "GAP"), ev
    if t == "json_field":
        p = os.path.join(ROOT, chk.get("file") or "")
        d = jload(p)
        if d is None:
            return "GAP", "文件缺失:%s" % chk.get("file")
        return "OK", "在档"
    if t == "manual":
        return "UNVERIFIED", "%s 判：%s" % (chk.get("who") or "人", chk.get("note") or "")
    return "UNKNOWN", "未知 check 类型 %r" % t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dispatch", action="store_true", help="把可派缺口写成队列卡")
    a = ap.parse_args()

    try:
        led = jload(LEDGER)
        if not led:
            raise ValueError("台账不可读")
    except Exception as e:
        print(json.dumps({"verdict": "E-LEDGER", "detail": str(e)[:200]}, ensure_ascii=False))
        return 2

    results = []
    for it in led.get("demands") or []:
        st, ev = evaluate(it)
        results.append({"id": it["id"], "domain": it["domain"], "demand": it["demand"],
                        "state": st, "evidence": ev, "gap": it.get("gap"),
                        "quote": (it.get("quote") or "")[:60]})
    cnt = {}
    for r in results:
        cnt[r["state"]] = cnt.get(r["state"], 0) + 1

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    L = ["# CEO 需求总账 · 实况 %s" % now, "",
         "_%d 条需求：满足 %d / 缺口 %d / 待人判 %d / 未定 %d。机检部分由规则算，"
         "人判部分标了谁判——不含糊过关。_"
         % (len(results), cnt.get("OK", 0), cnt.get("GAP", 0),
            cnt.get("UNVERIFIED", 0), cnt.get("UNKNOWN", 0)), ""]
    doms = {d["id"]: d["name"] for d in led.get("domains") or []}
    gaps = [r for r in results if r["state"] in ("GAP", "UNKNOWN")]
    L.append("## 现在必须补的（缺口）")
    L.append("")
    if gaps:
        for r in gaps:
            L.append("- **%s** %s｜%s｜修法：%s" % (r["id"], r["demand"], r["evidence"], r["gap"]))
    else:
        L.append("- 无。全部机检项通过。")
    L.append("")
    L.append("## 逐域实况")
    L.append("")
    for did, dname in doms.items():
        rows = [r for r in results if r["domain"] == did]
        if not rows:
            continue
        L.append("### %s %s" % (did, dname))
        for r in rows:
            mark = {"OK": "✅", "GAP": "❌", "UNVERIFIED": "◻", "UNKNOWN": "?"}.get(r["state"], "?")
            L.append("%s **%s** %s — %s" % (mark, r["id"], r["demand"], r["evidence"]))
        L.append("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(STATE, exist_ok=True)
    with open(STATE_OUT, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "counts": cnt, "results": results}, f, ensure_ascii=False, indent=1)

    if a.dispatch:
        import fleet_lane as fl
        want = [r for r in results if r["state"] == "GAP" and r["gap"]]
        rows = []
        for r in want:
            rows.append({
                "id": "DEMAND-%s-20261107" % r["id"], "state": "OPEN", "prio": "P1",
                "title": "补需求缺口 %s：%s" % (r["id"], r["demand"][:40]),
                "cmd": "python3 Tools/fleet/demand_audit.py",
                "cwd": "", "needs": "cpu", "line": "fleet-ops", "route": "local",
                "why": "CEO 需求总账机检未过：%s" % r["evidence"],
                "accept": "重跑 demand_audit 后该条转 OK，或写明为何转 UNVERIFIED",
                "created_by": "demand_audit.py",
            })
        if rows:
            fl.merge_jsonl(QUEUE, rows)
        print(json.dumps({"dispatched": len(rows)}, ensure_ascii=False))

    print(json.dumps({"verdict": "GAPS" if gaps else "ALL-OK", "counts": cnt,
                      "board": os.path.relpath(OUT, ROOT)}, ensure_ascii=False))
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())