# R-20260929-citycraft-02-workflow — 搭城工序方法论：blockout→街坊→成城
> 溯源：CEO 令 2026-09-29「所以你要学习如何搭建城市」（学城令）·消费方=City3D 施工线·判据预注册=Q1 白盒路网→成品街区分步工序带源/Q2 路网→街坊生成结构律（CityEngine 正法+开源工序）带源/Q3 施工级 checklist≥20 步每步可验证
> 验证声明：web 实读 17 次=检索 8+直读 9（另失败尝试 8 次不计·文末失败面）；成源 10 面=A5（CityEngine 官方文档×3+GDC Vault 页+ACM 摘要快照）/B1（Springer 章快照）/C4（josauder/phiresky/retrostyle 厂博/YouTube038 快照）·在册锚不重复采集·零断言三态·数字带出处

## 一、工序面：白盒路网→街坊→成城分步方法论（Q1）
- 街道分级先行【确认·A】CityEngine 官方算法原文「The algorithm distinguishes between major and minor streets」（doc.arcgis.com/en/cityengine/latest/help/help-grow-a-street.htm 直读）=主干/次街两级正法底座；社区三级=巷/大街/高速【确认·C·retrostylegames.com/blog/design-city-for-game 直读】
- 灰盒先行四阶段【确认·B 在册承接】KinematicSoup「greybox out the demo scene」（先灰盒→多艺术家共建→叙事道具→眼高尺度复查）+Level Design Book blockout 五法+Unity 四阶段 blockout→玩法规验证→dress→优化（R-20260928-05 在册双源）
- 大城=仍是关卡设计【确认·A·GDC 概要直引】GDC 2019 Insomniac《Level Design Workshop: Building New York in 'Marvel's Spider-Man': It's Still Just Level Design》（Josue Benavidez·gdcvault.com/play/1026248 直读）——概要原文「fundamental level design principles…apply at any scale」+大城挑战=把基础 LD 适配更大空间
- 分区→地标→细节层【确认·C】厂博工序：zoning 住/商/工/混合+公园文化绿带→landmark=定天际线+玩家导航双职→细节层=street furniture/涂鸦/建筑特征；先定主题再定尺度（楼/街/开放空间尺寸=scope 匹配叙事+引擎）（同源 C）

## 二、街坊生成正法面：路网→街坊→贴线（Q2·CityEngine 正法）
- 街坊切分正法【确认·A 直读】官方算法原文「major streets are created until they enclose an area, called a quarter. Then the quarter is subdivided by minor streets. The algorithm continues」=主干街生长至围合 quarter（街坊）→次街细分→循环；街坊平均大小=street to crossing ratio（官方公式原文「#Major street nodes / #Major crossing nodes」）
- 路网→街坊→地块三段链【确认·A+B】官方「Street Network layer containing the graph network, blocks, and street and lot shapes」（get-started-workflows 页直读）+「Blocks can be divided into polygonal shapes called lots」（street-lots 页直读）+Springer 教材章【B 快照】同构「import a street graph…automatically create street shapes, blocks, and lot shapes between the streets」
- 地块分类与贴线机制【确认·A】Lot=贴街/LotInner=街坊内不贴街/LotCorner=转角（recursive 或 offset 细分 Block Corner Length 参数产物）；streetWidth=逐边数组·首边=最大街宽边·0=不邻街（street-lots 页直读）→建筑贴街坊边排布官方机制=按最大街宽边定向
- 社区开源同构工序【确认·C 直读】josauder.github.io/procedural_city_generation（明示基于 Parish & Müller《Procedural Modeling of Cities》SIGGRAPH'01）：L 系统路网=axiom+生长规则+人口密度图→主干/次街→街区=路网图环提取（cycles）→街坊切地块→每地块一建筑·过大地块弃建（=留白机制）→楼高按密度定
- 正典与综述在册【确认·A 快照+C】Parish & Müller 2001 ACM 页摘要「运输网络遵循人口/环境影响因素+叠加的形态规划；建虚拟城=先设计路网再生成大量建筑」（dl.acm.org/doi/10.1145/383259.383292）；phiresky.github.io/procedural-cities 直读=Parish-Müller 系开源复现+文献表（Kelly&McCabe Citygen 综述/Lipp 分层城市建模）；Poofy1 Procedural-City 参数面=R-20260928-06 在册不重复
- 广场/公园占位【确认·C×2】过大地块弃建留白（josauder）+分区绿地/公园/文化区（retrostyle）；CityEngine 规则级 plaza 占位=待证（规则文件未直读）

## 三、Synty 范式承接面：在册锚+新采增量
- 在册锚（勿重复采集）：官方《Modular Buildings in Unity》(youtube.com/watch?v=cwKy7MEYW70)+《How to use a Synty Map Pack》(youtube.com/watch?v=4a40CjuvsSs)+KinematicSoup 灰盒律；官方无独立搭城方法论文本=R-20260928-05 通道扫描在册
- 新采增量【确认·零新采】本波 Synty 官方面检索=无新城市工序内容（官方 playlist PL2QPFqe01WRkGN7J8X0Okgq7R3REbCt48 即在册全部）；判定【判断】我方缺的不是模块拼接法（在册闭环）而是城坊结构正法——本波以一/二节 CityEngine 正法+GDC 工序回填，Synty 件只当「贴线建筑件库」消费

