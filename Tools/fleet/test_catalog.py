#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_catalog.py - 生成测试目录（测了什么、各多少例、还缺什么），再交给循环跑。

为什么生成：手写的测试清单三天就过期。本工具从各测试模块**直接数**用例，
把"层/模块/例数/覆盖什么/缺口"整理成 cph4/fleet/TEST-PLAN-v2.md，
再由 run_all_tests.py 负责跑、quality_score.py 负责算分。

用法：
  python3 Tools/fleet/test_catalog.py --write    # 生成 TEST-PLAN-v2.md
  python3 Tools/fleet/test_catalog.py            # 只打印摘要
  python3 Tools/fleet/test_catalog.py --self-test
"""
import argparse
import importlib
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "Tools", "fleet")
FLEET = os.path.join(ROOT, "cph4", "fleet")
DOC = os.path.join(FLEET, "TEST-PLAN-v2.md")
sys.path.insert(0, TOOLS)

# 已覆盖的测试面（模块 → 说明）
COVER = [
    ("regression", "CASES", "历史故障固化的回归断言（每条带负控）"),
    ("station_qa", "CASES", "机内执行工况：停/离线/无命令/人判/低盘/坏卡"),
    ("fleet_rehearsal", "SCEN", "跨机流转预演：交接/重复/离线/回执/漂移"),
    ("robustness_suite", "CASES", "存储与数据面：并发写/崩溃/坏行/状态机/数量级"),
]

# 明确还没覆盖的（写死，改口径要改这里；不许悄悄消失）
GAPS = [
    ("真 Windows 执行", "三台生产机的命令只在沙箱里模拟过，没有一次真机跑通用例"),
    ("真 GPU 出片", "ComfyUI/i2v 链路没有端到端跑过（无在线 GPU 机）"),
    ("真实网络分区", "只模拟了端点不可达，没测过 tailnet 抖动/半连通下的重试风暴"),
    ("长跑 24h", "所有用例都是秒级；没有 24h 稳定性（内存泄漏/句柄泄漏）观测"),
    ("断电恢复", "只测了半截文件，没测过 fsync 掉电后分片与回执的一致性"),
    ("大素材 IO", "1000 张卡测了，但没测 GB 级产物搬运与哈希的时间预算"),
    ("多机并发写同一分片", "单机并发测了；跨机同写不该发生，但没有闸去拦"),
    ("权限与越权", "只测了「不对外」的字面约束，没测凭据文件权限与越权路径"),
]


def count(module, attr):
    try:
        m = importlib.import_module(module)
        v = getattr(m, attr, None)
        return len(v) if v is not None else None
    except Exception as e:
        return "读取失败：%s" % str(e)[:60]


def suites_by_layer():
    try:
        import run_all_tests as rt
        out = {}
        for c in rt.CASES:
            out.setdefault(c[0], []).append(c[1])
        return out
    except Exception:
        return {}


def build():
    rows = []
    for mod, attr, why in COVER:
        rows.append({"module": mod, "attr": attr, "count": count(mod, attr), "why": why})
    try:
        import condition_matrix as cm
        spec, cpu, osm = cm.load_all()
        n_env = len(cm.cases_env(spec))
        n_cpu = len(cm.cases_cpu(cpu))
        n_os = len(cm.cases_os(osm))
        cond = {"env": n_env, "cpu": n_cpu, "os": n_os, "total": n_env + n_cpu + n_os}
    except Exception as e:
        cond = {"error": str(e)[:80]}
    try:
        import parallel_sim as ps
        par = list(ps.analyse(hours=1.0)["result"].keys())
    except Exception:
        par = []
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "cover": rows, "condition": cond,
            "parallel": par, "layers": suites_by_layer(), "gaps": GAPS}


def render(rep):
    L = []
    L.append("# 测试目录与缺口（TEST-PLAN v2）· %s" % rep["ts"][:10])
    L.append("")
    L.append("> 生成物：`python3 Tools/fleet/test_catalog.py --write`。改测试请改模块，不要手改本文件。")
    L.append("> 跑法：`python3 Tools/fleet/run_all_tests.py`（全量）｜`python3 Tools/fleet/quality_score.py`（算分）")
    L.append("")
    L.append("## 一、分层面（跑什么）")
    L.append("")
    L.append("| 层 | 内容 |")
    L.append("|---|---|")
    names = {"L0": "回归用例", "L1": "单元自检", "L2": "场景与条件", "L3": "一致性/文档", "L4": "总评分"}
    for layer, items in sorted(rep["layers"].items()):
        L.append("| %s %s | %s |" % (layer, names.get(layer, ""), "、".join(items)))
    L.append("")
    L.append("## 二、用例面（各多少例）")
    L.append("")
    L.append("| 模块 | 例数 | 覆盖什么 |")
    L.append("|---|---|---|")
    for r in rep["cover"]:
        L.append("| `%s.%s` | %s | %s |" % (r["module"], r["attr"], r["count"], r["why"]))
    c = rep["condition"]
    if "total" in c:
        L.append("| `condition_matrix`（生成） | %d（环境 %d / 核力 %d / 系统 %d） | 5 台机 × 环境偏差 × 核力禁区 |"
                 % (c["total"], c["env"], c["cpu"], c["os"]))
    L.append("| `parallel_sim`（生成） | %d 组合 | 单端点平摊/突发 × 有/无深席上升 |" % len(rep["parallel"]))
    L.append("")
    L.append("## 三、还没覆盖的（缺口，按优先级）")
    L.append("")
    L.append("| # | 缺口 | 为什么重要 |")
    L.append("|---|---|---|")
    for i, (name, why) in enumerate(rep["gaps"], 1):
        L.append("| %d | %s | %s |" % (i, name, why))
    L.append("")
    L.append("## 四、循环与迭代（怎么转起来）")
    L.append("")
    L.append("1. `run_all_tests.py` 全量跑一遍（层内失败继续跑完再汇总）。")
    L.append("2. 失败项先分「真故障」与「状态未达标」，后者不改口径不刷分。")
    L.append("3. 真故障走：定根因 → 改成断言 → 加负控（能判「该红必须红」）→ 重跑全量。")
    L.append("4. `self_loop.py` 自动修登记过的确定性项（文档漂移、本机探针），其余留给人判。")
    L.append("5. 每轮分数与残余阻塞写 `state/quality-history.jsonl`，趋势可查。")
    L.append("")
    L.append("**退出条件**：全量 0 失败且 `quality_score` 只剩外部阻塞（服务暂停／机器离线／未装机）。")
    return "\n".join(L)


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    rep = build()
    chk("能数出四类用例", all(isinstance(r["count"], int) and r["count"] > 0 for r in rep["cover"]), rep["cover"])
    chk("条件矩阵有总数", rep["condition"].get("total", 0) >= 50, rep["condition"])
    chk("缺口清单非空且每条带理由", rep["gaps"] and all(w for _, w in rep["gaps"]))
    doc = render(rep)
    chk("渲染含四段", all(k in doc for k in ("一、分层面", "二、用例面", "三、还没覆盖", "四、循环")))
    chk("渲染里没有未替换占位", "{" not in doc.replace("{}", ""))
    print("[test_catalog] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def _norm(ln):
    """比对前把"生成日期"抹平。

    文档头带 `· YYYY-MM-DD`，而校验器按"今天"重建——过了零点必然整篇判不一致，
    每天都要人工重写一次（2026-11-14 实锚）。日期不是内容，比较时归一化；
    行内其它字符照旧逐字比，真漂移仍然会红。
    """
    return re.sub(r"·\s*\d{4}-\d{2}-\d{2}", "· <date>", str(ln).rstrip())


def doc_diff(doc):
    """把 render 结果与磁盘 TEST-PLAN-v2.md 比对。

    2026-11-11 实锚：这一层原来只有 `--self-test`（在内存里 build+render 再断言
    自己），**从不比对磁盘文件**，所以全量 38/38 全绿的同时 TEST-PLAN-v2.md
    已经是旧版。用例名叫"测试目录新鲜"，实际没有一条检查新鲜度。
    """
    try:
        with open(DOC, encoding="utf-8") as f:
            disk = f.read()
    except Exception:
        return ["文档不存在：%s（先跑 --write）" % DOC]
    want = [_norm(ln) for ln in (doc + "\n").splitlines()]
    have = [_norm(ln) for ln in disk.splitlines()]
    if want == have:
        return []
    out = []
    for i, (a, b) in enumerate(zip(want, have)):
        if a != b:
            out.append("第 %d 行不一致：文档=%r 应为=%r" % (i + 1, b[:70], a[:70]))
            if len(out) >= 5:
                break
    if not out:
        out.append("行数不一致：文档 %d 行，应为 %d 行" % (len(have), len(want)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rep = build()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0
    doc = render(rep)
    total = sum(r["count"] for r in rep["cover"] if isinstance(r["count"], int))
    print("模块用例 %d 条 + 条件 %s 格 + 并发 %d 组合 + 层 %d"
          % (total, rep["condition"].get("total", "?"), len(rep["parallel"]), len(rep["layers"])))
    for r in rep["cover"]:
        print("  %-20s %s" % (r["module"], r["count"]))
    if a.check:
        dd = doc_diff(doc)
        print(("文档与实测不一致 %d 条：" % len(dd)) if dd else "文档与实测一致")
        for x in dd:
            print("  - %s" % x)
        return 1 if dd else 0
    if a.write:
        with open(DOC, "w", encoding="utf-8") as f:
            f.write(doc + "\n")
        print("→ %s" % os.path.relpath(DOC, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
