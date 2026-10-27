# R-20260929-modular-asset-efficiency — 大型模块化 lowpoly 资产库高效使用工程实践（CEO 令 P-65 bm-a 机·高效面）
> 溯源：ledger P-65「如何正确高效的使用？」CEO 令 2026-09-29·消费方=FluxVerse City3D 性能施工法+全盘方案性能节（现状 2000+ 静态件+120 路灯+12 行人→数千件+WebGL 参观端）·判据预注册=①URP 三合批通道选择证据（含 <256 顶点 instancing 判据）②共享图集=性能基石证据③Synty LOD 现状+遮挡作用④chunk/Addressables 流送（WebGL 侧）⑤反模式清单⑥模块库 vs AI 生成对比
> 验证声明：读数 20/20 触顶（本地 5=派工纪律件+R 模板+存量 R 直读 2+lowpoly-city-3d 总控技能；外部 15=检索 7+直采 8）·成源 A=3（Unity Manual SRPBatcher/OcclusionCulling·Unity 官方博客 Addressables）B=0 C=8（直采 2：uhiyamaLab/FrameDoctor·摘要级 6：wallstop/StreamZones/discussions×2/AI 对比四源组）·M 仓内承接 6（R-02/R-05/R-alive3d-01/R-td-craft-perf-live/总控+灯光技能）·三态：确认 23·推测 1·待证 1

## 一、合批策略：static batching vs SRP Batcher vs GPU instancing（判据①）
- 机制分层【确认·A+C】SRP Batcher 不减 draw call 数·只减同 shader 变体下逐 draw 的 CPU 准备成本（官方原句「reduces the CPU time Unity requires to prepare and dispatch draw calls for materials that use the same shader variant」·官方表 URP:Yes/Built-in:No）；static batching=构建期合并同材质静态网格成单 draw·代价=额外内存存合并网格+构建时间；GPU instancing=同网格+同材质海量实例单 draw；dynamic batching=300 顶点帽·URP 得不偿失默认关【C×2 同构】
- 选择律【确认·C×3 收敛】「不动的件 Static 旗·海量同网格重复件 instancing·其余 SRP Batcher 常开」；SRP Batcher 深律=shader 变体最少化（官方「use as few shader variants as possible…as many different materials with the same shader as you want」）——同 shader 下多材质不伤 SRP batch；Static 与 instancing 对同一件互斥（进合并网格后不再实例化）→散件按「永动？海量重复？」二叉分道
- <256 顶点判据澄清【确认·C+M】顶点数小非 instancing 硬排除项（300 顶点帽属 dynamic batching 非 instancing·适配律=「同网格海量重复」）；但仓内 WebGL 群体律已定谳（R-alive3d-01 承接）：WebGL 上 SRP Batcher 优先于 instancing·光点类小件走单 buffer 合批/CPU 粒子——城内 120 路灯=静态件入 Static 合并组即可·instancing 留给万级同网格散布
- 量级【确认·C】社区实测 200 树+100 岩+1000 草=3200 batches→≈300（Static+instancing+图集收尾·CPU 降至 1/10·画面零变化）；平台预算 guideline（非硬帽）：低端移动<500·高端<1000·主机<2000·PC<3000——WebGL 按移动档盯（仓内 CPU 瓶颈律 M 同向）
- 定谳：大城合批正解=SRP Batcher 常开（变体最少化）+静态件 Static 旗（共享材质成合并组）+海量同网格散件 instancing——三通道互补非互斥·WebGL 侧沿仓内群体律执行。

## 二、图集纪律与材质变体最小化（判据②）
- 图集=合批前提【确认·C 原句】static batching 与 instancing 均以「同材质」为前提——逐件独立小纹理=逐件独立材质=零合批；图集=把「多纹理多材质」压成「一纹理一材质」、制造合批机会的准备工作（2D SpriteAtlas=同构内建）
- Synty 结构红利【确认·M 承接 R-02/R-05】flat=每包一张共享渐变图集+换色=挪 UV 不增材质（R-02 双 A 证已闭环）——全套件天然「少材质+同 shader」=三条合批通道全开·此即「全系列共享一张图集=大城性能基石」的机制本体
- 混包混材质代价【确认·C×2】批破坏清单=不同材质（同 shader 异纹理也算）/异 lightmap/异 shader 变体/透明不透明混排；SetPass（材质切换次数）比 Batches 更贵——材质与 shader 种类=比 draw call 更上游的纪律指标
- 变体最小化实践【确认·C+M】残余小纹理道具统一进图集换单材质；窗灯 emission 变体=优先 AD-022 自带 Emissive_01~05 贴图直供（总控技能承接）；MaterialPropertyBlock 逐件变色会破 SRP Batcher【C】——变色一律走挪 UV/材质分组
- 定谳：共享图集=解锁全部合批通道的基石·混包必须收敛到统一 shader+最少材质数——材质数是 City3D 第一性能纪律指标（比 draw call 计数更早盯）。

