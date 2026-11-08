#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""supply_batch.py - 把盘上已经能干的真活一次铺成卡，喂满槽位（不做判断、不造假）。

CEO 2026-11-05「你放开全部的算力做好调度」：实测 squeeze 显示"可再吃 52 件、库存仅 3"，
不缺槽位缺活。本工具只把「输入真在盘、产物可判」的三类活落成卡：
  1. 软著材料清点（每个产品目录一张，缺件逐条列）
  2. 游戏提审缺口落单（按 SUBMIT-PACK 实测结果）
  3. 资产库六类缺口（按 asset_library_check 输出）

纪律：
  - 每张卡带 requires 与 hard_nodes=[bm-m]：数据只在本机仓库里，别的机器跑了会出假报告
  - deliverable 每产品独立，已存在就跳过（做过的不重做）
  - 输入不在本机时 audit 直接 rc=3 拒跑，绝不出"全部缺件"的假结论

用法：
  python3 Tools/fleet/supply_batch.py [--apply]
  python3 Tools/fleet/supply_batch.py --audit soft <产品目录名>
  python3 Tools/fleet/supply_batch.py --audit game <产品名>
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
AUDIT = os.path.join(F, "audits")
SOFT_ROOT = os.path.join(ROOT, "软著申请材料")
GAME_PACK = os.path.join(F, "game-v1", "SUBMIT-PACK-20261105.json")
SOFT_REQ = ("源程序", "说明书", "申请表", "privacy")


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def audit_soft(name):
    d = os.path.join(SOFT_ROOT, name)
    if not os.path.isdir(d):
        print("NO-INPUT soft %s" % name)
        return 3
    files = []
    for base, _, fs in os.walk(d):
        files += fs
    joined = " | ".join(files).lower()
    missing = [k for k in SOFT_REQ if k.lower() not in joined]
    out = {"ts": datetime.now().isoformat(timespec="seconds"), "product": name,
           "files": len(files), "missing": missing,
           "verdict": "READY" if not missing else "MISSING"}
    p = os.path.join(AUDIT, "soft", name + ".json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("AUDIT soft %s missing=%s" % (name, missing))
    return 0


def audit_game(name):
    if not os.path.exists(GAME_PACK):
        print("NO-INPUT game pack missing")
        return 3
    pack = json.load(open(GAME_PACK, encoding="utf-8"))
    hit = [p for p in (pack.get("items") or [])
           if (p.get("product") or p.get("dir")) == name]
    out = {"ts": datetime.now().isoformat(timespec="seconds"), "product": name,
           "gaps": (hit[0].get("lacks") if hit else ["未在提审包里找到该产品"]) or [],
           "source": os.path.relpath(GAME_PACK, ROOT)}
    p = os.path.join(AUDIT, "game", name + ".json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("AUDIT game %s gaps=%d" % (name, len(out["gaps"])))
    return 0


def _exclusive_lock():
    """跨进程互斥：供给器被脉按轮调用，两轮并发会各自通过"去重检查"再各写一张，
    于是同一交付物铺成两张（今天实测 4 次复发，11 组）。复检只能缩窗、不能消除竞争，
    真正的解法是**查与写在同一把锁里**。拿不到锁就跳过本轮（下一轮再来，不抢）。"""
    import contextlib

    @contextlib.contextmanager
    def _cm():
        path = os.path.join(F, ".supply-batch.lock")
        fh = None
        try:
            fh = open(path, "a+b")
            try:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except ImportError:
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            except (IOError, OSError):
                raise RuntimeError("locked")
            yield True
        except RuntimeError:
            yield False
        finally:
            if fh is not None:
                try:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
                fh.close()

    return _cm()


def build_cards():
    cards = []
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    n = 0
    for name in sorted(os.listdir(SOFT_ROOT)) if os.path.isdir(SOFT_ROOT) else []:
        if not os.path.isdir(os.path.join(SOFT_ROOT, name)):
            continue
        # 跳过非产品目录：__pycache__、_已封存_*、_报审提交区 之类会被误判成"缺件 4 类"，
        # 让"还缺材料"这件事失真（实测 3 条假缺件全是这类目录）。
        if name.startswith("_"):
            continue
        out = os.path.join("cph4", "fleet", "audits", "soft", name + ".json")
        if os.path.exists(os.path.join(ROOT, out)):
            continue
        n += 1
        cards.append({"id": "AUD-SOFT-%s-%02d" % (stamp, n),
                      "title": "软著材料清点：%s" % name,
                      "cmd": "python Tools/fleet/supply_batch.py --audit soft %s" % name,
                      "cwd": "", "needs": "cpu", "minutes": 1, "heavy": False,
                      "requires": [os.path.join("软著申请材料", name)],
                      "deliverable": out,
                      "accept": "缺件数=0 才算通过；缺件必须逐条列出类别",
                      "nodes": ["bm-m"], "hard_nodes": ["bm-m"], "prio": "P1",
                      "line": "biggame", "state": "READY", "created_by": "supply_batch",
                      "created_at": datetime.now().isoformat(timespec="seconds")})
    try:
        # 2026-11-08 改：逐款审计卡（最多 80 张、每张 1 分钟、钉死主控）= 账面产量，
        # 机器很忙但一行成品也没有。改为一张聚合盘点卡：产物是当日提审包 JSON，
        # 缺口在包里逐款列明，由报告读者看，而不是让每款各占一个卡位。
        stamp = datetime.now().strftime("%Y%m%d")
        out = "cph4/fleet/game-v1/SUBMIT-PACK-%s.json" % stamp
        if not os.path.exists(os.path.join(ROOT, out)):
            cards.append({"id": "PACK-GAME-%s" % stamp,
                          "title": "小游戏提审盘点（聚合：逐款缺口一包在内）",
                          "cmd": "python Tools/fleet/game_submit_pack.py --out %s" % out,
                          "cwd": "", "needs": "cpu", "minutes": 5, "heavy": False,
                          "requires": ["gaming"],
                          "deliverable": out,
                          "accept": "包内逐款列明四类缺件；不许把构建脚本当成品、草版当定稿",
                          "nodes": ["bm-a", "bm-c", "bm-m"], "hard_nodes": [],
                          "prio": "P1", "line": "biggame", "state": "READY",
                          "created_by": "supply_batch", "created_at":
                              datetime.now().isoformat(timespec="seconds")})
    except Exception as e:
        print("game pack skipped:", str(e)[:80])
    return cards


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--audit", nargs=2, metavar=("KIND", "NAME"))
    a = ap.parse_args(argv)
    if a.audit:
        kind, name = a.audit
        return audit_soft(name) if kind == "soft" else audit_game(name)
    cards = build_cards()
    have = {r.get("id") for r in rows(BACKLOG)}
    cards = [c for c in cards if c["id"] not in have]

    # 按交付物去重，不只按卡 id：id 带时间戳，每个批次都算"新卡"，
    # 于是同一交付物会被反复铺（实测 G18_PalacePlunder 连铺两天两张 OPEN）。
    # 判据=交付物已经有活卡（READY/OPEN/RUNNING/CLAIMED）就不再铺。
    LIVE = ("READY", "OPEN", "RUNNING", "CLAIMED", "PENDING")
    live_out = {}
    for p in (BACKLOG, os.path.join(F, "PRODUCTION-QUEUE.jsonl")):
        for r in rows(p):
            if str(r.get("state") or "").upper() in LIVE and r.get("deliverable"):
                live_out[r["deliverable"]] = r.get("id")
    dup = [c for c in cards if c.get("deliverable") in live_out]
    if dup:
        for c in dup[:5]:
            print("SKIP 已有活卡 %s <- %s" % (live_out[c["deliverable"]], c["deliverable"]))
        print("按交付物去重：跳过 %d 张" % len(dup))
    cards = [c for c in cards if c.get("deliverable") not in live_out]
    print("可铺卡 %d 张" % len(cards))
    if not a.apply:
        print("干跑；加 --apply 才写进备队列")
        return 0
    if cards:
        sys.path.insert(0, HERE)
        import fleet_lane as fl
        with _exclusive_lock() as got:
            if not got:
                print("另一轮供给正在写（锁被占），本轮跳过")
                return 0
            keep = _recheck_live(cards)
            if keep:
                print("已写 %d 张到备队列 READY" % fl.merge_jsonl(BACKLOG, keep))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))