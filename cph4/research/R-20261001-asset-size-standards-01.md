# R-20261001-asset-size-standards-01 · 小游戏 2D 控件/图标尺寸标准——业界与官方资料锚定件

- **令号**：CEO 令 O-20261001-2209（Button/Icon 需要多大 · 业界可查 · 不要超限）
- **日期**：2026-10-01（周四 · Asia/Shanghai）
- **状态**：**定稿**（四题闭环：官方规范 ✓ / 触控界标 ✓ / 头部对标 🟡 自测 / 规格表+限额面成表）
- **分级体系**：✓ 官方原文直抓（标注「双源」者为官方双页或官方+独立源互证）/ 🟡 单源社区（社区文、快照引用、本件自测）/ ⬜ 未验（含因技术原因未能直验）/ ✗ 判负（查无/不可测，如实排除）
- **纪律**：只写本件；未读仓内 >20KB 文件；全程分 6 次落盘（骨架→5 检查点→定稿）。
- **自测方法声明**：头部对标使用 **Apple 官方 iTunes lookup API 直链的宣传截图**（Apple 官方营销素材），逐像素目测估算（±5~10%），按 `1080÷截图宽` 折算到本司 1080 参考分辨率。全部标 🟡（单源·自测）。

---

## §0 尺寸规格表草案（先看这里·落实件）

> **内联底子对齐（直接引用·不推导）**：竖屏 1080 参考分辨率 + grid8；触控热区 128 律（热区 ≥ 可视，任何可点控件热区 ≥128px@1080）；图谱帽值 UI512 / 场景1024 / Icons256（从严取严）；≤128px 小件 flat 律 + @2x PNG-32；密度律 D1-D7。
> **换算底座**：主流机身物理宽 ≈68~71mm 承载 1080px → **1mm ≈ 15.2~15.9px@1080**。微信官方 7~9mm ≈ 107~143px；Google 官方 48dp≈9mm ≈ 137~143px；Apple 44pt（375pt 基准）≈127px。**本司 128 律 ≈8.1~8.4mm，被三大官方物理带全部覆盖 ✓**。

| 控件族 | 设计尺寸 @1080 竖屏（可视边） | 触控热区下限 | 依据 + 等级 |
|---|---|---|---|
| 主按钮（Play/购买大 CTA） | 宽 320~560px、高 ≥144px（grid8） | ≥128px（高全幅即达标） | Apple 44pt ✓ · Google 48dp≈9mm ✓ · 微信 7-9mm ✓ · WCAG 2.5.8 24px 底线 ✓ · 128 律（底子）；**头部大 CTA 未获可测样本（官方宣传图无 CTA，✗ 两例），列 ⬜ 待补测** |
| 次按钮（设置/排行/商店入口） | **128~192px 见方**（常态贴 192） | ≥128px（不足用透明扩边） | Royal Match 实测 设置/booster Ø≈193px 🟡；Gardenscapes 实测 关闭钮 Ø≈101px 🟡（头部也有 <128 可视件→靠热区扩边补足，反证 128 热区律必要）；Google「24dp 可视+48dp 热区」模式 ✓ |
| 胶囊（体力/任务/提示条） | **高 96~120px、宽 260~400px** | 可点时 ≥128px 热区（透明扩边） | RM 实测 计时胶囊 118px/进度 94px 高、宽 303~358px 🟡；GS 实测 HUD 行 ≈88~120px 🟡 |
| 图标 tile（功能格/道具钮） | **128~192px 见方** | ≥128px | RM 实测 booster Ø≈193px、圆心距 ≈215px 🟡；Google 模式折算 72px 可视+144px 热区 ✓ |
| 货币 icon（钻石/金币/体力） | **64~128px 可视** | 默认不可点；若为入口 → 热区≥128px | RM 实测 目标 icon 77~94px、计时饼图 Ø≈127px 🟡；GS 实测 货币 icon ≈95~101px 🟡 |
| 头像框 | HUD 级 96~160px；主角/hero 级 280~336px | 信息件·无热区要求 | RM 实测 国王头像拱 Ø≈303~325px 🟡（hero 级） |
| 面板底框（弹窗/棋盘底板） | 宽 ≤1000px（两侧留边 ≥40px）、高按内容 | — | RM 实测 棋盘面板 ≈912px（84% 画宽）🟡；图谱帽 UI512（底子） |
| 角标（红点/数量/NEW） | **48~64px**（气泡级大件 ≤88px） | 信息件；若自身可点 → 热区≥128px | RM 实测 徽章 Ø≈55~66px 🟡；GS 实测 订单气泡角标 Ø≈88px 🟡 |

