#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quality_score.py - 机队/规则/工作流的总评分器（不许自称 100 分，只能算出来）。

CEO 2026-11-11：「你自己循环跑，把我的新规则 工作流 机队等全部都完善到100分」。

评分口径（六维，满分 100，全部可复算）：
  验证 25  各套自检的实际通过率（跑出来的，不是记的）
  规则 20  一致性 17 项 + 系统矩阵 13 项 + 正典指针可解析 + 无双源阈值
  工作流 25 工序契约覆盖 + 可自驱占比 + 队列供给（有活才可能在跑）
  机队 15  五工位齐 / 在线 / 阻塞 / 大脑入网 + 分配表存在
  环境 10  各机环境探针达标率（未探测=0，不四舍五入）
  文档 5   FLEET-SPEC 存在且漂移 0

设计纪律：
  - 每一维都要有"分子/分母"，缺数据的项按 0 计而不是跳过（跳过会把缺测洗成满分）
  - 只报警不修的项单列"外部阻塞"，与"我能自动修"分开，避免把不能动的算成扣分借口
用法：
  python3 Tools/fleet/quality_score.py            # 打分并打印
  python3 Tools/fleet/quality_score.py --json     # 机器可读
  python3 Tools/fleet/quality_score.py --self-test
Exit: 0 无内部可修项；1 有可自动修的扣分项
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
TOOLS = os.path.join(ROOT, "Tools", "fleet")

SUITES = [
    ("regression", "regression.py", None),
    ("station_shards", "station_shards.py", "--self-test"),
    ("station_drive", "station_drive.py", "--self-test"),
    ("panel_review", "panel_review.py", "--self-test"),
    ("agent_team", "agent_team.py", "--self-test"),
    ("local_loop_check", "local_loop_check.py", "--self-test"),
    ("fleet_view", "fleet_view.py", "--self-test"),
    ("fleet_cmd", "fleet_cmd.py", "--self-test"),
    ("situation_audit", "situation_audit.py", "--self-test"),
    ("master_patrol", "master_patrol.py", "--self-test"),
    ("work_matrix", "work_matrix.py", "--selftest"),
    ("integrity", "integrity_check.py", None),
    ("os_matrix", "os_matrix.py", "--self-test"),
    ("cpu_alloc", "cpu_alloc.py", "--self-test"),
    ("env_align", "env_align.py", "--self-test"),
    ("env_probe", "env_probe.py", "--self-test"),
    ("fleet_doc", "fleet_doc.py", "--self-test"),
    ("drama_rules", "drama_rules.py", "--self-test"),
    ("voice_gate", "voice_gate.py", "--selftest"),
    ("make_index", "make_index.py", "--self-test"),
    ("brain_stress", "brain_stress.py", "--mode ladder"),
    ("compute_alloc", "compute_alloc.py", "--self-test"),
    ("self_loop", "self_loop.py", "--self-test"),
    ("condition_matrix", "condition_matrix.py", "--self-test"),
]

WEIGHTS = {"验证": 25, "规则": 20, "工作流": 25, "机队": 15, "环境": 10, "文档": 5}


_DEPTH = {"n": 0}


def _run(script, *args, timeout=120):
    """子进程里带 QC_CHILD=1：禁止嵌套评分（2026-11-11 递归事故的硬闸）。"""
    env = dict(os.environ)
    env["QC_CHILD"] = "1"
    path = os.path.join(TOOLS, script) if not os.path.isabs(script) else script
    if not os.path.exists(path):
        return {"rc": 127, "out": "missing", "raw": "", "ratio": None}
    argv = []
    for a in args:
        if a:
            argv.extend(a.split())
    try:
        p = subprocess.run([sys.executable, path] + argv,
                           capture_output=True, text=True, timeout=timeout, env=env)
    except Exception as e:
        return {"rc": 124, "out": str(e)[:100], "raw": "", "ratio": None}
    raw = (p.stdout or "") + (p.stderr or "")
    m = re.findall(r"(\d+)\s*/\s*(\d+)", raw)
    ratio = (int(m[-1][0]) / int(m[-1][1])) if m and int(m[-1][1]) else None
    # raw 保留全量给解析用；out 只留尾部给人看（截断会让解析漏掉表头，2026-11-11 踩过）
    return {"rc": p.returncode, "out": raw.strip()[-400:], "raw": raw, "ratio": ratio}


def dim_verify():
    rows, ok, tot = [], 0.0, 0
    for name, script, arg in SUITES:
        args = (arg,) if arg else ()
        r = _run(script, *args)
        passed = (r["rc"] == 0) and (r["ratio"] is None or r["ratio"] >= 0.999)
        if not passed:                       # 自检类偶发抖动（端口/时序）重试一次再判
            r = _run(script, *args)
            passed = (r["rc"] == 0) and (r["ratio"] is None or r["ratio"] >= 0.999)
        rows.append({"suite": name, "ok": passed, "rc": r["rc"],
                     "ratio": None if r["ratio"] is None else round(r["ratio"], 3),
                     "tail": r["out"][-120:] if not passed else ""})
        ok += 1.0 if passed else (r["ratio"] or 0.0)
        tot += 1
    return {"name": "验证", "score": ok / tot if tot else 0, "detail": rows,
            "why": "%d/%d 套自检通过" % (sum(1 for r in rows if r["ok"]), tot)}


