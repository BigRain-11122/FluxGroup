#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""station_shards.py - 工位分片的唯一读写入口（SYNC-DESIGN-v2）。

Why（2026-11-11 审计）：队列/车道/回执曾由多台机共写同一批文件，靠 union 与前缀
合并兜底，实测 INTAKE-PENDING 16849 行只有 238 个唯一 id。改为按工位分片后，
同一路径只有一个写入者，冲突与重复在物理上不再发生。

布局：
    cph4/fleet/rt/<station>/queue.jsonl        本工位队列（唯一写者）
    cph4/fleet/rt/<station>/receipts/<id>.json 本工位回执（append-only）
    cph4/fleet/rt/<station>/state.json         心跳与容量（每轮覆盖）
    cph4/fleet/rt/<station>/log/<YYYYMMDD>.jsonl 当日事件

约定：
  * 只写自己的分片；读别家一律 `git show origin/main:<path>`，不动工作树。
  * 队列按 id 合并，保留最后写入的字段；不做整表覆盖以外的事。
  * 缺文件=空，不报错（首次上手不该被当故障）。

用法：
    python3 Tools/fleet/station_shards.py --self-test
    python3 Tools/fleet/station_shards.py --list
    python3 Tools/fleet/station_shards.py --read visual
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DEFAULT = os.path.dirname(os.path.dirname(HERE))
RT_REL = "cph4/fleet/rt"
STATIONS = ("delivery", "visual", "audio", "brain", "control")


# ---------------------------------------------------------------- 写锁
# 2026-11-11 全盘审查发现：write_queue 是"整文件重写"，同机两个进程同时写会丢写。
# 一机一写者是跨机约定，挡不住同机并发（自驱循环 + 命令面 + 巡查可能同时动）。
# 这里加进程级排他锁，跨平台：POSIX 用 fcntl，Windows 用 msvcrt，都没有就退化为无锁。
import contextlib
import threading

_LOCAL = threading.local()


@contextlib.contextmanager
def _write_lock(path):
    depth = getattr(_LOCAL, "depth", 0)
    if depth:                      # 同线程重入（upsert 里再调 write_queue）不重复取锁
        _LOCAL.depth = depth + 1
        try:
            yield
        finally:
            _LOCAL.depth -= 1
        return
    lock = path + ".lock"
    os.makedirs(os.path.dirname(lock), exist_ok=True)
    fh = None
    try:
        fh = open(lock, "a+")
        try:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        except ImportError:
            try:
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            except Exception:
                pass
        _LOCAL.depth = 1
        yield
    finally:
        _LOCAL.depth = 0
        if fh:
            try:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            fh.close()


# 行级不变式：卡必须有 id 与 state；没有 product_id 的卡只允许出现在机制位（夜窗）。
# 状态清单**只许从 state_machine 派生**（2026-11-12）：此前这里写
# (DONE,CANCELLED,ARCHIVED,FAILED)、station_drive 写 (DONE,CANCELLED,SHELVED)，
# 两套互不相认，ARCHIVED 与 SHELVED 行为正好相反。改状态机只改 JSON。
import state_machine as _sm   # noqa: E402  （同目录，导入期失败即崩=正确行为）

TERMINAL = _sm.terminal()


def _root(root=None):
    return os.path.abspath(root or ROOT_DEFAULT)


def rt_dir(station, root=None):
    if station not in STATIONS:
        raise ValueError("unknown station: %s (allowed: %s)" % (station, ", ".join(STATIONS)))
    return os.path.join(_root(root), RT_REL, station)


def queue_path(station, root=None):
    return os.path.join(rt_dir(station, root), "queue.jsonl")


def receipts_dir(station, root=None):
    return os.path.join(rt_dir(station, root), "receipts")


def state_path(station, root=None):
    return os.path.join(rt_dir(station, root), "state.json")


def read_queue(station, root=None):
    """读本工位队列；缺文件返回空表。坏行跳过并计数（不因一行坏掉丢整份）。"""
    p = queue_path(station, root)
    rows, bad = [], 0
    if not os.path.exists(p):
        return rows
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                r = json.loads(s)
            except Exception:
                bad += 1
                continue
            if isinstance(r, dict) and r.get("id"):
                rows.append(r)
    return rows


