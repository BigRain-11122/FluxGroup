#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fleet_doc.py - 机队配置文档生成器（一处改配置，重跑即更新，并自动报漂移）。

CEO 2026-11-11：「你把我的机队电脑配置系统什么的好好维护一个文档」。

手写的机器文档一定会过期（本仓实测过"配置双写 8 处"的教训），所以这份文档不手写：
  数据源=STATIONS.json（工位/硬件/盘/软件）+ Tools/fleet-nodes.json（网络/工作目录/仓库/唤醒任务）
        + OS-MATRIX-v1.json（系统/解释器/锁/调度/核实状态）+ CPU-PLAN-v1.json（核数/并行规则）
        + AGENT-CAPACITY-v1.json + MODEL-COMPUTE.json（模型座位与额度）+ ASSET-VAULT.json（存储落点）
  产物=cph4/fleet/FLEET-SPEC.md（人读），漂移清单在文末；--check 只查不写。

用法：
  python3 Tools/fleet/fleet_doc.py --check     # 只报漂移（CI/巡检用，有漂移 rc=1）
  python3 Tools/fleet/fleet_doc.py --write     # 重新生成文档
  python3 Tools/fleet/fleet_doc.py --self-test
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
DOC = os.path.join(FLEET, "FLEET-SPEC.md")
MANUAL_START = "<!-- MANUAL:CHANGELOG -->"
MANUAL_END = "<!-- /MANUAL -->"

SOURCES = {
    "stations": os.path.join(FLEET, "STATIONS.json"),
    "nodes": os.path.join(ROOT, "Tools", "fleet-nodes.json"),
    "os": os.path.join(FLEET, "OS-MATRIX-v1.json"),
    "cpu": os.path.join(FLEET, "CPU-PLAN-v1.json"),
    "capacity": os.path.join(FLEET, "AGENT-CAPACITY-v1.json"),
    "compute": os.path.join(FLEET, "MODEL-COMPUTE.json"),
    "vault": os.path.join(FLEET, "ASSET-VAULT.json"),
}


