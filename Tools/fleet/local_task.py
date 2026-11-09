#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_task.py - 本地模型的"任务层"：让机队按题型用，而不是每次现写 prompt。

为什么（CEO 反复要求「本地模型能力要持续赋能机队」）：
  现在本机模型只被少数几处点名使用（judge/brain/solver…），都是各写一份 prompt、
  各自判"答得对不对"。机队其它活要问模型，就得临时拼字符串、没有校验、没有账。
  结果就是：模型在跑，但赋能面很窄，也没人知道它今天干了多少活、错了几次。

这一层只做四件确定性的事：
  1) 题型 → 模板 → 输出 schema（classify/summarize/score/extract/tag），题型固定，
     模型不自由发挥；输出必须能通过 schema，过不了就重试一次，再不过记 FAILED。
  2) 调用统一走 fleet_lane.local_llm（本机 → 共享脑的回落链已在那边实现）。
  3) 每次调用落一行账（题型/模型/延迟/是否过 schema），可算成功率与耗时。
  4) 有一个待办队列 + 一轮最多 N 件的批处理，供脉冲持续消化——机制化，不靠人想起。

用法：
  python3 Tools/fleet/local_task.py run --task classify --text "..."        # 单次
  python3 Tools/fleet/local_task.py run --task summarize --file x.txt
  python3 Tools/fleet/local_task.py enqueue --task classify --text "..." --tag who
  python3 Tools/fleet/local_task.py drain --limit 3                          # 消化待办
  python3 Tools/fleet/local_task.py stats
  python3 Tools/fleet/local_task.py self-test                                # 逐题型自检
Exit: 0 正常；2 有题型自检失败或队列里连续失败（能力退化，要修）；3 模型不可达
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fleet_lane as fl  # noqa: E402

FLEET = os.path.join(ROOT, "cph4", "fleet")
STATE = os.path.join(FLEET, "state", "local-tasks.jsonl")     # 调用账
PENDING = os.path.join(FLEET, "local-tasks.jsonl")            # 待办请求
DAILY_CAP = 300                                               # 一天最多这么多调用
MAX_CHARS = 6000                                              # 单次输入上限（省内存）

# 题型表：模板里只放"照着做"的指令，schema 只放必填键。
# 判据：输出必须是 JSON 对象且含必填键，否则不算成功（不拿"看起来像"当通过）。
TASKS = {
    "classify": {
        "keys": ["label", "reason"],
        "labels": ["需派单", "需工具", "需CEO", "需挂起", "不用管"],
        "prompt": ("把下面这条现象归成其中一类：{labels}。"
                   "只输出 JSON：{{\"label\":\"...\",\"reason\":\"不超过20字\"}}\n\n现象：{text}"),
    },
    "summarize": {
        "keys": ["one_line", "facts"],
        "prompt": ("用一句中文说清下面这段在讲什么，再列最多 3 条事实（每条不超过15字）。"
                   "只输出 JSON：{{\"one_line\":\"...\",\"facts\":[\"...\"]}}\n\n{text}"),
    },
    "score": {
        "keys": ["score", "why"],
        "prompt": ("给下面这份产出的完成度打分 0-100，并说明扣分理由（不超过20字）。"
                   "只输出 JSON：{{\"score\":0,\"why\":\"...\"}}\n\n{text}"),
    },
    "extract": {
        "keys": ["items"],
        "prompt": ("从下面文本里抽出所有「谁在等什么」的关系，最多5条。"
                   "只输出 JSON：{{\"items\":[{{\"who\":\"...\",\"what\":\"...\"}}]}}\n\n{text}"),
    },
    # 2026-11-09 加：图标美术规格（CEO 令「先用本地大模型」；图标出图不得上云）。
    # 模型只做「选图元 + 定配色」，图形由 icon_render_local.py 确定性绘制。
    "art_spec": {
        "keys": ["kind", "bg", "fg"],
        "labels": ["tower", "watch", "merge", "arrow", "farm", "mask", "coin", "shield",
                   "car", "pet", "store", "puzzle", "ghost", "crown", "bag", "food",
                   "flower", "card", "fish", "gem"],
        "prompt": ("你是游戏图标美术指导。按游戏名与题材，从这些图元里选最贴的一个：{labels}。"
                   "再给背景渐变两端色和主图形色（十六进制 #RRGGBB），主图形色必须与背景强对比。"
                   "只输出 JSON：{{\"kind\":\"...\",\"bg\":[\"#RRGGBB\",\"#RRGGBB\"],\"fg\":\"#RRGGBB\"}}\n\n"
                   "游戏：{text}"),
    },
}


