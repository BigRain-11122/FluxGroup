# R-20260928-lowpoly3d-city-tools-02 — lowpoly 3D 城市渲染与资产知识（Synty flat 风格·管线取舍·CC0/AI 资产·WebGL 参观端）
> 溯源：CEO 令 P-65 调研波「硅基生命城市 lowpoly 3D 转型·渲染与资产知识」2026-09-28·消费方=FluxVerse City 3D 转型全盘方案（Tuanjie 1.10.3=Unity 2022.3 基座·俯视角 3D 城市·Synty POLYGON 参照·WebGL 参观端）·判据预注册=①flat 渲染落地（顶点色/纯色材质·Built-in vs URP·渐变天空盒·俯视白天光照 baked vs realtime）②可商用 CC0 资产源+AI 生成低模面数实践③WebGL 参观端坑面（豁免已知判例：光照烘焙/内存/ASTC）

## 〇、采集账（占位收口）
- [x] T0 骨架早落盘 → [x] T1 仓内查重（polygon-style/light-daynight/assets-layers/toon-shader 四 R 件+POLYGON48 锚件·防重复调研）→ [x] T2 渲染管线域 → [x] T3 WebGL 域+许可域 → [x] T4 光照天空域+资产三径域 → 终稿

## 一、风格渲染定谳知识（判据①）
- flat 材质策略【确认·A×2 双证同构】业界两主流源同走「一张共享渐变图集」路：Synty 48 包仓内实测=每包仅 1-2 张梯度图集·平涂材质无 PBR 依赖（锚件《POLYGON48包》§三）；Kaykit 官方页原文「Textured using a single gradient atlas texture (1024x1024) that can be downsampled to 128x128」+「Low poly optimized models... including mobile」（kaylousberg.itch.io/kaykit-adventurers）→换色=挪 UV·同图集跨包混搭零违和
- 备选路=纯色/顶点色材质：URP+SRP Batcher 下「同 shader 任意多材质近乎免费」（A·Unity 官方博客）→纯色材质路机制可行；顶点色路（Kenney 式）本波未直证【待证·M】
- 管线取舍（Built-in vs URP）【确认·A 双源】：SRP Batcher 兼容表=Built-in:No·URP:Yes·HDRP:Yes（Unity 2022.3 Manual·SRPBatcher 页）；机制=不减 draw call 总数·只降 draw call 之间 CPU setup 成本·SetShaderPass 每 shader variant 一次（官方博客 2019）——城市场景恰是「海量同款材质」受益型
- 合批数字【确认·B=A 级官方博客原文】：总述「speed up your CPU during rendering by 1.2x to 4x, depending on the Scene」；实例 Book of the Dead(HDRP·PS4)×1.47·Boat Attack(LWRP·PS4)×2.13·FPS Sample(HDRP·PC)×1.23·最差场景(全动态+材质各异)×4(PS4·非 FPS 口径)；FPS Sample 余 1.67ms 滞标准路径=蒙皮网格+MaterialPropertyBlocks 所致（反例警示）
- 注意面【确认·A】：URP Asset 须手勾 SRP Batcher；官方注「低端设备若 shader 未优化，关 SRP Batcher 或更快」（SRPBatcher 页原文）→WebGL 低端机须 A/B 实测；Tuanjie=2022.3.x↔URP14 对应（仓内 toon-shader R·A×2 承接）；P3D_Spike 现为内置管线·Synty 部分包自带 URP_ExtractMe.unitypackage=切 URP 现成桥（锚件·仓内实测）
- WebGL 参观端坑面（判据③·非豁免面）【确认·A·Unity 2022.3 WebGL 手册】①GPU 近原生·CPU(WebAssembly)依浏览器=瓶颈面（webgl-performance 页）→SRP Batcher 数字在 WebGL 更承重；②无多线程/SIMD·mesh skinning 双优化失效=角色动画贵（同页）；③后台标签节流至约 1 帧/秒·Time.time 变慢→须挂钟时间兜底（同页）；④Exception support 应设 None（同页）；⑤targetFrameRate=-1 交浏览器节律·引擎假定 60fps 无法查询真值（同页）；⑥音频走 Web Audio API 兜底（FMOD 依赖线程不可用）·仅基础功能·麦克风不支持·pitch 仅正值（webgl-audio 页）；⑦Chrome Autoplay 政策=BGM 不经用户点击/触摸不自动播（同页·参观端首坑）

