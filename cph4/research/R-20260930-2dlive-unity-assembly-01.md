# R-20260930-2dlive-unity-assembly-01 · 团结引擎/Unity 2022.3 线·2D 序列帧动画的引擎组装正法与验收判据

- **令号**：CEO 令 O-20260930-1856（O-1706 追加令）· 调研路 1
- **日期**：2026-09-30（周三）
- **产线背景**：2D 动作/特效唯一产线＝本地生成短视频→取关键帧→sprite 图集→引擎内代码逐格播放（本件负责把「Unity 引擎如何正确组装」环节钉死）
- **工程基座**：团结引擎（Tuanjie）1.10（Unity 2022.3.62t12 线）· URP · 竖屏 1080 宽参考分辨率 · 微信小游戏+Win64 双面
- **证据分级**：✓＝两独立源互证（含「公司判例×官方文档」「团结镜像×Unity 官方」双通道；官方文档双通道同刊亦按 ✓ 记）／🟡＝单源或社区（官方单源亦记此级并注明）／⬜＝未验证（内部工程判断）／✗＝判负勿采用
- **取证方法说明**：全部 URL 于 2026-09-30 实测可达性；官方页内容以抓取原文为准；凡引用均给 URL 锚。

---

## §0 结论速览 —— SOP 章可直接照抄的判据表

| # | 判据项 | 判据值（可执行） | 证据级 | 出处 |
|---|--------|------------------|--------|------|
| 1 | 图集律 | 交付恒＝sprite 图集（网格 cell+统一锚点）+引擎内代码逐格播放；运行时禁 Animator | ✓（O-001/U276 立法） | §三 |
| 2 | 压缩档 | WebGL Normal＝ASTC 6x6（High=4x4/Low=8x8）；微信官方定位「ASTC＝小游戏环境主要压缩纹理格式」；引擎版>2021 用引擎自带 ASTC（官方明示） | ✓（U276×微信官方页互证） | §四/§五 |
| 3 | 微信包体 | 官方原文：总代码包≤30M、主包≤4M、单个分包不限大小；首屏 4 秒线；公司首资源包保守线 20MB | ✓（U276×官方页互证） | §五 |
| 4 | 图集创建 | `Assets > Create > 2D > Sprite Atlas`；Objects for Packing 可收精灵/纹理/文件夹（目录打包合法） | ✓（官方双通道） | §一 |
| 5 | 图集属性 | Padding≥4px（ASTC 6x6 面建议 12px）；Allow Rotation 关；Tight Packing 关；Read/Write 关；Mipmap 关 | ✓（默认值官方）／🟡（12px 倍数规则） | §一 |
| 6 | Include in Build | 关＝图集不随构建、精灵运行时空白直至 late binding；远程图集走 `SpriteAtlasManager.atlasRequested` 手动绑定 | ✓（官方双通道） | §一 |
| 7 | atlas 页 | 单页≤2048（内部帽）；SpriteAtlas 无强制 POT；超页拆集 | 🟡（内部保守线） | §一 |
| 8 | 切片 | Sprite Mode=Multiple+Grid By Cell Size（512×512）；pivot 九预设统一（特效 Center/角色 Bottom）；重切恒 Delete Existing | ✓（官方双通道） | §二 |
| 9 | Filter/PPU | 放大播放恒 Bilinear（像素风 1:1 才 Point）；PPU 恒默认 100（UI 走 Canvas Scaler；世界层用正交 size 对齐参考分辨率） | 🟡（官方语义+内部判据）／⬜（PPU 约定） | §二 |
| 10 | 播放器 | 预载 `Sprite[]`+deltaTime 累积翻帧+循环表+dedup map；禁每帧字典/反射查找（微信官方明示低性能）；SpriteRenderer=世界/特效面，UI Image=HUD 面 | ✓（律×官方页互证） | §三 |
| 11 | 合批 | 同图集＝官方明文「发单个绘制调用」；SRP Batcher 官方兼容面=mesh/skinned mesh，SpriteRenderer 不在其列——精灵合批验收以 drawcall 实读为准 | ✓（官方双源） | §四 |
| 12 | 播放验收 | 逐像素 diff=0px（RT 通道已实测可用）；循环缝无跳变；Profiler 播放期 GC Allocated in Frame=0（微信面单线程单帧无法 GC＝官方在册） | ✓（实测×官方页互证） | §三/§四 |
| 13 | drawcall 帽 | 主菜单<50·战斗<100（实读为准） | 🟡（公司内部帽） | §四 |
| 14 | 显存取证 | Profiler Memory 模块：Texture Memory＋Total Allocated＋GC Allocated in Frame；真机通道＝微信打包勾 Development Build+Autoconnect Profiler | ✓（官方页） | §四 |
| 15 | 微信纹理链 | PC 微信/开发者工具对 ASTC 软解为 RGBA32（内存代价）；微信压缩纹理工具 2.0=多格式自适应（重度游戏才用）；带 alpha 帧的 ETC2 回退在工具链路不可用→ASTC 即唯一实用压缩档 | ✓（官方页原文）／🟡（推论） | §五 |
| 16 | 远程资源 | atlas 走 CDN 官方机制在册（data-package 可删走 CDN）；AB 加载带来 2–3 倍内存开销、用完即释放；避免 UnityWebRequest cache | ✓（官方页原文） | §五 |
| 17 | 工具正源 | 微信官方文档站+SDK 新仓 `minigame-tuanjie-transform-sdk`；原 GitHub 仓已停用勿引；开发者工具用 Stable 版 | ✓（今日实测） | §五 |

