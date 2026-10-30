# 2026-10-27 漫剧线解堵方案

当前 60 集成片经 `audit_durations.py` 与 `sim_kinsoku4.py` 核验，`cph4/fleet/drama-001-stockera/episodes/EP001..060.json` 剧本映射无误，画面零缺陷。但 `R-20261027-drama-audio-remux-01.md` 证实存在严重“有声无轨”问题：3 层混音素材（`media/drama-mix-out/r1003_3layer/`）未合流，导致成片默片。

**待执行三步骤：**
1. **补声合流**：运维组对 EP002-003 执行 `ffmpeg -shortest` 指令，将混音源嵌入画面，验收物为带声轨 MP4；EP004-060 需先调用 `drama_voicegen_eps_r998.py` 生成全量语音。
2. **审计回退**：审核员检查 `cph4/fleet/drama-dept-v1/R-20261027-drama-audio-remux-01.md` 中 loudnorm 参数，确保真峰值≤-1.0dBFS，修复单集超标问题。
3. **固化标准**：将“双遍 loudnorm"逻辑写入 `drama_ep_burn.py` 装配链，防止未来默片复现；配合 `cph4/fleet/drama-dept-v1/epburn-handover/CSA-SMOKE-VERDICT-20261017.md` 验证一致性。

**【给谁·下一步】**
给 **导演席与配产组**：立即启动 `drama_voicegen_eps_r998.py` 批量生成 EP004-060 语音，验收物为音轨文件清单；随后执行全量合流，确保 `cph4/fleet/drama-dept-v1/R-20261027-drama-audio-remux-01.md` 中定义的“活”状态闭环。

---
*副大脑 bm-m · qwen3.5:35b-a3b 本地产出 · 依据仓库摘录*