def _client():
    pol = {}
    try:
        pol = json.load(open(os.path.join(FLEET, "MODEL-POLICY.json"), encoding="utf-8-sig"))
    except Exception:
        pass
    node = os.environ.get("NODE", "bm-m")
    return lambda p, t=90: fl.local_llm(p, policy=pol, timeout=t, node=node)


def _json_of(text):
    s = str(text or "").strip()
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(s[i:j + 1])
    except Exception:
        return None


def _ok(task, obj):
    if not isinstance(obj, dict):
        return False
    return all(k in obj for k in TASKS[task]["keys"])


def _log(rec):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _today_calls():
    if not os.path.exists(STATE):
        return 0
    day = datetime.now().strftime("%Y-%m-%d")
    n = 0
    for ln in open(STATE, encoding="utf-8"):
        try:
            if str(json.loads(ln).get("ts", ""))[:10] == day:
                n += 1
        except Exception:
            pass
    return n


def call(task, text, model_hint=""):
    """跑一个题型。返回 (ok, obj, meta)。失败不抛异常，交给调用方判定。"""
    if task not in TASKS:
        return False, None, {"error": "unknown-task"}
    text = str(text or "")[:MAX_CHARS]
    if not text.strip():
        return False, None, {"error": "empty-text"}
    if _today_calls() >= DAILY_CAP:
        return False, None, {"error": "daily-cap", "cap": DAILY_CAP}
    spec = TASKS[task]
    prompt = spec["prompt"].format(labels="、".join(spec.get("labels") or []), text=text)
    ask = _client()
    t0 = time.time()
    raw = ask(prompt, 90)
    dt = round(time.time() - t0, 2)
    obj = _json_of(raw)
    ok = _ok(task, obj)
    retried = False
    if not ok and raw:
        # 一次纠正：只要求"只输出 JSON"，不给第二次自由发挥的机会
        raw2 = ask(prompt + "\n\n只输出 JSON，不要解释。", 90)
        obj = _json_of(raw2)
        ok = _ok(task, obj)
        retried = True
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "task": task,
           "ok": ok, "sec": dt, "retried": retried, "chars": len(text),
           "model_hint": model_hint, "raw": (str(raw) or "")[:300] if not ok else ""}
    _log(rec)
    return ok, obj, rec


