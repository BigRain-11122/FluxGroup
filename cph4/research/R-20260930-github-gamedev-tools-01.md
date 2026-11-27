# R-20260930-github-gamedev-tools-01 · GitHub 游戏开发工具调研（微信小游戏工具链 / 图集 / PSD 源修）

- 调研员：D（集团后台调研）
- 日期：2026-09-30（Asia/Shanghai）
- 任务来源：CEO 令「github上有很多相关工具，调研后取用啊」
- 引擎/项目：吸嘟嘟 · 微信小游戏 · 团结引擎（Tuanjie）2022.3 · 主包 ≤4MB
- 范围：A 微信小游戏工具链（wechat-miniprogram 官方 org 全量盘点 + 包体/提审发布自动化，对应挂账「A9 包体预算实测（微信 AAC 转码后）」）；B 纹理/图集开源替代（对照已有 TJ 云图集+PIL 切片链，只判真缺口）；C psd-tools 深评（对应挂账缺陷「ui_postcard_frame 邮戳烤调试色值文本·像素级不可分离·须 PSD 源修」）；D 其它强相关缺口 ≤2。
- 硬标准：每条目 = 仓库真实 URL + star + 最近维护 + LICENSE 实查（MIT/Apache/BSD/CC0/Zlib/MPL=可入；GPL=本机用途+标注禁入发行包；无 LICENSE=判负）+ 平台（Windows/CLI/Python 可自动化）+ 接线点 + verdict（取用/观察/判负）+ 一句话因；一切当场核实，查不到写「未能核实」，禁止凭记忆编造。
- 已装勿重复推荐：gh/gitleaks/lychee/fd/fzf/jq/yq/node/rclone/blender/Pester；已评估勿重复评估：ImageAssert/AltTester/pywinauto。本次全部候选均不与之重叠。
- 数据通道（当天实况，如实记录）：本机 `gh` CLI 未认证不可用；MCP GitHub 工具全组异常（"Could not parse tool response"）；已绕行——GitHub REST API 匿名直连（core 60/时，search 10/分，curl+jq/ConvertFrom-Json 提取）+ raw.githubusercontent 文件直取 + npm/PyPI registry 交叉取证。所有 star/推送时间/许可均为 API 当场输出，非记忆值。

## 0. 结论速览

**一句话**：四件取用——**psd-tools**（解「ui_postcard_frame 邮戳烤调试色值」挂账缺陷，PSD 源修唯一可自动化路径，MIT、调研当日仍在推送）、**minigame-tuanjie-transform-sdk**（微信小游戏「Unity/团结引擎 SDK」官方本体，与我们引擎完全对口，MIT、2026-09-28 仍在推送）、**miniprogram-ci-dist**（miniprogram-ci 官方新家，提审发布自动化唯一正路，MIT 三证）、**fonttools**（主包内嵌 CJK 字体子集化，A9 条件必用，MIT）；一件强预警——**wasmsplit-v2-ci**（WASM 分包，正中 A9 包体挂账，但**无 LICENSE 三证**→判负，且官方 README 明示转换插件 ≥0.1.35 时「必须」配它，处置建议见 A4）；B 面查实**无真缺口**（TJ 云图集+PIL 链已覆盖，FreeTexPacker 作者明示弃坑）；另入账两项「官方仓生死」情报：3351★ 的 minigame-unity-webgl-transform **已被 GitHub Staff 禁用**（商标政策，当日实测不可访问），官方 **miniprogram-automator 已下线**（404 实测）。

