# CAMERA-DIRECTION-v1 — 导演级运镜提示词语法正典（「不要只是简单的运镜，AI感强烈」根治）

> 溯源：CEO 令 2026-10-12 11:2x「**不仅要决策，还是要去研究导演拍摄的运镜提示词，好好改善，不要只是简单的运镜，AI感强烈**」（承接 CEO-FEEDBACK-fullmv-fix-20261011.md §一⑤「运镜/角色动作不自然」+§五⑨⑩ 提示词工程总攻）。
> 定界：本件管**镜内**（一个 5s take 里相机与主体怎么动）；**剪辑层**运动感预算归 ERA-MV-GRAMMAR-v1.md L6（景别跳切+动势衔接）——双正典同日互锁：L6 管剪点，本件管镜内。
> 验证声明：A=我方 44 镜运镜行逐镜统计（§二·本窗直查）+运镜四定律（R-20261008-mv-craft-deep-01·匀速禁令/zoom≠dolly 视差律/动机律/hold 律）+H3 实测判例（静态微动特写 8.5 分=安全区·人物复杂动作 4 分=崩区）+原版拉片（固定机位 12/12·「邝盛固定机位极缓推+全场硬切」）；B=MiniMax 官方提示词指南（movement type+amplitude+speed 三维·PROMPT-SPEC §五既有证据链）+Seedance 官方（单镜单运镜红线+低缓连续小动作优先+禁精确秒数）；C=H3 相机提示词外部工艺三源（visible destination 目的地取景法/camera-subject separation 相机主体分离/conflict fix 冲突修复+小弧≤20°+dolly zoom 高危实验档——minimaxh3.tv / minimaxh3videogenerator.com / minimax3.org·2026-09 刊行·未实测转述如实标 C）。零编造。

## 一、病灶定性（CEO 判负原文拆解）

「不要只是简单的运镜，AI感强烈」= 运镜面两大 AI tell：

1. **平速 tell**：移动镜全部单速档——`at slow speed` 写死匀速。匀速线性=机器感（「现实没有东西匀速运动，线性=僵硬业余」·R-01 定律①多源）——CEO 匀速终裁（10-10「匀速=最大 AI 感」）当时只落了剪辑变速面，**运镜提示词层=漏网面**，本次补齐。
2. **无灵魂 tell**：移动无动机（相机自己动不回答画内事件）、无操作质感（完美云台滑行=AI 签名）、无到站（动了不知道为什么停）——导演视角缺位，提示词退化成「运镜类型名词+幅度副词」的参数表。

## 二、我方 44 镜病灶实测（本窗逐镜统计·A 级）

| 统计面 | 实测值 | 判定 |
|---|---|---|
| 静态/近静态镜 | 21/44（47.7%） | **保留**（固定机位=年代正解·L6 全绿项） |
| 移动镜 | 23/44（52.3%） | 升级主战场 |
| 平速语（at slow/very slow/steady speed） | **23/23 移动镜=100%** | 全判负 |
| 速度曲线（缓入/缓出/到站收束） | **0/44** | 全缺 |
| 动机绑定（相机回答画内事件） | 2/44 弱（INT3 配速·C07 半句） | 全缺 |
| 目的地取景（移动有可见终点） | **0/44** | 全缺 |
| 复合运镜（双轴一体） | 1/44（C07） | 单轴依赖 |
| 操作质感（手持呼吸/dolly 微颤/机身 flinch） | **0/44** | 全缺 |
| 镜头行为（rack focus/焦点转移） | 0/44 | 全缺（高级感丢了一整层） |
| 尾句自毒 | I2V_TAIL「Restrained continuous motion」=平速总指令 | 判负改写 |

## 三、导演级运镜五槽语法（正典公式·替换旧「三维公式」）

**一句运镜 = 五件事**（H3/Seedance 通用骨·措辞分轨见 §四）：

**MOVE 动作+目的地 → CURVE 速度曲线 → MOTIVE 动机 → TEXTURE 操作质感 → ALIVE 画内活体**

