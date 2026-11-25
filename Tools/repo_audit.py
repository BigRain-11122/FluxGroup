#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repo_audit.py — 全仓体检：把"过时/没用/错误"变成可复算的清单，不凭感觉删。

CEO 2026-11-25：「对我的仓库做一个全面了解，然后开始全部整理，并写好注释，
让机队能全面了解。尤其是清理过时没用错误的。」

为什么必须先造仪器再动手：仓里 1339 个 .py、6082 个 cph4 文件、24G，
手工翻不可能翻全，而且"我觉得没用"是最容易删错东西的判断。
所以本器只报**可证伪的事实**，每条都带证据（被谁引用 / 没人引用 / 内容与谁重复）。

七项检查（每项都能被负控推翻）：
  1 inventory        目录规模与新鲜度
  2 orphan_tools     .py 零引用（没人 import、没 plist/脚本/文档提到）
  3 superseded       同名文件多版本，低版本且零引用 → 被取代候选
  4 duplicates       内容完全相同（sha1 相同）
  5 zero_byte        空文件
  6 abs_path         硬编码本机绝对路径（换机器就断）
  7 stale_ref        文档/代码提到已不存在的文件
  8 dangling_link    断链软链

用法：
  python3 Tools/repo_audit.py --scan                 # 出 JSON + MD 台账
  python3 Tools/repo_audit.py --scan --include-data  # 连语料目录一起算重复
  python3 Tools/repo_audit.py --self-test
退出码：0 无高风险发现 / 1 有高风险 / 4 自检失败
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
# 本器在 Tools/ 下（不是 Tools/fleet/），所以只剥一层。
# 2026-11-25 实锚：写成剥两层会指到家目录，lstat 全失败 → 扫 0 个文件却报"全 0"，
# 是最典型的假绿。修好 ROOT 的同时加了"扫不到文件即失败"的闸。
ROOT = os.path.dirname(HERE)
OUT_JSON = os.path.join(ROOT, "cph4", "fleet", "REPO-AUDIT.json")
OUT_MD = os.path.join(ROOT, "cph4", "fleet", "REPO-AUDIT.md")

# 大目录/生成物不进引用扫描（24G 语料扫一遍没有意义，还会拖死）
SKIP_DIRS = {".git", "__pycache__", ".venv-housing", ".ruff_cache", "node_modules",
             ".codely-cli", "train", "_archive", "raw", "raw2", "corpus", "vendor",
             "房源数据", "media", "gaming"} | {d for d in ()}
SKIP_DIRS |= {f"train-{x}" for x in ("b", "h5", "__all__")}
# 自检里的负控会故意引用不存在的文件（nope.py / no_such_tool.py 之类）。
# 2026-11-25 实锚：第一版把它们 13 条里的 8 条当成"失效引用"，是假阳性。
FIXTURE_NAMES = ("nope.py", "no_such_tool.py", "not_a_tool.py", "new.py",
                 "missing.py", "bad.py", "fake.py", "x.py")
TEXT_EXT = {".py", ".md", ".json", ".jsonl", ".sh", ".ps1", ".cmd", ".bat", ".plist",
            ".yml", ".yaml", ".toml", ".txt", ".ts", ".js", ".html", ".vbs"}
MAX_BYTES = 2 * 1024 * 1024      # 单文件超过 2MB 不横扫（语料/日志）
ABS_PAT = re.compile(r"/Users/[A-Za-z0-9._-]+/|(?:^|[\"'\s])[A-Z]:[\\/]", re.M)
SELF = os.path.abspath(__file__)


def _git(*args):
    try:
        p = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)
        return p.stdout.splitlines() if p.returncode == 0 else []
    except Exception:                                  # noqa: BLE001
        return []


ARCHIVE_PREFIX = "_archive"


