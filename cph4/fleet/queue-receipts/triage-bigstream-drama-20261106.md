# 线级体检 bigstream-drama · 2026-11-06 23:49

## 工段与证据目录
- drama-script   owner=编剧席      lane=-      证据 1/1 存在 · 文件 41 · 最新 5.0h
- drama-kf       owner=漫剧席      lane=bm-b   证据 0/1 存在 · 文件 0 · 最新 —
- drama-voice    owner=声音席      lane=bm-b   证据 0/1 存在 · 文件 0 · 最新 —
- drama-mix      owner=声音席      lane=bm-b   证据 0/1 存在 · 文件 0 · 最新 —

## 判定
- 最近产出 5.0h 前（阈值 48.0h）→ FRESH 在阈内

## 下一步（按缺口）
- drama-kf：建目录/补输入后再谈产出（责任人=漫剧席）
- drama-voice：建目录/补输入后再谈产出（责任人=漫剧席）
- drama-mix：建目录/补输入后再谈产出（责任人=漫剧席）


## 空工段归因（卡 R-NEXT-BIGSTREAMD-EVIDENCE-20261106 的 accept 项）

逐条查过盘面（本机 media/、外盘 /Volumes/移动硬盘、素材登记路径），结论不是一句"建目录"：

| 工段 | 登记证据路径 | 本机 | 外盘 | 判定 |
|---|---|---|---|---|
| drama-script | cph4/fleet/drama-dept-v1 | 41 件，最新 5.0h | — | 有料，正常 |
| drama-kf | media/drama-eps | 不存在 | 不存在 | **本机没有素材**：分镜/画面由 bm-b（local-gpu）产，尚未回传 |
| drama-voice | media/drama-tts-out | 不存在 | 不存在 | **不是从未生产**：配音脚本 media/drama-tools/drama_voicegen_batch.py 的输出根写死在
Windows 机（C:\Fluxgroup\FluxGroup\media\drama-tts-out），产物应从 bm-b 回传，当前没有回传记录 |
| drama-mix | 依赖 voice | 不存在 | 不存在 | 上游未回传，无法开工 |

因此本线的下一步不是"再派一张造目录的卡"，而是两件事之一：
①把 bm-b 的 media/drama-tts-out / media/drama-eps 回传（产物通道：node/<node> 分支或 artifact relay）；
②或在能跑 TTS 的机器上重跑 drama_voicegen_batch.py 生成 EP001-003（pilot 已跑通过 EP001-003）。
