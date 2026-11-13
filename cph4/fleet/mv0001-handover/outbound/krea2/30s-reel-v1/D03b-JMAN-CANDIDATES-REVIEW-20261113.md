# D03b 男主身份锁四候选评审记录（v729 · 2026-11-13 深夜 · bm-c 视觉工位席）

> 目的：v729 三钉之一「D03b 男主弃文字描述改 jman 身份锁」的候选产出与机器初审判读。
> **选版权归导演席+CEO 眼终审**（10-09 判例：自检分只作参考不作呈报依据）。

## 一、路线迭代史（三批，病根逐批定谳）

| 批 | 配方 | 结果 | 病根定谳 |
|---|---|---|---|
| v1 | 三官方参考图（ref_main_9+ref_close_1+ref_mv_91）+jman_v1_rank32 LoRA 0.9 | 4/4 FAIL（马赛克故障/双重曝光/字幕残影污染全候选） | **ref_mv_91 是 MV 91s 转场段截帧**，自带马赛克转场+双曝+卡拉OK字幕，EditPlus 参考流逐像素渗入生成 |
| r2 | 双参考（去 ref_mv_91） | 首验 FAIL（「周本倫」名字水印白字烧入+马赛克仍在） | **ref_main_9（范特西海报）自带名字水印**；ref_close_1 早在 10-09 LoRA 数据集时就因文字判弃——**三张官方真照全带污染，参考图路整体出局** |
| r3 | **纯 LoRA**（jman_v1_rank32 @0.9 + ID_BLOCK 骨相词 + D03b 场景词，无参考图） | **3/4 PASS，画面全干净** | 正路确认（mv_full_kf_r2.py 验证板同款配方） |

## 二、四候选终榜（r3-lora，种子 30972901-04）

| 候选 | 种子 | 机器判 | 关键读数 |
|---|---|---|---|
| c1 | 30972901 | **FAIL 52/100** | 下颌 V 型+碎中分刘海=韩系花美男吸引子（J-24 同族）；构图光位合格但身份不达标 |
| c2 | 30972902 | PASS 75/100 | 下颌钝圆达标、韩系感 2/10、构图 9/10、判负零 |
| c3 | 30972903 | PASS 86/100 | 下颌 8/10、骨相 43/60、构图四要素全过、判负零 |
| c4 | 30972904 | PASS **85/100** | **下颌钝圆 9/10（全场最高）**、骨相 48/60、构图 37/40（最高）、判负零 |

机器初审推荐序：**c4 ≈ c3 > c2**（c4 下颌与构图最优；c3 综合均分最高；两者都在可交付线）。

## 三、复现参数（正典）

- 工具：`Tools/kf_d03b_jman.py --refs none --tag r3-lora --strength 0.9`（纯 LoRA graph=graph_lora_only）
- 工作流：krea2_turbo_fp8_scaled + jman_v1_rank32（strength 0.9）+ qwen3vl_4b_fp8_scaled + qwen_image_vae；1344×768 / 8步 / euler simple / cfg 1.0 / seed=3097290N
- 提示词正身：脚本内 PROMPT（jman trigger + ID_BLOCK 骨相正典 + D03b 构图权威词——正面近景直视/右上琥珀硬侧光/两河浮雕楔形文字墙/Rembrandt split/5279 胶片颗粒 + 反韩锚 + NO_TEXT）
- 产物：`media/mv-album-001-jay/v729-candidates/r3-lora/`（gitignored 产物区）
- 看板：`cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/publish_assets/D03b-jman-LOOKBOARD-r3-20261113.jpg`（入仓）
- 归档：v1/r2 污染候选隔离在 `v729-candidates/{refs-v1-mv91-polluted, r2}/`（零删除留痕）

## 四、遗留与建议

1. **选版待导演席+CEO**：本记录是机器初审，非终审（CEO 眼感门 >7 由 CEO 定）。
2. **LoRA 收敛力注意**：本批用的是 jman_v1_rank32（orders 简称）；mv_full_kf_r2 验证板正身是
   `jman_v1_640_rank32_final`。c1 的韩系漂移提示 rank32 版收敛力弱于 640 版——
   若导演席对 c3/c4 仍判「不像」，r4 备选=换 640_final 权重 + 下庭强化词（面中部脂肪感/厚平刘海盖眉）
   + 左侧轮廓光补亮（c4 单眼皮验证度扣分项）。
3. **参考图资产债**：三张官方真照全带污染（水印/特效/文字）——若未来要走参考图路，需先洗图
   （裁水印区/取无特效段），已入坑录（2026-11-13 判例）。
4. **v729 后续链**：D03b 定版后——新 KF 进 timeline → E04 表演 take 重烧（i2v）→ 九重复槽
   剪辑语言差异化 → 装配（mv_rebuild_from_edl.py 源片归位 14 件）→ 交付闸。
