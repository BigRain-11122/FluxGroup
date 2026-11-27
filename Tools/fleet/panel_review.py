#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""panel_review.py - 专家团评审：把"人判"换成"skill + 席位投票 + 确定性否决"。

CEO 2026-11-11：「不要人判，你给我找好 skill 和专家团，并让他们科学决策和审查」。

一轮评审三步（顺序不可换）：
  1 VETO  客观否决（产物在不在、哈希对不对、语感闸过不过、红线碰没碰）
          —— 任何一项不过直接 BLOCK，不进投票，不浪费算力。
  2 VOTE  每个席位按 skill 的 rubric 逐条判 PASS/FAIL 并给证据；
          席位经 local_model 通路调用（本机→大脑→主控），不可用则该席记 ABSTAIN。
  3 QUORUM 够票才 PASS；有 BLOCK 票记 REVISE 并列出理由；ABSTAIN 不算通过。

铁律：模型不可用 / 调用失败 → 该票 ABSTAIN；ABSTAIN 不构成通过。宁可 REVISE，不许假绿。

用法：
  python3 Tools/fleet/panel_review.py --product PROD-DRAMA-EP --stage script --evidence out/drama/script/
  python3 Tools/fleet/panel_review.py --task-type T-3D-ADAPT --evidence out/car/build/
  python3 Tools/fleet/panel_review.py --list
  python3 Tools/fleet/panel_review.py --self-test
返回码：0 PASS / 1 REVISE / 2 BLOCK / 3 自检失败
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, HERE)
import local_model as lm  # noqa: E402
import station_shards as ss  # noqa: E402

LEDGER = os.path.join("cph4", "fleet", "state", "panel-ledger.jsonl")


