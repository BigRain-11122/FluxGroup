# -*- coding: utf-8 -*-
"""
ready · 就绪自检

新 AI / 新机器进场的第一条命令。它把"你有没有读懂、能不能开工"变成可执行的检查，
而不是靠文档里一句"请先阅读"。

七项检查：
  1 位置：当前目录是不是 silicon-earth
  2 Python 版本
  3 git 可用，且在仓库内
  4 契约与数据校验（world_ops validate）
  5 派生内容与重算一致（check_state）
  6 任务板可读
  7 工具自测（agent_ops selftest）

用法：python tools/ready.py
退出码：0 就绪 / 1 未就绪（按提示修）
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PY = sys.executable

rows = []


def say(m):
    print(m, flush=True)


def check(name, fn, fix):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, f"{type(e).__name__}: {e}"
    rows.append((name, ok, detail, fix))
    say(("  ✓ " if ok else "  ✗ ") + name + (f"  · {detail}" if detail else ""))
    return ok


def c_location():
    for f in ("START-HERE.md", "CONTRACTS/world.schema.json", "tools/world_ops.py"):
        if not os.path.exists(os.path.join(ROOT, f)):
            return False, f"缺 {f}"
    if os.path.basename(ROOT).lower() != "silicon-earth":
        return False, f"当前根是 {ROOT}，看起来不是在 silicon-earth 里"
    return True, ROOT


def c_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 8)
    return ok, f"{v.major}.{v.minor}.{v.micro}"


def c_git():
    p = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        return False, "不在 git 仓库内"
    q = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                       capture_output=True, text=True)
    return True, f"仓库根 {q.stdout.strip()}"


def _run(args):
    p = subprocess.run([PY] + args, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def c_validate():
    rc, out = _run(["tools/world_ops.py", "validate"])
    last = out.splitlines()[-1] if out else ""
    return rc == 0, last


def c_state():
    rc, out = _run(["tools/check_state.py"])
    last = out.splitlines()[-1] if out else ""
    return rc == 0, last


def c_tasks():
    p = os.path.join(ROOT, "TASKS.json")
    if not os.path.exists(p):
        return False, "缺 TASKS.json"
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    tasks = d.get("tasks", [])
    done = {t["id"] for t in tasks if t.get("status") == "done"}
    ready = [t for t in tasks if t.get("status") == "todo"
             and all(x in done for x in (t.get("depends_on") or []))]
    return bool(tasks), f"{len(tasks)} 个任务，可领 {len(ready)} 个"


def c_selftest():
    rc, out = _run(["tools/agent_ops.py", "selftest"])
    last = out.splitlines()[-1] if out else ""
    return rc == 0, last


def c_repo():
    rc, out = _run(["tools/repo_check.py"])
    last = out.splitlines()[-1] if out else ""
    return rc == 0, last


def c_runtime():
    need = ["modules/m-w2-clock/data/events.jsonl", "modules/m-w2-clock/data/time.json",
            "modules/m-w3-settle/data/state.json", "modules/m-p2-memory/data/memory.json"]
    missing = [x for x in need if not os.path.exists(os.path.join(ROOT, x))]
    if missing:
        rc, out = _run(["tools/setup.py"])
        if rc != 0:
            return False, "初始化失败：" + (out.splitlines()[-1] if out else "")
        return True, f"已初始化 {len(missing)} 个运行时文件"
    return True, "齐全"


def c_status():
    if not os.path.exists(os.path.join(ROOT, "STATUS.md")):
        _run(["tools/status.py"])
    rc, out = _run(["tools/status.py", "--check"])
    last = out.splitlines()[-1] if out else ""
    return rc == 0, last


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    say("硅基地球 · 就绪自检\n")

    check("位置", c_location, "cd D:\\FluxGroup\\silicon-earth")
    check("Python", c_python, "装 3.8 以上")
    check("git", c_git, "先 clone 整个 FluxGroup 仓库")
    check("契约与数据", c_validate, "按输出修，红了别开工")
    check("派生内容", c_state, "重跑 settle/derive，别手改 state.json")
    check("任务板", c_tasks, "检查 TASKS.json 是否存在且可解析")
    check("仓库规范", c_repo, "按输出修：命名英文/无空格、单件≤95MB、无密钥")
    check("运行时状态", c_runtime, "跑 python tools/setup.py 初始化")
    check("总览页", c_status, "跑 python tools/status.py 重新生成 STATUS.md")
    check("工具自测", c_selftest, "看 agent_ops selftest 的失败项")

    bad = [r for r in rows if not r[1]]
    say("")
    if bad:
        say(f"未就绪：{len(bad)}/{len(rows)} 项未过")
        say("按顺序修：")
        for name, ok, detail, fix in bad:
            say(f"  · {name}：{fix}")
        return 1

    say(f"就绪：{len(rows)}/{len(rows)} 项全过")
    say("下一步：读 START-HERE 第五节，然后 claim 一个任务。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
