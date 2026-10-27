# R-20261023 小游戏 / 引擎 / AI 管线扫描（Biggame）

> 窗口 2026-08-23～10-23。分级：A=官方一手；B=行业媒体/榜单机构；C=厂商营销页（不单独作依据）。“未取得”=窗口内查无。

## 一 条目

| # | 名称 | 日期 | 链接 | 是什么 / 对我们的用处 | 结论 |
|---|---|---|---|---|---|
| 1 | 团结引擎 1.10.0 | 2026-07-27（窗口前；文档 2026-10-08） | [官方发布说明](https://www.nxrte.com/zixun/70415.html) · [手册](https://docs.unity.cn/cn/tuanjiemanual/Manual/index.html) | 小游戏首次全面逻辑多线程（Job/Burst/Managed/System.Threading）、AnimGraph 1.0 正式版、Infinity 粒子正式版、Timeline 1.7.7-t1；文档另列 HMI Android AppView 支持 Vulkan、QNX 8.0 Vulkan（检索摘要，未逐页核，B） | **采用**：小游戏 CPU 瓶颈与车机 Vulkan 都直接命中；先做 1.10 升级评估 |
| 2 | 小游戏 Instant Asset 工作流 | 文档 2026-10-08 | [手册页](https://docs.unity.cn/cn/tuanjiemanual/1.10/Manual/WhatsNew1.10.html) | 场景资源打包进 StreamingAssets / CDN，运行时按表加载；是首包 4MB 的官方解法 | **采用**：P01 首包方案按此改 |
| 3 | 微信小游戏包体规则 | 长期有效 | [官方文档](https://developers.weixin.qq.com/minigame/dev/guide/base-ability/code-package.html) | 主包 ≤4MB、代码包总大小 ≤30MB | **采用**：写成构建硬门 |
| 4 | 9 月微信小游戏畅销榜 | 2026-10-08 | [GameLook](http://www.gamelook.com.cn/2026/10/603357/) | TOP100 换血率 23%（近三月最低），TOP50 仅 1 款新品；模拟经营占 TOP10 三席；RPG 38 款但头部仅 2 席 | **采用为立项参照**：新品头部窗口在收窄 |
| 5 | 9 月小游戏六榜 | 2026-10-15 | [游戏客栈](http://www.gamekezhan.com/news/20261015/65206.html) | 微信畅销 TOP30 零新游；微信畅玩 TOP30 进 6 款新品；抖音热门榜进 10 款新品；双平台畅销重合 16 款 | **采用**：抖音=新品试验场，微信=长线收割 |
| 6 | DataEye 2026H1 买量报告 | 2026-09-12（转载） | [搜狐](https://www.sohu.com/a/1073460369_121819701) | 小游戏日耗 1.76 亿(+26%)，IAA 日耗 3410 万(+47%)；素材 2680 万条(+30%)；抖音 IAA 占比 74.7%→79.8%；轻休闲在投 1.5 万款占 70%+ | **采用**：IAA 是增量，素材产能是瓶颈 |
| 7 | 2026 微信小游戏大会数据（背景） | 2026-05-27 | [搜狐](https://www.sohu.com/a/1028424752_121124868) | MAU 5 亿+；IAA MAU 4 亿+、70% 用户只玩 IAA；IAP MAU 3 亿+；IAP 首发 5000 万流水内不分成；IAA 分成最高 90% | 采用（政策窗口，B） |
| 8 | AssetRipper 2.0.0 | 2026-08-24 | [Release](https://github.com/AssetRipper/AssetRipper/releases/tag/2.0.0) | Unity 包资产/脚本提取；支持 C#13–15、改进混淆代码反编译、shader 反编译（付费版） | **采用（限自家包体审计）**：核验发版包是否误带源工程/未授权素材 |
| 9 | ILSpy 11.1 | 2026-09-23 | [Release](https://github.com/icsharpcode/ILSpy/releases/tag/v11.1) | .NET 反编译；C#14 支持 + 大规模回归工具（nugetfuzz/decompdiff） | **采用（限自有程序集/第三方许可核查）** |
| 10 | Il2CppDumper / Cpp2IL | 2024-07-06 / 2022-09-26 | [Il2CppDumper](https://github.com/Perfare/Il2CppDumper/releases) · [Cpp2IL](https://github.com/SamboyCoding/Cpp2IL/releases) | 窗口内**未取得**新版；AssetRipper 2.0 已内置较新 Cpp2IL | **不采用**：无新进展，且不做竞品拆包 |
| 11 | 团结 AI Graph（1.10 包） | 文档 2026-10-08 | [包文档](https://docs.unity.cn/cn/Packages-cn/cn.tuanjie.ai.graph@1.0/manual/) | 引擎内 AIGC 工作流：2D 图/文本→纹理、3D、绑定参数；与 Sprite/Mesh/Material/Animation 直连，Inspector 一键生成替换 | **待验**：2D 立绘/图标可试；须先核商用条款与素材合规 |
| 12 | AI 2D 资产工具现状 | 2026-09 更新 | [Cinevva](https://app.cinevva.com/zh-CN/guides/ai-pixel-art-generators) · [Summer Engine](https://www.summerengine.com/zh/blog/ai-2d-game-asset-generator) | 单帧（角色/图标/背景）成熟；同一角色连贯动画帧、无缝图块集仍弱 | **部分采用**：动画帧仍走现有 2D 管线 + 人工修帧 |
| 13 | AI 关卡数据生成 | 窗口内**未取得**一手管线 | [C 级示例](https://www.summerengine.com/zh/ai-level-generator) | 均为厂商页/博客，无可复现管线与验收数据 | **不采用**：只走自建 JSON schema + 约束解码 + 校验器 |
| 14 | Unity 6.3 LTS / 6.6（6000.6.x） | 6.6 补丁 2026-10-01 | [6000.6.4f1](https://unity.com/releases/editor/whats-new/6000.6.4f1) | Unity 6.x 线持续发版（IL2CPP 元数据瘦身、URP 修复等） | **不采用**：团结基于 Unity 2022 LTS，特性不流入；仅作包体/IL2CPP 思路参照 |
| 15 | 高通 8295 规格 | 长期规格 | [EET-China](https://www.eet-china.com/mp/a255024.html) · [IT之家](https://www.ithome.com/0/695/559.htm) | GPU 2.9 TFLOPS(FP32)/5.8(FP16)、NPU 30 TOPS，一颗可带 11 屏 | **采用为预算基线**：4K 不是免费项 |
| 16 | DataEye-ADX MCP | 2026-09-28 | [资讯](https://gamenewstc.com/nd.jsp?id=4716) | ADX 开放 MCP，agent 可直接查榜单/素材数据 | **待验**：接入后周榜可自动核验 |

## 二 与我方现行做法冲突

**C1 4K 基线**
- 我们：4K/60 为基线，CPU/GPU ≤30%。
- 外部：8295 FP32 仅 2.9 TFLOPS（B），一颗芯片还要分给多屏；车机 HMI 实践普遍按分辨率/Draw Call 分级（B/C）。
- 后果：4K@60 下 30% GPU ≈ 0.87 TFLOPS（我方推算），后处理+UI 合成几乎吃满；低配或多屏并发必掉帧，美术预算还被一次性锁死。→ 建议 1440p 渲染 + 4K UI/视频层 + 超分，4K 只做 UI 基线。

**C2 HTML 原型 → 一次性移植**
- 我们：HTML 验循环、数值定稿，再一次性移植引擎。
- 外部：微信主包 4MB / 总 30MB（A）；小游戏多线程 1.10 才刚具备（A/B）；抖音热门榜月进 10 款新品、微信畅玩 TOP30 月进 6 款（B）——迭代节奏按周算。
- 后果：HTML 阶段验证不了包体、WASM 线程、真机 GPU；问题全堆到移植期爆发，返工落在最贵环节，且“一次性”追不上榜单换血。→ 原型第 2 周起加“最小构建”，量包体/线程/真机帧。

**C3 90 关线性排布**
- 我们：90 关线性推进，内容成本前置。
- 外部：微信畅销 TOP30 零新游、头部固化（B）；70% IAA 用户只玩休闲、人均月玩 7.5 款（B）；平台点名“创意单局类、素材依赖类”潜力（B）。
- 后果：留存实际由前 3–5 关决定，后面 85 关在验证前就沉没；线性结构也不利于买量切“单局即爆点”。→ 前 10 关做单局闭环+可变参数，90 关降级为参数化关卡池。

## 三 本周可落地（≤3）

1. **包体/线程基线**：用团结 1.10 打 P01 微信小游戏包，跑“开/关 Job 多线程”两版。验收：`build-report.md` 含主包 MB、总包 MB、启动 ms、主线程 CPU 峰值 ×2 组；主包 ≤4MB 判定输出为布尔值。
2. **4K 预算实测**：吸嘟嘟车机场景在 8295 实机（或 GPU 锁 30% 等效）跑 4K 与 1440p 各 5 分钟。验收：两份 CSV（帧时、GPU busy），末行给出“4K 下 GPU busy ≤30%：是/否”。
3. **前 10 关参数化**：前 10 关抽成 JSON（难度参数、单局时长、广告点）。验收：10 个 JSON 过 schema 校验 100%，本地模拟 100 局 0 报错，输出 1 页对照表。

## 四 分级与缺口

- A：团结 1.10 手册/包文档、微信包体规则、AssetRipper/ILSpy Release、Unity 版本页。B：GameLook、游戏客栈、DataEye 转载、微信大会报道、8295 规格。C：AI 工具站与博客（仅作线索，不单独作为依据）。
- **未取得**：团结 1.10 之后（08-23 起）的新版本发布记录；抖音官方 2026 Q3 白皮书；AI 关卡的公开可复现管线与量化验收；8295 上 4K Unity 实机帧率公开数据。