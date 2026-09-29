# R-20260929-threejs-fit — Three.js 赋能面调研（CEO 令 O-2026-09-29-017·开源借力专项）
> 溯源：O-2026-09-29-017（CEO 原话「调查Three.js 看是否能赋能我们」）·消费方=BigDomain 参观端重态选型+HQ 观测线+CEO 决策面·判据预注册=三问
> 验证声明：实读 19（内档 4·web_fetch 9·检索 2·shell 4）≤20 预算·A=11（threejs.org r186/GitHub LICENSE 原文/npm registry JSON/微信官方 web-view+canvas+分包文档/微信官方 threejs-miniprogram 仓/Draco 官方 README/本地体积直测×2）·B=3·C=3。失败面：①官方 web-view 文档无「WebGL」明文→XWeb=Chromium 122/126（官方社区公告·检索快照）推断可用=B 级·判据帧实测收口②我方小程序主体类型内档未载→web-view 可用性待证③Babylon/model-viewer/PlayCanvas 许可与引擎 WebGL 包体数未双源直验=待证④glTF 导出器选型未 spike⑤Draco 官方 README 无硬性压缩比（仅定性 "significantly smaller"）

## 一、内档实况面（坑律/三态/gate/观测窗）
- 正典锚（A-内档 4 件直读）：底座=Tuanjie URP 主线+自研 SiliconToon；参观端三态在册（轻量态=判据帧截图流·建议档→中态=伪 3D 全景/视频→重态=真 WebGL·主载体 HTML 直载·压双 gate 随 City3D 稳定版开）；反双建律/敏感面（web 3D 禁金融行情视觉）/AIGC 标识照辖。
- WebGL 坑律（City3D 实测在册）：平台性部分 three.js H5 同继承（后台节流挂钟兜底/帧率交浏览器/音频仅 Web Audio/Chrome Autoplay）；引擎特定坑（SMR 不可 instancing/Exception=None/skin 双优化失效）=Unity WebGL 面·three.js 无此三坑但 JS 单线程 CPU 瓶颈仍在（推测）；three.js 原生 InstancedMesh 在 WebGL 可用（B·文档级通识未直读）=web 轻量城真差异点。
- L1/EULA 辖面（R-synty-doctrine A 级转载）：48 包淘宝转售零授权·原型/风格验证/规格研究=合规·商用面双 gate；EULA 游戏类 Product 默认覆盖·非游戏须书面另约·禁 NFT/区块链/元宇宙类·AI 用途全禁——**Three.js 渲 Synty 件同辖（许可在资产不在渲染器·MIT 渲染器不改资产授权）**。
- 观测窗（R-silicon-watch 直读）：file:// 直开·零服务器·三件套·红线含「2D/零服务器」+禁行情汇率入界面+源戳诚实律——b 面嵌 3D 的「2D 红线」**已被 09-28 T0 解禁令覆盖**（P-2026-09-28-12·cph4/CODELY 09-28 条明文「观测窗『全 2D』自检改『3D 开放』」·窗 09-24 规格系解禁前旧态·实况优先勘误）；批3 已埋「城市活动块/城 Canvas 鸟瞰（可选）」升级位。

## 二、三问逐答（确认/推测/待证三态·数字带出处）
**问① 赋能面逐面判定**
- a.参观端轻量 3D 城=**备选（限单景·全城 Three.js 版判负）**：技术成立（three.module.min 88KB gzip 实测+MIT+H5 直载；安卓 web-view=XWeb Chromium 122/126 基→WebGL 可用 B 级推断）；但全城版=城景二次装配+材质重做→触反双建，且重态正典已定引擎 WebGL 主载——Three.js 生态位=「我的化身在城中」定点合影位/地标单景（归属四阶梯轻量呈现）·与截图流互补；小程序 web-view 压「个人主体禁用（官方原文）+业务域名后台配置」双待证。读数：核心 88KB gzip+资产 KB 级 vs 引擎 WebGL 包体 MB 级（C 级通识）·CPU 瓶颈两者同在。
- b.元宇宙观测窗嵌 3D 卡=**备选（三面中技术契合最高·可直接推进）**：纯本地静态窗可整段内联 three.module.min（单文件零外部 import·B 级待实测）·与七司卡片共存·零网络加载（file:// 本地）；CEO 观测单屏单景=低负载；L1=内部观测面=原型容忍面不触商用 gate（确认·SKILL 红线 1）；「2D 红线」拦点已被 09-28 T0 解禁令解除（防线二纠·见 §一勘误）——技术零拦。
- c.网页内容嵌入（BigStream/落地页）=**adopt**：引擎 WebGL 包体（MB 级·C 级）不可嵌内容页→Three.js=内容面轻量 3D 唯一可行径（MIT·88KB gzip·CDN 直载·3D 件懒加载不占首屏）；自制件/CC0 件零 gate 即日可做·Synty 件入公域营销=商用双 gate；敏感面+AIGC 标识照旧。

