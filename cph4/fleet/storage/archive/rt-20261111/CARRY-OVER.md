# 旧机制遗留的活（2026-11-11 清空前提取）

> 清空前 41 张分片卡里，32 张已作废、3 张 UNVERIFIED、4 张 OPEN、2 张 BLOCKED。
> 全部分片已清空、从头开始；下面这些是**有真实工作意图**的条目，需要在新机制里重新立卡（带 product_id/stage/task_type）。

- **[audio/BLOCKED]** `VCORP-GEN-r1202-EP001-060-20261108` — 短剧配音批生成 r1202_ep001_060（EP001-EP060，IndexTTS2）
  - 交付物：media/drama-tools/voicegen_r1202_ep001_060.DONE.json
- **[audio/BLOCKED]** `R-NEXT-BIGSTREAMD-TTS-QC-20261109` — 配音批质检：r1202 目录逐集时长/静音/体积（出可发布集数清单）
  - 交付物：cph4/fleet/queue-receipts/tts-qc-20261109.json
- **[audio/OPEN]** `REPAIR-R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101` — [repair] R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101 的根因与下一步
  - 交付物：cph4/fleet/repairs/R-TRIAGE-BIGSTREAMDUANJU-BMB-20261101.md
- **[audio/OPEN]** `UNBLOCK-VCORP-GEN-r1202-EP001-060-20261108` — [unblock] VCORP-GEN-r1202-EP001-060-20261108 的解锁动作
  - 交付物：cph4/fleet/repairs/VCORP-GEN-r1202-EP001-060-20261108-unblock.md
- **[audio/OPEN]** `UNBLOCK-R-NEXT-BIGSTREAMD-TTS-QC-20261109` — [unblock] R-NEXT-BIGSTREAMD-TTS-QC-20261109 的解锁动作
  - 交付物：cph4/fleet/repairs/R-NEXT-BIGSTREAMD-TTS-QC-20261109-unblock.md
- **[brain/UNVERIFIED]** `C-FIN-ETF-COMPOSITE` — ETF 复合因子轮动回测（钱的面：年化/夏普/回撤）
  - 交付物：quant/bigmoney/results/etf_composite_pf.json
- **[visual/UNVERIFIED]** `Q-MV-0001-003` — mv0001 v716 稳定性闸（seam/freeze）
  - 交付物：stability verdict
- **[visual/UNVERIFIED]** `asset-lib-char-gen-2026-11-06` — 
- **[visual/OPEN]** `R-NEXT-BIGSTREAMM-REBUILD-20261109` — MV 合成本片：按 EDL 行表重建成片 v721（缺的是成片，不是闸）
  - 交付物：cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v721.mp4
