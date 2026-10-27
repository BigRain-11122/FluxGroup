# -*- coding: utf-8 -*-
# patch_orders_results_r1018.py — orders.md 尾部补记 CEO 结果监督元批评令
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\sjs20\Desktop\FluxGroup\docs\orders.md"
raw = open(P, "rb").read()
bom = raw[:3] == b"\xef\xbb\xbf"
s = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")

MARK = "委员会结果监督强化案"
if MARK in s:
    print("SKIP: row already present")
    sys.exit(0)
if not s.endswith("\n"):
    s += "\n"

ROW = "| 2026-10-18 15:1x | CEO 令（原话·元批评）：「委员会要加强工作和业务的结果监督，每次都写的很好，流程规则一大堆，最后出来的没多少」 | **executed（当窗立法+首轮对账）**：C-20261018-05 三裁定=①结果账本常设（cph4/fleet/RESULTS-LEDGER-v1.md·三列只记用户可见件·委员会+巡班步0 首节必对账·简报先报三行数字过程 ≤3 行）②新法配额闸=每周 ≤3 条·必附产出指向·超产拒立（反流程膨胀·本案自耗 1/3）③决议件必带结果核对尾节。首轮对账=已上线 0/已交付候 CEO 2（mv0001 成片·meme V1）/在制 4 线·发布堵点=CEO 保留面如实载明零催办 | executed（机制在役·下轮起巡班首节执法） [via bm-a] |\n"
s += ROW
open(P, "wb").write((("\ufeff" if bom else "") + s).encode("utf-8"))
print("orders.md +1 row appended (bom=%s)" % bom)