## 二、资产三径知识（判据②）
- 径① CC0 包【确认·A×2 官方一手直证】Kenney 官网 FAQ 原文「all game assets on the asset pages are public domain licensed (CC0)… free to use them, even in commercial projects」+「Attribution is not required」+禁用其 logo（kenney.nl/support）；Kaykit 包页「Free for personal and commercial use, no attribution required. (CC0 Licensed)」+页面元数据「Asset license: Creative Commons Zero v1.0 Universal」+禁转售未改原件+「No generative AI was used」（kaylousberg.itch.io）→两源皆商用零署名·证据=各自官网原文
- 径② AI 生成 lowpoly【确认·A=平台工具规格（自源）】Rodin Gen-2.5 档默认帽=Extreme-Low 20,000 面·Low 60,000 面；Tripo P2=quad 四边面输出·低面数档·平台钳 25,000 面（P1=默认档）；减面工具 tripo_decimate 目标域 500–20,000 面（Codely 平台工具规格）
- 面数实践判据【确认·锚件】+【推导】：Synty 件=几十~两千面（48 包实测·业界事实标准）；AI 档上限(2 万面)高出 Synty 件均值 1-2 个数量级→**AI 生成件入城前必过 decimate 至几百~2 千面**【推导】；Kaykit=低模移动端优化（A）；Tripo/Rodin 低模品质第三方口碑未采【待证·M·预算让位】
- 径③ 商用包（Synty 正版）：L1 红线承接=现存 48 包禁入交付链/提审面·正版单包 $20-60 常年 5 折·首批 6-10 包预案（polygon-style R+锚件·A 承接）

## 三、光照天空（判据①后半）
- 渐变天空盒【确认·A】：Skybox 组件 Built-in/URP 均支持（HDRP 不支持）（class-Skybox 页）；内置程序化天空随主定向光旋转联动变化·环境光可取天空盒色→「转主光即得晨昏/夜」（Types of light 页）
- 俯视角白天做法【确认·A+锚件】：定向光=太阳·抽象世界官方语义「add convincing shading without exactly specifying where the light is coming from」正合平涂城（Types of light 页）；平涂材质对直射光敏感→**斜定向光+烘焙 AO**（锚件 AD-048 实证）；俯视构图天空占屏极小→纯色相机背景或廉价渐变天空盒足矣【推测】
- baked vs realtime 取舍：烘焙/内存/ASTC=已知判例豁免（派工令明示）；WebGL CPU=瓶颈（A）+城市主体静态→**静态城烘焙化（Unlit/AO/光图）·实时光仅留动态件与角色**【建议·推测级·样区验证收口】

## 四、结论应用表（落点四选一·逐条「结论→全盘方案哪一节」）
| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| flat 材质=一张共享渐变图集（Synty/Kaykit 双 A 证）+纯色材质路（SRP Batcher 多材质免费）·顶点色备选 | 任务单：全盘方案「材质规范」节 | 接线中 |
| 管线=URP 取代 Built-in：兼容表 Built-in:No+CPU 提速 1.2x-4x+P3D_Spike URP_ExtractMe 桥 | 任务单：全盘方案「渲染管线选型」节 | 接线中 |
| WebGL 七坑清单（无线程/skinning/后台节流/异常 None/帧率交浏览器/音频受限/自动播放） | 任务单：全盘方案「参观端 WebGL」节 | 接线中 |
| Kenney+Kaykit CC0 官方直证（商用·零署名·合规入库） | 任务单：全盘方案「资产源与合规」节 | 接线中 |
| AI 生成件 2 万面档须 decimate 至 Synty 量级（几百~2 千）后入城 | 任务单：全盘方案「AI 资产管线」节 | 接线中 |
| Synty 正版采购 Gate（$20-60/包·首批 6-10 包）+L1 禁入交付链 | 决策呈报：预算授权位 | 已闭环（承接） |
| 渐变天空盒（URP 支持）+斜定向光+环境光取天空盒+静态烘焙化/动态实时 | 任务单：全盘方案「光照与天空」节 | 接线中 |

## 【验证声明】
- 读数 20/20 触顶：本地 7（技能件/R 模板/四 R 件+锚件）+外部 13（Unity 官方手册 6 页·Kenney/Kaykit 官方页 2·Unity 官方博客 2 段·商业博客 1·搜索 2）
- 成源：A=8（Unity 手册 SRPBatcher/webgl-develop/webgl-performance/webgl-audio/class-Skybox/Lighting·Kenney 官网·Kaykit 官网）+仓内锚件承接 3+平台工具规格（自源 A）；B=Unity 官方博客（SRP 数字·A 级作者）；C=搜索摘要（Kaykit 多包页佐证）；断言三态：确认 15·推测 3·待证 3
- 失败面：thegamedev.guru 前 5000 字纯叙事无数字→弃作承重源（未续读·预算让位）；docs.tuanjie.cn 本波未访（沿 toon-shader 波连接失败留痕·重访触发器在册）；GitHub API 全程零调用（配额纪律遵守）；Unity 博客为 2019 年 LWRP 期文·数字口径=CPU 渲染时间非 FPS（原文自注）
- 防线二候选：Kaykit 页 license 元数据（Creative Commons Zero v1.0 Universal）与 Chrome Autoplay 政策页两承重主张待主会话独立直验
- 调研完成时间：2026-09-28（终稿 42 行·帽 ≤60 内）