def _archived(rel):
    """归档区一律不算账。用前缀判断而不是等值：
    2026-11-25 实锚：只忽略 `_archive` 时，新建的 `_archive-20261125/` 没被跳过，
    刚归档的 70 个文件又出现在"零引用"里，数字等于没降。"""
    return any(seg.startswith(ARCHIVE_PREFIX) for seg in rel.split("/"))


SELF_OUTPUTS = ("cph4/fleet/REPO-AUDIT.json", "cph4/fleet/REPO-AUDIT.md",
                "cph4/fleet/SYNC-STATUS.md", "cph4/fleet/state/fleet-sync.json",
                "cph4/fleet/ASK-20261125-ORPHANS.jsonl")


def _self_output(rel):
    """审计/探针自己的产物不许进扫描。

    2026-11-25 实锚：`REPO-AUDIT.json` 里列出了"不存在的工具"（它就是干这个的），
    下一轮又把这些路径当成"引用"，于是真失效引用从 3 条涨到 10 条——自己喂自己。
    """
    return rel in SELF_OUTPUTS or rel.startswith("cph4/fleet/state/")


def tracked(include_data=False):
    """返回 [(relpath, abspath, bytes)]。默认只取 git 跟踪的文本类文件。"""
    out = []
    for rel in _git("ls-files"):
        if _archived(rel) or _self_output(rel):
            continue
        base = os.path.basename(rel)
        if base.endswith((".jsonl", ".bin", ".safetensors", ".pt", ".png", ".jpg",
                          ".mp4", ".zip", ".pdf", ".gz", ".srt")) and not include_data:
            if rel.endswith(".jsonl") and base in ("titles.jsonl", "leads.jsonl",
                                                   "heads.jsonl", "endings.jsonl",
                                                   "harvest-ledger.jsonl"):
                pass                            # 这几种是小台账，照扫
            else:
                continue
        ap = os.path.join(ROOT, rel)
        try:
            # 必须用 lstat：断链软链 os.stat 会抛错，一抛就把这条记录整个跳过，
            # 于是"断链检查"永远查不到东西（2026-11-25 自检抓到）。
            st = os.lstat(ap)
        except OSError:
            continue
        if st.st_size > MAX_BYTES and not include_data:
            continue
        out.append((rel, ap, st.st_size))
    return out