def _own_station():
    """本机工位：唯一权威是 fleet_identity（身份文件 > hostname > FLEET_STATION）。

    2026-11-12 改。两件必须分清的事（原实现混为一谈）：
      - "没有任何证据" → 返回 None，不启用写保护（沙箱/新机首次部署时正常）
      - "身份读取失败" → 抛错（fail-closed）。原实现在 local_model 导入失败
        （一次普通编辑的语法错即可）时返回 None，一机一写者护栏随之静默失效。
    """
    try:
        import fleet_identity as fid
    except Exception as e:
        raise RuntimeError("身份模块不可用，拒绝写入（fail-closed）：%s" % e)
    return fid.station_or_none()


def guard_write(station, root=None, me=None):
    """一机一写者护栏：**纯判定，不写文件**（2026-11-12 抽出）。

    抽出来的理由：原来护栏埋在 write_queue 里，唯一能验它的办法是真往生产分片写
    （robustness R-11 就是这么干的，跑一次留一张假卡）。纯函数化后测试不必碰生产，
    也让"护栏到底在拦什么"可被单独复算。

    me: 本机工位；不传则从 fleet_identity 解析（解析失败会抛，fail-closed）。
    """
    if root is not None:
        return                      # 沙箱（显式 root）不受限
    who = me if me is not None else _own_station()
    if who and who != station:
        raise PermissionError("跨工位写被拒：本机=%s，目标分片=%s（一机一写者）"
                              % (who, station))


def write_queue(station, rows, root=None, allow_cross=False):
    """原子写：临时文件 + os.replace，避免半份文件被读到。按 id 去重（后写胜）。

    护栏（2026-11-11）：本机身份已声明时，禁止写别的工位分片。
    一机一写者是硬约束，靠"大家自觉"挡不住；沙箱（显式 root）不受此限。
    判定逻辑在 guard_write()（纯函数，可单独测，不必碰生产分片）。
    """
    # 合并（2026-11-12）：远端新增 allow_cross（显式越权通道，给主控派单/迁移用），
    # 本地的护栏已抽成纯函数 guard_write。两者都保留：只有显式 allow_cross 才跳过判定。
    if not allow_cross:
        guard_write(station, root)
    p = queue_path(station, root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    seen = {}
    order = []
    for r in rows:
        if not isinstance(r, dict) or not r.get("id"):
            continue
        k = str(r["id"])
        if k not in seen:
            order.append(k)
        seen[k] = r
    tmp = p + ".tmp.%d" % os.getpid()
    with _write_lock(p):
        with open(tmp, "w", encoding="utf-8") as f:
            for k in order:
                f.write(json.dumps(seen[k], ensure_ascii=False, sort_keys=False) + "\n")
        os.replace(tmp, p)
    return sum(1 for k in order if k in seen)


def upsert(station, row, root=None, allow_cross=False, force=False):
    """两个不同的越权通道，都保留（2026-11-12 合并）：
      allow_cross —— 显式允许写别家分片（主控派单/迁移用；护栏默认拒）
      force       —— 人工重开终态卡（必须带 reason；自动路径一律不许回跳）
    """
    with _write_lock(queue_path(station, root)):      # 读-改-写必须整体加锁，否则丢写
        return _upsert_locked(station, row, root, allow_cross=allow_cross, force=force)


def cas_state(station, card_id, expect, patch, root=None):
    """锁内比较并交换：当前状态 == expect 才应用 patch。返回 (ok, 当前卡)。

    2026-11-12 立。`claim` 原来是"读快照 → 无条件写 RUNNING"，不是原子取件：
    三个进程同时 --once 会各自看到同一张 OPEN 卡，实测执行 3 次、钱扣 3 遍、
    回执因同秒撞名只留 2 份。取件必须"锁内复读 + 校验仍为 OPEN"。
    """
    with _write_lock(queue_path(station, root)):
        rows = {str(r["id"]): r for r in read_queue(station, root)}
        cur = rows.get(str(card_id))
        if not cur or str(cur.get("state") or "").upper() != str(expect).upper():
            return False, cur
        merged = dict(cur)
        merged.update(patch)
        _upsert_locked(station, merged, root)
        return True, merged


def _upsert_locked(station, row, root=None, allow_cross=False, force=False):
    rows = {str(r["id"]): r for r in read_queue(station, root)}
    prev = rows.get(str(row.get("id")))
    if prev:
        merged = dict(prev)
        merged.update(row)
        # 状态迁移校验（2026-11-12 起以 state_machine 为唯一权威）：
        #  - 终态回跳（DONE->RUNNING 等）以前只留痕；现在留痕 + 计数，且**拒写**，
        #    因为回跳等于同卡重复执行，留痕也救不回已经花掉的算力和被覆盖的产物。
        #  - 其余非法迁移（OPEN->DONE 这种跳过执行的）先留痕放行：历史数据里可能有，
        #    等批次3 把 attempt/next_retry_at 补齐后再收紧，避免一次把系统卡死。
        _a = str(prev.get("state") or "").upper()
        _b = str(row.get("state") or "").upper()
        if _b and _a != _b:
            okm, why = _sm.can_transition(_a, _b, strict=False)
            need = {"from": prev.get("state"), "to": row.get("state"),
                    "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
                    "why": row.get("reason") or row.get("why") or "transition",
                    "legal": okm}
            if _a in TERMINAL and not force:
                raise PermissionError(
                    "终态回跳被拒：%s 的卡 %s 从 %s 改回 %s"
                    "（自动路径不许回跳；要重开请用 fleet_cmd card state --yes --why 说明原因）"
                    % ("/".join(TERMINAL), row.get("id"), _a, _b))
            if _a in TERMINAL and force:
                merged.setdefault("forced_reopen", 0)
                merged["forced_reopen"] = int(merged["forced_reopen"]) + 1
            hist = list(prev.get("history") or [])
            hist.append(need)
            merged["history"] = hist[-20:]
            if not okm:
                merged["illegal_transition"] = int(prev.get("illegal_transition") or 0) + 1
        rows[str(row["id"])] = merged
    else:
        rows[str(row["id"])] = row
    write_queue(station, list(rows.values()), root, allow_cross=allow_cross)
    return rows[str(row["id"])]


def append_receipt(station, receipt, root=None):
    d = receipts_dir(station, root)
    os.makedirs(d, exist_ok=True)
    rid = str(receipt.get("id") or receipt.get("card") or "unknown")
    p = os.path.join(d, "%s.json" % rid)
    if os.path.exists(p):
        # 2026-11-11 审查发现：按 id 命名会覆盖上一次回执，抽验就抽不到失败那次。
        # 已存在就带时间戳另存，历史全留（同 id 的多份回执按时间排序即重试史）。
        stamp = (receipt.get("ts") or "").replace(":", "").replace("-", "").replace("T", "")[:14]
        if not stamp:
            import time as _t
            stamp = _t.strftime("%Y%m%d%H%M%S")
        p = os.path.join(d, "%s-%s.json" % (rid, stamp))
    tmp = p + ".tmp.%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    return p


def append_log(station, event, root=None):
    import datetime
    day = datetime.datetime.now().strftime("%Y%m%d")
    d = os.path.join(rt_dir(station, root), "log")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, day + ".jsonl")
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return p


