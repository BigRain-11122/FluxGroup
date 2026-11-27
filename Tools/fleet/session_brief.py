#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""session_brief.py - 给"本地模型会话"的开工简报（零 LLM，全部盘上事实）。"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(ROOT, "cph4", "fleet")
S = os.path.join(F, "state")
OUT = os.path.join(F, "LOCAL-SESSION-BRIEF.md")


def j(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default or {}


def age(p):
    try:
        return round(time.time() - os.path.getmtime(p))
    except OSError:
        return None


def rows(p):
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    except OSError:
        pass
    return out


def main():
    pulse = j(os.path.join(F, "dispatcher", "PULSE.json"))
    sync = j(os.path.join(S, "state-sync.json"))
    cap = j(os.path.join(S, "capabilities.json"))
    board = j(os.path.join(S, "output-board.json"))
    sw = j(os.path.join(S, "selfwatch.json"))
    q = rows(os.path.join(F, "PRODUCTION-QUEUE.jsonl"))
    from collections import Counter
    states = Counter(r.get("state") for r in q)
    online = [n for n, e in cap.items() if isinstance(e, dict) and e.get("online")]
    prods = rows(os.path.join(F, "PRODUCTS.jsonl"))
    open_cards = [r for r in q if r.get("state") in ("OPEN", "BLOCKED")][:8]
    try:
        svc = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=5).stdout
        ns = sum(1 for l in svc.splitlines() if "com.fluxgroup." in l)
    except Exception:
        ns = -1

    L = ["# 本地会话开工简报（自动生成）", "",
         "> 新会话第一条指令：读本文件，按「下一步」继续；不要依赖上一段对话的上下文。",
         "> 重生成：python3 Tools/fleet/session_brief.py", "",
         "## 盘上事实", "",
         "| 项 | 值 |", "|---|---|",
         "| 生成时间 | %s |" % time.strftime("%Y-%m-%d %H:%M:%S"),
         "| 主控脉 | %ss 前，一拍 %ss，git=%s |" % (age(os.path.join(F, "dispatcher", "PULSE.json")),
                                                pulse.get("sec"), pulse.get("git")),
         "| 状态同步 | %ss 前 |" % round(time.time() - float(sync.get("ok_ts") or 0)),
         "| 常驻服务 | %d |" % ns,
         "| 在线节点 | %s（hub=%s） |" % (",".join(online), cap.get("_shared", {}).get("model_hub_online")),
         "| 队列 | %s |" % json.dumps(dict(states), ensure_ascii=False),
         "| 产出 | 产品 %s / 内部 %s / 缺失 %s |" % (board.get("product"), board.get("infra"), board.get("missing")),
         "| 自愈 | stale=%s |" % (sw.get("stale") or []),
         "| 发布包 | %s |" % (", ".join(p.get("id") for p in prods) or "-"),
         "", "## 下一步（按顺序做，不需要问）", "",
         "1. 看 cph4/fleet/CAPABILITIES.md：谁在线、能接什么；",
         "2. 处理 OPEN/BLOCKED（见下表），能改派就改派，需要人判的留在队列并写原因；",
         "3. 每完成一件，必须留下可核验产物（文件 + sha256），用 pack_release.py 打成交付包；",
         "4. 本地模型优先：4B 做判读/摘要，8B 做综合；云只走 Codely 且非必要不用。",
         "", "## 待办卡（前 8 张）", ""]
    for r in open_cards:
        L.append("- **%s** [%s] — %s" % (r.get("state"), r.get("id"), (r.get("note") or "")[:80]))
    if not open_cards:
        L.append("- 无（队列干净）")
    L += ["", "## 本地模型", "",
          "- 4B：qwen3.5:4b-mlx @ 11434（常驻，判读/摘要）",
          "- 8B：qwen3:8b-dsh32k @ 11436（32k，工具调用已验证，按需加载）",
          "- 共享：http://100.75.133.10:8792（Tailscale 内网免令牌，白名单 4B/4B-instruct/向量）",
          "", "## 红线", "",
          "- 只认盘上产物，不认「进程活着」；",
          "- 单写手：队列只由 master_agent 写，台账只由 CEO-PROXY 写；",
          "- 取消/停线必须写原因；远端交付物必须带 sha256；",
          "- 模型不得替 CEO 对外沟通、不得发密钥。"]
    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("brief:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
