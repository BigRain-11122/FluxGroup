---
name: fleet-ops
description: 机队运维专家席（网关管家版·canon 快照 2026-10-19·正身=cph4/skills/fleet-ops/）。Use when CEO 从手机问机队/机器/计划任务/弹窗/黑窗/同步/poke/心跳/停摆/让路/派单/车道类问题，或需要判障定位。Triggers on 机队/机器/bm-a/bm-b/bm-c/bm-d/计划任务/弹窗/黑窗/同步/心跳/停摆/让路/派单/车道.
---

# 机队运维席速查（网关管家版）

正典深度位（绝对路径·只读）：车道表=`C:\Users\sjs20\Desktop\FluxGroup\cph4\resource-chain.md` §9.1｜调度协议=`C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\dispatcher\CEO-PROXY\`｜机队名册=`C:\Users\sjs20\Desktop\FluxGroup\Tools\fleet-nodes.json`。本件只收 CEO 高频问判速查。

## 判障速查（CEO 问「X 怎么样/为什么不」先按此定位）

1. **机器在不在线**：跑 fleet-reality（见 AGENTS.md 手册 1）——看 tailnet=Y/N + listener :8790 /health + 心跳新鲜度；bm-d 若显示 empty-ip roster slot=采购期未入网，属正常态，勿报「离线故障」。
2. **「它怎么停了」三步**：①心跳文件 mtime 冻结 >30min=停摆嫌疑 ②拉取 .:fail=git 通道问题 ③判停摆正法=poke 该机 wake_tasks（名册里有）→3 分钟复探。你只做「唤醒+复探+如实报」，修复归机队会话。
3. **弹窗/黑窗复发**：=计划任务 LogonType 回归或新任务绕正门——如实记一笔转机队会话（fleet-ops 席），你不碰任务注册。
4. **同步慢**：先看 fleet-reality 的 origin/main 对齐情况——秒级通道（poke）+5min 轮询双轨在役，慢=正常兜底，故障才转。
5. **让路期误解**：工作日白天 bm-a GPU 空/重模型不在=让路律设计态，非故障。

## 车道速查（派活裁决口径）

bm-a=集团中枢+大内存（工作日白天重活禁）｜bm-b=声音+TTS+回测 CPU｜bm-c=生成视觉-only GPU 主力（其他活禁入其 GPU）｜bm-d=六卡机（V100×3 大脑+P 卡草稿厂·采购入网中）。谁干什么活按此口径答 CEO。

## 红线（与 AGENTS.md 同律）

只读+唤醒；禁注册任务/禁 git 写/禁停改生产任务；一切修复动作=转机队会话执行，你负责判清楚+说人话。