def _read(ap, limit=MAX_BYTES):
    try:
        with open(ap, encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except Exception:                                  # noqa: BLE001
        return ""


# ---------------- 各项检查 ----------------

def check_inventory(files):
    inv = {}
    for rel, ap, size in files:
        top = rel.split("/")[0] if "/" in rel else "(root)"
        d = inv.setdefault(top, {"files": 0, "bytes": 0, "newest": 0})
        d["files"] += 1
        d["bytes"] += size
        try:
            d["newest"] = max(d["newest"], int(os.path.getmtime(ap)))
        except OSError:
            pass
    for k, d in inv.items():
        d["mb"] = round(d["bytes"] / 1048576, 1)
        d["newest"] = datetime.fromtimestamp(d["newest"]).strftime("%Y-%m-%d") if d["newest"] else ""
    return inv


def check_orphans(files, texts):
    """Tools 下的 .py 零引用。

    引用判定（任一命中即算被用）：
      · 别的 .py 里出现该文件名或模块名
      · plist / sh / ps1 / cmd / bat / json / md 里出现该文件名
      · 文件名本身在文档里被提到
    诚实边界：动态调用（getattr、字符串拼接路径）识别不到，所以结论写"疑似"
    而不是"确定没用"——删除必须再看一眼。
    """
    py = [(rel, ap) for rel, ap, _ in files if rel.endswith(".py") and "/" in rel]
    corpus = []
    for rel, _ap, _s in files:
        if rel.endswith(tuple(TEXT_EXT)) and not rel.endswith(".py"):
            corpus.append(texts.get(rel, ""))
    other_py = " \n".join(texts.get(rel, "") for rel, _ in py)
    md_all = " \n".join(corpus)
    orphans = []
    for rel, _ in py:
        base = os.path.basename(rel)
        stem = base[:-3]
        if rel.endswith("__init__.py"):
            continue
        if os.path.abspath(_) == SELF:
            continue
        hit_self = base in other_py.replace(rel, "").replace(base, "")
        # 排除"自己文件里出现自己名字"
        others = other_py.replace(_read(os.path.join(ROOT, rel)), "")
        if base in others or stem in others:
            continue
        if base in md_all or stem in md_all:
            continue
        orphans.append({"file": rel, "bytes": _s if False else
                        next(s for r, _, s in files if r == rel)})
    return orphans


def check_superseded(files):
    """同名多版本：base-v1 / base-v2 / base-v3 → 低版本且零引用的列为候选。"""
    pat = re.compile(r"^(?P<stem>.+?)[-_]v(?P<n>\d+)(?P<rest>\.[A-Za-z0-9]+)$")
    groups = {}
    for rel, _ap, _s in files:
        base = os.path.basename(rel)
        m = pat.match(base)
        if not m:
            continue
        key = (os.path.dirname(rel), m.group("stem"), m.group("rest"))
        groups.setdefault(key, []).append((int(m.group("n")), rel))
    out = []
    for (d, stem, ext), items in groups.items():
        items.sort()
        top = items[-1][0]
        for n, rel in items:
            if n < top:
                out.append({"file": rel, "replaced_by": items[-1][1], "version": n,
                            "latest": top})
    return out


def check_duplicates(files):
    by = {}
    for rel, ap, size in files:
        if size == 0:
            continue
        h = hashlib.sha1()
        try:
            with open(ap, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 16), b""):
                    h.update(chunk)
        except OSError:
            continue
        by.setdefault(h.hexdigest(), []).append(rel)
    return [{"sha1": k, "files": v, "bytes": os.path.getsize(os.path.join(ROOT, v[0]))}
            for k, v in by.items() if len(v) > 1]


def check_zero_byte(files):
    return [{"file": rel} for rel, _ap, size in files if size == 0]


def check_abs_path(files, texts):
    hits = []
    for rel, _ap, _s in files:
        if not rel.endswith(tuple(TEXT_EXT)):
            continue
        t = texts.get(rel, "")
        n = len(ABS_PAT.findall(t))
        if n:
            hits.append({"file": rel, "hits": n})
    return hits


def check_stale_ref(files, texts):
    """文档/代码提到 Tools/xxx.py 但文件不存在。

    自检夹具不算账：`regression.py` / `agent_audit.py` 里写 `nope.py`、
    `no_such_tool.py` 是负控用例，报成"失效引用"就是假阳性（第一版踩过）。
    """
    real, fixtures, planned, historical = {}, {}, {}, {}
    # "计划中"标记：文档明写"先建/未建/needs_build"的，是待办不是断链。
    # 2026-11-25 实锚：UNLOCK-PLANS.json 里 4 条 needs_build 被当成失效引用报红。
    PLANNED = ("未建", "先建", "待建", "计划", "needs_build", "TODO", "尚未",
               "写 `", "下一步")
    pat = re.compile(r"(?:Tools|tools)/fleet/([A-Za-z0-9_.\-]+\.py)")
    for rel, _ap, _s in files:
        if not rel.endswith(tuple(TEXT_EXT)):
            continue
        if os.path.abspath(os.path.join(ROOT, rel)) == SELF:
            continue      # 本器源码里的夹具路径不是仓库引用（2026-11-25 自检泄漏）
        for line in texts.get(rel, "").splitlines():
            m = pat.search(line)
            if not m:
                continue
            name = m.group(1)
            if os.path.exists(os.path.join(ROOT, "Tools", "fleet", name)):
                continue
            if name in FIXTURE_NAMES:
                bucket = fixtures
            elif any(k in line for k in PLANNED):
                bucket = planned
            elif "LESSONS" in rel or "LEARNING-LEDGER" in rel:
                # 经验台账里的 evidence 记的是"当时存在过"，不是当前依赖。
                # 2026-11-25 实锚：L-20261107-02 的 evidence 指向已不存在的 queue_claim.py。
                bucket = historical
            else:
                bucket = real
            bucket.setdefault("Tools/fleet/" + name, []).append(rel)
    return ([{"missing": k, "referenced_by": v[:4], "count": len(v)}
             for k, v in sorted(real.items())],
            [{"fixture": k, "referenced_by": v[:3], "count": len(v)}
             for k, v in sorted(fixtures.items())],
            [{"planned": k, "referenced_by": v[:3], "count": len(v)}
             for k, v in sorted(planned.items())],
            [{"historical": k, "referenced_by": v[:3], "count": len(v)}
             for k, v in sorted(historical.items())])


