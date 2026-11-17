#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_surface.py — 养号线"面清单"审计（机跑判据，不靠记忆）。

为什么要有它：这条线已经 20 个工具、6 份正典、几万条语料，靠人肉记"哪个自检还过、
哪个只是写了没接线"必然失真。领域整面律要求：接到点状指令先摊开整面（≥8 项、带状态
与触发条件），并且落成机读件，下一轮由工具报告未决项。

判据来源（全部可复算）：
  工具存在 → 有 --self-test → 自检 rc==0 → 有正典指针 → 有常驻接线
语料/门槛/段位/训练/会话各自取磁盘事实，不取回执。

用法：
  python3 Tools/fleet/social_surface.py            # 审计 + 写报告
  python3 Tools/fleet/social_surface.py --json     # 只出机读件
  python3 Tools/fleet/social_surface.py --full     # 连慢自检一起跑（默认跳过模型类）
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOCIAL = os.path.join(ROOT, "cph4", "fleet", "social")
TRAIN = os.path.join(SOCIAL, "train")
STATE = os.path.join(ROOT, ".codely-cli", "state")
OUT_JSON = os.path.join(STATE, "social-surface.json")
OUT_MD = os.path.join(SOCIAL, "SURFACE-REPORT.md")

# 慢自检（要加载模型/联网）默认跳过，只标"未跑"不假装通过
SLOW = {"social_eval.py", "social_drafts.py", "social_collect.py", "social_browser.py",
        "social_douyin.py", "social_comment.py", "social_sweep.py"}
TOOLS = [
    ("social_collect.py", "只读采集（页面内公开接口）"),
    ("social_sweep.py", "批量补货（评论分页+弹幕 seg.so）"),
    ("social_ingest.py", "入库（矩阵校验/打码/去重/冷却）"),
    ("social_drafts.py", "三通道草稿（人味闸+品味闸）"),
    ("social_review.py", "人工批审回流 few-shot"),
    ("social_eval.py", "黄金集评测（红线/分类/人判）"),
    ("social_profile.py", "风格画像（长度/问句/催更率）"),
    ("social_learn.py", "24h 学习循环"),
    ("social_autopilot.py", "三层自动化（限额/熔断/审计）"),
    ("social_browser.py", "T3 浏览器代操作（有头+标定）"),
    ("social_riskguard.py", "风控闸（配额/抖动/熔断）"),
    ("social_comment.py", "自视频回复（wbi+csrf+回验）"),
    ("social_douyin.py", "抖音只读采集"),
    ("social_threads.py", "会话状态机（Chatwoot 模型）"),
    ("social_topics.py", "选题"),
    ("human_corpus.py", "语料清洗+训练门槛"),
    ("train_build.py", "造集（品味闸/去重/段位配额）"),
    ("train_lora.py", "LoRA 训练+运行卡"),
    ("train_eval.py", "按质量选点+分段评测"),
    ("train_sample.py", "基座 vs LoRA 对拍"),
    ("blind_ab.py", "盲评表"),
    ("comment_taste.py", "五维品味判据"),
    ("segments.py", "人群细分识别"),
    ("train_pipe.py", "训练工作流总入口"),
]


def run_selftest(script, timeout=180):
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, script), "--self-test"],
                           capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0
        tail = [l for l in out.splitlines() if "self-test" in l]
        return ok, (tail[-1] if tail else out.strip().splitlines()[-1:] or "")[0:120], \
            round(time.time() - t0, 1)
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT %ds" % timeout, timeout
    except Exception as e:
        return False, "ERR %s" % str(e)[:80], round(time.time() - t0, 1)


def corpus_facts():
    f = {}
    p = os.path.join(SOCIAL, "corpus", "human", "own_collected.jsonl")
    q = os.path.join(SOCIAL, "corpus", "human", "QUALITY-PASS.jsonl")
    for name, path in (("corpus_all", p), ("corpus_pass", q)):
        n = 0
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                if line.strip():
                    n += 1
        f[name] = n
    raw = os.path.join(SOCIAL, "raw", "bilibili.comment.jsonl")
    f["raw_comments"] = sum(1 for l in open(raw, encoding="utf-8")) if os.path.exists(raw) else 0
    st = os.path.join(TRAIN, "STATS.json")
    if os.path.exists(st):
        try:
            f["train_rows"] = json.load(open(st, encoding="utf-8")).get("train")
        except Exception:
            pass
    return f


def latest_eval():
    d = os.path.join(TRAIN, "RUNS")
    if not os.path.isdir(d):
        return {}
    runs = sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x)))
    if not runs:
        return {}
    run = runs[-1]
    out = {"run": run}
    for f in ("RUN.json", "EVAL.json", "BEST.json"):
        p = os.path.join(d, run, f)
        if os.path.exists(p):
            try:
                out[f] = json.load(open(p, encoding="utf-8"))
            except Exception:
                out[f] = "BAD_JSON"
    return out


