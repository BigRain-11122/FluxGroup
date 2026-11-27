# R-20260924-infra-5 直播推流全链路调研简报（第 5 路）

- 调研员：CPH4 Labs 并行调研 · 2026-09-24 · 依据 CEO 五技术底层问题调研令（第 5 路）
- 三态标注：**[确认]**=本地实测/官方页核验（带 URL+日期）；**[推测]**=推断待验；**[待证]**=拿不到现行值
- 唯一写入件=本简报；无任何其他文件改动；无 git 操作（主会话统一提交）

## §0 一页链路图 + 分阶段总览

```
[采集] Tuanjie 1.10.3 City 工程（bm-a·2022.3.62t15）
  A 系 前台窗口: gfxcapture(新·窗口级·被遮挡可取) / gdigrab(C-26 先例) / ddagrab(全桌面)
  B 系 引擎内: Camera.Render→RenderTexture→ReadPixels 管道（截图证明链 r12-r14 先例）
  前提新件: City 常驻播放器 build（当前城=编辑器批跑形态·无 player build [确认空白]）
      ↓ 原始帧 10-30fps（像素动画 10fps 正典 P-17）
[编码] NVENC h264（RTX 4070S 12GB·ffmpeg 9.0.1 h264_nvenc 本机实测在）
      ↓ 码流×1（tee 一编多推）
[推流×3]（三平台通道异构——见 §2 门槛矩阵）
  ├ RTMP → B站（第三方推流须粉丝≥5000·2025-05 新规；否则官方直播姬）
  ├ RTMP → 视频号（认证+推流权限申请通过后取码）
  └ 虚拟摄像头 → 抖音「直播伴侣」采集推流（0 粉可开·无第三方 RTMP 通道）
[弹幕回流] B站直播开放平台弹幕 WS（入驻审核制·个人门槛待证）
  抖音/视频号: 无公开 API=缺口如实记录
      ↓ 弹幕探针（perceptor 新文件·只读）
[入城] world-events JSONL → DANMAKU_* 事件族（T2 登记·7 天否决窗）
  → 引擎 EventRouter 映射表加行 → 城内信使粒子/弹幕雨/光脉冲（TECH §五拓展检查单 3 处改动面）
```

分阶段总览：**P0** B站官方直播姬窗口捕获开播（0 粉合法·零新代码）→ **P1** 三平台同窗（ffmpeg tee 一编多推+伴侣虚拟摄像头）→ **P2** 弹幕回流+DANMAKU_* 入城（T2）→ **P3** 24h 无人编排（平台政策高危·CEO 单独立项）。每阶段判据见 §4/§7。

## §1 现状与空白清单（代码级事实）

**已有资产 [确认]**（rg --no-ignore 全集团实测 2026-09-24）：
1. **C-26 屏录采集站 live**：`media/BigStream/src/render/record_screen.py`——ctypes 精确找窗 + FFmpeg **gdigrab** 区域采集（零安装），45s 首录实证（Biggame 总控·O-20260924-1115·1366x1079 奇数修复在案）；该令立「静默律外例=CEO 明令画面采集」先例——**前台窗口捕获路径集团已过实测**。
2. **OBS Studio 便携版在库**：`gaming/MiniGame/Software/OBS_录屏/`——obs-nvenc 插件（NVENC 编码就绪）+ rtmp-services 平台预设库（bin/data/obs-plugins 实测在盘）。
3. **FFmpeg 9.0.1 已装**（bm-a·gyan.dev full build·2026 现行版）：本机实测 `ffmpeg -encoders` 含 h264_nvenc/hevc_nvenc/av1_nvenc；`-filters` 含 **ddagrab + gfxcapture**——采集+硬编工具层全套现役。
4. **引擎批渲染先例**：City 工程 `-batchmode Camera.Render + ReadPixels→EncodeToPNG` 全套截图证明链（TECH §九 r12-r14·uGUI Overlay 陷阱/ReadPixels 行序陷阱在册）。
5. **直播镜头现成**：P-17 相机 L0 全景 48s/37s 双周期缓动漂移——观城漂移镜头天然直播观感，零新编排。
6. **弹幕入城消费端现成**：EventRouter 10s 轮询（TECH §七）+ events-registry 登记制 31 型 + T2 先登记后产出律 + verify.ps1 门禁。
7. **账号台账**：BigStream 11 平台**全未注册**（docs/accounts.md·账号=CEO 物理件）；已批开通批次①视频号+公众号 →②抖音+B站——三平台恰好全在批次①②。
8. CityWatch=静态 HTML 快照+无头 Edge 截图（city-watch.ps1 实读：只读聚合 state/events/git/Ollama）——CEO「离线快照非实时」判断属实。

