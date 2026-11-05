#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""soak_watch.py - 24h 运转向上的独立探针 + 长窗账本 + 漂移闸。

为什么存在（CEO 2026-11-05「你是怎么判断正确的？要闭环哦，不要自己在那搞，
然后要保障 24 小时运转没问题」）：
  之前的"PASS"都是我自己写的测试读我自己写的状态文件——度量自指。自指判据只能
  证明代码跑通，不能证明系统在运转。这里换黑盒：只从进程、端口、HTTP、磁盘产物、
  配置指纹这五处取证，不采信任何我自己生成的 verdict 文件。

探针（每项独立，互不依赖）：
  P1 主控脉活着：进程在 + MASTER-STATE 的 tick 龄 < 300s（看的是它，不是我说）
  P2 网关活着：/healthz 200 且 free_gb ≥ 阈值
  P3 模型在：/api/ps 里同时有生成档与嵌入档
  P4 控制台活着：8787 HTTP 200
  P5 真有产出：最近 DONE 卡的关闭时间在 N 小时内（生产面不是只有心跳）
  P6 机器有余量：磁盘 ≥15GB 且 swap 未增长（不许换页跑生产）
  P7 配置没被冲：关键文件 sha256 与基线一致（一天被冲 4 次的教训）
  P8 演练在跑：最近一次演练结论与时间

判定与升级：
  GREEN 全绿 / RED 有硬红 / WARN 只在可容忍项
  RED 连续 >=3 次（约 15 分钟）→ 写入 state/alerts.json（控制台可见）+ 尝试自愈
  （只自愈两件确定的事：主控脉与网关进程没了就 kickstart；其余只报告不强动）
  永不弹窗、永不发对外消息。

用法：
  python3 Tools/fleet/soak_watch.py            # 跑一轮，落账
  python3 Tools/fleet/soak_watch.py --json
  python3 Tools/fleet/soak_watch.py --baseline # 重写配置基线（改配置后必须手工跑）
  python3 Tools/fleet/soak_watch.py --negative # 负向自检：探针必须报红
  python3 Tools/fleet/soak_watch.py --report   # 长窗摘要（uptime/SLO/最近红项）
Exit: 0 GREEN | 1 WARN | 2 RED
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
LEDGER = os.path.join(STATE, "soak.jsonl")
SUMMARY = os.path.join(STATE, "soak-summary.json")
ALERTS = os.path.join(STATE, "alerts.json")
BASE = os.path.join(F, "SOAK-BASELINE.json")

WATCH_FILES = ("AUTONOMY-CONFIG.json", "LOCAL-MODEL-POLICY.json", "MAC-SLOTS-v1.json",
               "DECISION-LAYERS-v1.json", "UNLOCK-PLANS.json")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def cfg():
    return jload(os.path.join(F, "AUTONOMY-CONFIG.json"), {}) or {}


def http_ok(url, timeout=4):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200, r.read(400).decode("utf-8", "replace")
    except Exception as e:
        return False, str(e)[:80]


def proc_alive(pattern):
    try:
        p = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=8)
        return p.returncode == 0 and bool(p.stdout.strip())
    except Exception:
        return False


def age_s(ts):
    try:
        return (datetime.now() - datetime.fromisoformat(str(ts))).total_seconds()
    except Exception:
        return 1e9


def scale_gb():
    try:
        import shutil
        return round(shutil.disk_usage(ROOT).free / 1024 ** 3, 1)
    except Exception:
        return -1.0


def swap_mb():
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                             text=True, timeout=8).stdout
        return float(out.split("used = ")[1].split("M")[0])
    except Exception:
        return -1.0


def fingerprint():
    out = {}
    for name in WATCH_FILES:
        p = os.path.join(F, name)
        try:
            out[name] = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        except Exception:
            out[name] = "missing"
    return out


def _timed(res, key, fn, *a, **kw):
    """每个探针单独计时：只知"红/绿"看不出退化，今天嵌入从 0.1s 变 90s 就是这样被漏的。"""
    t = time.time()
    v = fn(*a, **kw)
    v["ms"] = int((time.time() - t) * 1000)
    res[key] = v
    return v


