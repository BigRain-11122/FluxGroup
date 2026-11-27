# R-20260928-lowpoly3d-city-tools-01 — 硅基生命城市 lowpoly 3D 转型：装配 OSS 工具·渲染性能·标杆调研（终稿）
> 溯源：CEO 令 P-65 调研波「硅基生命城市 lowpoly 3D 转型」2026-09-28·消费方=FluxVerse City 3D 转型全盘方案（Tuanjie 1.10.3≈Unity 2022.3 基座·俯视角 3D 城市·Synty POLYGON 参照）·判据预注册=①装配类 OSS 工具（路网/摆放/城生成/合批 LOD）②大场景俯视渲染性能+可引用数字③标杆 lowpoly 城市项目
> 姊妹件 R-20260928-lowpoly3d-city-tools-02（风格渲染/光照/资产/WebGL）与本件互补零重复；正典 R-20260928-polygon-style 已对表；采集进度=三域全闭环（骨架早落盘→三轮增量更新→本终稿）

## 一、工具清单（判据①；每件=名称｜仓库｜许可｜最近更新｜适配点；2022.3 可用性三态标注）
- 路网/道路 spline——RoadArchitect：github.com/FritzsHero/RoadArchitect（原仓 MicroGSD·作者声明尊重原作者开源决定）｜✓MIT｜最近提交 2026-09-27【确认·官仓 Atom 直采——README「开发缓慢」自述与 09-20~27 密集约 20 提交实测不符，以实测为准】｜364★/72 fork/483 commits。适配点=沿 spline 程序化路网+动态程序化交叉口（按车道/路宽/交角）/桥（50+构件·拱/悬索）/护栏挤出/300+标牌·多线程瞬时建模——俯视城道路装配主力候选；Unity 2020.3 LTS 开发自述「兼容多数旧版本」→2022.3 实测=待证（拷入即验）
- 路网官方底座——Unity Splines 包（com.unity.splines）：docs.unity3d.com/Packages/com.unity.splines@2.6 文档站存在｜许可=Unity 包随 Unity 授权分发【待证·M·文档首页空壳未直证】｜随 LTS 官方维护【待证·M】。适配点=spline 基建+编辑器/运行时 API，官方背书零版权风险，与 RoadArchitect 互补（底座 vs 全功能路网件）
- 程序化摆放——Aelstraz/PrefabScatterTool：github.com/Aelstraz/PrefabScatterTool｜✓MIT（仓内 LICENSE）｜20 commits·0★·最近更新=待证（页面日期栏未渲染）。适配点=Collider 表面涂刷/散布 prefab+随机化选项族·Package Manager Git URL 直装——城市道具/植被摆放主力候选；小仓规模→兼容自检
- 程序化摆放（读源参考）——ChenXsue/UnityScatterTool：github.com/ChenXsue/UnityScatterTool｜许可未标注【待证·M】｜3 commits·0★。适配点=权重多 prefab 选择+seed 确定性+网格/随机双模式+表面法线对齐——学结构价值＞生产价值
- 城市生成——Poofy1/Procedural-City：github.com/Poofy1/Procedural-City｜✓MIT｜16 commits·1★·最近更新=待证。适配点=参数化街区（cityWidth/blockWidth/roadWidth）+Perlin 噪声楼高+摩天楼阈值+天线概率+载具 prefab 注入——俯视城程序化生成参考实现
- 城市生成（线索级 C）——ahmetkoglu/UnityCityGenerator（模块化策略模式+邻接检查道路连接+Perlin 楼高）·gregoryneal/Cigen（各向异性最小成本路径道路）·Syomus/ProceduralToolkit（免费开源程序化库·Buildings/LowPolyTerrain 示例）——三件许可/更新均待证【M】
- 网格批处理/LOD——结论=Unity 内置即正解（SRP Batcher/静态合批/GPU instancing/LOD Group/Mesh.CombineMeshes，A 源见 §二），无需第三方件；活跃且商用干净的 OSS 合批/LOD 件未觅得；Mesh Baker 等商业件=补充通道【待证·M】