---

## §一 SpriteAtlas（v2）正确用法

### 1.1 V2 状态与模式

- **默认启用**：Unity 2022.2 起编辑器默认自动启用 Sprite Atlas V2（团结 1.10/2022.3 线＝V2 默认）。〔✓ 团结镜像 `Manual/SpriteAtlasV2.html`＋Unity 2022.3 同页互证〕
- **模式**：`Edit > Project Settings > Editor > Sprite Atlas > Mode`：`V2 - Enabled`（Edit/Play 双模式一律以图集为纹理源）／`V2 - Enabled for Builds`（仅构建 Player/AssetBundle/Addressables 时打包，Edit 模式用原始纹理）。
- **V1→V2 迁移**：开启后自动迁移既有 V1 资产，**迁移后不兼容 V1 且不可还原**——官方要求先备份再启用。

### 1.2 创建与 Objects for Packing

- 创建：`Assets > Create > 2D > Sprite Atlas`，产物 `.spriteatlas`。〔✓〕
- Objects for Packing 收件范围＝**精灵、纹理内精灵、文件夹**（官方原文 "packs textures (from sprites, sprites within textures, and sprites in folders)"）→ **目录打包合法**：帧 PNG 序列整目录拖入即可，无需逐件登记。〔✓ 官方双通道〕

### 1.3 属性正典表（class-SpriteAtlas 属性参考页·中文原文在册）

| 属性 | 官方语义/默认 | 本司序列帧判据 |
|---|---|---|
| Type | Master（默认）/Variant | 序列帧恒 Master；变体仅分档发布用（1.6） |
| Include in Build | 默认勾选＝随构建打包 | 首包内资源勾；远程 CDN/AssetBundle 图集**不勾**＋late binding（1.5） |
| Allow Rotation | 默认勾选可旋转打包提密度 | **关**。官方警告：图集旋转纹理时场景方向随之旋转（画布 UI 必须关）；序列帧关 rotation＝取样确定性判据 |
| Tight Packing | 默认勾选按轮廓打包 | **关**。统一矩形 cell 收益≈0，且引入轮廓 UV 不确定性 |
| Padding | 默认 **4px**＝「防止彼此相邻精灵的像素出现重叠」的缓冲（官方原文） | 基线 ≥4px；ASTC 6x6 面建议 12px（6 的整倍数）压渗色〔🟡 倍数规则＝压缩块原理推定〕 |
| Read/Write Enabled | 默认关；开启＝纹理数据副本、**内存翻倍**（官方原文） | 恒关（取证走 RT 截图，无运行时逐像素读取需求） |
| Generate Mip Maps | — | 恒关（2D/UISprite 无 mipmap 需求） |
| sRGB | 伽马存储 | 按项目色彩空间（URP 线性空间下勾） |
| Filter Mode | **图集级覆盖成员精灵的 Filter Mode**（官方原文） | 图集级统一（§二 2.4） |
| Default（平台覆盖面板） | 按平台覆盖成员纹理的分辨率/大小/压缩（官方原文：此面板可覆盖成员纹理的这些设置） | WebGL 面钉 ASTC（U276 Normal=6x6）；Win64 面 DXT/BC 线 |

### 1.4 POT 与页尺寸

- SpriteAtlas **无强制 POT 条款**（官方属性参考页无 POT 硬性要求）；Max Size 于平台覆盖面板设定；mipmap 关闭时 POT 非硬性要求。〔🟡 官方单源（无条款即无强制）〕
- **本司帽：单页 ≤2048**（微信低端真机显存/纹理上传路径风险；多页拆集可控）〔🟡 内部保守线〕。超页＝按技能/特效拆多页图集。

### 1.5 Include in Build 与 Late Binding（官方 Distribution 页原文）

