# 主控巡查 2026-11-11T15:13:26

## 一、机器
- **公司生产力机（delivery）** network_ok_not_registered ｜ 席 8 ｜ 类型 11 ｜ 工序 15 ｜ 队列 O0/R0/D0/B0 ｜ 回执 无
- **传家宝（visual）** blocked_no_comfyui ｜ 席 9 ｜ 类型 8 ｜ 工序 9 ｜ 队列 O1/R0/D0/B0 ｜ 回执 无
- **小钢炮（audio）** offline ｜ 席 7 ｜ 类型 4 ｜ 工序 8 ｜ 队列 O3/R0/D0/B2 ｜ 回执 无
- **算力大脑（brain）** not_installed ｜ 席 7 ｜ 类型 2 ｜ 工序 2 ｜ 队列 O0/R0/D0/B0 ｜ 回执 无
- **MacBook（control）** ready_paused ｜ 席 8 ｜ 类型 19 ｜ 工序 24 ｜ 队列 O0/R0/D0/B0 ｜ 回执 无

## 二、任务面
- 工序 59 道，有产物契约 2 道（缺 57）

## 三、抽验（0 件，失败 0）
- 本轮无待抽验件

## 四、需要出手
- [MACHINE-DOWN] visual：blocked_no_comfyui
- [WORK-QUEUED-NO-WORKER] visual：1 张 OPEN 但机器状态 blocked_no_comfyui
- [MACHINE-DOWN] audio：offline
- [WORK-QUEUED-NO-WORKER] audio：3 张 OPEN 但机器状态 offline
- [MACHINE-DOWN] brain：not_installed
- [NO-OUTPUT-CONTRACT] 57 道工序：没写产物路径，自驱无从下手（例：PROD-GAME-SUBMIT/材料套用, PROD-GAME-SUBMIT/打包, PROD-GAME-SUBMIT/图标）
