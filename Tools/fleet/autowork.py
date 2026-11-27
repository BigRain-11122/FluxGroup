#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""autowork.py - repetitive, low-risk work handed to the local 4B, on a schedule.

Scope by design: only work whose output can be checked against on-disk facts.
  W1 failure triage : every FAILED queue row -> one-line cause + one next action (rc/text given)
  W2 receipt digest : today's receipts -> 5-line digest for the CEO (paths cited, no new facts)
Idempotent: work already done today is skipped (state file). Never posts, never dispatches.
"""
import json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(F, "dispatcher", "AUTOWORK.md")
STATE = os.path.join(F, "dispatcher", "autowork-state.json")
# 模型名唯一来源=LOCAL-MODEL-POLICY.json（见 model_policy.py）
try:
    from model_policy import resident as _resident
    MODEL = _resident()
except Exception:
    # 2026-11-08：不再写死对照档。写死 qwen3:4b-instruct 会另拉一个 4B，把常驻的
    # qwen3.5:4b-mlx 挤出内存（OLLAMA_MAX_LOADED_MODELS 只有 4 个槽）。改读策略单源。
    import local_model as _lm
    MODEL = ((_lm._duties().get("resident") or {}).get("model")
             or "qwen3.5:4b-mlx")


def call(prompt):
    # 走统一通路（keep_alive 策略、调用审计、主控优先 hold 全生效）
    import local_model as _lm2
    return _lm2.generate(prompt, cls="master", timeout=180, keep_alive="5m",
                         num_ctx=8192, temperature=0.2, why="autowork")


def main():
    today = datetime.now().strftime("%Y%m%d")
    st = {}
    if os.path.exists(STATE):
        try:
            st = json.load(open(STATE, encoding="utf-8"))
        except Exception:
            st = {}
    if st.get("date") != today:
        st = {"date": today, "done": {}}
    done = []

    qp = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
    if not os.path.exists(qp):
        # 2026-11-11 机制切换：旧队列已归档，本工具由 station_drive 接管
        print("autowork 已退役：旧队列 %s 已归档（2026-11-11）。"
              "请用 python3 Tools/fleet/station_drive.py --once 走分片自驱。" % qp)
        return 2
    rows = [json.loads(l) for l in open(qp, encoding="utf-8") if l.strip()]
    failed = [r for r in rows if r.get("state") == "FAILED"]
    if failed and not st["done"].get("triage"):
        items = "\n".join("- %s | rc=%s | %s" % (r.get("id"), r.get("rc"),
                                                (r.get("failure") or "无记录")[:200]) for r in failed[:5])
        ans = call("你是机队运维判读席，只依据给出的失败记录作答，不要编造命令或路径。\n"
                   "对每条失败给一行：`卡片 -> 最可能原因 | 下一步动作(谁做什么)`。总长<=300字。\n" + items)
        if ans:
            st["done"]["triage"] = ans
            done.append("失败归因 %d 条" % len(failed[:5]))

    rd = os.path.join(F, "queue-receipts")
    fresh = []
    if os.path.isdir(rd):
        for f in sorted(os.listdir(rd)):
            p = os.path.join(rd, f)
            if os.path.isfile(p) and datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y%m%d") == today:
                fresh.append(f)
    if fresh and not st["done"].get("digest"):
        ans = call("下面这些文件是机队今天落库的产出清单。只依据文件名与数量写 4 行中文日报："
                   "①今天产出了几件、覆盖哪几条线 ②哪条线明显偏少 ③建议明天先做的一件事。"
                   "不要编造文件里没有的内容，不要写文件名以外的事实。\n" + "\n".join(fresh[:30]))
        if ans:
            st["done"]["digest"] = ans
            done.append("回执日报 %d 份" % len(fresh))

    lines = ["# 本地自动化产物 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    if st["done"].get("triage"):
        lines += ["## 失败归因", st["done"]["triage"], ""]
    if st["done"].get("digest"):
        lines += ["## 回执日报", st["done"]["digest"], ""]
    if not done:
        lines.append("- 今日无可做的重复件")
    lines.append("\n---\n*本地 4B · 只做重复性判读，不派单不发帖*")
    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[autowork] %s" % (", ".join(done) or "nothing due"))
    return 0


if __name__ == "__main__":
    sys.exit(main())