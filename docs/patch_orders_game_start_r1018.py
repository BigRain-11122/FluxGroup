# -*- coding: utf-8 -*-
# patch_orders_game_start_r1018.py — orders 落「游戏全线并行开工」令行
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\sjs20\Desktop\FluxGroup\docs\orders.md"
raw = open(P, "rb").read()
bom = raw[:3] == b"\xef\xbb\xbf"
s = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
if not s.endswith("\n"):
    s += "\n"
ROW = ("| 2026-10-18 00:1x | CEO 令（原话）：「游戏开发一点进度都没有，给我全部项目并行开工！」（**游戏全线并行开工令·北极星⓪ CEO 令=最高优先**） | "
       "**executing（当窗点火+三线派单）**：①卡点定谳=B2191 车道饥饿（C-20261015-03 云帽 live≥2 结构性饿死全部 M2-M6 游戏车道·mode-ledger 连续 CLOUD_CAP_DEFER 空转实证·MV 云批收口后 live 回落）→"
       "修法裁决令发 engine-tick 维护窗（@银河牛马/御湖湾）：游戏 M 车道豁免云帽 defer·修后 mode-ledger 须现游戏车道 TICK_DONE 行；"
       "②A 机线已点火=X026Gate.ps1 -Stage all 后台跑（P02 全链 8 门+七工程 cross 并发复验=全线开工机读实锤·汇总 x026_gate_summary.txt）+A 机 14 款下一波活排产（P02 G4 构建批/P06 攻坚/吸嘟嘟专家细审+接线/U361 四款 S4 提审段/FluxVerse 城市续推）；"
       "③@银河牛马（B 机 10 款）：G04 S4 开卷+G23/G26/G28/G05/G07/G08/G13/G14/G20 北极星复测→S4 提审段+车道饥饿修法；"
       "④@御湖湾牛马（C 机 8 款）：G02 S4 三🟡收口+G10 T031 提审排产+G09Y/G12/G03/G06/G17/G18 北极星复测→S4+车道饥饿修法；"
       "排产正身=cph4/fleet/GAME-PARALLEL-START-20261018.md（三线 32 款×段位×下一波活全表） | executing（门禁全链在跑·B/C 派单在行·回执核验=mode-ledger TICK_DONE+orders 回执节） [via bm-a] |\n")
s += ROW
open(P, "wb").write((("\ufeff" if bom else "") + s).encode("utf-8"))
print("orders.md +1 game-start row appended")
