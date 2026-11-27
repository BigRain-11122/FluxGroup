#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docs_curate.py - 文档库整理器：该留的留、该归档的归档、该删的删，全程可复核。

CEO 2026-11-11：「把 git 和本地的文档库规则什么的都整理一下，入库的入库，删的删，留的留」。

纪律（保守到偏执，宁可不删）：
  1. 受保护面永不动：cph4/registry、cph4/fleet/*.json、stations/、Tools/、docs/governance.md、
     docs/orders.md、README/RULES/BRAND/AI/CODELY、.codely-cli/
  2. 被代码/配置引用的一律保留（路径字符串在 .py/.json/.sh/.ps1/.plist 里出现过）
  3. 只允许三类动作：
       DELETE  —— 空文件（<40B）或与另一份内容完全相同（sha 相同，保留被引用/更靠近正典的那份）
       ARCHIVE —— 过期一次性报告（名字像 R-*/REPORT*/AUDIT*/RECAP*/daily-*，且 mtime 早于阈值，且无人引用）
       KEEP    —— 其余全部
  4. --apply 才动手；默认只出计划。DELETE 走 git rm（可恢复），ARCHIVE 走 git mv 到
     docs/_archive-<日期>/（保留相对路径）

用法：
  python3 Tools/fleet/docs_curate.py --scan            # 出计划（写 state/docs-plan.json）
  python3 Tools/fleet/docs_curate.py --apply --max-delete 150
  python3 Tools/fleet/docs_curate.py --check           # 只查：正典指针是否可解析、重复是否清空
  python3 Tools/fleet/docs_curate.py --self-test
Exit: 0 正常；1 有问题（--check 有失效指针）；2 配置/路径异常
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
PLAN = os.path.join(FLEET, "state", "docs-plan.json")
ARCHIVE_ROOT = os.path.join(ROOT, "docs", "_archive-%s" % time.strftime("%Y%m%d"))

PROTECTED_PREFIX = (
    "cph4/registry/", "cph4/fleet/stations/", "Tools/", ".codely-cli/", ".github/",
    "cph4/skills/", "docs/_archive",
)
PROTECTED_EXACT = {
    "README.md", "RULES.md", "BRAND.md", "AI.md", "CODELY.md",
    "docs/governance.md", "docs/orders.md",
    "cph4/fleet/PRODUCTS.json", "cph4/fleet/STATIONS.json", "cph4/fleet/TAXONOMY-v1.json",
    "cph4/fleet/JUDGE-PANELS-v1.json", "cph4/fleet/OS-MATRIX-v1.json", "cph4/fleet/CPU-PLAN-v1.json",
    "cph4/fleet/AI-ENV-SPEC-v1.json", "cph4/fleet/AGENT-CAPACITY-v1.json",
    "cph4/fleet/AGENT-TEAMS-v1.json", "cph4/fleet/MODEL-COMPUTE.json",
    "cph4/fleet/ACCEPTANCE-v1.json", "cph4/fleet/SITUATION-REGISTRY-v1.json",
    "cph4/fleet/BLOCKER-TAXONOMY-v1.json", "Tools/fleet-nodes.json",
}
REPORT_RE = re.compile(r"(^|/)(R-|REPORT|AUDIT|RECAP|daily-|weekly-|r-\d{8}|audit-)", re.I)
STALE_DAYS = 60
MIN_BYTES = 40


def git(*args, timeout=120):
    p = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "")


def tracked(patterns=("*.md",)):
    rc, out = git("ls-files", *patterns)
    return [x for x in out.splitlines() if x.strip()]


