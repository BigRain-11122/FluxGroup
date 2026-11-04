#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""line_plan.py - 把"工序表"变成真生产卡（供给层缺的那一环）。

为什么（2026-11-03 实测）：机队整夜在跑，49 张卡里 33 张是自检、15 张是体检，
零成片零可玩——因为派单侧手里只有"扫这条线缺什么"这类只读活，没有工序。
工序表声明在 cph4/fleet/ri/<group>/lines/<line>.json：每段有 cmd / deliverable /
accept / 依赖 / 机器偏好。本工具按盘上事实推进：上一段的产物没出就不派下一段，
同一段当天只派一次。

它只写 BACKLOG（READY），由 night_fill / master_agent 照常提成 OPEN；
不直接写队列（守 I7 单写入口）。

用法：
  python3 line_plan.py [--dry] [--line bigstream-mv] [--json]
Exit: 0 正常（0 张也算正常，会说明原因），1 工序表读不了。
"""
import argparse
import glob
import json
import os
import sys
import time
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FLEET = os.path.join(ROOT, "cph4", "fleet")
BACKLOG = os.path.join(FLEET, "PRODUCTION-BACKLOG.jsonl")
QUEUE = os.path.join(FLEET, "PRODUCTION-QUEUE.jsonl")
TABLES = os.path.join(FLEET, "ri", "*", "lines", "*.json")

sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402
import market_brief as MB  # noqa: E402

ACTIVE = ("OPEN", "RUNNING", "READY", "DONE", "UNVERIFIED")


def jload(p, d=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return d


def rows(path):
    out = []
    try:
        for line in open(path, encoding="utf-8-sig"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    except FileNotFoundError:
        pass
    return out


def render(tpl, table, stage, day):
    root_tools = "Tools"
    return (str(tpl).replace("{root_tools}", root_tools)
            .replace("{master}", str(table.get("master") or ""))
            .replace("{date}", day)
            .replace("{stage}", str(stage.get("id"))))


def validate_table(table):
    """工序表自身的结构错误：这种错会让整条线静默停摆，必须报出来而不是"等上一段"。

    2026-11-03 实测：短剧表里 episode-list 依赖的 tts-qc 段根本不存在，plan_table 只在
    skipped 里写"等上一段 tts-qc"然后 break，accept 段永远轮不到——线从第三天起永久停摆，
    报表上只是"跳过"，没有任何告警。悬空依赖=表错误，不是等待状态。
    """
    errs = []
    stages = table.get("stages") or []
    ids = [s.get("id") for s in stages]
    dup = sorted({i for i in ids if i and ids.count(i) > 1})
    if dup:
        errs.append("段 id 重复：%s" % ",".join(dup))
    known = {i for i in ids if i}
    for s in stages:
        sid = s.get("id") or "<无id>"
        for d in (s.get("depends_on") or []):
            if d not in known:
                errs.append("%s 依赖的 %s 段不存在（悬空依赖，该段永远不会被派）" % (sid, d))
        if not s.get("cmd"):
            errs.append("%s 没有 cmd" % sid)
        if not s.get("deliverable"):
            errs.append("%s 没有 deliverable（无法判完成）" % sid)
    if "accept" not in known:
        errs.append("没有 accept 段（交付必须有验收，DONE≠交付）")

    seen, stack = set(), set()

    def walk(n, path):
        if n in stack:
            errs.append("依赖成环：%s" % " → ".join(path + [n]))
            return
        if n in seen:
            return
        stack.add(n)
        for s in stages:
            if s.get("id") == n:
                for d in (s.get("depends_on") or []):
                    if d in known:
                        walk(d, path + [n])
        stack.discard(n)
        seen.add(n)

    for i in sorted(known):
        walk(i, [])
    return errs


def done_by_receipt(line, stage_id, day):
    """跨机产物认回执（2026-11-03 实锚）：量化/城市的产物落在别的机器的独立仓里，
    主控永远看不到那个路径，于是工序表把"已完成"判成"没做"，线永久停在第一段。
    判据：queue-receipts 下有当天该段回执且 rc==0，就认这一段落过。"""
    d = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
    if not os.path.isdir(d):
        return False
    for n in os.listdir(d):
        if not n.startswith("%s-%s-%s" % (line, stage_id, day)) or not n.endswith(".json"):
            continue
        try:
            r = json.load(open(os.path.join(d, n), encoding="utf-8"))
        except Exception:
            continue
        if r.get("rc") in (0, "0"):
            return True
    return False


def attempts_today(line, stage_id, day):
    """当天该段跑过几次（按回执计）：失败重排要有上限，否则每轮都重排会风暴。"""
    d = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
    if not os.path.isdir(d):
        return 0
    pre = "%s-%s-%s" % (line, stage_id, day)
    return sum(1 for n in os.listdir(d) if n.startswith(pre) and n.endswith(".json"))


def plan_table(table, day, existing, dry):
    line = table.get("line")
    stages = table.get("stages") or []
    made, skipped = [], []
    done_today = set()
    for st in stages:
        sid = "%s-%s-%s" % (line, st.get("id"), day)
        dl = render(st.get("deliverable") or "", table, st, day)
        dl_abs = dl if os.path.isabs(dl) else os.path.join(ROOT, dl)
        # 投料目录为空就不出卡（2026-11-04 实锚）：音色四张分片连挂两天，回执都是
        # "本分片无输入（inbox 共 0 个文件）"。盲派=每天造四张必然失败的卡。
        in_dir = st.get("input_dir")
        if in_dir:
            p_dir = in_dir if os.path.isabs(in_dir) else os.path.join(ROOT, in_dir)
            try:
                files = [f for f in os.listdir(p_dir)
                         if not f.startswith(".") and f.upper() != "README.MD"]
            except OSError:
                files = []
            if not files:
                skipped.append((sid, "NO-INPUT %s 为空（等投料）" % in_dir))
                continue
        if st["id"] in done_today or (dl and os.path.exists(dl_abs)) \
                or done_by_receipt(line, st["id"], day):
            done_today.add(st["id"])
        deps = st.get("depends_on") or []
        if deps and not all(d in done_today for d in deps):
            skipped.append((sid, "等上一段 " + ",".join(deps)))
            continue
        if sid in existing:
            st0 = str(existing[sid] or "").upper()
            # 归档/失败/取消的卡不许堵死当天重跑（2026-11-03 实锚：backtest 卡因同日换过书
            # 被 ARCHIVED，之后 same-day id 永远命中"已在队列"，正确的策略再也排不出去）。
            if st0 not in ("ARCHIVED", "FAILED", "CANCELLED"):
                skipped.append((sid, "已在队列(%s)" % st0))
                continue
            tries = attempts_today(line, st["id"], day)
            if tries >= 2:
                skipped.append((sid, "今日已失败/归档 %d 次，不再重排" % tries))
                continue
        card = {
            "id": sid,
            "title": "[%s] %s" % (table.get("name") or line, st.get("name") or st["id"]),
            "cmd": render(st.get("cmd") or "", table, st, day),
            "cwd": "",
            "requires": [render(r, table, st, day) for r in (st.get("requires") or [])],
            "deliverable": dl,
            "accept": st.get("accept") or "",
            "needs": st.get("needs") or "cpu",
            "nodes": st.get("nodes") or [],
            # requires=依赖仓内脚本/数据（独立仓只存在于特定机器）→ 必须钉死，不许回落。
            # 2026-11-03 实锚：signal 段只是"读 quant/... 结果"，没有 requires 也没钉，
            # 于是落到 Mac 报 E-BLOCKED-INPUT，而卡面显示"跑过了"。
            "hard_nodes": st.get("hard_nodes") or (
                list(st.get("nodes") or []) if st.get("requires") else []),
            "prio": table.get("priority") or "P1",
            "line": line,
            "day_ok": bool(st.get("day_ok", True)),
            "heavy": bool(st.get("heavy")),
            "verify_on_node": True,
            "ok_rc": st.get("ok_rc") or [0, 3],
            "minutes": st.get("minutes"),
            "why": "line_plan: 工序表 %s 段 %s（上一段产物已出）" % (line, st["id"]),
            "created_by": "line_plan",
            "created_at": fl.now_iso(),
            "state": "READY",
        }
        # 分片卡必须豁免语义判重：四张同题不同片的卡看起来"很像"，判重会把它们并成一张。
        if st.get("parallel"):
            card["parallel"] = True
            card["no_dedupe"] = True
        made.append(card)
        done_today.add(st["id"])
        # 默认一条线一次只推进一步，避免同线堆卡；但分片类工段（parallel=true，例如
        # 语料切片按分片拆到四台机）必须同一轮一起派出去，否则"所有机队并行"永远只有一台在跑。
        if not st.get("parallel"):
            break
    return made, skipped


def inactive_lines(root):
    """registry 里 PARKED/PAUSED 的线不许再出卡（2026-11-03 实锚）：
    短剧/漫剧已 PARKED，但工序表仍在生成卡，调度按 parked 跳过 → 卡永久 OPEN、机器空转。
    出卡方与派单方必须读同一份状态，否则两边各自正确、合起来卡死。"""
    try:
        reg = json.load(open(os.path.join(root, "cph4", "fleet", "LINE-REGISTRY.json"),
                             encoding="utf-8"))
    except Exception:
        return set()
    out = set()
    for l in (reg.get("lines") or []):
        if str(l.get("status") or "").upper() in ("PARKED", "PAUSED"):
            out.add(l.get("id"))
    return out


def reconcile_hard_nodes(rows_in, tables):
    """把工序表声明的 hard_nodes 补到已存在的卡上（2026-11-03 实锚）。

    为什么需要这步：表后来才标 hard_nodes 时，早先排出的卡仍是 None，
    派单方按"无钉子"处理就会回落——char-probe 因此落到 Mac，127.0.0.1:8188 连不上，
    产出一份假的"ComfyUI 不可达" BLOCKED，而 bm-c 上其实有 ComfyUI。
    补钉子只改卡面、不改状态，纯对齐。
    """
    want = {}
    for t in tables:
        for st in t.get("stages") or []:
            hn = st.get("hard_nodes") or (
                list(st.get("nodes") or []) if st.get("requires") else [])
            if hn:
                want["%s-%s-" % (t.get("line"), st.get("id"))] = list(hn)
    if not want:
        return 0
    n = 0
    for r in rows_in:
        rid = str(r.get("id") or "")
        if r.get("hard_nodes"):
            continue
        for pre, hn in want.items():
            if rid.startswith(pre):
                r["hard_nodes"] = hn
                n += 1
                break
    return n


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--line", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    day = date.today().isoformat()
    have = {}
    for r in rows(QUEUE) + rows(BACKLOG):
        if r.get("id"):
            have[r["id"]] = r.get("state")
    made, report = [], []
    bad_tables = 0
    INACTIVE = inactive_lines(ROOT)
    files = sorted(glob.glob(TABLES))
    if not files:
        print("没有工序表：%s" % TABLES)
        return 1
    for p in files:
        t = jload(p)
        if not t:
            print("工序表读不了：%s" % p)
            return 1
        if a.line and t.get("line") != a.line:
            continue
        if t.get("line") in INACTIVE:
            report.append({"line": t.get("line"), "table": os.path.relpath(p, ROOT), "cards": [],
                           "skipped": [("LINE-INACTIVE", "registry 里 PARKED/PAUSED：不出卡，避免死卡占队列")]})
            continue
        # 表结构（悬空依赖/无 accept/成环）先判：坏表一律不派卡，否则线会静默停摆。
        errs = validate_table(t)
        if errs:
            bad_tables += 1
            report.append({"line": t.get("line"), "table": os.path.relpath(p, ROOT), "cards": [],
                           "skipped": [("BAD-TABLE", e) for e in errs]})
            continue
        # 市场门（2026-11-03 CEO「务必有市场调研，不要产出垃圾」）：
        # 没有合格市场简报就不派生产卡——先调研再开工，不让机器拿体检充数。
        # 内部线（internal=true，如资产储备）不对外卖，没有市场可言：给它编一份市场简报
        # 就是造假，所以这类线跳过市场门，但仍要过结构与验收。
        if t.get("internal"):
            mk = {"verdict": "PASS", "gaps": []}
        else:
            mk = MB.check(t.get("line"))
        if mk.get("verdict") != "PASS":
            report.append({"line": t.get("line"), "table": os.path.relpath(p, ROOT), "cards": [],
                           "skipped": [("MARKET-GATE", "; ".join(mk.get("gaps") or []))]})
            continue
        cards, skipped = plan_table(t, day, have, a.dry)
        made.extend(cards)
        report.append({"line": t.get("line"), "table": os.path.relpath(p, ROOT),
                       "cards": [c["id"] for c in cards],
                       "skipped": skipped[:6]})
    fixed = 0
    if not a.dry:
        tables = [jload(p) for p in files]
        tables = [t for t in tables if t]
        q = rows(QUEUE)
        b = rows(BACKLOG)
        fixed = reconcile_hard_nodes(q, tables) + reconcile_hard_nodes(b, tables)
        if fixed:
            for path, rs in ((QUEUE, q), (BACKLOG, b)):
                with open(path, "w", encoding="utf-8") as f:
                    for r in rs:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if made and not a.dry:
        fl.merge_jsonl(BACKLOG, made)
    if a.json:
        print(json.dumps({"ts": fl.now_iso(), "dry": a.dry, "made": made, "report": report,
                          "bad_tables": bad_tables}, ensure_ascii=False, indent=1))
        return 2 if bad_tables else 0
    print("工序推进 %s%s" % (day, "（dry）" if a.dry else ""))
    for r in report:
        print("  %-18s 新卡 %s" % (r["line"], ", ".join(r["cards"]) or "0"))
        for sid, why in r["skipped"]:
            print("      - 跳过 %s：%s" % (sid, why))
    if fixed:
        print("补钉子 %d 张（工序表已声明 hard_nodes，旧卡缺失）" % fixed)
    print("合计 %d 张%s" % (len(made), "（已写 BACKLOG READY）" if made and not a.dry else ""))
    if bad_tables:
        print("工序表结构错误 %d 张（这些线的卡永远派不出来，先修表）" % bad_tables)
    return 2 if bad_tables else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))