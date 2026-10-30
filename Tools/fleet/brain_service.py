# -*- coding: utf-8 -*-
"""brain_service.py - bm-m as the fleet's SECOND BRAIN (CEO 2026-10-30 令).

Master was already dispatch + judgment seat. This adds the production leg: every
business line gets one concrete text deliverable per workday, written by the resident
model (qwen3:4b-instruct by default; 2026-10-30 bench on this 32GB M1 Pro: 4B 8k=3.3GB/
41.6 tok/s vs 35B-A3B 22.0GB/29-40 tok/s with 14-21s cold load) from REAL repo documents
(origin_blob reads git, so sparse checkout is no barrier), committed to queue-receipts/,
and announced in the daily bulletin that lanes pull.

Cost design: one line per tick (7 lines -> full sweep ~7 min at 60s ticks), each call
<=90s, so the control loop never starves. Zero cloud tokens -- local brain only.
Anti-hallucination (D-20261030-01 lesson): the prompt forbids inventing names/paths/
numbers; everything must trace to the excerpt handed to it.
"""
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_lane as fl

STATE_REL = "cph4/fleet/dispatcher/brain-state.json"
BULLETIN_REL = "cph4/fleet/inbox/BRAIN-BULLETIN.md"
RECEIPT_DIR = "cph4/fleet/queue-receipts"
PER_DAY = 1          # per line
WORKERS = 3          # parallel lines per tick (4B handles 3 concurrent calls at full speed)
CALL_TIMEOUT = 90

TASKS = {
    "bigstream-mv": ("cph4/fleet/mv0001-handover/canon", "给导演席的《爱在西元前》签核推进简报：①机器闸已证到什么 ②人工四项各查什么、怎么看证据 ③今天最该先拍的板是哪一项，为什么。"),
    "bigstream-duanju": ("cph4/fleet/drama-dept-v1", "短剧线日报：从台账里找出「素材在盘但工序没接上」的缺口清单（按损失大小排序），每条一句行动建议。"),
    "bigstream-drama": ("cph4/fleet/drama-dept-v1", "漫剧线解堵方案：只引用文档里真实存在的工具与路径，给出下一步三个动作（谁做、做什么、验收物）。禁止臆造命令。"),
    "voicebank": ("Tools/voicebank", "音色库建设推进：依据 VOICE-BANK-PLAN.md 的出厂闸与产能数据，产出今日可执行推进清单（含 60 席矩阵进度判断），并列出只有 CEO 能定的决策点。"),
    "recon": ("cph4/research", "竞品拆解晨报：从调研档案挑一条对 BigStream 本周生产最有用的结论，说明怎么用在哪道工序。"),
    "fleet-ops": ("cph4/fleet/dispatcher", "机队运行周报素材：汇总满负荷规则执行情况，指出机制仍可能空转的一个死角及补法。"),
}


def _state(root):
    return fl.read_json(os.path.join(root, STATE_REL.replace("/", os.sep)), {}) or {}


def _save_state(root, st):
    fl.write_json(os.path.join(root, STATE_REL.replace("/", os.sep)), st)


def _today():
    return time.strftime("%Y-%m-%d")


def _resolve_src(root, src):
    """src is an exact repo path on origin/main (sparse checkout irrelevant — 2026-10-30
    first run died because short names like 'mv0001-handover/canon' matched nothing)."""
    c = (src or "").strip("/")
    if not c:
        return []
    r = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", "origin/main", c],
                       capture_output=True, text=True, timeout=30)
    return [f for f in r.stdout.splitlines() if f.endswith((".md", ".json", ".txt"))]


def _excerpt(root, src, chars=3500):
    """Real bytes from origin/main (sparse checkout proof -- local existence is NOT used
    for selection, 2026-10-30: first brain run died on exactly that)."""
    try:
        files = _resolve_src(root, src)
        if not files:
            return ""
        # freshest canon first: prefer receipt/state/daily-looking names, then path order
        prio = ("RECEIPT", "STATE", "LOG", "PLAN", "SPEC", "LEDGER", "REPORT")
        def key(f):
            up = f.upper()
            p = next((i for i, w in enumerate(prio) if w in up), len(prio))
            return (p, f)
        def _date(f):
            import re as _re
            m = _re.findall(r"(20\d{6})", f.upper())
            return max(m) if m else "00000000"
        files.sort(key=lambda f: (-int(_date(f)), key(f)))
        parts = []
        for f in files[:4]:
            blob = fl.origin_blob(root, f) or ""
            if blob:
                parts.append("### 文件：%s\n%s" % (f, blob[:1400]))
        return "\n\n".join(parts)[:chars]
    except Exception:
        return ""


