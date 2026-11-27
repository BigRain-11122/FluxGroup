# 素材取料清单与通道协议（BigStream 漫剧/短剧 · 2026-11-20 bm-c 实测）

> 制=bm-c。回答「素材在哪、能不能拿到、拿不到怎么办」。
> 配套：`BIGSTREAM-LINE-MAP-v3.md`（产线总图）。

---

## 一、本机盘上现有（可直接开工·实测）

| 类 | 内容 | 量 | 证据 |
|---|---|---|---|
| 剧本正身 | `cph4/fleet/drama-001-stockera/episodes/EP001..060.json` | 60 集 | 目录 123 件 |
| 世界观 | `BIBLE.md` / `GUARDRAILS.md` / `SEASON1-ARC.md` | 3 件 | 在位 |
| 角色 LoRA | `jman_lora_v2`(162.6MB) · `jman_v1_640_rank32_final`(0.44GB) | 2 个 | `media/mv-album-001-jay/lora-out/`、`D:\ComfyUI\...\loras\` |
| 资产库 | faces 296 / characters 106 / scenes 12 / props 20 / styles 3 / typography 4 / motions 15 / transitions 10 | **841 件 / 505.7MB** | `media/asset/` |
| 出图模型 | animagine-xl-4.0 · DreamShaperXL_Lightning · krea2_turbo_fp8 · qwen_image_2.1_turbo_int8 · qwen_image_2512_fp8+2步LoRA | 5 套 | `D:\ComfyUI\ComfyUI\models\` |
| i2v 模型 | minimax_h3 int4/int8 + turbo 4step · **Wan2.2-TI2V-5B-Q4_K_M (3.2GB)** | 3 套 | 同上 |
| 音频 | piper + `zh_CN-huayan-medium.onnx` · edge_tts · faster-whisper-small | 3 条 | `.tools\piper-voices\`、`media\voicebank-models\` |
| 工具链 | drama_kf_plan / drama_kf_batch（本窗新建）· drama_assemble · drama_quality_gate · drama_manifest | 在位 | `Tools/fleet/` |

**结论：本机不缺"能开工"的素材**，缺的是**已渲染成片原件**（见 §三）。

---

## 二、通道矩阵（本机→他机·实测 2026-11-20）

| 通道 | 状态 | 容量 | 实测依据 |
|---|---|---|---|
| `git`（ssh.github.com:443） | ✅ 通 | 单件 <95MB，整批 <200MB | `ls-remote` 4.1s；fetch ~25KB/s 慢但在跑 |
| FleetLink `/poke` | ✅ bm-a:8790 | **只传信号，不传数据** | `/health` 返回 `{"ok":true,"node":"bm-a","version":"1.9.7"}` |
| FleetLink `/sync` | ✅ | ≤256KB/件（base64+gzip 后） | 与 `/poke` 同一监听器 v1.9 |
| SMB 445 | ⚠️ 端口应答 | 未授权 | `net view \\100.110.185.62` 空输出 |
| SSH 22 | ❌ bm-a 关 | — | Test-NetConnection False |
| ComfyUI 8188 / 服务 8090 | ❌ bm-a 关 | — | 同上 |

**判据**：机队**没有可用的大件（视频/权重）通道**。上一版记录「SMB/WinRM 关闭」在 2026-11-20 仍成立，只是 445 端口本身应答。

---

## 三、他机素材与可取性

| 件 | 所在 | 量 | 取法 | 状态 |
|---|---|---|---|---|
| **60 集成片** `media/drama-eps/EP001..060.mp4` | **bm-b** | 540×960/25fps/无音轨·4489s | 无通道（tailscale offline **9 天**） | ❌ 待 bm-b 复机 |
| 60 集 KF 原件 `media/drama-eps/eps-kf/` | bm-b | 每集 ~20 张 | 同上 | ❌ |
| GPT-SoVITS 安装 + 音色库 | bm-b | `C:\Fluxgroup\...\media\drama-tools\GPT-SoVITS` | 同上 | ❌ |
| MV v729 产物 | bm-a | 视频 | 无大件通道 | ⚠️ 只能要清单/小件 |
| drama 样片 `drama-sample-v1.mp4` (12.2MB) | **本仓 git** | 1 件 | git | ✅ 已在本地 |

---

## 四、处置决定（不是"等素材"）

**原则（承 CHAIN-BLUEPRINT §五 + CEO「别等」令）**：素材缺失不等于产线停摆——**能重建的就地重建**，只有"原件本身即证据"的（成片/签字档）才必须搬。

1. **60 集剧本在 git → 本机可完整重烧**。已实测：D3 生成器 + 烧制器打通（EP001 两镜 20s/帧·832×1472）。
   即：**不需要等 bm-b 的成片**，本机可以按新规格（1080×1920/30fps/带音轨）重出 60 集。
2. **bm-b 的成片仍要拿**——它是 v1 版本证据（回归/对比/判例），不是生产输入。等复机后走「bm-b 自建 HTTP 共享窗口」或「打包分卷随 git 小件」。
3. **bm-a 的 MV 素材不阻塞漫剧线**——两线共用的是角色 LoRA（本机已有）与判例（本机已有）。
4. **音色库**：本机先用 piper 单音色出片验证链路；多角色配音等 bm-b 或本机自建（GPT-SoVITS 可本机装）。

---

## 五、对 bm-a / bm-b 的取料请求（已落 inbox）

- `inbox/MSG-20261120-2240-bmc-drama-material.md`：
  - 致 bm-a：要 (a) drama 相关件清单（路径+字节数）；(b) 若 ≥1MB，请在 8790 起一个只读 `/get?p=` 端点或临时 HTTP 端口供本机拉取。
  - 致 bm-b（复机后）：60 集成片 + eps-kf 原件 + GPT-SoVITS 音色清单；同样走 8790 只读端点或分卷。

---

## 六、复验判据

1. `python Tools/fleet/drama_kf_plan.py --eps all` 一次产出 60 集 prompt 表（已验证单集 21 镜）
2. `python Tools/fleet/drama_kf_batch.py --ep 1` 全镜出图（冒烟 2 镜已过）
3. 任意他机件取回后，`sha256` 与来源回执一致
4. bm-b 复机 24h 内 ≥1 件取回或已明确不可取原因

—— bm-c · 2026-11-20
