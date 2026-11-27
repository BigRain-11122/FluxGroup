# -*- coding: utf-8 -*-
"""repo_layers.py - 管住"新文件落在哪一层"，而不是搬家。

背景：6102 个跟踪文件里 4300 个在 cph4/fleet，根下平铺 164 个且还在长；冲突 96% 来自
状态与代码混放。批量搬家会制造一波断链（这些文件被脉/卡/文档引用），所以先用闸管增量。

检查项（都能在本地算）：
  C1 根下小写散件（正典应大写，其余应进子目录）
  C2 根下文件数超阈值
  C3 L4 运行时目录被 git 跟踪（应为 0）
  C4 L2 通道（lanes/queue-receipts）被误忽略 = 断派单
  C5 archive 是否按月分目录
  C6 大件是否标了 -diff / linguist-generated

Usage: repo_layers.py [--json]
Exit: 0 合规；1 有告警
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLEET = os.path.join(ROOT, "cph4", "fleet")
OUT = os.path.join(FLEET, "REPO-LAYERS.md")
STATE = os.path.join(FLEET, "state", "repo-layers.json")
ROOT_MAX_FILES = 180
L4 = ("cph4/fleet/state/", "cph4/fleet/radar/", "cph4/fleet/chief/",
      "cph4/fleet/sync/", "cph4/fleet/memory-slim/")
L2 = ("cph4/fleet/lanes/", "cph4/fleet/queue-receipts/")
BIG = ("cph4/fleet/archive/", "cph4/fleet/audits/", "cph4/fleet/conversions/", "media/")


def git(*args, timeout=90):
    try:
        p = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "")
    except Exception:
        return 1, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    warns = []
    rc, out = git("ls-files")
    tracked = out.splitlines() if rc == 0 else []

    # C1/C2 根下散件
    root_files = [f for f in tracked
                  if f.startswith("cph4/fleet/") and f.count("/") == 2]
    # 只报「最近 7 天内新增」的小写散件：存量 10 个是历史文档，搬家会断链，
    # 用一个永远报警的闸只会让人忽略它（假红的另一种形式）。
    def _recent(f, days=7):
        rc2, ts = git("log", "-1", "--format=%ct", "--", f, timeout=20)
        try:
            return (time.time() - float(ts.strip() or 0)) < days * 86400
        except Exception:
            return True

    lowercase = [f for f in root_files
                 if re.match(r"^cph4/fleet/[a-z]", f) and f.endswith((".md", ".json", ".jsonl"))
                 and _recent(f)]
    if lowercase:
        warns.append("C1 根下小写散件 %d 个（正典请大写，其余进子目录）：%s"
                     % (len(lowercase), ", ".join(os.path.basename(x) for x in lowercase[:5])))
    if len(root_files) > ROOT_MAX_FILES:
        warns.append("C2 cph4/fleet 根下 %d 个文件，超阈值 %d"
                     % (len(root_files), ROOT_MAX_FILES))

    # C3 L4 被跟踪
    l4 = [f for f in tracked if f.startswith(L4)]
    if l4:
        warns.append("C3 运行时目录仍被跟踪 %d 个（应为 0）：%s" % (len(l4), l4[:3]))

    # C4 通道被忽略
    gi = [ln.strip() for ln in open(os.path.join(ROOT, ".gitignore"),
                                    encoding="utf-8").read().splitlines()]
    for p in L2:
        if p in gi:
            warns.append("C4 %s 整目录被忽略 = 切断机队取卡/上报" % p)

    # C5 archive 按月/日分目录
    arch = [f for f in tracked if f.startswith("cph4/fleet/archive/")]
    bad_layout = [f for f in arch if not re.match(
        r"^cph4/fleet/archive/[^/]+/\d{8}/[^/]+$", f)]
    if bad_layout:
        warns.append("C5 archive 有 %d 个文件未按 <line>/<YYYYMMDD>/ 归位：%s"
                     % (len(bad_layout), bad_layout[:3]))

    # C6 大件是否标 generated
    ga = ""
    try:
        ga = open(os.path.join(ROOT, ".gitattributes"), encoding="utf-8").read()
    except Exception:
        pass
    for p in BIG:
        if not any(p.rstrip("/") in ln for ln in ga.splitlines()):
            warns.append("C6 %s 未在 .gitattributes 标 -diff/linguist-generated" % p)

    verdict = "WARN" if warns else "OK"
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    L = ["# 仓库分层体检 %s" % now, "",
         "判定：**%s**｜跟踪 %d 文件｜cph4/fleet 根下 %d 个"
         % (verdict, len(tracked), len(root_files)), ""]
    if warns:
        for w in warns:
            L.append("- ⚠ %s" % w)
    else:
        L.append("- ✅ 分层合规：无散件堆积、无运行时入库、通道在 git、归档按月、大件已标记")
    L += ["", "分层定义见 `cph4/fleet/GIT-LAYERS-v1.md`。", ""]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"ts": now, "verdict": verdict, "warnings": warns,
                   "tracked": len(tracked), "root_files": len(root_files)},
                  f, ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": verdict, "warnings": len(warns),
                      "tracked": len(tracked), "root_files": len(root_files),
                      "board": os.path.relpath(OUT, ROOT)}, ensure_ascii=False))
    for w in warns[:6]:
        print("  WARN", w[:120])
    return 1 if warns else 0


if __name__ == "__main__":
    sys.exit(main())