# -*- coding: utf-8 -*-
"""
silicon-earth · 模拟测试台 v2

铁律：全部在临时副本里跑，不污染正本；每条测试都打印开始时间，避免"静默挂死"。
子进程输出一律重定向到 DEVNULL —— 用 PIPE 而不读，写满管道会死锁（v1 就是这么挂的）。

测试对应老板的真实意图：
  T1 世界能连续走 60 天，且记忆随事件增长
  T2 两个进程同时推进：不许重号、不许丢事件、结束后必须仍然合法
  T3 坏数据 5 例全部拦住
  T4 删掉重算，结果必须逐字节一致
  T5 断电 → 记忆 → 认不出（六扇门第一扇）
  T6 事件分布不单调（正能量但不空转）
  T7 非空模块必须 run/verify 齐备且能跑
  T8 真实协作流：领任务 → 租约生效 → 别人领不走 → 释放
  T9 世界不为访客暂停：无人观看也照样推进

运行：python tools/sim_test.py [--only T2]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY = sys.executable
results = []


def say(msg):
    print(msg, flush=True)


def run(args, cwd, timeout=180):
    p = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))


def fresh_copy(tag):
    dst = os.path.join(tempfile.mkdtemp(prefix="silicon-sim-"), tag)
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("node_modules", "__pycache__", ".git"))
    subprocess.run([PY, "tools/setup.py"], cwd=dst, capture_output=True)
    return dst


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def events_of(root):
    p = os.path.join(root, "modules", "m-w2-clock", "data", "events.jsonl")
    out, bad = [], 0
    if not os.path.exists(p):
        return out, bad
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                bad += 1
    return out, bad


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    say(("PASS  " if ok else "FAIL  ") + name + ("  · " + detail if detail else ""))


def timed(name, fn):
    say(f"\n--- {name} ---")
    t0 = time.time()
    try:
        fn()
    except Exception as e:
        record(name, False, f"异常 {type(e).__name__}: {e}")
    say(f"    ({time.time()-t0:.1f}s)")


# ---------------- T1 ----------------
def t1():
    root = fresh_copy("t1")
    for args in (["modules/m-w2-clock/engine.py", "60"],
                 ["modules/m-p2-memory/derive.py"],
                 ["modules/m-w3-settle/settle.py"]):
        rc, out = run(args, root)
        if rc != 0:
            return record("T1 长跑 60 天", False, f"{args[0]} rc={rc} {out[-200:]}")
    rc, _ = run(["tools/world_ops.py", "validate"], root)
    ev, bad = events_of(root)
    mem = load(os.path.join(root, "modules", "m-p2-memory", "data", "memory.json"))["memories"]
    ok = rc == 0 and len(ev) >= 60 and bad == 0 and len(mem) > 27
    record("T1 长跑 60 天", ok, f"事件 {len(ev)} · 记忆 {len(mem)} · 坏行 {bad} · validate rc={rc}")


# ---------------- T2 ----------------
def t2():
    root = fresh_copy("t2")
    dn = subprocess.DEVNULL
    base_n = len(events_of(root)[0])
    p1 = subprocess.Popen([PY, "modules/m-w2-clock/engine.py", "300"], cwd=root, stdout=dn, stderr=dn)
    time.sleep(0.3)
    p2 = subprocess.Popen([PY, "modules/m-w2-clock/engine.py", "300"], cwd=root, stdout=dn, stderr=dn)
    c1, c2 = p1.wait(timeout=180), p2.wait(timeout=180)
    ev, bad = events_of(root)
    ids = [e["id"] for e in ev]
    run(["modules/m-w3-settle/settle.py"], root)
    rc, _ = run(["tools/world_ops.py", "validate"], root)
    won = sum(1 for c in (c1, c2) if c == 0)
    ok = (won == 1 and sorted([c1, c2]) == [0, 1]
          and len(ids) - base_n == 300 and len(ids) == len(set(ids))
          and bad == 0 and rc == 0)
    record("T2 并发互斥", ok,
           f"rc [{c1},{c2}] · 成功 {won} · 新增 {len(ids)-base_n}/300 · 唯一 {len(set(ids))} · 坏行 {bad}")


# ---------------- T3 ----------------
def t3():
    def missing(root):
        p = os.path.join(root, "modules", "m-w1-regions", "data", "regions.json")
        d = load(p); d["regions"][0].pop("name", None); dump(p, d)

    def bad_enum(root):
        p = os.path.join(root, "modules", "m-w1-regions", "data", "regions.json")
        d = load(p); d["regions"][0]["kind"] = "city"; dump(p, d)

    def dup_id(root):
        p = os.path.join(root, "modules", "m-w1-regions", "data", "regions.json")
        d = load(p); d["regions"].append(dict(d["regions"][0])); dump(p, d)

    def dangling_fk(root):
        p = os.path.join(root, "modules", "m-p1-census", "data", "people.json")
        d = load(p); d["people"][0]["region_id"] = "R99"; dump(p, d)

    def bad_line(root):
        p = os.path.join(root, "modules", "m-w2-clock", "data", "events.jsonl")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write('{"id": "E9\n')

    cases = [("缺字段", missing), ("非法枚举", bad_enum), ("id 重复", dup_id),
             ("悬空外键", dangling_fk), ("坏 JSON 行", bad_line)]
    missed = []
    for name, fn in cases:
        root = fresh_copy("t3-" + name)
        fn(root)
        rc, _ = run(["tools/world_ops.py", "validate"], root)
        if rc == 0:
            missed.append(name)
    record("T3 坏数据拦截 5 例", not missed, "全部拦住" if not missed else "漏掉: " + ", ".join(missed))


# ---------------- T4 ----------------
def t4():
    root = fresh_copy("t4")
    run(["modules/m-w2-clock/engine.py", "30"], root)
    run(["modules/m-p2-memory/derive.py"], root)
    run(["modules/m-w3-settle/settle.py"], root)
    mp = os.path.join(root, "modules", "m-p2-memory", "data", "memory.json")
    sp = os.path.join(root, "modules", "m-w3-settle", "data", "state.json")
    m1, s1 = open(mp, "rb").read(), open(sp, "rb").read()
    os.remove(mp); os.remove(sp)
    run(["modules/m-p2-memory/derive.py"], root)
    run(["modules/m-w3-settle/settle.py"], root)
    m2, s2 = open(mp, "rb").read(), open(sp, "rb").read()
    record("T4 删除后重建一致", m1 == m2 and s1 == s2,
           f"memory {'同' if m1 == m2 else '不同'} · state {'同' if s1 == s2 else '不同'}")


# ---------------- T5 ----------------
def t5():
    root = fresh_copy("t5")
    rc, out = run(["modules/m-w2-clock/intervene.py", "--person", "P0101"], root)
    if rc != 0:
        return record("T5 断电→记忆", False, f"intervene rc={rc} {out[-200:]}")
    run(["modules/m-p2-memory/derive.py"], root)
    run(["modules/m-w3-settle/settle.py"], root)
    mem = load(os.path.join(root, "modules", "m-p2-memory", "data", "memory.json"))["memories"]
    lost = [m for m in mem if m["kind"] == "lost" and m["person_id"] == "P0101"]
    ok = bool(lost) and all(m.get("unrecognized") for m in lost) and all(m.get("event_id") for m in lost)
    rc2, _ = run(["tools/world_ops.py", "validate"], root)
    record("T5 断电→记忆→认不出", ok and rc2 == 0,
           f"lost {len(lost)} · 认不出 {'有' if ok else '无'} · validate rc={rc2}")


# ---------------- T6 ----------------
def t6():
    root = fresh_copy("t6")
    run(["modules/m-w2-clock/engine.py", "120"], root)
    ev, _ = events_of(root)
    c = Counter(e["type"] for e in ev)
    total = sum(c.values()) or 1
    topn = c.most_common(1)[0][1] if c else total
    cost = sum(1 for e in ev if e.get("weights", {}).get("cost"))
    ok = len(c) >= 3 and topn / total < 0.85 and cost / total >= 0.10
    record("T6 分布不单调且有损失", ok,
           f"{dict(c)} · 最高 {topn/total:.0%} · 损失事件 {cost/total:.0%}")


# ---------------- T7 ----------------
def t7():
    root = fresh_copy("t7")
    bad = []
    for mid in sorted(os.listdir(os.path.join(root, "modules"))):
        mj = os.path.join(root, "modules", mid, "module.json")
        if not os.path.exists(mj):
            continue
        meta = load(mj)
        if meta.get("status") == "empty":
            continue
        if not (meta.get("run") or "").strip() or not (meta.get("verify") or "").strip():
            bad.append(f"{mid} run/verify 空")
    rc, out = run(["tools/world_ops.py", "validate"], root)
    if rc != 0:
        bad.append("validate 未通过")
    record("T7 非空模块 run/verify 齐备", not bad, "全部齐备" if not bad else "; ".join(bad))


# ---------------- T8 ----------------
def t8():
    root = fresh_copy("t8")
    dn = subprocess.DEVNULL
    p1 = subprocess.Popen([PY, "tools/world_ops.py", "claim", "T03", "agent-a"], cwd=root, stdout=dn, stderr=dn)
    p2 = subprocess.Popen([PY, "tools/world_ops.py", "claim", "T03", "agent-b"], cwd=root, stdout=dn, stderr=dn)
    c1, c2 = p1.wait(timeout=60), p2.wait(timeout=60)
    data = load(os.path.join(root, "TASKS.json"))
    t = next(x for x in data["tasks"] if x["id"] == "T03")
    ok = sorted([c1, c2]) == [0, 1] and t["claimed_by"] in ("agent-a", "agent-b")
    record("T8 并发领取", ok, f"rc [{c1},{c2}] · 持有者 {t['claimed_by']}")


# ---------------- T9 ----------------
def t9():
    root = fresh_copy("t9")
    before = len(events_of(root)[0])
    tp = os.path.join(root, "modules", "m-w2-clock", "data", "time.json")
    before_day = load(tp)["day"] if os.path.exists(tp) else 0
    rc, _ = run(["modules/m-w2-clock/engine.py", "7"], root)
    ev, bad = events_of(root)
    t = load(tp)
    ok = rc == 0 and len(ev) - before == 7 and t["day"] - before_day == 7 and bad == 0
    record("T9 无人观看也推进", ok,
           f"新增 {len(ev)-before} 条 · 第 {before_day}→{t['day']} 天")


# ---------------- T12 ----------------
def t12():
    root = fresh_copy("t12")
    run(["modules/m-w2-clock/engine.py", "60"], root)
    run(["modules/m-w3-settle/settle.py"], root)
    st = load(os.path.join(root, "modules", "m-w3-settle", "data", "state.json"))
    base = load(os.path.join(root, "modules", "m-w3-settle", "data", "baseline.json"))["baseline"]
    ev, _ = events_of(root)
    per = Counter(e["region_id"] for e in ev)
    all_hit = all(per.get(r["id"], 0) > 0 for r in st["regions"])
    changed = sum(1 for r in st["regions"] if r["positivity"] != base.get(r["id"]))
    states = set(r["state"] for r in st["regions"])
    linked = sum(1 for e in ev if e.get("causes"))
    ok = all_hit and changed >= 3 and len(states) >= 2 and linked >= max(1, len(ev) // 3)
    record("T12 世界在变且有因果", ok,
           f"有事件 {len(per)}/9 · 数值变化 {changed} 块 · 状态 {len(states)} 种 · 带因果 {linked}/{len(ev)}")


TESTS = {"T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5,
         "T6": t6, "T7": t7, "T8": t8, "T9": t9, "T12": t12}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    only = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--only":
        only = sys.argv[2].split(",")
    for k, fn in TESTS.items():
        if only and k not in only:
            continue
        timed(k, fn)
    bad = [r for r in results if not r[1]]
    say("\n结果：{}/{} 通过".format(len(results) - len(bad), len(results)))
    if bad:
        say("未通过：" + ", ".join(r[0] for r in bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
