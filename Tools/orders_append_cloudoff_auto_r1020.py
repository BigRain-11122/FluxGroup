# -*- coding: utf-8 -*-
"""orders 台账追加：自动化任务全部本地（T0 追加令·脚本闸门）。"""
import io

ROW = (
    "| 2026-10-20 18:32（校时 18:32） | CEO 令（原话）「自动化任务全部走本地，不要再消耗云端 token」 | "
    "**executed·脚本闸门落地**：全集团 **16 个会拉起云端 codely 无头会话的自动化脚本**加统一闸门（开关=`cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md` 存在即拦，拦点在 Start-Process 前，本地前置照跑，留痕 `media/logs/cloud-off-suppressed.log`）——"
    "调度/巡视 7 件（patrol-runner/patrol-fleet-carrier/proxy-event-carrier/shift-supervisor/decision-round/evolution-tick/night-round）+子公司循环 6 件（BigStream/BigLife/BigDomain/BigCompute/BigMoney/FluxVerse iteration_loop）+游戏 3 件（MiniGame EngineTick/ModeTick〔8 任务共用〕/BoardForge）。"
    "**验证**=16 脚本 PowerShell 解析 0 错·闸门自测退出码 0 且落日志·现场 5 个 codely 全为 --experimental-acp 交互窗、无 -p 无头回合。"
    "**不受影响**=HQ-FleetDispatcher/IdleWatch/MemoryBudgetGate/SilenceGuard/WT-Park/bm-a-Sentinel/OllamaOrphanWatch/OpenClaw 等本地免费任务与各司纯 CPU 循环。"
    "**副作用**=无人值守轮的 LLM 判断面（L2 八班/域巡逻/各司迭代）暂停，本地确定性巡班照跑；恢复须先解令。"
    "正典修订=DISPATCHER-CHARTER §五.7+CLOUD-OFF v1 §八。 | executed（16 脚本+1 工具+2 正典；未提交 git） [via bm-a 控制台] |"
)


def main():
    p = "docs/orders.md"
    s = io.open(p, "r", encoding="utf-8", newline="").read()
    if "自动化任务全部走本地" in s:
        print("skip (already logged)")
        return
    nl = "\r\n" if "\r\n" in s else "\n"
    if not s.endswith(nl):
        s += nl
    s += ROW + nl
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("orders row appended")


if __name__ == "__main__":
    main()