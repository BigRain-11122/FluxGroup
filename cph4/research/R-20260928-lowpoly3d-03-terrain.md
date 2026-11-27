# R-20260928-lowpoly3d-03 地编/地形面调研（平面 chunk 基线验证）
> 定稿 2026-09-28 | CPH4 Labs | 消费方: FluxVerse City3D（URP·Tuanjie 1.10.3≈2022.3·WebGL 参观端） | 外部读取 19/20·检索 9 | 源分级 A官方/B权威/C社区/M待证

## §0 结论速览
- ①「禁 Terrain」基线**成立（确认）**：俯视平城无高程需求（设计律）+ 社区 C 级双源负面报告 + Synty 图集资产本为平面网格设计（仓内实查）。
- ②2022.3 URP **无内置水系统（确认·A+C 双源）**：官方 com.unity.urp-water-system 停在 preview 且只到 Unity 2021.3/URP 12 → 直接装不可行，走免费/开源第三方平面水。
- ③WebGL 大世界流送**必选（确认）**：WASM 堆默认上限 2048MB（官方）；首期 512m/1024m=场景全进首包最稳，远期 5000m=Addressables 远程组但有三坑。

## §一 地面系统选型: 平面 chunk vs Unity Terrain vs ProBuilder/Polybrush
**结论: 32m 平面 chunk 基线成立（确认）；Unity Terrain 仅在需连续坡地+植被细节系统时重评（推测）**
- Terrain 本质（A·官方 Manual 实读）: "A Terrain GameObject adds a large flat plane to your scene...create a detailed landscape"——从大平面雕刻的高度图管线，自带 trees/details 等重特性。
- 社区负面实证（C·双源·摘要级）: ①Reddit: 移动端 Terrain draw call 灾难"game running at 10fps is the terrain"; ②Unity Discussions 帖题"Draw Instanced terrain horribly slow and choppy on WebGL"——WebGL instanced terrain 帧率不可用（正文 403 未读全→细节待证）。
- 分块流送正面实证（C·Reddit）: "anything unity doesn't have to manage/draw is going to be faster...disable far away terrain chunks"——分块+卸载优于整体管理。
- ProBuilder/Polybrush 定位（推测）: 白盒/单体建模工具；512m 地面单体建模=大 mesh 编辑负担，chunk prefab 更简单可流送；其顶点色可作区块涂色备选（性能待证）。
- **高程触发器（本件新增判据）**: 设计需要 >±2m 连续起伏/坡地街区时→路径A=chunk 顶点位移烘焙进低模 mesh（保 batch）；路径B=Synty 件台地堆叠（现状 AD-015×26 即此径）。Unity Terrain 引入前必过 draw call 预算验证。
- 佐证（A·URP14 decal 文档）: "does not work on...terrain details"——Terrain 生态特殊渲染路径，与本项目平面地面无交集（已禁·不追 SRP Batcher×Terrain 兼容性）。

## §二 风格化水面(URP 2022.3) 与地面细节三径
**结论: 平面水=第三方免费/开源；主选 InteractiveStylizedWater(MIT)，备选 Ameye 免费版；官方水包禁装**
- 官方水包（A·package.json 实读）: com.unity.urp-water-system v2.0.0-preview.5，"unity":"2021.3"，依赖 URP 12.1.10，README 原文"not supported in any official capacity"——与 2022.3/URP 14 版本代差，移植成本>收益。
- URP 无内置水（C·官方论坛摘要）: "there doesn't seem to be a plan for an ocean system similar to what there is in HDRP, for URP"——与上互证（A+C 双源✓）。
- 候选清单: ①mozankatip/InteractiveStylizedWater: MIT·2023·43★·URP·plane 承载·要求开 Depth Texture+Opaque Texture·交互波纹（摘要级 C）; ②jp-netsis/LowPolyWater-URP: MIT·2020·8★（license 实读✓·功能待证）; ③Ameye "Stylized Water Shader (FREE)": URP 免费版（论坛帖 C·个人站 404→功能矩阵待证）。
- 参数要点: 平面水共性=全局开 Depth Texture（岸线深度衰减/软边）; Opaque Texture（折射类·全屏拷贝有代价·WebGL 待证）; 水面 plane 与水底材质分区对齐（水底已定谳）。
- **地面细节三径取舍**: ①材质/图集分区=主径（确认·施工参数单已定+Synty 单图集仓内实查）; ②路面标线=AD-022 路面件自带 Lines/Median（零成本）; ③顶点色=32m chunk 顶点过稀，不适细纹、仅适合大块渐变（推测·Synty shader 是否读顶点色=待证）; ④贴花 decal=点缀径。
- Decal（A·URP 14.0.12 文档实读）: Decal Renderer Feature+Projector; 技术=Automatic/DBuffer/Screen Space; DBuffer 需 DepthNormal prepass"less efficient on tile-based rendering GPUs"; Screen Space 官方荐瓦片 GPU·Normal Blend 低/中/高=1/3/5 深度采样; 限制=不投影透明面。→WebGL 俯视城选 Screen Space（瓦片 GPU 同移动端假定）; 渲染路径支持矩阵文档页未列（待证·Phase 0 验证）。

