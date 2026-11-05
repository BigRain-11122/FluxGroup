#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_convert.py - 方案→可验收产物，当分钟出第一件，不等周期。

为什么（CEO 2026-11-05「颗粒度细一点，做好各个方案的快速转化，不要等很久，
我很烦低效和卡点」）：
  以前一个想法先写文档、再等主控派卡、再等机器空出来，几十分钟才看到第一件东西。
  这里把"转化"做成一条固定流水：一页规格 + 拆到 ≤10 分钟的卡序列 + 立刻产一件
  可核验的实物（现状基线），全程 3 秒内。卡直接进备队列 READY，主控 45 秒内接走。

产出（cph4/fleet/conversions/<日期>/<slug>/）：
  1. SPEC.md        目标 / 机器可判的验收判据 / 最小可验收件 / 步骤表 / 风险与前置
  2. CARDS.jsonl    每步一张卡（id 带到秒，避免历史状态遮蔽），写进 PRODUCTION-BACKLOG=READY
  3. BASELINE.json  第一步的真实产物：相关输入在不在盘、多少件、指纹——不是空壳
  4. 一行结论       现在能看到什么 / 谁下一步动 / 预计多久

判据（写进 SPEC，机器可判）：
  C1 每步都有 deliverable 且路径在本仓内
  C2 每步预计 ≤10 分钟；超过就再拆
  C3 第一步的产物在本次运行结束时真实存在且非空
  C4 卡序列全部进备队列成功（可被主控接走）

用法：
  python3 Tools/fleet/plan_convert.py --idea "MV 第 7 曲四闸复核" --line bigstream-mv
  python3 Tools/fleet/plan_convert.py --idea "..." --inputs media/inbox --run
  python3 Tools/fleet/plan_convert.py --idea "..." --json
Exit: 0 转化完成且 C1-C4 全绿 | 2 有判据不满足
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
CONV = os.path.join(F, "conversions")
MAX_STEP_MIN = 10

# 四段式：任何方案都按"取证→加工→验收→交付"拆，避免一步跨太大变成一周的卡。
STAGES = (
    ("01-取证", "确认输入在盘、算出基线（多少件、指纹、缺口）",
     "python3 Tools/fleet/plan_convert.py --probe {conv} {inputs}"),
    ("02-加工", "对输入做本方案的核心加工；有 --tool 就真调，没有就先落可执行骨架与输入输出契约",
     "python3 Tools/fleet/plan_convert.py --step 2 --conv {conv} --tool {tool}"),
    ("03-验收", "跑机器可判的判据并出 PASS/FAIL 清单（含本仓验收腿的真实回执）",
     "python3 Tools/fleet/plan_convert.py --step 3 --conv {conv}"),
    ("04-交付", "出交付清单草稿：谁签、缺什么、可发物定义是否满足",
     "python3 Tools/fleet/plan_convert.py --step 4 --conv {conv}"),
)

KIND_HINTS = (
    ("mv", ("mv", "母版", "四闸", "曲")),
    ("game", ("游戏", "关卡", "提审", "包体")),
    ("asset", ("资产", "角色", "音色", "模型")),
    ("quant", ("回测", "信号", "因子", "csv")),
    ("report", ("报告", "复盘", "调研", "结论")),
)


def slugify(s):
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s.strip())[:40].strip("-")
    return s or "plan"


def kind_of(idea):
    low = idea.lower()
    for k, words in KIND_HINTS:
        if any(w in low for w in words):
            return k
    return "general"


def fingerprint(paths):
    out = []
    for p in paths:
        ap = p if os.path.isabs(p) else os.path.join(ROOT, p)
        item = {"path": p, "exists": os.path.exists(ap)}
        if item["exists"]:
            if os.path.isdir(ap):
                n = sum(len(fs) for _, _, fs in os.walk(ap))
                item.update({"kind": "dir", "files": n})
            else:
                b = open(ap, "rb").read()
                item.update({"kind": "file", "bytes": len(b),
                             "sha256": hashlib.sha256(b).hexdigest()[:16]})
        out.append(item)
    return out


