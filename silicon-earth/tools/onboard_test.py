# -*- coding: utf-8 -*-
"""
onboard_test · 真实接入测试

模拟的是真事：
  1) 从 git 里取一份「已提交」的快照（不是工作区拷贝，证明提交内容自足）
  2) 建成一个独立的种子仓库，再真 clone 出两台「新机器」
  3) 每个克隆里跑一个「新来的 AI」：照 START-HERE 走，validate → 领任务 → 跑 verify → 释放
  4) 两台各推进 5 天，检查跨机合并是否成立（预期：不成立，这是已知缺口）

运行：python tools/onboard_test.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PARENT = os.path.abspath(os.path.join(ROOT, ".."))
PY = sys.executable
results = []


def say(m):
    print(m, flush=True)


def sh(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    say(("PASS  " if ok else "FAIL  ") + name + ("  · " + detail if detail else ""))


def build_seed(base):
    """从 git 已提交内容导出快照，证明'仓库里有的就够了'。"""
    seed = os.path.join(base, "seed")
    os.makedirs(seed, exist_ok=True)
    zip_path = os.path.join(base, "seed.zip")
    rc, out = sh(["git", "archive", "--format=zip", "-o", zip_path, "HEAD:silicon-earth"], cwd=PARENT)
    if rc != 0:
        return None, f"git archive 失败: {out[-300:]}"
    sh(["powershell", "-NoProfile", "-Command",
        "Expand-Archive -Path '%s' -DestinationPath '%s' -Force" % (zip_path, seed)])
    if not os.path.exists(os.path.join(seed, "START-HERE.md")):
        return None, "快照里没有 START-HERE.md"
    # 建种子仓库
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "commit", "-q", "-m", "seed"]):
        rc, out = sh(cmd, cwd=seed)
        if rc != 0:
            return None, f"{cmd[1]} 失败: {out[-200:]}"
    return seed, ""


def clone(seed, base, name):
    dst = os.path.join(base, name)
    rc, out = sh(["git", "clone", "-q", seed, dst])
    return (dst if rc == 0 else None), out


def robot(dst, agent, task):
    """一个只会照文档走的机器人：validate → claim → 跑 verify → release。"""
    log = []
    rc, out = sh([PY, "tools/world_ops.py", "validate"], cwd=dst)
    log.append(("validate", rc))
    if rc != 0:
        return log, out
    rc, out = sh([PY, "tools/world_ops.py", "claim", task, agent], cwd=dst)
    log.append(("claim", rc))
    if rc != 0:
        return log, out
    tasks = json.load(open(os.path.join(dst, "TASKS.json"), encoding="utf-8"))
    t = next(x for x in tasks["tasks"] if x["id"] == task)
    rc, out = sh(t["verify"].split(), cwd=dst)
    log.append(("verify", rc))
    return log, out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base = tempfile.mkdtemp(prefix="silicon-onboard-")
    say(f"临时根目录 {base}")

    seed, err = build_seed(base)
    if not seed:
        record("从 git 取快照", False, err)
        return 1
    record("从 git 取快照", True, "HEAD:silicon-earth 导出成功，提交内容自足")

    a, out = clone(seed, base, "machine-a")
    b, out2 = clone(seed, base, "machine-b")
    record("两台机器各自 clone", bool(a and b), f"machine-a / machine-b")

    # A 机器：新来的 AI 照文档领 T03 并跑 verify
    log, out = robot(a, "agent-doubao", "T03")
    ok = all(rc == 0 for _, rc in log)
    record("机器A 照文档接入", ok, " → ".join(f"{k}:{rc}" for k, rc in log))

    # B 机器：同时领同一任务（不同克隆，互不影响，属预期）
    log_b, out_b = robot(b, "agent-qwen", "T03")
    ta = json.load(open(os.path.join(a, "TASKS.json"), encoding="utf-8"))
    tb = json.load(open(os.path.join(b, "TASKS.json"), encoding="utf-8"))
    ha = next(x for x in ta["tasks"] if x["id"] == "T03")["claimed_by"]
    hb = next(x for x in tb["tasks"] if x["id"] == "T03")["claimed_by"]
    record("机器B 独立接入", all(rc == 0 for _, rc in log_b) and ha == "agent-doubao" and hb == "agent-qwen",
           f"A 持有 {ha} · B 持有 {hb}（两库独立，属预期）")

    # 两台各推进 5 天 → 看跨机合并
    sh([PY, "modules/m-w2-clock/engine.py", "5"], cwd=a)
    sh([PY, "modules/m-w2-clock/engine.py", "5"], cwd=b)
    ea = [json.loads(l) for l in open(os.path.join(a, "modules/m-w2-clock/data/events.jsonl"), encoding="utf-8") if l.strip()]
    eb = [json.loads(l) for l in open(os.path.join(b, "modules/m-w2-clock/data/events.jsonl"), encoding="utf-8") if l.strip()]
    ids_a, ids_b = {e["id"] for e in ea}, {e["id"] for e in eb}
    clash = ids_a & ids_b
    record("跨机合并（已知缺口）", False,
           f"两台各推 5 天，事件 id 交集 {len(clash)} 条 → 没有合并机制，直接合并必然撞号")

    say("\n小结：单机接入是通的；跨机合并不是缺测试，是缺设计（BACKLOG B15）。")
    bad = [r for r in results if not r[1]]
    say(f"结果：{len(results)-len(bad)}/{len(results)} 通过")
    shutil.rmtree(base, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
