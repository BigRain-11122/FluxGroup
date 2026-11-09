#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""blocker_loop.py - 堵/坏/卡点的常驻闭环：检测 → 自动解 → 复查 → 升级。

CEO 2026-11-08：「堵点坏点卡点都要有相应的循环策略去检测和解决」。

为什么不是一个修一次：过去每类问题都是"这次发现了，修了"，
下次换个形态复发（假绿五型各自复发过、槽位配置写了没生效、同步假绿）。
所以这里把"每一类"都做成四件套：**判据 / 解法 / 周期 / 升级轮次**，
分类表=cph4/fleet/BLOCKER-TAXONOMY-v1.json，代码只实现它点名的检测器与解法。

硬约束（写在分类表 _law 里，这里执行）：
  · 自动解只做确定性、可逆的动作：补卡、改卡字段、推同步、重跑阶段；
    不自动改阈值、不自动删数据、不自动对外。
  · 解不了就按轮次升级，不许静默留着；同一件事连续 N 轮未解 → 进 CEO 面。
  · 同一 (class, key) 只记一次账，重复命中只加 strikes。

用法：
  python3 Tools/fleet/blocker_loop.py             # 只检测（不动作）
  python3 Tools/fleet/blocker_loop.py --apply     # 检测 + 自动解
  python3 Tools/fleet/blocker_loop.py --selftest  # 检查分类表与实现是否对齐
