# REBUILD-PLAN v2 — 漫剧产线彻底改造案（双轨换轨正身）

> 溯源：CEO 令 2026-10-19 ~14:4x「漫剧现在做的非常垃圾，直接调研采集最新工具github，组成专家团和技能，彻底改造」+追令「你自己去红果抖音等平台去看头部漫剧短剧真人剧！给我对标！」
> 判定依据：R-20261019-drama-benchmark-01（路线级错位定谳+差距清单）·R-20261017-drama-oss-tools-round3-01（波 A·3D 漫化 14 项）·波 B 两方向采集 2026-10-19（分镜一致性+中文配音全量·A 级直验）
> 执法律：**科学借鉴律**（orders 2026-10-19 14:48·commit 425831f4）=借骨架禁抄灵魂+必须适配+超越判据——本案一切对标动作先执法此律
> 位次：本件=漫剧产线改造总案 v2；v1 正典（DRAMA-PRODUCTION-SYSTEM-v1 十站链/精度阶梯/QC 闸）**结构保留**，D3 画风案与工具接线表按本件勘正执行；试点判据沿用 PILOT-001-PLAN（IP 池不变·视觉路线换轨）。

## 〇、改造定谳（一句话）

v1 路线=SD1.5 2D 漫画画风（CSA 冒烟盲评 2/10·平台头部零此路线）→ **v2 双轨**：短线主路=**AI 仿真人**（对齐红果头部管线·复用 MV 线现役能力·两周出粗样）；中长线=**Blender 3D 漫化**（波 A 工具链·一致性天花板+强动作戏）。2D 漫画路线降级为 D 级备选（判负留痕·重访触发器=平台 2D 头部出现）。

## 一、科学借鉴律执法注记（先执法后施工）

- **借骨架**：单集 2 分钟竖屏·80-120 集连载·季标签系列化运营（头部 >60% 结构）·3 秒钩/30 秒爆点/结尾悬念·仿真人画质及格线（写实 CG 人偶质感）
- **禁抄灵魂**：题材与 IP 一律不抄头部（万妖图录传/凡人百世书/聚宝仙盆等）·「剧名即钩子」句法学但字面不复刻·不借势他方视觉资产
- **必须适配**：自有 Biggame 软著 8 款 IP 池优先（零授权成本+游戏联动变现·合规最优）·机队车道适配（16G/8G/夜窗 12G·让路律不破）·中文配音三新作适配（中文是主战场）
- **城市同源加分项**（CEO 令 10-19 15:2x「真正发生在硅基城市里面的，给城市真正的赋予」）：IP 定选时故事发生在硅基生命城市宇宙内=加分——自有 canon+城市反哺内容+内容反哺城市三赢（通道=world-events.jsonl 事件流+FluxVerse canon·census 面冻结候解禁·总纲=BIGSTREAM-PRODUCTION-METHODOLOGY-v1 §七）
- **超越判据**（对标物及格线=我方起点）：盲评 ≥9（非 ≥8）·跨集一致性 ≥95%·单集成本 <300 元·日更 ≥1 集能力·「AI 感」逐集减法（承 MV CRAFT-SPEC §六-§八去 AI 感全律）
- **情感投入证据链**（CEO 令 10-19 15:2x「投入真正的精力和情感进去」·成片闸呈审必携件·缺链=REVISE）：立意深研档（每集立意有出处有升华）+表演细节档（三段式+情绪曲线）+情感值逐镜标定+多拍选优记录（takes 台账）随片归档——粗制滥造判负三查与导演席六轴第 3 轴互锁

## 二、短线主路（T0·AI 仿真人·两周内出粗样·复用 MV 线现役件零新基建）

```
D1 拆集剧本（qwen CPU·钩子三件套·季框架）
D2 分镜（六工序分镜卡·资产三视图/场景锁版不变）
D3 仿真人 KF（seedream photoreal 档+jman 骨相锚+光影法=写实 CG 人偶风·头部同款质感）
D4 i2v（云端 i2v 现役+H3·locked-off+内容微动律·CEO 13:36 方法论全执法）
D5 口型（LatentSync-1.5·官方 8G 中文优化档·已在册；Unity 位可加 uLipSync 预览）
D6 配音（IndexTTS-2.5 情感主力[权重 bilibili 许可·商用过合规闸]+GPT-SoVITS v2Pro 自训音色库[MIT·CHARACTER-LORA-STABLE-v1 正典]+VoxCPM2 文字造音色[Apache·合规最干净]+CosyVoice3 方言/旁白[Apache]）
D7 装配（whisper 词级锚+首尾剪除 0.3+0.5 律+MoviePy/ffmpeg）
D8 盲评闸 ≥9+跨集一致性抽检+AIGC 三标识 → D9 发布+季运营台账
```
- **关键改造点**：D3 画风四案「仿真人 CG 人偶风」升为默认案；takes 多拍选优/低清海选/队列驻留三效率引擎+多模态帧审全继承（MV 现役律直用）
- 一致性工艺：仿真人线=参考图锚+骨相锚+每角色 LoRA（seedream 系 KF 天然高一致·弱化 2D 天花板问题）

## 三、中长线（T1·Blender 3D 漫化·一致性天花板+强动作戏）