**问② 资产管线可行性=「需重做材质」态**（几何/贴图可过桥·材质层重做）
- 过桥径：City3D/Synty→glTF→GLTFLoader（原生支持 glTF+Draco+meshopt+KTX2·B 级通识）；导出步需自建=引擎无原生 glTF 导出（C 级待证·UnityGLTF 社区件或 Blender 中转·待 spike）；低模+共享图集→几何压缩收益有限·体积主导=图集贴图单张（分析）；解码器实测（A·jsdelivr 0.186.1 直测）：draco_decoder.wasm 279KB raw/86.4KB gzip（Apache-2.0）·meshopt_decoder 7.5KB gzip·GLTFLoader 源码 25.4KB gzip；npm 全包 20.4MB/1263 文件（A·registry）→运行面只 ship 核心构建（ESM 按需）。
- 损失面：URP Lit→glTF PBR=近似映射；emission 须 KHR 扩展导出；Synty UV offset 调色板换色须烘焙为材质变体（推测）；**SiliconToon 不随 glTF 移植**→Three.js 端自写 ShaderMaterial toon：基础 ramp+emission≈1 人日档·对齐五色律/昼夜色轮/夜窗/雾≈3-5 人日档（推测·待 spike）。
- L1 同辖注记：内部原型/观测面合规·商用面同双 gate·EULA「元宇宙类 Product 须书面另约」不因换渲染器消失。

**问③ 平台约束与分工定谳**
- 微信生态 A 级直读：web-view「个人类型的小程序暂不支持使用」+「其它网页需登录小程序管理后台配置业务域名」+自动铺满全页+postMessage 仅后退/销毁/分享/复制链接四时机+插件不支持；原生 canvas type="webgl"=基础库 2.7.0+·「WebGL 暂不支持真机调试」·开发工具默认关 GPU 硬件加速；包体=「单个分包/主包大小不能超过 2M」·「整个小程序所有分包大小不超过 30M（服务商代开发的小程序不超过 20M）」；官方 threejs-miniprogram=「Three.js 小程序 WebGL 的适配版本」但停 r108（「当前使用的 Three.js 版本号为 0.108.0」·18 commits 实质弃更）→原生 canvas 路径=适配层老化维护风险。
- H5/WebGL：安卓微信=XWeb（官方公告现网 Chromium 122/开发版 126）→WebGL 可用 B 级推断·判据帧实测收口；桌面端有 webgl2 报障社区帖（C·2024）；微信内置浏览器跑 three.js H5=业界常态（C）。
- 分工定谳（反双建一句话）：**引擎 WebGL=主城发布面+参观端全城重态（City3D 单源·SiliconToon 零重做）；Three.js=轻量嵌入面（观测窗 3D 卡/内容页 3D 件/参观端单景合影位）——Three.js 禁建全城双份·参观端主载仍=截图流→引擎 WebGL 重态**。
- 替代面一行判定：Babylon.js=全功能 web 引擎更重·已有 URP 主线→**判负**（双建风险）；model-viewer=〈model-viewer〉声明式放 glb 零代码→**c 面最省工备选**（限纯展示件·许可待证）；PlayCanvas=引擎+编辑器整案=第二套引擎→**判负**。

## 三、赋能面判定总表（三候选面×判定+理由一行）
| 候选面 | 判定 | 理由一行 |
|---|---|---|
| a.参观端轻量 3D 城 | 备选（限单景）·全城版判负 | 技术成立但全城版触反双建+材质重做·主载维持截图流→引擎 WebGL·web-view 双待证 |
| b.观测窗嵌 3D 卡 | 备选（可直接推进） | 技术契合最高（file://+MIT+88KB 内联零网络）·2D 红线已被 09-28 T0 解禁令覆盖·窗面正典随批勘误 |
| c.网页内容嵌入 | adopt | 内容面轻量 3D 唯一径·自制/CC0 零 gate 即做·Synty 件双 gate |

## 四、结论应用表（落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| 三面判定+「引擎主城/Three.js 轻量嵌入」分工定谳+替代面判负（b 面 2D 红线拦点防线二已纠=解禁令覆盖·无翻案件） | 决策呈报（CEO 裁·本件即载体） | 待呈报 |
| c 面内容页 3D 嵌入（自制/CC0 件先行·禁金融视觉·懒加载） | 任务单（@BigStream 内容线） | 建议开单 |
| 管线 spike：glTF 导出步选型+SiliconToon→ShaderMaterial toon（3-5 人日档） | 任务单（@City3D·b/c 面前置） | 建议开单 |
| 微信待证清单：小程序主体类型/业务域名备案/XWeb web-view WebGL 判据帧实测 | 任务单（@FluxVerse·M4 前置核验） | 建议开单 |

## 更新记录：T0 骨架落盘（早落盘律）→ T1 内档 4 件+three.js 官方/许可 A/B 双源 → T2 微信 A 级直读+体积直测 → T3 三问收口+判定表+应用表·终稿 43 行（node fs 机检）
- 防线二（HQ 收口窗）：MIT 原文直验 ✓+微信 web-view 官方原文直验（「个人类型的小程序暂不支持使用」/业务域名后台配置/文档无 WebGL 明文=B 级推断成立）✓+**就地纠一处**：b 面「2D 红线待 CEO 翻案」系过时判读——09-28 T0 解禁令（P-2026-09-28-12）明文覆盖观测窗（cph4/CODELY 09-28 条「观测窗『全 2D』自检改『3D 开放』」）·已改 §一/§二/§三/§四 四处+本行留痕。
