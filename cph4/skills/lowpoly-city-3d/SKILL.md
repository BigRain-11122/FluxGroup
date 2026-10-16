---
name: lowpoly-city-3d
description: 硅基生命城市（FluxVerse/City3D）lowpoly 3D 美术线常备技能：48 包 Synty 库 AD 引用法、俯视角 3D 装配 SOP（数据驱动）、URP 定谳参数（CEO 令）、摄像机三档、地编与程序化判定律、L1 许可红线、库=唯一源律（3D 资源禁云端生成·CEO 令 09-29）、资产利用律（调用最大化+生产零重复·三查闸/三登记·CEO 令 09-29）、U288 五闸同构门禁、坑律速查。当在 City 3D 线做城市装配、资产选型、渲染决策、性能调优或 3D 资产入库时使用。
---

# Lowpoly City 3D（硅基生命城市 3D 美术线）

正典方案=`gaming/FluxVerse/docs/lowpoly3d-transition-plan.md` v2；**施工参数单=`gaming/FluxVerse/docs/lowpoly3d-implementation-params.md`（URP 落位/城市大小/地编/程序化/摄像机/在库实查/点火三步——开工先读）**；**城市活性正典=`gaming/FluxVerse/docs/lowpoly3d-aliveness-plan.md`（CEO 令「真正的活起来」·五面活性/真数据投影律/事件演出 3D 重锚/Phase 判据——活性面开工先读）**；**城市×资产联动正典=`gaming/FluxVerse/docs/lowpoly3d-city-asset-synergy-plan.md`（CEO 令「真正适配」·器官×资产联动定谳表+适配度判据五条+七步序列——选型/分区/活性接线面开工先读）**；**城市重构总案=`gaming/FluxVerse/docs/lowpoly3d-city-rebuild-plan.md`（CEO 令 09-29 最高定谳「角色能走进建筑·真城市生活·推翻重构·不计沉没成本」——模块壳拼装建筑法/三锚点生活空间/R0-R6 重构路线·**当前主线·旧城施工让位**）**；资产唯一索引=`gaming/MiniGame/_共享与总控/俯视角3D资产_POLYGON48包全景梳理.md`；资产中台=`gaming/MiniGame/projects/P3D_Spike`（内置管线·参照工程）；**3D 工程落位=`gaming/FluxVerse/City3D`（URP 原生·CEO 定谳）**。

## 〇 专家技能分工表（四专家+本总控·每席带后台智能体派工模板）

| 席 | 技能 | 辖域 |
|---|---|---|
| 总控调度 | `lowpoly-city-3d`（本件） | 全局判据/红线/门禁/相机/管线 |
| 地编专家 | `city-3d-terrain` | 地面 chunk/水系/贴花/大世界扩展 |
| 灯光专家 | `city-3d-lighting` | 昼夜色轮/五色律 emission/bloom/烘焙 |
| 装配专家 | `city-3d-assembly` | Synty demo 范式/blockout→dress/prefab 组织 |
| 程序化专家 | `city-3d-procedural` | 散布/数据→摆放算法/街区填充 |

配套席位：资产审核=`asset-audit`；调研纪律=`cph4-research-dispatch`。专家派工=各技能内「派工模板」复制即派（后台智能体·产出走五闸收口）。

## 一 红线（开工前必过）

1. **L1 许可**：48 包=淘宝转售无商业授权——**禁入交付链/提审包/商用面**；原型/风格验证/规格研究=合规。参观端商业化 gate=正版采购（待 CEO 裁）。
2. **敏感面**：城市 UI/参观端禁金融行情视觉；QUANT 城走「中性金屏」自制件。
3. **AIGC**：AI 生成 3D 件入参观端→开门帧 AIGC 标识。
4. **引用法**：资产引用一律「AD-NNN+一句话」，禁裸包名。
5. **库=唯一源律**（CEO 令 09-29 升格终章「以后3D这一块资源不要用云端生成了，我会给资源库填充资源 你做好调用和标记」——09-28 库内优先律升格）：①3D 资源**禁一切云端生成**（generate_3d_model/generate_motion/tripo 族/decimate 全停·AI 生成件=冻结档案）；②**资源库=唯一来源**（48 包+CC0 在库件+CEO 亲填增量=唯一供给通道·真缺口=缺口清单呈报 CEO 填库·禁自行生成/采购）；③我方双责=**调用**（AD-NNN Prefab 实锚+运行时实测分档）+**标记**（选件清单留痕+索引更新+AD-NNN 引用制）。

## 二 装配 SOP（数据驱动律）