| # | 候选 | star | 最近维护 | LICENSE 实查 | verdict |
|---|---|---|---|---|---|
| C1 | psd-tools/psd-tools | 1468 | 2026-09-30（当日） | MIT（API+PyPI） | **取用**（解挂账缺陷） |
| A1 | wechat-miniprogram/minigame-tuanjie-transform-sdk | 190 | 2026-09-28 | MIT（API+仓内 LICENSE 文件） | **取用**（引擎基建） |
| A3 | wechat-miniprogram/miniprogram-ci-dist | 0（新迁仓） | 2026-09-30（当日） | MIT（三证） | **取用**（提审自动化） |
| D1 | fonttools/fonttools | 5269 | 2026-09-29 | MIT（API+PyPI） | **取用**（条件接线：包体含内嵌字体） |
| A5 | wechat-miniprogram/minigame-unity-wechat-preview | 12 | 2025-03-25 | MIT | 观察 |
| A4 | wechat-miniprogram/wasmsplit-v2-ci | 0 | 2026-09-22 | **无（三证均空）** | **判负**（无 LICENSE）＋强预警 |
| A2 | wechat-miniprogram/minigame-unity-webgl-transform | 3351 | 2025-09-12 | MIT | **判负**（仓库已被 GitHub 禁用，不可访问） |
| B1 | odrick/free-tex-packer（+core/cli） | 1285 | 2024-07-14（core 2026-09-11） | MIT | 判负（冗余＋主 GUI 停更） |
| B2 | ask-tao/image-splitter | 129 | 2025-08-25 | MIT | 判负（浏览器 GUI 手工，不可自动化） |
| C2 | PSD 字体提取小工具一族 | ≤15 | 2014–2016 | 部分 MIT | 判负（全灭三看法；psd-tools 自带覆盖） |

## 1. A · 微信小游戏工具链（wechat-miniprogram 官方 org 全量盘点）

### 1.0 盘点方法与总账

