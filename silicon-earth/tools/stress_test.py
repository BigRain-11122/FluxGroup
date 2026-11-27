# -*- coding: utf-8 -*-
"""
stress_test · 极端化 / 多样化测试

X1 长跑 1000 天（性能 + 完整性 + ID 不越位）
X2 空世界（0 事件、0 天）冷启动能否就绪
X3 极端数据（超长文本、emoji、badland 全空）
X4 四进程并发推进：恰好一个成功、无重号、无坏行
X5 十进程并发领取：恰好一个成功
X6 损坏自愈：末行截断 / state 删除 / time 缺失
X7 时钟边界：day=10000 继续推进（ID 位数）
X8 租约边界：过期 1 秒可接管，未过期 1 秒不可
X9 恶意数据：往事件流塞非 JSON 行，派生与结算不许崩

运行：python tools/stress_test.py [--only X1,X4]
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


def sh(args, cwd, timeout=600):
    p = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))


def record(name, ok, detail=""):
    rows.append((name, ok, detail))
    say(("PASS  " if ok else "FAIL  ") + name + ("  · " + detail if detail else ""))


def snap():
    base = tempfile.mkdtemp(prefix="se-stress-")
    z = os.path.join(base, "s.zip")
    subprocess.run(["git", "archive", "--format=zip", "-o", z, "HEAD:silicon-earth"],
                   cwd=PARENT, capture_output=True)
    dst = os.path.join(base, "silicon-earth")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Expand-Archive -Path '%s' -DestinationPath '%s' -Force" % (z, dst)],
                   capture_output=True)
    subprocess.run(["git", "init", "-q"], cwd=dst, capture_output=True)
    for k, v in (("core.autocrlf", "false"), ("user.email", "s@local"), ("user.name", "s")):
        subprocess.run(["git", "config", k, v], cwd=dst, capture_output=True)
    for c in (["git", "add", "-A"], ["git", "commit", "-q", "-m", "seed"]):
        subprocess.run(c, cwd=dst, capture_output=True)
    subprocess.run([PY, "tools/setup.py"], cwd=dst, capture_output=True)
    return dst


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, o):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=2)


def events_of(r):
    p = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    out, bad = [], 0
    if not os.path.exists(p):
        return out, bad
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                bad += 1
    return out, bad


def x1_longrun():
    r = snap()
    import time
    t0 = time.time()
    rc, _ = sh(["modules/m-w2-clock/engine.py", "1000"], r)
    dur = time.time() - t0
    sh(["modules/m-p2-memory/derive.py"], r)
    sh(["modules/m-w3-settle/settle.py"], r)
    rc2, out2 = sh(["tools/world_ops.py", "validate"], r)
    ev, bad = events_of(r)
    ids = {e["id"] for e in ev}
    ok = rc == 0 and rc2 == 0 and bad == 0 and len(ids) == len(ev) and len(ev) >= 1000
    record("X1 长跑 1000 天", ok, f"事件 {len(ev)} · 唯一 {len(ids)} · 坏行 {bad} · {dur:.1f}s")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x2_empty_world():
    r = snap()
    ep = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    open(ep, "w").close()
    dump(os.path.join(r, "modules", "m-w2-clock", "data", "time.json"),
         {"version": "1.1", "day": 0, "seq": 0})
    sh(["modules/m-w3-settle/settle.py"], r)
    sh(["modules/m-p2-memory/derive.py"], r)
    rc, out = sh(["tools/ready.py"], r)
    record("X2 空世界冷启动就绪", rc == 0, "7/7" if "7/7" in out else out.strip()[-60:])
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x3_extreme_data():
    r = snap()
    ep = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    tp = os.path.join(r, "modules", "m-w2-clock", "data", "time.json")
    t = load(tp)
    maxday, maxseq = t["day"], t["seq"]
    with open(ep, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                maxday = max(maxday, int(e["day"]))
                maxseq = max(maxseq, int(e["id"][1:]))
            except Exception:
                pass
    big = "很长的文本" * 500 + "🙂"
    ev = {"id": "E%04d" % (maxseq + 1), "day": maxday + 1, "region_id": "R01", "type": "help",
          "text": big, "actors": ["P0101", "P0102"], "causes": [],
          "weights": {"positive": 1, "cost": 0}}
    with open(ep, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    t["day"] = maxday + 1
    t["seq"] = maxseq + 1
    dump(tp, t)
    sh(["modules/m-w3-settle/settle.py"], r)
    rc, out = sh(["tools/world_ops.py", "validate"], r)
    record("X3 超长文本与emoji", rc == 0, f"rc={rc}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x4_four_engines():
    r = snap()
    dn = subprocess.DEVNULL
    ps = [subprocess.Popen([PY, "modules/m-w2-clock/engine.py", "200"], cwd=r,
                           stdout=dn, stderr=dn) for _ in range(4)]
    codes = [p.wait(timeout=300) for p in ps]
    ev, bad = events_of(r)
    ids = [e["id"] for e in ev]
    ok = sum(1 for c in codes if c == 0) == 1 and len(ids) == len(set(ids)) and bad == 0
    record("X4 四进程并发", ok, f"退出码 {codes} · 事件 {len(ids)} · 唯一 {len(set(ids))}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x5_ten_claims():
    r = snap()
    dn = subprocess.DEVNULL
    ps = [subprocess.Popen([PY, "tools/world_ops.py", "claim", "T03", "agent-%d" % i],
                           cwd=r, stdout=dn, stderr=dn) for i in range(10)]
    codes = [p.wait(timeout=120) for p in ps]
    d = load(os.path.join(r, "TASKS.json"))
    t = next(x for x in d["tasks"] if x["id"] == "T03")
    ok = sum(1 for c in codes if c == 0) == 1 and t.get("claimed_by")
    record("X5 十进程抢同一任务", ok, f"成功 {sum(1 for c in codes if c==0)} · 持有者 {t.get('claimed_by')}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x6_corruption():
    r = snap()
    ep = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    with open(ep, "a", encoding="utf-8") as f:
        f.write('{"id": "E9999", "day": 99')
    rc1, _ = sh(["modules/m-w2-clock/engine.py", "1"], r)
    os.remove(os.path.join(r, "modules", "m-w3-settle", "data", "state.json"))
    rc2, _ = sh(["modules/m-w3-settle/settle.py"], r)
    os.remove(os.path.join(r, "modules", "m-w2-clock", "data", "time.json"))
    rc3, out3 = sh(["modules/m-w2-clock/engine.py", "1"], r)
    ev, bad = events_of(r)
    record("X6 损坏自愈（截断/删state/删time）", rc1 == 0 and rc2 == 0 and rc3 == 0 and bad == 0,
           f"修尾 {rc1} · 重建 {rc2} · 缺时钟 {rc3}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x7_day_10000():
    r = snap()
    tp = os.path.join(r, "modules", "m-w2-clock", "data", "time.json")
    t = load(tp)
    t["day"] = 10000
    t["seq"] = 10000
    dump(tp, t)
    ep = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    with open(ep, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "E10000", "day": 10000, "region_id": "R01", "type": "help",
                            "text": "第10000天", "actors": ["P0101", "P0102"], "causes": [],
                            "weights": {"positive": 1, "cost": 0}}, ensure_ascii=False) + "\n")
    rc, out = sh(["modules/m-w2-clock/engine.py", "1"], r)
    sh(["modules/m-w3-settle/settle.py"], r)
    rc2, out2 = sh(["tools/check_state.py"], r)
    record("X7 第 10000 天仍可推进", rc == 0 and rc2 == 0, f"engine {rc} · check {rc2}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x8_lease_boundary():
    r = snap()
    sh(["tools/world_ops.py", "claim", "T03", "agent-a"], r)
    tp = os.path.join(r, "TASKS.json")
    import time
    now = int(time.time())
    d = load(tp)
    for t in d["tasks"]:
        if t["id"] == "T03":
            t["lease_until"] = now + 60
    dump(tp, d)
    rc1, _ = sh(["tools/agent_ops.py", "takeover", "T03", "agent-b", "抢未过期"], r)
    d = load(tp)
    for t in d["tasks"]:
        if t["id"] == "T03":
            t["lease_until"] = now - 1
    dump(tp, d)
    rc2, _ = sh(["tools/agent_ops.py", "takeover", "T03", "agent-b", "抢已过期"], r)
    record("X8 租约边界", rc1 != 0 and rc2 == 0, f"未过期 {rc1} · 已过期 {rc2}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


def x9_bad_line():
    r = snap()
    ep = os.path.join(r, "modules", "m-w2-clock", "data", "events.jsonl")
    with open(ep, "a", encoding="utf-8") as f:
        f.write("这不是JSON\n")
        f.write("[1,2,3]\n")
    rc1, o1 = sh(["modules/m-p2-memory/derive.py"], r)
    rc2, o2 = sh(["modules/m-w3-settle/settle.py"], r)
    record("X9 坏行不崩（派生/结算）", rc1 == 0 and rc2 == 0, f"derive {rc1} · settle {rc2}")
    shutil.rmtree(os.path.dirname(r), ignore_errors=True)


CASES = {"X1": x1_longrun, "X2": x2_empty_world, "X3": x3_extreme_data,
         "X4": x4_four_engines, "X5": x5_ten_claims, "X6": x6_corruption,
         "X7": x7_day_10000, "X8": x8_lease_boundary, "X9": x9_bad_line}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    only = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--only":
        only = sys.argv[2].split(",")
    for k, fn in CASES.items():
        if only and k not in only:
            continue
        try:
            fn()
        except Exception as e:
            record(k, False, f"异常 {type(e).__name__}: {e}")
    bad = [r for r in rows if not r[1]]
    say(f"\n结果：{len(rows)-len(bad)}/{len(rows)} 通过")
    if bad:
        say("未过：" + ", ".join(r[0] for r in bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