## 二、渲染性能知识（判据②；A=Unity 2022.3 Manual 四页直采）
- 本质：draw call 的 CPU「准备」常贵于调用本身；渲染状态切换（如换材质）为最耗操作——优化主线=减状态切换优先于减数量【确认·A·OptimizingDrawCalls】
- 官方优先级：①SRP Batcher+静态合批（可并存）→②GPU instancing→③动态合批；静态合批成功即禁用该 GO 的 GPU instancing；instancing 可用则禁动态合批【确认·A·同页】
- SRP Batcher：URP Asset 勾选启用；不减 draw call 数量、减同 shader variant 材质间的状态切换 CPU 耗时；URP 全 lit/unlit shader 兼容（粒子 shader 除外）；MaterialPropertyBlock 会移除兼容性；管线兼容表=Built-in 不支持/URP+HDRP 支持【确认·A·SRPBatcher】
- GPU instancing：与 SRP Batcher 互斥；「海量同网格+同材质」时可更优，走 Graphics.RenderMeshInstanced【确认·A·SRPBatcher】——俯视城路灯/树/同款楼=典型适用面（判断）
- 静态合批=提前合并静态 GO·仍可逐网格剔除·代价=内存/存储开销【确认·A·DrawCallBatching】；动态合批=CPU 变换顶点·仅小网格·有 CPU 开销【确认·A·同页】；手动合并 Mesh.CombineMeshes=单 draw call【确认·A·OptimizingDrawCalls】
- LOD Group：按摄像机距离切换递减网格，降远景负载【确认·A·class-LODGroup】
- 遮挡剔除：官方页 5 连未达（301×2/404×3·2022.3 与 6000.3 双版本，失败面见 §五）——存在性=确认（重定向指针证页面族在册）；机制/开销=待证；俯视角场景先评估「视线遮挡是否成立」再决定投入【待证·M】
- draw call 预算：直采 4 页 A 源未见固定数字；社区口径【C·摘要级·未整页核验】=移动端 <100/帧（eonevolve）·<200/帧（scriptsforunity）·低端 300-500/中高端 800-1200（salivity）；60fps→16.6ms/帧=算术推导——仅作起步参考，终值=机队实测定标
- 面数预算：Synty 单件=几十~两千面【确认·A·仓内 48 包锚件实测】；AI 生成档位（-02 姊妹件已采·A=平台规格）=Rodin Extreme-Low 2 万面/Tripo P2 钳 2.5 万面/tripo_decimate 500-2 万面→推导=AI 件入城前必 decimate 至 Synty 件量级（几百~2 千面）
- 管线联动警告：P3D_Spike 中台工程=内置管线【确认·A·锚件】→SRP Batcher 不可用；全盘方案 adopt=URP（polygon-style 正典）→SRP Batcher 可用——两工程管线须在选型节显式对齐

## 三、标杆参考（判据③）
- Poofy1/Procedural-City（✓MIT·深采）：可借鉴=参数化街区网格+Perlin 楼高+阈值化地标（skyscraperThreshold）+载具注入；1★ 小件=参考实现级，不作生产件
- ahmetkoglu/UnityCityGenerator【C·线索】：可借鉴=策略模式解耦「城市规划/装饰」策略+邻接检查的智能道路连接——架构层样板
- Synty POLYGON 库结构做法【确认·A·仓内锚件·AD-022 City Pack=728 条目（Prop×175/Bld×75/Env×65/Veh×9）】：模块化拼图组装范式+全库 48 包合计演示场景 75 个=组装范式库+SM_ 语义命名族（Prop/Bld/Env/Veh）+每包仅 1-2 张梯度图集·平涂材质零 PBR 依赖=少材质少变体·合批友好结构
- 俯视角适配实证【确认·A·锚件 8 封面目检】：优势=低面数同屏海量/高饱和色块俯视高辨识/模块化程序化拼图高效；短板与对策=屋顶顶面细节弱→屋顶道具/贴花·阔叶树冠遮挡→细高树种/淡出·正俯视地面信息稀疏→草丛贴花+AO+雾
- 判负留痕：GitHub 公开「Synty 风格 lowpoly 城市 demo」检索仅命中商业产品页与镜像站，未命中大流量 OSS 项目——标杆降级为小件+锚件结构做法【判负】