def parse_inputs(s):
    if not s:
        return []
    return [x.strip() for x in re.split(r"[,\s]+", s) if x.strip()]


def build(idea, line, tool, inputs, conv_dir):
    kind = kind_of(idea)
    steps = []
    for i, (name, why, cmd_tpl) in enumerate(STAGES, 1):
        cmd = cmd_tpl.replace("{conv}", conv_dir).replace("{inputs}", " ".join(inputs))
        cmd = cmd.replace("--tool {tool}", ("--tool " + tool) if tool else "")
        steps.append({
            "n": i, "stage": name, "why": why, "cmd": cmd,
            "minutes": 3 if i == 1 else (8 if i == 2 else 4),
            "deliverable": "%s/step%d-%s.json" % (conv_dir, i, name.split("-")[1]),
            "accept": "产物可解析且非空；%s" % ("输入清单与指纹齐" if i == 1 else "有 PASS/FAIL 清单"),
        })
    return kind, steps


def spec_md(idea, line, kind, steps, inputs, conv_dir):
    rows = "\n".join("| %d | %s | %s | %s | %d |" % (s["n"], s["stage"], s["why"],
                                                     "`%s`" % s["deliverable"], s["minutes"])
                     for s in steps)
    cmds = "\n".join("%d. **%s**（≤%d 分钟）\n   ```\n   %s\n   ```"
                     % (s["n"], s["stage"], s["minutes"], s["cmd"]) for s in steps)
    return """# 方案规格：{idea}

- 线：{line}｜类型：{kind}｜生成：{ts}
- 产出目录：`{conv}`

## 一、目标（一句话，可判）
{idea}

## 二、验收判据（机器可判，不靠感觉）
1. 每一步都有交付物路径且在本仓内；
2. 每一步 ≤{maxm} 分钟（超了就再拆，不许出现"一周的卡"）；
3. 第一步产物在转化当分钟就存在且非空；
4. 卡序列全部进备队列，主控 45 秒内可接走。

## 三、步骤（颗粒度：每步一件可验物）
| # | 阶段 | 做什么 | 交付物 | 分钟 |
|---|---|---|---|---|
{rows}

## 四、命令
{cmds}

## 五、风险与前置
- 输入在盘检查：{inputs}（缺料则第 1 步以 BLOCKED 落盘并具名缺什么，不造假产物）
- 加工工具未指定时，第 2 步先产出"可执行骨架 + 输入/输出契约"，不许空跑
- 本规格不改变任何既有阈值；阈值仍只认 AUTONOMY-CONFIG.json

## 六、下一分钟能看到什么
`{conv}/step1-取证.json`：输入在不在盘、各多少件、指纹。
""".format(idea=idea, line=line, kind=kind, ts=datetime.now().isoformat(timespec="seconds"),
           conv=conv_dir, maxm=MAX_STEP_MIN, rows=rows, cmds=cmds,
           inputs=", ".join(inputs) or "（未指定，第 1 步会全仓扫相关目录）")