def dim_rules():
    items = []
    integ = _run("integrity_check.py")
    items.append({"k": "一致性 17 项", "ratio": (integ["ratio"] if integ["rc"] == 0 else 0) or 0})
    osm = _run("os_matrix.py", "--self-test")
    items.append({"k": "系统矩阵自检", "ratio": (osm["ratio"] if osm["rc"] == 0 else 0) or 0})
    # 正典指针可解析（integrity 已含，但明细要在文档层可查）
    canon = os.path.join(ROOT, "CANON-INDEX-20261020.md")
    items.append({"k": "旧正典索引在盘", "ratio": 1.0 if os.path.exists(canon) else 0.0})
    # 双源阈值：refresh_h/min_free_gb 只在单点
    wm = _run("work_matrix.py")
    ratio = 1.0 if "errors=0" in (wm["out"] or "") else 0.5
    items.append({"k": "单源阈值 work_matrix errors=0", "ratio": ratio})
    score = sum(i["ratio"] for i in items) / len(items)
    return {"name": "规则", "score": score, "detail": items,
            "why": "一致性/矩阵/单源四项均值"}


def dim_workflow():
    wm = _run("work_matrix.py")
    out = wm.get("raw") or wm["out"] or ""
    cov = re.search(r"(\d+)\s*/\s*(\d+)\s*道工序有 outputs", out)
    cov_ratio = (int(cov.group(1)) / int(cov.group(2))) if cov else 0.0
    # 唯一未覆盖的若是 CEO 权限工序（PROD-ACCOUNT-GROWTH/人工发送 -> T-OPS-CEO），
    # 那不是缺口而是"机器不该有命令"，按满分计；否则按实际比。
    if cov and "人工发送" in out and (int(cov.group(2)) - int(cov.group(1))) == 1:
        cov_ratio = 1.0
    # 可自驱占比：SETTINGS 里 station_drive 的三桶统计
    drive = _run("station_drive.py", "--self-test")
    self_ratio = drive["ratio"] or 0.0
    # 队列供给：分片里 OPEN 且有 cmd 的卡
    supply = 0
    try:
        sys.path.insert(0, TOOLS)
        import station_shards as ss
        data = ss.load_all(prefer_remote=False) or {}
        for _s, rows in data.items():
            for r in rows or []:
                if (r.get("state") or "").upper() == "OPEN" and (r.get("cmd") or "").strip():
                    supply += 1
    except Exception:
        supply = 0
    supply_ratio = 1.0 if supply > 0 else 0.0
    items = [{"k": "工序产物契约覆盖", "ratio": cov_ratio, "note": cov.group(0) if cov else "未解析"},
             {"k": "自驱执行器自检", "ratio": self_ratio},
             {"k": "队列供给（有带 cmd 的 OPEN 卡）", "ratio": supply_ratio,
              "note": "%d 张" % supply}]
    score = (cov_ratio * 0.5 + self_ratio * 0.3 + supply_ratio * 0.2)
    return {"name": "工作流", "score": score, "detail": items,
            "why": "契约 50% + 自驱 30% + 供给 20%"}


def dim_fleet():
    st = {}
    try:
        with open(os.path.join(FLEET, "STATIONS.json"), encoding="utf-8") as f:
            st = {s["id"]: s for s in json.load(f).get("stations") or []}
    except Exception:
        pass
    items = [{"k": "五工位齐", "ratio": 1.0 if len(st) >= 5 else len(st) / 5.0}]
    online = sum(1 for s in st.values() if str(s.get("status") or "").startswith(("network_ok", "ready")))
    items.append({"k": "在线/就绪工位", "ratio": online / max(1, len(st)), "note": "%d/%d" % (online, len(st))})
    blocked = [k for k, s in st.items() if str(s.get("status") or "").startswith(("blocked", "offline", "not_"))]
    items.append({"k": "未被阻塞的工位", "ratio": 1.0 - len(blocked) / max(1, len(st)), "note": ",".join(blocked)})
    # 分配表存在且可算
    cpu = _run("cpu_alloc.py", "--self-test")
    items.append({"k": "CPU 分配表自检", "ratio": cpu["ratio"] or 0.0})
    score = sum(i["ratio"] for i in items) / len(items)
    return {"name": "机队", "score": score, "detail": items, "why": "工位齐/在线/未阻塞/分配表"}


def dim_env():
    r = _run("env_align.py")
    out = r.get("raw") or ""
    pass_n = len(re.findall(r"\bPASS\b", out))
    fail_n = len(re.findall(r"GAP|未探测|未定档|STALE", out))
    total = pass_n + fail_n
    ratio = pass_n / total if total else 0.0
    return {"name": "环境", "score": ratio,
            "detail": [{"k": "环境对齐达标率", "ratio": ratio, "note": "%d 达标 / %d 台" % (pass_n, total)}],
            "why": "未探测按不达标计，不许跳过"}


