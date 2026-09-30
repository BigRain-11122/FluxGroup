# R-20260930-2dlive-atlas-precision-01 · Sprite 图集拼装正法与精度保障判据（2D 序列帧产线·视频取帧源）

> R-件调研 · 2026-09-30 · 上下文 O-20260930-1856 路3
> 主题：视频取帧 PNG（帧间 bbox 抖动）→ 统一 cell 归一化 → 去重 → 图集拼装 → 压缩 → 播放全链路的正法与可机检精度判据。
> 产线背景（公司法，内联给定）：图集正典律（网格 cell＋统一锚点＋代码逐格播放＋资源账＋帧去重）；取帧五律＋极值采样 5-8 帧；双门制（数学门＋毒舌终审）；B6 判例（相邻帧连续性探针·曾漏 +18.4% 可见面积跳变）；团结引擎 WebGL ASTC 6x6（bpp≈3.56）。
> **依据等级图例：✓=两独立源互证 · 🟡=单源/社区/本司判例/产线内定 · ⬜=未验 · ✗=判负（证据否证）**
> 调研方法：官方文档直抓（TexturePacker／团结引擎手册／Unity Scripting API／Unity Manual／微信开放文档／scikit-image／PyPI），检索日 2026-09-30。未能直抓：OkCupid 评估文（403）、content-blockchain（连接失败）、deepwiki（429），均如实标注转引。Unity 英文 Manual SpriteAtlas 页 404，以团结引擎手册（同源中文镜像）＋Unity Scripting API 双官方替代互证。

## §0 结论速览（判据全表 · SOP 可直接抄）

### 0.1 产线 SOP 十条（可直接抄）
1. **取帧**：视频取帧五律＋极值采样 5-8 帧（关键姿态不漏；已立法，不展开）。
2. **alpha/bbox**：键控/亮度阈值取前景（α≥8/255），最大连通域 bbox，3 帧滑动中值＋形态学闭合抑抖。
3. **cell 归一化**：等比 bicubic 缩放至 512 档（长边=cell 内容区），底心/几何中心落格，round 取整（亚像素误差 ≤0.5px），全片统一 pivot（§2）。
4. **连续性探针（B6）**：逐相邻帧查 bbox 尺寸/主轴角/质心位移/可见面积包络（J5），违例=探针点→毒舌终审。
5. **帧去重**：SHA-256（解码后 RGBA 像素）精确合并 hold 帧（hold 白名单例外机制，§3.1）；pHash d≤5 复核近重复（§3.2）。
6. **拼图集**：Grid 算法网格满铺（512 档满铺式见 §1.1）；padding ≥2px（两家官方口径：TP"at least 2"、团结/Unity SpriteAtlas Padding 默认 4px）；extrude/bleed 1-2px；**禁 trim**（§1.2）；**rotation 显式关闭**（§1.3：团结/Unity 默认开启，必须手动关！）；POT 页（TP 默认上限 2048，超 16 帧升 4096）；禁 mipmap。
7. **压缩通道**：ASTC 6x6（3.56bpp，三源互证）为主；PNG-8 仅限平涂素材且强制 dithering＋过色带门（J17）。
8. **数学门**：J1-J18 全过（§0.2，全可机检）。
9. **毒舌终审**：探针点＋疑似帧人审，样本渲染取证。
10. **资源账入库**：atlas 估算式登记（ASTC=定值，PNG-8=实测 k 标定），单角色单 atlas 单 batch；打包逐包实测 ≤ 各线 80%（§5.3）。

