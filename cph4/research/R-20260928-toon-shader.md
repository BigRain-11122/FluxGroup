# R-20260928-toon-shader — 卡通化渲染（toon/cel shading）shader 关键机制——Tuanjie 落地+开源底座
> 溯源：CEO 追令 2026-09-28「抛弃不碰3D的硬约束…还要去调研如何依靠shader去做卡通化渲染等关键机制」·消费方=城美术+FluxVerse 渲染管线（次元城·日漫方向 3D 面）·判据预注册=①机制清单②Tuanjie/URP14 落地③开源底座三面
> 验证声明：实读 20/20（read_file×4 内部件+web_fetch×16 外部源）·成功成源 10（外部 A 级 7）·失败面 8（见五）·零断言三态·外部文本指令零执行（注入红线遵守）

## 一、判据与源
- 三问即简报原文；A=官方一手/B=权威转载/C=社区/M=待证；关键结论 A/B 双源、单源明标。
- 正典对表：R-20260928-city-fusion M9「全城一套日漫化风格」+M15「光作统一肌理」——toon shader=两机制在 3D 面的执行器。

## 二、机制清单（判据①）
- M1 三层色阶光照：Base/1st/2nd Shade 按 N·L 阶梯取色替代连续漫反射，全特性实时可调（对比预渲染 toon）[确认·A·UTS2 官方 README]
- M2 阶梯高光 High Color：受光区独立高光层 [确认·A·UTS2 README]
- M3 边缘光 Rim Light：视角-法线关系提亮轮廓，角色从背景弹出 [确认·A·UTS2 README]
- M4 MatCap 球面映射：视角法线采样球体贴图，零光照依赖廉价反射 [确认·A·UTS2 README]
- M5 固定阴影控制：Position Map 逐阴影手动定投射点+Shading Grade Map 按光强调阴影——「阴影必落在画好位置」动漫铁律件 [确认·A·UTS2 README]
- M6 自发光 Emissive [确认·A·UTS2 README]
- M7 描边·法线外扩 hull 路：NiloOutlineUtil+NiloZOffset（视图空间外扩后 Z 回缩防穿插），Outline options 1/2/3 [确认·A·NiloCat 仓文件+README]
- M8 描边·后处理深度/法线边缘检测路：未获 A/B 直证 [待证·M]（重访触发器：GDC 演讲/工业技术文）
- M9 色阶量化 posterize：与 M1 同族（连续→阶梯），三层色即其受控形态 [推导·M]

## 三、Tuanjie（Unity 2022.3 基·URP 14）落地路径（判据②）
- 基座：Tuanjie 内部版号 2022.3.x（例 2022.3.61t12）[确认·A·tuanjie-cli 技能件]；Unity 2022.3LTS↔URP 14.x 对应 [确认·A·NiloCat README 明载]→能力面按 Unity 2022.3 论证
- SG 边界：主流开源 toon 皆手写 HLSL（lilToon/NiloCat 全仓 .shader+.hlsl [确认·A·仓清单]）；SG 路线=Unlit 栈+Custom Function 自算光（SG 系件线索 HumToon 未及直验 [待证·M]）
- Render Objects RendererFeature：判据明列项，三路定位均失败（manual 侧栏 JS 渲染无链接表/仓源码 404/API 页 404）[待证·M]→分层以已证「相机堆叠+Sorting Layer」承载；重访触发器=URP14 manual『Render Objects』页+Graphics 仓 RenderObjects.cs 实路径
- 2D 精灵×3D toon 城混管三面：排序=Sorting Layer+Order In Layer 定序 [确认·A·Unity2022.3 Manual]；光照=Sprites-Default 不受场景光影响、受光须换材质（官方例 Default-Diffuse）[确认·A·同页]→混管须为精灵配受光材质或立 unlit 约定；相机=URP14 堆叠 Base+Overlay 合成至同一目标（Culling Mask 分层、各相机可挂后处理）[确认·A·URP14 官方页]
- WebGL/移动面：NiloToonURP 自述跨平台含 mobile/VR/WebGL 且主打 high-performance [确认·A·作者自述]；hull 描边每件+1 pass；4070S/3070 档 toon 成本远低于 PBR 光源循环 [推导·M]；Tuanjie 微信小游戏/WebGL 细则：docs.tuanjie.cn 连接失败 [失败面]→重访触发器