- 不勾 Include in Build：**「图集不加载，引用其纹理的精灵运行时显示空白，直至用 late binding 经 Sprite Atlas API 加载」**（官方原文）。〔✓ 官方双通道〕
- Late Binding 定义（官方原文）：运行时加载/换入图集；图集启动时不可用（AssetBundle/远程加载）时必须；可按条件绑定不同图集（官方例：高/低分辨率）。2D Common package Samples 提供官方示例工程。
- **本司接线判据**：微信面远程图集 → Include in Build 关＋`SpriteAtlasManager.atlasRequested` 回调手动绑定（对 AB 加载完成事件）；首包内图集 → Include in Build 开、无需 late binding。**验收**：远程路径必须有「缺失→加载完成」空窗处理与占位，否则真机空白。

### 1.6 Variant 变体与「多纹理压缩格式不支持图集」

- 变体机制（官方原文）：Type=Variant 需在 **Master Atlas** 属性指向主图集（主图集不能是变体）；变体接收主图集内容副本；**Scale 0.1~1**（变体纹理大小＝主图集×Scale，默认/最大 1）；变体含独立 Include in Build。〔✓ 团结镜像 `MasterVariantAtlases.html`＋Unity 同页互证〕
- 与 U276 判例的关系：**一个 .spriteatlas 不能同时承载多种纹理压缩格式**——官方出路＝同一主内容派生多个变体或多平台构建覆盖，运行时按设备择一加载（late binding 即绑定出口）。本司落地：微信面按 U276 单档 ASTC 6x6 走主图集；Win64 单独构建覆盖，不靠变体硬混。

### 1.7 内包 vs 外包取舍表

| 维度 | Unity SpriteAtlas 内包 | TexturePacker 外包+导入 |
|---|---|---|
| 打包时机 | 构建期自动（V2） | 美术期产 PNG 图集页 |
| 切片来源 | 源=单帧 PNG（每帧一 sprite），无需 Grid 切片 | 源=已拼大图，引擎内 Multiple+Grid By Cell Size（U276 官方切法形态） |
| padding/rotate/trim 控制 | Inspector 可控（1.3） | 工具级可控：Padding＋**Extrude（复制边缘像素防渲染伪影——工具官方知识库原文）**〔🟡 codeandweb.com/texturepacker/knowledgebase/sprite-extrude〕 |
| 页数管理 | Max Size 超限自动分页 | 手动分页，页利用率可控 |
| 与「多压缩格式不支持图集」关系 | 受此限（1.6） | 不受此限（压缩发生在整页纹理级） |
| 管线适配 | 帧去重后每帧一 sprite 目录整拖 | 拼页一次成图，**引擎侧一张纹理+网格切片**，与「网格 cell+统一锚点」正典完全对齐 |
| 风险 | Edit/构建期纹理源差异需理解 V2 模式 | 外部工具链依赖（extrude≥2 防缝：社区经验〔🟡〕） |
| **本司判据** | 备选：纯引擎内管线 | **主选**（产线现状＝外包拼页+网格切片，U276 官方切法形态）〔🟡〕 |

---

## §二 切片与导入

### 2.1 官方切法（U276 判例展开）

- Sprite Mode＝**Multiple**；Sprite Editor → Slice。
- Type 三选（官方原文）：Automatic（按周边透明自动框选，定位「隔离规则排布的图形如 tile sheet」）/ **Grid by Cell Size**（**Pixel Size 定瓦片高宽像素**）/ **Grid by Cell Count**（**Column & Row 定行列**）；官方定位 Grid 选项「**当精灵在创建过程中已经以常规模式布局时，这非常有用**」——序列帧统一 cell 网格＝Cell Size 场景。〔✓ 团结镜像+Unity EN 双通道〕
- Grid 附属参数（官方原文）：**Offset**（自图像左上平移网格）、**Padding**（SpriteRect 自网格轻微内缩——注意：与图集 padding 语义不同，此为切片矩形内缩）、**Keep Empty Rects**（保留无像素 SpriteRect，「对于按位置组织纹理切片的精灵有用」——可用于帧索引稳定性）。
- **Pivot＝九宫格预设之一或 Custom**（官方原文 "The Pivot can be set with one of nine preset locations or a Custom Pivot location"）。〔✓ 双通道〕
- **Method**（官方原文表）：Delete Existing（删全部旧 SpriteRect 后加新）／Smart（重叠时最佳原矩形被更新、新切片被丢弃）／Safe（保留全部原矩形、重叠新切片被丢弃）→ **序列帧重切恒用 Delete Existing**（sprite 数与命名确定性）。

### 2.2 Cell Size vs Count 选择判据

| 条件 | 选用 | 理由 |
|---|---|---|
| cell 尺寸已知恒等（本司 512px 档） | **Grid by Cell Size** | 写 512×512 即切；帧数变化不改变参数 |
| 仅知行列数/cell 非整数/页内外框留白等分 | Grid by Cell Count | 以行列反推，避免非整数 cell 误差 |
| alpha 孤岛散布不定 | Automatic | 本司**不用**：破坏网格确定性 |

**验收**：sprite 数＝去重帧数；4 角+中心帧 rect 零偏移；pivot 全帧一致（导 sprite meta 机器校验 pivot 相等）。

