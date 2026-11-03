#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_nightly.py - 凌晨记忆归纳总闸：多项目一起称重、超预算的下沉、出报告。

为什么（CEO 2026-11-03「建立全面的机制，在凌晨每个项目记忆都要归纳清理，节约 token，
控制记忆膨胀」）：
  之前只有"一个文件一次"的工具（Tools/memory-budget-gate.py），而且是手跑；
  仓里现有 7 份 CODELY.md（gaming 41.7KB / quant 38KB / 根 29.4KB …），每份都会被
  平台注入到对应工作区的每次会话里——膨胀的代价不是磁盘，是每一轮的 token。
  本工具只做编排，不重写判据：超预算就调用既有闸（快照零删除·法条不动·同题去重），
  然后汇总成一份可审的报告，记台账，提交。

用法：
  python3 Tools/fleet/memory_nightly.py --report     # 只称重，不动文件
  python3 Tools/fleet/memory_nightly.py              # 凌晨窗内才执行（02:00-05:00）
  python3 Tools/fleet/memory_nightly.py --force      # 任意时间强制执行一次
Exit: 0 正常；2 执行后仍有文件超预算（需要人看报告）
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GATE = os.path.join(ROOT, "Tools", "memory-budget-gate.py")
OUT_DIR = os.path.join(ROOT, "cph4", "fleet", "memory-slim")
LEDGER = os.path.join(OUT_DIR, "NIGHTLY-LEDGER.jsonl")

# 预算只认一处：house 闸 Tools/memory-budget-gate.py 的执法线 51200B/120 条、
# 预警 35840B/80 条。本工具不再自造一套（自造两套=改一处等于没改，已吃过一次亏：
# 我先按 30KB 判 gaming/quant OVER，闸按 50KB 判 quant「无动作」，两边打架）。
BUDGET = {"L0": (51200, 120), "L1": (51200, 120), "sub": (51200, 120)}
WARN_BYTES, WARN_ENTRIES = 35840, 80
ENTRY_RE = re.compile(r"^- \[", re.M)   # 缺 re.M 时 ^ 只匹配全文开头 → 条数恒为 0
TOKENS_PER_BYTE = 1.0 / 3.0           # 中文为主：1 token ≈ 3 字节（估算，报告里标明是估算）


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def measure(path):
    try:
        raw = open(path, "rb").read()
    except Exception:
        return None
    txt = raw.decode("utf-8", "replace")
    return {"path": path, "bytes": len(raw),
            "entries": len(ENTRY_RE.findall(txt, 0) or []),
            "lines": txt.count("\n") + 1}


def targets():
    """L0 + 仓根 L1 + 每个子项目 CODELY.md。"""
    out = []
    l0 = os.path.expanduser("~/.codely-cli/CODELY.md")
    if os.path.exists(l0):
        out.append(("L0", l0, os.path.expanduser("~/.codely-cli/..")))
    root_l1 = os.path.join(ROOT, "CODELY.md")
    if os.path.exists(root_l1):
        out.append(("L1", root_l1, ROOT))
    for p in sorted(glob.glob(os.path.join(ROOT, "*", "CODELY.md"))):
        rel = os.path.relpath(p, ROOT)
        if rel.startswith(".git") or rel.startswith("."):
            continue
        out.append(("sub:%s" % os.path.dirname(rel), p, os.path.join(ROOT, os.path.dirname(rel))))
    return out


def run_gate(path, root):
    """调用既有闸执行下沉（快照+法条保留+同题去重）；返回 (rc, tail)。"""
    try:
        r = subprocess.run([sys.executable, GATE, "--path", path, "--root", root],
                           capture_output=True, text=True, timeout=600)
        tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        return r.returncode, (tail[-1] if tail else "")
    except Exception as e:
        return -1, str(e)[:120]


POINTER_RE = re.compile(r"^- ([\w.\-]+\.md)（(\d+) 条）=(.+)$")


def fix_pointers(path):
    """闸把所有主题文件都写在主仓 .codely-cli/memory/topics/ 下，但索引行按各子项目
    自己的相对路径写（gaming/CODELY.md 里写成 .codely-cli/...，相对 gaming/ 就是死链）。
    这里把索引改成"从本文件出发真能走到的路径"，缺文件就标注 MISSING，不假装指得到。"""
    topics = os.path.join(ROOT, ".codely-cli", "memory", "topics")
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except Exception:
        return 0, []
    fixed, broken = 0, []
    for i, ln in enumerate(lines):
        m = POINTER_RE.match(ln)
        if not m:
            continue
        name = m.group(1)
        real = os.path.join(topics, name)
        if not os.path.exists(real):
            broken.append(name)
            lines[i] = "- %s（%s 条）=[MISSING] %s" % (m.group(1), m.group(2), real)
            continue
        rel = os.path.relpath(real, os.path.dirname(path))
        new = "- %s（%s 条）=%s" % (m.group(1), m.group(2), rel)
        if new != ln:
            lines[i] = new
            fixed += 1
    if fixed or broken:
        open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return fixed, broken


