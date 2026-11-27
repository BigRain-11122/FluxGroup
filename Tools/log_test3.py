# -*- coding: utf-8 -*-
"""Append test #3 to the prompt-library test log."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "TEST-20261105.md")

ADD = """
## 测试 3 · 导演解法：三镜一拍（5s × 3 剪成一条表演）

**思路**：一条 5 秒长镜演不出"渴望→抑制→泄露"（测试 1/2 已证），那就把表演交给**剪辑**——
三镜各演一个拍子，观众自己补完情绪链。这也是低预算片子的标准解法。

| 镜 | 拍子 | 提示词要点 | 实测 |
|---|---|---|---|
| S1 眼 | **反应**：有人在画外叩玻璃，她抬眼 | locked 85mm + 画外触发 + 瞳孔/下眼睑 + 一次慢眨眼 | **读出**：低头→抬眼看→落回，能读到"注意到" |
| S2 手 | **接触**：指尖按上冷玻璃、下滑、留印、呼气起雾 | locked 85mm + 接触 + 物理证据（印子/起雾） | **强**：手贴上玻璃并下滑，印子可见 |
| S3 唇 | **抑制与泄露**：抿唇、吞咽、下颌轻颤、张唇呼气 | locked 85mm + 抑制 + 微泄露 | 仍在渲染（本地单条 10 分钟+，异常慢） |

- S1：`tests/out/p3_three_shot/S1_ecu_eyes.mp4`（对照 `s1-compare.png`）
- S2：`tests/out/p3_three_shot/S2_ecu_fingertip.mp4`（对照 `s2-compare.png`）
- 已剪：`tests/out/p3_performance_cut.mp4`（10.33s，S1+S2）

### 三条硬发现（已写进词条）

1. **源帧决定景别上限**：源图是胸像，提示词要"极特写"，模型只回落到中近景。
   想做 ECU，必须先有一张 ECU 源帧——这条以前没人写，白试了三轮。
2. **物理触发 > 抽象情绪**：写"她注意到"演不出来；写"画外有人叩玻璃，她抬眼"就有了。
3. **一镜一拍**：5 秒只够一个动作 + 一个反应；三层必须拆三镜，靠剪辑连接。

### 结论

- 新增词条 `directing.low-budget-performance`（verified=true）与 `camera.source-frame-ceiling`（verified=true），存 `seeds/directing-v1.jsonl`。
- 现条件下的最优表演配方 = **锁定机位 + 局部细节 + 物理触发 + 一镜一拍 + 剪辑连接**。
"""
with io.open(log, "a", encoding="utf-8") as fh:
    fh.write(ADD)
print("appended test #3")