### 2.3 pivot 统一策略

- 官方九预设+Custom。**本司判据**：特效/动作帧＝**Center**（爆点居中；512 档内容居中归一化与 Center 咬合）；站立角色帧＝**Bottom**（脚底接地）；逐帧 Custom 仅限立项特批。
- pivot 不统一→播放抖动（§六坑⑥）；验收＝全帧 pivot 逐项相等。

### 2.4 Filter Mode：Bilinear vs Point

- 图集级 Filter 覆盖成员精灵（§一 1.3 官方原文）。
- **判据**：帧源 512 档在 1080 宽竖屏参考分辨率≈2.1x **非整数倍放大**→恒 **Bilinear**（Point 最近邻在非整数倍放大下闪烁/锯齿）；像素风 1:1 直出才 Point。〔🟡 FilterMode 官方语义（Point=最近邻、Bilinear=邻近像素插值）+内部判据〕

### 2.5 PPU 选取判据

- 官方语义：PPU＝每世界单位对应像素数（TextureImporter 导入项）。〔✓〕
- **本司分档**：UI 层（Canvas）PPU 对 UI 缩放无效，UI 适配走 Canvas Scaler，恒默认 100；世界层恒 **PPU=100（引擎默认）**，世界尺寸用正交相机 size 对齐参考分辨率（设计可视高 H px → size=H/200；例：可视高 2000px→size=10）。PPU 选值不影响采样质量与合批，纯团队约定取整可读；验收在播放 diff=0px+帧率，不在 PPU。〔⬜ 内部工程判断〕

### 2.6 压缩档

- U276：WebGL Normal＝ASTC 6x6（High=4x4/Low=8x8）→图集/纹理平台覆盖面板照设；Win64 面 DXT/BC 线。PNG-8/PNG-32 量化实测＋ASTC 6x6 预估照 O-001 资源账四件套入账。

---

## §三 运行时播放器正法

### 3.1 架构判据（U276 铁律）

运行时**禁 Animator**（本司 WebGL/微信面铁律）；播放器＝代码 index 翻帧：预载 `Sprite[]` 数组，`Time.deltaTime` 累积推进帧指针，循环表驱动（含 dedup map 展开），帧率表按特效独立设定。

### 3.2 SpriteRenderer.sprite 直换 vs UI Image.sprite

| 维度 | SpriteRenderer.sprite | UI Image.sprite |
|---|---|---|
| 渲染路径 | 世界空间，2D Renderer 直绘 | Canvas 空间，UGUI 批处理 |
| 每帧换 sprite 成本 | 该 renderer 脏标记重绘（引用赋值）〔⬜ 工程判断〕 | 触发所属 Canvas 重建（rebuild），Canvas 内元素越多重建面越大〔🟡 UGUI 重建语义=社区共识+引擎机制（官方手册 UIBestPractices 页在 2022.3 文档树已撤除，三路 URL 404 实测：tuanjiemanual/unity.cn/CN-2022.3）；**验收以 Frame Debugger/drawcall 实读兜底**〕 |
| 合批面 | 同图集+连续渲染序→单批（§四 4.1 官方原句） | Image 引用图集 sprite→UI 面合批 |
| 适用面 | **战斗世界物件/特效（本司主面）** | **HUD 挂件**（图标、条带） |
| 共同红线 | 每帧 SetActive 重建、每帧 new、每帧字符串拼名/字典查找 | 同左 |

### 3.3 GC 面（微信面官方在册依据）

- **预载**：一次性 `SpriteAtlas.GetSprites()`/AB 加载→`Sprite[]` 字段缓存；每帧仅 index→sprite 引用赋值＝零分配。
- **禁字典/反射查找**：团结官方明文「**反射调用和字典访问在微信小游戏平台上的性能较低，大量的调用可能会导致游戏卡顿……应该尽量减少反射调用和字典访问**」→ 播放器每帧翻帧必须走数组下标，禁每帧 `GetSprite(name)`/字典映射。〔✓ 团结官方《性能优化指引》原文〕
- **计时**：deltaTime 累积推进（勿每帧 +1 直翻）；播放帧率表驱动。
- **验收（GC=0 的官方依据）**：团结官方明文「**微信小游戏平台上因为单线程原因，在单帧内无法执行 GC 操作，因此需要注意单帧的内存分配**」→ Profiler 播放期 `GC Allocated in Frame`＝0 是硬判据；播放 diff=0px；循环缝（尾→首）无跳变。〔✓ 官方原文×公司实测通道互证〕

### 3.4 「运行时禁 Animator」证据面（双源核查·如实分账）