### 0.2 判据全表（可机检）
| ID | 判据 | 测量方法（可机检） | 建议阈值 | 失败动作 | 依据 |
|----|------|--------------------|----------|----------|------|
| J1 | 图集 padding | 读 atlas 元数据 spriteRect 间距 | 帧间 gap ≥2px（建议 2-4px；Unity 侧默认 4px 保持） | 返工拼图 | ✓（TP 官方"Use a value of at least 2…OpenGL rendering"＋团结官方"Padding…防止相邻精灵像素重叠，默认 4 像素"） |
| J2 | extrude/bleed | cell 边缘像素=内容边缘像素复制比对 | 每侧 ≥1px（建议 1-2px） | 返工 | ✓（TP 官方 extrude 定义＋gameimagekit 独立工具同语义"hide linear-filter seams"） |
| J3 | 禁 trim | 每帧 spriteRect == cellRect | 违例=拒收 | 重归一化 | ✓（TP 官方 trim 四模式语义＋StackOverflow trim/crop 语义问答；另有 Unity Discussions 案例第三源） |
| J4 | rotation 关 | atlas 元数据 rotation 字段全 0 | 全 0 | 返工 | 🟡（产线门；事实修正见 §1.3：题面"Unity SpriteAtlas 不可"判 ✗，团结/Unity 官方证实**默认开启**，产线必须显式关闭） |
| J5 | 连续性包络（B6） | 逐对相邻帧：bbox 尺寸/主轴角/质心位移/可见面积比 | 尺寸 ±5% 或 ±8px；角度 ±3°；位移 ≤4%cell（≈20px@512）；面积比 warn[0.90,1.10]／fail[0.85,1.15] | 探针点→毒舌终审 | 🟡（B6 判例·单源档案；阈值带产线内定） |
| J6 | 精确去重 | SHA-256(解码后 RGBA)；hold 白名单例外 | 非白名单重复=错帧审 | 审 | ✓（TP 官方 auto-alias"identical sprites placed once"＋imagehash README 密码学 hash 语义，独立两源） |
| J7 | pHash 近重复 | imagehash.phash(hash_size=8)，汉明距离 d | d=0 转精确合并；1≤d≤5 合并候选；6≤d≤10 疑似→终审；d>10 不同（README 异图例 d=33） | 审 | 🟡（README 锚点＋KodeJungle"a distance of 0-5 might suggest similarity"单源明数；6-10 带产线内定，须按 §3.2 标定法实测） |
| J8 | 循环缝 | 末帧 vs 首帧逐像素 \|Δ\|（含 alpha）＋SSIM | MAE ≤2.0/255；P99.9 \|Δ\|≤4；max\|Δ\|≤8；SSIM≥0.98 | 审/补缝 | 🟡（带宽产线内定；SSIM 公式与实现 ✓） |
| J9 | identity hold | SSIM(f_n, f_{n-1}) | ≥0.995 → hold 候选（转 J6 登记白名单） | 登记 | 🟡（工程带宽） |
| J10 | identity 断裂 | SSIM(f_n, f_{n-1}) | <0.50 → 跳帧/错帧审 | 审 | 🟡（工程带宽） |
| J11 | ASTC 伪影 | 解码后 vs 源 PNG：6×6 分块 PSNR＋Laplacian 高频方差比 | 块 PSNR ≥36dB；方差比 ≤1.25；违例块 ≤1% | 降 cell 档/换 PNG-24 | 🟡（阈值带内定；ASTC 有损＋3.56bpp＋质量随块尺寸 ✓ 三源） |
| J12 | 播放保真 | 按播放表重建帧 vs 归一化源帧 | 逐像素 diff=0px（唯一例外 alpha=0 区 RGB，对应官方 enableAlphaDilation/ClearTransparentPixels 语义区） | 全链排查 | 🟡（产线门；np.array_equal 机检零歧义） |
| J13 | POT 页 | 页宽高 ∈ {1024,2048,4096} | 是 | 返工 | ✓（TP 官方 POT size constraints＋默认 max 2048；Unity 官方 ASTC 表按块规格） |
| J14 | 页利用率 | 非空格数/总格数 | ≥50%；空格 alpha 全 0 | 跨角色合 atlas/裁帧 | 🟡（产线内定） |
| J15 | 资源账 | 实测 atlas bytes vs 估算式 | 偏差 ≤15%（ASTC 通道理论偏差≈0） | 补登记 | ✓（ASTC 3.556bpp 三源，公式可推导；PNG-8 通道须实测 k） |
| J16 | 单 atlas 单 batch | Frame Debugger：角色绘制 batch=1 | =1 | 拆材质排查 | ✓（团结官方 WebGL"Dynamic Batching 默认启用"＋Unity 官方合批=同材质合并渲染状态；反例佐证 CSDN 两篇） |
| J17 | PNG-8 色带门 | 渐变区量化误差 maxΔRGB／二阶差分符号翻转数 | maxΔRGB>8 → 拒收 PNG-8，改 PNG-24 或强制 dithering | 换格式 | ✓（TP 官方"banding artifacts"原句＋Unity 官方量化格式质量降级语义；阈值 8 产线内定） |
| J18 | mipmap 关闭 | 导入设置检查 | mipmap=False | 改设置 | 🟡（产线内定；TP 官方 Scaling variants 为缩放适配替代方案） |

## §一 拼图集（padding/extrude/trim/rotation/POT/PNG-8）

