#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repo_map.py - 用本机大模型分块读懂整个工程（结构全量 + 内容分层）。

为什么要这么干：
  仓库 5 万 KB 文本、6800 个文件，按全文喂模型要 90 小时；但"理解工程"不需要逐字读。
  所以分两层：
    - 结构层（规则，不花模型）：目录/文件数/体量/入口/层级 -> 100% 覆盖
    - 内容层（本地模型，分块）：每个文件先抽"骨架"（标题/文档串/函数名/JSON 键），
      再按 2KB 分块让模型出 2-3 条要点；结果按 (路径+mtime+模型+提示版本) 缓存，
      可断点续跑、可限时。

分层（tier）：
  1 正典：根目录 md / docs/*.md / cph4/*.md / cph4/fleet/*.md / 各业务线 README
  2 策略：cph4/fleet/*.json（<300KB）
  3 工具：Tools/**/*.py|ps1|sh 的文档串与函数名
  4 其余（默认不跑，留给后续）

用法：
  python3 Tools/fleet/repo_map.py scan
  python3 Tools/fleet/repo_map.py run --tier 1 --model qwen3:4b-instruct --max-seconds 900
  python3 Tools/fleet/repo_map.py report
  python3 Tools/fleet/repo_map.py status

退出码：0 正常；2 Ollama 不可用；3 无内容可跑。
"""
import argparse
import ast
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "cph4", "fleet", "state", "repo-map")
CACHE = os.path.join(OUT, "cache")
CHUNKS = os.path.join(OUT, "chunks.jsonl")
INVENTORY = os.path.join(OUT, "inventory.json")
SUMMARIES = os.path.join(OUT, "summaries.jsonl")
PROGRESS = os.path.join(OUT, "progress.json")
REPORT = os.path.join(OUT, "REPO-MAP.md")
OLLAMA = (os.environ.get("OLLAMA_URL") or "http://127.0.0.1:11434").rstrip("/")
PROMPT_VERSION = "v1"

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "auto-saves",
             "archive", "_archive", ".pytest_cache", "dist", "build"}
TEXT_EXT = {".md", ".py", ".json", ".ps1", ".sh", ".yaml", ".yml", ".ts", ".js",
            ".html", ".txt", ".toml", ".mjs", ".css"}

DOMAIN = [("docs/", "docs"), ("cph4/fleet/", "fleet"), ("cph4/", "cph4"),
          ("Tools/fleet/", "tools-fleet"), ("Tools/", "tools"),
          ("gaming/", "gaming"), ("quant/", "quant"), ("media/", "media"),
          ("domain/", "domain"), ("compute/", "compute"), ("life/", "life"),
          ("research/", "research"), ("house/", "house")]


def domain_of(path):
    for prefix, name in DOMAIN:
        if path.startswith(prefix):
            return name
    return "root"


def tier_of(path, size):
    p = path
    if size > 300_000:
        return 0
    if p.startswith("\u8f6f\u8457\u7533\u8bf7\u6750\u6599/"):
        return 0
    parts = p.split("/")
    if p.endswith(".md"):
        if len(parts) == 1:                      # 根正典
            return 1
        if parts[0] == "docs" and len(parts) == 2:
            return 1
        if parts[0] == "cph4" and len(parts) == 2:
            return 1
        if p.startswith("cph4/fleet/") and len(parts) == 3:
            return 1                              # 机队顶层正典
        if len(parts) == 2 and parts[1].lower() == "readme.md":
            return 1                              # 业务线 README
    if p.startswith("cph4/fleet/") and p.endswith(".json") and len(parts) == 3:
        return 2
    if p.startswith("Tools/") and len(parts) <= 3 and p.endswith((".py", ".ps1", ".sh")):
        return 3
    return 4


def _read(path, limit=400_000):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except Exception:
        return ""


def digest_md(text):
    lines = text.splitlines()
    heads = [l.strip() for l in lines if re.match(r"^#{1,4}\s", l)]
    body, n = [], 0
    for l in lines:
        s = l.strip()
        if not s or s.startswith("#") or s.startswith("|") or s.startswith(">"):
            continue
        body.append(s)
        n += len(s)
        if n > 900:
            break
    out = []
    if heads:
        out.append("H: " + " | ".join(heads[:18]))
    out.append("T: " + " ".join(body)[:900])
    return "\n".join(out)[:2400]


def digest_py(text, ext):
    out = []
    if ext == ".py":
        try:
            tree = ast.parse(text)
            doc = ast.get_docstring(tree) or ""
            if doc:
                out.append("DOC: " + " ".join(doc.split())[:600])
            names = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    d = ast.get_docstring(node) or ""
                    names.append(node.name + (": " + " ".join(d.split())[:80] if d else ""))
            if names:
                out.append("DEF: " + "; ".join(names[:25]))
        except Exception:
            out.append("T: " + " ".join(text.split())[:600])
    else:
        lines = [l.strip() for l in text.splitlines()]
        help_lines = [l for l in lines if l.startswith(("#", "//", "<#"))][:20]
        funcs = [l for l in lines if re.match(r"^(function|def\s)\s*\w+", l, re.I)][:20]
        if help_lines:
            out.append("DOC: " + " ".join(help_lines)[:700])
        if funcs:
            out.append("DEF: " + "; ".join(funcs[:20])[:600])
        if not out:
            out.append("T: " + " ".join(text.split())[:600])
    return "\n".join(out)[:2000]


def digest_json(text):
    try:
        d = json.loads(text)
    except Exception:
        return "T: " + text[:500].replace("\n", " ")
    if isinstance(d, dict):
        keys = list(d.keys())[:30]
        return ("KEYS(%d): %s" % (len(d), ", ".join(map(str, keys))))[:900]
    if isinstance(d, list):
        sample = d[0] if d else None
        sk = list(sample.keys())[:20] if isinstance(sample, dict) else type(sample).__name__
        return "LIST(%d) item_keys: %s" % (len(d), sk)
    return "T: " + str(d)[:300]


def digest_html(text):
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    return ("TITLE: %s\nH1: %s" % ((title.group(1) if title else "")[:120],
                                   " | ".join(re.sub(r"<[^>]+>", "", h).strip()[:60] for h in h1[:8])))[:800]


def digest_of(path, ext):
    text = _read(path)
    if not text.strip():
        return ""
    if ext == ".md":
        return digest_md(text)
    if ext in (".py", ".ps1", ".sh"):
        return digest_py(text, ext)
    if ext == ".json":
        return digest_json(text)
    if ext == ".html":
        return digest_html(text)
    return "T: " + " ".join(text.split())[:700]


def chunks_of(pid, path, tier, dom, digest, size=2200):
    out, buf = [], []
    for line in digest.splitlines():
        while len(line) > size:
            out.append(line[:size])
            line = line[size:]
        if sum(len(x) for x in buf) + len(line) > size and buf:
            out.append("\n".join(buf))
            buf = []
        buf.append(line)
    if buf:
        out.append("\n".join(buf))
    return [{"id": "%s#%d" % (pid, i), "path": path, "tier": tier, "domain": dom, "text": c}
            for i, c in enumerate(out)]


def scan():
    os.makedirs(OUT, exist_ok=True)
    inv, chunk_rows = [], []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(".git")]
        for f in fn:
            abs_p = os.path.join(dp, f)
            rel = os.path.relpath(abs_p, ROOT)
            ext = os.path.splitext(f)[1].lower()
            if ext not in TEXT_EXT:
                continue
            try:
                size = os.path.getsize(abs_p)
            except OSError:
                continue
            if size == 0 or size > 2_000_000:
                continue
            tier = tier_of(rel, size)
            dom = domain_of(rel)
            inv.append({"path": rel, "ext": ext, "size": size, "tier": tier, "domain": dom})
            if tier in (1, 2, 3):
                dg = digest_of(rel, ext)
                if dg.strip():
                    chunk_rows.extend(chunks_of("%s:%d" % (rel, size), rel, tier, dom, dg)[:2])
    inv.sort(key=lambda x: (x["tier"], x["path"]))
    json.dump(inv, open(INVENTORY, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    chunk_rows.sort(key=lambda x: (x["tier"], x["path"]))
    with open(CHUNKS, "w", encoding="utf-8") as f:
        for row in chunk_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    stat = {}
    for row in inv:
        stat[str(row["tier"])] = stat.get(str(row["tier"]), 0) + 1
    print("文件 %d；分块 %d；按层 %s" % (len(inv), len(chunk_rows), stat))
    print("清单：%s" % INVENTORY)
    print("分块：%s" % CHUNKS)
    return 0


def _ask(model, prompt, ctx, timeout):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "think": False, "stream": False, "keep_alive": "10m",
            "options": {"num_ctx": ctx, "num_predict": 180, "temperature": 0.2}}
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return (json.loads(r.read()).get("message") or {}).get("content") or ""


def _cache_path(key):
    return os.path.join(CACHE, key[:2], key + ".json")


def _load_cache(key):
    try:
        return json.load(open(_cache_path(key), encoding="utf-8"))
    except Exception:
        return None


def _save_cache(key, rec):
    p = _cache_path(key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(rec, open(p, "w", encoding="utf-8"), ensure_ascii=False)


def run(tier, model, ctx, limit, max_seconds, timeout=180):
    if not os.path.exists(CHUNKS):
        print("先跑 scan", file=sys.stderr)
        return 3
    rows = [json.loads(l) for l in open(CHUNKS, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r["tier"] == tier]
    if limit:
        rows = rows[:limit]
    if not rows:
        print("tier %d 没有分块" % tier)
        return 3
    done = 0
    t0 = time.time()
    os.makedirs(CACHE, exist_ok=True)
    for i, r in enumerate(rows, 1):
        if time.time() - t0 > max_seconds:
            print("到时限，已处理 %d/%d，可重跑续上。" % (done, len(rows)))
            break
        key = hashlib.sha1(("%s|%s|%s|%s" % (PROMPT_VERSION, model, r["id"], r["text"]))
                           .encode()).hexdigest()
        if _load_cache(key):
            done += 1
            continue
        prompt = ("文件：%s\n域：%s\n骨架：\n%s\n\n"
                  "用 2-3 条中文要点说明：①它是干什么的 ②关键约束/机制 ③和谁相连。"
                  "每条一行，以「- 」开头，总字数不超过 120，不要客套，不要复述路径。"
                  % (r["path"], r["domain"], r["text"]))
        try:
            txt = _ask(model, prompt, ctx, timeout)
        except Exception as e:
            print("  x %s %s" % (r["id"], str(e)[:80]))
            continue
        rec = {"id": r["id"], "path": r["path"], "tier": r["tier"], "domain": r["domain"],
               "model": model, "text": txt.strip(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        _save_cache(key, rec)
        with open(SUMMARIES, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        done += 1
        if i % 10 == 0 or i == 1:
            print("  %d/%d %s" % (i, len(rows), r["path"]))
    json.dump({"tier": tier, "model": model, "done": done, "total": len(rows),
               "seconds": round(time.time() - t0, 1),
               "updated": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(PROGRESS, "w", encoding="utf-8"), ensure_ascii=False)
    print("完成 %d/%d，用时 %.0fs" % (done, len(rows), time.time() - t0))
    return 0


def report():
    inv = json.load(open(INVENTORY, encoding="utf-8"))
    rows = []
    if os.path.exists(SUMMARIES):
        seen = set()
        for line in open(SUMMARIES, encoding="utf-8"):
            r = json.loads(line)
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            rows.append(r)
    by_tier, by_dom, chars = {}, {}, {}
    for r in inv:
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
        by_dom[r["domain"]] = by_dom.get(r["domain"], 0) + 1
        chars[r["domain"]] = chars.get(r["domain"], 0) + r["size"]
    lines = ["# 工程全图（repo-map，自动生成）", "",
             "> 结构层 100% 由规则覆盖；内容层由本机模型分块生成，逐块可追溯（cache）。",
             "", "## 一、体量", "",
             "| 层 | 文件数 |", "|---|---|"]
    for k in sorted(by_tier):
        lines.append("| tier %s | %d |" % (k, by_tier[k]))
    lines += ["", "| 域 | 文件数 | 体量 |", "|---|---|---|"]
    for k in sorted(chars, key=lambda x: -chars[x]):
        lines.append("| %s | %d | %.1f MB |" % (k, by_dom[k], chars[k] / 1e6))
    lines += ["", "## 二、按域要点", ""]
    for dom in sorted({r["domain"] for r in rows}):
        items = [r for r in rows if r["domain"] == dom]
        lines.append("### %s（%d 块）" % (dom, len(items)))
        seen = set()
        for r in items:
            if r["path"] in seen:
                continue
            seen.add(r["path"])
            first = [x for x in r["text"].splitlines() if x.strip()][:2]
            if first:
                lines.append("- %s: %s" % (r["path"],
                                           " / ".join(x.strip("- ").strip() for x in first)[:220]))
        lines.append("")
    if os.path.exists(os.path.join(OUT, "GAPS.md")):
        lines += ["", "## 三、缺口", "",
                  "同目录 GAPS.md：只有代码没有文档的工具/策略、以及文档里失效的路径引用。", ""]
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("报告：%s（%d 文件 / %d 块）" % (REPORT, len(seen), len(rows)))
    return 0



def gaps():
    """找两类缺口：①只有代码/策略、没有任何 md 提到 ②文档引用了不存在的路径。"""
    inv = json.load(open(INVENTORY, encoding="utf-8"))
    md = [r["path"] for r in inv if r["ext"] == ".md"]
    corpus = []
    for p in md:
        t = _read(p, 300_000).lower()
        if t:
            corpus.append((p, t))

    def hits(name):
        base = name.lower()
        stem = os.path.splitext(base)[0]
        out = []
        for p, t in corpus:
            if base in t or (len(stem) >= 8 and stem in t):
                out.append(p)
        return out

    tools = [r["path"] for r in inv if r["tier"] == 3]
    pols = [r["path"] for r in inv if r["tier"] == 2]
    orphan_tools = [p for p in tools if not hits(p)]
    orphan_pols = [p for p in pols if not hits(p)]

    pat = re.compile(r"(?<![A-Za-z0-9_/])(?:cph4|docs|Tools)/[A-Za-z0-9_\-./]+\.[A-Za-z0-9]{2,4}")
    known = set(r["path"].lower() for r in inv)
    broken = {}
    for p, t in corpus:
        if p.startswith((".codely-cli/", "cph4/fleet/queue-receipts/", "cph4/fleet/memory/")):
            continue
        for m in pat.findall(t):
            q = m.strip(".,;:)\"'")
            if q.lower() in known or "*" in q or "<" in q:
                continue
            if q.startswith(("cph4/fleet/state/", "cph4/fleet/queue-receipts/", "docs/_archive/", "cph4/fleet/archive/")):
                continue
            broken.setdefault(q, set()).add(p)

    lines = ["# 工程缺口清单（自动生成）", "",
             "> 判据：文档语料 = 仓库内全部 .md；命中 = 文件全名或长度>=8 的词干出现在任一 md。",
             "> 只列事实，不判该不该补。", "",
             "## 一、只有代码、没有任何 md 提到（%d/%d）" % (len(orphan_tools), len(tools)), ""]
    fleet_n = sum(1 for p in orphan_tools if p.startswith("Tools/fleet/"))
    lines.append("> 其中 Tools/fleet 占 %d 个，其余散在 Tools/ 根层。" % fleet_n)
    lines.append("")
    for p in orphan_tools:
        lines.append("- %s" % p)
    lines += ["", "## 二、只有策略 JSON、没有任何 md 提到（%d/%d）" % (len(orphan_pols), len(pols)), ""]
    for p in orphan_pols:
        lines.append("- %s" % p)
    lines += ["", "## 三、文档引用了但仓库里没有的路径（%d）" % len(broken), ""]
    for q in sorted(broken, key=lambda x: -len(broken[x]))[:60]:
        lines.append("- %s  <- %s" % (q, ", ".join(sorted(broken[q])[:2])))
    out = os.path.join(OUT, "GAPS.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("缺口报告：%s" % out)
    print("无文档代码 %d/%d；无文档策略 %d/%d；失效引用 %d" %
          (len(orphan_tools), len(tools), len(orphan_pols), len(pols), len(broken)))
    return 0


def status():
    if os.path.exists(INVENTORY):
        inv = json.load(open(INVENTORY, encoding="utf-8"))
        print("清单 %d 文件" % len(inv))
    if os.path.exists(CHUNKS):
        n = sum(1 for _ in open(CHUNKS, encoding="utf-8"))
        print("分块 %d" % n)
    if os.path.exists(PROGRESS):
        print("进度 %s" % open(PROGRESS, encoding="utf-8").read())
    if os.path.exists(REPORT):
        print("报告 %s" % REPORT)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="用本机模型分块读懂工程")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("scan")
    r = sub.add_parser("run")
    r.add_argument("--tier", type=int, default=1)
    r.add_argument("--model", default="qwen3:4b-instruct")
    r.add_argument("--ctx", type=int, default=4096)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--max-seconds", type=int, default=900)
    r.add_argument("--timeout", type=int, default=180)
    sub.add_parser("report")
    sub.add_parser("gaps")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    if a.cmd == "scan":
        return scan()
    if a.cmd == "run":
        return run(a.tier, a.model, a.ctx, a.limit, a.max_seconds, a.timeout)
    if a.cmd == "report":
        return report()
    if a.cmd == "gaps":
        return gaps()
    if a.cmd == "status":
        return status()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
