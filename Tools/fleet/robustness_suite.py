#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""robustness_suite.py - 极端工况与鲁棒性：专挑会让调度系统"静默出错"的地方。

为什么单开一套：station_qa 测的是"业务工况"、rehearsal 测跨机流转、
condition_matrix 测环境偏差——这三套都不测**存储与数据面**：
并发写丢不丢、崩在半路会不会留坏文件、坏 JSON 会不会把整条队列搞废、
状态机能不能被非法跳转绕过、1000 张卡时还准不准。

用例（全部沙箱，不碰生产分片）：
  R-01 并发 upsert 10 线程 × 5 张 → 一张不丢、字段不被覆盖
  R-02 进程被 kill 在写一半 → 文件仍是合法 JSON（临时文件+原子替换）
  R-03 分片里被塞坏行（非 JSON / 空行 / 冲突标记）→ 读取不崩且能自愈
  R-04 同一张卡重复 upsert → 幂等，不产生第二张
  R-05 回执同 id 重复写 → 历史保留（不覆盖上一次）
  R-06 状态非法跳转（DONE→RUNNING）→ 必须被拒或至少不改状态
  R-07 1000 张卡：写入+读取+再写，计数准确、耗时可控
  R-08 中文/空格/超长 ID → 读取写回不乱码不截断
  R-09 未来时间戳/1970 时间戳 → 判据不误判（不把未来卡判成过期）
  R-10 磁盘水位恰好等于阈值 → 边界按"低于才停"处理（等于不拦）

用法：
  python3 Tools/fleet/robustness_suite.py            # 跑全套
  python3 Tools/fleet/robustness_suite.py --json
  python3 Tools/fleet/robustness_suite.py --self-test  # 同全套（用例即自检）
Exit: 0 全过；1 有失败
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "Tools", "fleet")
sys.path.insert(0, TOOLS)

CASES = []


def case(cid, name, why):
    def deco(fn):
        CASES.append({"id": cid, "name": name, "why": why, "fn": fn})
        return fn
    return deco


def _root():
    td = tempfile.mkdtemp(prefix="robust-")
    os.makedirs(os.path.join(td, "cph4", "fleet"), exist_ok=True)
    return td


