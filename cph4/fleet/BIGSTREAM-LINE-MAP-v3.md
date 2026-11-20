# BigStream 自媒体产线总图 v3 — 五线 × D0-D9 九站 × 实测接线

> 制=bm-c（漫剧/短剧专职机）· 2026-11-20 · 全部条目以**本机盘上实测**为证，不抄记忆。
> 位次（查重律·只补缺不重立）：
> - 公司顶层设计 v1 = `company/bigstream/TOP-DESIGN-v1.md`（**§8 现状差距表由本件 §四 取代**）
> - 漫剧工作流正典 v1 = `drama-dept-v1/DRAMA-PRODUCTION-SYSTEM-v1.md`（十站链/精度阶梯/QC 闸，**结构保留不动**）
> - 漫剧改造案 v2 = `drama-dept-v1/REBUILD-PLAN-v2.md`（双轨换轨：仿真人短线 / Blender 3D 长线）
> - 机队链体检 = `CHAIN-BLUEPRINT-v1.md`（供给→领取→执行→验证→交接→回收）
> - 产品工序注册 = `PRODUCTS.json`（PROD-DRAMA-EP / PROD-DRAMA-AUDIO / PROD-DUANJU-AUDIO）
> 本件回答三个问题：**这条产线由哪几条线组成、每站现在真的能跑吗、素材在哪。**

---

## 一、五条线（同一骨架·五个变体）

| # | 线 | 形态 | 现状 |
|---|---|---|---|
| L1 | **MV** | 单曲横屏 3-5min·K 帧+i2v·原曲配歌 | 在产（v729 交接/签字链） |
| L2 | **AI 漫剧** | 竖屏 60-90s×80-120 集·面板+微动效+配音 | 60 集 v1 已出（bm-b 盘上）·目标档未达 |
| L3 | **AI 短剧** | 竖屏同构·写实 KF+i2v 真人感 | 立项/试点脚本已备·零成片 |
| L4 | **短视频** | 竖屏 14-15.5s 热点梗·旁白+BGM | 有 V1/V2 成片（meme-daily） |
| L5 | **视频二创** | 授权池素材重剪 | 有规格与调研·零成片 |

**关键结论（承 TOP-DESIGN-v1 §1，实测复核仍成立）**：L1/L2/L3 **是同一条链**（关键帧→i2v→剪辑→配音→字幕），差异只在画风底座、时序引擎、音频来源、一致性强度。所以本总图只画一套骨架，五个变体在表里标差异。

---

## 二、九站骨架（D0-D9）与每站闸

| 站 | 动作 | 产物 | 闸（机器可测） |
|---|---|---|---|
| D0 | IP 包（定选/世界观/题材预审） | BIBLE + 合规预审 | 题材 11 项红线 + 投资额底稿 |
| D1 | 拆集剧本 | `episodes/EP*.json` | 钩子三件套 + 因果链 10 问 |
| D2 | 分镜卡 | 每镜`detail_en`+`dur`+`fx`+`card` | 四案齐备（画风/音色/节奏/预算） |
| D3 | 关键帧面板 | `kf/<shot>.png` | 帧审签章 + 伪文字机核 |
| D4 | 动效/i2v | `i2v/<shot>.mp4` | 崩坏六检（morph/伪文字/物理/匀速/首帧保真/速度线） |
| D5 | 口型/表演 | 表演版 clip | 口型对位抽检 |
| D6 | 配音/音效/BGM | `audio/*.wav/mp3` | 音画对位 + 响度 |
| D7 | 装配 | 成片 mp4 | `drama_assemble.py` 规格断言 |
| D8 | 成片闸 | qa.json | `drama_quality_gate.py` 七条 + 盲评 |
| D9 | 发布/复盘 | 发布件+台账 | AIGC 三标识 + 备案 |

---

## 三、五线差异矩阵

| 维度 | L1 MV | L2 漫剧 | L3 短剧 | L4 短视频 | L5 二创 |
|---|---|---|---|---|---|
| 画幅/时长 | 横屏 3-5min | 竖屏 60-90s | 竖屏 60-90s | 竖屏 14-15.5s | 竖屏 15-60s |
| 视觉底座 | 写实 KF 1344×768 | **漫画面板**（9:16） | 写实 KF（9:16） | 现实感 KF | 原素材 |
| 时序引擎 | 乐句卡拍 | **台词驱动**（3s 钩/30s 爆/悬念） | 同漫剧 | 五拍结构 | 素材节奏 |
| 音频 | 原曲（禁 AI 音轨） | 配音+音效+BGM | 同漫剧 | 旁白+BGM | 原声+配乐 |
| 一致性 | 跨镜脸锚 | **跨集资产锁版**（三视图+LoRA） | 同漫剧 | 单条 | 低 |
| 动效 | i2v 一镜一动作 | 微动效为主+关键镜 i2v | i2v 为主 | i2v | 剪辑 |