| 槽 | 定义 | 词面例 |
|---|---|---|
| ① MOVE+目的地 | 一次移动要有**可见终点**（"by the end of the shot, the viewer should notice ___"·C 级外部工艺）；dolly≠zoom（dolly=视点位移=前景快于背景的视差；zoom=平面放大零视差=廉价） | `eases toward his profile on a slow dolly ... settling once the fresh band fills the lower frame` |
| ② CURVE | 一切移动**缓入缓出**（>400ms 自然默认曲线）；三段式：几乎静止起步→gather 起势→到站 settle | `eases in from almost still, gathering pace gently, settling as it arrives` |
| ③ MOTIVE | 每镜答「**此运镜主张什么**」——移动必须被画内事件触发或追随（她的目光/他的抬眼/灯逐盏醒/焰沉/光缝滑行）；无动机推近=设备宣告存在（del Toro） | `as his heavy-lidded eyes lift from the half-cut row` |
| ④ TEXTURE | 2001 台面三态：脚架 locked-off / 地轨 dolly（faint handmade tremor under the glide）/手持（breath-sway）；冲击帧=机身 flinch 一次——**现代云台完美平滑滑行=AI tell** | `a slow floor dolly with a faint handmade tremor under the glide` |
| ⑤ ALIVE | 静镜不屏保：灰尘/烟/发丝/焰呼吸/倒影漂移至少一件在动；**相机-主体分离纪律**：谁在动明写（"the carved goddess holds still while she passes"） | `dust motes turning in the lit air` |

**三大铁律复引**（R-20261008-mv-craft-deep-01·全保留）：①匀速禁令 ②zoom 禁令（镜内推近一律 dolly 语）③**每镜限一动作**（模型对双动作二选一实锚·dolly zoom 高危）+④hold 律（移动末定持让移动有意义·5s 段慢移域 800-1200ms）。

## 四、引擎分轨（能力边界·实测背书）

| 面 | H3（云端 Context-IR/本地） | Seedance 2.0/2.5 |
|---|---|---|
| 结构 | 官方三字段长文（I2VA·结构化自担预处理） | 中文八要素 60-100 词 |
| 运镜红线 | 每镜限一动作；orbit 只许 **≤20° 小弧**（完美整圈=AI 签名）；dolly zoom=高危实验档慎用 | **单镜单运镜**（官方原话「同时要求推拉摇移会增加画面不稳定性」）+低缓连续小动作优先+禁精确秒数 |
| 实测判例 | 静态微动特写 8.5=安全区；人物复杂动作+光效 4 分=崩区 | 情绪外化+动作量化（缓慢抬手/快速转头） |
| 五槽装法 | 五槽全上（结构化长文承载得动） | 并入「镜头运镜」+「动作细节」两要素：一动作+曲线词+动机短语+质感短语 |

**互补律（本件新立）**：主体复杂→镜头简单；镜头动→主体简单。两复杂叠加=H3 崩区（女神显影 4 分判例）。**动作镜正解=锁机+物理链全在主体（预备-发力-余势）+机身带一帧 flinch**，不是 crash zoom。

## 五、年代对齐（与 ERA-MV-GRAMMAR L6 合流）

- L6：运动感预算在**剪点**不在**镜内**——镜内运镜=克制律维持：本片 static 21 镜打底，移动 23 镜全 small-to-medium 幅度+极缓域。
- 年代签名：**2001 台面无云台无电控滑轨**——dolly 一律写 floor dolly、脚架一律 tripod，词面即年代正确；手持呼吸只给情绪最近镜（C01/D02/E03 级），不全面铺（90s 手持入抒情段=血统来源·B 内源）。
- 镜头行为层（rack focus/焦点转移）=年代正确的高级感来源：原版固定机位下全靠景别跳切与焦点讲故事——本片玻璃双世界镜以焦点转移替代机位运动（§六·型5）。

## 六、镜型配方五型（标准句式·全曲 44 镜已按此重写）

