# RESEARCH-账号经营与发布工具链（BigStream 短视频部 · 2026-10-12）

机队约束：Windows + PowerShell + Python，无 Docker。纯 web 调研，来源见文末。

## ① 多平台矩阵发布
- 商用：蚁小二（60+平台、免费≤5账号、20账号档年费≈598元、自带CLI/Agent对接能力）；易媒助手（违规词预检/带货挂车，20账号档年费≈200+元）；聚媒通（基础版30元/月·150元/年≤20账号；IP隔离版488元/年起、1000账号防关联）；新榜小豆芽（AI选题→混剪→发布→数据闭环，运营版年费708元）。价格出自2026-07四工具对比文（疑似软文，仅作量级参考）。
- 开源自建（Windows 可跑、无 Docker）：
  - social-auto-upload（dreammis，12.7k★）：Python+Playwright(patchright反检测)+扫码cookie；抖音/快手/小红书/B站/视频号/YouTube/百家号/TikTok；CLI+WebUI，定时+无头+多账号隔离。
  - MatrixMedia（hanliang97，935★，GPL-2.0）：Electron+Puppeteer 批量发7平台，GUI/CLI/HTTP/MCP，v0.12 自带账号数据统计中心。
  - biliup（Rust CLI）：B站投稿走官方 web 接口，单文件可执行、多P、可作库嵌入。
  - MatrixFlow（fullbearded）：AI 原生分发，备选。

## ② 平台官方发布 API 现状
- 抖音开放平台：有「内容发布」open_api（视频/图片直发抖音），但「视频发布及管理权限」需企业/机构资质，邮件提交授权书+营业执照审核；个人开发者拿不到发布能力，数据接口同样逐项审批。
- 视频号：微信「视频号助手API」仅开放直播基础信息/橱窗/留资/罗盘达人版等；发布接口不面向个人与普通第三方（广告/白名单服务商路线）→ 第三方工具全走浏览器自动化。
- B站：无公开第三方发布 API；web 投稿接口半开放（biliup 即用此），账密登录易触发验证，走 cookie/扫码。
- 结论：小团队合规路径=浏览器自动化自建件；量级上去再以企业资质申请抖音 open_api。

## ③ 数据看板（合规边界）
- 合规线：遵守 robots、走官方授权 API、只取自有账号数据、不逆向签名、不绕风控、不碰他人隐私；违反 robots 已有「不正当竞争」判例，爬隐私数据涉刑事。
- 开源方案：MatrixMedia v0.12 统计中心——登录态本地采集抖音/视频号/B站/百家号/头条/快手/小红书的自有账号粉丝与作品数据，日快照+增量对比；三级取数（页面fetch→被动嗅探→主进程）、单并发限速、数据不出本机；CLI/HTTP/MCP 供脚本与 Agent 查询。
- 抖音官方数据 API 需企业授权；付费替代=新抖/飞瓜/蝉妈妈。完播率/转粉比等深层指标平台不给个人 API，只能登录态后台本地取或人工。

## ④ 剪辑导出自动化
- pyJianYingDraft（GuanYixuan，fork gogelabs/pyjianyingdraft，pip 装）：程序化生成剪映草稿（轨道/字幕/模板/DraftFolder 管理）；Windows 全功能含自动导出，Linux/Mac 不能导出；坑：剪映 6+ 草稿加密，须锁旧版剪映。
- 衔接现状：Python 批量产草稿 → 剪映自动导出 mp4 → 落盘目录 → social-auto-upload/biliup 发布；已有 MCP 封装（自然语言生成草稿）实践，全链可无人值守。

## ⑤ 可落地三件（Windows+PS+Python，接线方式）
1. social-auto-upload＝发布件：git clone → uv sync（或 pip -r）→ cp conf.example.py conf.py → `uv run sau <平台> login` 扫码；PS Register-ScheduledTask 每日调 `uv run sau douyin upload-video --file x.mp4 --title t --headless`，多账号用 --account 隔离 cookie。
2. pyjianyingdraft＝生产件：pip 装进机队 Python，批量产草稿+剪映（锁≤6前版本）自动导出到 watched 目录，PS 收 mp4 喂给发布件。
3. MatrixMedia＝数据件：本机装 Electron 版，开统计中心每日快照，PS 经其 HTTP/MCP 拉 JSON 入库，做涨粉/作品趋势看板（只采自有账号，合规）。
- 备用：biliup-rs 单文件命令直投 B站，PS 一行调用，比浏览器自动化稳。

## 来源
- 蚁小二官网/FAQ/评测：yixiaoer.cn、xueyuan.yixiaoer.cn/article/46354
- 四工具对比（价格）：cnblogs.com/yurenshi/p/21959302
- social-auto-upload：github.com/dreammis/social-auto-upload；实测 blog.mushroom.cv（2026-06）
- 抖音开放平台：developer.open-douyin.com；发布方案与权限申请：open.douyin.com/.../douyin-publish-solution、.../type-and-permission
- 视频号API列表：developers.weixin.qq.com/doc/channels
- biliup：github.com/biliup/biliup、doc.biliup.rs
- MatrixMedia：github.com/hanliang97/MatrixMedia、v2ex.com/t/1247181
- pyJianYingDraft：github.com/GuanYixuan/pyJianYingDraft、pypi.org/project/pyjianyingdraft
- 爬虫合规：ailegal.baidu.com（抖音爬虫合法性问答）、CSDN 2025爬虫合规指南