def _j(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _fleet(name):
    return os.path.join(ROOT, "cph4", "fleet", name)


def panels():
    return (_j(_fleet("JUDGE-PANELS-v1.json"), {}) or {}).get("panels") or {}


def panel_for(product=None, stage=None, task_type=None):
    if task_type:
        return task_type, panels().get(task_type)
    tax = _j(_fleet("TAXONOMY-v1.json"), {}) or {}
    tid = ((tax.get("stage_map") or {}).get(product) or {}).get(stage)
    return tid, panels().get(tid)


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    if os.path.isdir(p):
        return sum(os.path.getsize(os.path.join(d, x)) for d, _, xs in os.walk(p) for x in xs)
    return -1


def vetoes(names, evidence):
    """确定性否决。返回 [(项, 通过?, 说明)]。"""
    out = []
    paths = [os.path.join(ROOT, e) for e in (evidence or [])]
    exists = [p for p in paths if os.path.exists(p) and _size(p) > 0]
    for n in names or []:
        if n == "no_artifact":
            out.append((n, bool(exists), "证据 %d 项，在盘 %d 项" % (len(paths), len(exists))))
        elif n == "hash_mismatch":
            bad = []
            for p in exists:
                if os.path.isfile(p):
                    # 若同目录有回执记录了 sha256，必须一致
                    for r in glob.glob(os.path.join(os.path.dirname(p), "*.json"))[:3]:
                        d = _j(r, {}) or {}
                        if d.get("sha256") and d.get("deliverable") and \
                                os.path.basename(d["deliverable"]) == os.path.basename(p):
                            if d["sha256"] != _sha(p):
                                bad.append(os.path.basename(p))
            out.append((n, not bad, "不一致: " + ",".join(bad) if bad else "无哈希冲突"))
        elif n == "voice_gate_fail":
            import voice_gate as vg
            fails = []
            for p in exists:
                if os.path.isfile(p) and p.endswith(".jsonl"):
                    for line in open(p, encoding="utf-8", errors="replace"):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            r = json.loads(line)
                        except Exception:
                            continue
                        res = vg.check(r.get("draft") or "", "comment", r.get("comment") or "")
                        if res["verdict"] == "BLOCK":
                            fails.append(str(r.get("id")))
            out.append((n, not fails, "语感闸未过 %d 条" % len(fails)))
        elif n == "off_redline":
            bad = [p for p in exists if os.path.basename(p).lower() in
                   ("cookies.txt", "cookie.json", "secrets.env")]
            out.append((n, not bad, "红线文件: " + ",".join(map(os.path.basename, bad)) if bad else "未碰红线"))
    return out


EVID_CHARS = 2400          # 单份证据最多带多少字
EVID_TOTAL = 6000          # 一轮评审最多带多少字（8B 的 8192 ctx 要留出判据与回答）


def _evidence_text(evidence, limit=EVID_TOTAL):
    """把证据变成席位真能看到的内容。

    Why（2026-11-13 实锚）：原来只把**文件路径**塞进提示词，席位根本读不到产物，
    只能对着路径猜——连给了 `## 怎么复现` 命令段都判"缺少命令可复制执行"，
    两次 REVISE。评审不看证据就是空转，8B 的算力全花在编理由上。
    """
    out, used = [], 0
    for e in evidence or []:
        s = str(e or "").strip()
        if not s:
            continue
        p = s if os.path.isabs(s) else os.path.join(ROOT, s)
        body = ""
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    body = f.read()
                # 首尾各留一段：可执行命令/结论通常在文末，只截头会让席位判"没写"（实锚）
                if len(body) > EVID_CHARS:
                    head = int(EVID_CHARS * 0.6)
                    tail = EVID_CHARS - head
                    body = (body[:head] + "\n……（中间省略 %d 字）……\n"
                            % (len(body) - EVID_CHARS) + body[-tail:])
            except Exception as ex:
                body = "（读取失败：%s）" % str(ex)[:60]
        elif os.path.isdir(p):
            try:
                names = sorted(os.listdir(p))[:30]
                body = "（目录，%d 项）%s" % (len(os.listdir(p)), "、".join(names))
            except Exception:
                body = "（目录读取失败）"
        if not body:
            body = s                      # 非文件证据（描述/URL）原样给
        if used + len(body) > limit:
            body = body[:max(0, limit - used)]
        used += len(body)
        out.append("--- %s ---\n%s" % (s, body))
        if used >= limit:
            break
    return "\n\n".join(out) or "（无）"


def _seat_prompt(panel, seat_id, evidence, idx):
    items = "\n".join("%d) %s" % (i + 1, r) for i, r in enumerate(panel["rubric"]))
    files = _evidence_text(evidence)
    return ("你是评审席 %s，按 skill「%s」的标准逐条判定。\n"
            "只依据给到的证据内容，不许推测；证据里没有的东西就算缺失。\n"
            "逐条回答，每条给 PASS 或 FAIL 并写一行证据/理由：\n%s\n\n"
            "证据：\n%s\n\n"
            "最后只输出一行 JSON：{\"vote\":\"PASS|REVISE|BLOCK\",\"items\":[{\"n\":1,\"r\":\"PASS\",\"why\":\"...\"}],\"reason\":\"一句话\"}"
            % (seat_id, panel.get("skill"), items, files))


def _parse(text):
    s, e = (text or "").find("{"), (text or "").rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        o = json.loads(text[s:e + 1])
    except Exception:
        return None
    v = str(o.get("vote") or "").upper()
    if v not in ("PASS", "REVISE", "BLOCK"):
        return None
    return o


def order_invariance(product=None, stage=None, task_type=None, evidence=None,
                     generate=None, runs=3, seed=7):
    """位置偏差检验：同一批证据换顺序，判决必须一致。

    依据：多评审/LLM-as-judge 的已知偏差——证据或候选项的排列会改变结论
    （ChatEval 与 Multi-Agents-Debate 都把"顺序敏感性"当作评审可信度的前置检验）。
    本仓已有 VETO/QUORUM，但没验过"同一证据换个顺序会不会翻案"。
    不一致时不给 PASS：判决不稳定就等于没判。
    """
    import random as _rnd
    ev = list(evidence or [])
    if len(ev) < 2:
        return {"stable": True, "verdicts": [], "note": "证据少于 2 项，顺序无意义"}
    rnd = _rnd.Random(seed)
    orders = [ev, list(reversed(ev))]
    for _ in range(max(0, runs - 1)):
        e = list(ev)
        rnd.shuffle(e)
        if e not in orders:
            orders.append(e)
    verdicts, details = [], []
    for e in orders:
        r = review(product=product, stage=stage, task_type=task_type,
                   evidence=e, generate=generate)
        verdicts.append(r.get("verdict"))
        details.append({"order": e, "verdict": r.get("verdict"), "why": r.get("why")})
    stable = len(set(verdicts)) == 1
    return {"stable": stable, "verdicts": verdicts, "orders": orders, "details": details,
            "note": "顺序不变" if stable else "顺序敏感：判决随证据排列变化，不得据此放行"}


def review(product=None, stage=None, task_type=None, evidence=None, generate=None,
           root=None, seat_runner=None):
    """跑一轮评审。generate/seat_runner 可注入，便于自检不起模型。"""
    tid, panel = panel_for(product, stage, task_type)
    if not panel:
        return {"verdict": "BLOCK", "why": "没有评审团配置: %s" % tid, "task_type": tid}
    v = vetoes(panel.get("veto") or [], evidence)
    blocked = [x for x in v if not x[1]]
    if blocked:
        return {"verdict": "BLOCK", "why": "否决项未过: " + "; ".join(
            "%s(%s)" % (x[0], x[2]) for x in blocked), "task_type": tid,
            "veto": [{"name": x[0], "pass": x[1], "why": x[2]} for x in v], "votes": []}

    votes = []
    gen = generate or (lambda p, seat: lm.generate(p, cls="review", timeout=120,
                                                   why="panel:%s" % seat))
    for seat in panel.get("seats") or []:
        try:
            text = gen(_seat_prompt(panel, seat, evidence or [], 0), seat) or ""
        except Exception as e:
            text = ""
            votes.append({"seat": seat, "vote": "ABSTAIN", "why": "调用异常:%s" % str(e)[:60]})
            continue
        o = _parse(text)
        if not o:
            votes.append({"seat": seat, "vote": "ABSTAIN", "why": "无有效 JSON（模型不可用或答偏）"})
        else:
            votes.append({"seat": seat, "vote": o["vote"], "reason": o.get("reason"),
                          "items": o.get("items")})

    need = int(panel.get("quorum") or 1)
    passes = [x for x in votes if x["vote"] == "PASS"]
    blocks = [x for x in votes if x["vote"] == "BLOCK"]
    if blocks:
        verdict, why = "REVISE", "有 BLOCK 票: " + "; ".join(
            "%s:%s" % (b["seat"], (b.get("reason") or "")[:40]) for b in blocks)
    elif len(passes) >= need:
        verdict, why = "PASS", "%d/%d 席通过（quorum=%d）" % (len(passes), len(votes), need)
    else:
        verdict, why = "REVISE", "通过票不足 %d/%d（quorum=%d）" % (len(passes), len(votes), need)

    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "task_type": tid,
           "product": product, "stage": stage, "skill": panel.get("skill"),
           "evidence": evidence or [], "verdict": verdict, "why": why, "votes": votes}
    if root is not False:
        p = os.path.join(root or ROOT, LEDGER)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def self_test():
    ok = total = 0

    def chk(n, c):
        nonlocal ok, total
        total += 1
        ok += 1 if c else 0
        print("%s %s" % ("ok  " if c else "FAIL", n))

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        ev = os.path.join(td, "out", "x")
        os.makedirs(ev)
        open(os.path.join(ev, "a.md"), "w").write("content")

        def g_pass(prompt, seat):
            return '前言 {"vote":"PASS","items":[{"n":1,"r":"PASS","why":"ok"}],"reason":"合规"}'

        def g_block(prompt, seat):
            return '{"vote":"BLOCK","reason":"缺家长键"}'

        def g_junk(prompt, seat):
            return "我觉得还行"

        r = review(task_type="T-3D-ADAPT", evidence=[ev], generate=g_pass)
        chk("全员 PASS -> PASS", r["verdict"] == "PASS")
        chk("否决项全过时不拦", not r.get("veto") or all(v["pass"] for v in r["veto"]))

    r = review(task_type="T-3D-ADAPT", evidence=["out/none"], generate=g_pass, root=False)
    chk("产物缺失 -> BLOCK 且不进投票", r["verdict"] == "BLOCK" and r["votes"] == [])

    r = review(task_type="T-3D-ADAPT", evidence=["Tools/fleet/panel_review.py"],
               generate=g_block, root=False)
    chk("有 BLOCK 票 -> REVISE", r["verdict"] == "REVISE" and "家长键" in r["why"])

    r = review(task_type="T-3D-ADAPT", evidence=["Tools/fleet/panel_review.py"],
               generate=g_junk, root=False)
    chk("模型答偏 -> ABSTAIN 不算通过", r["verdict"] == "REVISE" and
        all(v["vote"] == "ABSTAIN" for v in r["votes"]))

    r = review(task_type="T-NOT-EXIST", evidence=["x"], generate=g_pass, root=False)
    chk("没有评审团 -> BLOCK（不许默认通过）", r["verdict"] == "BLOCK")

    # 单席 quorum=1 的合规面板：模型不可用必须 ABSTAIN 而不是 PASS
    r = review(task_type="T-TEXT-COMPLIANCE", evidence=["Tools/fleet/panel_review.py"],
               generate=g_junk, root=False)
    chk("合规面板 quorum=1 也不会被答偏蒙过", r["verdict"] == "REVISE")

    chk("面板覆盖主要任务类型（>=30）", len(panels()) >= 30)
    # 位置偏差：顺序敏感必须判出来；顺序无关必须通过（ChatEval/MAD 的 position-bias 前置检验）
    # 证据用真实存在的文件（vetoes 会先查存在性，虚构路径会一律 BLOCK 而测不到投票面）
    EV3 = ["Tools/fleet/panel_review.py", "Tools/fleet/station_drive.py", "Tools/fleet/agent_team.py"]

    def g_flip(p, seat):
        ia, ib = p.find("panel_review.py"), p.find("station_drive.py")
        first = ia != -1 and (ib == -1 or ia < ib)
        return ('{"vote":"PASS","reason":"ok"}' if first
                else '{"vote":"BLOCK","reason":"顺序变了就翻"}')

    def g_stable(p, seat):
        return '{"vote":"PASS","reason":"ok"}'

    uv = order_invariance(task_type="T-3D-ADAPT", evidence=EV3, generate=g_flip, runs=3)
    chk("顺序敏感 -> stable=False（不许放行）", uv["stable"] is False)
    st = order_invariance(task_type="T-3D-ADAPT", evidence=EV3, generate=g_stable, runs=3)
    chk("顺序无关 -> stable=True", st["stable"] is True)

    print("[panel_review] %d/%d" % (ok, total))
    return 0 if ok == total else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product")
    ap.add_argument("--stage")
    ap.add_argument("--task-type")
    ap.add_argument("--evidence", nargs="*", default=[])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check-order", action="store_true",
                    help="位置偏差检验：同一批证据换顺序，判决必须一致")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.list:
        for tid, p in sorted(panels().items()):
            print("%-22s skill=%-18s seats=%s quorum=%s" % (
                tid, p.get("skill"), ",".join(p.get("seats") or []), p.get("quorum")))
        return 0
    if a.check_order:
        r = order_invariance(a.product, a.stage, a.task_type, a.evidence)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["stable"] else 1
    r = review(a.product, a.stage, a.task_type, a.evidence)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return {"PASS": 0, "REVISE": 1, "BLOCK": 2}.get(r["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
