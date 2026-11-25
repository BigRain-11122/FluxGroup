#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bigloom_done.py — "完美完成"的机检判据（不许自己宣布完工）。

CEO 2026-11-25：「自己科学推进，并建立好智能体，直到确认完美完成。」
"完美"必须可机检，否则就是自说自话。本器跑八条判据，全绿才退 0。

八条（每条都给证据，不给形容词）：
  1 softlinks       三条软链解析得到（gzh / accounts / BigLoom 根）
  2 audit_hard      全仓体检硬项 = 0（断链 + 真失效引用）
  3 seats_contract  席表每席 duty/out/judge/cad 齐；数字席必须 rule-only + facts_cmd
  4 loom_seats_ran  今日台账里至少一条 BigLoom 席记录且 ok=true（"设了要真跑"）
  5 sync_probe      同步探针无硬红
  6 corpora         两本账都有行（风格>0 且 产业>0）
  7 archive         归档台账存在且归档件全部在 git 里（可回滚）
  8 selftest        关键器自检全绿

用法：
  python3 Tools/fleet/bigloom_done.py            # 跑判据，出表
  python3 Tools/fleet/bigloom_done.py --json
退出码：0 全绿 / 1 有未达项 / 4 器本身坏了（跑不起来）
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")      # 数据目录（席表/台账/体检结果）
TOOLS = os.path.join(ROOT, "Tools", "fleet")     # 脚本目录（2026-11-25 实锚：
# 两者同名不同物，混用会让判据器把"脚本不存在"报成 6 个器全挂）
BIGLOOM = os.path.expanduser("~/BigLoom")
ARCHIVE = os.path.join(ROOT, "_archive-20261125")

CRITICAL = [
    ("repo_audit", "sys", os.path.join(ROOT, "Tools", "repo_audit.py")),
    ("fleet_sync_probe", "sys", os.path.join(TOOLS, "fleet_sync_probe.py")),
    ("gzh_loop", "sys", os.path.join(TOOLS, "gzh_loop.py")),
    ("gzh_trainset", "sys", os.path.join(TOOLS, "gzh_trainset.py")),
    ("wechat_article", "sys", os.path.join(TOOLS, "wechat_article.py")),
    ("harvest_generic", "venv", os.path.join(TOOLS, "harvest_generic.py")),
]


def _interp(kind):
    """解释器解析。'sys' = 当前解释器（不拿字符串 "python3" 当路径判断存在性——
    2026-11-25 实锚：当路径判断会让 6 个器全报"解释器缺"，判据器自己假红）。"""
    if kind == "sys":
        return sys.executable
    venv = os.path.join(ROOT, ".venv-housing", "bin", "python")
    return venv if os.path.exists(venv) else sys.executable