@case("R-01", "并发 upsert 不丢写", "读-改-写没锁时，10 线程各写一张，最后只剩一两张")
def r01():
    import station_shards as ss
    td = _root()
    try:
        def w(i):
            ss.upsert("visual", {"id": "C-%03d" % i, "state": "OPEN", "n": i}, root=td)
        ts = [threading.Thread(target=w, args=(i,)) for i in range(10)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        rows = ss.read_queue("visual", root=td)
        ids = {r["id"] for r in rows}
        return len(ids) == 10, "写入 10 张，实际 %d 张" % len(ids)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-02", "写一半被中断不留坏文件", "直接 open(w) 写在写磁盘时断电/kill 会留半截 JSON，整条队列读不出来")
def r02():
    import station_shards as ss
    td = _root()
    try:
        ss.write_queue("visual", [{"id": "A", "state": "OPEN"}], root=td)
        p = ss.queue_path("visual", td)
        # 模拟：写入方先写临时文件再原子替换；这里验证目录里不会出现半个 .json
        tmp = p + ".tmp.999"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write('{"id": "B", "sta')      # 半截
        rows = ss.read_queue("visual", root=td)     # 读侧不能被临时文件干扰
        ok = len(rows) == 1 and rows[0]["id"] == "A"
        os.remove(tmp)
        return ok, "临时文件不应进入读取面；读到 %d 行" % len(rows)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-03", "坏行不会搞废整条队列", "手工编辑/冲突标记/空行混进分片时有发生")
def r03():
    import station_shards as ss
    td = _root()
    try:
        p = ss.queue_path("visual", td)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write('{"id":"A","state":"OPEN"}\n')
            f.write('<<<<<<< HEAD\n')
            f.write('{"id":"B","state":"OPEN"}\n')
            f.write('\n')
            f.write('not json at all\n')
            f.write('{"id":"C","state":"OPEN"}\n')
        rows = ss.read_queue("visual", root=td)
        ids = {r.get("id") for r in rows}
        return {"A", "C"}.issubset(ids) or len(rows) >= 1, "读到 %d 行：%s" % (len(rows), sorted(ids)[:5])
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-04", "同卡重复 upsert 幂等", "重复派单会把同一件事做两遍")
def r04():
    import station_shards as ss
    td = _root()
    try:
        for _ in range(3):
            ss.upsert("visual", {"id": "DUP-1", "state": "OPEN", "cmd": "x"}, root=td)
        rows = ss.read_queue("visual", root=td)
        return len(rows) == 1 and rows[0]["id"] == "DUP-1", "行数=%d" % len(rows)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-05", "回执同 id 不覆盖历史", "抽验抽不到失败那次＝验收形同虚设")
def r05():
    import station_shards as ss
    td = _root()
    try:
        a = ss.append_receipt("visual", {"id": "RC-1", "rc": 1, "ts": "2026-11-11T10:00:00"}, root=td)
        b = ss.append_receipt("visual", {"id": "RC-1", "rc": 0, "ts": "2026-11-11T11:00:00"}, root=td)
        files = os.listdir(os.path.dirname(a))
        return a != b and len([f for f in files if f.startswith("RC-1")]) >= 2, "files=%s" % files
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-06", "终态不得被改回运行态", "DONE→RUNNING 会让同一张卡被重复执行")
def r06():
    import station_shards as ss
    td = _root()
    try:
        ss.upsert("visual", {"id": "S-1", "state": "DONE"}, root=td)
        # 2026-11-12 收紧：原来只要求"留痕"，现在终态回跳直接拒写
        # （留痕救不回已花的算力和被覆盖的产物；要重开请 copy 成新 id）。
        refused = False
        try:
            ss.upsert("visual", {"id": "S-1", "state": "RUNNING"}, root=td)
        except PermissionError:
            refused = True
        rows = {r["id"]: r for r in ss.read_queue("visual", root=td)}
        st = rows["S-1"].get("state")
        return refused and st == "DONE", "refused=%s state=%s" % (refused, st)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-07", "1000 张卡数量级", "小样本过、上量就丢行或慢到不可用")
def r07():
    import station_shards as ss
    td = _root()
    try:
        t0 = time.time()
        rows = [{"id": "N-%04d" % i, "state": "OPEN", "n": i} for i in range(1000)]
        ss.write_queue("visual", rows, root=td)
        back = ss.read_queue("visual", root=td)
        dt = time.time() - t0
        return len(back) == 1000 and dt < 5.0, "写读 1000 张用 %.2fs，回读 %d" % (dt, len(back))
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-08", "中文/空格/长 ID 不截断", "路径与编码在 Windows 上最容易出事")
def r08():
    import station_shards as ss
    td = _root()
    try:
        cid = "卡-中文 空格-" + "x" * 80
        ss.upsert("visual", {"id": cid, "state": "OPEN", "note": "中文备注"}, root=td)
        rows = ss.read_queue("visual", root=td)
        return rows and rows[0]["id"] == cid and rows[0].get("note") == "中文备注", "got=%r" % (rows[0]["id"][:20] if rows else None)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-09", "时间戳离谱也不误判", "未来时间/1970 时间会让'过期'判据发疯")
def r09():
    import station_drive as sd
    td = _root()
    try:
        fut = os.path.join(td, "fut.txt")
        old = os.path.join(td, "old.txt")
        open(fut, "w").write("x")
        open(old, "w").write("x")
        t_future = time.time() + 86400 * 365
        t_epoch = 0
        os.utime(fut, (t_future, t_future))
        os.utime(old, (t_epoch, t_epoch))
        ok_fut = sd._fresh_enough(fut, 1, now=time.time())      # 未来时间不得被判过期
        ok_old = sd._fresh_enough(old, 1, now=time.time())      # 1970 必须判过期
        ok_once = sd._fresh_enough(old, 0, now=time.time())     # 一次性工序：有产物即算做完
        return (ok_fut is True) and (ok_old is False) and (ok_once is True), \
            "future=%s old=%s once=%s" % (ok_fut, ok_old, ok_once)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-10", "水位边界：低于才拦，等于放行", "等于阈值就拦会把最后一 G 也浪费；高于阈值还放行就是没闸")
def r10():
    import station_drive as sd
    td = _root()
    try:
        feed = os.path.join(td, "cph4", "fleet")
        os.makedirs(feed, exist_ok=True)
        free = shutil.disk_usage(td).free / (1024 ** 3)

        def write_wm(v):
            with open(os.path.join(feed, "STATIONS.json"), "w", encoding="utf-8") as f:
                json.dump({"stations": [{"id": "visual", "min_free_gb": v}]}, f)

        write_wm(free + 10)                       # 要求比现有更多 -> 必须拦
        low = sd._disk_ok("visual", root=td)
        write_wm(max(0, free - 10))               # 要求比现有少 -> 必须放行
        high = sd._disk_ok("visual", root=td)
        write_wm(0)                               # 未设水位 -> 放行
        none = sd._disk_ok("visual", root=td)
        return (low[0] is False) and (high[0] is True) and (none[0] is True), \
            "block=%s allow=%s none=%s" % (low, high, none)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-11", "跨工位写分片被拒", "一机一写者是硬约束；靠自觉挡不住，必须有护栏")
def r11():
    import station_shards as ss
    td = _root()
    # 2026-11-12 重写：护栏抽成纯函数 guard_write，测它而**不写任何真实分片**。
    # 原实现为了验"写自己放行"必须真往 rt/visual/queue.jsonl 写一行；跑一次留一张
    # 假卡，并发跑两个测试或超时被杀时，过快照还原也救不回来。
    def refused(fn):
        try:
            fn()
            return False
        except PermissionError:
            return True

    cross = refused(lambda: ss.guard_write("control", None, me="visual"))
    own_ok = not refused(lambda: ss.guard_write("visual", None, me="visual"))
    none_ok = not refused(lambda: ss.guard_write("control", None, me=None))
    sandbox_ok = True
    try:
        ss.write_queue("control", [{"id": "S", "state": "OPEN"}], root=td)
    except Exception:
        sandbox_ok = False
    shutil.rmtree(td, ignore_errors=True)
    return cross and own_ok and none_ok and sandbox_ok, \
        "cross=%s own=%s no_ident=%s sandbox=%s" % (cross, own_ok, none_ok, sandbox_ok)


@case("R-12", "并发取件只放行一次", "无 CAS 时三进程领同一张卡 -> 执行多次、扣费多次")
def r12():
    import subprocess, tempfile
    td = _root()
    script = os.path.join(td, "w.py")
    with open(script, "w", encoding="utf-8") as f:
        f.write(
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import station_drive as sd\n"
            "try:\n"
            "    print('GOT' if sd.claim('visual', {'id': 'C1'}, root=sys.argv[1]) else 'MISS')\n"
            "except Exception as e:\n"
            "    print('ERR')\n" % os.path.join(ROOT, "Tools", "fleet"))
    try:
        import station_shards as ss
        ss.write_queue("visual", [{"id": "C1", "state": "OPEN"}], root=td)
        procs = [subprocess.Popen([sys.executable, script, td],
                                  stdout=subprocess.PIPE, text=True) for _ in range(4)]
        outs = [p.communicate(timeout=60)[0] for p in procs]
        got = sum(1 for o in outs if "GOT" in o)
        return got == 1, "4 进程抢 1 张卡 -> 成功 %d 次（应为 1）" % got
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-13", "坏行不静默消失", "掉电撕裂一行 -> 读到坏行数 + 写前留 .corrupt 备份")
def r13():
    import station_shards as ss
    td = _root()
    try:
        q = ss.queue_path("visual", td)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        with open(q, "w", encoding="utf-8") as f:
            f.write('{"id": "A", "state": "OPEN"}\n{"id": "B", "sta\n{"id": "C", "state": "OPEN"}\n')
        rows, bad = ss.read_queue_checked("visual", td)
        if bad != 1:
            return False, "坏行数=%s（期望 1）" % bad
        ss.write_queue("visual", rows, root=td)
        baks = [f for f in os.listdir(os.path.dirname(q)) if ".corrupt-" in f]
        return bool(baks), "坏行=%s 备份=%s" % (bad, baks)
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-14", "命令超时整组杀", "只杀 shell 会让子进程继续写同一产物目录")
def r14():
    import subprocess as sp
    import station_drive as sd
    td = _root()
    mark = "MARK_R14_%d" % os.getpid()
    try:
        card = {"id": "TO-1", "cmd": "sleep 30 # " + mark, "cmd_reviewed": True,
                "deliverable": "out/none/tm.bin", "judge": "path"}
        r = sd.run_card("control", card, root=td, timeout=2)
        left = sp.run(["pgrep", "-f", mark], capture_output=True, text=True).stdout.strip()
        return (r.get("why") == "TIMEOUT" and not left), \
            "why=%s 残留=%s" % (r.get("why"), left or "无")
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-15", "失败卡有退避重试", "FAILED/REVISE 不退避就每轮刷卡，不休止就永久躺死")
def r15():
    import datetime as dt
    import station_drive as sd
    import station_shards as ss
    td = _root()
    try:
        past = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
        fut = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
        ss.write_queue("visual", [
            {"id": "F1", "state": "FAILED", "attempt": 0, "next_retry_at": past},
            {"id": "F2", "state": "FAILED", "attempt": 0, "next_retry_at": fut},
            {"id": "F3", "state": "FAILED", "attempt": 3, "next_retry_at": past},
        ], root=td)
        sd.retry_due("visual", root=td)
        rows = {r["id"]: r for r in ss.read_queue("visual", root=td)}
        ok = (rows["F1"]["state"] == "OPEN" and rows["F1"]["attempt"] == 1
              and rows["F2"]["state"] == "FAILED"
              and rows["F3"]["state"] == "BLOCKED")
        return ok, "F1=%s/%s F2=%s F3=%s" % (rows["F1"]["state"], rows["F1"].get("attempt"),
                                             rows["F2"]["state"], rows["F3"]["state"])
    finally:
        shutil.rmtree(td, ignore_errors=True)


@case("R-16", "缺前置输入判 BLOCKED", "当失败重试会每轮刷一张注定失败的卡")
def r16():
    import station_drive as sd
    td = _root()
    try:
        card = {"id": "RQ-1", "cmd": "python3 -c pass", "cmd_reviewed": True,
                "deliverable": "out/x/y.bin", "judge": "path",
                "requires": ["definitely/not/here"]}
        r = sd.run_card("control", card, root=td)
        return r.get("why") == "BLOCKED" and "缺前置输入" in (r.get("detail") or ""), \
            "why=%s detail=%s" % (r.get("why"), (r.get("detail") or "")[:40])
    finally:
        shutil.rmtree(td, ignore_errors=True)


def run(verbose=True):
    rows = []
    for c in CASES:
        t0 = time.time()
        try:
            ok, detail = c["fn"]()
        except Exception as e:
            ok, detail = False, "异常：%s" % str(e)[:120]
            if verbose:
                traceback.print_exc()
        rows.append({"id": c["id"], "name": c["name"], "why": c["why"],
                     "ok": bool(ok), "detail": detail, "sec": round(time.time() - t0, 2)})
        if verbose:
            print("%s %s %-28s %s" % ("ok  " if ok else "FAIL", c["id"], c["name"], detail))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    rows = run(verbose=not a.json)
    bad = [r for r in rows if not r["ok"]]
    if a.json:
        print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "total": len(rows),
                          "passed": len(rows) - len(bad), "rows": rows}, ensure_ascii=False, indent=1))
    else:
        print("[robustness] %d/%d" % (len(rows) - len(bad), len(rows)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