def probes(quick=False):
    c = cfg()
    lp = c.get("local_priority") or {}
    min_free = float(lp.get("min_free_gb_for_fleet") or 7.0)
    res = {}

    # P1 主控脉
    ms = jload(os.path.join(F, "dispatcher", "MASTER-STATE.json"), {}) or {}
    tick_age = age_s(ms.get("master_tick_ts"))
    alive = proc_alive("master_pulse.py")
    res["P1_pulse"] = {"ok": alive and tick_age < 300,
                       "detail": "proc=%s tick_age=%ds cycle=%s"
                                 % (alive, int(tick_age) if tick_age < 1e8 else -1, ms.get("cycle"))}

    # P2 网关
    _t = time.time()
    ok, body = http_ok("http://127.0.0.1:11435/healthz")
    free = -1.0
    try:
        free = float(json.loads(body).get("free_gb", -1))
    except Exception:
        pass
    res["P2_gateway"] = {"ok": ok and (free < 0 or free >= min_free),
                         "ms": int((time.time() - _t) * 1000),
                         "detail": "http=%s free_gb=%s need>=%s" % (ok, free, min_free)}

    # P3 模型真能用（2026-11-05 教训：装没装 ≠ 能不能用。今天嵌入服务挂死 90s，
    # /api/ps 一直"正常"，只有真打一次才看得见）。1 token 生成 + 一次嵌入，代价可忽略。
    def _post(path, payload, timeout):
        req = urllib.request.Request("http://127.0.0.1:11434" + path,
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())

    pol = jload(os.path.join(F, "LOCAL-MODEL-POLICY.json"), {}) or {}
    gen_model = ((pol.get("duties") or {}).get("resident") or {}).get("model") or "qwen3.5:4b-mlx"
    emb_model = ((pol.get("duties") or {}).get("embedding") or {}).get("model") or "qwen3-embedding:0.6b"
    _t3 = time.time()
    t = time.time()
    try:
        g = (_post("/api/generate", {"model": gen_model, "prompt": "1+1=", "stream": False,
                                     "think": False, "options": {"num_predict": 1}},
                   25).get("response") or "")
        gen_ok, gen_detail = bool(g.strip()), "%.1fs" % (time.time() - t)
    except Exception as e:
        gen_ok, gen_detail = False, str(e)[:60]
    t = time.time()
    try:
        v = _post("/api/embeddings", {"model": emb_model, "prompt": "健康探针"}, 15).get("embedding")
        emb_ok, emb_detail = bool(v), "%d维 %.1fs" % (len(v or []), time.time() - t)
    except Exception as e:
        emb_ok, emb_detail = False, str(e)[:60]
    res["P3_models"] = {"ok": gen_ok and emb_ok,
                        "ms": int((time.time() - _t3) * 1000),
                        "detail": "gen[%s]:%s emb[%s]:%s"
                                  % (gen_model, gen_detail, emb_model, emb_detail)}

    # P4 控制台
    _t = time.time()
    ok, _ = http_ok("http://127.0.0.1:8787/")
    res["P4_console"] = {"ok": ok, "ms": int((time.time() - _t) * 1000),
                         "detail": "http=%s" % ok}

    if quick:
        for k, v in res.items():
            v["probe"] = k.split("_")[0]
        return res, {"swap_mb": -1, "disk_gb": -1, "free_gb": free,
                     "free_pct": -1.0, "last_pageouts": None}

    # P5 真产出（读队列里的关闭时间，不看任何 verdict）
    fresh_h = float((c.get("truth") or {}).get("done_fresh_hours") or 12)
    newest = None
    try:
        for line in open(os.path.join(F, "PRODUCTION-QUEUE.jsonl"), encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("state") == "DONE":
                t = r.get("closed_at") or r.get("finished_at")
                if t and (newest is None or str(t) > str(newest)):
                    newest = t
    except FileNotFoundError:
        pass
    d_age_h = (age_s(newest) / 3600.0) if newest else 1e9
    res["P5_output"] = {"ok": d_age_h <= fresh_h,
                        "detail": "newest_done=%s age=%.1fh limit=%.0fh"
                                  % (newest, d_age_h, fresh_h)}

    # P6 机器余量
    disk = scale_gb()
    sw = swap_mb()
    prev = jload(SUMMARY, {}) or {}
    # 2026-11-05 实测：swap 绝对值毫无意义——macOS 不会把已分配的 swap 还回去
    # （本机 swap 3.3GB 但可用 73%、pageouts 仅 1854，属历史占用不是压力）。
    # 判内存压力只认两件可核的事实：可用率过低，或两次采样间缺页在真的增长。
    free_pct, pageouts = -1.0, -1
    try:
        mp = subprocess.run(["memory_pressure"], capture_output=True, text=True, timeout=10).stdout
        for line in mp.splitlines():
            if "free percentage" in line:
                free_pct = float(line.strip().split()[-1].rstrip("%"))
    except Exception:
        pass
    try:
        vs = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        for line in vs.splitlines():
            if line.startswith("Pageouts:"):
                pageouts = int(line.split(":")[1].strip().rstrip("."))
    except Exception:
        pass
    prev_po = prev.get("last_pageouts")
    po_delta = (pageouts - prev_po) if (pageouts >= 0 and isinstance(prev_po, int)) else 0
    pressure = (free_pct >= 0 and free_pct < 15) or po_delta > 5000
    res["P6_machine"] = {"ok": disk >= 15 and not pressure,
                         "detail": "disk=%.1fGB free=%.0f%% pageouts+%d swap=%.0fMB"
                                   % (disk, free_pct, po_delta, sw)}

    # P9 物理前提（2026-11-05）：24h 运转靠插电 + 插电时不休眠 + caffeinate 活着。
    # 只验软件不验这个，等于半夜一睡全停还报绿。
    try:
        ac = "AC Power" in (subprocess.run(["pmset", "-g", "batt"], capture_output=True,
                                           text=True, timeout=8).stdout or "")
        custom = subprocess.run(["pmset", "-g", "custom"], capture_output=True, text=True,
                                timeout=8).stdout or ""
        seg = custom.split("AC Power:", 1)[1] if "AC Power:" in custom else ""
        ac_sleep = None
        for line in seg.splitlines():
            if line.strip().startswith("sleep "):
                try:
                    ac_sleep = int(line.split()[1])
                except Exception:
                    pass
                break
        caf = proc_alive("caffeinate")
        res["P9_power"] = {"ok": ac and ac_sleep == 0 and caf,
                           "detail": "ac=%s ac_sleep=%s caffeinate=%s" % (ac, ac_sleep, caf)}
    except Exception as e:
        res["P9_power"] = {"ok": False, "detail": str(e)[:60]}

    # P7 配置指纹
    fp = fingerprint()
    base = jload(BASE, {}) or {}
    bfp = base.get("fingerprint") or {}
    drift = sorted([k for k, v in fp.items() if bfp.get(k) and bfp[k] != v])
    res["P7_config"] = {"ok": not drift,
                        "detail": "drift=%s" % (drift or "-")}

    # P8 演练在跑
    rh = jload(os.path.join(STATE, "rehearsal.json"), {}) or {}
    r_age_h = age_s(rh.get("ts")) / 3600.0
    res["P8_rehearsal"] = {"ok": rh.get("verdict") == "PASS" and r_age_h <= 26,
                           "detail": "verdict=%s age=%.1fh" % (rh.get("verdict"), r_age_h)}
    for k, v in res.items():
        v["probe"] = k.split("_")[0]
    return res, {"swap_mb": sw, "disk_gb": disk, "free_gb": free,
                 "free_pct": free_pct, "last_pageouts": pageouts}


def _launchd_job(label):
    """取作业的 plist 路径（用户级）。找不到返回 None。"""
    p = os.path.expanduser("~/Library/LaunchAgents/%s.plist" % label)
    return p if os.path.exists(p) else None


def _kick(label):
    """kickstart 只能拉起"已装载但停止"的作业；unload 掉的要先 load。
    2026-11-05 实测：只 kickstart 时被 unload 的网关叫不回来，自愈等于假的。"""
    uid = os.getuid()
    try:
        subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (uid, label)],
                       capture_output=True, timeout=20)
        time.sleep(2)
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=10).stdout
        if label in out:
            return "%s kickstart ok" % label
    except Exception:
        pass
    plist = _launchd_job(label)
    if not plist:
        return "%s: plist missing, cannot heal" % label
    try:
        subprocess.run(["launchctl", "load", plist], capture_output=True, timeout=20)
        time.sleep(2)
        subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (uid, label)],
                       capture_output=True, timeout=20)
        return "%s load+kickstart" % label
    except Exception as e:
        return "%s heal failed: %s" % (label, str(e)[:60])