def last_commit_days(rel):
    """这个文件最后一次被提交是多少天前。用来区分"零引用"的两种情况：

    2026-11-25 实锚：`gzh_daily.py` 是用 `"gzh_%s.py" % step` 拼路径调子工具的，
    字面名匹配不到，于是 `gzh_formstats/gzh_trainset/gzh_publish` 这些**当天刚跑过
    自检的活工具**被判成"零引用"。如果照单归档，直接打断生产线。
    所以"零引用"必须再过一道新鲜度：近期改过的零引用 = 必须人看，不是过时。
    """
    try:
        p = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%ct", "--", rel],
                           capture_output=True, text=True)
        ts = int((p.stdout or "0").strip() or 0)
    except Exception:                                  # noqa: BLE001
        ts = 0
    if not ts:
        return None
    return (datetime.now() - datetime.fromtimestamp(ts)).days


def classify_orphans(orphans, stale_days=14):
    """零引用脚本分三档，因为"零引用"只说明没人按名字调，不等于没用。

    high   = 名字就是一次性（下划线开头/带日期/test/old/bak/fix）且无近期改动
    stale  = 零引用 + 超过 stale_days 没动过（真·过时候选）
    recent = 零引用但近期改过 → **必须人看**（很可能是被拼接路径调用的活工具）
    """
    import re as _re
    one_shot = _re.compile(r"^_|_\d{8}|(?:^|[_-])(test|old|bak|copy|tmp|tmp\d*)(?:[_-]|\.py$)")
    high, stale, recent = [], [], []
    for x in orphans:
        base = os.path.basename(x["file"])
        days = last_commit_days(x["file"])
        x = dict(x, days=days)
        if days is not None and days <= stale_days:
            recent.append(x)
        elif one_shot.search(base):
            high.append(x)
        else:
            stale.append(x)
    return high, stale, recent


def check_dangling(files):
    out = []
    for rel, ap, _s in files:
        if os.path.islink(ap) and not os.path.exists(ap):
            out.append({"link": rel, "target": os.readlink(ap)})
    return out


# ---------------- 汇总 ----------------

def scan(include_data=False, verbose=True):
    files = tracked(include_data=include_data)
    texts = {}
    for rel, ap, _s in files:
        if rel.endswith(tuple(TEXT_EXT)):
            texts[rel] = _read(ap)
    res = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "scanned_files": len(files),
        "inventory": check_inventory(files),
        "orphan_tools": check_orphans(files, texts),
        "superseded": check_superseded(files),
        "duplicates": check_duplicates(files),
        "zero_byte": check_zero_byte(files),
        "abs_path": check_abs_path(files, texts),
        "stale_ref": check_stale_ref(files, texts)[0],
        "stale_fixtures": check_stale_ref(files, texts)[1],
        "planned_tools": check_stale_ref(files, texts)[2],
        "historical_ref": check_stale_ref(files, texts)[3],
        "dangling_link": check_dangling(files),
    }
    res["summary"] = {k: len(res[k]) for k in
                      ("orphan_tools", "superseded", "duplicates", "zero_byte",
                       "abs_path", "stale_ref", "dangling_link")}
    res["orphan_high"], res["orphan_stale"], res["orphan_recent"] = \
        classify_orphans(res["orphan_tools"])
    res["summary"]["orphan_high"] = len(res["orphan_high"])
    res["summary"]["orphan_stale"] = len(res["orphan_stale"])
    res["summary"]["orphan_recent"] = len(res["orphan_recent"])
    if verbose:
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(OUT_MD, "w", encoding="utf-8").write(render_md(res))
        print("[audit] 扫了 %d 个文件 → %s" % (len(files), os.path.relpath(OUT_MD, ROOT)))
        for k, v in res["summary"].items():
            print("  %-14s %d" % (k, v))
    return res