- **工具链**（波 A 14 项 A 级直验）：Kitsu（分镜镜头表·736★ AGPL·产线管理面）→ mcp-for-blender（31.6k★ MIT·LLM 控 Blender）→ nijiGPen（2D→3D 生成）→ Malt（NPR 渲染·MIT）/Goo Engine（动漫定制 Blender·试点）→ Rigify 骨骼 → GameRig/storytools 辅件 → CGRU 渲染农场 headless 批量出图
- **一致性组合拳**（波 B）：3D 角色渲染**无限角度训练集**→InstantID（SDXL·商用干净）/Qwen-Image-Edit（Apache 底座）→每角色 LoRA 锁脸→Toonflow（18k★·短剧/漫剧编排平台·剧本→分镜→角色资产）——3D 训练集路线=纯 2D 剧组做不到的**独有优势位**
- **选路判据**：动作戏占比 >30% 或连载规划 >60 集→3D 线；文戏情感向+快验证→仿真人线；两线共用 D1/D2/D6-D9 站
- **首 PoC 判据**：装配件验证（Kitsu→mcp-for-blender→Malt 出 3 镜样片·头 3 周内）

## 四、工具接线表 v2（站→主力→许可→机位·两波全量勘正）

| 站 | 主力 | 备选 | 许可结论 | 机位 |
|---|---|---|---|---|
| D1 拆集 | qwen CPU+screenwriting | inkos/wind-comic 编排参照 | Apache/MIT | 全机 CPU 24/7 |
| D2 分镜 | Kitsu 分镜表+六工序 | Toonflow 编排面（18k★）·storytools | AGPL/转化中 ⚠核 | CPU |
| D3 KF-仿真人 | seedream+骨相锚+角色 LoRA | InstantID/Qwen-Image-Edit 编辑位 | 底座商用干净/Apache | bm-c 16G |
| D3 KF-3D 漫化 | mcp-for-blender+Malt/Goo+Rigify | nijiGPen·dream-textures 辅 | MIT/Apache 为主 | bm-a 夜窗渲染 |
| D4 动效 | 云端 i2v+H3（关键镜） | RIFE/LTX-Video 补 | 现役 | 云端+bm-c |
| D5 口型 | LatentSync-1.5（8G 中文档） | uLipSync（Unity 实时·MIT）·FACEGOOD（MIT·blendshape）·NVIDIA Audio2Face-3D（买力位） | 见各仓·商用闸 | bm-b 8G |
| D6 配音 | IndexTTS-2.5+GPT-SoVITS v2Pro+VoxCPM2 | CosyVoice3（方言/流式） | 权重 bilibili 许可 ⚠商用闸/MIT/Apache | bm-b/bm-a |
| D7 装配 | MoviePy+ffmpeg+whisper | — | MIT | bm-b CPU |
| D8 质检 | 盲评 ≥9+脸锚抽检+多模态帧审 | VQAScore 承 MV 标定 | MIT/Apache | 全席 |

**判负留痕**（勿再引入）：Storyboarder（2024-03 冻结·高星陷阱）·JTRP·OpenVoice v2（中文 0.3-0.4）·Wav2Lip（学术非商用）·2D 连续多镜一致性 5 款（D-20261019-17）·fish-speech（S2 Pro 转闭源）·MeloTTS/ChatTTS（无稳定克隆/CC-BY-NC）。

## 五、专家团+skill（CEO 令「组成专家团和技能」执法）

- **漫剧导演席=drama-director skill**（本批新立·canon=cph4/skills/drama-director/）：评审分层承 MV 总令（专家群审→导演总控→CEO 上线·禁越级）+审查面五轴（画质及格线/连载钩子链/一致性锚/合规三标识/成本线）——**一切漫剧/短剧剧本/分镜/样片/成片过导演席签字才放生产**
- **环节专家矩阵**（对齐 MV 五件套 MV-ALL-STAGE-EXPERT-COVERAGE 模式）：剧本席/分镜席/KF 席/动效席/配音席/装配席/QC 盲评席/合规席（AIGC 三标识+题材 11 项红线）/运营席（季标签+囤稿台账）——首批=导演席落地（本窗），其余席位**随 PoC 挂位·有活才立位**（防空转立席）
- AGENT-LIBRARY §六登记执法（不登记不存在律）

## 六、执行序（先快后全律·禁跳步）

| 步 | 动作 | 判据 | 归属 |
|---|---|---|---|
| 1 | 本案+benchmark+skill+登记上链（本窗） | commit+push 验证 | bm-a 交互窗 |
| 2 | PoC-A：AI 仿真人 3×20s 粗样（自有 IP·seedream KF+云端 i2v+IndexTTS-2.5） | 盲评初读+CEO 点方向（一周内） | drama-dept+bm-c/bm-b |
| 3 | PoC-B：Blender 3D 漫化 3 镜样片（Kitsu→mcp-for-blender→Malt） | 3 镜出图+一致性目检（三周内） | bm-a 夜窗 |
| 4 | 双 PoC 对比定谳主路（成本/一致性/速度三维） | 对比板呈 CEO 终判 | 导演席+委员会 |
| 5 | PILOT-001 全链开工（T1→T2→T3 精度阶梯·季运营框架） | 成片闸 CERTIFIED | drama-dept 全席 |

## 七、机队排程（让路律不破·MV-only 红线不动）

- 前期全 CPU 面（剧本/分镜/调研/装配件/Toonflow 编排）=全机 24/7 不受限
- GPU 面：bm-c 16G=仿真人 KF+LoRA（MV 波次间隙错峰）·bm-b 8G=LatentSync+配音推理+480P animatic·bm-a 夜窗 12G=Blender headless 渲染+IndexTTS-2.5 主推理
- 云端：仿真人 KF 走 seedream 档·关键镜 i2v 走云端快车道（记账 attribution·云端严管令照旧）

## 八、红区不变项（INDEX §四全量继承·不重述）

投资额 <30 万红线/AIGC 三标识/自有 IP 优先/禁真人肖像声音参考（含明星声克隆·民法典 1018/1019）/创作过程留痕——逐条执法位不变；配音数据集素材逐 license 过闸（CC0/Common Voice 可用·AISHELL-3 须核·Emilia/WenetSpeech4TTS 非商用勿用于成品）。