def threads_facts():
    p = os.path.join(STATE, "social-threads.json")
    if not os.path.exists(p):
        return {"threads": 0}
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return {"threads": "BAD_JSON"}
    by = {}
    for v in d.values():
        by[v.get("status")] = by.get(v.get("status"), 0) + 1
    return {"threads": len(d), "by_status": by}


def launchd_facts():
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
    except Exception:
        return {}
    rows = {}
    for line in out.splitlines():
        if "fluxgroup" in line and ("social" in line or "modelqueue" in line):
            parts = line.split()
            rows[parts[2]] = {"pid": parts[0], "last_exit": parts[1]}
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()

    rows = []
    for script, what in TOOLS:
        path = os.path.join(HERE, script)
        exists = os.path.exists(path)
        has_st = False
        if exists:
            has_st = "--self-test" in open(path, encoding="utf-8", errors="replace").read()
        ok, note, secs = None, "", None
        if exists and has_st and (a.full or script not in SLOW):
            ok, note, secs = run_selftest(script)
        rows.append({"tool": script, "what": what, "exists": exists,
                     "has_selftest": has_st, "selftest_ok": ok, "selftest_note": note,
                     "secs": secs})

    facts = {"corpus": corpus_facts(), "latest_run": latest_eval(),
             "threads": threads_facts(), "launchd": launchd_facts(),
             "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}

    # 未决项：由判据产生，不是人写
    gaps = []
    for r in rows:
        if not r["exists"]:
            gaps.append("%s 不存在" % r["tool"])
        elif not r["has_selftest"]:
            gaps.append("%s 没有自检" % r["tool"])
        elif r["selftest_ok"] is False:
            gaps.append("%s 自检 FAIL：%s" % (r["tool"], r["selftest_note"]))
    c = facts["corpus"]
    if c.get("corpus_pass", 0) < 2000:
        gaps.append("好语料 %d 条 < 2000，训练样本不足" % c.get("corpus_pass", 0))
    lr = facts["latest_run"]
    ev = (lr.get("EVAL.json") or {}).get("best")
    if ev and ev == "base":
        gaps.append("最近一次训练没有 checkpoint 超过基座")
    # 接线判据：光有数据不算接线，得出现在调用方源码里（静态可查、不靠自述）
    wired = {"social_threads.py": ["social_drafts.py", "social_autopilot.py",
                                    "social_ingest.py"]}
    for mod, callers in wired.items():
        name = mod[:-3]
        hit = []
        for caller in callers:
            fp = os.path.join(HERE, caller)
            if os.path.exists(fp) and name in open(fp, encoding="utf-8",
                                                  errors="replace").read():
                hit.append(caller)
        if not hit:
            gaps.append("%s 没有接线（%s 里都没调用它）" % (mod, "/".join(callers)))
    if facts["threads"].get("threads") == 0:
        gaps.append("会话状态机还没有真实会话记录")
    for k, v in facts["launchd"].items():
        if v.get("pid") in ("-", "0"):
            gaps.append("常驻 %s 最近退出码 %s（可能没在跑）" % (k, v.get("last_exit")))

    payload = {"rows": rows, "facts": facts, "gaps": gaps}
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(payload, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 1 if gaps else 0

    ok_n = sum(1 for r in rows if r["selftest_ok"] is True)
    tested = sum(1 for r in rows if r["selftest_ok"] is not None)
    print("[surface] 工具 %d 个 · 自检通过 %d/%d（另有 %d 个慢自检未跑）"
          % (len(rows), ok_n, tested, sum(1 for r in rows if r["selftest_ok"] is None)))
    print("[surface] 语料：raw %d · 可训练 %d · 过品味闸 %d"
          % (c.get("raw_comments", 0), c.get("corpus_all", 0), c.get("corpus_pass", 0)))
    if lr.get("run"):
        e = lr.get("EVAL.json") or {}
        print("[surface] 最近训练 %s · 选点 %s" % (lr["run"], e.get("best", "?")))
    print("[surface] 会话 %s · 常驻 %s"
          % (facts["threads"], ",".join(facts["launchd"].keys()) or "无"))
    if gaps:
        print("[surface] 未决 %d 项：" % len(gaps))
        for g in gaps:
            print("  - %s" % g)
    else:
        print("[surface] 无未决项")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# 养号线面清单（机跑判据·%s）\n\n" % facts["ts"])
        f.write("| 工具 | 做什么 | 存在 | 有自检 | 自检 |\n|---|---|---|---|---|\n")
        for r in rows:
            st = "未跑" if r["selftest_ok"] is None else ("PASS" if r["selftest_ok"] else "FAIL")
            f.write("| %s | %s | %s | %s | %s |\n"
                    % (r["tool"], r["what"], "Y" if r["exists"] else "N",
                       "Y" if r["has_selftest"] else "N", st))
        f.write("\n## 磁盘事实\n\n```\n%s\n```\n" % json.dumps(facts, ensure_ascii=False, indent=1))
        f.write("\n## 未决项（%d）\n\n" % len(gaps))
        for g in gaps:
            f.write("- %s\n" % g)
    print("[surface] → %s / %s" % (os.path.relpath(OUT_MD, ROOT), os.path.relpath(OUT_JSON, ROOT)))
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