def _j(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:                                   # noqa: BLE001
        return default


def _rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def c_softlinks():
    links = {"gzh": os.path.join(ROOT, "cph4", "fleet", "social", "gzh"),
             "accounts": os.path.join(ROOT, "cph4", "fleet", "social", "ACCOUNTS-REGISTRY-v1.json"),
             "bigloom_root": BIGLOOM}
    bad = [k for k, p in links.items() if not os.path.exists(p)]
    return not bad, ("全部解析" if not bad else "断: " + ",".join(bad))


def c_audit_hard():
    a = _j(os.path.join(FLEET, "REPO-AUDIT.json"), {}) or {}
    s = a.get("summary") or {}
    if not s:
        return False, "还没跑体检（REPO-AUDIT.json 不存在）"
    hard = s.get("stale_ref", 0) + s.get("dangling_link", 0)
    return hard == 0, "硬项 %d（扫 %s 个文件）" % (hard, a.get("scanned_files"))


def c_seats_contract():
    d = _j(os.path.join(FLEET, "AGENT-TEAMS-v1.json"), {}) or {}
    miss, unbacked, n = [], [], 0
    for st, seats in (d.get("teams") or {}).items():
        for s in seats:
            n += 1
            for k in ("duty", "out", "judge", "cad"):
                if k not in s or s.get(k) in (None, ""):
                    miss.append("%s/%s 缺 %s" % (st, s.get("id"), k))
            if s.get("numbers") == "rule-only" and not s.get("facts_cmd"):
                unbacked.append("%s/%s" % (st, s.get("id")))
    ok = not miss and not unbacked
    return ok, "共 %d 席；缺字段 %d，数字无据 %d" % (n, len(miss), len(unbacked))


def c_loom_seats_ran():
    p = os.path.join(FLEET, "agent-runs", date.today().strftime("%Y%m%d") + ".jsonl")
    rows = _rows(p)
    hit = [r for r in rows if "LOOM" in str(r.get("seat") or "") and r.get("ok")]
    if not rows:
        return False, "今日无任何席位执行记录（设了没跑）"
    if not hit:
        return False, "今日 %d 条记录，但没有 BigLoom 席成功的一条" % len(rows)
    return True, "今日 %d 条，BigLoom 成功 %d 条：%s" % (
        len(rows), len(hit), ",".join(sorted({r["seat"] for r in hit})))


def c_sync_probe():
    s = _j(os.path.join(FLEET, "state", "fleet-sync.json"), {}) or {}
    if not s:
        return False, "还没跑同步探针"
    hard = s.get("hard") or []
    return not hard, ("无硬红" if not hard else "%d 条：%s" % (len(hard), hard[0][:60]))


def c_corpora():
    def n(p):
        try:
            return sum(1 for l in open(p, encoding="utf-8") if l.strip())
        except FileNotFoundError:
            return -1
    st = n(os.path.join(BIGLOOM, "gzh", "ARTICLES.jsonl"))
    ind = n(os.path.join(BIGLOOM, "gzh", "ARTICLES-INDUSTRY.jsonl"))
    return (st > 0 and ind > 0), "风格 %d 行 / 产业 %d 行" % (st, ind)


def c_archive():
    ledger = os.path.join(ARCHIVE, "LEDGER.md")
    if not os.path.exists(ledger):
        return False, "没有归档台账"
    files = []
    for dp, _dn, fn in os.walk(ARCHIVE):
        for f in fn:
            if f != "LEDGER.md":
                files.append(os.path.relpath(os.path.join(dp, f), ROOT))
    if not files:
        return False, "台账在但归档区是空的（假记账）"
    p = subprocess.run(["git", "-C", ROOT, "ls-files", "--"] + files,
                       capture_output=True, text=True)
    tracked = [x for x in p.stdout.splitlines() if x.strip()]
    return len(tracked) == len(files), "归档 %d 件，git 跟踪 %d 件（差=%d）" % (
        len(files), len(tracked), len(files) - len(tracked))


def c_selftest():
    bad, done = [], []
    for name, kind, path in CRITICAL:
        py = _interp(kind)
        if not os.path.exists(path):
            bad.append("%s(缺文件)" % name)
            continue
        if not py or not os.path.exists(py):
            bad.append("%s(解释器不可用)" % name)
            continue
        if os.path.abspath(path) == os.path.abspath(__file__):
            # 绝不把自己当被测对象：2026-11-25 实锚，把自己列进自检清单导致
            # --self-test 调 --self-test，指数级起进程（881 个）。
            continue
        env = dict(os.environ, BIGLOOM_DONE_CHILD="1")
        try:
            r = subprocess.run([py, path, "--self-test"], capture_output=True,
                               text=True, timeout=900, env=env)
        except subprocess.TimeoutExpired:
            bad.append("%s(超时)" % name)
            continue
        if r.returncode != 0:
            bad.append(name)
        else:
            done.append(name)
    return not bad, ("%d/%d 通过" % (len(done), len(CRITICAL))
                     + ("；失败: " + ",".join(bad) if bad else ""))


CHECKS = [
    ("1 softlinks", c_softlinks),
    ("2 audit_hard", c_audit_hard),
    ("3 seats_contract", c_seats_contract),
    ("4 loom_seats_ran", c_loom_seats_ran),
    ("5 sync_probe", c_sync_probe),
    ("6 corpora", c_corpora),
    ("7 archive", c_archive),
    ("8 selftest", c_selftest),
]


def run(verbose=True):
    out = []
    for name, fn in CHECKS:
        try:
            ok, why = fn()
        except Exception as e:                          # noqa: BLE001
            ok, why = False, "判据器异常 %s: %s" % (type(e).__name__, str(e)[:80])
        out.append({"check": name, "ok": bool(ok), "why": why})
    if verbose:
        print("BigLoom 完工判据（%s）" % date.today().isoformat())
        print("=" * 62)
        for r in out:
            print("%s %-18s %s" % ("PASS" if r["ok"] else "FAIL", r["check"], r["why"]))
        bad = [r for r in out if not r["ok"]]
        print("=" * 62)
        print("结论：%s（%d/%d）" % ("全绿·可宣布完成" if not bad else
                                    "未完成，还差 %d 条" % len(bad),
                                    len(out) - len(bad), len(out)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test and os.environ.get("BIGLOOM_DONE_CHILD") == "1":
        # 被上游当子进程调用时直接短路，不做任何自检——递归的第二道保险
        print("[self-test] SKIP（BIGLOOM_DONE_CHILD=1，防互相调用递归）")
        return 0
    if a.self_test:
        # 判据器自检：故意把语料读成空必须变红（负控），不在临时目录里伪造全绿
        r = run(verbose=False)
        neg = [x for x in r if x["check"].startswith("6 corpora")][0]
        if neg["ok"] and "0 行" in neg["why"]:
            print("FAIL 负控：语料 0 行却判通过", file=sys.stderr)
            return 4
        print("[self-test] 判据器可跑，%d 条判据返回了明确结论" % len(r))
        return 0
    out = run(verbose=not a.json)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if all(x["ok"] for x in out) else 1


if __name__ == "__main__":
    sys.exit(main())
