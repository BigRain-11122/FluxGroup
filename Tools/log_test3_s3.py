# -*- coding: utf-8 -*-
"""Record S3 completion + the VRAM/queue lesson in the prompt-library test log."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = os.path.join(ROOT, "cph4", "fleet", "prompt-library", "tests", "TEST-20261105.md")

ADD = """
### S3 补记（2026-11-05 21:4x）

第一次跑 S3（"抿唇+吞咽+下颌颤+张唇"四件事塞一句）**23 分钟没出片**，GPU 满载 11.7/12.3GB。
处置：①掐客户端进程；②`POST /interrupt` 无效（队列仍 running=1）；③**重启 ComfyUI** 清队列与显存；
④把提示词压到 **22 词、只留一个事件**（抿唇→吞咽→呼气，去掉"下颌颤"）。

重跑结果：**300 秒出片**，动作读出（抿唇、低头、抬眼），三镜剪成 **15.5 秒**表演段：
`tests/out/p3_performance_cut.mp4`

### 由此新增的操作规矩（本地 H3）

1. **一条提示词只许一个事件**。四件事塞一句 → 采样时间暴涨且动作互相抵消。
2. **单条 >10 分钟 = 异常**，标准时长 130–300 秒；超时先查显存与队列，不要干等。
3. **`/interrupt` 不一定生效**：队列 `running` 不清就重启 ComfyUI，重启是干净解。
4. 重启后第一条会慢些（加载模型），从第二条恢复正常。
"""
with io.open(log, "a", encoding="utf-8") as fh:
    fh.write(ADD)
print("appended S3 note")