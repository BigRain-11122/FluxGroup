#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_reviewer.py - 每日代码/文档评审：本地模型看最近改动，挑风险。

只读、只出意见；不阻断提交。
"""
import json, os, subprocess, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet"); S = os.path.join(F, "state")
OUTDIR = os.path.join(F, "REVIEWS")
MODEL = os.environ.get("REVIEW_MODEL") or "qwen3.5:4b-mlx"


def sh(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=60).stdout


def ask(prompt):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "think": False, "stream": False, "keep_alive": "10m",
            "options": {"num_ctx": 8192, "num_predict": 300, "temperature": 0.2}}
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return ((json.loads(r.read()).get("message") or {}).get("content") or "").strip()


def main():
    day = time.strftime("%Y%m%d")
    files = [l for l in sh(["git", "log", "--since=24 hours", "--name-only", "--pretty=format:"]).splitlines() if l.strip()]
    seen, pick = set(), []
    for f in files:
        if f in seen or not f.endswith((".py", ".js", ".ts", ".sh", ".md", ".yml", ".yaml", ".json")):
            continue
        seen.add(f); pick.append(f)
        if len(pick) >= 8:
            break
    if not pick:
        print("no changes in 24h"); return 0
    parts = []
    for f in pick:
        diff = sh(["git", "log", "-1", "--format=", "-p", "--", f])[:2500]
        if diff:
            parts.append("### %s\n%s" % (f, diff))
    txt = ask("你是代码评审席。只依据下面 diff，指出：①最可能的风险 ②缺什么测试或校验 ③是否破坏兼容。\n"
              "每条一行，最多 6 条，不要客套，不要编造文件。\n\n" + "\n".join(parts)[:9000])
    os.makedirs(OUTDIR, exist_ok=True)
    p = os.path.join(OUTDIR, "REVIEW-%s.md" % day)
    open(p, "w", encoding="utf-8").write("# 评审 %s\n\n审查文件：%s\n\n%s\n" % (day, ", ".join(pick), txt))
    json.dump({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": pick, "text": txt},
              open(os.path.join(S, "review.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("review:", p)
    print(txt[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