### 1.1 padding 与 extrude/bleed 防渗色
- **帧间 padding（shape padding）**：TexturePacker 官方定义"sprite 之间添加透明像素以避免邻帧伪影"，**原句级阈值："Use a value of at least 2 to avoid dragging in pixels from neighbor sprites when using OpenGL rendering."**；团结引擎官方定义 Padding"防止精灵图集中彼此相邻精灵之间的像素出现重叠，**默认值为 4 个像素**"。两家官方口径一致（≥2 起步、4 为厂商默认）→ 产线定 2-4px。✓
- **页边 padding（border padding）**：TP 官方"页边框与 sprite 间留空"，>0 防页边越界采样。
- **extrude**：TP 官方原句"Extrude repeats the sprite's pixels at the border. Sprite's size is not changed."——边缘像素外扩复制；官方两用途：相邻摆放防闪烁、检查边缘半透明像素。独立第二源 gameimagekit（第三方纹理工具）："extrude/bleed edge pixels to hide linear-filter seams"。→ 产线取 1-2px，与 padding 叠加后线性过滤越界 1-2px 采到的仍是本帧边缘色。✓
- **512 档满铺定式**：pitch=512 = 内容 504 + 每侧 [padding 2 + extrude 2]×2；2048² 页=4×4=16 帧；4096²=8×8=64 帧；POT 整除零浪费；内容到内容净距 8px ≥4px。J1/J2/J13 同时满足。
- **mipmap**：2D 序列帧 atlas 关 mipmap（缩放适配走 TP 官方 Scaling variants 双档 atlas 或引擎内双套 atlas），省 33% 体积并杜绝 mip 级越界渗色。🟡

### 1.2 trim 改变 pivot 的帧对齐风险（产线=禁 trim）
TexturePacker 官方 trim 模式语义（原文摘录）：
| 模式 | 语义 | anchor/位置 |
|------|------|-------------|
| None | 不动 | 原位 |
| Trim | 裁掉透明边，使用时仍按原尺寸呈现，**anchor 不变**（"might not be available in all frameworks"） | anchor 保留 |
| Crop, keep position | 裁掉且实际变小，位置保留（anchor 语义不变） | anchor 保留、框变小 |
| Crop, flush position | 裁掉且**位置清零："sprite placement changes depending of the amount of removed transparent border"** | 位置随裁切量漂移 |
- **风险机理（视频取帧线）**：视频帧间 bbox 天然抖动 1-3px → 逐帧 trim 量互异 → ①各帧有效框尺寸/偏移互异，即使 anchor 语义保留，逐帧不同的"裁切量×重建偏移"引入亚像素~像素级锚点微漂=播放抖动、呼吸感失真；②自研"代码逐格播放"以固定 pitch 网格寻址，trim 直接破坏网格前提；③官方明示部分框架不支持 Trim 语义，Unity 社区有 TP trim 后 pivot 异位实例。✓（TP 官方＋StackOverflow 语义问答，两独立源）
- **产线判（正法）**：视频取帧线一律**禁 trim**；确需省面积，先归一化统一 cell，再全片**恒定量**安全框裁切（等效手工 trim 固定值），pivot 用归一化坐标重算并登记。

### 1.3 rotation —— 题面说法判负（✗），产线仍关
- **题面内联"TexturePacker 可/Unity SpriteAtlas 不可"的核验结果**：
  - TexturePacker：官方 `--enable-rotation/--disable-rotation`，"允许 90° 旋转获得更佳排布……**Might not be supported by all game/web frameworks**" → 可旋转＋官方兼容性警告 ✓（官方单源）
  - Unity/团结 SpriteAtlas：**团结引擎官方手册《Sprite Atlas properties reference》原文——"Allow Rotation：选中此复选框允许在 Unity 将精灵打包到精灵图集时旋转精灵……并且默认情况下会启用此选项。如果精灵图集包含画布 UI 元素纹理，请禁用此选项，因为 Unity 在打包期间旋转精灵图集中的纹理时，也会在场景中旋转它们的方向。"**；Unity Scripting API `SpriteAtlasPackingSettings` 官方字段 `enableRotation`（"Determines if rotating a sprite is possible during packing"）。两个官方源一致 → **"Unity SpriteAtlas 不可 rotation"判 ✗（判负）：非但可旋转，且默认开启。**
- **产线判**：rotation **显式关闭**（J4）。理由：①Grid 满铺产线旋转收益=0（等大 cell 矩形满铺无空隙）；②旋转增加逐格播放 UV 反变换步骤，扩大 J12 排查面；③连续性探针与渲染取证需额外处理 90° 态；④官方手册自己给出"画布 UI 纹理须禁用"的告警语境，序列帧图集同理求稳。**注意：因团结/Unity 默认开启，此项必须显式设置，不可依赖默认值。**
- 补充：`SpriteAtlasPackingSettings` 官方还含 `enableAlphaDilation`（"Sets the boundary padding pixels alpha to 0"）、`blockOffset`、`enableTightPacking`、`padding` 四字段——Tight Packing 亦默认开启，本产线同样应关闭（tight 按轮廓打包破坏满铺网格前提）。

