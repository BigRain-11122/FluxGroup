# R-20261019-city-carrier-survey-01 — 城市端载体初勘（闭环赋能令配套件·四问直答）
> 溯源：CEO 令 2026-10-19 15:3x 闭环赋能令「我们做的事情都要闭环赋能…MV 真的会在城市大屏幕播放，短剧漫剧等真的会在硅基城市里面发生，委员会去调研，然后落实」·消费方=委员会 C-20261019-01 案（18:00 常务轮证据包）+city-3d/siliconwatch/silicon-city-ops 三线·判据预注册=①城内有无现成屏 ②事件流 schema 兼容度 ③面板挂位 ④媒资可达性
> 验证声明：调研员本机实读 25 次·发现全部 **A 级本机实读**（gaming/=gitignored 子仓·glob/内容检索静默跳坑在案——全程文件系统枚举+逐文件读）；失败面=K:\ 卷本机不存在（任务书路径口径失效·媒资池正身=主仓 media/）；无 B/C 级转述。

## 一、屏幕资产（判定：静态屏现成充足·「会播视频的屏」需新建一组件）
- 屏幕/招牌类 prefab 命中 **691 个**：AD-022 城市包 Billboard 全家族（`City3D\Assets\lowpoly\01_*\AD-022_*\PolygonCity\Prefabs\Props\SM_Prop_Billboard_01/Billboard_Pole_01/Billboard_Roof_01/Billboard_Sign_01~07.prefab`）+Megacity 楼体巨幕（`ithappy\Megacity\Prefabs\Props\advertising_001~005.prefab`·`billboard_001~002.prefab`）+夜店/办公/商店包屏幕补充池。
- **运行时视频链路=零**：两工程 122 个 .cs 全扫·VideoPlayer 引用 0 处·RenderTexture 41 处全为 Editor 截图/验证脚本——做法=屏面材质接 RenderTexture+挂 VideoPlayer（或逐帧序列贴图降级）。

## 二、事件流（判定：管道现成·零 schema 改动）
- `gaming\FluxVerse\world\world-events.jsonl`（409KB）：一行一事件·字段 `ts_utc/type/actor/repo/zone/summary`；`schema\events-registry.json` v0.1=**MEDIA_OUTPUT（BigStream 产物落盘·2026-09-24 起 emitting）与 CONTENT_PUBLISH（内容发布·reserved）已在册**·zone=media·每类型带 city_action 城市动作映射。
- 引擎消费点=`gaming\FluxVerse\City\Assets\Scripts\CityEventRouter.cs`——**只读轮询每 ~10s+SeekToEnd 尾追**·分发 glow 脉冲+音频（FluxAudioRouter）；BreathingPulse 等 8 个 .cs 引用同一流——**事件落 jsonl 即被城市感知**。

## 三、面板位（判定：模板+生成器各一处小改）
- CEO 面板真身=`gaming\MiniGame\硅基生命元宇宙.html`（107KB·当日仍在刷新）·模板=`tools\siliconwatch\canonical.html`（源）·生成器=`generate.ps1`（ASCII 律中文全在 strings.json）·零运行时网络+5 分钟自刷。
- 现有导航 12 面板（#sec-*）；「城内上演」挂位=canonical.html L661-674 nav 构建段加链接+sec-title 块·数据源=generate.ps1 烘焙读媒体档期台账（候选 `media\BigStream\output\finished.md`）——不走运行时轮询（面板零网络律）。

## 四、媒资池（判定：同机同盘可达·任务书路径口径失效）
- K:\ 卷与 `C:\Fluxgroup\FluxGroup\media` 均不存在——**实际媒资池=主仓 `C:\Users\sjs20\Desktop\FluxGroup\media\`**：BigStream（output\renders 逐版目录+finished.md 结算台账）/MV\mv0001（cloud-v4\ blockA/B+KF1~KF10 mp4 共 20+件+audio\mv001_lossless.wav 39.4MB）/MUSIC\jay（12 专辑目录）/drama-pilot-in（seg1~3.mp4+PILOT-PREVIEW-3x20s.mp4）/drama-pilot-out（空）/meme-daily-v1。
- 与 City3D 同机同盘同仓——Unity 可 file:// 直读或拷 StreamingAssets。

## 五、风险与建议面
1. **WebGL 发布目标下 VideoPlayer 支持受限**——城市若走 WebGL·「上大屏」需逐帧序列贴图方案·须真机定谳。
2. **world-events 单写律（P-43）**：城侧只读消费·剧集事件须新增发射探针·禁城内直写 jsonl。
3. 首演片源建议=PILOT-PREVIEW-3x20s.mp4 或 mv0001 cloud-v4 合成块（drama-pilot-out 空+MV 成片呈分镜块形态·无单一长片）。
4. 面板改动必认 canonical.html 为源（防 sync-template 覆盖）。
5. 双工程分工（City3D=装配/City=事件路由）——大屏组件落位哪个工程需先定谳。

## 六、结论应用表
| 结论 | 落点 | 状态 |
|---|---|---|
| 四问全闭环·载体与管道全现成（缺=VideoPlayer 新组件+档期探针一根新线） | 决策呈报（C-20261019-01 §五回填·委员会 18:00 班裁定） | 接线中 |
| 屏幕挂位清单（AD-022 Billboard 家族+Megacity advertising） | 任务单（city-3d 线施工·首屏位选址裁定后） | 接线中 |
| 事件类型复用判定（MEDIA_OUTPUT/CONTENT_PUBLISH 在册零改 schema） | 任务单（发射探针新建·P-43 单写律执法） | 接线中 |
| 媒资池路径勘正（正身=主仓 media/·K:\ 与 C:\Fluxgroup 口径失效） | 判负留痕（任务书旧路径弃用·后续任务单一律用主仓 media/） | 已闭环 |

- 更新记录：T0 调研员骨架（在飞）→ 终稿 15:37 归档（调研员 26 次工具调用·报告全文归档本件·秘书处落盘）。
- 防线二：承重主张两根=①屏幕资产/VideoPlayer 空白（调研员 A 级实读·路径锚在案可回查）②事件流 schema 与消费点（events-registry.json+CityEventRouter.cs 直读）——均为本机 A 级实锚。