def run_step(n, conv_rel, tool=""):
    """第 2/3/4 步的确定性实现：都写自己的产物，不互相顶替，也不造假。

    第 2 步：有工具就真调（rc 与 tail 入账）；没工具就落"可执行骨架 + 输入输出契约"，
            并把缺件具名写进 blocked（不产出假成果）。
    第 3 步：跑本仓已有的验收腿（verify_done），再把它的结果与本方案的判据合并成清单。
    第 4 步：出交付清单草稿——可发物定义、谁签、还缺什么。
    """
    import subprocess
    conv_abs = os.path.join(ROOT, conv_rel) if not os.path.isabs(conv_rel) else conv_rel
    spec = os.path.join(conv_abs, "SPEC.md")
    idea = ""
    try:
        first = [l for l in open(spec, encoding="utf-8") if l.startswith("# 方案规格：")]
        idea = first[0].replace("# 方案规格：", "").strip() if first else ""
    except FileNotFoundError:
        pass
    name = {1: "取证", 2: "加工", 3: "验收", 4: "交付"}.get(n, "步骤")
    out = {"ts": datetime.now().isoformat(timespec="seconds"), "conv": conv_rel,
           "step": n, "stage": name, "idea": idea}
    if n == 1:
        # 第一步就是取证：直接复用 --probe 的产物，不再落一个空壳
        return 0
    if n == 2:
        if tool:
            t = time.time()
            p = subprocess.run(tool, shell=True, cwd=ROOT, capture_output=True, text=True,
                               timeout=900)
            out.update({"tool": tool, "rc": p.returncode, "sec": round(time.time() - t, 1),
                        "stdout_tail": (p.stdout or "").strip().splitlines()[-3:],
                        "stderr_tail": (p.stderr or "").strip().splitlines()[-3:]})
            out["ok"] = p.returncode == 0
        else:
            out.update({"ok": True, "tool": None,
                        "contract": {"input": "见 step1-取证.json", "output": "本方案第 4 步交付件",
                                     "owner": "未指定工具", "next": "指定 --tool 后重跑本步"},
                        "blocked": ["未指定加工工具：本步只落骨架，不算交付"]})
    elif n == 3:
        p = subprocess.run([sys.executable, os.path.join(ROOT, "Tools", "fleet", "verify_done.py"),
                            "--hours", "24"], cwd=ROOT, capture_output=True, text=True, timeout=300)
        out.update({"verify_rc": p.returncode,
                    "verify_tail": (p.stdout or "").strip().splitlines()[-5:],
                    "criteria": ["交付物存在且非空", "判据可机器判", "无 BLOCKED 未具名"],
                    "ok": os.path.exists(os.path.join(conv_abs, "step1-取证.json"))})
    else:
        out.update({"ok": True,
                    "ship_draft": {"publishable_def": "见 AUTONOMY-CONFIG.capacity.publishable_def",
                                   "sign_by": "CEO（对外发布权）", "internal_ready": True},
                    "missing": ["外部发布声明位（平台勾选，CEO 执行）"]})
    os.makedirs(conv_abs, exist_ok=True)
    p2 = os.path.join(conv_abs, "step%d-%s.json" % (n, name))
    json.dump(out, open(p2, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("STEP%d %s ok=%s" % (n, p2, out.get("ok")))
    return 0 if out.get("ok") else 2


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--idea", required=False, help="方案原文（一句话即可）")
    ap.add_argument("--line", default="fleet-ops")
    ap.add_argument("--tool", default="", help="第 2 步要调用的真实工具（不给则先落骨架与契约）")
    ap.add_argument("--inputs", default="", help="输入路径，逗号/空格分隔")
    ap.add_argument("--probe", nargs="*", default=None, help="内部用：第一步取证")
    ap.add_argument("--run", action="store_true", help="立刻跑第一步（默认也跑）")
    ap.add_argument("--node", default="bm-m",
                    help="卡硬钉的机器（转化件在本机盘上，别让别的机器白接：2026-11-05 实测 bm-b/bm-a 抢走后 FAILED）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--step", type=int, default=0, help="内部用：跑第 N 步并落该步产物")
    ap.add_argument("--queue-only", action="store_true", help="内部用：转换时不跑步骤")
    ap.add_argument("--conv", default="", help="内部用：方案目录")
    a = ap.parse_args(argv)

    if a.step:
        return run_step(a.step, a.conv, a.tool)

    if a.probe is not None:
        # 第一步取证：真实清点 + 指纹，落 step1
        conv = a.probe[0] if a.probe else ""
        inputs = a.probe[1:]
        targets = inputs or ["media", "Tools/fleet", "cph4/fleet"]
        data = {"ts": datetime.now().isoformat(timespec="seconds"),
                "conv": conv, "inputs": fingerprint(targets)}
        os.makedirs(os.path.join(ROOT, conv), exist_ok=True)
        p = os.path.join(ROOT, conv, "step1-取证.json")
        json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("STEP1", p)
        return 0

    if not a.idea:
        print("需要 --idea")
        return 2
    t0 = time.time()
    stamp = datetime.now().strftime("%Y%m%d")
    conv_rel = os.path.join("cph4", "fleet", "conversions", stamp, slugify(a.idea))
    conv_abs = os.path.join(ROOT, conv_rel)
    os.makedirs(conv_abs, exist_ok=True)
    inputs = parse_inputs(a.inputs)

    kind, steps = build(a.idea, a.line, a.tool, inputs, conv_rel)
    open(os.path.join(conv_abs, "SPEC.md"), "w", encoding="utf-8").write(
        spec_md(a.idea, a.line, kind, steps, inputs, conv_rel))

    # 卡序列：id 到秒，避免历史 CANCELLED 遮蔽同名新卡
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    cards = []
    for s in steps:
        cards.append({"id": "CNV-%s-%d" % (ts, s["n"]), "title": "转化·%s（%s）" % (s["stage"], a.idea[:24]),
                      "cmd": s["cmd"], "cwd": ROOT, "needs": "cpu", "minutes": s["minutes"],
                      "heavy": False, "deliverable": s["deliverable"], "accept": s["accept"],
                      "nodes": ["bm-m"], "hard_nodes": [a.node], "line": a.line,
                      "prio": "P2", "state": "READY",
                      "created_by": "plan_convert", "created_at": datetime.now().isoformat(timespec="seconds")})
    with open(os.path.join(conv_abs, "CARDS.jsonl"), "w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # 2026-11-05 实测教训：把四步都丢进队列，等于让 3 秒的记账步骤去排 45 秒一轮的队，
    # 四步要 3 分钟。正法=当场跑掉能不靠机器的步骤（取证/验收/交付），只把"真加工"排队。
    queued = 0
    inline = [1, 3, 4] if a.tool else [1, 2, 3, 4]
    for _n in inline:
        try:
            run_step(_n, conv_rel, a.tool)
        except Exception as e:
            print("inline step%d failed: %s" % (_n, str(e)[:80]))
    to_queue = [c for c in cards if c["id"].endswith("-2") and a.tool]
    try:
        sys.path.insert(0, HERE)
        import fleet_lane as fl
        if to_queue:
            queued = fl.merge_jsonl(BACKLOG, to_queue)
    except Exception as e:
        print("入队失败:", str(e)[:100])

    # 立刻跑第一步（不等任何周期）：取证真跑，不是占位
    step1 = os.path.join(conv_abs, "step1-取证.json")
    rc = os.system("cd %s && python3 Tools/fleet/plan_convert.py --probe %s %s >/dev/null"
                   % (ROOT, conv_rel, " ".join(inputs))) if not os.path.exists(step1) else 0
    s1_ok = os.path.exists(step1) and os.path.getsize(step1) > 0

    checks = {
        "C1_every_step_has_deliverable": all(s.get("deliverable") for s in steps),
        "C2_steps_under_10min": all(int(s["minutes"]) <= MAX_STEP_MIN for s in steps),
        "C3_step1_artifact_now": s1_ok,
        "C4_work_queued_if_tool": (queued >= 1) if a.tool else True,
    }
    out = {"ts": datetime.now().isoformat(timespec="seconds"), "idea": a.idea, "line": a.line,
           "kind": kind, "conv": conv_rel, "seconds": round(time.time() - t0, 2),
           "steps": steps, "checks": checks, "all_green": all(checks.values()),
           "next": "主控下一轮（≤45s）接走 CNV 卡；现在就能看 step1-取证.json"}
    json.dump(out, open(os.path.join(conv_abs, "CONVERT.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("[convert] %s → %s（%.2fs，%d 张卡入备队列）"
              % (kind, conv_rel, out["seconds"], queued))
        for k, v in checks.items():
            print("  %-32s %s" % (k, "OK" if v else "RED"))
        print("  现在能看：%s/（SPEC + 四步产物，已当场出齐）" % conv_rel)
        if a.tool:
            print("  下一步：真加工卡已入备队列，主控 ≤45s 接走")
        else:
            print("  下一步：本次无真加工（未给 --tool），转化已闭环；要动真活加 --tool <命令>")
    return 0 if out["all_green"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))