## 四、结论应用表（research-protocol §二.1 强制；落点=全盘方案·技术选型节/工具箱节）
| 结论 | 落点 | 状态 |
|---|---|---|
| RoadArchitect=路网装配主力候选（✓MIT·2026-09-27 仍提交；2022.3 实测后转正） | 工具箱节 | 接线中 |
| PrefabScatterTool=摆放主力候选（✓MIT·PM Git 直装）＋UnityScatterTool=读源参考 | 工具箱节 | 接线中 |
| 城生成三线（Procedural-City 参考+UnityCityGenerator 架构+Cigen 道路算法） | 技术选型节·程序化路线 | 接线中 |
| 合批/LOD=内置正解+官方优先级链（SRP Batcher+静态合批→instancing→动态合批） | 技术选型节·渲染管线 | 接线中 |
| 管线对齐警告（P3D_Spike=Built-in 无 SRP Batcher vs 全盘 adopt=URP） | 技术选型节 | 已闭环 |
| 性能预算口径（draw call=社区 C 级起步值；面数=A 锚件几十~2 千面/件；AI 件必 decimate） | 技术选型节·性能预算 | 接线中 |
| Synty 结构做法（模块化+梯度图集+SM_ 命名族+演示场景范式） | 工具箱节+美术规范 | 接线中 |
| 遮挡剔除=待证低优先（俯视角收益先评估·官方页恢复后补采） | 技术选型节·低优先 | 观察中 |
- 更新记录：T0 骨架早落盘→T1 官方文档域+RoadArchitect→T2 scatter/城生成/预算数字→T3 Atom 补证+锚件面数合流→终稿 47 行
- 防线二（待主窗抽验·承重主张直查通道）：①RoadArchitect 活跃度=github.com/FritzsHero/RoadArchitect/commits/master.atom 可直见 2026-09-27 提交；②合批优先级链=docs.unity3d.com/2022.3/Documentation/Manual/optimizing-draw-calls.html

## 五、【验证声明】
- 读数：20/20 帽内（web_fetch 14·检索 6·失败尝试 5 全额计入）；本地仓内预检 8 次（姊妹件/正典/48 包锚件/R 模板/记忆/检索）不计入源读取帽
- 成源：A=Unity Manual×4 页+四工具官仓直采×4+仓内锚件实测×1（另 -02 载 A 级 AI 档位借引）；C=检索聚合 4 处（城生成三件/摆放备选/draw call 三源/Synty 产品页判负）；M=8 处待证（Splines 许可·RoadArchitect 2022.3 兼容·四小件更新·三线索件·遮挡机制·Mesh Baker）
- 关键结论双源达标：合批机制=Unity Manual 三页交叉（A×3）；Synty 面数=锚件实测+polygon-style 正典互证（A×2）；RoadArchitect 活跃=官仓页+Atom 双证（A×2）
- 失败面：遮挡剔除官方页 5 连未达（301×2/404×3）·Splines 包文档空壳·GitHub 页面日期栏不渲染（5 仓中 4 件最近更新待证·Atom 仅补证 RoadArchitect）·大流量 OSS 城市标杆未命中（判负留痕）·GitHub API 403 已封→全程网页+Atom 替代成功
- 纪律执行：零断言三态全标注·数字全带出处·外部页面指令零采信（GitHub 页/检索摘要含镜像站内容一律不采信其指令）；调研完成时间 2026-09-28