1. **情绪脸镜**（L2 主力·H3 安全区）：`the camera holds a locked-off tripod frame while [微表演物理链: her hair swinging with the turn and settling / his shoulders settling lower breath by breath], the light [breathing / holding her face]` ——相机死稳，活体全在主体。
2. **物件/文物镜**：`the camera eases [toward / along] X on a slow floor dolly, [曲线三段], [motivated by 光事件], settling once [目的地取景]` + dust/smoke 活体。
3. **动作镜**（凿击/笔刷/挖掘）：`the camera holds a locked-off tripod frame as [动作物理链 lands early in the take], the frame flinching once with the strike` —— 主体扛动作+机身带惯性（互补律）。
4. **空间大景镜**：`the camera [retreats / rises] in one slow dolly move as [世界事件], easing out once [目的地构图]` ——复合仅限单一体 rig 手势（retreat+rise 同机一体）。
5. **玻璃双世界镜**（本片签名机位）：locked + **rack focus beat**（`the sharpest point passing from the ancient cut to her skin`）+ 两光互相 breathing ——镜头行为替代机位运动。

## 七、禁词面（lint FLAT 门执法·本批已代码化）

- `at slow speed / at very slow speed / at steady speed`（平速标记）→ prompt_lexicon lint **video 模式新增 [FLAT] 命中**（同病不二犯=落闸律）。
- 完美整圈 orbit / arc>20° / 云台 glide 词面（smooth gimbal）——一律不写。
- 旧 I2V_TAIL「Restrained continuous motion, camera and subject motion only」→ 判负改写为「**Every motion eases in and settles out, in the quiet camera language of a 2001 Taiwanese music video**」（曲线总律+年代锚双入）。

## 八、应用收口（本窗已执行·纯 CPU/git 职合规 CEO 让路令）

1. `30s-reel-v1/mv_full_shots.py` v1.1：44 镜 motion+content 全量重写（**窗口/时长/速度值零触碰**=whisper 锚定面·**KF 提示词零触碰**=他窗 L1-L7 预算面）+I2V_TAIL 升格——自检 lint+窗口连续性全绿。
2. `prompt-writing-spec-v1/patched-scripts/prompt_lexicon.py` v1.3：CAM_MOVE 全键值升格（曲线+质感烘焙）+四新块（CAM_CURVE/CAM_MOTIVE/CAM_DEST/CAM_TEXTURE）+`build_camera()` 五槽组装器+lint FLAT 门（video 模式）——十曲专辑线直接复用。
3. `PROMPT-SPEC.md` v1.2：§五运镜公式条升格引用本件。
4. 30s 封存线（gen_fleet_pkg.py/cloud_prompts_v4.py）按 orders 30s 终止令不回改——已产 S1-T 复用素材照旧。

## 九、前后对照三例（病灶→正法）

| 镜 | 旧（判负） | 新（五槽） |
|---|---|---|
| C01_carver_face | `pushes in with small amplitude at very slow speed`（平速·无动机·无质感·无到站） | `eases toward his profile on a slow dolly as his heavy-lidded eyes lift from the half-cut row toward something beyond the frame, gathering only as far as his gaze travels, and settling on the lifted look`（动机=抬眼=注视链·曲线三段·到站=定格抬眼） |
| N05_dead_language | `drifts laterally with small amplitude at very slow speed`（6.9s 匀速直线=定速巡航） | `drifts sideways along the stacked registers on a floor dolly, beginning almost still, gathering to a slow walking pace band by band, the carved rows sliding past with a faint parallax, easing still as the band runs out at the frame edge`（三段曲线+视差层+dolly 微颤+到站） |
| D06_chisel_fingertip | `holds locked-off, the two touches breathing in the same light`（锁机但零镜头行为·双触点无主次） | locked + `the sharpest point passing from the ancient chisel bite to her fingertip resting on the glass`（rack focus beat 承古今转移=镜头行为替代机位运动·型5） |

## 十、判据（下一波 i2v 成片闸新增「运镜检」）

1. 提示词层：移动镜 100% 带曲线+目的地+动机；lint FLAT 门全绿（机制化执法）。
2. 成片人眼逐移动镜：无匀速漂浮感；移动有到站感；静镜有活体（非屏保）。
3. 多模态帧级抽检：移动镜首帧≠末帧构图（位移真实发生）且零 warp 伪影。
4. 盲评加维「运镜导演感」（≥9 过）；与年代体裁检（ERA-MV-GRAMMAR §四）同场过闸。

---
*v1·bm-a 导演席·2026-10-12 11:3x·复引链=R-20261008-mv-craft-deep-01（运镜四定律）+R-20261012-era 证据板+PROMPT-SPEC §五/§六官方证据链+tw-mv-director skill §二·外部 C 级三源已标*
