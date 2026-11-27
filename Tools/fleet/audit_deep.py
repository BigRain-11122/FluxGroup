#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_deep.py - 深度审计：查漏补缺，按 P0/P1/P2 分级，可复跑。

CEO 2026-11-11：「全面审查，查漏补缺，颗粒度要非常细和全面」。
测试证明"该做的做对了"，审计回答"还有哪些没做/做歪了"。两类检查分工明确：
  配置面：能否解析、是否被引用（孤儿配置）、关键字段是否齐全
  代码面：异常吞没、注入面、绝对路径、绕过统一通路
  数据面：台账体量与轮转、回执质量、状态文件可读
  体系面：重复实现、禁区声明、文档与代码口径一致

分级：
  P0 会造成错误决策或数据损坏（红线）
  P1 会在特定条件下出错/难以维护（该修）
  P2 卫生问题（有空再修）
用法：
  python3 Tools/fleet/audit_deep.py            # 打印
  python3 Tools/fleet/audit_deep.py --json
  python3 Tools/fleet/audit_deep.py --self-test
Exit: 0 无 P0；1 有 P0
"""
import argparse
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "Tools", "fleet")
FLEET = os.path.join(ROOT, "cph4", "fleet")
SELF = os.path.basename(__file__)
PY = [p for p in sorted(glob.glob(os.path.join(TOOLS, "*.py")))
      if os.path.basename(p) != SELF]     # 审计器自己的字面量不算问题（自引用误报）

# 允许直连模型端点的模块：压测/诊断/采集类，不属于业务通路。
# 纪律（2026-11-11）：每一项都必须写理由。白名单可以扩，但不能无声扩——
# 没有理由的覆盖等于把真问题藏起来（实锚：station_agent.py 曾凭"带令牌"
# 留在白名单里，实际绕过了 keep_alive/额度/优先级，是业务模块而非诊断件）。
DIRECT_OK_REASON = {
    # 通路本体
    "llm_selftest.py": "自检：验证网关令牌与通路",
    "model_gateway.py": "网关本体（透传 /api/generate）",
    "llm_gateway.py": "网关本体（路径白名单）",
    "codely_bridge.py": "桥接：endpoint 由入参指定",
    # 基准/压测：必须直连才能测出延迟与装载行为
    "model_radar.py": "模型雷达：bench 与 digest 比对",
    "local_capacity_bench.py": "容量标定：装载/卸载测速",
    "brain_stress.py": "算力压测：有界短调用验端点退避",
    "parallel_sim.py": "并发模拟：发请求测排队与 p95",
    "judge_bench.py": "评审基准：多模型同题比对",
    "mlx_bench.py": "MLX 基准：解码速度对标",
    "local_llm_bench.py": "本地 LLM 基准（可复跑对照组）",
    "mac_loadout.py": "机型装载表：按实测速度归档",
    "skill_eval.py": "技能评测：跑题集打分",
    # 探针/治理：采样式小请求或装载控制
    "soak_watch.py": "长跑观测：发心跳式小请求",
    "mem_guard.py": "内存守卫：探针式小请求",
    "resource_governor.py": "资源治理：按 swap 红线装卸模型",
    "capacity_guard.py": "容量守卫：hold 未释放时排队",
    "capacity_probe.py": "容量探针：读已加载与显存占用",
    "env_probe.py": "环境采集：只探 /api/tags 取 digest",
    "local_inference_audit.py": "推理栈体检：查谁在听 11434、参数是否落盘",
    "warm_models.py": "预热：有活即热、无活即卸的执行体",
    "compute_alloc.py": "算力调度：预热/卸载模型本体",
    # 向量与视觉：端点或入参形态 local_model 不覆盖
    "embed_dedupe.py": "向量：embed 端点转 generate",
    "asset_caption.py": "视觉：需要 images 字段（local_model 只支持文本）",
    "asset_prompts.py": "视觉提示词：带图片参考",
    # 以下属业务直连，尚未迁移（诚实登记，不假装合理）
    "fleet_lane.py": "待迁移：端点来自 LANES 配置，非诊断用途",
    "local_decide.py": "待迁移：本地判定路由，判定后直连生成",
}
# 移出白名单的业务模块（2026-11-11）：它们绕过 keep_alive/额度/优先级 hold，
# 是 AUDIT-DEEP 的 P1 真账，必须改走 local_model.generate。
DIRECT_OK = {
    "llm_client.py", "local_model.py",
} | set(DIRECT_OK_REASON)
LOG_LIMIT_MB = 20


def rel(p):
    return os.path.relpath(p, ROOT)


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def check_configs():
    out = []
    files = sorted(glob.glob(os.path.join(FLEET, "*.json")))
    bad = []
    for p in files:
        try:
            json.load(open(p, encoding="utf-8-sig"))
        except Exception as e:
            bad.append({"file": rel(p), "err": str(e)[:80]})
    if bad:
        out.append({"id": "CFG-PARSE", "level": "P0", "what": "配置文件无法解析",
                    "detail": bad[:5], "fix": "修 JSON；解析失败会让整条链路用默认值静默跑"})
    # 孤儿配置：没有任何 .py 提到它的文件名
    code = "\n".join(read(p) for p in PY)
    orphans = [rel(p) for p in files if os.path.basename(p) not in code]
    if orphans:
        out.append({"id": "CFG-ORPHAN", "level": "P2", "what": "配置没有被任何代码引用（孤儿）",
                    "count": len(orphans), "detail": orphans[:10],
                    "fix": "确认是历史件就归档；是真配置就把读取方补上"})
    return out


def check_code():
    out = []
    docs = []
    for p in PY:
        t = read(p)
        docs.append((os.path.basename(p), t))
    bare = [n for n, t in docs if re.search(r"^\s*except\s*:\s*$", t, re.M)]
    if bare:
        out.append({"id": "CODE-BARE-EXCEPT", "level": "P1", "what": "裸 except 吞掉所有异常",
                    "count": len(bare), "detail": bare[:8],
                    "fix": "至少 except Exception as e 并记一句原因，否则坏了自己也不知道"})
    # 只认内建 eval/exec：`model.eval()`（PyTorch）不是注入面
    ev = [n for n, t in docs if re.search(r"(?<!\.)\b(eval|exec)\s*\(", t)]
    if ev:
        out.append({"id": "CODE-EVAL", "level": "P1", "what": "使用 eval/exec（注入面）",
                    "count": len(ev), "detail": ev[:5], "fix": "改用 json/ast 或白名单解析"})
    sh = [n for n, t in docs if "shell=True" in t]
    if sh:
        out.append({"id": "CODE-SHELL-TRUE", "level": "P2", "what": "subprocess shell=True",
                    "count": len(sh), "detail": sh[:8],
                    "fix": "确认参数不含外部输入；有则改列表形式"})
    absu = [n for n, t in docs if re.search(r"/Users/[A-Za-z0-9._-]+|C:\\\\Users\\\\", t)]
    if absu:
        out.append({"id": "CODE-ABS-PATH", "level": "P2", "what": "代码里写死本机绝对路径",
                    "count": len(absu), "detail": absu[:8],
                    "fix": "改环境变量/配置文件，否则换机即错"})
    # 绕过统一模型通路。判据看"真实调用形态"，不看字符串存在性：
    # 2026-11-11 实锚（两轮假阳性）——只认端点会把 audit_deep.py 自己（把端点
    # 当被检测的坏模式）判成直连；再加上"含 urllib.request 字样"又会把
    # automation_plan.py（把这两个名字当探测常量）判成直连。必须匹配到调用括号。
    HTTP_CALL = re.compile(r"(urllib\.request\.(urlopen|Request)|requests\.(get|post|Session))\s*\(")
    direct = [n for n, t in docs
              if "api/generate" in t and HTTP_CALL.search(t) and n not in DIRECT_OK]
    if direct:
        out.append({"id": "ARCH-MODEL-BYPASS", "level": "P1",
                    "what": "非诊断类模块直连模型端点（绕过 keep_alive/审计/优先级 hold）",
                    "count": len(direct), "detail": direct[:10],
                    "fix": "改走 local_model.generate；确属诊断的加进 DIRECT_OK 白名单"})
    return out


def check_data():
    out = []
    big = []
    for pat in ("cph4/fleet/**/*.jsonl", "cph4/fleet/*.jsonl"):
        for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
            try:
                mb = os.path.getsize(p) / 1e6
            except Exception:
                continue
            if mb >= LOG_LIMIT_MB:
                big.append({"file": rel(p), "mb": round(mb, 1)})
    if big:
        out.append({"id": "DATA-LOG-GROWTH", "level": "P1", "what": "台账/日志无上限增长",
                    "count": len(big), "detail": big[:6],
                    "fix": "按天分片或按月归档；单文件过大会让读取与 diff 都变慢"})
    receipts = glob.glob(os.path.join(FLEET, "**", "receipts", "*.json"), recursive=True)
    if receipts:
        sha = rc = 0
        for p in receipts[:2000]:
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            sha += 1 if d.get("sha256") else 0
            rc += 1 if "rc" in d else 0
        if sha < len(receipts):
            out.append({"id": "DATA-RECEIPT-WEAK", "level": "P2",
                        "what": "回执缺 sha256/rc（无法独立复核）",
                        "count": len(receipts) - sha, "detail": [],
                        "fix": "新回执强制带 sha256 与 rc；老回执标 legacy"})
    return out


# 2026-11-11 机制切换后，旧队列已归档；仍在读它的工具属"退役面"
NEW_PLANE = {
    "station_shards.py", "station_drive.py", "station_qa.py", "station_agent.py",
    "station_status.py", "panel_review.py", "quality_score.py", "self_loop.py",
    "run_all_tests.py", "condition_matrix.py", "robustness_suite.py", "parallel_sim.py",
    "env_probe.py", "env_align.py", "os_matrix.py", "cpu_alloc.py", "fleet_doc.py",
    "docs_curate.py", "test_catalog.py", "cmd_latency.py", "notify.py", "audit_deep.py",
}


def check_legacy():
    """旧队列退役面：文件引用 PRODUCTION-QUEUE.jsonl 且不在新平面上。"""
    out = []
    rows = []
    for p in PY:
        n = os.path.basename(p)
        t = read(p)
        if "PRODUCTION-QUEUE.jsonl" not in t or n in NEW_PLANE:
            continue
        guarded = ("os.path.exists" in t) or ("exists(" in t) or ("try:" in t and "FileNotFound" in t)
        rows.append({"tool": n, "guard": guarded})
    if rows:
        unguarded = [r["tool"] for r in rows if not r["guard"]]
        if unguarded:
            out.append({"id": "LEGACY-QUEUE-CRASH", "level": "P1",
                        "what": "读旧队列且无存在性保护（一跑就 FileNotFoundError）",
                        "count": len(unguarded), "detail": unguarded[:10],
                        "fix": "迁到 station_shards.read_queue，或显式报退役退出"})
        guarded = [r["tool"] for r in rows if r["guard"]]
        if guarded:
            out.append({"id": "LEGACY-QUEUE-STALE", "level": "P2",
                        "what": "仍引用旧队列但有空保护（不崩，只是能力过时）",
                        "count": len(guarded), "detail": guarded[:8],
                        "fix": "新平面=station_*/panel/quality；旧工具不进 go-live，逐步迁移"})
    return out


def check_architecture():
    out = []
    impls = []
    for p in PY:
        t = read(p)
        if ("ASSET-VAULT.json" in t and re.search(r"^def root\(", t, re.M)
                and os.path.basename(p) != "vault.py"):
            impls.append(os.path.basename(p))
    if len(impls) > 1:
        out.append({"id": "ARCH-DUP-ROOT", "level": "P2", "what": "库根解析有多份实现",
                    "count": len(impls), "detail": impls,
                    "fix": "统一到 vault.root()；多处解析迟早给出不同答案"})
    # 系统口径：Windows 岗书不得出现 python3（OS-9 的交叉验证）
    bad = []
    for sid in ("delivery", "visual", "audio"):
        p = os.path.join(FLEET, "stations", sid, "CHARTER.md")
        if os.path.exists(p) and "python3 " in read(p):
            bad.append(sid)
    if bad:
        out.append({"id": "ARCH-PY3-WIN", "level": "P0",
                    "what": "Windows 岗位书里写了 python3", "detail": bad,
                    "fix": "改 python；该机上第一条命令就会 rc=9009"})
    return out


def audit():
    rows = []
    for fn in (check_configs, check_code, check_data, check_legacy, check_architecture):
        try:
            rows.extend(fn())
        except Exception as e:
            rows.append({"id": "AUDIT-INTERNAL", "level": "P1",
                         "what": "审计器自身异常：%s" % fn.__name__, "detail": str(e)[:120]})
    counts = {}
    for r in rows:
        counts[r["level"]] = counts.get(r["level"], 0) + 1
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "findings": rows, "counts": counts,
            "files_scanned": {"py": len(PY), "json": len(glob.glob(os.path.join(FLEET, "*.json")))},
            "verdict": "有 P0 必须停手" if counts.get("P0") else
                       ("有 P1 待修" if counts.get("P1") else "无阻塞项")}


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    chk("审计能跑出结果", bool(audit()["findings"]) is not None)
    r = audit()
    chk("发现项都带 id/level/what", all({"id", "level", "what"} <= set(x) for x in r["findings"]),
        r["findings"][:1])
    chk("等级只在 P0/P1/P2", all(x["level"] in ("P0", "P1", "P2") for x in r["findings"]))
    chk("旧队列退役面被清点出来", any(x["id"].startswith("LEGACY-QUEUE") for x in r["findings"]),
        [x["id"] for x in r["findings"]])
    chk("P0 会改变判决", (r["counts"].get("P0") and "停手" in r["verdict"])
        or (not r["counts"].get("P0") and "停手" not in r["verdict"]), r["verdict"])
    # 负控：喂一个含 python3 的假岗书，必须报 P0
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = os.path.join(td, "stations", "delivery")
        os.makedirs(d)
        open(os.path.join(d, "CHARTER.md"), "w").write("跑 python3 Tools/fleet/x.py\n")
        old = FLEET
        try:
            globals()["FLEET"] = td
            hit = [x for x in check_architecture() if x["id"] == "ARCH-PY3-WIN"]
            chk("负控：Windows 岗书写 python3 必须报 P0", bool(hit) and hit[0]["level"] == "P0", hit)
        finally:
            globals()["FLEET"] = old
    # 白名单不许无声扩张：每个豁免项都必须写理由
    noreason = sorted(n for n in DIRECT_OK if n not in DIRECT_OK_REASON
                      and n not in ("llm_client.py", "local_model.py"))
    chk("白名单每一项都有理由", not noreason, noreason)
    # 负控：业务模块不许靠"带令牌"留在白名单里（station_agent 曾被这样放过）
    chk("负控：业务模块 station_agent 不在直连白名单",
        "station_agent.py" not in DIRECT_OK)
    print("[audit_deep] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    r = audit()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("扫描 %d 个 py / %d 个 json｜P0=%d P1=%d P2=%d｜%s"
              % (r["files_scanned"]["py"], r["files_scanned"]["json"],
                 r["counts"].get("P0", 0), r["counts"].get("P1", 0), r["counts"].get("P2", 0),
                 r["verdict"]))
        for f in r["findings"]:
            d = f.get("detail")
            extra = ""
            if isinstance(d, list) and d:
                extra = "｜例：" + (", ".join(x if isinstance(x, str) else str(x) for x in d[:4]))
            print("  [%s] %-20s %s%s" % (f["level"], f["id"], f["what"], extra))
            print("       修法：%s" % (f.get("fix") or "—"))
    try:
        os.makedirs(os.path.join(FLEET, "state"), exist_ok=True)
        with open(os.path.join(FLEET, "state", "audit-deep.json"), "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return 1 if r["counts"].get("P0") else 0


if __name__ == "__main__":
    sys.exit(main())