**执行律（全表通用）**：可视走 grid8；热区 ≥ 可视且 ≥128px；间距 ≥24px（Google 官方 8dp 间隔折算 ✓）；图谱帽值内制作；≤128px 小件 flat+@2x PNG-32；密度不越 D1-D7。

## §一 官方规范：微信 WeUI / 小程序·小游戏设计指引

- **微信小程序设计指南（官方成文，原文直抓）** https://developers.weixin.qq.com/miniprogram/design/
  - **热区成文**（§3.2 避免误操作，原文）：「手指的点击精确度远不如鼠标，因此在设计页面上需点击的控件时，需要充分考虑到其热区面积，避免由于可点击区域过小或过于密集而造成误操作。由于手机屏幕分辨率各不相同，因此最适宜点击像素尺寸也不完全一致，**但换算成物理尺寸后大致是在 7mm-9mm 之间**。」→ **微信官方触控线=7~9mm ≈107~143px@1080；本司 128 律落在带内 ✓（官方成文为物理尺寸制，非 px 制；Google 官方 7-10mm 带互证 → 双源）**
  - **字号成文**（§5.1）：常用字号 **22 / 17 / 15 / 14 / 12（pt）** ✓（官方单页）
  - **设计稿基准成文**（§六）：**375px 基准（固定布局）或 390px 基准（响应式）** ✓（官方单页；1080=375×2.88 同构）
  - **标签栏密度成文**（§2.1）：「标签数量不得少于 2 个，最多不得超过 5 个，**为确保点击区域，建议标签数量不超过 4 项**」✓（官方单页；密度律 D1-D7 的外部同构）
  - **组件级 px 尺寸：官方空白**（指南未给任何控件 px 数值），官方口径=「使用或模仿标准组件尺寸进行设计」+ WeUI 控件库（sketch 组件库 / weui.io）
- **WeUI 实现层**：按钮默认宽 100%、mini 型自适应、边框-文本距 0.75em（https://www.kancloud.cn/ywfwj2008/weui/274515 🟡 社区镜像文档）；**按钮高度无成文值 ⬜待验**（GitHub 代码检索接口故障，如实注明）
- **微信包体官方四值 ✓（官方双页互证，与令文逐项一致）**：
  - 「**代码包总大小不能超过 30M，单个分包不限制大小，主包不超过 4M**」——https://developers.weixin.qq.com/minigame/dev/guide/base-ability/code-package.html
  - 「**整个小游戏所有主包+分包大小不超过 30M；主包不超过 4M；单个普通分包不限制大小；单个独立分包不超过 4M**」——https://developers.weixin.qq.com/minigame/dev/guide/base-ability/subPackage/useSubPackage.html
  - 社区印证：https://forum.cocos.org/t/topic/157835 🟡
- **压缩纹理官方指引 ✓（官方双页：CN 工具文档 + EN 性能文档）** https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/CompressedTexture.html：
  - 「**ASTC 是多数移动设备中游戏运行的主要支持的纹理格式，因此也是微信小游戏环境下主要使用到的压缩纹理资源**」；支持 ASTC 8x8/6x6/5x5/4x4，**默认推荐 Block Size 8x8**；不支持 ASTC HDR；「**RGB Compressed ETC 4 bits 请勿使用**」；移动端 ASTC / PC·Mac DXT5（https://developers.weixin.qq.com/minigame/en/dev/guide/performance/perf-action-texture-compression.html）
  - 同页快照：「ASTC 是不受纹理资源高宽影响的」→ **官方无「必须 2 的幂（POT）」成文 ✓；POT=WebGL1/ETC1 时代引擎传统（🟡），微信语境下让位于 ASTC 8x8 律**
- **图片格式白名单（官方成文）**：png/jpg/svg/atlas/astc/ktx/pkm/dds 等（code-package.html）→ 与 @2x PNG-32 底子兼容 ✓
- 小游戏专属设计指引：开放文档未见独立成文入口（盘点自文档导航），**官方口径沿用小程序设计指南**。

## §二 触控界标：Apple HIG 44pt / Material 48dp / 休闲游戏惯例

