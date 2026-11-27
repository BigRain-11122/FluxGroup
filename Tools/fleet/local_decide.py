#!/usr/bin/env python3
"""local_decide.py - 本地判定路由（能本地判的不上云）

用法:
  python Tools/fleet/local_decide.py route <任务类型>
  python Tools/fleet/local_decide.py route --list
  python Tools/fleet/local_decide.py health
  python Tools/fleet/local_decide.py ask L1 "文本"          # 需本地 ollama，让路态会拒绝

规则正身: cph4/fleet/LOCAL-COMPUTE-ALLOCATION-v1.md
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POLICY = os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json")
FLAG = os.path.join(ROOT, ".codely-cli", "machine-state.flag")

# L0 = 纯规则，不进模型；L1 = 本地 4B；L2 = 本地 8B；L3 = 云端
ROUTES = {
    "count":        ("L0", "数量统计由脚本算，模型算术不可信"),
    "date-math":    ("L0", "日期差/期限由脚本算"),
    "money":        ("L0", "金额比例由脚本算"),
    "hash":         ("L0", "sha/哈希比对是确定性操作"),
    "format":       ("L0", "格式校验是确定性操作"),
    "dedupe":       ("L0", "内容 sha 相同即重复，无需模型"),
    "gate":         ("L0", "闸的真假由断言给，模型只做解释"),
    "classify":     ("L1", "短文本分类，有明确答案"),
    "extract":      ("L1", "字段抽取，有明确答案"),
    "parse-receipt": ("L1", "回执解析，结构化"),
    "summarize-log": ("L1", "日志摘要，短输入"),
    "triage":       ("L1", "告警归因，可规则复算"),
    "short-copy":   ("L2", "短文案初稿，需连贯表达"),
    "rank":         ("L2", "候选排序，需权衡但领域内"),
    "spec-draft":   ("L2", "规格草拟，需结构表达"),
    "direction":    ("L3", "方向/跨线权衡，错代价高"),
    "architecture": ("L3", "架构决策"),
    "external-copy": ("L3", "对外内容，红线风险"),
    "longform":     ("L3", "长篇创作"),
}


def is_paused():
    return os.path.exists(FLAG)


def load_policy():
    try:
        return json.load(open(POLICY, encoding="utf-8"))
    except Exception:
        return {}


def node_for(level):
    p = load_policy()
    nodes = p.get("nodes", {})
    if level == "L0":
        return "local-script"
    if level == "L1":
        return nodes.get("bm-m", {}).get("duties", {}).get("resident", {}).get("model", "qwen3.5:4b-mlx")
    if level == "L2":
        return nodes.get("bm-a", {}).get("duties", {}).get("resident", {}).get("model", "qwen3.5:4b")
    return "cloud"


def cmd_route(task):
    if task == "--list":
        for k, (lv, why) in sorted(ROUTES.items(), key=lambda x: x[1][0]):
            print(f"{lv}  {k:16} {why}")
        return 0
    hit = ROUTES.get(task)
    if not hit:
        print(f"UNKNOWN task={task}（未登记的类型默认 L3，须先登记再降级）")
        return 3
    lv, why = hit
    if lv in ("L1", "L2") and is_paused():
        print(f"{lv}  blocked=paused  理由={why}  说明=让路态本地模型停，降级到 L0 或排队")
        return 2
    print(json.dumps({"level": lv, "target": node_for(lv), "why": why}, ensure_ascii=False))
    return 0


def cmd_health():
    out = {"paused": is_paused(), "ollama": None, "models": []}
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3) as r:
            d = json.loads(r.read().decode())
        out["ollama"] = "reachable"
        out["models"] = [m.get("name") for m in d.get("models", [])][:10]
    except Exception as e:
        out["ollama"] = f"unreachable: {type(e).__name__}"
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["ollama"] == "reachable" else 2


def cmd_ask(level, text):
    if is_paused():
        print("REFUSED: 本机在让路态，本地模型不可用")
        return 2
    model = node_for(level)
    if model == "cloud":
        print("REFUSED: L3 不走本地，请走云端")
        return 3
    prompt = ("你是判定器。只回答结论，并另起一行写依据。"
              "若无法判定就回答 UNKNOWN，不要猜。\n\n" + text)
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "think": False,
                       "options": {"temperature": 0}}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode())
    except Exception as e:
        print(f"ASK FAIL {type(e).__name__}: {e}")
        return 2
    resp = (d.get("response") or "").strip()
    if "依据" not in resp:
        print("ASK INVALID: 缺依据字段，视为未判定\n" + resp[:200])
        return 4
    print(json.dumps({"model": model, "level": level, "answer": resp}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p1 = sub.add_parser("route"); p1.add_argument("task")
    sub.add_parser("health")
    p3 = sub.add_parser("ask"); p3.add_argument("level"); p3.add_argument("text")
    a = ap.parse_args()
    if a.cmd == "route":
        return cmd_route(a.task)
    if a.cmd == "health":
        return cmd_health()
    if a.cmd == "ask":
        return cmd_ask(a.level, a.text)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())