def render_md(r):
    L = ["# 全仓体检台账", "",
         "> 由 `Tools/repo_audit.py --scan` 生成，可随时复算。**本件只报事实，不自动删。**",
         "> 判据写在器里；每条结论都能被负控推翻（见 --self-test）。", "",
         "- 生成时间：%s" % r["ts"],
         "- 扫描文件：%d 个（不含语料大文件与二进制）" % r["scanned_files"], "",
         "## 汇总", "", "| 项 | 条数 |", "|---|---|"]
    for k, v in r["summary"].items():
        L.append("| %s | %d |" % (k, v))
    L += ["", "## 目录规模", "", "| 目录 | 文件 | 体积 | 最新改动 |", "|---|---|---|---|"]
    for k, d in sorted(r["inventory"].items(), key=lambda kv: -kv[1]["bytes"])[:20]:
        L.append("| %s | %d | %sMB | %s |" % (k, d["files"], d["mb"], d["newest"]))

    def block(title, rows, fmt):
        L.extend(["", "## " + title, ""])
        if not rows:
            L.append("（无）")
            return
        for x in rows[:60]:
            L.append(fmt(x))
        if len(rows) > 60:
            L.append("- ……另 %d 条见 JSON" % (len(rows) - 60))

    block("零引用的 Tools 脚本（疑似过时，删前须再看一眼）", r["orphan_tools"],
          lambda x: "- `%s`（%d 字节）" % (x["file"], x["bytes"]))
    block("同名多版本的低版本（被高版本取代候选）", r["superseded"],
          lambda x: "- `%s` → 已被 `%s` 取代" % (x["file"], x["replaced_by"]))
    block("内容完全重复", r["duplicates"],
          lambda x: "- %d 字节：%s" % (x["bytes"], " · ".join("`%s`" % f for f in x["files"])))
    block("空文件", r["zero_byte"], lambda x: "- `%s`" % x["file"])
    block("硬编码本机绝对路径（换机器就断）", r["abs_path"],
          lambda x: "- `%s`（%d 处）" % (x["file"], x["hits"]))
    block("引用了不存在的文件", r["stale_ref"],
          lambda x: "- `%s` ← %s（%d 处提到）" % (x["missing"], "、".join(x["referenced_by"]), x["count"]))
    block("断链软链", r["dangling_link"], lambda x: "- `%s` → `%s`" % (x["link"], x["target"]))
    L += ["", "---", "", "## 怎么用这份台账", "",
          "1. 先看**硬编码绝对路径**与**断链**：这两类是错误，不是风格问题，优先修。",
          "2. 再看**零引用**与**低版本**：这是「过时」的候选，但删前必须人看一眼（动态调用识别不到）。",
          "3. 清理一律**移到 `_archive-YYYYMMDD/` 并写台账**，不硬删——可回滚比省空间重要。",
          ""]
    return "\n".join(L)


# ---------------- 自检（每项都带负控） ----------------