def cross_file_dupes(rows):
    """不同文件里的同一条（按前 60 字归一）：多半是从别处抄过来的整条，人工合并。"""
    seen = {}
    dupes = []
    for t in rows:
        if not t.get("exists"):
            continue
        try:
            txt = open(t["path"], encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for line in txt.splitlines():
            if not line.startswith("- ["):
                continue
            k = re.sub(r"\s+", "", line[:60])
            if k in seen and seen[k] != t["key"]:
                dupes.append({"key": k[:40], "in": [seen[k], t["key"]]})
            else:
                seen[k] = t["key"]
    return dupes[:20]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)

    hour = time.localtime().tm_hour
    if not a.report and not a.force and not (2 <= hour < 5):
        print(json.dumps({"skipped": "outside 02:00-05:00 window", "hour": hour}, ensure_ascii=False))
        return 0

    rows = []
    for kind, path, root in targets():
        m = measure(path)
        if m is None:
            continue
        budget_b, budget_e = BUDGET["L0" if kind == "L0" else ("L1" if kind == "L1" else "sub")]
        over = m["bytes"] > budget_b or m["entries"] > budget_e
        warn = (not over) and (m["bytes"] > WARN_BYTES or m["entries"] > WARN_ENTRIES)
        row = {"key": kind, **m, "budget_bytes": budget_b, "budget_entries": budget_e,
               "exists": True, "over": over, "warn": warn,
               "tokens_est": int(m["bytes"] * TOKENS_PER_BYTE),
               "root": root}
        # 指针修复与"超不超预算"无关：子项目里的主题路径归闸写在主仓，索引必须能真走到
        np_fixed, np_broken = (0, [])
        if not a.report:
            np_fixed, np_broken = fix_pointers(path)
        row["pointers_fixed"], row["pointers_broken"] = np_fixed, np_broken
        if over and not a.report:
            rc, tail = run_gate(path, root)
            after = measure(path) or m
            row.update({"gate_rc": rc, "gate_tail": tail,
                        "bytes_after": after["bytes"], "entries_after": after["entries"],
                        "saved_bytes": max(0, m["bytes"] - after["bytes"]),
                        "saved_tokens_est": int(max(0, m["bytes"] - after["bytes"]) * TOKENS_PER_BYTE),
                        "still_over": after["bytes"] > budget_b})
        rows.append(row)

    dupes = cross_file_dupes(rows)
    total_before = sum(r["bytes"] for r in rows)
    total_after = sum(r.get("bytes_after", r["bytes"]) for r in rows)
    still = [r["key"] for r in rows if r.get("still_over") or (a.report and r["over"])]
    rep = {"ts": now(), "mode": "report" if a.report else "enforce",
           "files": rows, "cross_file_dupes": dupes,
           "total_bytes_before": total_before, "total_bytes_after": total_after,
           "saved_tokens_est": int(max(0, total_before - total_after) * TOKENS_PER_BYTE),
           "still_over_budget": still,
           "verdict": "GAPS" if still else "OK"}

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "NIGHTLY-%s.json" % time.strftime("%Y%m%d"))
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": rep["ts"], "mode": rep["mode"],
                            "files": len(rows), "over_before": len([r for r in rows if r["over"]]),
                            "saved_tokens_est": rep["saved_tokens_est"],
                            "still_over": still}, ensure_ascii=False) + "\n")

    print("MEMORY-NIGHTLY %s · %d 份记忆 · 合计 %.1fKB → %.1fKB（省 ~%d tokens 估算）"
          % (rep["verdict"], len(rows), total_before / 1024.0, total_after / 1024.0,
             rep["saved_tokens_est"]))
    for r in sorted(rows, key=lambda x: -x["bytes"]):
        flag = "OVER" if r["over"] else ("WARN" if r["warn"] else "ok")
        after = ("→%.1fKB" % (r.get("bytes_after", r["bytes"]) / 1024.0)) if r.get("bytes_after") else ""
        print("  %-10s %-22s %6.1fKB %3d条 预算%3dKB %s %s"
              % (r["key"], os.path.basename(os.path.dirname(r["path"])) or ".", r["bytes"] / 1024.0,
                 r["entries"], r["budget_bytes"] // 1024, flag, after))
    if dupes:
        print("  跨文件重复 %d 组（需人工合并）：%s" % (len(dupes), ", ".join(d["key"][:20] for d in dupes[:3])))
    print("  报告 " + os.path.relpath(out, ROOT))
    return 2 if still else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))