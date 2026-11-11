#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""station_agent.py - 每台机自己的智能体（一机一体，读自己岗位书，巡查自己领域）。

Why（2026-11-11 CEO 令「每台机器都要有自己的智能体，他们可以链接主控的算力，去巡查和验收」）：
  过去只有主控一个脑子在盯全队，别的机器只是执行器。现在每台机有自己的智能体：
  它读自己的岗位书、巡自己的队列与产物、把发现写成 finding；需要判断时调用主控的
  本地模型（8792 网关），而不是各自装模型。

边界（写死）：
  1. 只读不写别人的分片；只写自己的 rt/<station>/。
  2. 不改卡状态——发现只报给主控与工位，落地动作仍由规则脚本或人执行。
  3. 执行者不自证：本智能体的结论是"初审/巡查",不是最终验收。
  4. 模型只做归纳与建议；拿不到模型就退化为规则结论（记 MODEL-UNAVAILABLE，不算失败）。

用法：
    python3 Tools/fleet/station_agent.py --station visual --once
    python3 Tools/fleet/station_agent.py --station audio --loop 300
    python3 Tools/fleet/station_agent.py --self-test
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DEFAULT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import station_shards as ss  # noqa: E402

STATIONS_JSON = "cph4/fleet/STATIONS.json"
CARD_POLICY = "cph4/fleet/CARD-POLICY-v1.json"
CHARTER_REL = "cph4/fleet/stations/%s/CHARTER.md"
GATEWAY = os.environ.get("FLUX_LLM_GATEWAY", "http://100.75.133.10:8792")
TOKEN_ENV = "FLUX_LLM_TOKEN"
STALE_OPEN_H = 24
RUNNING_NO_RECEIPT_MIN = 60
WIN_PATH = ("C:", "D:", "E:", "K:")


def _read_json(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def _policy(root):
    return _read_json(os.path.join(root, CARD_POLICY), {}) or {}


def _charter_hash(root, station):
    p = os.path.join(root, CHARTER_REL % station)
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    except OSError:
        return None


def _is_local_path(p):
    s = str(p or "")
    if not s:
        return False
    if s.startswith(WIN_PATH) or s.startswith("/Users/") or s.startswith("/Volumes/"):
        return False
    return not os.path.isabs(s)


def patrol(root, station, now=None):
    """确定性巡查：只产 finding，不改任何卡状态。"""
    now = now or time.time()
    pol = _policy(root)
    lease = (pol.get("lease_minutes") or {})
    findings = []

    def add(code, severity, subject, detail):
        findings.append({"code": code, "severity": severity,
                         "subject": subject, "detail": detail})

    rows = ss.read_queue(station, root)
    seen = {}
    for r in rows:
        rid = str(r.get("id"))
        seen[rid] = seen.get(rid, 0) + 1
    for rid, n in seen.items():
        if n > 1:
            add("F-DUP-ID", "high", rid, "同一 id 出现 %d 行" % n)

    receipts_dir = ss.receipts_dir(station, root)
    have = set()
    try:
        have = {f.rsplit(".", 1)[0] for f in os.listdir(receipts_dir) if f.endswith(".json")}
    except OSError:
        pass

    for r in rows:
        rid = str(r.get("id"))
        st = str(r.get("state") or "").upper()
        if st == "OPEN":
            ts = r.get("created_at") or r.get("migrated_at")
            try:
                age_h = (now - time.mktime(time.strptime(str(ts)[:19], "%Y-%m-%dT%H:%M:%S"))) / 3600
            except Exception:
                age_h = None
            if age_h and age_h > STALE_OPEN_H:
                add("W-STALE-OPEN", "warn", rid, "OPEN 已 %.0f 小时无人认领" % age_h)
        if st == "BLOCKED" and not r.get("blocked_by"):
            add("F-BLOCKED-NO-REASON", "high", rid, "BLOCKED 未写原因，无人能解")
        if st in ("RUNNING", "CLAIMED") and rid not in have:
            add("W-RUNNING-NO-RECEIPT", "warn", rid, "在跑但本工位没有回执")
        if st == "DONE":
            d = r.get("deliverable")
            if d and _is_local_path(d):
                p = os.path.join(root, str(d))
                if not os.path.exists(p):
                    add("F-DONE-NO-ARTIFACT", "high", rid, "DONE 但产物不存在：%s" % d)

    # 磁盘（本地工位才有意义）
    try:
        du = shutil.disk_usage(root)
        free_gb = du.free / 2**30
        if free_gb < 20:
            add("W-DISK-LOW", "warn", "disk", "剩余 %.0fG" % free_gb)
    except OSError:
        pass

    # 岗位书漂移：配了 charter 指针但文件不在
    st_cfg = {s["id"]: s for s in (_read_json(os.path.join(root, STATIONS_JSON), {}) or {}).get("stations", [])}
    cfg = st_cfg.get(station) or {}
    if cfg.get("charter") and not os.path.exists(os.path.join(root, cfg["charter"])):
        add("F-CHARTER-MISSING", "high", station, "岗位书不存在：%s" % cfg.get("charter"))
    return findings


def triage_with_model(findings, station):
    """把发现压成一句结论；拿不到模型就返回 None（不当作失败）。"""
    tok = os.environ.get(TOKEN_ENV)
    if not tok or not findings:
        return None
    prompt = ("你是%s工位的巡查助手。以下是本工位本轮巡查发现，请用一句中文给出"
              "最该先处理的一件事与理由，不要编造未给出的信息：\n%s"
              % (station, json.dumps(findings[:20], ensure_ascii=False)))
    body = json.dumps({"model": os.environ.get("FLUX_LOCAL_MODEL", "qwen3.5:4b-mlx"),
                       "prompt": prompt, "stream": False, "think": False,
                       "options": {"num_ctx": 8192, "temperature": 0,
                                   "num_predict": 160}}).encode()
    req = urllib.request.Request(GATEWAY + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json",
                                          "X-Flux-Token": tok})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        return str(d.get("response") or "").strip()[:300] or None
    except Exception:
        return None