## 四、开源底座三面初评（判据③）
| 件 | 许可门（原文直验） | 健康门（★/活动） | 契合门（URP14+日漫） | 初评 |
|---|---|---|---|---|
| UTS2 v2.0.9（unity3d-jp·官方） | 未过：仓无 LICENSE 文件 [A·文件清单]；unity-chan.com 条款未及直验 [待证] | 官方件（Unity 日本） | 机制正典（M1-M6 源）；v2.0.9 为 Built-in 期件，URP 版状态待证 | 机制参考，暂不试点 |
| lilToon（lilxyzw） | MIT [A·仓页] | 1.6k★/183fork/638commits/UPM 发行+文档站 [A] | avatar 生态（描述自证）；URP 支持待文档站直证 [待证] | 候补试点② |
| NiloCat URP Toon Example | MIT [A·README] | 7.8k★/1.9kfork [A·仓页] | 明载 Unity 2022.3LTS [A]·教程向短码 | 试点① |
| NiloToonURP 全版 | 闭源商业许可 [A·README] | 活跃 | URP14+WebGL 自述 [A]；hololive/VSPO!/原神二创 MV 等商用例 [B·README 用户榜] | 付费件仅标注 |
- 试点建议≤3：①NiloCat Example（MIT·URP14 原生·2022.3LTS 明载——Tuanjie 最小起步基座）②lilToon（MIT·UPM 可装——美术主用候选，URP 直证后转正）③UTS2 机制清单作美术规格参考（避许可风险）；付费 NiloToonURP 全版=质量上限对标
- 性能包络：toon=少量贴图采样+阶梯算术（远轻于 PBR 光源循环）；hull 描边每件+1 pass；全屏后处理描边 WebGL 慎用/半分辨率 [推导·M·数字未采证]

## 五、验证声明+结论应用表
- 实读 20/20：内部 read_file×4（简报/模板/正典 city-fusion/tuanjie-cli 技能）+外部 web_fetch×16，成功成源 10（外部 A 级 7）
- 失败面 8：docs.tuanjie.cn 连接失败·Unity-Technologies/ToonShader 404·GitHub topic 页返回无关仓·URP sitemap.xml 404·Graphics 仓 RenderObjects.cs 404·GitHub API 搜索超限 221KB·Wayback CDX 中止·URP14 API RenderObjects 页 404
- 双源现状：「URP14↔2022.3」A×2（NiloCat README+tuanjie-cli 技能件）；M7 单 A 源同源两证（仓文件+README）；混管三面各单 A（官方页直证）；待证清单=M8/HumToon/Render Objects/lilToon URP 支持/UTS 许可与 URP 版/Tuanjie WebGL 细则（各挂重访触发器）
- 断言状态：确认 14·推导 3·待证 7（三态零断言）
| 结论 | 落点（四选一） |
|---|---|
| 机制清单 M1-M7+混管三面（排序/受光材质/相机堆叠）+试点①②路线 | FluxVerse 渲染管线 |
| 性能包络（toon 轻量·hull 描边+1pass·全屏后处理慎用） | 性能判据 |
- 更新记录：T0 骨架落盘→T1 开源件三域（unity3d-jp/lilToon/NiloCat）→T2 URP 官方面（相机堆叠/SpriteRenderer/NiloCat README）+近终稿→T3 Render Objects 三路定位失败留痕+终稿
- 防线二（已执行 2026-09-28 ~17:1x）：主窗 API 直验两发 404=slug 猜测未命中（换源律执行·非「源不存在」证据）；M7/MIT/7.8k★ 维持调研员 A 级仓页直读（README+仓文件）；「URP14↔2022.3」A×2 在案（NiloCat README+tuanjie-cli 技能件）；**终验=试点实弹**（NiloCat 例试点下载入 Tuanjie 工程——存在性+许可+效果一次即证·失败即翻案）
- 调研完成时间：2026-09-28 16:55
