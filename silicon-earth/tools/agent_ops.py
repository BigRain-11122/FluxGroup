# -*- coding: utf-8 -*-
"""
agent_ops · AI 工作模式的执行层

四个动作，对应一个 AI 进场后的真实流程：
  status   <agent>                我手上有什么活、该读什么、该跑什么
  guard    [--fix-note]           我改的文件是否都在自己模块的 writes 内（越界当场红）
  takeover <task> <agent> [note]  前任租约过期/放弃时接管，并留一句话交接
  handoff  <task> <agent> <note>  未完成就交班，写清做到哪、下一步
  selftest                        在临时副本里自测上面四条

设计原则：不靠自觉，靠命令。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))


def say(m):
    print(m, flush=True)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, o):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def modules(root):
    out = {}
    mod_dir = os.path.join(root, "modules")
    if not os.path.isdir(mod_dir):
        return out
    for mid in os.listdir(mod_dir):
        mj = os.path.join(mod_dir, mid, "module.json")
        if os.path.exists(mj):
            out[mid] = load(mj)
    return out


def owner_of(path, mods):
    """最长前缀匹配：这个文件归哪个模块写。"""
    path = path.replace("\\", "/")
    best, best_len = None, -1
    for mid, meta in mods.items():
        for w in meta.get("writes", []):
            w = w.replace("\\", "/").rstrip("/")
            if path == w or path.startswith(w + "/") or path.startswith(w):
                if len(w) > best_len:
                    best, best_len = mid, len(w)
    return best


# ---------------- status ----------------
def status(root, agent):
    tasks = load(_board(root))["tasks"]
    mine = [t for t in tasks if t.get("claimed_by") == agent]
    if not mine:
        say(f"{agent}：手上没有活。去 TASKS.json 里找 status=todo 的，用 claim 领。")
        return 0
    mods = modules(root)
    for t in mine:
        meta = mods.get(t["module"], {})
        left = max(0, int(t.get("lease_until") or 0) - int(time.time()))
        say(f"· {t['id']} {t['title']}  [{t['module']}]  租约剩 {left//60} 分钟")
        say(f"  读：START-HERE.md → modules/{t['module']}/module.json → CONTRACTS/")
        say(f"  跑：{meta.get('run') or '（无）'}")
        say(f"  验：{t.get('verify')}")
        say(f"  验收：{t.get('acceptance') or '（未写验收标准）'}")
        if t.get("handoff"):
            say(f"  前任交接：{t['handoff'][-1].get('note')}")
        say(f"  只许写：{', '.join(meta.get('writes', [])) or '无'}")
    return 0


# ---------------- guard ----------------
SHARED = ("CONTRACTS/", "tools/", "REPORTS/")
IGNORE = ("TASKS.json", "TASKS.lock", "STATUS.md")


def _git(root, *args):
    p = subprocess.run(["git"] + list(args), cwd=root, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "")


def changed_paths(root):
    """工作区改动 + 本分支相对 main 的改动（含已提交）。"""
    paths = set()
    rc, out = _git(root, "status", "--porcelain")
    if rc == 0:
        for line in out.splitlines():
            if len(line) > 3:
                paths.add(line[3:].strip().strip('"').replace("\\", "/"))
    rc, out = _git(root, "diff", "--name-only", "main...HEAD")
    if rc == 0:
        for line in out.splitlines():
            if line.strip():
                paths.add(line.strip().replace("\\", "/"))
    rc, prefix = _git(root, "rev-parse", "--show-prefix")
    pre = prefix.strip() if rc == 0 else ""
    out_paths = []
    for p in paths:
        if not p:
            continue
        if pre and not p.startswith(pre):
            continue
        q = p[len(pre):] if pre else p
        if q in IGNORE or "__pycache__" in q or q.endswith(".pyc"):
            continue
        out_paths.append(q)
    return sorted(set(out_paths))


def guard(root, agent):
    if not agent:
        say("✗ 必须给 --agent：不知道你是谁，就无法判断你该写什么")
        return 2
    mods = modules(root)
    tasks = load(_board(root))["tasks"]
    mine = [t for t in tasks if t.get("claimed_by") == agent]
    allowed = []
    for t in mine:
        m = mods.get(t["module"])
        if m:
            allowed += [w.replace("\\", "/").rstrip("/") for w in m.get("writes", [])]
    is_controller = agent in ("总控", "controller")

    paths = changed_paths(root)
    bad = []
    for path in paths:
        ok = any(path == a or path.startswith(a + "/") or path.startswith(a) for a in allowed)
        if not ok and is_controller:
            ok = True
        if not ok:
            bad.append(path)

    say(f"agent={agent} · 领到 {len(mine)} 个任务 · 允许写 {len(allowed)} 个前缀")
    if not paths:
        say("没有检测到任何改动（工作区干净）")
        return 0
    for p in paths:
        hit = any(p == a or p.startswith(a + "/") or p.startswith(a) for a in allowed) or is_controller
        say(f"  {'✓' if hit else '✗'} {p}")
    if bad:
        say(f"\n✗ {len(bad)} 个文件越界（不在你领取任务所属模块的 writes 内）")
        return 1
    say("\n✓ 全部在授权范围内")
    return 0


# ---------------- takeover / handoff ----------------
def _board(root):
    return os.environ.get("SILICON_BOARD") or os.path.join(root, "TASKS.json")


def _lock(root):
    lk = _board(root) + ".lock"
    for _ in (1, 2):
        try:
            fd = os.open(lk, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lk
        except FileExistsError:
            if time.time() - os.path.getmtime(lk) > 30:
                try:
                    os.remove(lk)
                except FileNotFoundError:
                    pass
                continue
            return None
    return None


def takeover(root, task_id, agent, note=""):
    lk = _lock(root)
    if not lk:
        say("✗ 任务板被占用")
        return 1
    try:
        tp = _board(root)
        data = load(tp)
        now = int(time.time())
        for t in data["tasks"]:
            if t["id"] != task_id:
                continue
            holder = t.get("claimed_by")
            lease = int(t.get("lease_until") or 0)
            if holder and holder != agent and lease > now:
                say(f"✗ {task_id} 仍由 {holder} 持有（租约剩 {(lease-now)//60} 分钟），不许抢")
                return 1
            t["handoff"] = t.get("handoff", [])
            if holder and holder != agent:
                t["handoff"].append({"from": holder, "to": agent,
                                     "at": now, "note": note or "（无留言）"})
            t["claimed_by"] = agent
            t["claimed_at"] = now
            t["lease_until"] = now + 2 * 3600
            t["status"] = "doing"
            dump(tp, data)
            say(f"✓ {task_id} 已由 {agent} 接管" + (f"，前任 {holder}" if holder and holder != agent else ""))
            return 0
        say(f"✗ 没有任务 {task_id}")
        return 1
    finally:
        try:
            os.remove(lk)
        except FileNotFoundError:
            pass


def handoff(root, task_id, agent, note):
    lk = _lock(root)
    if not lk:
        say("✗ 任务板被占用")
        return 1
    try:
        tp = _board(root)
        data = load(tp)
        for t in data["tasks"]:
            if t["id"] != task_id:
                continue
            if t.get("claimed_by") != agent:
                say(f"✗ {task_id} 不是 {agent} 的活，不能替人交班")
                return 1
            t.setdefault("handoff", []).append(
                {"from": agent, "to": None, "at": int(time.time()), "note": note})
            t["claimed_by"] = None
            t["claimed_at"] = None
            t["lease_until"] = None
            t["status"] = "todo"
            dump(tp, data)
            say(f"✓ {task_id} 已交班：{note}")
            return 0
        say(f"✗ 没有任务 {task_id}")
        return 1
    finally:
        try:
            os.remove(lk)
        except FileNotFoundError:
            pass


# ---------------- selftest ----------------
def selftest():
    base = tempfile.mkdtemp(prefix="agent-ops-")
    dst = os.path.join(base, "repo")
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("node_modules", "__pycache__", ".git"))
    ok_all = True

    # 0 基线：先建临时仓，否则 git status 无从比较
    subprocess.run(["git", "init", "-q"], cwd=dst)
    subprocess.run(["git", "add", "-A"], cwd=dst)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=dst)

    # 先领活：agent-a 负责 T03（m-p2-memory），否则没有授权范围
    subprocess.run([sys.executable, "tools/world_ops.py", "claim", "T03", "agent-a"],
                   cwd=dst, capture_output=True)

    # 1 越界：在模块目录里造一个没人声明的文件
    rogue = os.path.join(dst, "modules", "m-w1-regions", "data", "rogue.json")
    with open(rogue, "w", encoding="utf-8") as f:
        f.write('{"x":1}')
    rc, _ = run_guard(dst)
    ok = rc != 0
    ok_all = ok_all and ok
    say(("PASS  " if ok else "FAIL  ") + "guard 抓到越界写（应为红）")
    os.remove(rogue)

    # 2 合法写必须通过（agent-a 领的是 T03 → m-p2-memory）
    legal = os.path.join(dst, "modules", "m-p2-memory", "data", "seed.json")
    d = load(legal)
    d["note"] = d.get("note", "") + "."
    dump(legal, d)
    rc, _ = run_guard(dst)
    ok = rc == 0
    ok_all = ok_all and ok
    say(("PASS  " if ok else "FAIL  ") + "guard 放行合法写（应为绿）")

    # 3 租约有效时不许接管
    takeover(dst, "T03", "agent-a")
    rc = takeover(dst, "T03", "agent-b")
    ok = rc != 0
    ok_all &= ok
    say(("PASS  " if ok else "FAIL  ") + "租约有效仍可被抢（应为红）")

    # 4 租约过期后可接管，且留交接
    tp = os.path.join(dst, "TASKS.json")
    data = load(tp)
    for t in data["tasks"]:
        if t["id"] == "T03":
            t["lease_until"] = 0
    dump(tp, data)
    rc = takeover(dst, "T03", "agent-b", "接手：已跑通 validate")
    data = load(tp)
    t = next(x for x in data["tasks"] if x["id"] == "T03")
    ok = rc == 0 and t["claimed_by"] == "agent-b" and bool(t["handoff"])
    ok_all &= ok
    say(("PASS  " if ok else "FAIL  ") + "过期接管与交接记录")

    # 5 交班后回到 todo
    rc = handoff(dst, "T03", "agent-b", "只差日报")
    data = load(tp)
    t = next(x for x in data["tasks"] if x["id"] == "T03")
    ok = rc == 0 and t["claimed_by"] is None and t["status"] == "todo"
    ok_all &= ok
    say(("PASS  " if ok else "FAIL  ") + "交班后释放回 todo")

    shutil.rmtree(base, ignore_errors=True)
    say("\n结果：" + ("全部通过" if ok_all else "有失败"))
    return 0 if ok_all else 1


def run_guard(root, agent="agent-a"):
    p = subprocess.run([sys.executable, os.path.join(HERE, "agent_ops.py"), "guard",
                        "--root", root, "--agent", agent],
                       cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    argv = list(sys.argv)
    root = ROOT
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        del argv[i:i + 2]
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status" and len(argv) >= 3:
        sys.exit(status(root, argv[2]))
    elif cmd == "guard":
        ag = ""
        if "--agent" in argv:
            i = argv.index("--agent")
            ag = argv[i + 1] if len(argv) > i + 1 else ""
        sys.exit(guard(root, ag))
    elif cmd == "takeover" and len(argv) >= 4:
        note = argv[4] if len(argv) > 4 else ""
        sys.exit(takeover(root, argv[2], argv[3], note))
    elif cmd == "handoff" and len(argv) >= 5:
        sys.exit(handoff(root, argv[2], argv[3], argv[4]))
    elif cmd == "selftest":
        sys.exit(selftest())
    else:
        say("用法: agent_ops.py status|guard|takeover|handoff|selftest [--root DIR]")
        sys.exit(2)