**空白 [确认]**（CEO 原话「一行代码都没有」核验=成立）：
- `rtmp|nvenc|gdigrab|ddagrab|danmaku` 全集团命中仅：OBS 安装包 locale 文件、BigStream 屏录站/台账、资产二进制——**直播推流链路零产品代码**。
- events-registry 31 型**无 DANMAKU_* 族**（schema/events-registry.json 实读）。
- **无 City 常驻播放器 build**（直播需常驻渲染进程·当前城只有编辑器批跑）。
- 无推流编排器/无弹幕探针/无平台凭据（.env 密钥面不存在）。

## §2 三平台准入矩阵（全部现行核验·带日期）

| 维度 | B站 | 抖音 | 视频号 |
|---|---|---|---|
| 集团账号现状 [确认] | 未注册·批次② | 未注册·批次② | 未注册·批次①（已批首发） |
| 基础开播资格 | 实名即可；官方工具 0 粉可开播 | 实名+年满18；**直播伴侣 0 粉可开播**（官方文档 streamingtool.douyin.com/docs/qna_aqv5pxy7「伴侣已支持0粉开播」[确认·现行]） | 手机微信内开播零门槛（实名）；PC 侧见下行 |
| 第三方 RTMP 推流（OBS/ffmpeg） | **粉丝≥5000 才有权限**——2025-05-12 官宣·05-26 生效（此前 100 粉）[确认·来源 bilibili.com/blackboard/activity-pSrb2KQb6G.html 官方排查指南「0 粉的主播可通过 PC直播姬…官方开播工具进行直播」+163.com 2025-05-12 报道] | **无官方第三方 RTMP 通道**：用户证据「抖音禁用 OBS 直推」；抓包取码教程=灰色违规路径 [确认·知乎 p/874476240/CSDN 在案·不采]。合规变通=**OBS/ffmpeg 虚拟摄像头→直播伴侣采集推流** | **认证（职业/兴趣）后还须申请推流权限，审核通过后视频号助手后台才有推流码** [确认·obs.cn/article/139+CSDN 129792388 教程链·2022-2023 帖]；免认证变通=OBS 虚拟摄像头+电脑版微信开播 [确认·知乎 p/559134743]；认证粉丝门槛数字 [待证·CEO 登录 channels.weixin.qq.com 亲验] |
| 无人值守政策 | **相对最宽容**：24h 虚拟/AI 直播间生态大量先例 [推测·经验观察非官方明文]；录播挂机有低质治理 | **最严**：健康分制度 2024-01-03 正式运行（初始 100 分·违规扣 1-8 分·分级管理·低分禁播）[确认·sohu/toutiao]；「循环播放预制视频」违规检测警告文案实证 [确认·知乎 p/21354620208·2025]；2026 全平台无人直播新规（toutiao 7654479971875897891）区分「合规动态实景 vs 违规循环录播」[确认·2026] | 带货/橱窗域=「虚拟直播」直接违规（《视频号橱窗达人低质量内容细则》修订·2024-06 征求意见·界面新闻 11304511）[确认]；非带货普通直播无专项细则 [待证]；2026-02-01《直播电商监督管理办法》（市监总局+网信办）数字人主播入国家监管（带货域）[确认·人民网 2026-02-02] |
| 弹幕/数据 API | **直播开放平台**（open-live.bilibili.com）：入驻审核制（申请页存在个人通道 open-register-form/personal·审核 1-3 工作日·密钥邮件发送·「双方联调开发」商务式）→提供弹幕信息推送 WebSocket+开播/下播 API+弹幕发送 [确认·官方页文案]；**个人入驻粉丝门槛数字 [待证]** | 无公开弹幕 API；伴侣仅本地展示；第三方抓包库=灰色不采 [确认·缺口] | 无公开 API——集团既有调研已定谳（BigStream platform-playbook 2026-09-23 在册「视频号：无公开 API」·人工后台导出中转）[确认·缺口] |

