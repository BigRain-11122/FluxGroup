#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能成对评测：同一批问题，挂技能 vs 不挂技能，比命中率。

为什么必须这样做（2026-11 综述 SkillDelta 结论）：
  "相关 ≠ 有用"。结构合规只能证明格式对，证明不了它真的改变行为；
  唯一可用的证据是 with/without 成对对照。

数据：cph4/skills/<name>/eval.json
  {"model":"qwen3:4b-instruct","tasks":[{"q":"...","must":["必须出现的词1","词2"]}]}

判分：每个任务命中 must 的比例；聚合 = 均值。delta = with - without（同模型同温度）。

用法：
  python3 Tools/fleet/skill_eval.py --skill fleet-ops
  python3 Tools/fleet/skill_eval.py --skill ship-ops --json-out cph4/fleet/queue-receipts/skill-eval-ship-ops-20261103.json
"""

import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = "qwen3:4b-instruct"


def chat(model, system, user, timeout=180, num_predict=160):
    body = {
        "model": model,
        "prompt": user,
        "system": system,
        "stream": False,
        "options": {"temperature": 0, "num_predict": num_predict, "num_ctx": 8192},
    }
    req = urllib.request.Request(
        OLLAMA + "/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "")


def score(text, must):
    hit = [m for m in must if m in text]
    return len(hit) / float(len(must)), hit


def load_skill(name):
    p = os.path.join(ROOT, "cph4", "skills", name, "SKILL.md")
    if not os.path.isfile(p):
        raise SystemExit("no such skill: %s" % name)
    text = open(p, encoding="utf-8").read()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        text = text[end + 4:] if end > 0 else text
    return text.strip()


def main(argv):
    if "--skill" not in argv:
        print(__doc__)
        return 2
    name = argv[argv.index("--skill") + 1]
    spec_path = os.path.join(ROOT, "cph4", "skills", name, "eval.json")
    if not os.path.isfile(spec_path):
        raise SystemExit("no eval.json for %s（先写 6 道有判据的题）" % name)
    spec = json.load(open(spec_path, encoding="utf-8"))
    model = spec.get("model", DEFAULT_MODEL)
    tasks = spec["tasks"]
    body = load_skill(name)
    system_with = ("你正在执行 FluxGroup 集团任务。以下是你这个席位的技能手册，"
                   "严格按它回答，不要发明手册里没有的做法。\n\n" + body[:6000])
    system_without = "你正在执行 FluxGroup 集团任务。直接回答问题，简短。"
    rows = []
    t0 = time.time()
    for i, t in enumerate(tasks, 1):
        a_with = chat(model, system_with, t["q"])
        b_without = chat(model, system_without, t["q"])
        sw, hw = score(a_with, t["must"])
        so, ho = score(b_without, t["must"])
        rows.append({"q": t["q"], "must": t["must"], "with": round(sw, 3), "without": round(so, 3),
                     "hit_with": hw, "hit_without": ho,
                     "ans_with": a_with.strip()[:300], "ans_without": b_without.strip()[:300]})
        print("  [%d/%d] with=%.2f without=%.2f  %s" % (i, len(tasks), sw, so, t["q"][:34]))
    n = len(rows)
    m_with = sum(r["with"] for r in rows) / n
    m_without = sum(r["without"] for r in rows) / n
    wins = sum(1 for r in rows if r["with"] > r["without"])
    losses = sum(1 for r in rows if r["with"] < r["without"])
    out = {"skill": name, "model": model, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "n": n, "with": round(m_with, 3), "without": round(m_without, 3),
           "delta": round(m_with - m_without, 3), "wins": wins, "losses": losses,
           "seconds": round(time.time() - t0, 1), "rows": rows}
    print("RESULT %s  with=%.3f without=%.3f delta=%+.3f  win/loss=%d/%d  %.0fs"
          % (name, m_with, m_without, m_with - m_without, wins, losses, out["seconds"]))
    if "--json-out" in argv:
        p = argv[argv.index("--json-out") + 1]
        os.makedirs(os.path.dirname(os.path.join(ROOT, p)) or ".", exist_ok=True)
        with open(os.path.join(ROOT, p), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("wrote", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))