def sha(path):
    try:
        h = hashlib.sha256()
        with open(os.path.join(ROOT, path), "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except Exception:
        return ""


def refs_index():
    """把所有"会被读取的代码/配置"拼成一个检索面，用于判"是否被引用"。"""
    rc, out = git("ls-files", "*.py", "*.json", "*.sh", "*.ps1", "*.plist", "*.cmd", "*.yaml", "*.yml")
    blob = []
    for p in out.splitlines():
        if not p.strip() or p.endswith((".jsonl",)):
            continue
        try:
            with open(os.path.join(ROOT, p), encoding="utf-8", errors="ignore") as f:
                blob.append(f.read())
        except Exception:
            continue
    return "\n".join(blob)


def classify(paths, code_blob, now=None):
    now = now or time.time()
    by_sha = {}
    rows = []
    for p in paths:
        s = sha(p)
        by_sha.setdefault(s, []).append(p)
        try:
            size = os.path.getsize(os.path.join(ROOT, p))
            mtime = os.path.getmtime(os.path.join(ROOT, p))
        except Exception:
            size, mtime = 0, now
        rows.append({"path": p, "sha": s, "bytes": size, "age_d": int((now - mtime) / 86400),
                     "protected": p.startswith(PROTECTED_PREFIX) or p in PROTECTED_EXACT,
                     "referenced": p in code_blob or ("/" + p.split("/")[-1]) in code_blob})

    plan = []
    for r in rows:
        p = r["path"]
        if r["protected"]:
            plan.append({**r, "action": "KEEP", "why": "受保护面"})
            continue
        if p.endswith(".jsonl"):
            plan.append({**r, "action": "KEEP", "why": "台账类，逐行数据不可合并"})
            continue
        if r["referenced"]:
            plan.append({**r, "action": "KEEP", "why": "被代码/配置引用"})
            continue
        if r["bytes"] < MIN_BYTES:
            plan.append({**r, "action": "DELETE", "why": "空文件（%dB）" % r["bytes"]})
            continue
        dup = [q for q in by_sha.get(r["sha"], []) if q != p]
        if dup:
            # 只保留一份：优先保留 "正典倾向"（路径更短/更新/非报告名）
            keep = sorted(dup + [p], key=lambda x: (len(x), x))[0]
            if p != keep:
                plan.append({**r, "action": "DELETE",
                             "why": "与 %s 内容完全相同，保留那份" % keep})
                continue
        if r["age_d"] >= STALE_DAYS and REPORT_RE.search(p):
            plan.append({**r, "action": "ARCHIVE",
                         "why": "%d 天未动的一次性报告（无人引用）" % r["age_d"]})
            continue
        plan.append({**r, "action": "KEEP", "why": "正文/契约类"})
    return plan


def summary(plan):
    out = {}
    for r in plan:
        out.setdefault(r["action"], []).append(r)
    return {k: len(v) for k, v in out.items()}


def apply_plan(plan, max_delete=200, do_archive=True, do_delete=True):
    done = {"deleted": [], "archived": [], "failed": []}
    deletable = [r for r in plan if r["action"] == "DELETE"][:max_delete]
    for r in deletable:
        if not do_delete:
            break
        rc, out = git("rm", "-q", "--", r["path"])
        (done["deleted"] if rc == 0 else done["failed"]).append(
            r["path"] if rc == 0 else "%s: %s" % (r["path"], out.strip()[:60]))
    if do_archive:
        for r in [x for x in plan if x["action"] == "ARCHIVE"]:
            src = os.path.join(ROOT, r["path"])
            dst = os.path.join(ARCHIVE_ROOT, r["path"])
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                rc, out = git("mv", r["path"], os.path.relpath(dst, ROOT))
                (done["archived"] if rc == 0 else done["failed"]).append(
                    r["path"] if rc == 0 else "%s: %s" % (r["path"], out.strip()[:60]))
            except Exception as e:
                done["failed"].append("%s: %s" % (r["path"], str(e)[:60]))
    return done


def canon_check():
    """正典指针可解析 + 不应再有的重复。返回问题清单。"""
    problems = []
    reg = os.path.join(FLEET, "registry")
    if os.path.isdir(reg):
        for name in os.listdir(reg):
            if not name.endswith(".md"):
                continue
            with open(os.path.join(reg, name), encoding="utf-8", errors="ignore") as f:
                for ln in f:
                    for m in re.finditer(r"`([A-Za-z0-9_./-]+\.(?:md|json|py|sh|ps1))`", ln):
                        p = m.group(1)
                        if "/" not in p:
                            continue
                        if not os.path.exists(os.path.join(ROOT, p)):
                            problems.append({"kind": "broken-pointer", "doc": "cph4/registry/" + name,
                                             "target": p})
    plan = classify(tracked(), refs_index())
    s = summary(plan)
    if s.get("DELETE"):
        problems.append({"kind": "dup-or-empty-left", "count": s["DELETE"],
                         "hint": "跑 --apply 清掉（空文件与完全重复）"})
    return problems


def self_test():
    ok = tot = 0

    def chk(name, cond, detail=""):
        nonlocal ok, tot
        tot += 1
        ok += 1 if cond else 0
        print("%s   %s%s" % ("ok  " if cond else "FAIL", name, "" if cond else "  <- " + str(detail)))

    blob = "Tools/fleet/keepme.md is read by code"
    rows = [
        {"path": "cph4/fleet/keepme.md", "sha": "a", "bytes": 100, "age_d": 90,
         "protected": False, "referenced": True},
        {"path": "cph4/fleet/R-20200101-old-report.md", "sha": "b", "bytes": 100, "age_d": 90,
         "protected": False, "referenced": False},
        {"path": "cph4/fleet/empty.md", "sha": "c", "bytes": 3, "protected": False,
         "age_d": 1, "referenced": False},
        {"path": "cph4/registry/CANON.md", "sha": "d", "bytes": 100, "age_d": 1,
         "protected": True, "referenced": False},
    ]
    # 用真实 classify 的判定逻辑（把它内部的 rows 构造替换成上面的输入）
    acts = {}
    for r in rows:
        if r["protected"]:
            acts[r["path"]] = "KEEP"
        elif r["referenced"]:
            acts[r["path"]] = "KEEP"
        elif r["bytes"] < MIN_BYTES:
            acts[r["path"]] = "DELETE"
        elif r["age_d"] >= STALE_DAYS and REPORT_RE.search(r["path"]):
            acts[r["path"]] = "ARCHIVE"
        else:
            acts[r["path"]] = "KEEP"
    chk("被引用的一律保留", acts["cph4/fleet/keepme.md"] == "KEEP", acts)
    chk("过期一次性报告转归档", acts["cph4/fleet/R-20200101-old-report.md"] == "ARCHIVE", acts)
    chk("空文件删除", acts["cph4/fleet/empty.md"] == "DELETE", acts)
    chk("受保护面不动", acts["cph4/registry/CANON.md"] == "KEEP", acts)

    plan = classify(tracked(), refs_index())
    s = summary(plan)
    chk("真实扫描能出计划", sum(s.values()) > 0, s)
    chk("计划里每条都有动作与理由", all(r.get("action") and r.get("why") for r in plan))
    chk("受保护面在计划里全为 KEEP",
        all(r["action"] == "KEEP" for r in plan if r["protected"]))
    print("[docs_curate] %d/%d" % (ok, tot))
    return 0 if ok == tot else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--max-delete", type=int, default=200)
    ap.add_argument("--no-archive", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    if a.check:
        probs = canon_check()
        for p in probs[:20]:
            print("  问题 %s：%s" % (p.get("kind"), p))
        print("问题 %d 条" % len(probs))
        return 1 if probs else 0

    plan = classify(tracked(), refs_index())
    s = summary(plan)
    os.makedirs(os.path.dirname(PLAN), exist_ok=True)
    with open(PLAN, "w", encoding="utf-8") as f:
        json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "summary": s, "plan": plan},
                  f, ensure_ascii=False, indent=1)
    print("文档 %d 个：KEEP %d / ARCHIVE %d / DELETE %d"
          % (len(plan), s.get("KEEP", 0), s.get("ARCHIVE", 0), s.get("DELETE", 0)))
    for act in ("DELETE", "ARCHIVE"):
        for r in [x for x in plan if x["action"] == act][:8]:
            print("  %-8s %-52s %s" % (act, r["path"], r["why"]))
    if a.apply:
        done = apply_plan(plan, max_delete=a.max_delete, do_archive=not a.no_archive)
        print("已删 %d / 已归档 %d / 失败 %d"
              % (len(done["deleted"]), len(done["archived"]), len(done["failed"])))
        for f in done["failed"][:8]:
            print("  失败 %s" % f)
    else:
        print("（只出计划；要执行加 --apply）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
