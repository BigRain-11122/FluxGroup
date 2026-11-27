# visual 工位 BLOCKED 卡分诊（2026-11-13 23:4x · bm-c 工位席）

> 背景：v3 自驱循环开始消费 11-13 23:13 起自造的工序卡。六张卡执行过、工具真实、
> 但全部卡在「上游输入缺失」。按岗位书 §六「同一错误两次→停下写根因」，逐卡分诊如下。
> 巡检（station_agent）与主控可直接消费本文件。

## 逐卡根因与处置

### 1. SD-visual-PROD-MV-SINGLE-mv-kf —— 已修（转 DONE 路径）
- 根因：deliverable 指向 `30s-reel-v1/kf/`（空目录），而 mv0001 的 KF 早在 v4 时代已烧完，
  真实产物在 `30s-reel-v1/frames/`（KF1-10 + KFT，2026-10-10）。
- 处置：已发布 11 帧到 kf/ 判据目录 + 回执
  `rt/visual/receipts/SD-visual-PROD-MV-SINGLE-mv-kf-20261113-2313.json`（带 sha256）。
  下一轮 station_drive 验收即转 DONE。
- 后续：PRODUCTS 的 mv-plan 工序仍缺命令（建议接
  `python Tools/mv_emit_prompts.py --script <shots py> --out cph4/fleet/mv0001-handover/plan/kf_prompts.json`），
  41 曲线复用时的上游链才完整。mv0001 本身 KF 阶段已完成，无需再 emit。

### 2. SD-visual-PROD-MV-SINGLE-mv-cut —— 等素材定稿（不现在打通）
- 根因（实测 rc=2）：`mv_rebuild_from_edl.py` DRY 判 `CANNOT-BUILD-HERE`——73 行 timeline 里
  14 行源片不在本机 rebuild 源目录（S1-S10/T/SING3b/SIL4/Z02）。S1-S10 实际在
  `30s-reel-v1/fleet-shots/FLUXGROUP/`（12 件），rebuild 工具按自己的源目录找不到。
- 更重要的时序理由：**v729 三钉未定稿**——D03b 男主候选未选版、E04 表演 take 未烧、
  九重复槽差异化未做。现在硬装配出来的只会是旧素材重组，无交付价值。
- 处置建议：卡留 BLOCKED，等 v729 素材定稿后一并处理（源片归位 + v729 装配器差异化的
  重建已列在 v729 计划里）。判据 `full_mv_cut.mp4` 属 30s 契约路径，与 v72x 全长链的
  产物线不同——建议主控裁定契约口径（30s 契约 vs 全长产物线）。

### 3. SD-visual-PROD-SHORTVIDEO-TRACK-字幕 —— 跨工位依赖，等 audio
- 根因（实测 rc=3=BLOCKED 回执）：`subs_asr.py --in mix/master.wav` 的输入不存在。
  混音母版归 PROD-SHORTVIDEO-TRACK 的「混音」工序，owner_station=audio（bm-b），当前
  bm-b offline。本机 faster_whisper 1.2.1 在位，ASR 后端就绪，纯等上游。
- 处置建议：卡留 BLOCKED 等 audio 工位恢复产出混音母版。无本机可修项。

### 4-6. SD-visual-PROD-DRAMA-EP-assets / kf / assembly —— drama 线未立项，引导卡
- 根因：drama 线当前无实际项目（无 storyboard→kf_prompts 上游链，`out/drama/` 全空）。
  assets 卡 rc=3（drama_manifest 需要列素材的 dir 不存在）；kf 卡 rc=1（kf_prompts.json 不存在）；
  assembly 卡 rc=3（manifest 缺）。工具链（drama_manifest→job_kf_batch→drama_assemble）已接线，
  等 drama 线第一个实际项目立项+storyboard 产物落地即自然打通。
- 处置建议：三卡是供给引导卡（TOOL-PENDING 验证用），留 BLOCKED 或由主控择机关闭，
  待 PROD-DRAMA-EP 实项目开工后重开。

### 7. HO-ASSET-LORA-CH01-20261111 —— 训练家缺位，建议改派 bm-a
- 根因：`blocked_by: TRAIN_HOME（D:\FluxGroup-Offload\15-training）`——该路径在本机不存在，
  本机没有 LoRA 训练环境（musubi-tuner/sd-scripts 未装；11-09 判例在案）。
- 处置建议：CH01 林小满 LoRA 训练（15 图参考集已过闸）建议改派 **bm-a**——10-09 jman LoRA
  训练环境在彼（musubi-tuner + krea2_train_network 12GB 配方已验证）；或主控另派
  「bm-c 训练家安装」卡（需要 ~10GB 盘 + 安装窗）。参考集与规格：`HO-` 单原文 +
  `jman-lora-training-spec-v1.md` 复用速记。

### 8. asset-lib-asset-gen-scenes-2026-11-11 —— 在跑，等结果
- 23:18 已被 station_drive 重新 claim（租约 180 分钟），asset_gen 场景出图在执行中。
  等本轮回执；若再失败按 §六 写根因。

## 工位席结论
- 本工位命令面全部真实可跑；BLOCKED 集中在「上游产物/上游工位/训练环境」三类，
  均非本工位可单方修复项。
- 唯一新增自驱缺口=mv-plan 命令（见 §1 后续），其余七工序已接。（2026-11-14 注：主控 11:51 已接
  mv-plan 并实跑 DONE，kf_prompts.json 38 镜产出——该项闭合。）
- GPU 主线不受影响：v729 D03b 候选批（r3-lora）与 mv-i2v 批在 ComfyUI FIFO 正常消化。

## 增补（2026-11-14 12:53 轮观察·重造-挂起拉锯，机制面报主控）

- 主控 12:00 审计挂起五条零产出线后，station_drive 12:53 轮又按供给缺口**重造**了其中三张
  （SD-visual-mv-cut/字幕/drama-kf，新 id 带 -20261114-1253 时间戳）并重跑再 FAILED。
  形态=「主控挂起 → 自驱重造 → 再失败 → 再挂起」拉锯；单轮浪费极小（三工具几秒 fail-fast），
  但台账 FAILED 噪音持续，attempt/挂起语义被重造绕过（新 id 不继承旧卡冷却）。
- 根因定位（供主控修法参考）：station_drive 的 would_create 判定只看「PRODUCTS 命令在不在」
  （Tools/fleet/station_drive.py L298 附近），不看「该工序根因=上游缺」的历史事实——
  建议加一道「上游产物存在性前置」或「同产品同工序 24h 内 FAILED ≥2 则重造降频/需人工重开」闸。
- 本工位侧不自行改 station_drive 源码（机制工具归主控域），三卡的根因与等待条件见上表。