退出码：0 无命中或全部已解 / 1 有未解且未到升级轮次 / 2 有到升级轮次的（要人/要CEO）
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
F = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(F, "state")
SPEC = os.path.join(F, "BLOCKER-TAXONOMY-v1.json")
QUEUE = os.path.join(F, "PRODUCTION-QUEUE.jsonl")
BACKLOG = os.path.join(F, "PRODUCTION-BACKLOG.jsonl")
LEDGER = os.path.join(STATE, "blocker-ledger.jsonl")
STRIKES = os.path.join(STATE, "blocker-strikes.json")
BOARD = os.path.join(F, "BLOCKER-LOOP.md")
sys.path.insert(0, HERE)


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def jload(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def jl(p):
    out = []
    try:
        for line in open(p, encoding="utf-8-sig"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return out


def spec():
    return jload(SPEC, {}) or {}


# ------------------------------------------------------------------ 检测器
def d_lane_empty_and_queue_thin():
    import fleet_lane as fl
    rows = jl(QUEUE)
    opens = [r for r in rows if str(r.get("state") or "").upper() == "OPEN"]
    lanes = {}
    for n in fl.ACTIVE_LANES:
        d = jload(fl.lane_file(ROOT, n), {})
        if d:
            lanes[n] = len(d.get("jobs") or [])
    idle = [n for n, c in lanes.items() if c == 0]
    if idle and len(opens) < 2 * len(lanes):
        return [{"key": "lanes-%d" % len(idle),
                 "detail": "%d 台空转（%s），待派卡只有 %d 张"
                           % (len(idle), ",".join(sorted(idle)), len(opens))}]
    return []


def d_declared_but_no_card():
    steps = (jload(os.path.join(F, "LINE-NEXT-STEPS.json")) or {}).get("lines") or {}
    lines = (jload(os.path.join(STATE, "lines.json")) or {}).get("lines") or []
    rows = jl(QUEUE)
    live = {str(r.get("id")) for r in rows
            if str(r.get("state") or "").upper() in ("OPEN", "RUNNING", "READY", "CLAIMED")}
    hits = []
    for ln in lines:
        lid = str(ln.get("id"))
        if str(ln.get("declared") or "ACTIVE").upper() != "ACTIVE":
            continue
        cards = ((steps.get(lid) or {}).get("cards")) or []
        if not cards:
            continue
        prefix = "R-NEXT-%s" % lid.upper().replace("-", "")[:10]
        if any(i.startswith(prefix) for i in live):
            continue
        # 已完成且产物在盘 = 已推进，不算没派
        done = [r for r in rows if str(r.get("id", "")).startswith(prefix)
                and str(r.get("state") or "").upper() == "DONE"
                and os.path.exists(os.path.join(ROOT, str(r.get("deliverable") or "")))]
        if done:
            continue
        hits.append({"key": lid, "detail": "声明 %s 但无在飞卡"
                     % ",".join(c.get("key", "") for c in cards)})
    return hits


def d_card_defect_repeat():
    rows = jl(QUEUE)
    bad = [r for r in rows if str(r.get("state") or "").upper() in ("CARD-DEFECT", "FAILED")]
    from collections import Counter
    by = Counter((str(r.get("line") or "-"), str(r.get("error_class") or "E-UNKNOWN"))
                 for r in bad)
    hits = []
    for (line, cls), n in by.items():
        if n >= 2:
            ids = [r.get("id") for r in bad
                   if str(r.get("line") or "-") == line
                   and str(r.get("error_class") or "E-UNKNOWN") == cls][:4]
            hits.append({"key": "%s/%s" % (line, cls),
                         "detail": "%s 类失败 %d 次（%s）" % (cls, n, ",".join(map(str, ids))),
                         "cards": ids})
    return hits


def d_card_contract_violations():
    import card_contract_check as cc
    v, _bad = cc.check(ROOT)
    return [{"key": "%s/%s" % (x.get("src"), x.get("id")),
             "detail": "[%s] %s" % (x.get("rule"), x.get("why")),
             "raw": x} for x in v]


def d_node_no_receipt():
    import lane_trust as lt
    import fleet_lane as fl
    hits = []
    for n in fl.ACTIVE_LANES:
        tier, st, why = lt.tier(n)
        if tier in ("silent", "unknown", "probe-only"):
            hits.append({"key": n, "detail": "%s：%s" % (tier, why)})
    return hits



def _node_of(receipt_basename):
    """从回执文件名取机器名。机器名自己带 "-"（bm-a），只切最后一个 "-" 会得到 "a"，
    于是 last_output 永远匹配不上 owner，停摆检测静默失效（2026-11-08 实锚）。"""
    return "-".join(str(receipt_basename).rsplit("-", 2)[-2:])


def _node_last_output():
    """每台机器「最后一次真产出」的时刻（秒）。产物判据=state/remote-receipts 里带该机后缀的回执。"""
    import glob
    out = {}
    for p in glob.glob(os.path.join(F, "state", "remote-receipts", "*.json")):
        b = os.path.basename(p)[:-5]
        node = _node_of(b)
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if m > out.get(node, 0):
            out[node] = m
    return out


def _stalled_worker_hours():
    """阈值唯一源优先取 CARD-POLICY，取不到才用 6h（不许在代码里再立第二个数）。"""
    try:
        cp = jload(os.path.join(F, "CARD-POLICY-v1.json"), {}) or {}
        v = (((cp.get("stall") or {}).get("no_output_hours")))
        if v:
            return float(v)
    except Exception:
        pass
    return 6.0


def d_stalled_worker_cards():
    """认领了卡却几小时零产出的机器：卡挂在它名下，别的机器看不见，等于把活锁死。

    2026-11-08 实锚：bm-a 自 03:15 起零产出，4 张卡（含 AUD-GAME 审计）在它名下
    挂了 7 小时，队列看起来「有在飞」，实际没人跑；09:36 那批才被 STALL 判据撤掉。
    """
    import time
    thr = _stalled_worker_hours() * 3600
    last = _node_last_output()
    t = time.time()
    hits = []
    rows = [r for r in jl(QUEUE) if isinstance(r, dict)]   # 走模块变量，夹具可替换
    by_owner = {}
    for r in rows:
        if r.get("state") != "RUNNING":
            continue
        ow = r.get("owner")
        if not ow:
            continue
        by_owner.setdefault(ow, []).append(r)
    for ow, cards in by_owner.items():
        lo = last.get(ow)
        if lo is None:
            continue                      # 没有回执档案的机器不在此判（另有无回执类）
        idle = t - lo
        if idle < thr:
            continue
        # 刚认领不到 30 分钟的卡不撤，避免和正常启动抢跑
        # 只留"认领超过 5 分钟仍无动静"的卡：这台机器已经 6h+ 零产出，说明它会认领
        # 但执行不动；5 分钟足够真正能干的机器启动，再久就是把活锁死。
        old_enough = [c for c in cards
                      if not _ts_recent(c.get("claimed_at") or c.get("created_at"), 300)]
        if not old_enough:
            continue
        hits.append({"key": ow,
                     "detail": "%s 已 %.1fh 零产出，名下 %d 张在飞卡（含 %s）"
                               % (ow, idle / 3600, len(old_enough), old_enough[0].get("id")),
                     "cards": [c.get("id") for c in old_enough]})
    return hits


def _ts_recent(ts, within_s):
    """时间戳在 within_s 秒内 → True（解析失败按「不新」处理，宁可不动手）。"""
    import time
    from datetime import datetime
    if not ts:
        return False
    try:
        return (time.time() - datetime.fromisoformat(str(ts)).timestamp()) < within_s
    except Exception:
        return False


def d_local_ahead_of_origin():
    try:
        out = subprocess.run(["git", "-C", ROOT, "rev-list", "--count", "origin/main..HEAD"],
                             capture_output=True, text=True, timeout=30)
        n = int((out.stdout or "0").strip() or 0)
    except Exception:
        return []
    if n > 0:
        return [{"key": "ahead%d" % n, "detail": "本地领先 origin %d 个提交" % n}]
    return []


def d_stage_liveness_stale():
    import stage_liveness as sl
    res = sl.audit()
    return [{"key": s, "detail": "阶段超期未真跑"} for s in (res.get("stale") or [])]


def d_patrol_fake_red():
    import patrol
    out = []
    for it in patrol.collect():
        k = str(it.get("key") or "")
        if k.startswith(("remote:", "decl:")) or it.get("round") == "R5":
            out.append({"key": k, "detail": it.get("title") or ""})
    return out


def d_queue_drift():
    """同一 id 在队列与备队列里状态不一致（实测会凭空生出"已派却没派"）。"""
    a = {str(r.get("id")): str(r.get("state") or "").upper() for r in jl(QUEUE)}
    b = {str(r.get("id")): str(r.get("state") or "").upper() for r in jl(BACKLOG)}
    DEAD = {"DONE", "CANCELLED", "ARCHIVED"}
    hits = []
    for i in set(a) & set(b):
        if a[i] != b[i] and not (a[i] in DEAD and b[i] in DEAD):
            hits.append({"key": i, "detail": "队列=%s 备队列=%s" % (a[i], b[i])})
    return hits


def _remote_repo_prefixes():
    """子仓前缀（quant/bigmoney、domain/BigDomain 等）：这些产物在别的机器的独立仓里。"""
    cfg = jload(os.path.join(ROOT, "Tools", "fleet-nodes.json"), {}) or {}
    out = set()
    for n in (cfg.get("nodes") or []):
        for r in (n.get("repos") or []):
            r = str(r).strip("./")
            if r and r != ".":
                out.add(r)
    return out


def d_artifact_missing():
    """卡说完成了，交付物却不在盘 = 假完成（E-ARTIFACT）。

    只判**本机可判**的路径=仓内相对路径。Windows 盘符路径（D:\\…）在本机
    os.path.isabs 返回 False，按相对路径判就是拿看不见的东西定罪——实测
    48 条"假完成"全是 bm-a 上的 D:\\FleetWorker\\…，一条真问题都没有。
    """
    WIN_ABS = re.compile(r"^[A-Za-z]:[\\/]")
    hits = []
    for r in jl(QUEUE):
        if str(r.get("state") or "").upper() not in ("DONE", "UNVERIFIED"):
            continue
        d = str(r.get("deliverable") or "").strip()
        if not d:
            continue
        if WIN_ABS.match(d) or d.startswith("/Volumes/") or d.startswith("/Users/"):
            continue
        if d.startswith("cph4/fleet/state/"):
            continue      # state/ 是可重建投影（会被清理），不算假完成
        if any(d == r or d.startswith(r + "/") for r in _remote_repo_prefixes()):
            continue      # 子仓（bm-a 等的独立仓库），本机不可判
        if "/" not in d and "." not in d and len(d) < 40:
            continue
        if not os.path.exists(os.path.join(ROOT, d)):
            hits.append({"key": str(r.get("id")), "detail": "交付物不在盘：%s" % d})
    return hits


def d_unverified_stuck():
    rows = [r for r in jl(QUEUE) if str(r.get("state") or "").upper() == "UNVERIFIED"]
    return [{"key": str(r.get("id")), "detail": "回执未对上"} for r in rows]


def d_card_unowned():
    """OPEN/RUNNING 却没人负责的卡（RG-09 的兄弟：阻塞也要有主）。"""
    hits = []
    for r in jl(QUEUE):
        if str(r.get("state") or "").upper() in ("OPEN", "RUNNING") and not r.get("owner"):
            hits.append({"key": str(r.get("id")), "detail": "无 owner"})
    return hits


def d_cadence_drift():
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "cadence.py")],
                           cwd=ROOT, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "").strip().splitlines()
        import json as _j
        for line in reversed(out):
            line = line.strip()
            if line.startswith("{"):
                d = _j.loads(line)
                if d.get("errors") or d.get("warnings"):
                    return [{"key": "cadence",
                             "detail": "errors=%s warnings=%s"
                                       % (d.get("errors"), d.get("warnings"))}]
                break
    except Exception:
        pass
    return []


