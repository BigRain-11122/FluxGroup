#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_all_tests.py - 全量测试总入口（一条命令跑完所有可跑的层）。

分层（由快到慢，任一层失败就继续跑完再汇总，不中断取证）：
  L0 回归用例      regression.py（历史故障固化的 RG-*，含负控）
  L1 单元自检      各工具 --self-test（21 套）
  L2 场景          station_qa（12 工况）/ fleet_rehearsal（14 场景）
  L3 一致性        integrity_check（17 项）/ situation_audit（情况台账）
  L4 总评分        quality_score（六维 100 分，外部阻塞单列）

纪律：
  - 每条都记录 rc、耗时、尾部输出；失败项单独列出并带修复提示
  - 不隐藏 SKIP：谁能跑谁不能跑都要写出来
  - 只读为主；唯一会写盘的是各套自检自己的临时目录
用法：
  python3 Tools/fleet/run_all_tests.py                 # 全量
  python3 Tools/fleet/run_all_tests.py --layer L0,L1    # 只跑指定层
  python3 Tools/fleet/run_all_tests.py --json
Exit: 0 全绿；1 有失败
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "Tools", "fleet")

# kind: "check" = 返回码必须 0；"report" = 只要跑通即可（rc 0/1 都是正常判决，
# 例如情况台账有 OPEN 项、总评分有扣分项——那是状态，不是工具坏了）
CASES = [
    # (层, 名称, 脚本, 附加参数)
    ("L0", "回归用例 RG-*", "regression.py", []),
    ("L1", "shards 分片/锁", "station_shards.py", ["--self-test"]),
    ("L1", "drive 自驱", "station_drive.py", ["--self-test"]),
    # 2026-11-12：单轮自检照不到"多轮×多分片×新旧格式"的缺陷（重复建卡、僵尸卡、
    # 执行体失联）。这一套专门跑连续工况，每条关键断言都配负控。
    ("L2", "chain 全链路工况", "chain_cases.py", []),
    ("L1", "social risk 风险标注", "social_risk.py", ["--self-test"]),
    ("L1", "social topics 选题", "social_topics.py", ["--self-test"]),
    ("L1", "compute offer 算力商品", "compute_offer.py", ["--self-test"]),
    # 改善台账：扫描真实事实 -> 合并 -> 校验。rc=1 表示还有待办（正常状态），
    # 只有 rc=2（假完成/证据缺失）才是问题，所以按 report 型跑。
    ("L3", "improve 改善台账", "improve_drive.py", ["--check"], "report"),
    ("L1", "panel 评审团", "panel_review.py", ["--self-test"]),
    ("L1", "agent 席位", "agent_team.py", ["--self-test"]),
    ("L1", "local loop 本地闭环", "local_loop_check.py", ["--self-test"]),
    ("L1", "view 一屏", "fleet_view.py", ["--self-test"]),
    ("L1", "cmd 命令面", "fleet_cmd.py", ["--self-test"]),
    ("L1", "work matrix 颗粒度", "work_matrix.py", ["--selftest"]),
    ("L1", "drama rules 漫剧闸", "drama_rules.py", ["--self-test"]),
    ("L1", "voice gate 语感", "voice_gate.py", ["--selftest"]),
    ("L1", "make index 索引", "make_index.py", ["--self-test"]),
    ("L1", "os matrix 跨系统", "os_matrix.py", ["--self-test"]),
    ("L1", "cpu alloc 分配", "cpu_alloc.py", ["--self-test"]),
    ("L1", "env probe 环境采集", "env_probe.py", ["--self-test"]),
    ("L1", "env align 环境对齐", "env_align.py", ["--self-test"]),
    ("L1", "fleet doc 文档生成", "fleet_doc.py", ["--self-test"]),
    ("L1", "compute alloc 算力调度", "compute_alloc.py", ["--self-test"]),
    ("L1", "brain stress 端点阶梯", "brain_stress.py", ["--mode", "ladder"]),
    ("L1", "quality score 评分器", "quality_score.py", ["--self-test"]),
    ("L1", "self loop 回环", "self_loop.py", ["--self-test"]),
    ("L1", "condition matrix 环境矩阵", "condition_matrix.py", ["--self-test"]),
    ("L1", "parallel sim 并发模型", "parallel_sim.py", ["--self-test"]),
    ("L1", "cmd latency 命令通道", "cmd_latency.py", ["--self-test"]),
    ("L1", "docs curate 文档整理", "docs_curate.py", ["--self-test"]),
    ("L1", "automation plan 排班校验", "automation_plan.py", ["--self-test"]),
    ("L1", "identity 身份唯一权威", "fleet_identity.py", ["--self-test"]),
    ("L1", "state machine 状态机权威", "state_machine.py", ["--self-test"]),
    ("L1", "drive agent 执行体生成", "install_drive_agent.py", ["--self-test"]),
    ("L1", "automation runner 调度器", "automation_runner.py", ["--self-test"]),
    ("L2", "工况 QA 12 例", "station_qa.py", []),
    ("L2", "鲁棒性 10 例", "robustness_suite.py", []),
    ("L2", "条件矩阵 80 格", "condition_matrix.py", ["--rounds", "2"]),
    ("L2", "并发争用模型", "parallel_sim.py", ["--hours", "1"]),
    # 可达性受真实机器开关影响（外部状态），按 report 处理：只要求跑通，判决写进输出
    ("L2", "命令下发延迟", "cmd_latency.py", [], "report"),
    ("L2", "预演 14 场景", "fleet_rehearsal.py", []),
    ("L3", "一致性 17 项", "integrity_check.py", []),
    ("L3", "情况台账", "situation_audit.py", [], "report"),
    ("L3", "文档库/正典指针", "docs_curate.py", ["--check"]),
    ("L3", "深度审计（P0 才判红）", "audit_deep.py", []),
    ("L3", "测试目录新鲜", "test_catalog.py", ["--check"]),
    ("L3", "文档与配置一致", "fleet_doc.py", ["--check"]),
    ("L4", "总评分", "quality_score.py", [], "report"),
]