### 1.4 POT 页尺寸
- TP 官方 size constraints：POT／MultipleOf4／WordAligned／AnySize；max width/height **默认 2048**；官方注明"用 ASTC/PVRTC/ETC 压缩时 TexturePacker 自动满足格式约束"（ASTC 6×6 块要求宽高为块尺寸倍数，工具自动对齐）。✓（TP＋Unity 两厂商官方）
- **产线定式**：POT 且 pitch 整除（512 档天然满足 2048/4096）；2048² 起步（≤16 帧）；17-64 帧升 4096²（利用率 J14≥50%：17 帧入 4096 利用率 27% ✗ → 17-32 帧优先跨角色合 atlas 或双 2048 页+资源账权衡）；>64 帧拆多页或多角色合 atlas（§5.2 权衡）。

### 1.5 PNG-8 调色板量化的水彩色带风险
- TP 官方：png8="PNG (8bit indexed). Smaller file size with **up to 256 colors**. Good for **simple graphics**."；dithering 节原句："**Reducing colors can sometimes result in 'banding artifacts', which can negatively impact image quality**"。Unity 官方格式表将量化格式（如 RGBA 16bit 4444）质量标 Medium 低于未压缩——两家厂商文档共通"减色=降质"语义。✓
- 水彩渐变（连续长渐变＋低对比过渡）为 256 色量化色带最高危内容。
- **缓解序**（TP 官方选项）：PngQuantLow/Medium/High（PNG-8 专用抖动强度三档）、FloydSteinberg(±Alpha)、Atkinson(±Alpha)、NearestNeighbour、Linear；含 alpha 版适合半透明渐变。抖动=把量化误差散布成噪声消带，代价=引入高频噪声 → **pHash/连续性/循环缝判据必须在抖动前的源帧上跑**（机检输入=归一化源帧，非 atlas 终图）。
- **产线判（J17）**：水彩/长渐变素材禁 PNG-8（改 PNG-24 或 ASTC 通道）；平涂/描边风可用 PNG-8+PngQuantMedium。判据=渐变区 maxΔRGB>8 拒收，或梯度单调性（二阶差分符号翻转）探针超限拒收。

## §二 帧归一化（bbox→cell·512 档·对齐取整·pivot·可见面积跳变）

### 2.1 算法（产线正法·SOP）
1. 输入：视频取帧 PNG（取帧五律＋极值采样 5-8 帧已保证关键姿态不漏）。
2. 前景提取：绿幕/黑底→键控或亮度阈值得 alpha（二值阈值 α≥8/255）；已有 alpha 通道直接用。
3. bbox：每帧最大连通域包围盒 (x0,y0,w,h)；对 bbox 序列做 3 帧滑动中值＋形态学闭合，抑制隔行扫描与视频压缩噪声的 1px 级抖动。
4. 缩放：s = cell_inner / max(w,h)，等比 bicubic；**禁非等比**（形变不可逆且破坏连续性判据）。512 档=设计 cell 512（含安全边，满铺式 §1.1）。
5. 落格：底心对齐（足部/待机/行走动画推荐）或几何中心对齐，坐标 round 取整。
6. pivot 统一：全片同一归一化 pivot（如 (0.5, 0.0) 底心）；图集=固定 pitch 网格，播放代码用 `cell 序号×pitch` 计算 UV，**不逐帧读偏移**——"代码逐格播放"正典律的技术前提，也是 J12=0px 门可成立的前提。
7. 输出即"正典帧"：取整单向不可逆，全链判据一律相对归一化后帧，不回溯视频原帧。

### 2.2 精度损失账
- 亚像素取整误差 ≤0.5px（均匀量化，无系统偏移）；缩放插值 bicubic 振铃可忽略；PNG 保存无损。
- 视频源隔行/压缩噪声在 bbox 抑抖步骤消化（并入 J5 连续性包络监控）。
- 合计：归一化环节几何损失仅半像素量级 → 后续全链 0px 保真判据以"归一化帧"为基准。

