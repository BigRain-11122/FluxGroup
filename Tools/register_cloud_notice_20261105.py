# -*- coding: utf-8 -*-
"""Register the CEO 2026-11-05 20:2x cloud-quota notice: unlimited for now, but
only for finished deliverables and must-use cases; local first."""
import io
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)

ROW = (
    "| 2026-11-05 20:22（校时 20:22） | CEO 令（原话）：「云端暂时不限量，通知下去，"
    "但只有出成品和必须用的时候用，优先本地」 | **executed（当窗落两处 + 全员知会）**："
    "①**临时解禁面**=云端生成额度即日起**暂不限量**（含视频/图像/音频生成），有效期至 CEO 下一次收紧令；"
    "②**用途闸不变**=只允许两类用法——(a) **出成品**（直接进交付件的镜头/封面/成片素材）；"
    "(b) **必须用**（本地无该能力，或本地做不出该质量、或时间窗不允许）；"
    "③**优先本地律不变**=同一件事本地能做且质量够 → 一律本地，禁为省事走云；"
    "④**单件 >500 积分确认闸仍在**（不属额度限制，是花费闸）——但不代签，需 CEO 亲批；"
    "⑤**每日任务数上限仍是平台硬限**（今日实测 100/100 已满，24:00 后恢复）；"
    "⑥落件=docs/orders.md 本行 + cph4/token-economy.md §10.7 + fleet inbox 知会 | "
    "executed [via bm-a 交互窗] |\n"
)

orders = os.path.join(ROOT, "docs", "orders.md")
with io.open(orders, "a", encoding="utf-8") as fh:
    fh.write(ROW)
print("appended orders.md")

sec = """
### 10.7 云端临时解禁（CEO 2026-11-05 20:22 令·有效期至下一次收紧令）

- **额度**：暂不限量（视频/图像/音频生成）。原 §10.1-§10.6 的"例外面/白名单"不再是准入门槛。
- **用途闸（替代准入闸）**：只许两类——(a) 出成品；(b) 必须用（本地无能力/本地质量不够/时间窗不够）。
- **优先本地律不变**：本地能做且够用的一律本地，禁为省事绕云。
- **仍有效的闸**：单件 >500 积分确认（花费闸，不代签）；平台每日任务数上限（外部硬限）。
- **留痕**：每次云端批量使用在 orders 记一行用途与件数，便于日后算账。
"""
te = os.path.join(ROOT, "cph4", "token-economy.md")
with io.open(te, "a", encoding="utf-8") as fh:
    fh.write(sec)
print("appended token-economy.md §10.7")

bulletin = os.path.join(ROOT, "cph4", "fleet", "inbox", "BRAIN-BULLETIN.md")
line = ("\n- [2026-11-05 20:22 | CEO 令·全员知会] **云端额度暂不限量**（视频/图像/音频），"
        "但只准两种用法：**出成品**、**必须用**（本地做不到或时间不够）；**优先本地律不变**。"
        "单件 >500 积分仍需 CEO 亲批；平台每日任务数上限不变。正身=docs/orders.md 20:22 行 + token-economy §10.7。\n")
os.makedirs(os.path.dirname(bulletin), exist_ok=True)
with io.open(bulletin, "a", encoding="utf-8") as fh:
    fh.write(line)
print("appended fleet BRAIN-BULLETIN.md")