**矩阵结论**：P0 最小闭环只有 B站官方直播姬路零门槛可走；三平台「无人值守」容忍度=B站>视频号（非带货域）>抖音（最严）。

## §3 技术选型对比

### 3.1 采集（bm-a·像素城 10-30fps 足够）

| 方案 | 机制 | 窗口/遮挡 | 现状 |
|---|---|---|---|
| A1 gdigrab | GDI·`title=窗口名` | 窗口级·**被遮挡会录到遮挡物**·30fps 上限 | **C-26 集团已实测**（45s 成片） |
| A2 gfxcapture | Windows.Graphics.Capture（Win10+）·ffmpeg 9.0.1 新滤镜 | **窗口级·被遮挡/最小化也能取**·max 60fps·VFR·D3D11 帧可直通 NVENC | ffmpeg 官方 wiki 现行推荐 [确认·trac.ffmpeg.org/wiki/Capture/Desktop·2025-09-14 更新]；本机在·未实测 |
| A3 ddagrab | Desktop Duplication（Win8+） | 只能全桌面·D3D11 **零拷贝直通 NVENC** | 同上 |
| B 引擎内 ReadPixels 管道 | Camera.Render→RT→ReadPixels/AsyncGPUReadback→stdout 帧流 | 无窗口依赖·**headless 无人值守正规军**·可叠加 UI | 截图证明链 r12-r14 先例 [确认]；连续帧管道=新开发 [待证] |

取舍：P0-P1 用 A 系前台窗口（A2 gfxcapture 首选·A1 兜底）；P2+ 升 B 系引擎内管道。**共同前提=City 常驻播放器 build**（前台捕获需窗口常驻；O-1115 静默律外例先例适用=CEO 明令画面采集授权，24h 常驻窗属更大例外→P3 必须走 B 系 headless）。

### 3.2 编码（与回测动员令的让路关系=本节核心）

- **NVENC h264（首选）**：4070S（单 NVENC 引擎）·ffmpeg h264_nvenc 本机在 [确认]。GeForce 并发会话上限演进：3→5（驱动 531.41·2023-03-23 发布·tomshardware/techspot）→**8**（2024-01 起 Reddit r/nvidia+NV 开发者论坛实证）[确认]——本链路 tee 一编=1 会话、OBS 三输出=3 会话，均≤8。1080p30 NVENC 显存 ~1GB·CPU 近零——**GPU 编码车道天然绕开回测动员令的 CPU 保留 20% 车道**，无让路冲突；仅需 fleet §10 共享机纪律前置（verdict 检查·RAM<4GB 禁新重活·GPU keepwarm 释放阀共存）。
- **x264 veryfast（备胎）**：1080p30 约吃 4-6 核满载/路·medium 翻倍 [推测·量级]；32 核 bm-a 理论可跑但**与回测抢 CPU 车道**；bm-b（16 核·无 NVENC）=回测宿主 Money02·动员令期不可借 [确认·fleet-allocations]——x264 无部署位，仅 NVENC 失效时降级预案。

### 3.3 推流宿主（三通道异构）

```
City player 前台窗口（gfxcapture/gdigrab）
  → ffmpeg 编码 h264_nvenc ×1
     ├ tee muxer → RTMP B站（≥5000 粉后·B站直播间开播设置取地址+推流码 [确认·官方排查指南语境]）
     ├ tee muxer → RTMP 视频号（视频号助手「直播管理→创建直播」取推流地址+密钥 [确认·教程链]）
     └ dshow 虚拟摄像头 → 抖音直播伴侣采集 → 伴侣推流（伴侣内部编码·官方通道）
```

- **ffmpeg CLI = 静默律最优宿主**（零 GUI 零弹窗·tee 一编多推·断流重连脚本化）。
- OBS 便携版（在库）= P1 值班可视化面/虚拟摄像头出口（obs-nvenc+平台预设现成；CLI flags `--startstreaming --minimize-to-tray --disable-updater` 可静默但故障弹窗风险 [待证]）。
- 抖音伴侣 = 官方唯一通道但 GUI 常驻——**无人值守自动化脆弱 [待证]**，P1-P2 限有人值守时段。
- 零服务器红线判读：本链路=本地进程直连三平台 RTMP/伴侣，**无任何自建服务器/无公网入站端口**——不触零服务器红线 [确认·判读]。