### 2.3 相邻帧可见面积跳变阈值（B6 判例）
- 测量：A_n=帧内 α>0 像素计数；r=A_n/A_{n-1}。
- 阈值：warn 界 0.90/1.10；fail 界 **0.85/1.15**。判例 B6 曾漏 **+18.4%**（r=1.184）→ 现行 fail 上界 1.15 必然截获该量级（1.184>1.15）。
- 例外通道：极值采样帧（动作极点处面积突变合法）＋hold 白名单帧，显式登记后豁免。
- 依据：🟡 本司判例（单源档案）＋动画连续性工程常识；无外部公开文献可直接互证，作产线内定法。

## §三 帧去重（精确 hash＋pHash）

### 3.1 精确 hash（SHA-256·hold 白名单例外）
- **对象**：解码后 RGBA 像素 buffer，而非 PNG 文件字节——PNG 编码器/压缩参数差异会造成假阴性；像素级 hash 才是"帧等价"判据。
- **两源互证**：①imagehash 官方 README："密码学哈希（MD5/SHA）对图像微小变化产生完全不同哈希"→密码学哈希只适合逐位相同判定，感知相似须另用感知哈希；②TexturePacker 官方 auto-alias："by default identical sprite images are only placed once on the texture to save space, the data entries refer to this shared sprite"——工业级图集工具默认即做精确同图合并。✓
- **用途 A（省体积·正收益）**：相邻 hold 帧（动作停格）同 hash → 图集存 1 cell，播放表多帧映射同格；hold 帧是去重最大收益来源。
- **用途 B（纠错探针）**：**非相邻**帧同 hash 而播放表预期不同 → 疑似取帧错序/重复帧 → 毒舌终审。
- **hold 白名单例外**：白名单=「极值采样清单」＋「逐段 hold run（连续 ≥2 帧同 hash）」自动登记。白名单帧对**不触发错帧告警**（例外语义），但**仍参与合并省体积**。
- 阈值：0/1 判定无带宽；判据=「重复帧是否在白名单」。

### 3.2 感知 hash pHash（库与阈值）
- **库**：Python `imagehash`（PyPI ImageHash 4.3.2，2025-02-01 发布；`pip install imagehash`；依赖 Pillow/numpy/scipy.fftpack）。pHash 算法另有独立原版实现 pHash.org（C++）→ 算法本身两源 ✓；Python 库为 Buchner 单实现 🟡。
- **用法**：`imagehash.phash(img, hash_size=8)` → 64-bit（8×8 DCT 低频）；汉明距离=`h1-h2`。
- **README 实测锚点**：完全不同图 d=33；hashsize=8 下"same hash"分组=肉眼完全一致（d=0）。
- **阈值带与标定法**：d=0 完全同帧（转 3.1 合并）；**1≤d≤5 近重复**→合并候选＋人审；**6≤d≤10 疑似**→毒舌终审；**d>10 基本不同**。KodeJungle 独立教程佐证"a distance of 0-5 might suggest similarity…isn't universal，须按数据集实验定阈值"。🟡（README 锚点＋KodeJungle 单源明数；6-10 带为产线内定）
- **产线标定法（SOP）**：每新素材批次抽 ≥30 对"已知同 hold/已知不同"帧对实测 d 分布，若分布与默认带冲突（如 hold 对 d 中位数 >5），以实测分布重定带并登记——KodeJungle 的"阈值非普适"警告即此操作依据。
- **产线适配**：pHash（DCT 低频）对平移敏感；本产线帧已 cell 归一化对齐，平移变量已消除 → 阈值可比通用场景收紧 1-2 档。
- 复杂度：帧 O(1) 哈希，全片两两 O(n²)（n≤200 无压力）。

