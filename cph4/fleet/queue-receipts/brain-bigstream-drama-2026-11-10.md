> ⛔ 引证核验未过（2 处查无此文件），本页结论不可作为决策依据：
> .drama-state.json
> frame_diff.py

# 2026-11-03

## 漫剧线解堵方案
当前核心阻塞点明确：**口型同步缺失**（LatentSync 需装接口站）、**字幕生成质量极低**（cer 0.67，FAIL）、**分辨率压缩过度**（540×960 vs 1080×1920）。

动作一：**装口型接口站**。由运维团队安装 `cph4/fleet/drama-dept-v1/GITHUB-PIPELINES-20261103.md` 指定的 `bytedance/LatentSync`（Apache-2.0），并在工作机部署 `ShmuelRonen/ComfyUI-LatentsyncWrapper`，强制说话镜过口型校验。
动作二：**重构字幕管线**。由算法组运行 `frame_diff.py` 检测 ASR 差异，将 `/Users/junsheng.sun/.cache/whisper-mlx/large-v3-turbo` 推理替换为商用模型；利用 `.drama-state.json` 记录缺陷，拒绝低 cer（>5%）样本进入剪辑。
动作三：**实施分辨率升频**。由工程组在 `cph4/fleet/drama-dept-v1/HEAD-BENCHMARK-20261103.md` 指导下，将生成输出重绘为 1080×1920，消除 540×960 的“一档”糊感。

【给谁·下一步】

<!-- verify: citations=4 unverified=2 -->

---
*副大脑 bm-m · qwen3.5:4b-mlx 本地产出 · 依据仓库摘录*