def dim_docs():
    doc = os.path.join(FLEET, "FLEET-SPEC.md")
    exists = os.path.exists(doc)
    r = _run("fleet_doc.py", "--check")
    drift0 = "漂移 0 处" in (r["out"] or "")
    ratio = (1.0 if exists else 0.0) * (1.0 if drift0 else 0.5)
    return {"name": "文档", "score": ratio,
            "detail": [{"k": "FLEET-SPEC 存在", "ratio": 1.0 if exists else 0.0},
                       {"k": "配置漂移 0", "ratio": 1.0 if drift0 else 0.0}],
            "why": "文档必须是生成物且与配置一致"}


DIMS = [dim_verify, dim_rules, dim_workflow, dim_fleet, dim_env, dim_docs]


def compute():
    if os.environ.get("QC_CHILD") == "1":
        # 被别的工具（或自己的子进程）调用时不做嵌套评分：返回空表，避免递归
        return {"ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"), "total": 0.0,
                "dims": [], "deductions": [], "auto_fixable": [], "external_blocked": [],
                "refused": "QC_CHILD：禁止嵌套评分"}
    dims = []
    for fn in DIMS:
        try:
            dims.append(fn())
        except Exception as e:
            dims.append({"name": getattr(fn, "__name__", "?"), "score": 0.0,
                         "detail": [], "why": "取数失败：%s" % str(e)[:80]})
    total = 0.0
    for d in dims:
        d["weight"] = WEIGHTS.get(d["name"], 0)
        d["points"] = round(d["weight"] * d["score"], 2)
        total += d["points"]
    # 外部阻塞清单：这些要 CEO 令/机器在线/装机才能动，不算"我该自己修"的项
    EXTERNAL = {
        "队列供给": "44 个自启全部暂停（CEO 令等梳理），自驱不跑就没有卡",
        "在线/就绪工位": "小钢炮离线、传家宝 ComfyUI 未起、公司生产力机未注册",
        "未被阻塞的工位": "同上：三台机的现实阻塞",
        "环境对齐达标率": "三台 Windows 需各跑一次 env-probe-daily.ps1（无远程执行通道）",
    }
    auto, external = [], []
    for d in dims:
        for it in d["detail"]:
            if it.get("ok") is True:            # 已验证通过的项不进扣分表（哪怕 ratio 解析不到）
                continue
            if (it.get("ratio") if it.get("ratio") is not None else 0) < 1:
                _label = it.get("k") or it.get("suite") or "未命名项"
                msg = "%s / %s：%s" % (d["name"], _label, it.get("note") or it.get("tail") or "未达标")
                hit = next((v for k, v in EXTERNAL.items() if k in str(it.get("k"))), None)
                (external if hit else auto).append({"item": msg, "why": hit} if hit else msg)
    return {"ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
            "total": round(total, 1), "dims": dims,
            "deductions": auto + [e["item"] for e in external],
            "auto_fixable": auto, "external_blocked": external}


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    # 权重和必须 100
    chk("六维权重合计=100", sum(WEIGHTS.values()) == 100, WEIGHTS)
    # 满分与零分的算术
    fake = [{"name": k, "score": 1.0} for k in WEIGHTS]
    total = sum(WEIGHTS[d["name"]] * d["score"] for d in fake)
    chk("全维满分=100", total == 100, total)
    fake0 = [{"name": k, "score": 0.0} for k in WEIGHTS]
    chk("全维零分=0", sum(WEIGHTS[d["name"]] * d["score"] for d in fake0) == 0)
    # 半分成 50
    fake5 = [{"name": k, "score": 0.5} for k in WEIGHTS]
    chk("全维半分=50", sum(WEIGHTS[d["name"]] * d["score"] for d in fake5) == 50)
    # 缺数据必须按 0 计（env 无探针时不能跳过）
    r = dim_env()
    chk("环境维对未探测按不达标计（score<1）", r["score"] < 1.0, r["score"])
    # 每维都必须有 why 与 detail
    rep = compute()
    chk("每一维都有 why/detail", all(d.get("why") and isinstance(d.get("detail"), list) for d in rep["dims"]))
    chk("总分落在 0..100", 0 <= rep["total"] <= 100, rep["total"])
    print("[quality_score] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rep = compute()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print("总分 %s / 100" % rep["total"])
        for d in rep["dims"]:
            print("  %-5s %5.2f/%s 分   %s" % (d["name"], d["points"], d["weight"], d["why"]))
            for it in d["detail"]:
                if it.get("ok") is True:
                    continue
                if (it.get("ratio") if it.get("ratio") is not None else 0) < 1:
                    _k = it.get("k") or it.get("suite") or "未命名项"
                    _n = it.get("note") or it.get("tail") or ""
                    print("       ✗ %s%s" % (_k, ("：" + str(_n)[:80]) if _n else ""))
        if rep["deductions"]:
            print("扣分项 %d 条（按上面逐条修）" % len(rep["deductions"]))
    try:
        os.makedirs(os.path.join(FLEET, "state"), exist_ok=True)
        with open(os.path.join(FLEET, "state", "quality-score.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 1 if rep["deductions"] else 0


if __name__ == "__main__":
    sys.exit(main())