### 3.4 带宽与机队

- 上行需求：B站+视频号 RTMP 各 4-6Mbps + 抖音伴侣 6-8Mbps（伴侣 1080p 推荐 6Mbps [确认·CSDN 143184539]）≈ **15-20Mbps 上行**——bm-a 上行带宽 [待证·P0 前实测]。
- 承建机=bm-a（集团唯一 NVENC 机·FluxVerse 承建位已在 fleet-allocations 表 [确认]）；bm-a 实测 YELLOW-HEAVY（2026-09-24 心跳 [确认]）——开播时段须与 BigMoney GPU 空窗协商（fleet §10 verdict 驱动）。

## §4 分阶段实施计划

- **P0 单平台最小闭环（B站·零新代码路径）**
  内容：City player build（DevLoop·P-15 工程产物线）→ CEO 注册 B站+实名 → **官方 PC 直播姬窗口捕获开播**（0 粉合法通道）→ 30min 试播。
  判据：城画面 B站直播间可见 30min 稳定零崩溃；截图取证入 docs/；开播配置先 commit+打 tag（发布锚律 §3.4）；CEO 亲验。
- **P1 三平台同窗（账号门槛各就位后）**
  内容：ffmpeg tee 一编两推（B站+视频号 RTMP）+虚拟摄像头喂抖音伴侣；断流自愈脚本；OBS 值班面板。
  判据：三平台同窗开播画面同步；RTMP 路延迟<5s [待证]；断网模拟自愈 3 连通过；全程零弹窗（静默律）。
  依赖（日历瓶颈）：B站 5000 粉养号（BigStream「拍城」内容线导流）/视频号认证+推流权限申请/抖音实名——全 CEO 物理件。
- **P2 弹幕入城（T2 事件族）**
  内容：B站直播开放平台入驻（CEO 申请·密钥物理件）→ 弹幕 WS 探针 `probes/danmaku.ps1`（ASCII 律·只读·游标 `dm:<platform>:<id>`）→ **DANMAKU_MSG/GIFT/ENTER/LIKE 四型 T2 先登记**（7 天否决窗）→ 引擎映射表加行（信使粒子/弹幕雨/光脉冲）→ 内容过滤门（外部文本入城前置）。
  判据：真弹幕→城内呈现 ≤10s；T2 流程全绿（否决窗期满无否决+scan/verify 双绿）；脏词样例零入城断言；弹幕风暴节流（10s 轮聚合·粗粒度令牌律 r48 同族）。
- **P3 24h 无人编排（CEO 单独立项·政策高危）**
  内容：B 系引擎内 headless 帧管道+开机自启+计划任务+断流自愈+排播（r13 四档昼夜色轮=天然 24h 内容骨架）。
  判据：72h 连播零人工干预；三平台零违规警告记录（健康分无扣分）；带宽峰谷实测入台账。
  策略：**B站先行试点**（虚拟直播生态最宽容）→ 视频号非带货域次之 → **抖音默认不启**（无人值守=违规高危）。

## §5 风险与合规

1. **平台封禁**：抖音健康分扣分→断播→收回直播权限阶梯 [确认·2024-01-03 制度]；2026 全平台无人直播新规趋严 [确认]——P3 抖音通道默认关闭是设计结论而非妥协。视频号带货域虚拟直播=违规 [确认·2024-06 细则]；我方非带货像素城直播属其细则外域但数字人治理趋严，开播前逐平台人工复核现行规则（平台规则变动频繁·本简报全部数字 2026-09-24 核验）。
2. **内容安全**：弹幕=外部文本入城——过滤门为 P2 硬前置（脏词/敏感词/广告词表·探针内实现）；**AIGC 标识义务**：直播画面=AI 生成像素城，依《人工智能生成合成内容标识办法》（2025-09-01 施行 [确认·公开法规]）直播间标题/简介显著标注（BigStream CONSTITUTION 红线同款）。
3. **静默律**：无人值守禁弹窗——ffmpeg CLI 直推零弹窗（B站/视频号路合规）；伴侣/OBS GUI=有人值守时段；P3 headless 引擎内管道是静默律正解。
4. **发布锚律**（versioning §3.4）：每次开播所用 City build+推流配置可定位到唯一 commit（tag）——开播脚本将 tag 写入直播间简介=对外可追溯。
5. **单点与让路**：bm-a 三线并跑（BigMoney 开发+Biggame EngineTick+FluxVerse）+YELLOW-HEAVY 实测——开播窗口与回测 GPU 空窗协商；上行带宽 [待证] 是隐藏硬门槛。

