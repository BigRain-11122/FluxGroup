# 2026-10-27 短剧线日报：工序缺口与行动建议

经核查台账，当前存在以下「素材在盘但工序未接」的断层，按潜在业务损失排序：

1. **EP004 至 EP060 全量配音缺口**：`cph4/fleet/drama-001-stockera/episodes/EP001..060.json` 确认剧本在位，但仅 `media/drama-mix-out/r1003_3layer/` 中存留前 3 集混音，导致后续 57 集为无声音默片；行动：立即调用 `drama_voicegen_eps_r998.py` 启动 TTS 全量生成并接入装配。
2. **EP001-003 单集声画合流未批量执行**：虽已有 `C:\Fluxgroup\FluxGroup\media\drama-eps-audio\EP001_AUDIO-r1003.mp4` 样片，但 `drama_ep_burn.py` 尚未批量运行将音轨写入其余集数；行动：修改装配器默认链，加入双遍 loudnorm 参数强制处理真峰值超限。
3. **黑帧判定逻辑需升级**：`sim_kinsoku4.py` 当前无法自动区分设计内黑卡与异常黑帧，导致 `audit_durations.py` 误报风险；行动：在回归复验脚本中增加 `kind=card` 字段前置校验逻辑。

【给谁·下一步】
请 CEO 确认是否立即将 EP002/EP060（参考文档：`cph4/fleet/drama-dept-v1/R-20261027-drama-audio-remux-01.md`）的配音与合流排入今日产线，以消除 9 天产能空转；若需复测 CSA 一致性（参考 `cph4/fleet/drama-dept-v1/epburn-handover/CSA-SMOKE-VERDICT-20261017.md`）请先批复。

---
*副大脑 bm-m · qwen3.5:35b-a3b 本地产出 · 依据仓库摘录*