- **Apple HIG 44pt ✓（官方存档页原文直抓 + 社区多源互证=双源）**：「**Provide ample spacing for interactive elements. Try to maintain a minimum tappable area of 44pt x 44pt for all controls.**」——https://web.archive.org/web/20170801000000/https://developer.apple.com/ios/human-interface-guidelines/visual-design/layout/ ；当前版 HIG 页需 JS 未能直验 ⬜（https://developer.apple.com/design/human-interface-guidelines/buttons ）；社区同值转引 🟡（buildwithaccess / evinced）
- **Google/Android 官方 ✓（原文直抓 + M1/M3 官方页快照=双源）** https://support.google.com/accessibility/android/answer/7101858：
  - 「width and height of **at least 48dp**」；「An element like an **icon may appear to be 24x24dp but the padding surrounding it comprises the full 48x48dp touch target**」（热区＞可视的官方背书）；「at least 48x48dp, **separated by 8dp** or more」；「A touch target of 48x48dp results in a physical size of **about 9mm**... recommended target size for touchscreen objects is **7-10mm**」
- **W3C/WCAG 2.2 ✓（原文直抓）**：2.5.8 Target Size (Minimum)（AA）「**at least 24 by 24 CSS pixels**」；2.5.5 Target Size (Enhanced)（AAA）「**at least 44 by 44 CSS pixels**」
- **三界标汇聚**：Apple 44pt（≈127px@1080）/ Google 48dp（≈144px@1080）/ 微信 7-9mm（≈107~143px@1080）/ WCAG 24~44px → **行业触控下界共识带 ≈7~10mm 物理；本司 128 律=带中值（8.1~8.4mm）✓**
- **休闲游戏业界惯例 🟡（社区源原文直抓）** https://egmatic.com/blog/mobile-game-touch-controls-design-for-thumbs：
  - 惯例表同引四界标（Apple 44×44pt=「命中区而非可视尺寸」/ Material 48×48dp / WCAG AA 24×24 / WCAG AAA 44×44 CSS px）
  - 游戏专门三律：**「Treat 48 as the floor」（把 48 当下限，主行动显著大于下限）**；**「The hit area can be larger than the icon」（热区＞可视·透明扩边是标准做法）**；**「Separate targets generously」（目标间慷慨留距）**
  - 握持研究（引 Steven Hoober 1300+ 用户观察）：**49% 单手握持、约 75% 触点来自拇指**；主行动置屏幕下 1/3，顶栏只放只读信息
  - 同级社区源未直验：https://www.designmonks.co/blog/perfect-mobile-button-size ⬜

## §三 头部对标：Royal Match / Playrix 系 HUD·按钮·icon（🟡 单源·官方宣传截图自测）

- **方法**：Apple 官方 iTunes lookup API 直链宣传截图，逐像素目测估算（±5~10%），×2.755（392→1080）或 ×3.375（320→1080）折算。**业界拆解文均偏经济留存，头部 UI 成文尺寸数据=业界空白（如实标注）**；本节为自测补位。
- **Royal Match（Dream Games，2021）实测折算表**（素材：iTunes API 392×696 截图 2 张）：

| 元素 | 实测 @392 | 折算 @1080 | 备注 |
|---|---|---|---|
| 关卡顶 HUD 带高 | ≈120px（17.5% 屏高） | **≈330px** | 三段式 Target/主角头像/Moves |
| 悬浮 HUD 行高 | ≈60px（8.6% 屏高） | ≈165px | 计时/进度/停止三件套 |
| booster 圆钮（底部 5 连） | Ø≈70px（17.5~18.5% 画宽） | **Ø≈193px**（圆心距≈215px） | 高频操作件，全圆钮 |
| 设置齿轮圆钮 | Ø≈70px | **Ø≈193px** | 底部道具栏最右 |
| 停止/退出圆钮 | Ø≈60px（15.3% 画宽） | Ø≈165px | 右上 |
| 计时饼图 icon | Ø≈46px | **Ø≈127px** | 与 128 律重合 |
| 计时/进度胶囊 | 高 43/34px、宽 110/130px | 高 **118/94px**、宽 303/358px | |
| 国王头像拱（hero 级） | Ø≈110~118px（28~30% 画宽） | **Ø≈303~325px** | 场景视觉件 |
| Target 目标 icon | 28~34px | **77~94px** | |
| 数字徽章「3」 | Ø≈20~24px | **Ø≈55~66px** | |
| 棋盘面板 | 宽 ≈331px（84% 画宽）、8×8 格 | **宽 ≈912px**、单格 113~124px | 面板:UI:背景=46:33:21 |