def run_once(root, station, use_model=True):
    t0 = time.time()
    findings = patrol(root, station)
    advice = triage_with_model(findings, station) if (use_model and findings) else None
    state = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "station": station,
        "charter_sha": _charter_hash(root, station),
        "findings": len(findings),
        "by_severity": {k: sum(1 for f in findings if f["severity"] == k) for k in ("high", "warn")},
        "model": "ok" if advice else ("skipped" if not findings else "unavailable"),
        "advice": advice,
        "sec": round(time.time() - t0, 2),
    }
    ss.write_json_state = None  # 显式不做别的事
    os.makedirs(os.path.dirname(ss.state_path(station, root)), exist_ok=True)
    tmp = ss.state_path(station, root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ss.state_path(station, root))
    for f in findings:
        ss.append_log(station, dict(f, evt="FINDING", ts=state["ts"]), root)
    return state, findings


def self_test():
    import tempfile
    fails = []

    def chk(name, cond, detail=""):
        if not cond:
            fails.append("%s %s" % (name, detail))

    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "cph4", "fleet", "rt", "visual", "receipts"), exist_ok=True)
        os.makedirs(os.path.join(td, "cph4", "fleet", "stations", "visual"), exist_ok=True)
        open(os.path.join(td, "cph4", "fleet", "stations", "visual", "CHARTER.md"), "w").write("x")
        json.dump({"stations": [{"id": "visual", "charter": "cph4/fleet/stations/visual/CHARTER.md"}]},
                  open(os.path.join(td, "cph4", "fleet", "STATIONS.json"), "w"))
        json.dump({"lease_minutes": {"gpu": 180}}, open(os.path.join(td, "cph4", "fleet", "CARD-POLICY-v1.json"), "w"))
        ss.write_queue("visual", [
            {"id": "A", "state": "OPEN", "created_at": "2020-01-01T00:00:00"},
            {"id": "B", "state": "BLOCKED"},
            {"id": "C", "state": "RUNNING"},
            {"id": "D", "state": "DONE", "deliverable": "no/such/file.mp4"},
        ], td)
        fs = patrol(td, "visual")
        codes = {f["code"] for f in fs}
        chk("stale-open", "W-STALE-OPEN" in codes, str(codes))
        chk("blocked-no-reason", "F-BLOCKED-NO-REASON" in codes)
        chk("running-no-receipt", "W-RUNNING-NO-RECEIPT" in codes)
        chk("done-no-artifact", "F-DONE-NO-ARTIFACT" in codes)
        st, fs2 = run_once(td, "visual", use_model=False)
        chk("state-written", os.path.exists(ss.state_path("visual", td)))
        chk("no-cross-write", not os.path.exists(ss.queue_path("audio", td)))
        chk("model-skipped", st["model"] in ("skipped", "unavailable"), st["model"])
    if fails:
        print("SELFTEST FAIL (%d)：" % len(fails))
        for x in fails:
            print("  -", x)
        return 1
    print("SELFTEST OK: 7/7（巡查四类发现 + 状态落盘 + 不跨工位写 + 无模型可退化）")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", choices=ss.STATIONS)
    ap.add_argument("--root", default=None)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", type=int, default=0)
    ap.add_argument("--no-model", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.station:
        ap.print_help()
        return 0
    root = os.path.abspath(a.root or ROOT_DEFAULT)
    if a.loop:
        while True:
            state, fs = run_once(root, a.station, use_model=not a.no_model)
            print("[%s] %s findings=%d model=%s" % (state["ts"], a.station, state["findings"], state["model"]))
            time.sleep(max(30, a.loop))
    state, fs = run_once(root, a.station, use_model=not a.no_model)
    print(json.dumps(state, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