> 承 TOP-DESIGN §10 铁律：**禁 Ken Burns 推拉静图**（v1 路线曾被 CEO 判「不是运镜」）；不用短视频转场语法（白闪/抽帧抖动/贴纸）。

---

## 四、接线实测表（本机 bm-c·2026-11-20）

**判读口径**：✅已接线=命令在仓且本机可直接跑；⚠️半接线=有脚本但路径/参数写死他机；❌未接线=无人产该产物。

| 站 | 漫剧/短剧 | 实测证据 | 判 |
|---|---|---|---|
| D0 IP | `drama-001-stockera/BIBLE.md`+`GUARDRAILS.md` 在盘 | 两件在位 | ✅（静态） |
| D1 剧本 | `episodes/EP001..060.json` 60 集全在盘（schema=`ep/title/shots[n,dur,kind,ids,detail_en,sub,speaker,fx,card]`） | 目录 123 件 | ✅ |
| D2 分镜 | 分镜卡=EP json 内的 `detail_en`+`dur`（无独立工序） | 同上 | ✅（内嵌） |
| D3 关键帧 | `job_kf_batch.py`→`mv_kf_batch.py` 在盘，但输入 `cph4/fleet/out/drama/kf_prompts.json` **不存在**，全仓无该文件生成器 | `out/drama/` 整目录不存在 | ❌ **断点#1** |
| D4 i2v | `local-i2v/h3_i2v_album.py` 有 `--manifest/--out/--width/--height/--wf`（可泛化）；但 manifest 生成器只服务 MV 专辑 | 无 drama manifest | ⚠️ 缺 manifest 桥 |
| D5 口型 | LatentSync 本机在册（media/latentsync*） | 目录在位 | ⚠️ 未接 drama |
| D6 配音 | 本机 `piper`+`zh_CN-huayan-medium.onnx`+`edge_tts`+`faster_whisper` 全可用；GPT-SoVITS 只在 bm-b | `K:\Fluxgroup\.tools\piper-voices\` | ⚠️ 单音色可跑 |
| D7 装配 | `Tools/fleet/drama_assemble.py`（1080×1920/30fps+loudnorm -14+烧字幕） | argparse 三参齐 | ✅ |
| D8 QC | `Tools/fleet/drama_quality_gate.py`（七条硬指标） | 在位 | ✅ |
| D9 发布 | 无账号/无授权（CEO 保留面） | — | ❌（合规封存） |

**产线物理足迹**：`cph4/fleet/out/drama/` **整目录不存在**——PRODUCTS.json 里 9 站的 outputs 全部落空。这不是「跑得慢」，是**工序注册了但没有第一次点火**。

---

## 五、断点清单（按阻断严重度）

| # | 断点 | 根因 | 处置 |
|---|---|---|---|
| 1 | **D3 无 prompts 生成器** | 剧本→KF prompt 这一步从来没有工序；每集靠人工/一次性脚本 | 建 `drama_kf_plan.py`（EP json→kf_prompts.json，含 77-token 预算压缩与结构化 token） |
| 2 | **D4 无 drama manifest 桥** | i2v runner 吃 MV 专辑的 manifest 格式，drama 没有生成器 | 建 drama manifest（kf png+win_s+i2v_prompt→units） |
| 3 | **三条线共用一组输出目录** | PROD-DRAMA-EP outputs 写死 `out/drama/*`，60 集与样片同树 | 按 `out/drama/<episode>/` 分集建树 |
| 4 | **素材无大件通道** | git 禁大件、FleetLink /sync ≤256KB、bm-a 仅 8790 开放、bm-b 离线 9 天 | 见 §六 |
| 5 | **D6 音色库单薄** | 本机只 piper 单音色；多角色配音依赖 bm-b GPT-SoVITS（离线） | 先用 piper 多参数+edge_tts 兜底，多角色排期等 bm-b |

---

## 六、素材三处分布与通道现实（实测）

| 处 | 有什么 | 通道 | 能否取 |
|---|---|---|---|
| **git 仓** | 剧本正身 60 集/部门正典/工具/资产索引 | `git fetch`（ssh.github.com:443） | ✅ 可取（本次实测 ~25KB/s，3388 objects） |
| **本机盘** | 资产库 841 件/506MB（faces296·characters106·scenes12·props20·styles3·typography4·motions15·transitions10）+ LoRA `jman_lora_v2`/`jman_v1_640_rank32_final` + 模型全套 | 本地 | ✅ 已在本机 |
| **bm-a** | MV v729 产物、样片线；在线 | 仅 8790（FleetLink，/health+/sync 小件）；22/8090/8188 关；SMB 445 应答但匿名不可列 | ⚠️ 只能小件 |
| **bm-b** | **60 集成片 `media/drama-eps/EP001..060.mp4`**（4489s）+ GPT-SoVITS + drama-tools 真身 | tailscale offline **9 天** | ❌ 不可取 |
| **bm-m / bm-m-1** | 主控；bm-m 离线 22 天，bm-m-1 在线 | — | ⚠️ |

**结构性事实**：机队**没有可用的跨机大件通道**。视频/权重这一级素材只能靠「本机重烧」或「目标机自建」。所以「拿素材」的正确解法不是搬文件，是**搬可重建的源**（剧本 JSON/prompt 表/种子/配方）——这正是 `drama-001-stockera/episodes/` 已经在 git 里的原因。

---

## 七、本机（bm-c）角色与排程

- **角色**：漫剧/短剧 视觉底座主产机（KF+i2v+装配+QC 全链本地）。
- **硬件实测**：RTX 3070 16GB（当前 free 16.0GB·GPU 1%）、ComfyUI 8188 已起。
- **模型在位**：`animagine-xl-4.0`(SDXL 动漫) / `DreamShaperXL_Lightning`(8步) / `krea2_turbo_fp8`(12.2GB) / `qwen_image_2.1_turbo_int8` / `qwen_image_2512_fp8`+2步 LoRA / `minimax_h3` int4+int8 / **`Wan2.2-TI2V-5B-Q4_K_M`(3.2GB·轻量 i2v)**。
- **音频**：piper(zh_CN-huayan) / edge_tts / faster-whisper。
- **排程**：主控派卡最高优先；无卡时漫剧线自驱（D3→D4→D7→D8 串行单批）。

---

## 八、红线（不重述·只引用）

`drama-dept-v1/INDEX.md §四` 全量继承：微短剧备案 · AIGC 三标识 · 自有 IP 优先 · 禁真人肖像/声音参考 · 创作过程留痕 · BGM 正版池。另承 TOP-DESIGN §7 停线条件：连续 7 天无新成片 → 停线自查。

---

## 九、复验判据（可跑）

1. `cph4/fleet/out/drama/<ep>/kf_prompts.json` 存在且 `len(json)==镜数`
2. `kf/*.png` 张数==非 card 镜数
3. `i2v/*.mp4` 逐镜存在且 `ffprobe` 时长≈`dur`
4. `drama_quality_gate.py` 七条全 PASS
5. `quality_gate.py --line bigstream-drama` 四闸 PASS

---

## 十、接线补丁（不改共享注册表·待合批执行）

本窗**没有**改 `PRODUCTS.json`——本机落后 origin/main 494 提交且在公共注册表上并发编辑会撞车。补丁如下，由合批窗执行：

```json
// PROD-DRAMA-EP
"stages": ["script","assets","storyboard","kf-plan","kf","i2v-plan","i2v","audio","assembly","qc","publish"],
"outputs": {
  "kf-plan":  "cph4/fleet/out/drama/EP<nnn>/kf_prompts.json",
  "kf":       "cph4/fleet/out/drama/EP<nnn>/kf/",
  "i2v-plan": "cph4/fleet/out/drama/EP<nnn>/i2v_manifest.json",
  "i2v":      "cph4/fleet/out/drama/EP<nnn>/i2v/"
},
"commands": {
  "kf-plan":  "python Tools/fleet/drama_kf_plan.py --eps <nnn>",
  "kf":       "python Tools/fleet/drama_kf_batch.py --ep <nnn>",
  "i2v-plan": "python Tools/fleet/drama_i2v_plan.py --ep <nnn>",
  "chain":    "python Tools/fleet/drama_ep_chain.py --ep <nnn> --stages plan,kf,i2v-plan"
}
```
`pending_stage_reasons.i2v` 改写为：manifest 桥已补（`drama_i2v_plan.py`），剩余限制=单镜 ≤10s（16GB 卡实测墙）。

—— bm-c · 2026-11-20