0. **开工三查闸**（资产利用律 §一·正典=`docs/lowpoly3d-asset-law.md`）：查件（`City3D-staging/polygon48-item-catalog.tsv` 件名账）→查例（各专家技能判例节）→查用（`City3D-staging/asset-usage-ledger.md` 用量账）——三查不过禁动工：库里有=禁自制/禁生成，量过=禁重量，踩过=禁再踩。
1. 版式数据源=`Tools/city/td-organic-data.txt`（路网/水系/桥/广场/树点位·与 2D 遗产同源）——3D 摆放脚本读同一数据，禁凭手感摆放；**1 格=8–16m（以 AD-022 路面件实测宽定标·Phase 0 锁定）**。
2. 城市结构锚（512×512m 初始城）：脑塔=原点·脑环 r≈40m·三城中心 r≈180m 120° 扇形·外环感知网 r≈240m；16×16 chunk（32m）。
3. 起步组合=AD-048 白盒底座→AD-022 城市街区→AD-015 植被地形→AD-042 人物→AD-010 粒子→AD-039 图标；按区扩表见方案 §四映射表。
4. 路网几何律：**8m 网格正交为骨**（Synty 路件=固定宽 90° 正交模块·SM_Env_Road_01/02/03/Arrow/Bare/Crossing/Lines/Median 实测在库）；曲线=短直段折线逼近（每 8m 转角 ≤15°）；立交/异形=Phase 2 RoadArchitect 评估。
5. 材质律：flat=一张共享渐变图集（换色=挪 UV·R-02 双 A 证）；窗灯=**emission 改造材质变体**（优先 AD-022 自带 Emissive_01~05 贴图直供）。
6. 装配后必跑：远/近双轨判据截图组（U280 帧设计律）+ 帧率读数 + 多模态抽件体检。

## 三 管线与性能判据（URP 定谳版·CEO 令「定URP」）