def d_quality_below():
    txt_p = os.path.join(F, "QUALITY-BOARD.md")
    try:
        txt = open(txt_p, encoding="utf-8").read()
    except FileNotFoundError:
        return [{"key": "no-board", "detail": "质量屏不存在"}]
    hits = []
    for line in txt.splitlines():
        if line.startswith("|") and "FAIL" in line and "未评分" not in line:
            name = line.split("|")[1].strip()
            hits.append({"key": name, "detail": line.strip()[:80]})
    return hits


def d_volume_missing():
    rows = jl(os.path.join(F, "vault", "index.jsonl"))
    vols = set()
    for r in rows:
        p = str(r.get("path") or "").replace("\\", "/")
        if p.startswith("/Volumes/"):
            v = p.split("/")[2]
            if not os.path.isdir("/Volumes/%s" % v):
                vols.add(v)
    return [{"key": v, "detail": "台账有引用但卷未挂载"} for v in sorted(vols)]


def d_backup_stale():
    d = jload(os.path.join(STATE, "dr-check.json"), {}) or {}
    if str(d.get("verdict") or "").upper() in ("FAIL", "STALE"):
        return [{"key": "backup", "detail": str(d.get("why") or "备份不新鲜")[:80]}]
    return []


def d_node_repo_diverged():
    """节点仓库已分叉：/poke 只做 ff-only，分叉节点永远拉不到新卡。

    2026-11-08 实锚：bm-c 的 '.' head 在半小时内换了三次（7a34e02e -> 783ab0f7 ->
    1d5c8d410），全都不是 origin/main 祖先；poke 回 accepted:true 而 last_pull 停在
    22:30，派卡与产出归集全部到不了，界面上却只显示"车道空闲"。
    与 NODE-UNSERVICEABLE 的分工：那是"没有回执"，这里是"根本没拉到卡"。
    判据用 git 祖先关系而不是回执/心跳，所以不会被"假受理"骗过。
    """
    import json as _j
    import urllib.request as _u
    try:
        nodes = (_j.load(open(os.path.join(ROOT, "Tools", "fleet-nodes.json"),
                              encoding="utf-8")).get("nodes") or [])
    except Exception:
        return []
    try:
        origin = subprocess.run(["git", "-C", ROOT, "rev-parse", "origin/main"],
                                capture_output=True, text=True, timeout=45).stdout.strip()
    except Exception:
        return []
    if not origin:
        return []
    hits = []
    for n in nodes:
        if not n.get("enabled"):
            continue
        ip = str(n.get("tailnet_ip") or "")
        if not ip or ip.startswith("PENDING"):
            continue
        try:
            with _u.urlopen("http://%s:8790/status" % ip, timeout=8) as r:
                st = _j.loads(r.read().decode())
        except Exception:
            continue            # 取不到状态属"离线"，由别的类判，这里不误报
        head = (st.get("repo_heads") or {}).get(".")
        if not head or head == origin:
            continue
        try:
            chk = subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", head, origin],
                                 capture_output=True, text=True, timeout=45)
        except Exception:
            continue            # 判不了（超时/对象缺失）就不动手，绝不据此报红
        if chk.returncode == 0:
            continue            # 只是落后：ff-only 能合，不算堵
        # rc=1 已分叉；rc=128 等 = 该 head 本库没有（节点自己的新提交）——同样是分叉，
        # 因为 ff-only 只在"head 是 origin 祖先"时才成功，未确认祖先就等于收不到卡。
        # 2026-11-08 实锚：bm-c 半小时里 head 换了四次，全是 128，早期写法会全部漏报。
        hits.append({
            "key": n.get("id"),
            "detail": ("%s 仓库已分叉（head %s 非 origin/main 祖先），/poke 只会假受理，"
                       "新卡与产出归集到不了；解=在该机跑 "
                       "Tools/fleet/remote_closeout_card.py --nodes %s --print-cmd"
                       % (n.get("id"), head[:9], n.get("id"))),
        })
    return hits


