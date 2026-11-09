# -*- coding: utf-8 -*-
"""local_judge.py - answer the smart-tier judgment queue, and escalate what is beyond it.

CEO 2026-11-01: 「你做的事情不要超过你的能力，要上云还是上云，不要频繁触发硬盘交换，合理使用
你 macbook 的算力」。So this seat is two-staged, not one:
  1. the local 4B answers when the question is a routing/attribution call it can ground in
     the given evidence (measured 3.5s, 3.3GB, no swap);
  2. when its own answer says it cannot decide (需要人工/证据不足), or the call is a real
     judgment (取舍/方向/仲裁), the row is marked ESCALATED and handed to the cloud seat
     instead of being answered by a model that has no business answering it.
The 35B-A3B is never loaded here: 21.9GB on a 32GB box that is already swapping.

Answer/model fields are written either way, so the audit trail shows which brain spoke.
D-20261030-01 lesson stays: the prompt forbids inventing tools or paths.
"""
import json
from concurrent.futures import ThreadPoolExecutor
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_lane as fl

MAX_PER_CYCLE = 4   # 4B ~3.5s/judgment on the real queue -> fits the 60s tick with margin

JUDGE_MODEL = (fl.LANES.get("bm-m", {}).get("llm") or {}).get("model") or "qwen3:4b-instruct"

PROMPT = """你是机队主控的本地判断席（只依据给定证据回答，严禁编造不存在的工具、命令或路径；证据不足就回答"需要人工裁决+原因"）。
问题：{question}
背景证据：{evidence}
业务约束：算力分层=本地优先；本地判不了的上云（单次≤50积分、当日≤200）；主控机只做调度与文本、云端不用于确定性脚本。
请用不超过 80 字给出下一步动作（谁、做什么），格式："动作｜理由"。判不了就只回"需要人工裁决"。"""

ESCALATE_MARKERS = ("需要人工", "证据不足", "无法判断", "不能确定", "需人工")


def brain_seat(root):
    """Return the judgment seat to use first: the server brain when it is live, else local.

    CEO 2026-11-01: 主控是大脑，但后面还有真正的算力服务器大脑介入. The seat is therefore
    declarative (cph4/fleet/BRAIN-SEAT.json): flip tiers[server].state to ACTIVE and fill its
    endpoint/model, and this leg moves heavy judgment to bm-d without a code change. Until
    then it stays on the 4B - which is honest about what a 32GB laptop can judge.
    """
    path = os.path.join(root, "cph4", "fleet", "BRAIN-SEAT.json")
    try:
        with open(path, encoding="utf-8") as f:
            seat = json.load(f)
    except Exception:
        return ("bm-m", "")
    for t in seat.get("tiers") or []:
        if str(t.get("state") or "").upper() != "ACTIVE":
            continue
        # A tested upgrade seat (e.g. 8B judge) wins over the fast 4B seat.
        jc = t.get("judge_candidate") or {}
        if str(jc.get("state") or "").upper() == "ACTIVE" and jc.get("model"):
            return (t.get("node") or "bm-m", jc["model"])
        if t.get("id") == "server" and t.get("endpoint") and t.get("model"):
            return (t.get("node") or "bm-d", t.get("model") or "")
    return ("bm-m", "")


def needs_cloud(answer: str) -> bool:
    a = str(answer or "")
    return (not a.strip()) or any(m in a for m in ESCALATE_MARKERS)


# ---- 超时自动保守裁决（2026-11-02 换挡）
# 实测 43 条判定里委员会真裁决 0 次，全被机制或本地模型消化——"等 24h 人判"这一层
# 必须能被机器兜住：超 SLA 就按最保守的默认动作结案，留理由与依据，不让人成为堵点。
SLA_H = 24
DEFAULT_DECISIONS = {
    "CAPACITY": ("不动作",
                 "资源类默认不动作：盲杀会打断生产；跌破内存地板就暂停该卡等夜窗，不杀进程"),
    "LINE-LATE": ("机制优先",
                  "线级迟到先走 LINE-NEXT-STEPS + night_plan 派卡；机制仍有效时不另裁决"),
    "LINE-STALE": ("机制优先",
                   "同上；再过一个窗口仍无产物，由 chief 停线并写明 kill 理由"),
    "LINE-BLOCKED": ("换车道",
                     "按 LANES 能力表改派能跑的机器；没有任何车道能跑就拆活或降级，不挂着等"),
    "RETRY": ("重试一次",
              "同一张卡最多重试一次；再失败标 FAILED 并带原因，不无限重排"),
}


def _age_h(ts):
    from datetime import datetime
    try:
        s = str(ts).replace("Z", "")
        t = datetime.fromisoformat(s)
        now = datetime.now(t.tzinfo) if t.tzinfo else datetime.now()
        return (now - t).total_seconds() / 3600.0
    except Exception:
        return None


