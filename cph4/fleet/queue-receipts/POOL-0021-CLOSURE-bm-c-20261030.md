# POOL-0021 收口回执（bm-c · 2026-10-30 23:3x）— 建议由 dispatcher 翻 done

卡面：Qwen-Image-2.1-Turbo KF 提速试烧批（int8 四件部署 + vs Krea2 对比三账 + 许可商用判定）

## 结论：卡面三项验收物早已全部存在，卡只是从未翻面，不需要重烧

| 验收项 | 证据（已在仓/工作树） | 状态 |
|---|---|---|
| 四件部署（sha/尺寸） | `cph4/fleet/qwen21-deploy-receipt-c2099.md` §一 leg-1：DiT int8 7,256,787,829B / TE w4a8 6,312,105,364B / VAE bf16 675,509,688B / turbo LoRA 913,314,512B，`weights_verdict_c2099.json` = OK 4/4 | ✅ |
| 试烧 + 对比三账 | 同回执 §三 冒烟 1024²×8 步 = 41.4s、峰值 14841MB、画质 7/10；对比 = `hq-wt-c2108/media/comfy-sidecar/compare/compare_verdict.json` + 拼板 `QWEN21-vs-KREA2-board-c2099.jpg`（3 同题材：qwen 64.5/192.2/125.8s vs krea 94.7/97.8/44.6s） | ✅ |
| 许可商用判定 | `hq-wt-c2108/cph4/fleet/bmc/qwen21_weights_c2094/LICENSE-VERDICT-20261020-c2101.md`（qwen-research 非 Apache；试烧合法，采用前须读全文） | ✅ |

## 判读（不翻案的结论）

- 盲评 **Krea2 胜 ≈2.5/3**：Qwen 在叙事可读性、材质落位占优，但硬字幕式「错字」、头部/肢体易崩、整体偏 CGI 塑料感。
- 因此 **Qwen-Image-2.1 不进 KF 主力席**，KF 席继续 Krea2+jman；Qwen 只保留「空镜/氛围片」侧路与低色价路径。
- 侧车形态：v0.42 独立侧车在 `K:\ComfyUICore`（与 8188 的 0.36 互不污染）。**当前 8199 未运行**——按需起，不常驻（起侧车=1 次 20s 级冷启，占卡与 8188 产批互斥，guard 只做 busy-hold）。

## 本机侧标签（避免重复劳动）

- 2026-10-24 有一条「POOL-0021 跑不通（VAE size mismatch / UNETLoader 认不出）」的记录，实测是**用错 VAE 配方**（拿 qwen_image_2.1_vae_bf16 走 WanVAE 架构加载）。正解就是 C2099 的 v0.42 侧车路线，已在 10-20 验证通过；该冲突记录作废，勿按它对 0.36 主环境动手。

## 建议动作

- `POOL.json` 的写手是 dispatcher（本机不写），请按本回执把 POOL-0021 翻 `done-closed-with-verdict`。
- 无需再烧任何 qwen21 帧。