def produce(root, line, task, src):
    ex = _excerpt(root, src)
    if not ex:
        return None, "no-excerpt"
    allowed = set(re.findall(r"[A-Za-z0-9_./-]+\.(?:md|json|py|txt)", ex))
    prompt = ("你是 FluxGroup 机队的副大脑 bm-m（本地判读席）。只依据下面给出的仓库摘录写作，"
              "严禁编造文件名、人名、数字、路径；正文中出现的每个文件名都必须逐字来自摘录清单："
              "%s。证据不足就写『需补充：…』。\n任务：%s\n"
              "格式：Markdown，标题用今天日期，<=350字，最后一段是【给谁·下一步】。\n\n"
              "=== 仓库摘录 ===\n%s") % (sorted(allowed)[:40], task, ex)
    ans = fl.local_llm(prompt, node="bm-m", timeout=CALL_TIMEOUT)
    if not ans:
        return None, "llm-fail"
    # citation gate: any referenced .md/.json/.py/.txt that is not in the excerpt set
    cited = set(re.findall(r"`?([A-Za-z0-9_./-]+\.(?:md|json|py|txt))`?", ans))
    ghost = {c for c in cited
             if not any(c == a or c in a or a.endswith(c) for a in allowed)}
    if ghost:
        ans += "\n\n> ⚠️ 引用核验未过（主控已标记，请勿据此行动）：%s" % ", ".join(sorted(ghost))
    safe = re.sub(r"[^a-z0-9-]", "-", line)
    path = os.path.join(root, RECEIPT_DIR, "brain-%s-%s.md" % (safe, _today()))
    model_used = (fl.LANES.get("bm-m", {}).get("llm") or {}).get("model") or "local"
    with open(path, "w", encoding="utf-8") as f:
        f.write(ans.strip() + "\n\n---\n*副大脑 bm-m · %s 本地产出 · 依据仓库摘录*\n" % model_used)
    return path, "ok"


def main():
    root = fl.ROOT_DEFAULT
    st = _state(root)
    if st.get("date") != _today():
        st = {"date": _today(), "done": {}}
    todo = [(l, t, s) for l, (s, t) in TASKS.items()
            if int(st["done"].get(l, 0)) < PER_DAY]
    if not todo:
        print("[brain] all %d lines served today" % len(TASKS))
        return 0
    # 2026-10-31: one line per tick left 6 of 7 lines waiting ~30 min behind a model that
    # already answers 3 calls in parallel at full speed. Batch them; results are collected
    # and written serially, so the state file and bulletin keep a single writer.
    batch = todo[:WORKERS]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(lambda x: produce(root, x[0], x[1], x[2]), batch))
    served = 0
    for (line, _t, _s), (path, note) in zip(batch, results):
        st["done"][line] = int(st["done"].get(line, 0)) + (1 if path else 0)
        if not path:
            st.setdefault("fail", {})[line] = note
            continue
        served += 1
        _bulletin(root, line, path)
        print("[brain] %s -> %s (%s)" % (line, os.path.basename(path), note))
    _save_state(root, st)
    if not served:
        print("[brain] batch produced nothing (%d tried)" % len(batch))
    return 0


def _bulletin(root, line, path):
    """Lanes pull repo files <=256KB via FleetLink /sync -> announce there."""
    bp = os.path.join(root, BULLETIN_REL.replace("/", os.sep))
    rel = os.path.relpath(path, root)
    head = ""
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                if ln.startswith("#"):
                    head = ln.strip(); break
    except Exception:
        pass
    entry = "- **%s** %s → [%s](/%s)\n" % (_today(), head or line, os.path.basename(path), rel)
    old = ""
    if os.path.exists(bp):
        with open(bp, encoding="utf-8") as f:
            old = f.read()
    os.makedirs(os.path.dirname(bp), exist_ok=True)
    if entry.strip() not in old:
        with open(bp, "w", encoding="utf-8") as f:
            f.write("# 副大脑公告栏（bm-m 本地判读席每日产出·车道自动同步）\n\n" + entry + old)


if __name__ == "__main__":
    sys.exit(main())