def autodecide(rows):
    """把超过 SLA 仍 OPEN 的判定按默认动作结案，返回结案条数。"""
    n = 0
    for r in rows:
        if r.get("state") != "OPEN":
            continue
        age = _age_h(r.get("ts"))
        if age is None or age < SLA_H:
            continue
        act, why = DEFAULT_DECISIONS.get(r.get("kind") or "", ("不动作", "未知题型默认不动作，仅记录"))
        r["state"] = "ANSWERED"
        r["answer"] = "【机器默认裁决·超%dh】%s：%s" % (SLA_H, act, why)
        r["model"] = "policy:autodecide-sla%d" % SLA_H
        r["answered_at"] = fl.now_iso()
        r["autodecided"] = True
        n += 1
    return n


def try_8b(prompt):
    """4B 说判不了时，先用 8B 单槽再试一次，仍不行才上云。
    8B 车道有人（DSH）就跳过，绝不抢。"""
    import urllib.request, json as _j
    base = os.environ.get("AGENT_LANE", "http://127.0.0.1:11436")
    try:
        ps = _j.loads(urllib.request.urlopen(base + "/api/ps", timeout=3).read())
        if ps.get("models"):
            return ""
        body = {"model": os.environ.get("JUDGE_8B", "qwen3:8b-dsh32k"),
                "messages": [{"role": "user", "content": prompt}],
                "think": False, "stream": False, "keep_alive": "3m",
                "options": {"num_ctx": 8192, "num_predict": 160, "temperature": 0.1}}
        req = urllib.request.Request(base + "/api/chat", data=_j.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            return ((_j.loads(r.read()).get("message") or {}).get("content") or "").strip()
    except Exception:
        return ""


def main():
    root = fl.ROOT_DEFAULT
    seat_node, seat_model = brain_seat(root)
    if seat_model:
        # fl.local_llm picks the lane's configured model; a bench-approved seat overrides it.
        fl.LANES.setdefault(seat_node, {}).setdefault("llm", {})["model"] = seat_model
    path = os.path.join(root, fl.JUDGMENT_REL.replace("/", os.sep))
    rows = fl.read_jsonl(path)
    auto = autodecide(rows)          # 先让超时项按默认动作结案，再让模型处理新的
    # 路由 v2（2026-11-05）：这几类题型已有规则裁决（decision_close 跑在本阶段之前），
    # 再让 4B 跑一遍只是浪费一轮——实测这类题在 4B 上几乎全 escalate，且缺料归因 3/3 判错。
    RULE_KINDS = {"LINE-LATE", "LINE-STALE", "LINE-BLOCKED", "CAPACITY", "RETRY"}
    todo = [r for r in rows if r.get("state") == "OPEN"
            and str(r.get("kind") or "").upper() not in RULE_KINDS][:MAX_PER_CYCLE]
    # Parallel on purpose: 2026-10-31 measured 3 concurrent 4B calls at ~41 tok/s each with
    # no extra memory, so serialising judgments burns wall-clock for nothing.
    prompts = [PROMPT.format(question=r.get("question", ""),
                             evidence=json.dumps(r.get("evidence") or {}, ensure_ascii=False)[:1200])
               for r in todo]
    with ThreadPoolExecutor(max_workers=MAX_PER_CYCLE) as ex:
        answers = list(ex.map(lambda p: fl.local_llm(p, node=seat_node, timeout=90), prompts))
    n = 0
    esc = 0
    for r, ans, qtext in zip(todo, answers, prompts):
        if not ans or not str(ans).strip():
            r["note"] = "local-judge failed this round (ollama down?)"
            continue
        text = str(ans).strip()[:500]
        r["answer"] = text
        r["model"] = ("local:%s" % seat_model) if seat_node=="bm-m" else ("seat:%s" % seat_node)
        r["answered_at"] = fl.now_iso()
        if needs_cloud(text):
            # 2026-11-09：4B 判不了先让 8B 试（本地第二档），仍不行才上云。
            ans8 = try_8b(qtext)
            if ans8 and not needs_cloud(ans8):
                r["answer"] = ans8[:500]
                r["model"] = "local:8B"
                r["answered_at"] = fl.now_iso()
                r["state"] = "ANSWERED"
                n += 1
                continue
            # Beyond the 4B's ability: keep it OPEN for the cloud seat instead of letting
            # a weak model close a real judgment. Wasted local rounds are cheap; a wrong
            # verdict from a 4B is not.
            r["state"] = "ESCALATED"
            r["escalate_to"] = "cloud-smart"
            r["escalate_why"] = "local 4B said it cannot decide: %s" % text[:80]
            esc += 1
        else:
            r["state"] = "ANSWERED"
            n += 1
    if n or esc or auto:
        fl.write_jsonl(path, rows)
    open_count = sum(1 for r in rows if r.get("state") == "OPEN")
    esc_count = sum(1 for r in rows if r.get("state") == "ESCALATED")
    print("[local_judge] seat=%s answered=%d autodecided=%d escalated=%d(cloud-smart) still_open=%d"
          % (seat_node, n, auto, esc, open_count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