DETECTORS = {
    "stalled_worker_cards": d_stalled_worker_cards,
    "lane_empty_and_queue_thin": d_lane_empty_and_queue_thin,
    "declared_but_no_card": d_declared_but_no_card,
    "card_defect_repeat": d_card_defect_repeat,
    "card_contract_violations": d_card_contract_violations,
    "node_no_receipt": d_node_no_receipt,
    "local_ahead_of_origin": d_local_ahead_of_origin,
    "stage_liveness_stale": d_stage_liveness_stale,
    "patrol_fake_red": d_patrol_fake_red,
    "queue_drift": d_queue_drift,
    "artifact_missing": d_artifact_missing,
    "unverified_stuck": d_unverified_stuck,
    "card_unowned": d_card_unowned,
    "cadence_drift": d_cadence_drift,
    "quality_below": d_quality_below,
    "volume_missing": d_volume_missing,
    "backup_stale": d_backup_stale,
    "node_repo_diverged": d_node_repo_diverged,
}


# ------------------------------------------------------------------ 解法
def _run(argv, timeout=180):
    try:
        r = subprocess.run([sys.executable] + argv, cwd=ROOT, capture_output=True,
                           text=True, timeout=timeout,
                           env=dict(os.environ, FLUX_AUTOMATION="1"))
        return r.returncode, (((r.stdout or "").strip().splitlines() or [""])[-1])[:110]
    except Exception as e:
        return 99, str(e)[:90]


