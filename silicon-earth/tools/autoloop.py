# -*- coding: utf-8 -*-
"""
autoloop · 按 ROADMAP 自己往前走

规则（科学推进，不蛮干）：
  1 开跑前必须 validate 绿；红就停，不改任何东西。
  2 从上往下取第一个 status=todo，跑 run，再跑 verify。
  3 verify 绿 → 该行标 done，提交，记一行日志。
  4 verify 红 → 该行标 blocked，停下并写清原因；不连跑后面的。
  5 不 push、不改契约、不动别人的模块。
  6 每步只提交 silicon-earth 路径。

用法：
  python tools/autoloop.py --once     只做一步
  python tools/autoloop.py --watch 600 每 10 分钟一轮，直到没有 todo
"""
import io
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(ROOT, ".."))
MAP = os.path.join(ROOT, "ROADMAP.md")
LOG = os.path.join(ROOT, "REPORTS", "AUTOLOOP-%s.md" % time.strftime("%Y%m%d"))
PY = sys.executable
ROW = re.compile(r"^\|\s*(S\d+)\s*\|\s*(.+?)\s*\|\s*`?(.+?)`?\s*\|\s*`?(.+?)`?\s*\|\s*(\w+)\s*\|$")


def say(m):
    print(m, flush=True)


def sh(args, cwd=ROOT):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))


def rows():
    out = []
    for line in io.open(MAP, encoding="utf-8"):
        m = ROW.match(line.strip())
        if m:
            out.append({"id": m.group(1), "title": m.group(2), "run": m.group(3).strip(),
                        "verify": m.group(4).strip(), "status": m.group(5)})
    return out


def set_status(rid, status):
    lines = io.open(MAP, encoding="utf-8").read().splitlines()
    for i, line in enumerate(lines):
        m = ROW.match(line.strip())
        if m and m.group(1) == rid:
            lines[i] = re.sub(r"\|\s*(\w+)\s*\|\s*$", "| %s |" % status, line)
            break
    io.open(MAP, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def log(text):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


PATHS = ["silicon-earth/tools", "silicon-earth/modules", "silicon-earth/CONTRACTS",
         "silicon-earth/ROADMAP.md", "silicon-earth/STATUS.md", "silicon-earth/REPORTS"]


def dirty():
    # 只看本线路径：别的会话在 DESIGN/ 等地写东西，不影响本线推进
    args = ["git", "status", "--porcelain", "--"] + PATHS
    rc, out = sh(args, cwd=REPO)
    return [l for l in (out or "").splitlines() if l.strip()]


def commit(rid, title):
    # 只提交本线目录，绝不把别人在 DESIGN/ 等处的在制件卷进来
    sh(["git", "add", "-A", "--"] + PATHS, cwd=REPO)
    rc, out = sh(["git", "commit", "-q", "-m", "%s: %s（自动循环）" % (rid, title)], cwd=REPO)
    return rc, out


def one_round():
    d = dirty()
    if d:
        say("✗ 工作区有未提交改动，自动循环不动手（防止把别人的在制件提交）：")
        for line in d[:5]:
            say("   " + line)
        return False

    rc, out = sh([PY, "tools/world_ops.py", "validate"])
    if rc != 0:
        say("✗ 开局 validate 红，停。")
        log(f"## {time.strftime('%H:%M')} 开局 validate 红\n```\n{out[-500:]}\n```")
        return False

    todo = [r for r in rows() if r["status"] == "todo"]
    if not todo:
        say("没有 todo 了。")
        return False
    step = todo[0]
    say(f"▶ {step['id']} {step['title']}")
    t0 = time.time()
    rc1, out1 = sh(step["run"].split())
    rc2, out2 = (0, "") if rc1 != 0 else sh(step["verify"].split())
    ok = rc1 == 0 and rc2 == 0
    dur = time.time() - t0

    if ok:
        set_status(step["id"], "done")
        c_rc, c_out = commit(step["id"], step["title"])
        say(f"✓ {step['id']} 通过（{dur:.1f}s），已提交")
        log(f"## {time.strftime('%H:%M')} {step['id']} {step['title']} · PASS ({dur:.1f}s)\n"
            f"- run rc={rc1} · verify rc={rc2} · commit rc={c_rc}")
        return True

    set_status(step["id"], "blocked")
    say(f"✗ {step['id']} 未通过：run rc={rc1} verify rc={rc2}")
    log(f"## {time.strftime('%H:%M')} {step['id']} {step['title']} · BLOCKED\n"
        f"```\n{(out1 or out2)[-600:]}\n```")
    return False


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if "--once" in sys.argv:
        return 0 if one_round() else 0
    wait = 600
    if "--watch" in sys.argv:
        i = sys.argv.index("--watch")
        if len(sys.argv) > i + 1:
            wait = int(sys.argv[i + 1])
    while True:
        if not one_round():
            if not [r for r in rows() if r["status"] == "todo"]:
                break
        time.sleep(wait)
    return 0


if __name__ == "__main__":
    sys.exit(main())