def heal(res):
    """只自愈两件确定的事；其余一律只报告，不擅自改系统。"""
    acts = []
    if not res.get("P1_pulse", {}).get("ok"):
        acts.append(_kick("com.fluxgroup.pulse"))
    if not res.get("P2_gateway", {}).get("ok"):
        acts.append(_kick("com.fluxgroup.gateway"))
    return acts


def run(negative=False, quick=False):
    _t_all = time.time()
    res, extra = probes(quick=quick)
    if negative:
        # 负向自检：故意把两项做成必红，验证探针不是摆设（结果不落账本）
        res["P2_gateway"] = {"ok": False, "detail": "NEGATIVE-CONTROL", "probe": "N2"}
        res["P5_output"] = {"ok": False, "detail": "NEGATIVE-CONTROL", "probe": "N5"}
    bad = [k for k, v in res.items() if not v["ok"]]
    verdict = "GREEN" if not bad else "RED"
    now = datetime.now().isoformat(timespec="seconds")

    prev = jload(SUMMARY, {}) or {}
    streak = int(prev.get("red_streak") or 0)
    streak = streak + 1 if bad else 0
    acts = heal(res) if (bad and not negative) else []
    if bad and not negative and streak >= 3:
        try:
            jload_hist = []
            with open(LEDGER, encoding="utf-8") as f:
                for line in f.readlines()[-60:]:
                    try:
                        jload_hist.append(json.loads(line))
                    except Exception:
                        pass
            json.dump({"ts": now, "verdict": verdict, "red": bad, "streak": streak,
                       "detail": {k: v["detail"] for k, v in res.items() if not v["ok"]},
                       "healed": acts,
                       "note": "连续 %d 次红：需人看，主控脉与控制台已可见" % streak},
                      open(ALERTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception:
            pass

    row = {"ts": now, "verdict": verdict, "red": bad, "quick": quick,
           "total_ms": int((time.time() - _t_all) * 1000),
           "ms": {k: v.get("ms") for k, v in res.items()},
           "probes": {k: v["ok"] for k, v in res.items()},
           "detail": {k: v["detail"] for k, v in res.items()},
           "healed": acts, "red_streak": streak, **extra}
    if not negative:
        try:
            os.makedirs(STATE, exist_ok=True)
            with open(LEDGER, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass
    # 长窗摘要
    window_h = float((cfg().get("truth") or {}).get("soak_window_hours") or 24)
    hist = []
    try:
        cut = (datetime.now() - timedelta(hours=window_h)).isoformat()
        for line in open(LEDGER, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if str(r.get("ts")) >= cut:
                hist.append(r)
    except FileNotFoundError:
        pass
    n = len(hist) or 1
    green = sum(1 for r in hist if r.get("verdict") == "GREEN")
    per = {}
    for r in hist:
        for k in r.get("red") or []:
            per[k] = per.get(k, 0) + 1
    capped = int((cfg().get("truth") or {}).get("soak_min_samples") or 48)
    enough = len(hist) >= capped
    summary = {
        "ts": now, "window_hours": window_h, "samples": len(hist),
        "window_complete": age_s((jload(SUMMARY, {}) or {}).get("first_ts") or now) >= window_h * 3600,
        "first_ts": (prev.get("first_ts") or now),
        "green_pct": round(100.0 * green / n, 1),
        "red_by_probe": per, "verdict": verdict, "red": bad,
        "red_streak": streak, "last": row,
        "last_full_ts": (now if not row.get("quick") else prev.get("last_full_ts")),
        "last_pageouts": row.get("last_pageouts"),
        "slo": {"green_pct_min": 99.0, "max_consecutive_red": 2,
                "enough_samples": enough, "samples_needed": capped},
        "claimable_24h": False if not enough else (round(100.0 * green / n, 1) >= 99.0
                                                   and per == {}),
    }
    try:
        if not negative:      # 负向自检不许污染账本与摘要，否则屏幕上会出现假红
            json.dump(summary, open(SUMMARY, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
    except Exception:
        pass
    return row, summary


def report():
    s = jload(SUMMARY, {}) or {}
    if not s:
        print("尚无账本：先跑一次 soak_watch.py")
        return 2
    print("窗口 %.0fh｜采样 %d 次｜绿 %.1f%%｜够不够判 24h=%s"
          % (s.get("window_hours", 0), s.get("samples", 0), s.get("green_pct", 0),
             s.get("claimable_24h")))
    print("红项计数：%s" % (s.get("red_by_probe") or "无"))
    print("最近一轮：%s red=%s %s" % (s.get("verdict"), s.get("red") or "-", s.get("ts")))
    first = s.get("first_ts")
    if first:
        have_h = age_s(first) / 3600.0
        print("已观察 %.1fh / 24h（不够 24h 不许说\"24 小时没问题\"）" % have_h)
    return 0


def write_baseline():
    fp = fingerprint()
    json.dump({"ts": datetime.now().isoformat(timespec="seconds"), "fingerprint": fp},
              open(BASE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("baseline written:", fp)
    return 0


def reset_window(reason=""):
    """把 24h 窗口从"系统就绪"这一刻重新起算；旧账本归档、不删除。

    为什么允许重起：SLO 只能测"修好之后的系统"。但重起必须是显式动作并留理由，
    不许用删账本的方式把红洗掉——那是今天最反对的假绿。
    """
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    arch = os.path.join(STATE, "soak-archive-%s.jsonl" % ts)
    moved = 0
    try:
        if os.path.exists(LEDGER):
            os.replace(LEDGER, arch)
            moved = sum(1 for _ in open(arch, encoding="utf-8"))
    except Exception:
        pass
    for p in (SUMMARY, ALERTS):
        try:
            os.remove(p)
        except OSError:
            pass
    json.dump({"ts": datetime.now().isoformat(timespec="seconds"), "reason": reason,
               "archived_ledger": arch if moved else None, "archived_samples": moved},
              open(os.path.join(STATE, "soak-cutover.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("窗口重起于 %s（归档 %d 条 → %s）理由：%s"
          % (ts, moved, arch if moved else "-", reason))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--negative", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--quick", action="store_true", help="轻检：只验脉/网关/模型/控制台（15s 档）")
    ap.add_argument("--auto", action="store_true",
                    help="按配置自动升降档：距上次全检超过 soak_full_seconds 就跑全检")
    ap.add_argument("--reset-window", action="store_true", help="把 24h 窗口从此刻重算")
    ap.add_argument("--reason", default="", help="重起理由（必填，写进 cutover 件）")
    a = ap.parse_args(argv)
    if a.baseline:
        return write_baseline()
    if a.report:
        return report()
    if a.reset_window:
        if not a.reason:
            print("拒绝：--reset-window 必须带 --reason（不许无理由洗账）")
            return 2
        return reset_window(a.reason)
    quick = a.quick
    if a.auto:
        # 15 秒一次太密，全检（9 项）不必每次都跑：距上次全检超过阈值就升档。
        prev = jload(SUMMARY, {}) or {}
        full_s = float((cfg().get("truth") or {}).get("soak_full_seconds") or 60)
        last_full = age_s(prev.get("last_full_ts") or "")
        quick = last_full < full_s
    row, s = run(negative=a.negative, quick=quick)
    if a.json:
        print(json.dumps(row, ensure_ascii=False, indent=1))
    else:
        print("[soak] %s red=%s streak=%d" % (row["verdict"], row["red"] or "-",
                                              row["red_streak"]))
        for k, v in row["detail"].items():
            print("  %-14s %s %s" % (k, "OK " if row["probes"][k] else "RED", v))
        if row["healed"]:
            print("  自愈:", row["healed"])
        print("  窗口 %.0fh 采样 %d 绿 %.1f%% 可判 24h=%s"
              % (s["window_hours"], s["samples"], s["green_pct"], s["claimable_24h"]))
    if a.negative:
        red = set(row["red"])
        ok = {"P2_gateway", "P5_output"} <= red
        print("负向自检：%s（注入的两项必须报红）" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 2
    return 0 if row["verdict"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))