def r_supply(hits):
    acts = []
    for argv in (["Tools/fleet/night_fill.py", "--target", "6"],
                 ["Tools/fleet/workgen.py", "--root", "."],
                 ["Tools/fleet/supply_batch.py", "--apply"]):
        rc, tail = _run(argv)
        acts.append("%s rc=%d %s" % (os.path.basename(argv[0]), rc, tail))
    return acts


def r_night_plan(hits):
    rc, tail = _run(["Tools/fleet/night_plan.py"])
    return ["night_plan rc=%d %s" % (rc, tail)]


def r_cancel_and_record(hits):
    import fleet_lane as fl
    # 护栏：只撤「已经死掉」的卡。命中是按 (line, error_class) 归组的，组里可能混进
    # 同 id 但已经重新开成 OPEN/RUNNING 的新卡——那是在飞的活，撤了就是误杀。
    cur = {str(r.get("id")): str(r.get("state") or "").upper() for r in jl(QUEUE)}
    DEAD = ("CARD-DEFECT", "FAILED", "BLOCKED", "UNVERIFIED")
    patch = []
    for h in hits:
        for cid in (h.get("cards") or []):
            if cur.get(str(cid), "MISSING") not in DEAD:
                continue
            patch.append({"id": cid, "state": "CANCELLED",
                          "cancel_reason": "坏卡闭环：%s —— 同类失败反复，"
                                           "先撤卡再改声明/命令，不重派同一张" % h.get("detail", "")[:80]})
    if not patch:
        return []
    n = fl.merge_jsonl(QUEUE, patch)
    return ["撤销 %d 张反复失败的卡（仅限已死状态）" % n]


def r_fix_card_fields(hits):
    import fleet_lane as fl
    import card_contract_check as cc
    patch = []
    for h in hits:
        v = h.get("raw") or {}
        cid, rule = v.get("id"), v.get("rule")
        if not cid:
            continue
        if rule == "NEEDS-INVISIBLE":
            patch.append({"id": cid, "needs": "cpu",
                          "fix_note": "闭环自动修：非法 needs → cpu"})
        elif rule == "NODE-CAP-MISMATCH":
            want = v.get("needs")
            ok_nodes = [n for n, caps in (cc.LANE_CAPS or {}).items() if want in caps]
            if ok_nodes:
                patch.append({"id": cid, "nodes": ok_nodes[:3],
                              "fix_note": "闭环自动修：钉到有该能力的机器 %s" % ",".join(ok_nodes[:3])})
        elif rule == "DEAD-INPUT":
            patch.append({"id": cid, "state": "BLOCKED", "owner": "bm-m",
                          "blocked_reason": "输入在未挂载的卷 %s" % v.get("volume")})
    if not patch:
        return []
    src = BACKLOG if any(any(x.get("id") == p["id"] for x in jl(BACKLOG)) for p in patch) else QUEUE
    n = fl.merge_jsonl(src, patch)
    return ["修 %d 张卡字段" % n]