## §四 精度判据全表（可机检）——总表见 §0.2，本节补机理与实现要点
- **4.1 循环缝 J8**：末帧 vs 首帧逐像素 |Δ|（含 alpha 通道）＋SSIM 全图。带宽：MAE≤2.0/255、P99.9 |Δ|≤4、max|Δ|≤8、SSIM≥0.98。语义：循环动画首尾相接不得有可见跳变；逐像素门卡硬伤，SSIM 卡结构性差异。🟡
- **4.2 identity J9/J10**：scikit-image `structural_similarity` 官方要点——**浮点输入必须显式 data_range**（否则结果无效）；对齐 Wang 2004 原始算法需 gaussian_weights=True、sigma=1.5、use_sample_covariance=False；返回 mssim 标量，full=True 得逐点 SSIM 图（可定位断裂区）。✓（scikit-image 官方文档＋Wang 2004 IEEE TIP 13(4):600-612，两独立源）。阈值带（hold≥0.995／断裂<0.50）为产线工程带宽 🟡。
- **4.3 连续性包络 J5**：见 §2.3；纯 numpy/OpenCV 轮廓与连通域即可机检，B6 探针即此实现。🟡
- **4.4 ASTC 6x6 伪影 J11**：解码 ASTC→RGBA 与源 PNG 按 6×6 块网格比 PSNR＋Laplacian 高频方差比（块效应/ringing 抬高高频能量；方差比=V(decoded)/V(source)，per-tile）。**ASTC 定率：固定 128bit/块，footprint 4×4~12×12，6×6→3.56 bits/texel。三源互证：①Wikipedia ASTC（引 Khronos Data Format Spec/HPG 2012 论文）；②TexturePacker 官方像素格式表 ASTC_6x6→3.56；③Unity 官方 GPU texture formats reference"6x6: 3.56"（quality 栏"Low to high"随块尺寸：4x4=8bpp 最佳至 12x12=0.89bpp）。** ✓ HPG 2012 论文实测 ASTC 在 2 与 3.56bpp 档 PSNR 优于 PVRTC/S3TC/ETC2（经 Wikipedia 引用）→ 6x6 档质量定位有据。团结 WebGL 纹理压缩官方可选 DXT/ETC2/ASTC 三者（团结手册 WebGL 设置页）✓；"6x6 为团结默认档"未在官方页找到逐字依据 → ⬜ 产线背景内定（微信官方"压缩纹理工具/压缩纹理优化"文档证 Unity/团结管线支持 ASTC 按需加载与首资源包优化）。阈值带 🟡 产线内定。
- **4.5 播放保真 J12**：播放表驱动重建帧 vs 归一化源帧 `np.array_equal` 全等，diff=0px；唯一豁免=alpha 全 0 区 RGB 无定义（与官方 `enableAlphaDilation`"boundary padding pixels alpha to 0"、TP `ClearTransparentPixels` 语义区对应）。机检零歧义。🟡
- **4.6 机检工具链**：SSIM/PSNR=scikit-image；逐像素 diff=numpy 布尔运算；bbox/面积=OpenCV connectedComponents/轮廓；hash=hashlib/imagehash；ASTC 解码=Arm 官方 astc-encoder（`astcenc` CLI，Wikipedia 官方外链）或引擎内 Texture2D 回读。✓（全官方/主流库）

## §五 资源账（体积估算式·单 atlas 单 batch·包体三线）

### 5.1 atlas 体积估算式（PNG-8 实测 vs ASTC 预估）
- **通式**：`V_atlas ≈ 页宽×页高×bpp/8`（字节）；多页求和；帧数 N 与页关系：N≤16→2048²，17≤N≤64→4096²（利用率 J14 门），>64→多页/多角色合页。
- **ASTC 6x6（预估=实值）**：bpp=3.556 定值（三源 ✓），**与画面内容零相关** → 估算式无偏差，资源账可精确到字节：
  - 2048² 页 = 2048×2048×3.556/8 ≈ **1.78 MiB**（≈1.86 MB）
  - 4096² 页 = 4096×4096×3.556/8 ≈ **7.11 MiB**（≈7.46 MB）
  - 例：40 帧动画 @512 档 → 40×512²×3.556/8 ≈ 4.66 MB，装 4096² 单页（利用率 40/64=62.5% ✓）
- **PNG-8（必须实测标定）**：`V ≈ 帧数×pitch²×k/8`，k=有效压缩 bpp，随内容剧烈波动：平涂/描边风 k≈0.5-1.5，水彩/厚涂渐变 k≈2-4（且受 dithering 强度影响）→ **标定法：每类画风抽 3 张代表 atlas 实测，取 k 登记资源账，估算偏差门 J15=15%**。🟡（k 带为产线经验，官方无此数）
- **显存账（关键差异）**：PNG-8 上传 GPU 需解码为 RGBA32=**32bpp**（4096²≈67 MiB 显存）；ASTC 硬件解码保持 **3.56bpp**（4096²≈7.11 MiB）——约 **9 倍差**，微信小游戏低端机内存红线场景 ASTC 为唯一解。微信官方"压缩纹理工具/压缩纹理优化"文档即为该管线背书（ASTC 按需加载、降 bundle 体积）。✓
- **结论**：包体账两条通道都要登记（ASTC 定值、PNG-8 实测 k），显存账只认 ASTC。