1. **微信官方**：转换工具官方文档/性能优化页**无「Animator 组件专项处理或禁用」成文条款**——官方空白。
2. 微信官方在册的相邻事实：UnityWebGL 基于 WebAssembly「算力不及原生 APP」「**Unity 并未对 WebGL 平台做特别裁剪，启动较慢**」〔🟡 微信性能优化总览页摘要〕；原工具仓文档（Gitee 镜像）「UnityWebGL 目前不支持多线程，导致部分模块比如 AI、**动画**、渲染无法得到多线程的加速……最主要因素」〔🟡 镜像〕；按品类定流畅度标准（轻度休闲低档机 30fps+，可用小游戏云测取兼容性报告）〔🟡 微信优化运行性能页摘要〕。
3. **团结官方（正源《性能优化指引》）**：「Unity WebGL 不支持 SIMD，且默认不使用多线程，因此 CPU 的 Skinning 性能比较低，另外微信小游戏/WebGL 平台均不支持 Compute Shader，正常的 Compute GPU Skinning 也无法使用」——WebGL 面动画/蒙皮算力受限在册。〔🟡→正源镜像单源；与 Unity 官方 WebGL 平台限制共识互证记 ✓（引擎双官方在册）〕
4. **Unity 官方**：无「禁 Animator」成文（官方功能不出禁用文档）——官方空白。
5. **结论**：「序列帧该不该用 Animator」**官方无成文裁决——官方空白·内部闸自担**（如实标注）。铁律的工程依据（律 ✓＋论证 🟡）：①Animator 每实例每帧状态机求值+曲线采样，在 WASM 单线程环境放大（上引双官方在册事实）；②资产形态不匹配——sprite 序列走 Animator 需 AnimationClip 帧轨+状态机，徒增包体与运行时；③直换路径 diff=0px/GC=0 可机器取证，Animator 路径取证面复杂；④WebGL 无多线程/SIMD（双官方在册）→index 数组翻帧是 WASM 面最小开销解。

---

## §四 合批与性能

### 4.1 同图集合批：官方在册证据

- 官方原文（class-SpriteAtlas 页·中文）：「Unity 通常会为场景中的每个纹理发出一个绘制调用；但是，在具有许多纹理的项目中，多个绘制调用会占用大量资源」；「**Unity 可以调用此单个纹理来发出单个绘制调用而不是发出多个绘制调用，能够以较小的性能开销一次性访问压缩的纹理**」→ **共享同图集＝精灵合批基本盘（官方明文）**。〔✓ 团结镜像+Unity CN 同页互证〕

### 4.2 SRP Batcher 适用面：SpriteRenderer 不在其列

- 官方原文（SRPBatcher 页·GameObject compatibility）：兼容要求＝「**The GameObject must contain either a mesh or a skinned mesh. It can't be a particle.**」＋「mustn't use MaterialPropertyBlocks」＋「shader 须兼容（URP 内置 lit/unlit 全兼容，粒子版除外）」。**要求表未含 SpriteRenderer**——精灵不走 SRP Batcher 代码路径。〔✓ 团结镜像+Unity EN 双通道〕
- 社区佐证：Unity Discussions 两帖（"SRP Batcher & SpriteRenderer"、"Need clarifications about SRP Batcher, 2D URP, and SpriteRenderer"）报告 URP 下 SpriteRenderer 不由 SRP Batcher 合批。〔🟡〕
- **判据落地**：精灵合批正源证据＝同图集（4.1）＋**drawcall 实读**；URP 下 SRP Batcher 仍开（mesh 类受益，官方启用路径：URP Asset 勾选 SRP Batcher），但**验收不得以 SRP Batcher 为精灵合批依据**。Frame Debugger 官方在册可查批不批原因（"Nodes have different shaders" 等）。〔✓〕

### 4.3 drawcall 预算

- 本司帽：主菜单<50·战斗<100（实读为准）〔🟡 内部帽，官方无成文数值〕。破批三源：跨纹理/跨材质、渲染序穿插他类绘制、MPB（mesh 类）。

### 4.4 显存实测方法（官方计数器口径）

- **Profiler Memory 模块官方计数器**（团结镜像 `Manual/ProfilerWindow.html` 在册表）：**Texture Memory**＝「应用程序中的纹理已使用的内存量」；**Total Allocated**＝「已使用的内存总量」；Mesh Memory；Material Count；Object Count；GC Used Memory；**GC Allocated in Frame**＝「GC 堆中每帧分配的内存量」。〔✓ 官方页原文〕
- Simple 视图＝实时逐帧总览（Total 基于 System Used Memory 计数器）；Detailed 视图＝Take Sample 快照列表。官方明示「This information is available in **Release Players**」——发布版可读。〔✓〕
- **微信真机通道**（团结《性能优化指引》原文）：微信小游戏打包时勾选 **Development Build＋Autoconnect Profiler**；Editor 监听超时后可用引擎目录 `WeixinMiniGameSupport/BuildTools/websockify` 重启（nodejs 命令在册）。〔✓〕
- **本司取证**：编辑器+真机双口径；RT 截图通道（已实测可用）对渲染结果取证；资源账四件套（PNG-32/PNG-8 实测+ASTC 6x6 预估+drawcall 实读）照 O-001 入账。