def r_dispatch_probe(hits):
    import fleet_lane as fl
    made = []
    for h in hits:
        n = h.get("key")
        cid = "PROBE-AUTO-%s-%s" % (n, datetime.now().strftime("%Y%m%d"))
        if any(r.get("id") == cid for r in jl(QUEUE) + jl(BACKLOG)):
            continue
        card = {"id": cid,
                "title": "节点认领自证：%s 写回执证明还能取卡" % n,
                "cmd": ("python -c \"import json,os;os.makedirs('cph4/fleet/queue-receipts',exist_ok=True);"
                        "open('cph4/fleet/queue-receipts/node-probe-%s.json','w').write("
                        "json.dumps({'node':'%s','ok':True,'auto':True}))\"" % (n, n)),
                "cwd": "", "needs": "cpu", "nodes": [n], "hard_nodes": [n],
                "prio": "P0", "day_ok": True, "probe": True, "verify_on_node": True,
                "state": "READY", "requires": [],
                "deliverable": "cph4/fleet/queue-receipts/node-probe-%s.json" % n,
                "accept": "回执在 origin 出现即证明能取卡", "line": "fleet-ops",
                "created_by": "blocker_loop", "created_at": now(),
                "why": "闭环：%s" % (h.get("detail") or "")[:80]}
        fl.merge_jsonl(BACKLOG, [card])
        made.append(cid)
    return ["派自证卡 %s" % ",".join(made) if made else "自证卡已在册"]


def r_state_push(hits):
    rc, tail = _run(["Tools/fleet/state_push.py"])
    return ["state_push rc=%d %s" % (rc, tail)]


def r_run_stale_stage_once(hits):
    import master_pulse as mp
    want = {h.get("key") for h in hits}
    acts = []
    for name, argv, to, ok, _slow in mp.STAGES:
        if name not in want:
            continue
        rc, tail = _run([argv[0]] + list(argv[1:]) if argv[0].endswith(".py") else argv,
                        timeout=min(int(to or 120), 180))
        acts.append("%s rc=%d %s" % (name, rc, tail))
        if len(acts) >= 3:
            break
    return acts or ["没有可重跑的阶段"]


def r_classify_only(hits):
    return ["已定性为不需行动（%d 项），不重复报" % len(hits)]


def r_reconcile_drift(hits):
    """同 id 漂移：以「队列」为准（它是派单真值），把备队列那行对齐；两边都死就不动。"""
    import fleet_lane as fl
    q = {str(r.get("id")): r for r in jl(QUEUE)}
    patch = []
    for h in hits:
        i = h.get("key")
        if i in q and q[i].get("state"):
            patch.append(dict(q[i], fix_note="闭环：按队列对齐备队列状态"))
    if not patch:
        return []
    return ["对齐 %d 行" % fl.merge_jsonl(BACKLOG, patch)]


def r_reopen_missing(hits):
    """假完成：交付物不在盘就把卡打回 OPEN，并写清原因（不许留在 DONE 里骗人）。"""
    import fleet_lane as fl
    patch = [{"id": h.get("key"), "state": "OPEN",
              "reopen_reason": "闭环：交付物不在盘（E-ARTIFACT），重新执行",
              "reopened_at": now()} for h in hits]
    if not patch:
        return []
    return ["重开 %d 张假完成卡" % fl.merge_jsonl(QUEUE, patch)]


def r_receipt_match(hits):
    rc, tail = _run(["Tools/fleet/receipt_match.py", "--apply"])
    return ["receipt_match rc=%d %s" % (rc, tail)]


def r_assign_owner(hits):
    """无主的活卡：按卡的 nodes 里第一台在线机定责；定不了就挂到主控（至少有人）。"""
    import fleet_lane as fl
    patch = []
    for h in hits:
        i = h.get("key")
        row = next((r for r in jl(QUEUE) if str(r.get("id")) == i), None)
        if not row:
            continue
        pref = [n for n in (row.get("nodes") or []) if n in fl.ACTIVE_LANES]
        patch.append({"id": i, "owner": (pref or ["bm-m"])[0],
                      "owner_note": "闭环：无主卡按 nodes 定责"})
    if not patch:
        return []
    return ["定责 %d 张" % fl.merge_jsonl(QUEUE, patch)]