def run_one(layer, name, script, args, kind="check", timeout=240):
    path = os.path.join(TOOLS, script)
    if not os.path.exists(path):
        return {"layer": layer, "name": name, "script": script, "rc": 127,
                "sec": 0, "tail": "脚本不存在"}
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, path] + args, capture_output=True,
                           text=True, timeout=timeout)
        rc = p.returncode
        out = ((p.stdout or "") + (p.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        rc, out = 124, "超时 %ss" % timeout
    ok = (rc == 0) if kind == "check" else (rc in (0, 1))
    return {"layer": layer, "name": name, "script": script, "rc": rc, "kind": kind,
            "ok": ok, "sec": round(time.time() - t0, 1), "tail": out[-500:]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", default="L0,L1,L2,L3,L4")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    want = set(x.strip().upper() for x in a.layer.split(",") if x.strip())

    rows = []
    for case in CASES:
        layer, name, script, args = case[:4]
        kind = case[4] if len(case) > 4 else "check"
        if layer not in want:
            continue
        r = run_one(layer, name, script, args, kind)
        rows.append(r)
        if not a.json:
            mark = "ok  " if r["ok"] else "FAIL"
            extra = "" if r["ok"] else "rc=%d" % r["rc"]
            if kind == "report" and r["rc"] == 1:
                extra = "（状态未达标，非故障）"
            print("[%s] %-28s %5.1fs %s" % (mark, name, r["sec"], extra))

    bad = [r for r in rows if not r["ok"]]
    if a.json:
        print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "total": len(rows),
                          "passed": len(rows) - len(bad), "rows": rows,
                          "failed": [{k: r[k] for k in ("layer", "name", "rc", "tail")} for r in bad]},
                         ensure_ascii=False, indent=1))
    else:
        print("\n合计 %d / 通过 %d / 失败 %d｜耗时 %.1fs"
              % (len(rows), len(rows) - len(bad), len(bad), sum(r["sec"] for r in rows)))
        for r in bad:
            print("\n== 失败：%s（%s, rc=%d）\n%s" % (r["name"], r["script"], r["rc"], r["tail"][-300:]))
    try:
        os.makedirs(os.path.join(ROOT, "cph4", "fleet", "state"), exist_ok=True)
        with open(os.path.join(ROOT, "cph4", "fleet", "state", "all-tests.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "passed": len(rows) - len(bad), "total": len(rows),
                       "failed": [r["name"] for r in bad]}, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