def digest(path):
    """产物摘要的唯一实现：文件=内容 sha256；目录=相对路径+大小+文件摘要按序再取 sha256。
    2026-11-11 预演发现：自驱与巡查各写一份目录哈希算法，抽验必然永远不一致。"""
    import hashlib as _h
    if os.path.isfile(path):
        h = _h.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    if not os.path.isdir(path):
        return None
    h = _h.sha256()
    for d, dirs, xs in os.walk(path):
        dirs.sort()
        for x in sorted(xs):
            fp = os.path.join(d, x)
            rel = os.path.relpath(fp, path)
            h.update(rel.encode())
            h.update(b"|")
            try:
                h.update(str(os.path.getsize(fp)).encode())
                h.update(b"|")
                with open(fp, "rb") as f:
                    h.update(_h.sha256(f.read()).digest())
            except OSError:
                continue
            h.update(b"|")
    return h.hexdigest()


def read_remote_queue(station, root=None, ref="origin/main"):
    """读 origin 上的分片：只走 git blob，不 checkout，不动工作树。"""
    rel = "%s/%s/queue.jsonl" % (RT_REL, station)
    try:
        out = subprocess.run(["git", "show", "%s:%s" % (ref, rel)], cwd=_root(root),
                             capture_output=True, text=True, timeout=30,
                             encoding="utf-8", errors="replace")
    except Exception:
        return []
    if out.returncode != 0:
        return []
    rows = []
    for line in out.stdout.splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            r = json.loads(s)
        except Exception:
            continue
        if isinstance(r, dict) and r.get("id"):
            rows.append(r)
    return rows


