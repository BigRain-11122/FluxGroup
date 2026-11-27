# -*- coding: utf-8 -*-
"""commander.py - 指挥层一屏（CEO 只看这一屏）。

按 cph4/fleet/COMMAND-CADENCE-v1.json 的六个节拍做结论，不重复跑工具：
A 值守四件 / B 机队实况 / C 线与产出 / D 一屏 / E 指挥质量 / F 手交 CEO。

Iron rules it obeys:
  * every number comes from disk (lines.json / queue / receipts), never from a heartbeat;
  * it never counts its own output as evidence;
  * zero LLM by default - a 4B that answers arithmetic wrong must not be in the loop
    (2026-11-03). --model adds only a one-line summary, rule-checked.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
LINES = os.path.join(STATE, "lines.json")
ALERTS = os.path.join(STATE, "alerts.json")
OUT = os.path.join(FLEET, "COMMAND-BOARD.md")

sys.path.insert(0, os.path.join(ROOT, "Tools", "fleet"))


def jload(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def qrows():
    out = []
    try:
        with open(QUEUE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return out


def iso_age_h(ts):
    try:
        t = time.mktime(time.strptime(str(ts)[:19], "%Y-%m-%dT%H:%M:%S"))
        return max(0.0, (time.time() - t) / 3600.0)
    except Exception:
        return None


def receipts_self_improve():
    d = os.path.join(FLEET, "queue-receipts")
    got = {}
    if not os.path.isdir(d):
        return got
    for f in os.listdir(d):
        if f.startswith("self-improve-") and f.endswith("-latest.json"):
            r = jload(os.path.join(d, f), {})
            if r.get("node"):
                got[r["node"]] = r
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="store_true", help="加一句 4B 摘要（默认关）")
    a = ap.parse_args()

    rows = qrows()
    live = [r for r in rows if str(r.get("state", "")).upper() in
            ("OPEN", "READY", "CLAIMED", "RUNNING")]
    by_state = {}
    for r in rows:
        s = str(r.get("state") or "NONE").upper()
        by_state[s] = by_state.get(s, 0) + 1
    openish = [r for r in live if str(r.get("state", "")).upper() in ("OPEN", "READY")]
    running = [r for r in live if str(r.get("state", "")).upper() in ("CLAIMED", "RUNNING")]
    defects = [r for r in rows if str(r.get("state") or "").upper() == "CARD-DEFECT"]
    rework = [r for r in live if int(r.get("retries") or 0) >= 3]
    owners = {}
    for r in running:
        o = str(r.get("owner") or "?")
        owners[o] = owners.get(o, 0) + 1

    lines = (jload(LINES, {}) or {}).get("lines") or []
    # 2026-11-10：PARKED 是 CEO 令暂停的线（短剧/切片/车机），它们"不产出"是合规状态，
    # 不是停血。原来把 PARKED 也算进 stale，让"9 条线超 72h"这个数字永远下不去，
    # 真正的 ACTIVE 停血被稀释。stale 只统计 ACTIVE。
    stale = [l for l in lines if (l.get("age_h") or 0) > 72
             and str(l.get("declared") or "").upper() != "PARKED"]
    parked = [l for l in lines if str(l.get("declared") or "").upper() == "PARKED"]
    active = [l for l in lines if str(l.get("declared")) == "ACTIVE"]
    alerts = jload(ALERTS, {}) or {}
    alist = alerts.get("alerts") if isinstance(alerts, dict) else alerts
    alist = alist if isinstance(alist, list) else []
    si = receipts_self_improve()

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    L = []
    L.append("# 指挥一屏 %s" % now)
    L.append("")
    L.append("_节奏表=COMMAND-CADENCE-v1.json｜本屏由规则从盘上事实算出，未用模型猜数_")
    L.append("")

    # --- 最重要的一件事：用可判定的顺序选，不用模型挑 ---
    top = None
    if not openish and not running:
        top = "队列没有可执行卡，机队在等料 —— 立即补卡（A1）"
    elif defects:
        top = "有 %d 张空壳卡（无 cmd），已隔离待重造 —— 查造卡器（A3）" % len(defects)
    elif rework:
        top = "%d 张卡返工≥3 次，根因未解 —— 停线诊断，别重派（C2）" % len(rework)
    elif stale:
        top = "%d 条线超 72h 无产物 —— 挂起或补方向（C1/F2）" % len(stale)
    elif alist:
        top = "有 %d 条未处理告警 —— 先归因再派单（D2）" % len(alist)
    else:
        top = "无阻塞；按各线下一步继续推进（D1）"
    L.append("## 现在最重要的一件事")
    L.append("")
    L.append("**%s**" % top)
    L.append("")

    L.append("## A 值守（45 秒档，纯规则）")
    L.append("")
    L.append("1. 可派卡 **%d** 张｜在飞 **%d** 张｜空壳卡隔离 **%d** 张"
             % (len(openish), len(running), len(defects)))
    L.append("2. 在飞分布：%s" % (", ".join("%s=%d" % kv for kv in sorted(owners.items())) or "无"))
    L.append("3. 返工≥3 次的活卡：**%d** 张%s"
             % (len(rework), ("（" + ", ".join(str(r.get('id')) for r in rework[:3]) + "）")
                if rework else ""))
    L.append("")

    L.append("## B 机队实况（3 分钟档）")
    L.append("")
    if si:
        for n in sorted(si):
            r = si[n]
            chk = {c.get("check"): c.get("verdict") for c in (r.get("checks") or [])}
            L.append("- **%s** %s｜reload=%s shells=%s deps=%s｜%s"
                     % (n, r.get("verdict"), chk.get("reload"), chk.get("shells"),
                        chk.get("deps"), str(r.get("ts") or "")[:16]))
    else:
        L.append("- 还没有任何机器的自改回执（说明卡未被执行，先查投码与分叉）")
    L.append("")

    L.append("## C 线与产出（15 分钟档）")
    L.append("")
    L.append("| 线 | 声明 | 产出年龄 |")
    L.append("|---|---|---|")
    for l in sorted(lines, key=lambda x: -(x.get("age_h") or 0))[:10]:
        age = l.get("age_h")
        flag = " ⚠" if (age or 0) > 72 else ""
        L.append("| %s | %s | %s%s |" % (l.get("name") or l.get("id"), l.get("declared"),
                                         ("%.1fh" % age) if age is not None else "N/A", flag))
    L.append("")
    L.append("ACTIVE 线 %d 条｜超 72h 无产物 %d 条｜PARKED %d 条（按 CEO 令暂停，不计入停血）"
             % (len(active), len(stale), len(parked)))
    L.append("")

    L.append("## D 告警（60 分钟档）")
    L.append("")
    L.append("未处理告警 **%d** 条" % len(alist))
    for x in alist[:5]:
        if isinstance(x, dict):
            L.append("- %s｜%s" % (x.get("id") or x.get("stem") or "?",
                                   str(x.get("note") or x.get("error_class") or "")[:60]))
    L.append("")

    L.append("## E 指挥质量（6 小时档）")
    L.append("")
    done = by_state.get("DONE", 0)
    fail = by_state.get("FAILED", 0)
    unv = by_state.get("UNVERIFIED", 0)
    tot = done + fail + unv
    L.append("1. 队列 %d 行：DONE %d｜FAILED %d｜UNVERIFIED %d｜CANCELLED %d"
             % (len(rows), done, fail, unv, by_state.get("CANCELLED", 0)))
    if tot:
        L.append("2. 完成占比 %.0f%%（DONE/%d）" % (100.0 * done / tot, tot))
    L.append("3. 空壳卡累计隔离 %d 张（越少越好，涨了就是造卡器又出错）" % len(defects))
    L.append("")

    L.append("## F 需要 CEO 的（≤3 条，其余自决）")
    L.append("")
    ceo = []
    if si:
        for n, r in sorted(si.items()):
            if r.get("verdict") != "SELF-OK":
                ceo.append("%s 自检未过（%s）" % (n, r.get("verdict")))
    for l in stale[:2]:
        ceo.append("%s 已 %.0fh 无产物，需定去留" % (l.get("name"), l.get("age_h") or 0))
    if not ceo:
        ceo.append("无 —— 全部按既有规则自决推进")
    for i, c in enumerate(ceo[:3], 1):
        L.append("%d. %s" % (i, c))
    L.append("")

    if a.model:
        try:
            import fleet_lane as fl
            prompt = ("用一句中文说明当前机队状态，只准依据下面数字，不要算新的数：\n"
                      "可派卡%d 在飞%d 空壳%d 返工%d 超72h线%d 告警%d"
                      % (len(openish), len(running), len(defects), len(rework),
                         len(stale), len(alist)))
            txt = fl.local_llm(prompt, node="bm-m", timeout=60)
            if txt:
                L.append("## 一句话（4B，仅供参考）")
                L.append("")
                L.append(str(txt).strip().splitlines()[0][:200])
                L.append("")
        except Exception:
            pass

    md = "\n".join(L)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(md)
    print(json.dumps({"board": os.path.relpath(OUT, ROOT),
                      "top": top,
                      "openish": len(openish), "running": len(running),
                      "defects": len(defects), "rework": len(rework),
                      "stale_lines": len(stale), "alerts": len(alist)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())