---

## §五 微信小游戏特有面

### 5.1 包体官方限制（与 U276 互证）

- 官方原文（`developers.weixin.qq.com/minigame/dev/guide/base-ability/code-package.html`）：「**代码包总大小不能超过 30M，单个分包不限制大小，主包不超过 4M**」。〔✓ 与 U276 判例互证〕
- 分包加载机制（`…/base-ability/subPackage/useSubPackage.html`）：首启只下载「主包」，主包内触发其它分包下载——atlas 资源分包化/远程化是主通道。
- 首屏 4 秒线（U276）；公司首资源包保守线 20MB（内部）。旧限 8M/20M＝历史规则，✗ 判负勿引。

### 5.2 转换工具链正源（今日实测）

- 官方方案在册支持团结引擎（Guide.html 原文列出「团结引擎及 Unity 引擎……理论上支持的引擎版本涵盖：Unity 2018~2022、团结引擎」）；推荐引擎版本页：`…/Design/UnityVersion`。〔✓〕
- **SDK 正式版**：PackageManager git URL `https://github.com/wechat-miniprogram/minigame-tuanjie-transform-sdk.git`（预览版 `#pre-release`）；UnityPackage 经 `game.weixin.qq.com` 官方通道；开发者工具用 **Stable 版**（官方明示勿用「小游戏版 Minigame Build」）。〔✓〕
- **⚠️ 原仓 `github.com/wechat-miniprogram/minigame-unity-webgl-transform` 已被 GitHub 停用（商标政策，2026-09-30 实读页面原话 "THIS REPOSITORY HAS BEEN DISABLED … GitHub's Trademark Policy"）——判负勿引勿下载；第三方 Gitee 镜像仅作线索。**〔✓ 今日实测〕

### 5.3 转换工具硬约束清单（官方页原文）

- 命令面（`…/Design/Transform.html`）：`--webgl-version` 默认 **2**；`--cdn-url`（资源 CDN 地址）；`--load-from-subpackage`（首包资源从本地加载）；`--no-compress`（不压缩首包资源）；`--preload-list`（预下载清单）；`--background-video`（加载阶段视频＝首屏 4 秒线工具）。〔✓〕
- 导出结构：`minigame/data-package/*.data.bin`＝资源包；官方注原文：「**可以将资源包从该目录删除，走 CDN 下载，否则该文件会被打包到小游戏包里**」——**atlas 走 CDN 的官方机制在册**。〔✓〕
- 首包数据文件构成与优化（团结《性能优化指引》官方清单）：tuanjie_default_resources、Il2cpp metadata、tuanjie_builtin_extra（Shader）、场景、Resources 文件夹资源、全局设置——优化法＝**尽量避免使用 Resources 文件夹；BuildSettings 仅保留首场景（其余 AB/Streaming 加载）；简化首场景；统一并裁剪字体；压缩纹理和音频；Quality 页微信小游戏平台只留一档；取消 Auto Graphics API 只用 WebGL1.0/2.0；移除未用 Always Included Shaders；AutoStreaming 按需加载或 AB/Addressables 拆包（团结官方注明 tuanjie_default_resources 593KB→341KB）**。〔✓ 官方原文〕

### 5.4 纹理压缩与真机回退链（官方页原文）

- 官方定位（`…/Design/CompressedTexture.html`）：「**ASTC 是多数移动设备中游戏运行的主要支持的纹理格式，因此也是微信小游戏环境下主要使用到的压缩的纹理资源**」。〔✓〕
- 机型覆盖：「ASTC 能支持最近 3-4 年大部分机型；但 PC 端不支持 ASTC 依然需要解压」；「如引擎版本高于 2021，可使用引擎自身的 ASTC 压缩格式（移动端覆盖率较广，**PC 微信、微信开发者工具将软解为 RGBA32**）」→ **本司 2022.3/团结 1.10 线＝引擎自带 ASTC 线（官方明示可用）**。〔✓〕
- 微信压缩纹理工具 2.0（Beta）：对同一纹理生成多格式（ASTC/DXT/ETC2），按运行设备 GPU 下载可识别的压缩纹理（自适应加载）；纹理从 ab 剥离→ab 更小；官方建议「轻中度游戏两者皆可；重度游戏（MMO/SLG）内存压力大时结合 WXAssetBundle」→ **本司轻中度线＝引擎自带 ASTC 即可，不引入微信纹理工具**。〔✓〕
- 工具 Format 支持表（官方）：RGB Compressed **ETC2 4bits 支持**、RGBA Compressed **ETC2 8bits 不支持**、RGB Compressed **ETC 4bits 请勿使用（资源占位符专用）**、BC7 支持、Crunched DXT 不支持、RGBA 32bit 支持 → 判读：**带 alpha 的序列帧在微信工具链路 ETC2 回退实际不可用（RGBA ETC2 8bit 不支持），ASTC 即唯一实用压缩档**。〔🟡 官方表+推论〕
- 工具版本支持：2019/2020/2021 部分版本（建议 2019.4.28f1c1/2020.3.10f1c1/2021.2.18f1c1，旧线才用）；新版本不再依赖 Node.js。〔✓〕

