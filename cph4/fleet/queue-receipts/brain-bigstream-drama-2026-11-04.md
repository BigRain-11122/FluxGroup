> ⛔ 引证核验未过（3 处查无此文件），本页结论不可作为决策依据：
> bili_repurpose.py
> drama_mix3_r1003.py
> frame_diff.py

# 2026-11-04 漫剧线解堵方案

现状：交付面已定 `media/drama-eps-audio`，60 集有声品合格；但正片画面母版仍沉默。瓶颈在于**平台改造**需新路径，且口型同步模块（bytedance/LatentSync）未纳入流水线。

下一步三个动作：
1. **谁做**：MacBook Pro 与前端工程组；**做什么**：调用 `bili_repurpose.py` 将发布路由切至 `drama-eps-audio`，禁止混流正片目录；**验收物**：日志中无旧路径命中记录。
2. **谁做**：视频处理组；**做什么**：在 `drama_mix3_r1003.py` 内嵌入 `.bak-20261031-sfxsnap` 补丁，补全 `render_sfx` 落位逻辑；**验收物**：混音体检单显示零缺件、zero-waveform。
3. **谁做**：AI 基建组；**做什么**：安装 `ShmuelRonen/ComfyUI-LatentSyncWrapper`，建立口型置信度门禁，强制说话镜过测；**验收物**：pipeline 日志中所有生成帧通过 `frame_diff.py` 一致性检测。

【给谁·下一步】交付组即刻执行路径切换，基建组完成 ComfyUI 封装部署。

<!-- verify: citations=3 unverified=3 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