- **管线=URP 原生**（A/B 已取消）；SRP Batcher 官方表 Built-in:No/URP:Yes（直验✓）+CPU 提速 1.2x–4x+WebGL CPU 瓶颈承重；反例注：低端 WebGL shader 未优化时关 SRP Batcher 或更快（验证跑把关）。
- 资产过桥：Synty URP_ExtractMe（部分包）+Render Pipeline Converter 兜底；判据=抽件渲染对比零色差。**URP 程序化建管线三 API**（P3D spike 实测）：UniversalRenderPipelineAsset.Create+PostProcessData.asset 挂载+GraphicsSettings.defaultRenderPipeline；**shadowDistance 公有 setter 须调大（默认 50·俯视高机位必丢影）**。
- 相机三档（参数单 §五）：L0 总览 俯角 50°·高度 320m±｜L1 区景 55°·110m±｜L2 实体 60°·24m±｜FOV 45°·缩放带 16m↔400m 连续（MoveTowards 24/s 沿承）·默认锁北向·正交备选。
- 光照：斜定向光+只烘 AO+Light Probes（R-04：烘焙 GI 撞动态太阳）；渐变天空盒+环境光取天空盒（接昼夜色轮）。
- WebGL 坑律（R-02+波①修正 `R-20260928-alive3d-01`）：CPU 瓶颈/skinning 双优化失效（多线程+SIMD 失效·蒙皮显著变贵·官方直证措辞修正）/后台节流挂钟兜底/Exception=None/帧率交浏览器/音频仅 Web Audio/Chrome Autoplay 挡 BGM（开门帧交互即解）/**群体律**：SMR 不可 instancing·SRP Batcher 优先于 instancing·<256 顶点不宜 instancing（光点走单 buffer 合批/CPU 粒子）·AnimationInstancing 无 WebGL 定谳判负。
- 程序化判定律：**只做「重复件分布」，不做「城市结构」**（结构=数据驱动设计）。

## 四 工程接入坑律（实测在册）

- `tuanjie-cli projects create` 会自动开 GUI 编辑器盯新工程——同工程再跑 batchmode 必崩「already open」；预热导入交给该实例（ImportWorker 归零×2+Editor.log 停摆 2 分钟=收工判据）。
- Unity 会升级重写老 .meta（GUID 不变）；包目录直拷入 `Assets\` 即可（.meta 随行）。
- 批建造 SOP 通用（batchmode -quit -executeMethod -logFile+600s 看门狗+fail-loud .done 哨兵）。
- 编辑器桥（unity-mcp v10）自启脚本须幂等：每轮查 IsRunning 再 StartAutoConnect；免 GUI 导入唯一正道=MCP refresh_unity。
- AD-022 demo 场景 YAML 的 PrefabInstance m_LocalPosition=局部坐标——裁街区用引擎世界包围盒法（P3D spike 实测）。
- Tuanjie 编辑器脚本两坑（2026-09-29 实测）：`RenderSettings`=静态类直写属性（禁实例化误用）；URP 类型在编辑器批脚本须全限定名（`UnityEngine.Rendering.Universal.*`·裸名不解析）。
- unitypackage 解包重建判例（10-08 三包实测）：pathname 文件尾带 `\n`+字面 `00` 两字节杂质——重建器只取 pathname **首行**（Get-Content -TotalCount 1），按尾字节 Trim/空字节替换皆漏判。
- AD-049 判例三则（10-08 快样实测）：①车体定向=**最大 mesh 体积投票法**（renderer bounds 会被影子面片/挂件拉偏·横跨车道判例）；②路系模数=15×15m 板件+75×75m 立交（与 Synty 5m 格**不同模数**·两路系混用须先过对齐律）；③包内 .mat 实为 Built-in Standard（官宣 URP 不实）→URPMaterialBridge.Convert 通路 155 材质零破。

## 五 资源供给（CEO 令 09-29：3D 禁云端生成·库=唯一源·我方=调用+标记）

- **云端生成径永久停用**：3D 资源全族（generate_3d_model/generate_motion/tripo 族/decimate/天空盒生成中 3D 件等）一律禁；AI 生成件=冻结档案仅对照。**真缺口=缺口清单呈报 CEO**（CEO 填充资源库=唯一供给通道）——禁自行云端生成/外部采购。
- **调用律**：选件一律 AD-NNN Prefab 实锚（v1 判例：抽 Model 无材质指配=假阴性品红）+运行时 Measure 实测分档（bounds 体高/占地判据）+确定性 seed；`CityAssembler.cs`=范式件（EnvPf/ScifiBldPf/SpacePropPf 常量实锚+FitLong 长轴归一）。
- **标记律**：选件清单留痕=建批 report（`City3D-staging/assemble-report.md` 等·原始日志层）+收工登记 `City3D-staging/asset-usage-ledger.md`（跨城用量账·策展视图）；新增资源入 48 包索引（`MiniGame/_共享与总控/俯视角3D资产_POLYGON48包全景梳理.md`）；引用面全场景 AD-NNN 引用制（禁裸包名）。
- **资产利用律**（CEO 令 09-29 追加「最大化利用好·不要重复干」·正典=`docs/lowpoly3d-asset-law.md` V1.0）：调用最大化+生产零重复——开工三查闸（件名账/判例/用量账）+收工三登记（用量账/判例/索引）+demo 按需开采+一次生产终身复用；两城利用率实况与未用高价值面=`City3D-staging/asset-usage-ledger.md`（AD-022 Apartment 模块套件 23 件/店面 16 件/AD-020 全矿=下批扩容查账即得）。
- CC0 在库件（Kaykit 161 动画/Kenney/Quaternius）=库内资产可用；新 CC0 引入须先呈报（缺口判定→CEO 裁·非自行抓取）。

## 六 判据门禁（U288 五闸同构·2026-09-28 接入集团审查体系）

正典=`MiniGame/_共享与总控/游戏UI交付五闸审查体系.md` V1.0（U288 立典·集团推广位=各司骨架同构自建）。

**City 3D 五闸链**：
| 闸 | City 3D 执法 |
|---|---|
| 闸1 产前五问 | 数据驱动在档？AD-NNN 引用合规？三红线过（L1/敏感面/AIGC）？判据帧预注册？外部件核验闸过？ |
| 闸2 收件三查 | 内容忠实+风格协调+落位验证（U282·多模态抽件体检） |
| 闸3 装配双闸 | 场景断言（件数/位置/seed 对账）+引擎帧率门（WebGL 30fps 底线） |
| 闸4 渲染取证 | 远/近双轨判据帧（U280 帧设计律）+取证探针（出框/骑跨像素实证·勿凭目检断言） |
| 闸5 合样终审 | Phase 判据全绿 → CEO 复验（禁执行侧自证·U098） |

**六条不通过红线**（U288 同构）：取证确认出框／包络违例／已知缺陷未挂账／硬闸红／断言无取证／执行侧自证——任一命中**禁呈审，与评分无关**。
**判据帧双系律**（2026-09-29 判例）：装配器直出帧=A_ 系=品红中间态（未过桥未过官方基准）——**正式呈审帧=过桥器 B_ 系**；DayNightCycle（ExecuteAlways·北京钟）会抢 rig 覆写 B_ 系日帧（v3.1 判例：官方基准档从未真入镜）——判据帧捕获须锁日夜态。
**机检优先律**：评审断言降级为线索；机器可验判据=唯一 PASS 依据。

**Phase 门**：Phase 0=30fps+三档双轨截图+导入零错+URP 零色差｜Phase 1=行为映射逐条可验｜Phase 2=实况抽查+性能达标｜Phase 3=合规三红线+正版采购 gate+WebGL 七坑过闸。
