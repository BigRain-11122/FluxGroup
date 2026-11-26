# -*- coding: utf-8 -*-
"""city_contract_check.py — 硅基城市跨仓契约闸（只读，不修任何数据）。

为什么要有它：BigLife（语义/居民）与 FluxVerse/CityWeb（几何/渲染）是两个仓，
现状靠一个 JSON 偶然对齐，谁也没验过对方。CEO 2026-11-26 令「不要各干各的」，
本闸就是那句令的执行机关——**红了不许对外说"已接通"**。

判据（全部确定性）：
  A 生产件 schema：agent-loop 协议号 / 每拍每人有 place / 地点在 places.json 内 / act 在词表
  B 桥一致性：slots[].id 都在 agent-loop.agents 里；slots 带 place/act 字段
  C 消费侧声明：CityWeb/types.ts 必须声明 place 与 act_label —— 缺 = consumer-not-wired
  D 相遇对称：MEET 两人 with 互指、同地点

用法：
  python -X utf8 Tools/city_contract_check.py
  python -X utf8 Tools/city_contract_check.py --json
退出码 0=合，1=不合（并打印每侧责任方）。
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIGLIFE = os.path.join(ROOT, "life", "BigLife")
FV = os.environ.get("FLUXVERSE_ROOT") or r"D:\FluxGroup\gaming\FluxVerse"
PLACES = os.path.join(ROOT, "cph4", "city-foundation", "places.json")
AGENT = os.path.join(BIGLIFE, "state", "agents")
BRIDGE = os.path.join(FV, "world-public", "city-bridge.json")
TYPES = os.path.join(FV, "CityWeb", "src", "types.ts")

ACTS = {"work", "move", "seek", "rest", "wait"}


def load_places():
    try:
        j = json.load(io.open(PLACES, encoding="utf-8"))
        legal = set()
        for ps in (j.get("districts") or {}).values():
            legal |= set(ps)
        legal |= set(j.get("plaza") or [])
        legal |= set(j.get("fallback") or [])
        return legal, j.get("protocol")
    except (OSError, ValueError):
        return set(), None


def latest_agent_file():
    try:
        fs = [f for f in os.listdir(AGENT) if f.startswith("agent-loop-") and f.endswith(".json")]
        if not fs:
            return None
        return os.path.join(AGENT, sorted(fs)[-1])
    except OSError:
        return None


def main():
    issues = []          # (side, code, detail)
    legal, pproto = load_places()
    if not legal:
        issues.append(("group", "places-missing", PLACES))

    # ---- A. 生产件 ----
    ap = latest_agent_file()
    al = None
    if not ap:
        issues.append(("biglife", "agent-loop-missing", AGENT))
    else:
        try:
            al = json.load(io.open(ap, encoding="utf-8"))
        except ValueError as exc:
            issues.append(("biglife", "agent-loop-bad-json", str(exc)))
    if al:
        if al.get("protocol") != "biglife-agent-loop-v1":
            issues.append(("biglife", "protocol-mismatch", str(al.get("protocol"))))
        agents = set((al.get("agents") or {}).keys())
        for snap in al.get("timeline") or []:
            got = set((snap.get("agents") or {}).keys())
            if got != agents:
                issues.append(("biglife", "turn-incomplete",
                               "turn %s 缺 %d 人" % (snap.get("turn"), len(agents - got))))
            for cid, s in (snap.get("agents") or {}).items():
                if legal and s.get("place") not in legal:
                    issues.append(("biglife", "place-unknown", "%s:%s" % (cid, s.get("place"))))
                if s.get("act") not in ACTS:
                    issues.append(("biglife", "act-unknown", "%s:%s" % (cid, s.get("act"))))

    # ---- B. 桥 ----
    br = None
    try:
        br = json.load(io.open(BRIDGE, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        issues.append(("biglife", "bridge-missing", str(exc)))
    if br and al:
        agents = set((al.get("agents") or {}).keys())
        for s in br.get("slots") or []:
            sid = s.get("id")
            if sid not in agents:
                issues.append(("biglife", "slot-not-in-agents", str(sid)))
            if "place" not in s or "act" not in s:
                issues.append(("biglife", "slot-no-behavior-fields", str(sid)))

    # ---- C. 消费侧声明（"各干各的"报警器）----
    try:
        ts = io.open(TYPES, encoding="utf-8", errors="replace").read()
    except OSError:
        ts = ""
        issues.append(("cityweb", "types-missing", TYPES))
    if ts:
        for f in ("place", "act_label"):
            if not re.search(r"\b%s\?" % re.escape(f), ts):
                issues.append(("cityweb", "consumer-not-wired", f))
    if ts and "residents.ts" and not re.search(r"place", ts):
        issues.append(("cityweb", "consumer-not-wired", "place"))

    # ---- D. 相遇对称 ----
    if al:
        tl = {snap.get("turn"): snap.get("agents") or {} for snap in al.get("timeline") or []}
        for e in al.get("events") or []:
            if e.get("type") != "MEET":
                continue
            a, b, t = e.get("a"), e.get("b"), e.get("turn")
            snap = tl.get(t) or {}
            if (snap.get(a) or {}).get("with") != b or (snap.get(b) or {}).get("with") != a:
                issues.append(("biglife", "meet-asymmetric", "%s<->%s@%s" % (a, b, t)))

    if "--json" in sys.argv:
        print(json.dumps({"ok": not issues, "issues": issues}, ensure_ascii=False, indent=1))
    else:
        print("places=%d protocol=%s agent_loop=%s"
              % (len(legal), pproto, os.path.basename(ap) if ap else "-"))
        if not issues:
            print("verdict: PASS（两侧契约一致）")
        else:
            print("verdict: FAIL（%d 项）" % len(issues))
            for side, code, detail in issues[:12]:
                print("  [%s] %-24s %s" % (side, code, detail))
            if len(issues) > 12:
                print("  ... 其余 %d 项" % (len(issues) - 12))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