### 5.5 内存与远程资源纪律（团结官方原文）

- 双堆结构：「Mono Heap 由 Il2cpp 分配管理，其他 Native 内存……由 Emscripten 的 malloc 分配管理（默认 dlmalloc）**这两部分都是只增不减，而且相互独立，空闲空间无法共享**，因此需要各自都注意控制峰值」。〔✓〕
- AB 纪律：「加载 AssetBundle 时往往会带来 **AB 文件大小 2–3 倍的内存开销**，因此在使用完 AB 之后及时释放」；「下载 AB 文件时，应尽量避免使用 UnityWebRequest 的 cache 机制（cache 文件存在 JS 内存文件系统，无法主动删除）」→ **远程图集加载必须即用即释放+禁 cache**。〔✓〕
- 真机压缩音频警告：普通浏览器（非微信环境）勿用压缩音频，可能导致声音异常。〔🟡 顺带在册〕

---

## §六 组装 SOP 全链（分步清单 + 每步验收判据 + 坑面）

**前置**：帧源＝本地生成短视频→取关键帧 PNG 序列；cell 统一 512px 档；与 O-001 图集正典律（资源账四件套+帧去重）咬合。

| 步 | 动作 | 验收判据（可执行） | 已知坑 |
|----|------|--------------------|--------|
| 1 | 视频取帧：按 fps/关键帧抽 PNG，命名 `fx_0000.png…` | 帧数=设计表；全帧同分辨率；背景已剥离；首尾帧完整 | 端点半帧、重复帧混入、绿幕残边 |
| 2 | 帧归一化到统一 cell（512×512 画布，同轴基准对齐） | 全部 PNG=512×512；逐像素尺寸一致；无裁切（溢出→升 1024 档须立项） | 亚像素重采样模糊；基准不统一致抖动 |
| 3 | 帧去重：逐像素 hash 去重，录 dedup map | 保留帧两两 diff>0；dedup 展开后播放总时长不变 | 感知 hash 误杀近似帧（禁作唯一依据） |
| 4 | 拼 atlas：外包法主选/内包法备选；padding≥4px（ASTC 6x6 面 12px 档）或 extrude≥2；**禁 rotate**；trim 关/保守 | 页≤2048；页利用率入账；PNG-8 量化实测；ASTC 6x6 预估入资源账 | 渗血/bleeding；页超限；旋转切片 |
| 5 | 导入设置：Sprite (2D and UI)+Multiple+PPU=100+Bilinear+平台压缩档（§二） | Inspector 全项对照 §一/§二 正典表复核 | 压缩档误用；Read/Write 误开内存翻倍 |
| 6 | 切片：Grid By Cell Size（512×512）+pivot 统一+Method=Delete Existing→Apply | sprite 数=去重帧数；pivot 全帧相等；4 角+中心帧 rect 零偏移 | 网格偏移；pivot 不一致；Smart/Safe 残留旧切片 |
| 7 | 播放器接线：预载 `Sprite[]`+deltaTime 累积翻帧+循环表+dedup map；**禁 Animator、禁每帧字典/反射查找** | 播放 diff=0px（RT 通道）；循环缝无跳变；Profiler 播放期 GC Allocated in Frame=0 | 每帧 Load/new 数组/GameObject 重建/字典查找（微信面官方明示低性能） |
| 8 | 性能取证：drawcall 实读对照帽（菜单<50/战斗<100）＋Profiler Memory（Texture Memory/Total Allocated/GC）＋真机通道（Development Build+Autoconnect Profiler）＋资源账四件套 | 四件套入账；drawcall 帽内；显存读数留档（编辑器+真机双口径）；主包≤4MB/总包≤30MB 实测过线 | 只看编辑器不看真机；包体超线才发现；AB 未释放（2–3 倍内存坑） |

**坑面总表**（验收红线）：①渗色→padding 不足（步 4 解法：padding 12px 或 extrude≥2）；②ASTC 6x6 细线/渐变块状伪影→真机 QC 不过线另立项（升 4x4 或 PNG-8+Point 非默认线）；③掉帧→计时逻辑错（须 deltaTime 累积）或 GC（微信面单帧无法 GC＝官方在册）；④主包超线→atlas 未入分包/CDN（官方机制 §五 5.3；Resources 文件夹禁用＝官方清单）；⑤超页 2048→拆集；⑥pivot 不统一→抖动；⑦512 档≈2.1x 放大→Bilinear（§二 2.4）；⑧PC 微信/开发者工具对 ASTC 软解 RGBA32（内存代价）→PC 面验收按软解口径记录（§五 5.4）；⑨远程 AB 即用即释放、禁 UnityWebRequest cache（2–3 倍内存坑，官方在册）。

