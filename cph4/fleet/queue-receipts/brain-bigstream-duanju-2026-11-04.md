> ⛔ 引证核验未过（2 处查无此文件），本页结论不可作为决策依据：
> bili_repurpose.py
> drama_mix3_r1003.py

# 短剧线日报 · 2026-11-03

【缺口】正片目录无 a:0 流（静音母版），导致交付侧无法兼容“画面带声”策略。
【行动】按 `bili_repurpose.py` 改造逻辑，仅 `-c:v copy -map 0:v -map 1:a` 生成备份，严禁重编码画面。

【缺口】混音 `drama_mix3_r1003.py` 缺号落位补丁，导致 SFX 素材虽在盘但无法归位。
【行动】启用 `.bak-20261031-sfxsnap` 回退机制，暂搁置该集渲染，优先保障交付面 `media/drama-eps-audio` 零缺件。

【缺口】身份锁“脸部图+角色身份串”数据未显性同步，可能导致生成内容偏离预设档案。
【行动】强制接入 `TengXianhai/ai-short-drama-agent` 的三件套校验门控，否则断流阻断。

【需补充：…】因正片目录与 `media/drama-eps-audio` 分轨并行，缺失具体素材文件名无法定位缺口大小排序。

【给谁·下一步】给交付决策席，立即冻结重编码操作，转用现有母版备份链闭环。

<!-- verify: citations=2 unverified=2 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