def r_release_stalled(hits):
    """把停摆机器名下的在飞卡退回 OPEN 并改派其他在线机。

    为什么不能只报不修：卡挂在 owner 名下时，别的机器的 claim 看不到它（state=RUNNING），
    于是「有活」和「没人干」可以同时成立（bm-a 03:15–09:36 实锚）。
    动作是可逆的：只改 state/owner/nodes 并写明理由，谁都能重开或接手。
    """
    import fleet_lane as fl
    cur = {str(r.get("id")): r for r in jl(QUEUE) if isinstance(r, dict)}
    alive = [n for n in fl.ACTIVE_LANES]
    patch, moved = [], 0
    for h in hits:
        stalled = h.get("key")
        others = [n for n in alive if n != stalled]
        if not others:
            continue
        for cid in (h.get("cards") or []):
            row = cur.get(str(cid))
            if not row or str(row.get("state") or "").upper() != "RUNNING":
                continue          # 期间已被执行完或改过状态，绝不覆盖
            patch.append({"id": cid, "state": "OPEN", "owner": None,
                          "claimed_at": None,
                          "nodes": others,
                          "release_reason": "RELEASED-STALLED-WORKER: %s（改派 %s）"
                                            % (h.get("detail", "")[:80], ",".join(others)),
                          "released_by": "blocker_loop:stalled_worker"})
            moved += 1
    if not patch:
        return []
    n = fl.merge_jsonl(QUEUE, patch)
    return ["释放 %d 张停摆机名下的卡并改派（%d 条落盘）" % (moved, n)]


def r_rebuild_cadence(hits):
    rc, tail = _run(["Tools/fleet/cadence_build.py"])
    return ["cadence_build rc=%d %s" % (rc, tail)]


def r_vault_rebuild(hits):
    rc, tail = _run(["Tools/fleet/vault.py", "rebuild"], timeout=300)
    return ["vault rebuild rc=%d %s" % (rc, tail)]


def r_run_backup(hits):
    try:
        r = subprocess.run(["/bin/bash", os.path.join(ROOT, "Tools", "fleet",
                                                     "backup_sync.sh")],
                           cwd=ROOT, capture_output=True, text=True, timeout=600)
        return ["backup rc=%d" % r.returncode]
    except Exception as e:
        return ["backup 异常 %s" % str(e)[:60]]


RESOLVERS = {
    "run:night_fill+workgen+supply_batch": r_supply,
    "run:night_plan": r_night_plan,
    "cancel_and_record": r_cancel_and_record,
    "fix_card_fields": r_fix_card_fields,
    "dispatch_probe": r_dispatch_probe,
    "state_push": r_state_push,
    "run_stale_stage_once": r_run_stale_stage_once,
    "classify_only": r_classify_only,
    "reconcile_drift": r_reconcile_drift,
    "reopen_missing": r_reopen_missing,
    "receipt_match": r_receipt_match,
    "assign_owner": r_assign_owner,
    "rebuild_cadence": r_rebuild_cadence,
    "vault_rebuild": r_vault_rebuild,
    "run_backup": r_run_backup,
    "release_stalled": r_release_stalled,
}


# ------------------------------------------------------------------ 闭环
def coverage():
    """分类表点名的检测器/解法是否都实现了；缺的就是纸面政策。"""
    sp = spec()
    missing = []
    for c in (sp.get("classes") or []):
        if c.get("detect") not in DETECTORS:
            missing.append("%s:detect=%s" % (c.get("id"), c.get("detect")))
        if c.get("resolve") not in RESOLVERS:
            missing.append("%s:resolve=%s" % (c.get("id"), c.get("resolve")))
        for k in ("every_s", "escalate_after", "owner", "symptom"):
            if c.get(k) in (None, ""):
                missing.append("%s:缺%s" % (c.get("id"), k))
    return missing


