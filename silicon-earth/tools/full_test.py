# -*- coding: utf-8 -*-
"""
full_test · 全流程多样化测试

补现有套件没覆盖的真实场景，并汇总全部套件：
  N1 崩溃重放：把时钟调回去再推进 → 必须拒绝
  N2 接力：A 做一半交班，B 接管并交付 → 必须成功
  N3 依赖门：前置未完成时领取 → 必须拒绝
  N4 契约被改：把枚举收窄 → validate 必须红
  N5 派生被删：删掉 state.json 重算 → 必须恢复且一致
  N6 释放门：别人的任务不能释放；自己的可以放弃

运行：python tools/full_test.py [--only N1,N2]
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


def snap():
    base = tempfile.mkdtemp(prefix="se-full-")
    z = os.path.join(base, "se.zip")
    p = subprocess.run(["git", "archive", "--format=zip", "-o", z, "HEAD:silicon-earth"],
                       cwd=PARENT, capture_output=True, text=True)
    if p.returncode != 0:
        return None, p.stderr
    dst = os.path.join(base, "silicon-earth")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Expand-Archive -Path '%s' -DestinationPath '%s' -Force" % (z, dst)],
                   capture_output=True)
    subprocess.run(["git", "init", "-q"], cwd=dst, capture_output=True)
    for k, v in (("core.autocrlf", "false"), ("user.email", "full@local"), ("user.name", "full")):
        subprocess.run(["git", "config", k, v], cwd=dst, capture_output=True)
    for c in (["git", "add", "-A"], ["git", "commit", "-q", "-m", "seed"]):
        subprocess.run(c, cwd=dst, capture_output=True)
    subprocess.run([PY, "tools/setup.py"], cwd=dst, capture_output=True)
    return dst, ""


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jdump(p, o):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=2)


def n1_crash():
    r, _ = snap()
    tp = os.path.join(r, "modules", "m-w2-clock", "data", "time.json")
    t = jload(tp)
    t["day"] = max(0, t["day"] - 1)   # 模拟：事件已写、时钟没更新
    jdump(tp, t)
    rc, out = sh(["modules/m-w2-clock/engine.py", "1"], r)
    ep = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    days = []
    with open(ep, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    days.append(json.loads(line)["day"])
                except Exception:
                    pass
    ok = rc == 0 and len(days) == len(set(days))
    record("N1 崩溃后自愈且不写重", ok, f"rc={rc} · 天唯一={len(days)==len(set(days))}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def n2_relay():
    r, _ = snap()
    sh(["tools/world_ops.py", "claim", "T03", "agent-a"], r)
    with open(os.path.join(r, "modules", "m-p2-memory", "data", "seed.json"), "a", encoding="utf-8") as f:
        f.write("\n")
    sh(["tools/agent_ops.py", "handoff", "T03", "agent-a", "写到一半，剩下的交给下一位"], r)
    rc1, out1 = sh(["tools/agent_ops.py", "takeover", "T03", "agent-b", "接手继续"], r)
    rc2, out2 = sh(["tools/deliver.py", "T03", "agent-b"], r)
    d = jload(os.path.join(r, "TASKS.json"))
    t = next(x for x in d["tasks"] if x["id"] == "T03")
    ok = rc1 == 0 and rc2 == 0 and t["status"] == "done" and t.get("handoff")
    record("N2 接力后能交付", ok, f"takeover {rc1} · deliver {rc2} · status {t['status']}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def n3_dep():
    r, _ = snap()
    rc, out = sh(["tools/world_ops.py", "claim", "T12", "agent-a"], r)
    record("N3 依赖门", rc != 0 and "T02" in out, f"rc={rc}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def n4_contract():
    r, _ = snap()
    p = os.path.join(r, "CONTRACTS", "world.schema.json")
    d = jload(p)
    d["definitions"]["region"]["properties"]["kind"]["enum"] = ["home"]
    jdump(p, d)
    rc, out = sh(["tools/world_ops.py", "validate"], r)
    record("N4 契约被改会被抓", rc != 0 and "枚举" in out, f"rc={rc}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def n5_rebuild():
    r, _ = snap()
    sp = os.path.join(r, "modules", "m-w3-settle", "data", "state.json")
    before = jload(sp)
    os.remove(sp)
    rc1, _ = sh(["modules/m-w3-settle/settle.py"], r)
    rc2, out = sh(["tools/check_state.py"], r)
    after = jload(sp) if os.path.exists(sp) else None
    same = bool(after) and before.get("day") == after.get("day") and before.get("regions") == after.get("regions")
    record("N5 派生被删可恢复", rc1 == 0 and rc2 == 0 and same,
           f"settle {rc1} · check {rc2} · 内容{'一致' if same else '不同'}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def n6_release():
    r, _ = snap()
    sh(["tools/world_ops.py", "claim", "T03", "agent-a"], r)
    rc1, out1 = sh(["tools/world_ops.py", "release", "T03", "agent-b"], r)
    rc2, out2 = sh(["tools/world_ops.py", "release", "T03", "agent-a"], r)
    d = jload(os.path.join(r, "TASKS.json"))
    t = next(x for x in d["tasks"] if x["id"] == "T03")
    ok = rc1 != 0 and rc2 == 0 and t["status"] == "todo" and not t["claimed_by"]
    record("N6 释放门", ok, f"他人释放 {rc1} · 本人释放 {rc2} · status {t['status']}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def suite(name, args, cwd):
    rc, out = sh(args, cwd)
    last = [x for x in out.strip().splitlines() if "结果" in x or "就绪" in x or "通过" in x]
    record(name, rc == 0, (last[-1] if last else out.strip().splitlines()[-1] if out.strip() else "")[:70])


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    only = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--only":
        only = sys.argv[2].split(",")

    if not only:
        say("=== 既有套件 ===")
        suite("S1 就绪自检", ["tools/ready.py"], ROOT)
        suite("S2 主测试 10 项", ["tools/sim_test.py"], ROOT)
        suite("S3 闭环 7 项", ["tools/loop_test.py"], ROOT)
        suite("S4 工具自测 5 项", ["tools/agent_ops.py", "selftest"], ROOT)
        say("\n=== 新增场景 ===")

    cases = {"N1": n1_crash, "N2": n2_relay, "N3": n3_dep,
             "N4": n4_contract, "N5": n5_rebuild, "N6": n6_release}
    for k, fn in cases.items():
        if only and k not in only:
            continue
        try:
            fn()
        except Exception as e:
            record(k, False, f"异常 {type(e).__name__}: {e}")

    bad = [r for r in rows if not r[1]]
    say(f"\n合计：{len(rows)-len(bad)}/{len(rows)} 通过")
    if bad:
        say("未过：" + ", ".join(r[0] for r in bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