def load(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def collect():
    st = load(SOURCES["stations"], {}) or {}
    nodes = load(SOURCES["nodes"], {}) or {}
    osx = load(SOURCES["os"], {}) or {}
    cpu = load(SOURCES["cpu"], {}) or {}
    cap = load(SOURCES["capacity"], {}) or {}
    comp = load(SOURCES["compute"], {}) or {}
    vault = load(SOURCES["vault"], {}) or {}

    stations = {s.get("id"): s for s in (st.get("stations") or [])}
    node_by_host = {}
    for n in nodes.get("nodes") or []:
        node_by_host[str(n.get("host") or "").lower()] = n
    return {"stations": stations, "nodes": nodes, "node_by_host": node_by_host,
            "os": osx.get("machines") or {}, "cpu": cpu.get("machines") or {},
            "classes": cpu.get("classes") or {}, "capacity": cap.get("machines") or {},
            "compute": comp, "vault": vault,
            "rules": osx.get("rules") or [], "principles": cpu.get("_principles") or []}


def node_of(data, sid, station):
    """按 hostname 反查节点代号（不许按 id 硬编码：bm-c 对应 visual 这种映射只能由 hostname 得出）。"""
    host = str(station.get("hostname") or "").lower()
    n = data["node_by_host"].get(host)
    if n:
        return n
    for n in data["nodes"].get("nodes") or []:
        if str(n.get("id") or "").replace("bm-", "") in (sid,):
            return n
    return {}


def drift(data):
    """六个数据源必须互相认得上、关键字段必须一致。漂移=文档不可信的根因。"""
    out = []
    st, osx, cpu, cap = data["stations"], data["os"], data["cpu"], data["capacity"]
    ids = set(st)
    for name, other in (("OS-MATRIX", set(osx)), ("CPU-PLAN", set(cpu))):
        miss = sorted(ids - other)
        extra = sorted(other - ids)
        if miss:
            out.append("工位表有、%s 缺：%s" % (name, ",".join(miss)))
        if extra:
            out.append("%s 有、工位表缺：%s" % (name, ",".join(extra)))
    for sid, s in st.items():
        c = cpu.get(sid) or {}
        if c:
            if s.get("cpu_cores") and c.get("cores") and s["cpu_cores"] != c["cores"]:
                out.append("%s 核数不一致：STATIONS=%s CPU-PLAN=%s" % (sid, s["cpu_cores"], c["cores"]))
            # 内存允许 1G 内取整差（94 与 93.6 是同一台机），超过才算漂移
            if s.get("ram_gb") and c.get("ram_gb") and abs(float(s["ram_gb"]) - float(c["ram_gb"])) > 1.0:
                out.append("%s 内存不一致：STATIONS=%s CPU-PLAN=%s" % (sid, s["ram_gb"], c["ram_gb"]))
        o = osx.get(sid) or {}
        if o and o.get("verified"):
            a = str(s.get("os") or "").lower()
            b = str(o.get("os") or "").lower()
            if a and b and a != b:
                out.append("%s 系统不一致：STATIONS=%s OS-MATRIX=%s" % (sid, a, b))
        capm = cap.get(sid) or {}
        lm = s.get("local_model") or {}
        if capm.get("concurrency") and lm.get("concurrency") \
                and int(capm["concurrency"]) != int(lm["concurrency"]):
            out.append("%s 模型并发不一致：STATIONS=%s AGENT-CAPACITY=%s"
                       % (sid, lm["concurrency"], capm["concurrency"]))
        if not node_of(data, sid, s):
            out.append("%s 在 fleet-nodes.json 里找不到对应节点（网络/工作目录信息将缺失）" % sid)
        # Windows 机声称装了 python3 = 与实测冲突（2026-11-03 rc=9009 两次）
        if str(s.get("os") or "").lower() == "windows":
            sw = [str(x).strip() for x in (s.get("software") or [])]
            if any(x == "python3" or x.startswith("python3 ") for x in sw):
                out.append("%s 是 Windows 却声明装了 python3（实测无，卡里写 python3 必 rc=9009）" % sid)
    return out


def _fmt(v, dash="—"):
    if v is None or v == "" or v == [] or v == {}:
        return dash
    if isinstance(v, list):
        return "、".join(str(x) for x in v)
    if isinstance(v, dict):
        return "、".join("%s=%s" % (k, v[k]) for k in sorted(v))
    return str(v)


def machine_section(i, sid, data, doc_time):
    s = data["stations"][sid]
    o = data["os"].get(sid) or {}
    c = data["cpu"].get(sid) or {}
    cap = data["capacity"].get(sid) or {}
    n = node_of(data, sid, s)
    lm = s.get("local_model") or {}
    gpu = s.get("gpu") or {}
    budget = (cap.get("budget") or {})

    L = []
    L.append("### %d) %s（工位 %s%s）" % (
        i, s.get("machine") or s.get("name") or sid, sid,
        (" / " + n.get("id")) if n.get("id") else ""))
    L.append("")
    L.append("| 项 | 值 |")
    L.append("|---|---|")
    L.append("| 机器名 | %s |" % _fmt(s.get("machine") or n.get("host")))
    L.append("| 系统 | %s%s |" % (
        o.get("os_label") or s.get("os") or "—",
        "（已核实）" if o.get("verified") else "（**未核实**）"))
    L.append("| 核实依据 | %s |" % _fmt(o.get("evidence")))
    L.append("| 解释器 / shell | %s / %s |" % (_fmt(o.get("python")), _fmt(o.get("shell"))))
    L.append("| 路径约定 | %s |" % _fmt(o.get("path_style")))
    L.append("| 文件锁 | %s |" % _fmt(o.get("lock")))
    L.append("| 调度器 | %s |" % _fmt(o.get("scheduler")))
    L.append("| CPU | %s %sC/%sT%s |" % (
        _fmt(c.get("cpu") or s.get("cpu_note") or ""), _fmt(s.get("cpu_cores")),
        _fmt(s.get("cpu_threads")),
        "" if c.get("avx2") is not False else "（**无 AVX2**）"))
    L.append("| 内存 | %s GB |" % _fmt(s.get("ram_gb")))
    _extra = gpu.get("extra")
    L.append("| GPU | %s%s |" % (
        _fmt(gpu.get("model")),
        ("（%sG 显存%s）" % (gpu.get("vram_gb"),
                           ("，" + str(_extra)) if _extra else "")) if gpu.get("vram_gb") else ""))
    if s.get("disks"):
        parts = []
        for dk in (s.get("disks") or []):
            if isinstance(dk, dict):
                free = dk.get("free_gb")
                parts.append("%s（%s%s）" % (dk.get("mount"), dk.get("role") or "",
                                            ("，余 %sG" % free) if free else ""))
            else:
                parts.append(str(dk))
        L.append("| 磁盘 | %s |" % "；".join(parts))
    L.append("| 工作目录 | %s |" % _fmt(n.get("root") or s.get("work_dir")))
    L.append("| 网络 | tailnet %s（端口 %s） |" % (
        _fmt(n.get("tailnet_ip") or s.get("tailnet_ip")), _fmt(data["nodes"].get("port"))))
    L.append("| 角色 | %s |" % _fmt(s.get("role")))
    L.append("| 班次 | %s |" % _fmt(s.get("hours") or s.get("shifts")))
    L.append("| 允许的活 | %s |" % _fmt(s.get("allowed_work")))
    L.append("| 禁区 | %s |" % _fmt(s.get("forbidden_work") or s.get("blocked_scope")))
    L.append("| 磁盘水位 | 低于 %s GB 停手 |" % _fmt(s.get("min_free_gb")))
    L.append("| 模型座位 | %s（%sG，ctx %s，并发 %s） |" % (
        _fmt(lm.get("model")), _fmt(lm.get("vram_gb")), _fmt(lm.get("num_ctx")),
        _fmt(lm.get("concurrency"))))
    L.append("| 模型额度 | %s 次/天，%s 模型分钟/天，实测 %s tok/s |" % (
        _fmt(budget.get("calls_per_day")), _fmt(budget.get("model_minutes_per_day")),
        _fmt(cap.get("tok_s"))))
    if s.get("software"):
        L.append("| 已装软件 | %s |" % _fmt(s.get("software")))
    if n.get("wake_tasks"):
        L.append("| 唤醒任务 | %s |" % _fmt(n.get("wake_tasks")))
    if s.get("status"):
        L.append("| 当前状态 | %s |" % _fmt(s.get("status")))
    L.append("")

    # 该机能跑哪几类 CPU 活（并行上限来自 CPU-PLAN，按夜窗算）
    rows = []
    for cls, cd in sorted(data["classes"].items()):
        if sid not in (cd.get("machines") or []):
            continue
        usable = (c.get("cores") or 0) * float(c.get("night_share") or 1) - (c.get("reserve_cores") or 0)
        threads = cd.get("threads") or 1
        if cd.get("needs_avx2") and c.get("avx2") is False:
            fb = cd.get("no_avx2_fallback") or {}
            if not fb:
                continue
            threads = fb.get("threads") or threads
        by_mem = max(0, (float(s.get("ram_gb") or 0) * 0.8 - 8) // max(0.1, cd.get("mem_gb") or 1))
        par = int(max(0, min(usable // threads, by_mem)))
        if par:
            rows.append("| %s | %s | %s | %s |" % (cd.get("name") or cls, threads, cd.get("mem_gb"), par))
    if rows:
        L.append("**可承担的 CPU 活（夜窗并行上限）**")
        L.append("")
        L.append("| 活类 | 单任务线程 | 单任务内存 GB | 并行 |")
        L.append("|---|---|---|---|")
        L.extend(rows)
        L.append("")
    if s.get("charter"):
        L.append("岗位书：`%s`" % s["charter"])
        L.append("")
    return "\n".join(L)


def render(data, doc_time):
    st = data["stations"]
    dr = drift(data)
    vault = (data["vault"].get("vault") or {})
    comp = data["compute"]

    L = []
    L.append("# 机队配置与系统说明书（FLEET-SPEC）")
    L.append("")
    L.append("> 生成时间：%s｜生成器：`Tools/fleet/fleet_doc.py`｜**本文件是生成物，不要手改正文**" % doc_time)
    L.append("> 数据源（改这里，不改正文）：`STATIONS.json` · `Tools/fleet-nodes.json` · `OS-MATRIX-v1.json` · "
             "`CPU-PLAN-v1.json` · `AGENT-CAPACITY-v1.json` · `MODEL-COMPUTE.json` · `ASSET-VAULT.json`")
    L.append("> 改完跑 `python3 Tools/fleet/fleet_doc.py --write`；只查不改跑 `--check`（有漂移 rc=1）。")
    L.append("")

    # 速查表
    L.append("## 一、速查表")
    L.append("")
    L.append("| 工位 | 机器 | 系统 | CPU | 内存 | GPU | 角色 | 状态 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for sid, s in st.items():
        o = data["os"].get(sid) or {}
        c = data["cpu"].get(sid) or {}
        gpu = s.get("gpu") or {}
        L.append("| %s | %s | %s%s | %s %sC/%sT | %sG | %s | %s | %s |" % (
            sid, _fmt(s.get("machine") or s.get("name")),
            o.get("os_label") or s.get("os") or "—",
            "" if o.get("verified") else "（未核实）",
            _fmt(c.get("cpu") or ""), _fmt(s.get("cpu_cores")), _fmt(s.get("cpu_threads")),
            _fmt(s.get("ram_gb")), _fmt(gpu.get("model")),
            (s.get("role") or "")[:18], _fmt(s.get("status"))))
    L.append("")
    total_c = sum(int(s.get("cpu_cores") or 0) for s in st.values())
    total_t = sum(int(s.get("cpu_threads") or 0) for s in st.values())
    total_ram = sum(float(s.get("ram_gb") or 0) for s in st.values())
    total_vram = sum(float((s.get("gpu") or {}).get("vram_gb") or 0) for s in st.values())
    L.append("合计：**%d 核 / %d 线程 / %.0fG 内存 / %.0fG 显存**（%d 台）"
             % (total_c, total_t, total_ram, total_vram, len(st)))
    L.append("")

    # 逐机
    L.append("## 二、逐机配置")
    L.append("")
    for i, sid in enumerate(st, 1):
        L.append(machine_section(i, sid, data, doc_time))

    # 跨机约定
    L.append("## 三、跨机约定（命令写错必失败的地方）")
    L.append("")
    L.append("| # | 铁律 | 说明 |")
    L.append("|---|---|---|")
    for r in data["rules"]:
        L.append("| %s | %s | %s |" % (r.get("id"), r.get("rule"), r.get("detail")))
    L.append("")
    L.append("队列与存储：分片 `cph4/fleet/rt/<工位>/`（一机一写者，主控只读 origin 快照）；"
             "素材字节留产出机，素材库落点 `%s`（status=%s；重建目标 %s:%s）。"
             % (_fmt(vault.get("path")), _fmt(vault.get("status")),
                _fmt((vault.get("target") or {}).get("machine")),
                _fmt((vault.get("target") or {}).get("path"))))
    L.append("")

    # 模型端点
    L.append("## 四、模型端点阶梯")
    L.append("")
    L.append("| 端点 | order | url | 角色 |")
    L.append("|---|---|---|---|")
    for g in comp.get("gateways") or []:
        L.append("| %s | %s | %s | %s |" % (
            g.get("name") or g.get("id"), g.get("order"),
            g.get("url") or "**空（未装备）**", g.get("role")))
    L.append("")
    L.append("规则：%s" % _fmt((comp.get("routing") or {}).get("rule")))
    L.append("")

    # 缺口
    gaps = []
    for sid, o in data["os"].items():
        if not o.get("verified"):
            gaps.append("%s：系统未核实（%s）——%s" % (
                sid, o.get("os_label"), o.get("decision_needed") or "装机实测后回填"))
    for g in comp.get("gateways") or []:
        if not g.get("url"):
            gaps.append("%s：端点未装备（%s）" % (g.get("name") or g.get("id"), g.get("pending") or ""))
    if vault.get("status") == "EMPTY":
        gaps.append("素材库为空（已按 CEO 令清空），重建落点 %s" %
                    _fmt((vault.get("target") or {}).get("path")))
    L.append("## 五、缺口与待决（按此清单推进，不要靠记忆）")
    L.append("")
    for i, g in enumerate(gaps, 1):
        L.append("%d. %s" % (i, g))
    L.append("")

    # 漂移
    L.append("## 六、配置一致性校验")
    L.append("")
    if dr:
        L.append("**发现 %d 处漂移（文档与配置不一致，按下面清单修数据源）：**" % len(dr))
        L.append("")
        for d in dr:
            L.append("- %s" % d)
    else:
        L.append("六源一致，无漂移。")
    L.append("")

    # 人工区
    L.append("## 七、变更日志（人工区，重新生成会保留）")
    L.append("")
    L.append(MANUAL_START)
    L.append("- 2026-11-11 首版：由 fleet_doc.py 依据六份配置生成，替代此前散落在多份 md 的机器说明。")
    L.append(MANUAL_END)
    L.append("")
    return "\n".join(L), dr


def keep_manual(new_text, old_path=DOC):
    try:
        with open(old_path, encoding="utf-8") as f:
            old = f.read()
        a = old.index(MANUAL_START)
        b = old.index(MANUAL_END) + len(MANUAL_END)
        block = old[a:b]
        a2 = new_text.index(MANUAL_START)
        b2 = new_text.index(MANUAL_END) + len(MANUAL_END)
        return new_text[:a2] + block + new_text[b2:]
    except Exception:
        return new_text


def self_test():
    import tempfile
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    data = collect()
    text, dr = render(data, "2026-11-11T00:00:00")

    chk("真实配置能生成文档且含全部工位", all(("\n### " in text) and (sid in text) for sid in data["stations"]),
        list(data["stations"]))
    chk("文档含速查表/跨机约定/端点阶梯/人工区四段",
        all(k in text for k in ("## 一、速查表", "## 三、跨机约定", "## 四、模型端点阶梯", MANUAL_START)))

    # 漂移：造一份核数不一致的假数据
    fake = {"stations": dict(data["stations"]), "os": dict(data["os"]), "cpu": dict(data["cpu"]),
            "capacity": dict(data["capacity"]), "classes": data["classes"],
            "nodes": data["nodes"], "node_by_host": data["node_by_host"],
            "compute": data["compute"], "vault": data["vault"], "rules": data["rules"]}
    sid = sorted(fake["stations"])[0]
    fake["stations"][sid] = dict(fake["stations"][sid])
    fake["stations"][sid]["cpu_cores"] = 999
    d = drift(fake)
    chk("核数与 CPU-PLAN 不一致 -> 报漂移", any("核数不一致" in x and sid in x for x in d), d)

    # 漂移：OS 不一致（仅当已核实）
    fake2 = dict(fake)
    fake2["stations"] = dict(data["stations"])
    fake2["os"] = dict(data["os"])
    osid = [k for k, v in data["os"].items() if v.get("verified")][0]
    fake2["os"][osid] = dict(fake2["os"][osid]); fake2["os"][osid]["os"] = "plan9"
    fake2["stations"][osid] = dict(fake2["stations"][osid]); fake2["stations"][osid]["os"] = "windows"
    d2 = drift(fake2)
    chk("已核实机器的 OS 与工位表不符 -> 报漂移", any("系统不一致" in x for x in d2), d2)

    # 缺机器：CPU-PLAN 少一台
    fake3 = dict(fake2)
    fake3["os"] = dict(data["os"])
    fake3["cpu"] = {k: v for k, v in data["cpu"].items() if k != sid}
    d3 = drift(fake3)
    chk("少一台机器 -> 报缺项", any("CPU-PLAN 缺" in x for x in d3), d3)

    # 人工区保留
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "d.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("x\n%s\n- 手写一条\n%s\ny" % (MANUAL_START, MANUAL_END))
        merged = keep_manual("%s\n%s\n- 新内容\n%s\n%s" % ("A", MANUAL_START, MANUAL_END, "B"), p)
        chk("重新生成保留人工区内容", "手写一条" in merged and "新内容" not in merged, merged[:80])

    print("[fleet_doc] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    data = collect()
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    text, dr = render(data, now)
    if a.check or not a.write:
        print("工位 %d：%s" % (len(data["stations"]), "、".join(data["stations"])))
        print("漂移 %d 处" % len(dr))
        for d in dr:
            print("  - %s" % d)
        if not a.write:
            print("（只查不写；要更新文档加 --write）")
        return 1 if dr else 0
    merged = keep_manual(text)
    with open(DOC, "w", encoding="utf-8") as f:
        f.write(merged)
    print("已写 %s（%d 行，漂移 %d 处）" % (os.path.relpath(DOC, ROOT), merged.count("\n") + 1, len(dr)))
    return 1 if dr else 0


if __name__ == "__main__":
    sys.exit(main())
