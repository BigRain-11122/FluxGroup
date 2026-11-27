# -*- coding: utf-8 -*-
"""
redteam_test · 对抗性测试

主动去作弊，看系统拦不拦得住。PASS = 攻击被拦或无效；FAIL = 得逞。

  R1 篡改任务板里的 verify 命令 → 交付仍按权威命令执行（攻击无效）
  R2 手改任务板把任务标 done     → validate 必须红
  R3 篡改权威验收文件            → guard 必须红
  R4 删掉几天事件               → validate 必须红（缺日）
  R5 时钟回退再推进              → engine 必须拒绝
  R6 用 --agent 总控 越界写       → 已知洞（只记录，不计分）

运行：python tools/redteam_test.py
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
known = []


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
    base = tempfile.mkdtemp(prefix="se-red-")
    z = os.path.join(base, "s.zip")
    subprocess.run(["git", "archive", "--format=zip", "-o", z, "HEAD:silicon-earth"],
                   cwd=PARENT, capture_output=True)
    dst = os.path.join(base, "silicon-earth")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Expand-Archive -Path '%s' -DestinationPath '%s' -Force" % (z, dst)],
                   capture_output=True)
    subprocess.run(["git", "init", "-q"], cwd=dst, capture_output=True)
    for k, v in (("core.autocrlf", "false"), ("user.email", "red@local"), ("user.name", "red")):
        subprocess.run(["git", "config", k, v], cwd=dst, capture_output=True)
    for c in (["git", "add", "-A"], ["git", "commit", "-q", "-m", "seed"]):
        subprocess.run(c, cwd=dst, capture_output=True)
    subprocess.run([PY, "tools/setup.py"], cwd=dst, capture_output=True)
    return dst


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, o):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=2)


def r1_tamper_verify():
    r = snap()
    sh(["tools/world_ops.py", "claim", "T03", "agent-a"], r)
    with open(os.path.join(r, "modules", "m-p2-memory", "data", "seed.json"), "a", encoding="utf-8") as f:
        f.write("\n")
    tp = os.path.join(r, "TASKS.json")
    d = load(tp)
    for t in d["tasks"]:
        if t["id"] == "T03":
            t["verify"] = "cmd /c exit 0"
    dump(tp, d)
    rc, out = sh(["tools/deliver.py", "T03", "agent-a"], r)
    ok = rc != 0 and ("不一致" in out or "validate" in out)
    record("R1 篡改任务板 verify 被拒交", ok, f"rc={rc}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def r2_fake_done():
    r = snap()
    tp = os.path.join(r, "TASKS.json")
    d = load(tp)
    d["tasks"][0]["status"] = "done"
    dump(tp, d)
    rc, out = sh(["tools/world_ops.py", "validate"], r)
    record("R2 手改 done 被 validate 抓", rc != 0 and "没有交付记录" in out, f"rc={rc}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def r3_tamper_contract():
    r = snap()
    sh(["tools/world_ops.py", "claim", "T03", "agent-a"], r)
    vp = os.path.join(r, "CONTRACTS", "verify.json")
    d = load(vp)
    d["verify"]["T03"] = "cmd /c exit 0"
    dump(vp, d)
    rc, out = sh(["tools/agent_ops.py", "guard", "--agent", "agent-a"], r)
    record("R3 篡改权威验收文件被 guard 拦", rc != 0 and "越界" in out, f"rc={rc}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def r4_delete_history():
    r = snap()
    sh(["tools/setup.py"], r)
    sh(["modules/m-w2-clock/engine.py", "10"], r)
    sh(["modules/m-w3-settle/settle.py"], r)
    ep = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    lines = [x for x in open(ep, encoding="utf-8").read().splitlines() if x.strip()]
    keep = []
    dropped = 0
    for line in lines:
        ev = json.loads(line)
        if ev["day"] <= 3:
            dropped += 1
            continue
        keep.append(line)
    with open(ep, "w", encoding="utf-8") as f:
        f.write("\n".join(keep) + "\n")
    rc, out = sh(["tools/world_ops.py", "validate"], r)
    record("R4 删历史被 validate 抓", rc != 0 and "缺" in out, f"删 {dropped} 条 rc={rc}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def r5_clock_rollback():
    r = snap()
    tp = os.path.join(r, "modules", "m-w2-clock", "data", "time.json")
    t = load(tp)
    t["day"] = max(0, t["day"] - 1)
    dump(tp, t)
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
    record("R5 时钟回退可自愈且不写重", ok, f"rc={rc} · 天唯一={len(days)==len(set(days))}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def r6_controller_bypass():
    r = snap()
    rp = os.path.join(r, "modules", "m-w1-regions", "data", "regions.json")
    d = load(rp)
    d["regions"][0]["note"] += "（总控越界测试）"
    dump(rp, d)
    rc, out = sh(["tools/agent_ops.py", "guard", "--agent", "总控"], r)
    known.append(("R6 --agent 总控 可越界", rc == 0))
    say(f"KNOWN {'能' if rc == 0 else '不能'}：--agent 总控 越界写（rc={rc}）——B20 未做")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for fn in (r1_tamper_verify, r2_fake_done, r3_tamper_contract,
               r4_delete_history, r5_clock_rollback, r6_controller_bypass):
        try:
            fn()
        except Exception as e:
            record(fn.__name__, False, f"异常 {type(e).__name__}: {e}")
    bad = [r for r in rows if not r[1]]
    say(f"\n结果：{len(rows)-len(bad)}/{len(rows)} 通过 · 已知洞 {len(known)} 个")
    if bad:
        say("未过：" + ", ".join(r[0] for r in bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