- **Gardenscapes（Playrix，2016）实测折算表**（素材：iTunes API 320×480 截图；另一张为纯剧情插画，✗ 判负不可测）：

| 元素 | 实测 @320 | 折算 @1080 | 备注 |
|---|---|---|---|
| HUD 行高（浮动式） | 26~30px（5.5~6.3% 屏高） | **≈88~120px** | 无整宽顶栏，浮动控件行 |
| Stage 胶囊 | 68×26px（21% 宽） | ≈230×88px | |
| 货币计数胶囊 | 75×28px | ≈253×94px | |
| 关闭 X 圆钮 | Ø≈30px（9.4% 宽） | **Ø≈101px** | **低于 128 律的可视件实例** |
| 引导箭头按钮 | 42×42px（13.1% 宽） | **≈142px** | |
| 货币 icon | 28~30px | ≈95~101px | |
| 订单气泡（可点件） | 64×54px | ≈216×182px | |
| 「2」数量角标 | Ø≈26px（8.1% 宽） | **Ø≈88px** | 大件角标变体 |

- **对照结论**：
  1. **头部实操带**：次按钮/图标 tile 常态 **142~193px@1080**（RM 关卡件贴 192、GS 剧情件贴 144 再下探 101）；顶栏带 **88~330px**；货币 icon **77~127px**；角标 **55~88px**。**头部下限与本司 128 热区律咬合**。
  2. **GS 存在 Ø≈101px 的关闭钮可视件（<128）**——头部也靠「热区＞可视」扩边补救 → **本司 128 热区律比头部可视实践更严，「从严取严」被业界实况反向印证为必要**。
  3. **操作频率驱动尺寸**：RM 高频 booster Ø193 > GS 低频剧情关闭钮 Ø101；主行动显著大于下限（与 egmatic「48 当下限」律一致 🟡）。
  4. Playrix 系其他（Fishdom 等）：GUD 同库可比，未逐一自测 ⬜。
- **拆解库锚**：Game UI Database·Royal Match（屏幕级拆解结构：HUD and Overlays→Item & Ability Buttons/Clock & Timer、Pre-Game & Lobby、Offers & Bundles）https://www.gameuidatabase.com/gameData.php?id=1061 🟡

## §四 落实件：限额面（「不要超限」令意）

| 限额项 | 数值 | 等级 |
|---|---|---|
| 微信主包 | **≤4M** | ✓（官方双页） |
| 微信总包（主+全部分包） | **≤30M** | ✓（官方双页） |
| 单个普通分包 | **不限制大小**（受总量约束） | ✓（官方双页） |
| 单个独立分包 | **≤4M** | ✓（官方双页） |
| 纹理格式 | **ASTC 8x8 首选**（4x4 最清晰但内存高）；ETC1 请勿使用；PC 端 DXT5 | ✓（官方双页） |
| POT（2 的幂） | **官方无强制成文**（ASTC 不受宽高影响）→ 本司件不强制 POT，强制「ASTC 8x8+帽值」；POT 仅作 WebGL1 兼容备选律 | ✓（官方原文）；POT 传统律本身 🟡 |
| 图谱帽值 | UI ≤512 / 场景 ≤1024 / Icons ≤256（底子·从严取严，不评级） | 底子 |
| 小件律 | ≤128px flat + @2x PNG-32（底子）；微信白名单含 png ✓ | 底子+✓ |
| 触控下限 | 热区 ≥128px@1080（=7~9mm 带中值）；可视可小、热区不缩 | 底子；三官方带互证 ✓ |

## §末 分级台账 + URL 清单

**分级台账**（按可独立引用结论计）：✓×12（微信四值/微信 7-9mm/字号/375·390 基准/标签≤4/Apple 44pt/Google 48dp 族/WCAG 24×24/WCAG 44×44/ASTC 8x8/无 POT 强制/白名单）· 🟡×16（M1/M3 快照、egmatic 惯例、Cocos 帖、Apple 当前页转引、WeUI 宽度口径、GUD 结构、RM 自测 7 条、GS 自测 5 条）· ⬜×4（WeUI 按钮高度、Apple 当前 HIG 直验、DesignMonks、头部大 CTA 样本）· ✗×2（RM 宣传图#5、GS 宣传图#3 均为纯插画无 UI，不可测，如实排除）。