## 四、施工 checklist（22 步·四阶段·每步可验证·对齐 td-organic-data 格点+CityAssembler/SciFiCityBuilder 确定性装配）
- 工序骨架源=一/二节；新设数字（格宽/地标频次）=【设计档·施工定谳】；其余=仓内在册锚
- 【A 定谳】1.定主题与城界（俯视 lowpoly 城）→验证=格点域边界闭合（C）
- 2.街道三级映射格点：主干/次街/巷格宽（设计档）→验证=16 掩码表全覆盖 AD-022 SM_Env_Road_* 无孤件（R-06 掩码律）
- 3.主干街定线至围合城坊→验证=俯视所有城坊=闭环 quarter（CityEngine quarter 律·A）
- 4.次街细分城坊至 32m chunk 粒度→验证=每城坊可整分入 chunk（R-05 chunk 律）
- 5.城坊注册：格点簇 id+逐边街宽→验证=streetWidth 逐边数组可查（CityEngine 属性律·A）
- 【B 白盒】6.AD-048/ProBuilder 白盒路网→验证=16 掩码路件全接无错缝（R-05/R-06）
- 7.功能分区 zoning 住/商/工/混合/公园文化→验证=分区块无重叠全覆盖（C）
- 8.节点地标占位：每城坊锚 1 地标或广场→验证=320m 俯视屏每屏见≥1 地标（设计档·导航律 C）
- 9.灰盒验证：45° 方位×35°/60° 俯角双档截图→验证=白盒构图过闸再进 dress（灰盒先行律·B 在册）
- 【C 贴线】10.城坊 offset 切地块 Lot/LotInner/LotCorner→验证=逐地块边街宽齐备（A 机制）
- 11.建筑贴线：Lot 首边=最大街宽边朝街→验证=街面连续无断口（A 贴线机制）
- 12.转角地块按 Block Corner Length 律处理→验证=转角件不错位（A+AD-022 转角族）
- 13.过大地块弃建留白→验证=无巨宅吞街坊·留白即广场/公园位（C）
- 14.LotInner 内院低密填充→验证=不挡街面视线（C）
- 15.楼高档钳制：QUANT 办公高/GAME 公寓中→验证=同 seed 高程复现一致（R-06 档位）
- 【D 成城】16.dress 换 AD-022/AD-018 成品件→验证=件数/材质/variants 合规（R-05 装配 SOP）
- 17.叙事道具层：street furniture/招牌/彩蛋按密度表散布→验证=24m 眼高机位叙事件可见（B KinematicSoup）
- 18.公园/广场与绿带落地→验证=绿块非空非溢（C）
- 19.灯光配方官方四件套（环境光+雾+主光阴影+后处理）→验证=对齐 48 包 demo 提取基准档（R-20260929-city-top1-01 在册）
- 20.眼高尺度复查：24m 机位走街→验证=KinematicSoup 眼高律通过
- 21.优化收口：draw call/chunk 流送/烘焙→验证=WebGL 预算过闸（R-05 优化段）
- 22.回归验证：同数据+同 seed 全城重建→验证=确定性装配逐件一致（R-06 回归可验律）

## 五、结论应用表（落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| 街坊切分正法：主干围合 quarter→次街细分→地块三分类+streetWidth 贴线定向 | 任务单：City3D 施工线/CityAssembler 工序接入 | 接线中 |
| 22 步四阶段施工 checklist（A 定谳→B 白盒→C 贴线→D 成城） | 任务单：施工工序文件落地 | 接线中 |
| GDC 大城=LD 原则任意尺度适配+灰盒先行律 | 任务单：checklist 阶段闸条款 | 接线中 |
| Synty 官方无搭城方法论文本（零新采） | 判负留痕：外部正法回填·Synty 面无欠账 | 已闭环 |

- 更新记录：T0 骨架早落盘→T1 街坊正法域（CityEngine×3 页+Parish-Müller+josauder）→T2 头部工序域（GDC+厂博）→T3 Synty 增量核验（零新采）→T4 终稿 58 行。
- 失败面：①Parish-Müller PDF 三镜像（naturewizard.at DNS 解析失败/Berkeley 镜像/ACM dlnext）均吐二进制=论文正文未直读（内容主张经 ACM 摘要快照+josauder C 转述+CityEngine A 产品化三重承载）；②GDC 双场 PDF 同因二进制→改 www.gdcvault.com 演讲页直读成功；③uat.gdcvault.com 解析内网 IP 遭 SSRF 拦截；④behindthedraft.com/classcentral.com 403；⑤DuckDuckGo 首查 Parish 一次 bot 拦截（换措辞第二次中）。
- 防线二候选：①「major streets enclose a quarter→minor 细分」原文=doc.arcgis.com/en/cityengine/latest/help/help-grow-a-street.htm；②GDC 会名/讲者/概要=www.gdcvault.com/play/1026248。