## §三 大世界扩展: additive scene vs Addressables（WebGL 参观端）+ 分区粒度
**结论（首期确认·远期推测）: 512m/1024m=全场景进首包+additive 组织（零 catalog 依赖最稳）; 5000m=Addressables 远程组+三坑检查表前置**
- 内存硬约束（A·官方实读）: WebGL WASM 堆上限默认 2048MB·线性增长步长 16MB——5000m 全城常驻不可行，流送必选。
- 缓存（A·官方 webgl-caching 摘要）: 须开 DataCaching 缓存进 IndexedDB; "default browser HTTP cache doesn't guarantee...caches a particular response"——HTTP 缓存不可靠。
- Addressables WebGL 三坑（C·社区）: ①大/多文件下载故障"problem occurs when I want to download many or large files"; ②新版本 WebGL 故障 issue（2019.4 可用·版本细节待证）; ③无法加载用户本地 bundle（只认 LocalLoadPath/RemoteLoadPath）→参观端须全远程或全首包。
- 服务器压缩坑（C·双源·官方错误文本）: gzip/brotli 须配 HTTP "Content-Encoding" 响应头，否则 "Unable to parse Build/*.framework.js.gz"（StackOverflow+中文社区双源）。
- additive 卡顿对策（C·bugnet 实读）: 根因=激活全落一帧; 对策=allowSceneActivation=false 至 progress 0.9 安静帧激活+Awake/Start 分帧+预热 shader 变体与对象池。
- 流送模式参照（B·Oculus 官方样例）: "players only interact with one section of a world at a time"近区高保真/远区低分辨率+LOD——基于 Addressables 的开放世界样例（Dead & Buried 2）。
- **分区粒度（推测·待证）**: 5000m÷32m≈156×156 chunk; 建议扇区场景 256–512m（8×8–16×16 chunk/场景·全城约 100–400 场景·计算值）——无权威数字源; Sectorize 工具文档（B/C）证明 "terrain tiles→sectors→additive scenes around cameras" 为成熟模式（面向 Terrain·模式可迁移）; Phase 2 前实测定标。

## 【应用表】（落点=施工参数单 §三地编节修订）
| # | 落点 | 修订建议 | 依据 | 置信 |
|---|---|---|---|---|
| 1 | §三.1 平面分块 | 基线确认不动; 新增「高程触发器」: >±2m 连续起伏需求才启高程路径（chunk 顶点位移/件台地堆叠），禁 Terrain 维持 | 设计律+C 双源+A | 确认 |
| 2 | §三.3 水系 | 候选清单化: 主选 InteractiveStylizedWater(MIT)·备选 Ameye 免费版; 官方 urp-water-system 禁装(preview·URP12); 全局开 Depth Texture; Opaque Texture 代价 Phase 0 验证 | A+C | 确认(候选级) |
| 3 | §三 新增贴花行 | 细节定序: 材质分区(主)→路面件标线→decal 点缀(Screen Space·瓦片 GPU 禁 DBuffer); 路径矩阵 Phase 0 验证 | A(URP14 文档) | 确认(文档级) |
| 4 | §三 新增扩展行 | 1024m 期仍全场景进首包; 5000m 启 Addressables 前置三坑检查表(Content-Encoding 头/DataCaching-IndexedDB/bundle 少而大) | A+C | 部分待证 |
| 5 | 施工律(卡顿三律) | Phase 2 清单: allowSceneActivation 门控+激活分帧+shader 预热 | C | 推测→实测 |
| 6 | 顶点色备查 | Synty shader 顶点色支持未验——需大块渐变分区再验; 现材质分区已覆盖 | M | 待证 |

## 【验证声明】
- 读数: 外部读取 19/20（网页 16+仓内 3）; 检索 9 次; **主会话止损令已执行**——停止采集，以已采证据收口，两优先域（①选型证据②平面水）均已双源承重。
- 成源: A 5 处（官方 Manual/URP14 decal 文档/webgl 文档×2 摘要级/官方水包 package.json+README）; B 1 处（Oculus 样例）; C 8 处（Reddit×2·官方论坛×3·bugnet·压缩双源·粒度社区）; 关键结论双源: 禁 Terrain=设计律+C 双源; 无内置水=A+C。
- 三态: 确认=禁 Terrain 基线/无内置水/WASM 2048MB/decal 技术矩阵; 推测=高程触发器阈值/ProBuilder 定位/分区粒度/首期-远期路线; 其余见失败面。
- 失败面（诚实标注）: ①discussions.unity.com 正文多次抓取失败(403/空渲染)——WebGL instanced terrain 仅标题+摘要级; ②Ameye 个人站 404 免费版矩阵未核; ③Addressables 新版故障具体版本未核; ④decal 渲染路径矩阵官方页未列; ⑤分区粒度无权威数字=推测; ⑥LowPolyWater-URP 仅 license 实读; ⑦部分 C 级证据为搜索摘要未逐条直读全文（预算内取舍）。
- 移交 Phase 0: Opaque Texture WebGL 代价/decal 路径矩阵/水 shader 装机对比; 移交 Phase 2: 分区粒度定标/压缩头服务器配置验证。