---

## §末 参考源 URL 清单

**团结官方镜像（U271 正源·docs.unity.cn/cn/tuanjiemanual）**——2026-09-30 实测可达：
- Sprite Atlas V2：`https://docs.unity.cn/cn/tuanjiemanual/Manual/SpriteAtlasV2.html`
- 主/变体图集：`https://docs.unity.cn/cn/tuanjiemanual/Manual/MasterVariantAtlases.html`
- 自动切片（含 Grid 参数/Pivot/Method 表）：`https://docs.unity.cn/cn/tuanjiemanual/Manual/sprite-automatic-slicing.html`
- SRP Batcher：`https://docs.unity.cn/cn/tuanjiemanual/Manual/SRPBatcher.html`
- 性能优化指引（微信面：GC 单线程/反射字典/AB 内存/首包优化清单）：`https://docs.unity.cn/cn/tuanjiemanual/Manual/Optimization.html`
- Profiler 窗口（Memory 模块计数器表）：`https://docs.unity.cn/cn/tuanjiemanual/Manual/ProfilerWindow.html`

**Unity 官方 2022.3**：
- 精灵图集属性参考（CN）：`https://docs.unity3d.com/cn/2022.3/Manual/class-SpriteAtlas.html`
- Sprite Atlas V2（EN）：`https://docs.unity3d.com/2022.3/Documentation/Manual/SpriteAtlasV2.html`
- 图集分发/Late Binding（EN）：`https://docs.unity3d.com/2022.3/Documentation/Manual/SpriteAtlasDistribution.html`
- 自动切片（EN）：`https://docs.unity3d.com/2022.3/Documentation/Manual/sprite-automatic-slicing.html`
- SRP Batcher（EN，GameObject compatibility 原文）：`https://docs.unity3d.com/2022.3/Documentation/Manual/SRPBatcher.html`

**微信官方（developers.weixin.qq.com）**：
- 适配指南（支持团结引擎在册）：`https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/Guide.html`
- 技术原理：`https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/TechSummary.html`
- 推荐引擎版本：`https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/UnityVersion.html`
- 转换工具使用指南（命令面/导出结构/CDN）：`https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/Transform.html`
- 压缩纹理优化/微信压缩纹理工具 2.0：`https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/CompressedTexture.html`
- 代码包大小限制（总包 30M/主包 4M 原文）：`https://developers.weixin.qq.com/minigame/dev/guide/base-ability/code-package.html`
- 分包加载：`https://developers.weixin.qq.com/minigame/dev/guide/base-ability/subPackage/useSubPackage.html`
- SDK 新仓：`https://github.com/wechat-miniprogram/minigame-tuanjie-transform-sdk`

**TexturePacker（工具官方·🟡）**：
- Extrude 知识库（边缘复制防伪影）：`https://www.codeandweb.com/texturepacker/knowledgebase/sprite-extrude`
- 文档主页：`https://www.codeandweb.com/texturepacker/documentation`

**社区（🟡 仅线索）**：
- Unity Discussions "SRP Batcher & SpriteRenderer"：`https://discussions.unity.com/t/srp-batcher-spriterenderer/918871`；"Need clarifications about SRP Batcher, 2D URP, and SpriteRenderer"：`https://discussions.unity.com/t/need-clarifications-about-srp-batcher-2d-urp-and-spriterenderer/1680153`
- 原仓文档 Gitee 镜像（WebGL 无多线程/动画模块受限句）：`https://gitee.com/wechat-minigame/minigame-unity-webgl-transform`
- 微信性能优化总览/优化运行性能页：`https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/PerfOptimization.html`（及运行性能子页）

**⚠️ 判负勿引（✗）**：
- `https://github.com/wechat-miniprogram/minigame-unity-webgl-transform`（GitHub 商标政策停用，2026-09-30 实读）
- 微信包体旧限 8M/20M（历史规则）；docs.tuanjie.cn（连接层不可达，U271 判例，改走 docs.unity.cn 镜像）
- Unity 手册 UIBestPractices/Canvas 页 2022.3 路径（tuanjiemanual/unity.cn/CN-2022.3 三路 404 实测——UGUI 重建语义以包文档/社区共识+实读兜底）

**内联立法与实测（公司判例，不在外部 URL）**：O-001 图集正典律；U276 官方切法/平台判例；U271 官方文档正源判例；帧案播放逐像素 diff=0px 实测；引擎批模式截图/RT 取证通道实测；部件图集 11 件 PNG-8 仅 0.26MB 实测。
