# -*- coding: utf-8 -*-
"""
deliver · 唯一交付出口（v2）

v2 按群审修四个洞：
  1 零工作量交付 —— 本分支必须真的改动过该任务模块 writes 内的文件
  2 手改派生内容 —— check_state 从源头重算比对（含 day 与区域完整性）
  3 state 过期 —— 先跑 world_ops validate
  4 并发覆盖 —— 写回前重读任务板，租约变了就作废（CAS）

用法：python tools/deliver.py T03 agent-你的名字
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PY = sys.executable


def say(m):
    print(m, flush=True)


def git(*args):
    p = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "")


def changed_relative():
    sys.path.insert(0, HERE)
    from agent_ops import changed_paths
    return changed_paths(ROOT)


def changed_since(epoch):
    """回退方案：没有 base_sha 时按领取时刻取提交改动。"""
    if not epoch:
        return []
    rc, out = git("log", "--since=@%d" % int(epoch), "--name-only", "--pretty=format:", "HEAD")
    if rc != 0:
        return []
    return [x.strip().replace("\\", "/") for x in out.splitlines() if x.strip()]


def changed_from_base(base):
    if not base:
        return []
    rc, out = git("diff", "--name-only", "%s..HEAD" % base)
    if rc != 0:
        return []
    return [x.strip().replace("\\", "/") for x in out.splitlines() if x.strip()]


def main(task_id, agent):
    tp = os.environ.get("SILICON_BOARD") or os.path.join(ROOT, "TASKS.json")
    with open(tp, encoding="utf-8") as f:
        data = json.load(f)

    for t in data["tasks"]:
        if t["id"] != task_id:
            continue

        holder = t.get("claimed_by")
        if holder != agent:
            say(f"✗ {task_id} 由 {holder or '无人'} 持有，{agent} 不能交付")
            return 1

        # 1 零工作量：必须真的改过本模块 writes 内的文件
        if t.get("module_at_claim") and t["module_at_claim"] != t.get("module"):
            say("✗ 任务的 module 字段在领取后被改过，拒绝交付")
            return 1
        mj = os.path.join(ROOT, "modules", t["module"], "module.json")
        meta = json.load(open(mj, encoding="utf-8"))
        writes = [w.replace("\\", "/").rstrip("/") for w in meta.get("writes", [])]
        touched = [p for p in (changed_relative()
                               + changed_from_base(t.get("base_sha"))
                               + ([] if t.get("base_sha") else changed_since(t.get("claimed_at"))))
                   if any(p == w or p.startswith(w + "/") or p.startswith(w) for w in writes)]
        if not touched:
            say(f"✗ 没有任何改动落在 {t['module']} 的 writes 内：无改动不算交付")
            say(f"  应写：{', '.join(writes) or '（该模块未声明 writes）'}")
            return 1

        # 2 越界
        g = subprocess.run([PY, os.path.join(ROOT, "tools", "agent_ops.py"),
                            "guard", "--root", ROOT, "--agent", agent],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if g.returncode != 0:
            say("✗ guard 未通过：有越界改动，先撤回再交付")
            say((g.stdout or "")[-300:])
            return 1

        # 3 契约与新鲜度
        v = subprocess.run([PY, os.path.join(ROOT, "tools", "world_ops.py"), "validate"],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if v.returncode != 0:
            say("✗ validate 未通过（可能是 state 过期或数据不一致）")
            say((v.stdout or "")[-300:])
            return 1

        # 4 派生内容与重算一致
        c = subprocess.run([PY, os.path.join(ROOT, "tools", "check_state.py")],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if c.returncode != 0:
            say("✗ 派生数据与重算不一致：手改不算交付")
            say((c.stdout or "")[-300:])
            return 1

        # 5 verify：命令来自 CONTRACTS/verify.json（总控所有），不认任务板里的可改文本
        vp = os.path.join(ROOT, "CONTRACTS", "verify.json")
        try:
            with open(vp, encoding="utf-8") as f:
                vmap = json.load(f).get("verify", {})
        except Exception:
            say("✗ 缺 CONTRACTS/verify.json：没有权威验收命令，不许交付")
            return 1
        cmd = (vmap.get(task_id) or "").strip()
        if not cmd:
            say(f"✗ {task_id} 在 CONTRACTS/verify.json 里没有验收命令")
            return 1
        if (t.get("verify") or "").strip() and t["verify"].strip() != cmd:
            say("· 注意：任务板里的 verify 与权威命令不一致，按权威命令执行")
        p = subprocess.run(cmd.split(), cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode != 0:
            say(f"✗ verify 未通过 rc={p.returncode}，不算交付")
            say((p.stdout or "")[-400:])
            return 1

        # 6 CAS：写回前重读，租约被别人动过就作废
        with open(tp, encoding="utf-8") as f:
            fresh = json.load(f)
        ft = next((x for x in fresh["tasks"] if x["id"] == task_id), None)
        if not ft or ft.get("claimed_by") != agent or ft.get("lease_until") != t.get("lease_until"):
            say("✗ 交付期间任务板被改动（租约变化），本次作废，请重试")
            return 1

        ft.setdefault("deliveries", []).append({
            "by": agent, "verify": cmd, "rc": 0,
            "files": touched, "at": int(time.time())
        })
        ft["claimed_by"] = None
        ft["claimed_at"] = None
        ft["lease_until"] = None
        ft["status"] = "done"
        tmp = tp + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(fresh, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, tp)
        say(f"✓ {task_id} 交付通过：改动 {len(touched)} 个文件，verify rc=0，状态 done")
        return 0

    say(f"✗ 没有任务 {task_id}")
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 3:
        say("用法: python tools/deliver.py <task-id> <agent>")
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