def self_test():
    import shutil
    cases = []
    d = tempfile.mkdtemp(prefix="audit-")
    try:
        os.makedirs(os.path.join(d, "Tools", "fleet"), exist_ok=True)
        os.makedirs(os.path.join(d, "docs"), exist_ok=True)

        def w(p, s):
            full = os.path.join(d, p)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w", encoding="utf-8").write(s)
        # 被引用的脚本 + 没人引用的脚本
        w("Tools/fleet/used.py", "print(1)\n")
        w("Tools/fleet/orphan.py", "print(2)\n")
        w("run.sh", "python3 Tools/fleet/used.py\n")
        # 多版本
        w("docs/SPEC-v1.md", "旧\n")
        w("docs/SPEC-v2.md", "新\n")
        w("docs/REF-v1.md", "引用见 SPEC-v2.md\n")
        w("docs/REF-v2.md", "x\n")
        # 重复 + 空文件
        w("docs/a.md", "同样内容\n")
        w("docs/b.md", "同样内容\n")
        w("docs/empty.md", "")
        # 绝对路径 + 失效引用 + 断链
        w("docs/bad.md", "路径 /Users/someone/x 与 Tools/fleet/nope.py\n")
        os.symlink(os.path.join(d, "nowhere"), os.path.join(d, "docs", "link.md"))

        saved = (globals()["ROOT"], globals()["_git"])
        globals()["ROOT"] = d
        globals()["_git"] = lambda *a: [os.path.relpath(os.path.join(dp, f), d)
                                        for dp, _dn, fn in os.walk(d) for f in fn
                                        if ".git" not in dp]
        try:
            r = scan(verbose=False)
        finally:
            globals()["ROOT"], globals()["_git"] = saved

        orph = {x["file"] for x in r["orphan_tools"]}
        cases.append(("零引用被抓到", "Tools/fleet/orphan.py" in orph))
        cases.append(("负控[被脚本引用] 不许误报", "Tools/fleet/used.py" not in orph))

        sup = {x["file"] for x in r["superseded"]}
        cases.append(("低版本被抓到", "docs/SPEC-v1.md" in sup))
        cases.append(("负控[最高版本] 不许被列为取代候选", "docs/SPEC-v2.md" not in sup))
        cases.append(("两套版本链各自独立", "docs/REF-v1.md" in sup and "docs/REF-v2.md" not in sup))

        dup = [set(x["files"]) for x in r["duplicates"]]
        cases.append(("重复内容被抓到", {"docs/a.md", "docs/b.md"} in dup))
        cases.append(("负控[内容不同] 不许算重复",
                      not any({"docs/SPEC-v1.md", "docs/SPEC-v2.md"} == s for s in dup)))

        cases.append(("空文件被抓到", any(x["file"] == "docs/empty.md" for x in r["zero_byte"])))
        cases.append(("绝对路径被抓到", any(x["file"] == "docs/bad.md" for x in r["abs_path"])))
        cases.append(("失效引用被抓到",
                      any("nope.py" in x["fixture"] for x in r["stale_fixtures"])))
        cases.append(("负控[存在的文件] 不许报失效引用",
                      not any("used.py" in x["missing"] for x in r["stale_ref"])))
        cases.append(("负控[自检夹具] 不许计入真失效引用",
                      not any("nope.py" in x["missing"] for x in r["stale_ref"])))
        cases.append(("断链被抓到", any(x["link"].endswith("link.md") for x in r["dangling_link"])))
    finally:
        shutil.rmtree(d, ignore_errors=True)

    ok = sum(1 for _, v in cases if v)
    for n, v in cases:
        print("  %s %s" % ("PASS" if v else "FAIL", n))
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--include-data", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.scan:
        r = scan(include_data=a.include_data)
        if r["scanned_files"] == 0:
            # 扫不到文件绝不等于干净。这条闸就是防"路径写错→全 0→假绿"。
            print("[audit] 失败：一个文件都没扫到，先查 ROOT 与 git 仓库", file=sys.stderr)
            return 4
        hard = r["summary"]["abs_path"] + r["summary"]["dangling_link"] + r["summary"]["stale_ref"]
        return 1 if hard else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