- org 仓库全量 **80 个**（`/orgs/wechat-miniprogram/repos` 两页取全，page2 为空），逐仓当场记录 star/pushed_at/license/archived。
- 与小游戏管线相关的官方仓（当场核实值）：`minigame-tuanjie-transform-sdk`（190★/2026-09-28/MIT）、`minigame-unity-webgl-transform`（3351★/2025-09-12/MIT/**已被禁用**，见 A2）、`miniprogram-ci-dist`（0★/2026-09-30/MIT）、`wasmsplit-v2-ci`（0★/2026-09-22/**无 LICENSE**）、`minigame-unity-wechat-preview`（12★/2025-03-25/MIT）、`minigame-canvas-engine`（312★/2026-09-10/MIT，canvas2D 布局引擎——我们走团结渲染，不需要）、`lottie-miniprogram`（432★/2024-05-07/MIT，小游戏 Lottie 播放器——同上不需要）、`minigame-api-typings`（162★/2026-07-27/MIT，wx API 的 TS 类型——仅当手写 JS 胶水才有用，备查）、`minigame-lockstep-demo`（128★/2026-03-09/MIT，帧同步 demo——无多人需求，不采）、`miniprogram-slim`（129★/**已归档** 2022-12-11/MIT，包体瘦身——归档且能力已被开发者工具内置依赖分析取代，不采）、`minigame-adaptor`（136★/已归档 2021/NOASSERTION，不采）、`ai-mode-skills`（206★/2026-09-10/MIT，见 4.1 未凑数说明）、`wasmsplit-ci`（V1，0★/2026-07-07/无 LICENSE，官方明示不再维护）。
- **三条「官方仓生死」硬情报（当日实测，均与采信路径直接相关）**：
  1. 旧主仓 `wechat-miniprogram/miniprogram-ci` **已不可访问**（API 404，也不在 org 列表）——源码与 README 迁至 `miniprogram-ci-dist`，npm 包 `repository.url` 直指该仓（三证闭环，见 A3）；
  2. `minigame-unity-webgl-transform` **被 GitHub Staff 禁用**（HTML 页原文："Access to this repository has been disabled by GitHub Staff due to a violation of GitHub's Trademark Policy"），API 报 "Repository access blocked"，其 GitHub Pages 文档站同日 404——见 A2；
  3. 官方自动化测试仓 `wechat-miniprogram/miniprogram-automator` **已下线**（API 404 实测，org 列表亦无）——坐实 A3 是提审发布自动化的唯一官方正路。

### A1 · minigame-tuanjie-transform-sdk —— 官方「微信小游戏 Unity/团结引擎 SDK」本体 ⭐核心

- URL：https://github.com/wechat-miniprogram/minigame-tuanjie-transform-sdk
- star：190 ／ 最近维护：2026-09-28（调研前 2 天仍在推送）／ archived=否
- LICENSE：**MIT**（GitHub API 实查；仓库根目录实见 `LICENSE` 文件）
- 平台：Unity/团结 Package Manager 经 git URL 安装（README 原文：`Window - Package Manager - 右上 + - Add package from git URL... 输入本仓库Git资源地址`）；Windows 友好；UPM 包名实查 `com.qq.weixin.minigame`
- 内容实查（README 直引）：标题「微信小游戏Unity/团结引擎SDK」；「有关微信SDK的最新特性与使用请阅读 Unity WebGL 微信小游戏适配方案」；FAQ 含「空项目/未用 WXSDK Runtime 能力时，团结引擎导出项目将微信 Runtime 包裁剪 → 在游戏合理位置增加对 WXSDK 的使用即可」（我们导出 SOP 直收此坑）
- CHANGELOG 实查（`CHANGELOG.md` 直引）：最新条目 **2026-9-16 v0.1.34**，含「多包融合工具」「EmscriptenGLX 支持压缩纹理」「EmscriptenGLX 支持多线程」「鸿蒙视频音频播放适配」等——**包体/纹理压缩方向在活跃演进，正是 A9 的配套能力**；仓 2026-09-28 仍有推送（≥0.1.35 或在预备，见 A4 预警）
- ⚠️ 如实记录：README 所指文档站 https://wechat-miniprogram.github.io/minigame-unity-webgl-transform/ 当日实测 **404**（其宿主仓库已被禁用，见 A2）——文档以 SDK 仓内文件 + developers.weixin.qq.com 小游戏频道为准
- 接线点：①团结 2022.3 工程 Package Manager 挂 `https://github.com/wechat-miniprogram/minigame-tuanjie-transform-sdk.git`，WXSDK（登录/分享/性能/资源加载）以此为唯一官方更新源；②**版本锁定**：UPM git 引用锁到提交/版本（当前 CHANGELOG 最新 v0.1.34），升级前先看 A4 许可预警；③导出裁剪坑写入《微信导出 SOP》
- verdict：**取用**
- 一句话因：官方团结引擎专用 SDK，与本项目引擎完全对口、两天前仍在更新、MIT 无风险，A9 的压缩纹理/多包能力也随它演进。

### A2 · minigame-unity-webgl-transform —— 3351★ 文档库：**已被 GitHub 禁用，当下不可取用**

- URL：https://github.com/wechat-miniprogram/minigame-unity-webgl-transform
- star：3351 ／ 最后推送：2025-09-12 ／ LICENSE：MIT（org listing 实查）
- 描述（API 原文）："Wechat Mini Game Unity engine adapter documents."
- **生死实查（2026-09-30）**：
  - 仓库 HTML 页原文："### This repository has been disabled … due to a violation of GitHub's Trademark Policy"（GitHub Staff 禁用，商标政策违规）；
  - API `/contents` 返回 "Repository access blocked"；raw README 404；
  - 其 GitHub Pages 文档站 https://wechat-miniprogram.github.io/minigame-unity-webgl-transform/ 实测 404（curl 状态码直查）。
- 判定说明：star/许可数据仍由 org listing 返回（禁用仓仍列示），但**内容当下完全不可访问**；其职能（Unity→小游戏适配方案/文档）对我们团结项目本就由 A1 SDK 承接，文档侧改以 developers.weixin.qq.com 小游戏频道 + A1 仓内文件为准。
- verdict：**判负**（当下不可访问；留观官方是否迁移/恢复，恢复后按 MIT 可转「取用」）
- 一句话因：曾经的权威文档库已被 GitHub 禁用+文档站同死，取用无门，职能由 A1 与官方文档站承接。

### A3 · miniprogram-ci（官方新家 = miniprogram-ci-dist）—— 上传/预览/构建自动化 CLI ⭐核心

- URL：https://github.com/wechat-miniprogram/miniprogram-ci-dist
- star：0（2026 年新迁移仓，热度未跟上；npm 包 `miniprogram-ci` 即其发行面，最新 **2.1.48**）
- 最近维护：2026-09-30（调研当日有推送）；npm 包当日可用
- LICENSE：**MIT，三证实查**——①仓 `package.json` 实取 `"license": "MIT"`；②npm registry `miniprogram-ci/2.1.48` 实取 `"license": "MIT"`；③npm 包 `repository.url` 实取 `git+https://github.com/wechat-miniprogram/miniprogram-ci-dist.git`（官方归属闭环）
- 平台：Node.js CLI（`bin/miniprogram-ci.js`），Windows 可自动化；前置（README 原文）：需小程序管理员身份在 mp 后台「开发-开发设置」下载**代码上传密钥**并配置 **IP 白名单**
- 内容实查（README 直引）：「miniprogram-ci 是从微信开发者工具中抽离的关于小程序/**小游戏**项目代码的编译模块」；近期变更含「依赖分析升级」「terser 5.27.1」「修复 不编译代码的情况下代码体积依然变大的问题」等
- 接线点：**提审发布自动化主件**——发布脚本以 `miniprogram-ci upload`（`--pp` 项目路径 / `--pkp` 密钥路径 / `--appid` / `--uv` 版本号等，参数表以仓内 README 为准）替代手工开发者工具上传；密钥走内部凭据管理不入库；构建产物体积日志回填 A9 包体台账
- verdict：**取用**
- 一句话因：官方上传/预览自动化唯一正路（automator 已下线佐证），MIT 三证、调研当日仍在发版。

### A4 · wasmsplit-v2-ci —— WASM 分包（正中 A9，但无 LICENSE → 判负 + 强预警）⚠️

- URL：https://github.com/wechat-miniprogram/wasmsplit-v2-ci
- star：0 ／ 最近维护：2026-09-22 ／ npm：`wasmsplit-v2-ci` 最新 **2.1.5**（registry modified 2026-09-22）
- LICENSE：**无——三证均空**：①GitHub API license=null（默认分支 master 实查）；②仓 `package.json` 实取 `l:null`；③npm registry license 字段为空。V1 `wasmsplit-ci` 同样无许可（npm 1.1.37 实查 license 空），且官方 README 明示 V1「不会再维护」。
- 平台：Node CLI（`npm install -g wasmsplit-v2-ci`），Windows 可自动化
- 用途实查（README 直引）：「微信小游戏通用适配方案的 Wasm 代码分包工具（命令行/CI 版本）。把小游戏的 wasm 代码包拆分为首包与子包，降低启动下载耗时与编译耗时；配合 iOS 高性能模式按函数粒度按需加载，降低运行时内存压力」；CI 三行：`init` → `getinfo`（导出函数收集信息）→ `dosplit --release`
- **强预警（与 A1 版本强绑定，README 直引）**：「当使用最新的微信转换插件导出微信小游戏时（版本 >= 0.1.35），必须使用本工具与 V2 IDE 插件。版本 <= 0.1.34 时，必须使用 V1」——即 A1 升到 ≥0.1.35 后，本工具进入**强制**路径，届时许可问题必须先解决。
- 接线点（**未接线**，待许可）：若将来升级 A1 ≥0.1.35，先向上游提 issue 索要 LICENSE 或取得官方书面授权（腾讯官方仓，可走商务/社区渠道），再按「CI 三行」接入发布流水线；当前处置=**A1 锁 ≤0.1.34**，绕开强制依赖。
- verdict：**判负**（无 LICENSE，按硬标准）
- 一句话因：能力正中 A9 包体挂账、官方且新，但三证查无任何许可声明——禁入管线，先锁 SDK ≤0.1.34 并向上游催许可。

### A5 · minigame-unity-wechat-preview —— WXSDK 免转换真机预览插件（官方，实验性依赖）

- URL：https://github.com/wechat-miniprogram/minigame-unity-wechat-preview
- star：12 ／ 最近维护：2025-03-25 ／ LICENSE：MIT ／ archived=否
- 平台：团结/Unity UPM 包（git URL 导入，README 实查步骤）；依赖（README 直引）：Newtonsoft Json 3.2.1、**WebRTC 3.0.0-pre.6、Unity Render Streaming 3.1.0-exp.7**（experimental）、Input System 1.5.1、WXSDK ≥0.1.25
- 用途实查（README 直引）：「为了为开发者提供无需转换即可预览 WXSDK 效果的支持，推出了基于 WebRTC 音视频与数据传输的 WeChat Preview 插件」——Editor 内点「开始运行」→ 手机扫码或开发者工具打开本地预览包即可真机预览（Portrait/Landscape、帧率 30、码率/缩放可配、可显示触摸位置、音频 APIOnly/AudioSource 可选）
- 接线点：微信能力联调加速（登录/分享/支付类 WXSDK 行为免整包转换在真机快速验证）；须 Editor 与手机同局域网
- verdict：**观察**（价值真实=联调节省整包转换时间，但依赖 experimental 的 Render Streaming 栈、star 低、半年未推——先观望，联调痛点实感强烈时再试）
- 一句话因：官方免转换预览唯一方案、MIT，但依赖实验性 WebRTC 栈且热度极低，按需再启用。

## 2. B · 纹理/图集开源替代（对照「TJ 云图集 + PIL 切片链」判增量）

### 2.0 结论：**无真缺口，不新增工具**

引擎内打包已被 TJ 云图集（SpriteAtlas 编译期产出）覆盖，切片已被 PIL 链覆盖；引擎外独立打包/切图的候选要么作者弃坑、要么是 GUI 手工工具不可自动化、要么许可缺失或生态错位（libGDX/UE/运行时向）。为避免凑数，逐条判负并留档如下。

### B1 · odrick/free-tex-packer（+core/cli 家族）—— TexturePacker 最知名开源替代

- URL：https://github.com/odrick/free-tex-packer
- star：1285 ／ 最近维护：2024-07-14 ／ LICENSE：MIT（API 实查）
- **作者弃坑声明（README 直引）**："IMPORTANT: I don't have time to imporove this app anymore. Only critical bugs will be fixed."
- 家族实查（全 MIT）：`free-tex-packer-core`（151★，**2026-09-11 仍活跃**，JS/TS 核心库）；`free-tex-packer-cli`（25★，2023-06-14 停更）；gulp/webpack 插件（2021 停更）
- 能力（README 实查）：rotation/trimming/multipacking，导出 json/xml/css/pixi.js/godot/phaser/cocos2d，Zip 支持，TinyPNG 支持，Split sheet 工具，mustache 自定义模板
- 增量判定：引擎内 → TJ 云图集已覆盖且编译期自动；引擎外批量重排/第三方格式导出 → 当前管线无此场景；主 GUI 作者明示弃坑，CLI 停更 3 年。
- verdict：**判负**（管线冗余＋主工具弃坑；唯一活支线 core 是给 JS 开发者嵌 Web 管线的，与我们无接线点）
- 一句话因：MIT 但已是弃坑工具，且我们两条既有链把它的场景全部覆盖——取用=纯冗余。

### B2 · ask-tao/image-splitter —— 雪碧图浏览器切图工具（本次检索面最优切片工具）

- URL：https://github.com/ask-tao/image-splitter
- star：129 ／ 最近维护：2025-08-25 ／ LICENSE：MIT
- 平台（README 实查）：Vue3 + Vite 的**浏览器端**工具，「完全在浏览器端本地运行」——手工 GUI，非 CLI/Python，不可自动化接线
- 能力（README 实查）：框选模式（**自动识别**＋拖拽选框）、内边距模式、固定宽高模式、网格模式
- 增量判定：PIL 切片链已覆盖自动化切片；本工具唯一亮点「自动识别不规则子图」当前无对应场景（我们源图来自 PSD 分层导出，切图边界已知）。
- verdict：**判负**（浏览器 GUI 手工工具，不可自动化；能力被 PIL 链覆盖）
- 一句话因：自动识别是唯一亮点，但场景不存在且不可脚本化——留档不接线。

### 2.2 扫过即弃清单（当场核实过、不单独立条目的其余候选）

| 仓库 | star / 维护 / 许可 | 弃因（一句话） |
|---|---|---|
| crashinvaders/gdx-texture-packer-gui | 707 / 2024-08-09 / Apache-2.0 | libGDX 生态 GUI 打包器，Unity/团结管线接不上 |
| maxartz15/MA_TextureAtlasser | 502 / 2026-09-14 / MIT | Unity 编辑器**手动**合图工具，与 SpriteAtlas（TJ 云图集）能力冗余 |
| Thekla/thekla_atlas | 501 / 2026-04-09 / MIT | 运行时 C++ 网格 atlas（The Witness 系），非 2D 精灵图集工具 |
| firtoz/Unity3D-TextureAtlasSlicer | 141 / 2026-01-10 / **无 LICENSE** | TexturePacker XML→Unity 导入桥，无许可判负且我们不用 TexturePacker |
| nical/guillotiere | 198 / 2026-03-18 / NOASSERTION | 运行时动态图集分配器（Rust），许可不明且非管线位 |
| microsoft/UVAtlas | 927 / 2026-04-22 / MIT | 3D 网格 UV atlas，与 2D 精灵图集无关 |
| memononen/fontstash | 785 / 2023-07-13 / Zlib | 运行时字体纹理图集（C 库），与资产管线无关 |
| azarrias/sprite-sheet-splitter 等 GPL/无许可小工具 | ≤10 | GPL（仅本机）或无许可，star 过不了三看法 |

## 3. C · psd-tools 深评（缺陷：ui_postcard_frame 邮戳烤调试色值文本·像素级不可分离·须 PSD 源修）

### 3.0 结论

**psd-tools 完整覆盖「定位→删除→存盘→重导出」四步 PSD 源修链，且无需安装 Photoshop**；改写文本内容/字体渲染不支持——但我们的目标恰是**整层清除**而非改写，短板无碍。判：**取用**，为本次调研接线价值第一。

### C1 · psd-tools/psd-tools

- URL：https://github.com/psd-tools/psd-tools
- star：1468 ／ 最近维护：**2026-09-30（调研当日有推送）** ／ LICENSE：**MIT**（GitHub API 实查）／ PyPI 最新 **1.21.0**（registry 实查）
- 平台：Python 包（Windows/CLI 可自动化，`pip install psd-tools`，`pip install 'psd-tools[composite]'` 可选强化合成）；自带 CLI：`psd-tools export in.psd out.png`、`psd-tools export in.psd[0] out-0.png`（**官方 usage 文档直引**，可整图/按层导出 PNG）
- **能力-缺陷映射（全部源码/文档当场直引）**：

| 修复步骤 | psd-tools 能力 | 证据（当日直引） |
|---|---|---|
| ① 定位调试文本层 | 遍历全图层 `psd.descendants()`；`TypeLayer`（文本层）可读 `layer.text`（只读）、`layer.kind`；按层名/文本正则匹配调试标记（如色值 `#xxxxxx`、`debug` 等） | layers.py 实查：`class TypeLayer(Layer): "Layer that has text and styling information…"`；`def text(self) -> str: "Text in the layer. Read-only."`；`def descendants(include_clip=True)`（GroupMixin） |
| ② 整层删除 | `layer.parent.remove(layer)`（官方推荐写法；`Layer.delete_layer()` 为其弃用别名） | layers.py 实查：`def remove(self, layer: Layer) -> Self: "Removes the specified layer from the group. This operation rewrites the internal references of the layer."`；README：「Basic editing of pixel layers and groups, such as **adding or removing a layer**」（limited support 项） |
| ③ 写回 PSD 源 | `psd.save('fixed.psd')` | psd_image.py 实查 `def save(...)`；usage.rst 直引：「If the PSD File's layer structure was updated, saving it will update the ImageData section.」 |
| ④ 重导出净版 PNG | `psd.composite().save('fixed.png')` 或按层导出；文本层在 PSD 内自带栅格缓存，合成**不需要字体**（规避其「Font rendering 不支持」短板） | README：「Read and write of the low-level PSD/PSB file structure」；CLI export 命令见上 |

- **官方保真警告（usage.rst 直引，如实入账）**：「the rendered image is likely different from the Photoshop's rendering due to the limited rendering support in psd_tools」——即 composite 导出与 Photoshop 渲染可能有差；处置见 3.2 的双路方案与验收门。
- issue 面核查（search 实查）：未发现「删层后存盘损坏」类聚集 issue；近期 issue/PR 集中在合成保真修复（如 Knockout compositing、Lab 合成、描边效果 #825，2026-08/09 连续合入）——存盘与合成路径在活跃维护。
- **顺带查（PSD 文本/字体信息提取）**：psd-tools 自带 `TypeLayer.typesetting`（typesetting.py 实查：`class FontInfo`，`postscript_name / family / style`；usage.rst 示例直引 `for run in paragraph: print(run.text, run.style.font_name, run.style.font_size)`）——**字体名/字号/逐段文本均可脚本提取**，可直接用于美术台账（PSD 用了什么字体→是否需要入包，衔接 D1）。

### 3.2 缺陷修复操作方案（拟，主会话可一步执行）

前提（如实声明）：该调试色值文本在 PSD 源中为**独立图层**（文本层或独立像素层）；若已被栅格化并入邮戳美术同一层，则任何工具都救不了，只能回美术重制。

```python
# scripts/psd_strip_debug.py（拟）
from psd_tools import PSDImage
psd = PSDImage.open('ui_postcard_frame.psd')
for layer in list(psd.descendants()):              # 遍历全树（GroupMixin.descendants，实查）
    if layer.kind == 'type' and is_debug_marker(layer.text, layer.name):   # 只读文本定位（实查 API）
        layer.parent.remove(layer)                 # 官方删层 API（实查：重写层内部引用）
psd.save('ui_postcard_frame.fixed.psd')            # PSD 源修完成（实查：save 更新 ImageData 节）
psd.composite().save('ui_postcard_frame.fixed.png')  # 可选：直接产出净版 PNG
```

双路验收：
- **路 A（全自动，先试）**：修后 `composite()` 导出 vs 原版 `composite()` 导出做像素 diff——差异应**只**落在被删调试文本处；通过 → 净版 PNG 直接接既有 PIL 切片链。
- **路 B（保底）**：脚本只做「删层+存盘」，修版 `*.fixed.psd` 交美术在其工具（Photoshop 等）重导出——源修这个最难的环节已自动化，人工只剩导出动作。
- 沿用：同一脚本参数化后可处理所有「PSD 源内清调试残留」类缺陷（正则白名单保护正式图层）。

### 3.3 PSD 字体提取独立工具检索结论（顺带项收口）

检索（`psd font extract` 等组，star 降序）逐仓三看**全灭**：safareli/psd-extractor（15★/2015-11/MIT）、bomberstudios/psd-extract-font-info（12★/2014/MIT）、opi/psdtxtractor（4★/2016/MIT）、hamsterbacke23/psdfontinfo（无许可/2015）、slash3b/extractPSDFonts（无许可/2016）——全部十年前古董、无维护。**结论：不另取工具，psd-tools 的 typesetting API 已覆盖该需求**（见 C1）。

## 4. D · 其它强相关缺口（限 ≤2，须具体接线点）

### D1 · fonttools/fonttools —— CJK 字体子集化（A9 包体的条件必用件）

- URL：https://github.com/fonttools/fonttools
- star：5269 ／ 最近维护：2026-09-29 ／ LICENSE：**MIT**（GitHub API + PyPI 双查）／ PyPI 最新 **4.66.1**；subset 子模块存在性以 raw 直查 HTTP 200 核实（`Lib/fontTools/subset/__init__.py`）
- 平台：Python 库 + `pyftsubset` CLI（Windows 可自动化）
- 缺口论证：微信小游戏主包 ≤4MB；完整 CJK 字体动辄 3–10MB，若 UI 品牌字体（治愈系糖瓷风大概率配圆体/手写体）内嵌，**必须**只保留游戏实际用字——pyftsubset 是事实标准。与 C1 成链：psd-tools 从 PSD 提取 `typesetting` 字体名（C1 实查）→ 设计确认对应字体文件 → fonttools 按游戏文案全集子集化 → MB 级降到 KB 级入包。
- 接线点（条件触发）：A9 包体预算实测时若台账含内嵌 TTF/OTF → `pyftsubset brand.ttf --text-file=<游戏文案全集.txt> --output-file=brand.subset.ttf`（参数细节以官方文档为准），产物入团结工程并复测包体；share 图/远程 CDN 素材中的字体同理。
- verdict：**取用**（条件接线：A9 实测含内嵌字体即启用；不含则不入管线）
- 一句话因：内嵌 CJK 字体子集化的事实标准、MIT、双源活跃，是 4MB 主包预算下唯一能把字体从 MB 打到 KB 的开源件。

### 4.1 未凑数说明（查过、核实过、但不收的 D 候选）

- `wechat-miniprogram/ai-mode-skills`（206★/MIT/2026-09-10）：官方 Agent Skills 库，但方向是「小程序 AI 开发模式」——把小程序源码改造成 AI 可调度的原子接口/组件，需 nightly 开发者工具，面向小程序而非团结渲染的小游戏，与本项目管线无接线点 → 不收。
- `wechat-miniprogram/minigame-api-typings`（162★/MIT/2026-07-27）：wx 小游戏 API 的 TS 类型，仅当手写 JS 胶水才有用——团结导出链自动生成胶水，暂无手写面 → 备查不收。
- `wechat-miniprogram/minigame-canvas-engine`（312★/MIT）与 `lottie-miniprogram`（432★/MIT）：均为「非 Unity 渲染」小游戏的 UI/动画方案，团结渲染管线用不上 → 不收。
- 社区搜索面（`wechat minigame` star 降序）：esengine/estella（682★/Apache-2.0，独立 2D 引擎）、AnranS/godot_for_minigame（57★/MIT，Godot→微信导出）等均引擎错位；fastwego/miniprogram（92★/NOASSERTION/停更 2023）许可不明 → 全部不收。
- D2 空缺声明：以上皆不满足「强相关+具体接线点」双条件，宁缺毋滥，D 仅收 1 件（D1）。

## 5. Top 取用建议排序（按接线价值）

1. **C1 psd-tools**（MIT · 1468★ · 当日活跃）——唯一能**立刻开工解挂账缺陷**的件：「ui_postcard_frame 邮戳烤调试色值文本·须 PSD 源修」四步链（读层定位→官方 API 删层→存盘→composite 重导出）全通，双路验收兜底；附带 PSD 文本/字体台账提取（喂 D1）。
2. **A1 minigame-tuanjie-transform-sdk**（MIT · 190★ · 2026-09-28）——引擎基建级：团结 2022.3 的微信小游戏官方 SDK 本体（UPM git URL 直挂），WXSDK 唯一官方更新源；CHANGELOG 实证包体/压缩纹理方向活跃演进（A9 配套）；**锁 ≤0.1.34** 直至 A4 许可解决。
3. **A3 miniprogram-ci-dist**（MIT 三证 · 当日发版）——提审发布自动化唯一官方正路（automator 已下线佐证）：上传/预览 CLI 进发布脚本，产物体积日志回填 A9 台账；密钥+IP 白名单按其 README。
4. **D1 fonttools**（MIT · 5269★ · 双源活跃）——条件接线：A9 实测含内嵌字体即启用 pyftsubset，CJK 字体 MB→KB，是 4MB 主包的保命件。
5. **A5 minigame-unity-wechat-preview**（MIT · 12★）——观察：微信能力联调免整包转换真机预览，实验性依赖栈，痛点实感强烈时再启。
6. **A4 wasmsplit-v2-ci**（无 LICENSE · 判负）——不接线但**强预警**：A1 ≥0.1.35 起官方强制配套；先锁 0.1.34，同步向上游催 LICENSE/书面授权，许可补齐前不得入管线。

## 6. 执行序（主会话接线步骤，全部不涉及本次调研安装）

- **Step 1（解挂账缺陷）**：按 3.2 方案落 `psd-tools` 修复脚本（路 A 像素 diff 验收 → 过则 PIL 链直连；不过走路 B 交美术重导出）；修版 PSD 归档留证。
- **Step 2（引擎基建）**：团结工程 UPM 挂 A1 SDK git URL，**锁 ≤0.1.34**；导出裁剪坑（WXSDK Runtime 被裁）写入《微信导出 SOP》。
- **Step 3（提审自动化）**：接入 A3 `miniprogram-ci`（npm 安装，密钥入凭据管理），发布脚本替换手工上传；每次构建记录产物体积 → A9 包体台账。
- **Step 4（A9 收口）**：包体实测若含内嵌字体 → 启用 D1 pyftsubset（文案全集子集化）复测；A4 许可未解决前不升 A1 ≥0.1.35。
- **红线**：B 面不新增任何工具（TJ 云图集+PIL 链已覆盖）；A4/A2/无 LICENSE 件一律不入管线；GPL 件（本次仅检索面擦过、未收）不得进发行包。

---

状态：**完成**
（2026-09-30 · 调研员D；全部 star/维护时间/许可均 GitHub/npm/PyPI API 当场核实；三条「官方仓生死」情报（webgl-transform 被禁用、miniprogram-ci 迁移 -dist、automator 下线）当日实测；gh/MCP 故障已绕行不影响证据强度）