### 5.2 单 atlas=单 batch
- **原理（两官方源）**：Unity 官方合批文档——静态合批"combines meshes that use the same material"（同材质才可合并渲染状态更新）；团结官方 WebGL Player 设置——"Dynamic Batching：选中此复选框可在构建中使用动态批处理（**默认情况下启用**）"。同贴图＋同材质=合批前提，图集正是把全帧塞进同贴图的手段 → 一角色一 atlas 一材质一 batch。✓（反例佐证：CSDN 两篇独立文记录材质/图集设置不当致合批失效）
- **判据 J16**：Frame Debugger 实测角色绘制 batch=1；失败=排查材质拆分/贴图混用。
- **拆页权衡**：>64 帧须多页（多贴图=多 batch）→ 优先"多角色共用 4096² atlas"保单 batch（同屏角色共享材质）；跨页角色避免同屏。

### 5.3 包体三线分配表（微信小游戏）
**官方现行限制（直抓原句，微信开放文档《分包加载》2026-09-30 抓取）**：
- "整个小游戏所有主包+分包大小不超过 **30M**"
- "主包不超过 **4M**"
- "单个普通分包不限制大小"（受 30M 总额约束）
- "单个独立分包不超过 4M"
✓（官方正文直抓；旧官方镜像存历史值 8M/4M，证沿革）
**勘误**：题面"首资源包 20MB"**非微信官方线**——官方对普通分包不设单包上限，20M 为本司产线内定的**首启动体验预算**（在 30M 总额内自设，控制首屏下载时长），标 🟡（产线内定）而非官方限制。

**三线分配表（可直接抄）**：
| 线 | 硬限 | 产线预算（≤80%） | 内容构成 | 判据 |
|----|------|------------------|----------|------|
| 主包 | 4M（官方 ✓） | ≤3.2M | 引擎 wasm/js＋启动代码＋首场景配置＋最小 UI atlas | 打包实测 ≤3.2M，超=阻塞 |
| 首资源包（分包） | 官方不限单包（30M 总额内）；产线内定 20M 🟡 | ≤16M | 主角全套 atlas（idle/walk/战斗）＋首场景资源＋必要音效 | 实测 ≤16M；`wx.preDownloadSubpackage`（基础库 3.4.9+，官方 API ✓）预下载保首启动 |
| 总包 | 30M（官方 ✓） | ≤24M | 全量角色/场景 atlas＋音频＋后续内容 | 资源账汇总 ≤24M，留 ≥20% 迭代缓冲；超=毒舌终审＋裁资产 |
- **资产级账本**：每个 atlas 登记帧数/页数/cell 档/压缩通道/实测 bytes/显存 bytes，三线汇总自动核账；J15 偏差 15% 门兜底。

## §末 信息源 URL 清单
> 标注：✓=两独立源互证条目所用 · 官方=厂商一手文档 · 🟡=单源/社区 · 未直抓=如实注明

**判据互证核心源**
1. TexturePacker 官方 Documentation · Texture Settings（padding"at least 2"原句/extrude 定义/trim 四模式/rotation/POT/默认 2048/PNG-8 256 色/banding artifacts 原句/dithering 全表/auto-alias/ASTC 表）——https://www.codeandweb.com/texturepacker/documentation/texture-settings 【官方·已直抓】
2. 团结引擎手册 · Sprite Atlas properties reference（Allow Rotation 默认启用原句/Tight Packing 默认启用/Padding 默认 4 像素原句）——https://docs.unity.cn/cn/tuanjiemanual/1.4/Manual/class-SpriteAtlas.html 【官方·已直抓】
3. Unity Scripting API · SpriteAtlasPackingSettings（enableRotation/padding/enableTightPacking/enableAlphaDilation/blockOffset 字段）——https://docs.unity3d.com/ScriptReference/U2D.SpriteAtlasPackingSettings.html 【官方·已直抓·与源 2 互证】
4. Unity Manual · GPU texture formats reference（ASTC 各块 bpp：12x12:0.89…6x6:3.56…4x4:8；quality 随块尺寸）——https://docs.unity3d.com/Manual/texture-formats-reference.html 【官方·已直抓】
5. Wikipedia · Adaptive scalable texture compression（固定 128bit/块；6×6→3.56bpp；HPG 2012 论文引文"ASTC 在 2/3.56bpp 优于 PVRTC/S3TC/ETC2"）——https://en.wikipedia.org/wiki/Adaptive_scalable_texture_compression 【已直抓·ASTC 源①；Khronos Data Format Spec v1.1/HPG2012 为其引用源②】
6. 微信开放文档 · 小游戏分包加载（现行限制原句：30M/4M/普通分包不限/独立分包 4M；preDownloadSubpackage 3.4.9+）——https://developers.weixin.qq.com/minigame/dev/guide/base-ability/subPackage/useSubPackage.html 【官方·已直抓】
7. 微信小游戏旧文档镜像 · 分包加载（历史限制 8M/4M，证沿革）——https://mp.weixin.qq.com/debug/minigame/dev/guide/base-ability/sub-packages.html 【官方·已直抓】
8. 微信开放文档 · 压缩纹理优化/微信小游戏压缩纹理工具（Unity/团结管线 ASTC 按需加载、首资源包优化概念）——https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/CompressedTexture.html 【官方·经检索摘要】
9. 团结引擎手册 · Texture Compression in WebGL（WebGL 构建纹理压缩格式三选 DXT/ETC2/ASTC；Dynamic Batching 默认启用原句）——https://docs.unity.cn/cn/tuanjiemanual/Manual/webgl-texture-format.html 【官方·已直抓】
10. Unity Manual · Introduction to static batching（合批=同材质合并渲染状态）——https://docs.unity3d.com/Manual/DrawCallBatching.html 【官方·已直抓】
11. scikit-image metrics API · structural_similarity（data_range 强制/gaussian_weights sigma1.5/Wang 2004 对齐参数/full 返回）——https://scikit-image.org/docs/stable/api/skimage.metrics.html 【官方·已直抓】
12. Wang, Bovik, Sheikh, Simoncelli (2004) Image quality assessment: From error visibility to structural similarity. IEEE TIP 13(4):600-612【SSIM 原文·经 scikit-image 引用，与源 11 互证】