## 三、LOD 与 Occlusion Culling（判据③）
- Occlusion 机制与判据【确认·A】=烘焙数据剔除被完全遮挡的 Renderer（视锥裁剪不查遮挡）；官方适用判据「works best in Scenes where small, well-defined areas are clearly separated from one another by solid GameObjects」（房间-走廊型）·开销面=运行时 CPU 查询+烘焙数据占内存·收益面=GPU overdraw bound 时——URP 可走 GPU occlusion culling
- 程序化红线【确认·A 原句】「If your Project generates Scene geometry at runtime, Unity's built-in occlusion culling is not suitable」——扩展期程序化散布件不被烘焙遮挡覆盖·须单列裁剪路径（视锥+距离阈值）
- 城市适配【推测·工程判断】俯视角三档相机（L0 320m 总览/L2 24m 街景）看屋顶为主→遮挡收益低；L2/WebGL 参观低机位档收益才立·按 Profiler 实测定夺——本波不烘焙遮挡·留 L2 档触发器
- LOD 现状【待证】Synty 48 包自带 LOD：仓内实查件（R-02/R-05/48 包索引）零 LOD 记录+外部社区零直证（检索仅截断线索）→收口=下波 read_file 直读 AD-022/AD-015 prefab 抽验 LODGroup（本波子仓 ignore 屏蔽+读数触顶未执行）
- 定谳：本波不引入 LOD（POLYGON 件本已低模·压缩空间小+证据未闭环）；主流三径=LOD Group/第三方生成器/Impostor 均排后——合批与遮挡先做·Profiler 触发再上·外部工具须过 U288 核验闸。

## 四、场景组织：chunk 化/prefab 化/Addressables 流送·WebGL 侧（判据④）
- chunk=装卸单元【确认·A】Addressables 官方核心律原句「create AssetBundles that contain discrete sets of assets that you expect to be loaded and unloaded together」——按「同装卸预期」分组打包·恰为 16×16（32m）chunk 结构流送直证；依赖链自动载入+引用计数归零才释放→共享件（图集/材质）入公共组防重复膨胀
- additive 流送【确认·C×2+M】bootstrap 永驻+内容场景 additive 装卸（wallstop）；开源 StreamZones=Addressables+网格分块 additive 流送参照件（过 U288 外部件核验闸再采）；仓内承接=R-05 多场景三坑（跨场景引用禁/烘焙归属定死/异步时序）+prefab variants 组织已闭环
- WebGL 硬约束【确认·C 摘要级+M】社区实况=大场景 Addressables 多组在低端机浏览器内存崩溃（discussions 两帖同构）·100+ 场景帖共识方向=单 build 动态装卸优；仓内 WebGL 坑律承接（CPU 瓶颈/蒙皮变贵/后台节流挂钟）——首期单 build+内存纪律·远程 CDN 组后置
- 组织纪律【确认·C】大工程切小场景分文件=合并冲突少+迭代快+装卸尖峰可预测——与 chunk 化同构互证
- 定谳：数千件城=16×16 chunk prefab 化+按 chunk 分 Addressables 组（bootstrap 永驻+additive 装卸+图集材质公共组）——WebGL 参观端首期单 build·远程流送后置。

