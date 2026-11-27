# -*- coding: utf-8 -*-
"""
loop_test · 闭环测试 v2

v2 按群审修：
  - L2 必须有真实改动（否则 deliver 应拒），并验证零改动会被拒
  - L3/L4/L5 断言具体字样，不再用写死的说明
  - 全部在 git 导出的全新快照里跑

用例：
  L1 全新快照就绪
  L2 领活 → 有改动 → 交付成功 → done
  L2b 零改动交付 → 必须被拒
  L3 非持有者交付 → 必须被拒
  L4 手改派生数据 → 必须被拒
  L5 越界写 → guard 必须为红
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PARENT = os.path.abspath(os.path.join(ROOT, ".."))
PY = sys.executable
rows = []


def say(m):
    print(m, flush=True)


def sh(args, cwd):
    p = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))


def record(name, ok, detail=""):
    rows.append((name, ok, detail))
    say(("PASS  " if ok else "FAIL  ") + name + ("  · " + detail if detail else ""))


def snapshot():
    base = tempfile.mkdtemp(prefix="se-loop-")
    zipf = os.path.join(base, "se.zip")
    p = subprocess.run(["git", "archive", "--format=zip", "-o", zipf, "HEAD:silicon-earth"],
                       cwd=PARENT, capture_output=True, text=True)
    if p.returncode != 0:
        return None, p.stderr
    dst = os.path.join(base, "silicon-earth")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Expand-Archive -Path '%s' -DestinationPath '%s' -Force" % (zipf, dst)],
                   capture_output=True)
    subprocess.run(["git", "init", "-q"], cwd=dst, capture_output=True)
    for k, v in (("core.autocrlf", "false"), ("user.email", "loop@local"), ("user.name", "loop")):
        subprocess.run(["git", "config", k, v], cwd=dst, capture_output=True)
    for c in (["git", "add", "-A"], ["git", "commit", "-q", "-m", "seed"]):
        subprocess.run(c, cwd=dst, capture_output=True)
    subprocess.run([PY, "tools/setup.py"], cwd=dst, capture_output=True)
    return dst, ""


def touch(root, rel, note="loop-test"):
    p = os.path.join(root, rel.replace("/", os.sep))
    with open(p, "a", encoding="utf-8") as f:
        f.write("\n")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root, err = snapshot()
    if not root:
        record("L0 取快照", False, err[-200:])
        return 1
    say(f"快照：{root}\n")

    rc, out = sh(["tools/ready.py"], root)
    record("L1 全新快照就绪", rc == 0, "ready rc=0")

    # L2b 零改动交付 → 必须被拒
    sh(["tools/world_ops.py", "claim", "T03", "agent-a"], root)
    rc0, out0 = sh(["tools/deliver.py", "T03", "agent-a"], root)
    record("L2b 零改动被拒", rc0 != 0 and "无改动不算交付" in out0, out0.strip().splitlines()[0][:60])

    # L2 有真实改动 → 交付成功
    touch(root, "modules/m-p2-memory/data/seed.json")
    rc2, out2 = sh(["tools/deliver.py", "T03", "agent-a"], root)
    data = json.load(open(os.path.join(root, "TASKS.json"), encoding="utf-8"))
    t03 = next(x for x in data["tasks"] if x["id"] == "T03")
    record("L2 有改动→交付→done", rc2 == 0 and t03["status"] == "done",
           (out2.strip().splitlines() or [""])[-1][:100])

    # L2c 提交之后仍能交付（修"先 commit 就零改动"的死循环）
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "after L2"], cwd=root, capture_output=True)
    sh(["tools/world_ops.py", "claim", "T02", "agent-b"], root)
    with open(os.path.join(root, "modules", "m-w3-settle", "settle.py"), "a", encoding="utf-8") as f:
        f.write("\n# loop-test: 真实改动\n")
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "work T02"], cwd=root, capture_output=True)
    rc6, out6 = sh(["tools/deliver.py", "T02", "agent-b"], root)
    record("L2c 提交后仍可交付", rc6 == 0, (out6.strip().splitlines() or [""])[-1][:90])

    # L3 非持有者
    sh(["tools/world_ops.py", "claim", "T12", "agent-c"], root)
    rc3, out3 = sh(["tools/deliver.py", "T12", "agent-d"], root)
    record("L3 非持有者被拒", rc3 != 0 and "不能交付" in out3, out3.strip().splitlines()[0][:60])

    # L4 手改派生数据（先做一处合法改动，再篡改 state）
    touch(root, "modules/m-w3-settle/settle.py")
    sp = os.path.join(root, "modules", "m-w3-settle", "data", "state.json")
    d = json.load(open(sp, encoding="utf-8"))
    d["regions"][0]["positivity"] = 9999
    json.dump(d, open(sp, "w", encoding="utf-8"), ensure_ascii=False)
    rc4, out4 = sh(["tools/deliver.py", "T12", "agent-c"], root)
    record("L4 手改派生被拒", rc4 != 0 and ("重算不一致" in out4 or "validate 未通过" in out4),
           out4.strip().splitlines()[0][:60])

    # L5 越界写
    touch(root, "modules/m-w1-regions/data/regions.json")
    rc5, out5 = sh(["tools/agent_ops.py", "guard", "--agent", "agent-b"], root)
    record("L5 越界被 guard 拦", rc5 != 0 and "越界" in out5, f"rc={rc5}")

    bad = [r for r in rows if not r[1]]
    say(f"\n结果：{len(rows)-len(bad)}/{len(rows)} 通过")
    if bad:
        say("未过：" + ", ".join(r[0] for r in bad))
    shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