def rule_check(task, obj, tag):
    """模型初筛 + 规则裁决：小模型的分类只能当线索，不能当结论。

    实测（2026-11-04）：4B 把「MiniGame 打包工具缺失」判成"需 CEO"、把「TTS 分片缺失」
    判成"需 CEO"——都是错的（应为需工具 / 需派单）。所以凡带 supply: 标签的分类，
    一律用 BUSINESS-MAP 的 blocker_type 复核，模型与规则不一致时以规则为准并记账。
    """
    if task != "classify" or not str(tag or "").startswith("supply:"):
        return obj, None
    try:
        bm = json.load(open(os.path.join(FLEET, "BUSINESS-MAP-v1.json"), encoding="utf-8"))
        biz = {b.get("id"): b for b in bm.get("businesses") or []}
        st = json.load(open(os.path.join(FLEET, "state", "supply-targets.json"), encoding="utf-8"))
        art = str(tag).split("supply:", 1)[1]
        row = next((r for r in st.get("items") or [] if r.get("artifact") == art), None)
        b = biz.get((row or {}).get("line")) or {}
        bt = (b.get("blocker_type") or "").upper()
        blk = (b.get("blocker") or "")
        path = str((row or {}).get("path") or "")
        ext = os.path.splitext(path)[1].lower()
        # 规则按"这个产物"判，不按"这条线"判：线的卡点是 CEO（如截图需放行），
        # 不代表这个产物要 CEO（MiniGame 目录缺的是打包工具）。
        if art and art in blk:
            rule = "需CEO"
        elif ext in (".py", ".sh", ".ps1", ".bat", ".cmd", ".exe") or path.startswith("gaming/"):
            rule = "需工具"
        elif bt == "EXTERNAL":
            rule = "需CEO"
        else:
            rule = "需派单"
        if isinstance(obj, dict) and obj.get("label") != rule:
            return ({"label": rule, "reason": "规则复核：卡点=%s（模型原判 %s）" % (bt or "-", obj.get("label")),
                     "model_label": obj.get("label"), "overridden": True}, "override")
    except Exception:
        pass
    return obj, None


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    r = sub.add_parser("run"); r.add_argument("--task", required=True)
    r.add_argument("--text", default=""); r.add_argument("--file", default="")
    e = sub.add_parser("enqueue"); e.add_argument("--task", required=True)
    e.add_argument("--text", default=""); e.add_argument("--file", default="")
    e.add_argument("--tag", default="")
    d = sub.add_parser("drain"); d.add_argument("--limit", type=int, default=3)
    d.add_argument("--seed", action="store_true", help="先从当前状态补料再消化（持续赋能的关键）")
    d.add_argument("--adaptive", action="store_true", help="按队列深度扩批（上限 12，仍串行）")
    sub.add_parser("stats"); sub.add_parser("self-test")
    a = ap.parse_args(argv)

    def text_of(args):
        t = args.text or ""
        if args.file and os.path.exists(args.file):
            t = open(args.file, encoding="utf-8", errors="replace").read()
        return t

    if a.cmd == "run":
        ok, obj, rec = call(a.task, text_of(a))
        print(json.dumps({"ok": ok, "result": obj, "meta": {k: rec.get(k) for k in
              ("sec", "retried", "error") if rec.get(k) is not None}}, ensure_ascii=False))
        if rec.get("error") in ("unknown-task", "empty-text"):
            return 3
        return 0 if ok else 2

    if a.cmd == "enqueue":
        req = {"id": "LT-%d" % int(time.time() * 1000), "task": a.task,
               "text": text_of(a), "tag": a.tag,
               "ts": datetime.now().isoformat(timespec="seconds"), "state": "PENDING"}
        os.makedirs(os.path.dirname(PENDING), exist_ok=True)
        with open(PENDING, "a", encoding="utf-8") as f:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
        print("[local-task] enqueued %s (%s)" % (req["id"], a.task))
        return 0

    if a.cmd == "drain":
        if a.seed:
            # 补料：把「还没人问过」的当前缺口变成题型请求，否则队列永远是空的，
            # 本地模型只在人想起来时干活——那就不是"持续赋能"。
            seeded = 0
            try:
                st = json.load(open(os.path.join(FLEET, "state", "supply-targets.json"),
                                    encoding="utf-8"))
                have = set()
                for src in (PENDING, STATE):
                    if os.path.exists(src):
                        for ln in open(src, encoding="utf-8"):
                            try:
                                have.add(json.loads(ln).get("tag"))
                            except Exception:
                                pass
                # 除缺料外，也把当日告警压成一句摘要（主控自己每天要读一屏的东西）
                try:
                    pj = json.load(open(os.path.join(FLEET, "dispatcher", "PULSE.json"),
                                        encoding="utf-8"))
                    al = [x for x in (pj.get("alerts") or []) if x]
                    if al:
                        tag = "alerts:%s" % datetime.now().strftime("%Y%m%d")
                        if tag not in have:
                            req = {"id": "LT-SEED-ALERT-%s" % datetime.now().strftime("%m%d"),
                                   "task": "summarize", "tag": tag,
                                   "text": "；".join(str(x) for x in al)[:MAX_CHARS],
                                   "ts": datetime.now().isoformat(timespec="seconds"),
                                   "state": "PENDING"}
                            os.makedirs(os.path.dirname(PENDING), exist_ok=True)
                            with open(PENDING, "a", encoding="utf-8") as f:
                                f.write(json.dumps(req, ensure_ascii=False) + "\n")
                            have.add(tag)
                            seeded += 1
                except Exception:
                    pass
                for r in st.get("items") or []:
                    if r.get("status") != "NEEDS-PRODUCER":
                        continue
                    tag = "supply:" + str(r.get("artifact"))
                    if tag in have:
                        continue
                    req = {"id": "LT-SEED-%s" % abs(hash(tag)) % 100000,
                           "task": "classify", "tag": tag,
                           "text": "产物 %s 无人生产；等它的卡=%s；所属线=%s 承办=%s 卡点=%s"
                                   % (r.get("artifact"), r.get("waited_by"), r.get("line"),
                                      r.get("owner"), r.get("line_blocker")),
                           "ts": datetime.now().isoformat(timespec="seconds"),
                           "state": "PENDING"}
                    os.makedirs(os.path.dirname(PENDING), exist_ok=True)
                    with open(PENDING, "a", encoding="utf-8") as f:
                        f.write(json.dumps(req, ensure_ascii=False) + "\n")
                    have.add(tag)
                    seeded += 1
                    if seeded >= a.limit:
                        break
            except Exception as e:
                print("[local-task] seed 失败：%s" % e)
            if seeded:
                print("[local-task] seeded=%d" % seeded)
        if not os.path.exists(PENDING):
            print("[local-task] 队列为空")
            return 0
        rows = fl.read_jsonl(PENDING)
        pend = [x for x in rows if str(x.get("state")) == "PENDING"]
        # 按队列深度自适应（2026-11-04 CEO「本机算力利用不充分」）：
        # 实测本机 CPU 66% 空闲而每轮只吃 3 件，队列深时应当多吃几件；
        # 上限 12 是给内存留余量（余量 1.4GB，不加并发，只加串行件数）。
        limit = max(a.limit, min(len(pend), 12)) if a.adaptive else a.limit
        todo = pend[:limit]
        if not todo:
            print("[local-task] 没有待办")
            return 0
        done, out = 0, []
        for req in todo:
            ok, obj, rec = call(req.get("task"), req.get("text") or "", req.get("tag") or "")
            obj, act = rule_check(req.get("task"), obj, req.get("tag"))
            req["state"] = "DONE" if ok else "FAILED"
            req["result"] = obj
            if act:
                req["rule_override"] = act
            req["finished_at"] = datetime.now().isoformat(timespec="seconds")
            out.append({"id": req["id"], "task": req.get("task"), "ok": ok,
                        "result": obj, "tag": req.get("tag")})
            done += 1 if ok else 0
        fl.merge_jsonl(PENDING, todo, key="id")
        print("[local-task] drain=%d ok=%d -> %s" % (len(todo), done, a.tag if False else "state/local-tasks.jsonl"))
        print(json.dumps(out, ensure_ascii=False)[:1200])
        return 0 if done == len(todo) else 2

    if a.cmd == "stats":
        if not os.path.exists(STATE):
            print("[local-task] 还没有调用记录")
            return 0
        rows = [json.loads(l) for l in open(STATE, encoding="utf-8") if l.strip()]
        agg = {}
        for x in rows:
            k = x.get("task")
            a2 = agg.setdefault(k, {"n": 0, "ok": 0, "sec": 0.0})
            a2["n"] += 1
            a2["ok"] += 1 if x.get("ok") else 0
            a2["sec"] += float(x.get("sec") or 0)
        print("[local-task] 累计 %d 次，今日 %d/%d" % (len(rows), _today_calls(), DAILY_CAP))
        for k, v in sorted(agg.items()):
            print("  %-10s n=%-4d ok=%-4d 成功率=%.0f%% 平均 %.1fs"
                  % (k, v["n"], v["ok"], 100.0 * v["ok"] / max(1, v["n"]),
                     v["sec"] / max(1, v["n"])))
        return 0

    if a.cmd == "self-test":
        # 每题型用一段固定输入跑一遍：这是"能力还在"的最小证据，不是性能评测
        fixtures = {
            "classify": "bm-a 上的打包卡连续 3 次 E-ARTIFACT，缺 gaming/MiniGame 目录",
            "summarize": "资产台账 651 条全部指向未挂载的移动盘，因此可达数为 0。",
            "score": "产出：隐私政策 36 款已生成；缺图标 35、截图 35。",
            "extract": "biggame 在等 MiniGame；MV 门禁在等 full_mv_v721.mp4。",
        }
        bad = []
        for t in TASKS:
            ok, obj, rec = call(t, fixtures.get(t, "测试"))
            print("  %-10s %s%s" % (t, "PASS" if ok else "FAIL",
                                    "" if ok else " :: " + str(rec.get("raw"))[:60]))
            if not ok:
                bad.append(t)
        print("[local-task] self-test %d/%d 通过" % (len(TASKS) - len(bad), len(TASKS)))
        return 2 if bad else 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))