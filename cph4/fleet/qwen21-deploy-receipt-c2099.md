# POOL-0021 leg-1/leg-2 回执 — Qwen-Image-2.1-Turbo int8 部署 + 冒烟（bm-c C2099 窗）

> receipt id=qwen21-deploy-c2099 · 2026-10-20 01:5x · 执行席=bm-c 交互窗（CEO 全负荷令 O-20261019-1935 当窗执行）
> 卡=POOL-0021（P2·gpu-production·KF 提速验证批）· leg-1=四件权重 · leg-2=专属节点侧车 + 1024² 冒烟

## 一 结论（一句话）

**四件权重齐（字节+头双验）· v0.42 侧车在 8199 立起（生产 8188 零改动）· 1024² 8 步冒烟 PASS：含冷加载 41.4s，显存峰 14841MB（空显存 15273MB 起）· 出图质量 7/10（几何类弱项，见 §五）。**

## 二 leg-1 权重（四件全齐）

| 件 | 落点 | 字节 | 校验 |
|---|---|---|---|
| DiT turbo int8 | `models/diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors` | 7,256,787,829 | 期望字节恒等 + safetensors 头 JSON 合法 |
| TE w4a8 | `models/text_encoders/qwen3vl_8b_w4a8.safetensors` | 6,312,105,364 | 同上 |
| VAE bf16 | `models/vae/qwen_image_2.1_vae_bf16.safetensors` | 675,509,688 | 同上 |
| turbo LoRA | `models/loras/qwen_image_2.1_turbo_lora_avg_rank_178_bf16.safetensors` | 913,314,512 | 同上 |

- 正式判定件：`media/qwen21-deploy/weights_verdict_c2099.json` = **OK 4/4**
- **勘误**：c2094 runner 收尾写的 `QWEN21-WEIGHTS-END PARTIAL 3/4` 是中途快照——DiT 在后续守卫续跑中于 **01:21:46** 补齐到完整字节（5 次重试确实死了，但续跑腿把它补上了）。按「盘面终态优先」律（10-17 r1058 判例）以本件为准。

## 三 leg-2 侧车（v0.42，端口 8199）

- **为什么不用主服务**：生产 8188 跑 v0.36.0，H3 i2v / 星晴 KF / S7R 画质链全压在上面；Qwen-Image-2.1 专属节点 `TextEncodeQwenImage21` / `QwenImage21Cache` 在 0.36 不存在（object_info 实测），升级主服务=拿整条产线冒险。bm-b 先例（v0.40 并行便携版 8199）照走，改为**核心在 K 盘、解释器共用生产便携 python**（少一份 torch）。
- 部署物：
  - `K:\ComfyUICore\ComfyUI\`（git clone `Comfy-Org/ComfyUI` **v0.42.0**）
  - `K:\ComfyUICore\extra_model_paths.yaml`（共享生产权重树，零拷贝）
  - `K:\ComfyUICore\c2099_sidecar_boot.py`（引导器：把侧车根置顶再跑 main，解决 `app` 包被生产树抢先解析）
  - `K:\ComfyUICore\custom_nodes\`（空目录，v0.42 启动必需）
- 解释器侧改动（可逆）：`D:\ComfyUI\python_embeded\python313._pth` 加一行 `K:/ComfyUICore/ComfyUI`（**生产树仍排第一**，全部既有 runner 零回归；备份 `python313._pth.bak-c2099`；补丁脚本 `K:\Fluxgroup\.codely-cli\c2099_pth_sidecar.py`）。另装了 v0.42 要求的锁定包：`comfyui-frontend-package 1.55.18 / comfy-kitchen 0.2.39 / comfy-aimdo 0.5.6 / comfyui-embedded-docs 0.5.14`（生产 0.36 兼容，冒烟与侧车均正常）。
- **常驻治理**：`bmc-SidecarGuard` 每 10 分钟（task-register 正门·隐藏链·S4U 被 UAC 降级 InteractiveToken 并入积压账）：不在 → 无窗拉起；在且队列空 → `POST /free` 回基线；CEO 暂停旗=零动作（按 `pause` 行首判，`resumed` 不拦）。实测：`action=idle-free`，显存回落 **2319MB**。
- 组成：`cph4/fleet/idle-guard-kit/sidecar_guard_c2099.py`

## 四 冒烟三账（1024²·8 步·cfg1·euler/simple·turbo LoRA 1.0·Cache auto/default）

| 账 | 实测 |
|---|---|
| 速度 | **41.4s**（含冷加载；bm-b 8G 同栈热跑 20s/张） |
| 显存 | 基线 2245MB → 峰值 **14841MB**（16GB 卡内；/free 后 15207MB 空闲） |
| 质量 | **7/10**（光影/景深/氛围过关；弱项=器物内部几何：卷盘不对称、底部卡槽/螺丝「融化」、木纹偏涂抹） |

- 产物：`media/comfy-sidecar/smoke/qwen21_smoke_1024_s991001.png` + `qwen21_smoke_receipt.json`
- 运行件：`cph4/fleet/idle-guard-kit/qwen21_smoke_c2099.py`

## 五 判读与下一步

- **能力面**：Qwen-Image-2.1 走 v0.42 侧车可用；适合「场景/道具/氛围类 KF 与静物特写」的提速试验，**不适合**需要器物精确几何、标签文字或人脸的镜头（ID 脸面仍走 Krea2+jman 道，规格原文禁区照旧）。
- **对比三账的下一腿**（POOL-0021 剩余项）：同提示词 Turbo vs Krea2 turbo 同板对照 + 回填 R-20261019 §五应用表——**尚未做**，列下轮 bank 活。
- **许可**：Qwen-Image-2.1 为 `qwen-research` 非 Apache，试烧合法、量产采用前须读全文出判定行——**本窗未出判定行**，随对比批一并提交。
- **并发约束**：侧车空闲时自动让出显存，但**烧批进行中会与 8188 抢卡** → 侧车批只允许在 8188 队列空档跑（guard 的 busy-hold 分支只保护侧车自己，跨服务互斥需调度侧保证）。本窗冒烟即为唯一在跑批。

——
执行席=bm-c C2099 · 2026-10-20 01:5x

## 对比定谒（C2108 收割轮·盲读板定谒）2026-10-20 02:02

- 证据：`media/comfy-sidecar/compare/QWEN21-vs-KREA2-board-c2099.jpg` + `compare_receipt.json`（3 题同种子对拍：sky / cassette / dusk；qwen 1024 native，krea 1344x768；串行、每轮 /free）
- 耗时/显存：qwen 64.5s / 192.2s / 125.8s（峰 15848MB）；krea 94.7s / 97.8s / 44.6s（峰 15729MB）
- 盲读结论：**Krea2 胜 ~2.5/3 行**。Qwen 仅在“星锦链可读性”一行占优；cassette 硬表面“熔蜡”、dusk 人体轮廓糊成一团（头肩相融/IT肢体相融）；优点=情绪调色与光影氛围真实（dust motes 最佳），不足=胶感偏塑料 CGI、细节几何不稳。
- 定谒：**Qwen-Image-2.1 不接管 KF 生产主力席**（仍 Krea2+jman），只取其“空镜/氛围垫片”侧路与后期调色参。POOL-0021 leg-2 探针已得可判定文字证据，可关节点。
- 遗留：v040 可携包阶段下载 leg 已废（0.40/0.40.0 两 tag 均 404），现役侧车=v0.42.0 git clone（K:\ComfyUICore），无需可携包。