def cycle(apply=False, force=False):
    sp = spec()
    strikes = jload(STRIKES, {}) or {}
    sched = jload(os.path.join(STATE, "blocker-schedule.json"), {}) or {}
    tnow = datetime.now().timestamp()
    rows, acts, escalate, skipped = [], [], [], []
    for c in (sp.get("classes") or []):
        cid = c.get("id")
        det = DETECTORS.get(c.get("detect"))
        if not det:
            continue
        # 按类分配频率（CEO 2026-11-08「合理规划频率和手段」）：每类只在自己的周期到期时
        # 才跑，不再 16 类同一节拍——同步落后 120s、探针 1h、备份/质量 1h，各按危害定档。
        every = int(c.get("every_s") or 300)
        last = float(sched.get(cid) or 0)
        if not force and last and (tnow - last) < every:
            skipped.append(cid)
            continue
        sched[cid] = tnow
        try:
            hits = det() or []
        except Exception as e:
            hits = [{"key": "detector-error", "detail": "%s: %s" % (type(e).__name__, str(e)[:80])}]
        done = []
        if hits and apply and c.get("auto"):
            try:
                done = RESOLVERS[c.get("resolve")](hits) or []
            except Exception as e:
                done = ["解法异常 %s" % str(e)[:80]]
        for h in hits:
            k = "%s|%s" % (cid, h.get("key"))
            n = int(strikes.get(k) or 0) + (0 if done else 1)
            strikes[k] = n
            rows.append({"class": cid, "key": h.get("key"), "detail": h.get("detail"),
                         "strikes": n, "resolved": bool(done),
                         "actions": done, "ts": now()})
            if not done and n >= int(c.get("escalate_after") or 99):
                escalate.append("%s %s（连续 %d 轮未解）" % (cid, h.get("key"), n))
            if done:
                strikes[k] = 0
        if hits:
            acts.append("%s：命中 %d" % (cid, len(hits)))
        elif strikes.get("%s|*" % cid):
            pass
    return rows, acts, escalate, strikes, sched, skipped


def board(rows, acts, escalate, skipped=None):
    by = {}
    for r in rows:
        by.setdefault(r["class"], []).append(r)
    L = ["# 堵/坏/卡点闭环 %s" % now(), "",
         "分类表：`cph4/fleet/BLOCKER-TAXONOMY-v1.json`（每类四件套：判据/解法/周期/升级轮次）。",
         "本轮命中 %d 项 · 已解 %d · 待升级 %d · 未到周期跳过 %d 类" % (
             len(rows), len([r for r in rows if r["resolved"]]), len(escalate),
             len(skipped or [])), ""]
    if escalate:
        L += ["## 需升级（连轮未解）", ""] + ["- " + e for e in escalate] + [""]
    for cid, rs in by.items():
        L += ["## %s（%d）" % (cid, len(rs)), ""]
        for r in rs[:6]:
            L.append("- `%s` %s%s" % (r["key"], (r["detail"] or "")[:70],
                                      " ✅" + r["actions"][0][:50] if r["resolved"] else
                                      " · 待解（第 %d 轮）" % r["strikes"]))
        L.append("")
    if not by:
        L += ["**本轮无命中。**", ""]
    L += ["---", "_自动解只做确定性动作；解不了的按轮次升级，不许静默留着_"]
    return "\n".join(L) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="忽略各自周期，全部类都跑一遍")
    a = ap.parse_args(argv)

    miss = coverage()
    if a.selftest:
        print(json.dumps({"classes": len(spec().get("classes") or []),
                          "missing": miss, "verdict": "FAIL" if miss else "PASS"},
                         ensure_ascii=False))
        return 1 if miss else 0

    rows, acts, escalate, strikes, sched, skipped = cycle(
        apply=a.apply, force=('--force' in argv))
    txt = board(rows, acts, escalate, skipped)
    os.makedirs(STATE, exist_ok=True)
    open(BOARD, "w", encoding="utf-8").write(txt)
    if a.apply and rows:
        with open(LEDGER, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(strikes, open(STRIKES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.makedirs(STATE, exist_ok=True)
    json.dump(sched, open(os.path.join(STATE, "blocker-schedule.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"ts": now(), "hits": len(rows),
               "resolved": len([r for r in rows if r["resolved"]]),
               "escalate": escalate, "acts": acts, "missing": miss},
              open(os.path.join(STATE, "blocker-loop.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(txt)
    print("[blocker] 命中 %d · 已解 %d · 升级 %d · 分类表缺口 %d"
          % (len(rows), len([r for r in rows if r["resolved"]]), len(escalate), len(miss)))
    if miss:
        return 2
    return 2 if escalate else (1 if rows else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))