## 五、社区公认反模式清单（判据⑤）
- 材质类【确认·C】逐件独立材质/同 shader 异纹理=破三合批通道（解药=§二图集纪律）；MaterialPropertyBlock 逐件变色破 SRP Batcher
- 静态类【确认·C】非均匀缩放破 static batching（模块件摆整倍缩放）；dynamic batching URP 默认关（300 帽+CPU 合并得不偿失）
- 灯光类【确认·M】逐件实时灯=红线级——仓内灯光线已定谳 WebGL 灯预算 9 帽/16 保守+只烘 AO+Light Probes（city-3d-lighting 正典承接）
- 动画类【确认·M】逐件 Animator 待机装饰=反模式——群体走 VAT（R-alive3d-01/04 承接）+一次性脉冲走脚本驱动零 Animator（R-td-craft-perf-live 载体取舍律承接）·Animator 仅当状态机复杂度值得
- 散布与透明【确认·C+M】过密散布无公认密度数（R-05 已判待证·Phase 0 demo 基线收口）；透明混排破合批+overdraw=GPU 侧独立成本；程序化件不进烘焙遮挡（§三 A 证）
- 定谳：七坑全部可机检/法检——材质数·缩放·dynamic 开关·灯数·Animator 数·透明件数·散布密度=五闸闸1 产前五问量化检查项。

## 六、模块库拼装 vs AI 生成管线对比（判据⑥）
- 社区定位（四源摘要级收敛）【确认·C】AI 生成 3D=概念/灰盒/一次性静物/背景件/快速原型可用·「not reliably one-click production tools for…a consistent hero-asset」（wavect）——一致性=第一短板；工作室产线实证=三瓶颈（halabaojia）
- 效率对比【确认·C+M】模块库=乐高即时拼装（R-05 官方店拷「Modular sections are easy to piece together」已闭环）+75 demo=构图样本源；AI 生成=逐件时长+风格漂移+返工——规模化装配模块库完胜·单件 hero AI 有 niche
- 性能对比【确认·C 摘要级】AI 生成件自带独立贴图材质·需后置图集化工序才可合批（AI 资产图集实务文同构佐证）→逐件异材质直击图集纪律底线=合批基础崩坏；模块库共享图集=三通道天然全开——大城性能面模块库压倒性
- 集团红线承接【确认·M】库=唯一源律（CEO 令 09-29：3D 禁云端生成·资源库=唯一供给通道·我方=调用+标记）已定谳——本件外部证据（一致性短板+性能基础崩坏+后置图集化成本）=该令工程面佐证·非改判动议
- 定谳：模块库拼装=大城效率与性能双正解·AI 生成在集团禁令内冻结——外部共识与 CEO 令同向·零冲突。

## 七、结论应用表（research-protocol §二.1 强制·落点四选一）
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| SRP Batcher 常开+变体最少化+静态件 Static 旗+重复静态件合并组+散件 instancing 二叉分道 | 任务单：City3D 性能施工法（全盘方案性能节） | 接线中 |
| 图集纪律=材质数第一指标+MPB 禁令+emission 变体贴图直供 | 任务单：City3D 材质规范条款（承接 R-02/R-05） | 接线中 |
| LOD 本波不引入+遮挡仅 L2 档触发+程序化散布件裁剪路径单列 | 任务单：City3D 优化清单（Profiler 触发制） | 接线中 |
| 16×16 chunk Addressables 分组+bootstrap 永驻+WebGL 单 build 内存纪律 | 任务单：全盘方案「工程组织」节 | 接线中 |
| 反模式七坑入五闸闸1 产前五问量化检查项 | 法文修改：U288 同构 City3D 五闸检查单 | 接线中 |
| AI 生成工程面佐证（与库=唯一源令同向） | 决策呈报：CEO 令外部佐证注记 | 已闭环 |
| Synty LOD 现状未闭环（外部零直证+仓内 grep 未执行） | 判负留痕：下波 read_file 直读 prefab 抽验 | 已闭环 |

- 更新记录：T0 骨架早落盘→T1 面一（A+C 双源）→T2 面三/四（Occlusion+Addressables 双 A）→T3 面六+仓内正典承接→终稿 N 行（读数 20/20 触顶）。失败面：unitycodemonkey 登录墙不成源·2022.3 Occlusion 页重定向 404→6000.4 版代偿成源·Synty LOD 社区零直证·48 包仓内 grep 未执行（子仓 ignore 屏蔽+读数触顶）·Addressables 博客 17.5k 字符仅采前段（场景流送 cheat sheet 段未采·摘要级补偿）。防线二候选：①static batching 内存代价/300 帽属 dynamic 之机制分界（C×2 直读可复验）②「运行时几何不宜内置遮挡」适用边界（A 原句直读可验）。