**URL 清单**：
1. https://developers.weixin.qq.com/miniprogram/design/ —— 微信·小程序设计指南（热区 7-9mm/字号/375·390 基准/标签≤4）✓
2. https://developers.weixin.qq.com/minigame/dev/guide/base-ability/code-package.html —— 微信·代码包（包大小限制+格式白名单）✓
3. https://developers.weixin.qq.com/minigame/dev/guide/base-ability/subPackage/useSubPackage.html —— 微信·分包加载（四值原文）✓
4. https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/CompressedTexture.html —— 微信·压缩纹理（ASTC 8x8/ETC1 禁用）✓
5. https://developers.weixin.qq.com/minigame/en/dev/guide/performance/perf-action-texture-compression.html —— 微信·纹理压缩 EN（移动 ASTC/PC DXT5）✓（快照）
6. https://web.archive.org/web/20170801000000/https://developer.apple.com/ios/human-interface-guidelines/visual-design/layout/ —— Apple HIG 存档（44pt×44pt 原文）✓
7. https://developer.apple.com/design/human-interface-guidelines/buttons —— Apple 当前 HIG（页需 JS 未直验，如实注明）⬜
8. https://support.google.com/accessibility/android/answer/7101858 —— Google（48dp≈9mm/7-10mm/8dp 间距/24dp+48dp 模式原文）✓
9. https://m1.material.io/usability/accessibility.html —— Material 1 官方页（需 JS·快照）🟡
10. https://m3.material.io/foundations/designing/structure —— Material 3 官方页（需 JS·快照）🟡
11. https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html —— W3C 2.5.8（24×24 原文）✓
12. https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html —— W3C 2.5.5（44×44 原文）✓
13. https://egmatic.com/blog/mobile-game-touch-controls-design-for-thumbs —— 休闲拇指触控惯例（48 当下限/热区＞可视/49% 单手）🟡
14. https://www.designmonks.co/blog/perfect-mobile-button-size —— 移动按钮尺寸惯例（未直验）⬜
15. https://forum.cocos.org/t/topic/157835 —— Cocos 论坛·分包四值社区印证 🟡
16. https://buildwithaccess.com/blog/touch-target-size-mobile-accessibility-wcag —— Apple 44pt 社区转引 🟡
17. https://knowledge.evinced.com/mobile-validations/tappable-area —— Apple 44pt 社区转引 🟡
18. https://www.gameuidatabase.com/gameData.php?id=1061 —— Game UI Database·Royal Match 屏幕级拆解 🟡
19. https://www.kancloud.cn/ywfwj2008/weui/274515 —— WeUI Button 文档镜像（宽 100%/mini 自适应）🟡
20. https://weui.io —— WeUI 官方示例站（参考）⬜
21. https://itunes.apple.com/lookup?id=1482155847&country=US —— Apple iTunes API·Royal Match 官方截图直链（自测素材来源）✓（素材）
22. https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/e1/3a/77/e13a77a8-7f4b-e90d-1462-2fb97781227f/7e33d9b3-9323-40f8-a631-60d44884338f_bird.jpg/392x696bb.jpg —— RM 关卡截图·自测对象① 🟡（素材）
23. https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/87/18/10/8718109c-4eeb-a3b0-be97-62706c895025/edede7e9-6c2e-401d-804d-32d96e7b4641_iphone-8.jpg/392x696bb.jpg —— RM 计时场景截图·自测对象② 🟡（素材）
24. https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/3b/19/93/3b1993b7-92ce-5353-6269-15f942217586/f8ac570a-bb40-467b-8586-7846389a1901_1242x2208_07.png/392x696bb.png —— RM 宣传图#5（纯 key art 无 UI，✗ 判负不可测）
25. https://itunes.apple.com/search?term=gardenscapes&entity=software&limit=2 —— Apple iTunes API·Gardenscapes 官方截图直链 ✓（素材）
26. https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/d3/0c/80/d30c808a-2c7b-c22b-68ca-a9aeb147bd51/1284x2778_gs_aso_screenshot134_en_v1_p2_as.png/320x480bb.jpg —— GS 游戏内截图·自测对象③ 🟡（素材）
27. https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/c0/61/52/c061525d-a61f-1c1d-b2ab-a738930a48a7/1284x2778_gs_aso_screenshot134_en_v1_p3_as.png/320x480bb.jpg —— GS 宣传图#3（纯剧情插画无 UI，✗ 判负不可测）

（完）