## §6 分工（禁双开工边界）

| 面 | 归属 | 边界 |
|---|---|---|
| 三平台账号注册/实名/认证/推流权限申请/B站开放平台入驻 | **CEO 物理件**（AI 永不代办·accounts.md 纪律） | 密钥只进 .env（gitignored） |
| City player build+引擎内帧管道+DANMAKU 探针+城内弹幕呈现 | **FluxVerse-DevLoop**（引擎+perceptor 域） | world-events/引擎=FluxVerse 仓面 |
| 推流宿主编排（ffmpeg tee/OBS/伴侣操作链）+直播内容策略+账号养粉+直播合规（AIGC 标识） | **BigStream**（媒体产线域·C-26 屏录站同族工具链） | 「拍城」正典内容线承担导流 |
| 本简报+DANMAKU_* 族规格+准入矩阵核验+验收判据 | **CPH4 Labs** | 零产品代码（调研令纪律） |
| 禁双开工执法 | 推流工具链=BigStream（C-26 同族）；事件探针+引擎映射=FluxVerse-DevLoop（perceptor 正典域）；两边不互建（governance §6） | 争议面呈 CEO |

## §7 验收判据（汇总）

- P0：B站直播间 30min 稳定+截图取证+tag 在案+CEO 亲验。
- P1：三平台同窗+断流自愈 3 连+RTMP 延迟<5s+全程零弹窗。
- P2：弹幕→城内呈现 ≤10s+T2 全绿（否决窗期满+scan/verify 双绿）+过滤门断言（脏词样例零入城）+风暴节流实证。
- P3：72h 零人工干预+零平台警告（健康分零扣分）+带宽峰谷入台账。

## §8 诚实自检

- **确认面（带源）**：ffmpeg 9.0.1+h264_nvenc+ddagrab/gfxcapture 本机实测；OBS 便携版在库；C-26 gdigrab 先例；B站第三方推流 5000 粉门槛（2025-05-12 官宣·官方排查指南+163）；抖音伴侣 0 粉开播（streamingtool.douyin.com 官方文档）+禁第三方 RTMP 直推（用户证据+抓包教程=灰色不采）；抖音健康分（2024-01-03）；2026 无人直播新规（toutiao）；视频号带货域虚拟直播违规（2024-06 细则修订·界面新闻）；《直播电商监督管理办法》（2026-02-01）；NVENC 并发 3→5（531.41·2023-03）→8（2024）；视频号无公开 API（集团 platform-playbook 2026-09-23 在册）；全链路零推流代码（rg 实测）；ffmpeg 采集文档（trac.ffmpeg.org·2025-09-14 更新）。
- **勘正**：调研令原文「RTX 4070S 16GB」——fleet-allocations.md 与 BigStream PLAN.md §7-4 双源均载 **12GB**（4070 SUPER 规格），本简报按 12GB 编制；16GB 为 4070 Ti SUPER。
- **待证面**：B站开放平台个人入驻粉丝门槛数字（官方站 JS 空壳取不到正文·CEO 注册后登录 open-live.bilibili.com 亲验）；视频号非带货推流权限条件（CEO 登录 channels.weixin.qq.com 亲验）；City player build 可行性（未建过）；bm-a 上行带宽；直播伴侣无人值守自动化；OBS 便携版版本号；引擎内连续帧管道性能；RTMP 端到端延迟。
- **推测面**：x264 veryfast 核负载量级；上行 15-20Mbps 估算；B站 24h 虚拟直播宽容度=生态经验观察非官方明文。
- **负结果如实**：Bing 中文检索两轮无效（返回无关结果）改用 DuckDuckGo 破壳；B站 open-live 文档主页 JS 渲染空壳——正文级门槛数字留待账号就位后亲验，不以记忆数字冒充现行值。
