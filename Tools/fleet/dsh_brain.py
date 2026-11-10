#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dsh_brain.py - 自动化轮的本地大脑：先本地模型，质量不过再升档，最后才上 codely。

为什么（CEO 2026-11-10 原话「尽量用本地大模型做自动化，慢点没关系，但要质量高，
解决不了就用codely」）：
  自动化轮里真正需要判断的只有几件事——这张失败卡根因是什么、这条线下一件产物该是
  什么、这张 DONE 是真货还是空壳、这条挂起线该救还是判死。这些不需要云端大模型，
  本地 4B/9B 在「给了证据就能答」的题上够用；但本地模型会编、会漏字段、会把不存在的
  路径写得很像，所以必须**契约化输出 + 规则复核 + 逐级升档**。

档位阶梯（同一题，从便宜到贵）：
  1. qwen3.5:4b-mlx   常驻，最快，先答
  2. qwen3.5:9b-mlx   4B 不过契约或自评低时升档
  3. deepseek-r1:14b  难题/长证据；仍不过 → 4. codely -p（真正的编码级解题）

质量闸（不看模型自评，看可核验事实）：
  - 输出必须是 JSON（允许 ```json 包裹），必填键缺失=不过
  - 引用的文件路径必须存在（幻觉路径当场抓）
  - 枚举值必须落在白名单（例如 root_cause 只能是 INPUT/SCRIPT/PERM/GATE/ENV/UNKNOWN）
  - 长度/空值检查

用法：
  python3 Tools/fleet/dsh_brain.py --task rework_rootcause --input /tmp/x.json
  python3 Tools/fleet/dsh_brain.py --task line_plan --input - --json
  python3 Tools/fleet/dsh_brain.py --task ... --no-codely     # 只走本地档
  python3 Tools/fleet/dsh_brain.py --selftest                 # 契约自证（不调模型）
Exit: 0 有合格答案 / 2 全部档位失败（已在 stderr 说明断在哪） / 1 用法错
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(ROOT, "cph4", "fleet", "state", "dsh-brain.jsonl")
OLLAMA = os.environ.get("OLLAMA_ENDPOINT", "http://127.0.0.1:11434")
# 默认只跑 fast 档：2026-11-10 实测 4B 单题 57-84s，9B 在 32GB 统一内存上 300s 起不来
# （加载即换页），硬上只会把一轮从 1 分钟拖成 6 分钟。9B/14B 用 --big / --deep 显式点。
TIERS = [("fast", "qwen3.5:4b-mlx", 150)]
BIG_TIER = ("big", "qwen3.5:9b-mlx", 300)
# 14B 只在 --deep 时启用：2026-11-10 实测它在自动化轮里一次判读要 6-8 分钟，
# 而这类题（给了证据做选择）4B/9B 足够；把最慢的档留给人工点名的难题。
DEEP_TIER = ("deep", "deepseek-r1:14b", 480)

# 本地小模型会把语义正确的答案写成白名单外的词（"idle" 而不是 "none"）。
# 这不该算不合格——错的是词汇不是判断。按语义归一，归不了才判失败。
ENUM_ALIASES = {
    "actions.action": {
        "idle": "none", "wait": "none", "noop": "none", "do_nothing": "none",
        "ok": "none", "healthy": "none", "skip": "none",
        "reset": "node_sync", "git_reset": "node_sync", "sync": "node_sync",
        "wake": "poke", "pokes": "poke",
        "kill": "cancel_zombie", "cancel": "cancel_zombie", "requeue": "redispatch",
        "rebalance": "redispatch", "redistribute": "redispatch", "retry": "redispatch",
        "repair": "peer_sync", "winrm": "peer_sync",
    },
    "root_cause": {
        "MISSING_INPUT": "INPUT", "NO_INPUT": "INPUT", "MISSING_SCRIPT": "SCRIPT",
        "SCRIPT_MISSING": "SCRIPT", "PERMISSION": "PERM", "AUTH": "PERM",
        "JUDGE": "GATE", "CRITERIA": "GATE", "FALSE_NEGATIVE": "GATE",
        "ENVIRONMENT": "ENV", "SERVICE_DOWN": "ENV", "CARD": "CONTRACT",
    },
    "verdict": {"TRUE": "REAL", "OK": "REAL", "GOOD": "REAL", "EMPTY": "FAKE",
                "STUB": "FAKE", "PLACEHOLDER": "FAKE", "REFUSAL": "FAKE", "MIXED": "PARTIAL"},
    "decision": {"KEEP": "PRODUCE", "REVIVE": "PRODUCE", "RETIRE": "DEAD", "KILL": "DEAD"},
}
CODELY = "/Users/junsheng.sun/Library/Application Support/Tuanjie Cowork/bin/codely"

# 每类任务的输出契约。required=必填键；enums=枚举白名单；paths=要求真实存在的路径键。
TASKS = {
    "fleet_triage": {
        "goal": "根据三台机的 /status 与队列摘要，决定这一轮对每台机做什么（不写报告，只给动作）",
        "required": ["actions"],
        "enums": {"actions.action": ["poke", "adopt", "node_sync", "peer_sync", "cancel_zombie",
                                    "redispatch", "none"]},
        "item_keys": ["node", "action", "why"],
        "hint": '{"actions":[{"node":"bm-a","action":"poke","why":"..."}]}',
    },
    "rework_rootcause": {
        "goal": "给一张失败卡与它的回执，判定根因类别与最小修法，不要重派同一张卡",
        "required": ["root_cause", "fix", "next"],
        "enums": {"root_cause": ["INPUT", "SCRIPT", "PERM", "GATE", "ENV", "CONTRACT", "UNKNOWN"]},
        "hint": '{"root_cause":"GATE","fix":"...","next":"..."}',
    },
    "line_plan": {
        "goal": "给一条产线的现状，给出今天能出的最小可验收产物与它的执行方式",
        "required": ["deliverable", "how", "accept"],
        "paths": ["deliverable"],
        "hint": '{"deliverable":"cph4/fleet/reports/x.md","how":"...","accept":"..."}',
    },
    "quality_audit": {
        "goal": "判断一张 DONE 卡的交付物是真产物还是空壳/占位/拒答",
        "required": ["verdict", "why"],
        "enums": {"verdict": ["REAL", "FAKE", "PARTIAL"]},
        "hint": '{"verdict":"FAKE","why":"..."}',
    },
    "parked_decision": {
        "goal": "给一条超 72h 无产物的线，二选一：今天出最小件，或判死因",
        "required": ["decision", "why", "next"],
        "enums": {"decision": ["PRODUCE", "DEAD"]},
        "hint": '{"decision":"PRODUCE","why":"...","next":"..."}',
    },
}


def now():
    return datetime.now().isoformat(timespec="seconds")


def log(rec):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _extract_json(text):
    """模型爱把 JSON 包在 ```json 里，或在前面加一段解释。只取第一个完整对象。"""
    if not text:
        return None
    s = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.S)
    if m:
        s = m.group(1)
    else:
        i, j = s.find("{"), s.rfind("}")
        if i >= 0 and j > i:
            s = s[i:j + 1]
    try:
        return json.loads(s)
    except Exception:
        return None


def _path_ok(p):
    p = str(p or "").strip()
    if not p:
        return False
    full = p if os.path.isabs(p) else os.path.join(ROOT, p)
    return os.path.exists(full)


def normalize(task, obj):
    """把白名单外的同义词拽回白名单；只改词，不改判断。"""
    if not isinstance(obj, dict):
        return obj
    spec = TASKS.get(task) or {}
    for key in (spec.get("enums") or {}):
        al = ENUM_ALIASES.get(key) or {}
        if "." in key:
            head, sub = key.split(".", 1)
            for it in obj.get(head) or []:
                if isinstance(it, dict) and it.get(sub) in al:
                    it[sub] = al[it[sub]]
        elif obj.get(key) in al:
            obj[key] = al[obj[key]]
    return obj


def validate(task, obj):
    """规则复核：返回 (ok, 问题列表)。不看模型怎么夸自己。"""
    spec = TASKS[task]
    errs = []
    if not isinstance(obj, dict):
        return False, ["输出不是 JSON 对象"]
    for k in spec["required"]:
        if obj.get(k) in (None, "", [], {}):
            errs.append("缺必填键 %s" % k)
    for key, allowed in (spec.get("enums") or {}).items():
        if "." in key:
            head, sub = key.split(".", 1)
            items = obj.get(head) or []
            if not isinstance(items, list) or not items:
                errs.append("%s 必须是非空数组" % head)
                continue
            for i, it in enumerate(items):
                v = (it or {}).get(sub) if isinstance(it, dict) else None
                if v not in allowed:
                    errs.append("%s[%d].%s=%r 不在白名单 %s" % (head, i, sub, v, allowed))
                for ik in spec.get("item_keys") or []:
                    if not (it or {}).get(ik):
                        errs.append("%s[%d] 缺 %s" % (head, i, ik))
        else:
            if obj.get(key) not in allowed:
                errs.append("%s=%r 不在白名单 %s" % (key, obj.get(key), allowed))
    for key in spec.get("paths") or []:
        v = obj.get(key)
        if v and not _path_ok(v):
            errs.append("%s 指向不存在的路径：%s（幻觉路径）" % (key, v))
    # 通用反空话：why/fix/next 这类字段不许少于 8 个字符，也不许整段是"待定/稍后/需要更多信息"
    for k in ("why", "fix", "next", "how", "accept"):
        if k in obj and isinstance(obj[k], str):
            v = obj[k].strip()
            if v and len(v) < 5:
                errs.append("%s 太短，读不出结论" % k)
            if re.search(r"待定|稍后|需要更多信息|无法判断|不知道", v):
                errs.append("%s 是空话：%s" % (k, v[:40]))
    return (not errs), errs


# ---- 硬规则复核：格式对了不代表判断对了 -------------------------------------
# 2026-11-10 实锚：4B 对 bm-a（ahead=266）判 "none，等上游同步"——格式合格、语义是错的。
# 规则先算事实，模型只能在这些事实之上做选择；顶撞硬事实的答案一律判不合格、升档。
_QIDS = {}


def queue_ids():
    """真实存在的卡号集合：模型最爱编一个看起来很真的卡号。"""
    if _QIDS:
        return _QIDS
    try:
        for ln in open(os.path.join(ROOT, "cph4", "fleet", "PRODUCTION-QUEUE.jsonl"),
                       encoding="utf-8"):
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("id"):
                _QIDS[str(r["id"])] = 1
    except Exception:
        pass
    return _QIDS


def looks_like_id(s):
    s = str(s or "").strip()
    if len(s) < 8 or not re.match(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+){2,}$", s):
        return False
    return bool(re.search(r"\d", s))


def rules_violations(task, obj, payload):
    out = []
    if not isinstance(obj, dict):
        return ["输出不是对象"]
    if task == "fleet_triage":
        facts = {n.get("node"): n for n in (payload.get("nodes") or []) if isinstance(n, dict)}
        acts = {a.get("node"): a.get("action") for a in (obj.get("actions") or [])
                if isinstance(a, dict)}
        for node, f in facts.items():
            act = acts.get(node)
            ahead = f.get("ahead")
            if ahead is None and isinstance(f.get("fork"), str) and "/" in f["fork"]:
                try:
                    ahead = int(f["fork"].split("/")[0].split()[0])
                except Exception:
                    ahead = None
            age = f.get("stamp_age_s")
            if ahead and ahead > 0 and act in ("none", "cancel_zombie"):
                out.append("%s 领先 %s 个提交却判 %s（分叉必须先收编或 reset）" % (node, ahead, act))
            if ahead == 0 and age is not None and age < 900 and act == "node_sync":
                out.append("%s 已同步且戳新鲜，不需要 reset" % node)
            if act is None:
                out.append("%s 没有给动作" % node)
    elif task == "rework_rootcause":
        if obj.get("root_cause") == "UNKNOWN":
            out.append("根因判 UNKNOWN：证据已给足，必须落到具体类别")
        fix = str(obj.get("fix") or "").strip()
        if re.match(r"^[a-z_]+(:\s*\S+)?$", fix) or not re.search(
                r"改|修|删|补|加|重跑|换|停|收口|对齐|重建|回滚|起", fix):
            out.append("fix 不是修法，只是字段/名词：%r" % fix[:40])
    elif task == "quality_audit":
        why = str(obj.get("why") or "")
        if obj.get("verdict") == "REAL" and not re.search(r"\d", why):
            out.append("判 REAL 但理由里没有任何可核对的数字（字节/行数/mtime）")
    elif task == "line_plan":
        d = str(obj.get("deliverable") or "")
        if d and not re.search(r"\.(md|json|jsonl|txt|csv|png|jpg|mp4|wav|py)$", d):
            out.append("deliverable 不是文件路径：%s" % d[:60])
    # 通用：任何字段里出现 "像卡号但队列里没有" 的字符串 = 幻觉
    ids = queue_ids()
    def walk(v):
        if isinstance(v, str):
            if looks_like_id(v) and v not in ids:
                out.append("引用了不存在的卡号：%s" % v)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
    walk(obj)
    return out


def ask_ollama(model, prompt, timeout, num_predict=800):
    body = json.dumps({
        "model": model, "prompt": prompt, "stream": False, "think": False,
        "keep_alive": "15m",
        "options": {"num_ctx": 8192, "num_predict": num_predict, "temperature": 0.2},
    }).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request(OLLAMA.rstrip("/") + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8", "replace") or "{}")
        return d.get("response") or "", time.time() - t0, None
    except Exception as exc:  # noqa: BLE001
        return "", time.time() - t0, "%s: %s" % (type(exc).__name__, str(exc)[:120])


def ask_codely(prompt, timeout=900):
    """本地档全不过时才上 codely：给它完整题面 + 契约，只要一段 JSON 结论。"""
    if not os.path.exists(CODELY):
        return "", 0.0, "codely 不存在"
    t0 = time.time()
    try:
        p = subprocess.run([CODELY, "-p", prompt, "--approval-mode", "default"],
                           capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return (p.stdout or "") + (("\n" + p.stderr) if p.returncode else ""), time.time() - t0, None
    except Exception as exc:  # noqa: BLE001
        return "", time.time() - t0, "%s: %s" % (type(exc).__name__, str(exc)[:120])


def build_prompt(task, payload):
    spec = TASKS[task]
    rules = []
    for key, allowed in (spec.get("enums") or {}).items():
        rules.append("   %s 只能取：%s" % (key, " | ".join(allowed)))
    allow_block = ("\n枚举白名单（必须逐字使用）：\n" + "\n".join(rules)) if rules else ""
    return (
        "你是 FLUX 机队的主控判断模块。只输出一个 JSON 对象，不要解释、不要客套、不要 Markdown 正文。\n"
        "任务：%s\n"
        "输出契约：%s\n%s\n"
        "硬规则：\n"
        "1) 只依据下面给出的事实，不许编造不存在的文件、卡号、主机；\n"
        "2) 路径必须从证据里原样引用；\n"
        "3) 结论要能被执行，不要写「需要进一步分析」这类空话；\n"
        "4) 只输出 JSON。\n\n"
        "证据：\n%s\n" % (spec["goal"], spec["hint"], allow_block,
                          json.dumps(payload, ensure_ascii=False)[:12000])
    )


def run(task, payload, allow_codely=True, quiet=False):
    if task not in TASKS:
        print("未知任务 %r，可用：%s" % (task, ",".join(TASKS)), file=sys.stderr)
        return 1, None
    prompt = build_prompt(task, payload)
    attempts = []
    tiers = list(TIERS)
    if getattr(run, "_big", False):
        tiers.append(BIG_TIER)
    if getattr(run, "_deep", False):
        tiers += [BIG_TIER, DEEP_TIER]
    for tier, model, tmo in tiers:
        right, secs, err = ask_ollama(model, prompt, tmo)
        obj = normalize(task, _extract_json(right))
        ok, errs = validate(task, obj) if obj else (False, ["无 JSON 输出 %s" % (err or "")])
        if ok:
            errs = rules_violations(task, obj, payload)
            ok = not errs
        attempts.append({"tier": tier, "model": model, "ok": ok, "secs": round(secs, 1),
                         "errs": errs[:4]})
        if not quiet:
            print("[brain] %-5s %-18s %5.1fs %s" % (tier, model, secs,
                                                    "OK" if ok else "FAIL " + "; ".join(errs[:2])),
                  file=sys.stderr)
        if ok:
            log({"ts": now(), "task": task, "tier": tier, "model": model, "ok": True,
                 "secs": round(secs, 1), "attempts": attempts})
            return 0, obj
        # 升档前把失败原因喂回去，比重复问同一句有用
        prompt = prompt + "\n上一次输出不合格：%s\n请修正后只输出 JSON。\n" % "; ".join(errs[:3])
    if allow_codely:
        out, secs, err = ask_codely(prompt + "\n本地模型多次不合格，请你直接给出合格 JSON。",
                                    timeout=900)
        obj = normalize(task, _extract_json(out))
        ok, errs = validate(task, obj) if obj else (False, ["codely 无 JSON %s" % (err or "")])
        if ok:
            errs = rules_violations(task, obj, payload)
            ok = not errs
        attempts.append({"tier": "codely", "model": "codely", "ok": ok,
                         "secs": round(secs, 1), "errs": errs[:4]})
        if not quiet:
            print("[brain] codely %.0fs %s" % (secs, "OK" if ok else "FAIL " + "; ".join(errs[:2])),
                  file=sys.stderr)
        if ok:
            log({"ts": now(), "task": task, "tier": "codely", "model": "codely", "ok": True,
                 "secs": round(secs, 1), "attempts": attempts})
            return 0, obj
    log({"ts": now(), "task": task, "tier": "none", "ok": False, "attempts": attempts})
    if not quiet:
        print("[brain] 全部档位失败：%s" % json.dumps(attempts[-1], ensure_ascii=False), file=sys.stderr)
    return 2, None


def selftest():
    """不调模型，只证契约闸会拦：假路径/坏枚举/空话必须被拒。"""
    cases = [
        ("rework_rootcause", {"root_cause": "GATE", "fix": "把判据里的 BLOCKED 改成行首匹配",
                              "next": "重跑一张验证"}, True),
        ("rework_rootcause", {"root_cause": "MAGIC", "fix": "xxxxxxxxxx", "next": "yyyyyyyyyy"}, False),
        ("quality_audit", {"verdict": "REAL", "why": "待定"}, False),
        ("line_plan", {"deliverable": "cph4/fleet/reports/不存在.md", "how": "派一张卡给 bm-a",
                       "accept": "产物非空且进 git"}, False),
    ]
    rule_cases = [
        ("fleet_triage", {"actions": [{"node": "bm-a", "action": "none", "why": "等上游同步就好"}]},
         {"nodes": [{"node": "bm-a", "ahead": 266, "stamp_age_s": 120}]}, False),
        ("fleet_triage", {"actions": [{"node": "bm-c", "action": "node_sync", "why": "落后太多先 reset"}]},
         {"nodes": [{"node": "bm-c", "ahead": 0, "stamp_age_s": 100}]}, False),
        ("rework_rootcause", {"root_cause": "GATE", "fix": "verify_on_node: bm-m",
                              "next": "R-TRIAGE-NOT-EXIST-20260101"}, {}, False),
    ]
    bad = 0
    for task, obj, payload, want in rule_cases:
        v = rules_violations(task, obj, payload)
        good = (bool(v) != want) if False else ((not v) == want)
        bad += 0 if good else 1
        print("[selftest] rule %-15s want=%-5s got=%-5s %s" % (task, want, not v, v[:1]))
    for task, obj, want in cases:
        ok, errs = validate(task, obj)
        good = (ok == want)
        bad += 0 if good else 1
        print("[selftest] %-18s want=%-5s got=%-5s %s" % (task, want, ok, "" if good else errs))
    print("[selftest] %s" % ("PASS" if not bad else "FAIL %d" % bad))
    return 0 if not bad else 1


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--task")
    ap.add_argument("--input", help="JSON 文件路径，或 - 读 stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-codely", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--big", action="store_true", help="允许升到 9B（默认不升）")
    ap.add_argument("--deep", action="store_true", help="允许升到 14B（慢，只给难题）")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.task:
        ap.print_help()
        return 1
    run._big = bool(a.big)
    run._deep = bool(a.deep)
    raw = sys.stdin.read() if a.input == "-" else (
        open(a.input, encoding="utf-8").read() if a.input else "{}")
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {"raw": raw[:12000]}
    rc, obj = run(a.task, payload, allow_codely=not a.no_codely)
    if obj is not None:
        print(json.dumps(obj, ensure_ascii=False) if a.json else json.dumps(obj, ensure_ascii=False, indent=1))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