def load_all(root=None, prefer_remote=True):
    """五份分片汇总（视图，不落盘）。默认优先读 origin，读不到回落本地。"""
    out = {}
    for s in STATIONS:
        rows = read_remote_queue(s, root) if prefer_remote else []
        if not rows:
            rows = read_queue(s, root)
        out[s] = rows
    return out


def self_test():
    fails = []

    def chk(name, cond, detail=""):
        if not cond:
            fails.append("%s %s" % (name, detail))

    with tempfile.TemporaryDirectory() as td:
        # 1 缺文件 = 空表，不报错
        chk("missing-empty", read_queue("visual", td) == [])
        # 2 写入后读回
        n = write_queue("visual", [{"id": "A", "state": "OPEN"}, {"id": "B", "state": "OPEN"}], td)
        chk("write-count", n == 2, str(n))
        chk("read-back", len(read_queue("visual", td)) == 2)
        # 3 按 id 去重且后写胜
        write_queue("visual", [{"id": "A", "state": "OPEN"}, {"id": "A", "state": "RUNNING"}], td)
        rows = {r["id"]: r for r in read_queue("visual", td)}
        chk("dedupe", len(rows) == 1 and rows["A"]["state"] == "RUNNING")
        # 4 upsert 合并字段
        upsert("visual", {"id": "A", "owner": "visual-1"}, td)
        rows = {r["id"]: r for r in read_queue("visual", td)}
        chk("upsert-merge", rows["A"].get("owner") == "visual-1" and rows["A"].get("state") == "RUNNING")
        # 5 回执与日志
        p = append_receipt("visual", {"id": "A", "outcome": "OK"}, td)
        chk("receipt", os.path.exists(p) and json.load(open(p)).get("outcome") == "OK")
        p2 = append_log("visual", {"evt": "test"}, td)
        chk("log", os.path.exists(p2) and p2.endswith(".jsonl"))
        # 6 非法工位拒绝
        try:
            rt_dir("nope", td)
            chk("bad-station", False)
        except ValueError:
            pass
        # 7 分片互不影响
        write_queue("audio", [{"id": "C", "state": "OPEN"}], td)
        chk("isolated", len(read_queue("visual", td)) == 1 and len(read_queue("audio", td)) == 1)
        # 8 状态清单必须从 state_machine 派生（唯一权威），不许回退成硬编码
        import state_machine as _sm2
        chk("terminal-derived", tuple(TERMINAL) == _sm2.terminal(),
            "%s vs %s" % (TERMINAL, _sm2.terminal()))
        # 9 终态回跳：自动路径拒、人工 force 放行并留痕
        write_queue("visual", [{"id": "Z", "state": "DONE"}], td)
        try:
            upsert("visual", {"id": "Z", "state": "OPEN"}, td)
            chk("no-auto-reopen", False)
        except PermissionError:
            pass
        upsert("visual", {"id": "Z", "state": "OPEN", "why": "人工重开"}, td, force=True)
        z = {r["id"]: r for r in read_queue("visual", td)}["Z"]
        chk("forced-reopen", z.get("state") == "OPEN" and int(z.get("forced_reopen") or 0) == 1, z)
        # 10 非法迁移（跳过执行）留痕并计数
        upsert("visual", {"id": "Y", "state": "OPEN"}, td)
        upsert("visual", {"id": "Y", "state": "DONE"}, td)
        y = {r["id"]: r for r in read_queue("visual", td)}["Y"]
        chk("illegal-counted", int(y.get("illegal_transition") or 0) == 1 and y.get("history"), y)

    if fails:
        print("SELFTEST FAIL: " + "; ".join(fails))
        return 1
    print("SELFTEST OK: 10/10")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--read", metavar="STATION")
    ap.add_argument("--remote", action="store_true", help="读 origin 而不是本地")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.list:
        for s in STATIONS:
            n = len(read_queue(s, a.root))
            print("%-9s %d rows  %s" % (s, n, queue_path(s, a.root)))
        return 0
    if a.read:
        rows = read_remote_queue(a.read, a.root) if a.remote else read_queue(a.read, a.root)
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
