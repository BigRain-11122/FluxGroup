# 巡查（有序）2026-11-11T00:02:11

排序规则：**轮次决定先后**（断链 → 供给 → 执行 → 质量 → 方向），轮内按阻塞他人×3 + 停摆时长 + 修复成本。全部 6 条。

## R1 断链/停摆（3 条）· 机器或通道断了，后面所有活都白派

 1. **主控脉 blocker：resident-model-size** → 看 PULSE.json 该 blocker 的判据，修因不是压阈值｜`bm-m`
 2. **主控脉 blocker：com.fluxgroup.ollama** → 看 PULSE.json 该 blocker 的判据，修因不是压阈值｜`bm-m`
 3. **主控脉 blocker：git-sync** → 看 PULSE.json 该 blocker 的判据，修因不是压阈值｜`bm-m`

## R3 执行（1 条）· 卡在飞但不动 / 失败无主 / 阻塞过期

 4. **NODE-SYNC-bm-b-2330 无责任人（BLOCKED）** → 定责：改卡重派或落根因账｜`bm-m`

## R4 质量（1 条）· 产物不合格或闸失效

 5. **1 条线质量未达阈值** → 逐条看 QUALITY-BOARD 的硬伤列，改产物不改阈值｜`bm-m`

## R5 方向（1 条）· 声明在跑但长时间没产物

 6. **RECON·竞品拆解 声明 ACTIVE 但已停 83 小时** → 要么给它真活，要么改声明为 PARKED（不许挂着 ACTIVE 骗人）｜`bm-m`

---
_巡查只做排序与定责；具体做法在各条目的 evidence 里，改判据请改对应正身件_