**社区/佐证源（🟡）**
13. ImageHash (PyPI 4.3.2) README（哈希类型/汉明距离语义/异图 d=33 锚点/密码学 vs 感知 hash 立场）——https://pypi.org/project/ImageHash/ 【库官方·已直抓】
14. pHash.org（pHash 原版 C++ 实现，算法独立源）——https://www.phash.org/ 【算法互证】
15. KodeJungle · Beginner Guide to Hashing with pHash in Python（"distance of 0-5 might suggest similarity…isn't universal"）——https://kodejungle.org/learning/hashing/beginner-guide-to-hashing-with-phash-in-python/ 【社区·已直抓】
16. gameimagekit · Texture Prep（extrude/bleed 防 linear-filter seams、POT pad）——https://gameimagekit.com/en/tool/texture-prep 【社区工具·已检索摘要】
17. StackOverflow · Trim mode "Crop Keep position"（trim/crop 语义）——https://stackoverflow.com/questions/19940031/ 【社区·已检索摘要】
18. Unity Discussions · TexturePacker pivot point in weird positions（trim/pivot 漂移案例）——https://discussions.unity.com/t/texturepacker-pivot-point-in-weird-positions/150782 【社区·已检索摘要】
19. CSDN · Unity Sprite Atlas 的 Allow Rotation 与 Tight Packing 陷阱（两篇独立文）——https://blog.csdn.net/weixin_42676824/article/details/160758953 ；https://blog.csdn.net/weixin_29015127/article/details/162778119 【社区·合批失效反例佐证】
20. CSDN · 用团结引擎的 astc 压缩纹理省下 50% 内存（微信小游戏实战）——https://blog.csdn.net/w3x4y/article/details/152709325 【社区·ASTC 显存收益佐证】

**未直抓（转引/失败，如实注明）**
21. OkCupid Tech Blog · Evaluating perceptual image hashes（imagehash README 指名的阈值评估文）——https://tech.okcupid.com/evaluating-perceptual-image-hashes-at-okcupid-e98a3e74aa3a 【403·转引 ⬜】
22. content-blockchain.org · Testing different image hash functions（imagehash README 指名）——https://content-blockchain.org/research/testing-different-image-hash-functions/ 【连接失败·转引 ⬜】
23. deepwiki · DupImageDetection Hamming Distance and Similarity Thresholds —— https://deepwiki.com/xuehuachunsheng/DupImageDetection/3.4-hamming-distance-and-similarity-thresholds 【429·未用】

**判负与勘误记录**
- ✗ 题面内联"rotation：Unity SpriteAtlas 不可"——团结手册（Allow Rotation 复选框，默认启用）＋Unity Scripting API（enableRotation 字段）双官方源判负。
- 🟡 题面内联"首资源包 20MB"——微信官方现行对普通分包无单包上限（30M 总额内），20M 为本司产线内定预算，非官方限制。
- ⬜ 题面内联"ASTC 6x6=团结 WebGL 官方默认"——团结官方证实 WebGL 可选 DXT/ETC2/ASTC，"6x6 为默认档"未见官方逐字依据，按产线背景内定处理。

（完 · R-20260930-2dlive-atlas-precision-01 · 2026-09-30）
