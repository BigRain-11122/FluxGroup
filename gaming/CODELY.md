

## Codely Structured Memories

### User

### Feedback

### Project
- [2026-09-23 13:15:07] MiniGame 项目已于 2026-09-23 从 C:\Users\sjs20\Desktop\MiniGame 迁移至 C:\Users\sjs20\Desktop\FluxGroup\gaming\MiniGame（同卷重命名，.git 完好）。trusted_hooks.json、Biggame总控.lnk 及 20 个 MiniGame* 计划任务已全部改指新路径。迁移后复查（同日13:13）补修三处 finisher 漏项：全局 settings.json cockpit-heartbeat 钩子、GimmeAll ProjectSettings.asset 的 weixinMiniGameTemplate 路径、trusted_hooks.json 中 GUIAgentUnity 工作区残留旧条目——均已改指新址并复查稳定；若 trusted_hooks.json 再现旧路径，重启 Cowork 应用可根治。迁移脚本与日志已于同日经用户确认删除。注意：若有进程 CWD 位于项目根目录内，目录级重命名会被锁死（finisher 曾因继承旧 CWD 自锁），迁移/重命名前需先排查进程工作目录。
- [2026-09-23 13:28:10] MiniGame 根级文件规范整理已完成（2026-09-23·X742 批·U161 落册·commit 623326bb 已推 master）：①删乱码空壳目录 ②软著 8 PDF 归位 _归档/软著解析/ 正名（7 份去"]"残括号，txt 同步 git mv 保历史）③parse_pdf.py 自定位自愈 ④send_report.py 退役入工具退役区 ⑤.codely 剪贴板 png 退跟踪 + gitignore 加 .codely/ 规则 ⑥.gitignore 九段双编码乱码注释重写 UTF-8（规则零改动）⑦README §一⑥本地资源库区/§三/§五 + 08号§1A + 09号§7 地图回写。整理原则=X035「锚点不动、分区可读」：统计件/工程区/01-09包/三库/分机-b/c件全未动。遗留提醒：send_report.py 含明文 QQ 邮箱 SMTP 授权码（已入 git 历史，建议用户轮换）。
- [2026-09-23 13:42:29] MiniGame 流程文档统一整理已完成（2026-09-23·X744 批·U162 落册·commit 1dc27cf1 已推 master）：①开工令/扩容令（已执行毕调度令）归档 _归档/一次性调度令/ ②G10 定纲令归位 G10_CrazyTrade/（4 引用改指）③FE 队列瘦身 130.9→22.3KB（63 条已处置并档入 _归档，13 活条目保留，EvolutionProbe 正则兼容）④README§一②刷新为 19 件实况+§三 00总纲→MASTER ⑤08号§1A、AI总控接口 v1.4、10号§4 补 U140-U161 域行。整理原则：引用普查前置（引用面 2-137 文件的编号文档体系零合并——00/05/06 合并先例已完成）；PixelTownBoard 解析面（美术/音乐清单）与 tick 单写者域（STATUS 146.5/150KB 临界）不碰，STATUS 按 U042 留给 SIG_BLOT→M5 模型层处理。
- [2026-09-23 13:54:39] MiniGame 文件规范规模化硬化已完成（2026-09-23·X745 批·U163 落册·commit a1572591 已推 master）：①tools/RefCheck.ps1=引用普查执法件（U162①机械化·迁移/改名前必跑）②tools/EncodingGate.ps1 挂 .githooks/pre-commit 双闸链=U+FFFD 坏行门禁（fail-open）③Housekeeping 6c 根级游离件周报+tools/root-manifest.txt 白名单 ④README§四 9-11 扩容三律（新款 G<两位>_英文名 落位/根级容量 30·60 阈值触发 CEO 分线分组/一次性件归档 SLA）⑤登记簿§0 新 U 行≤1.2KB 规范。重大根因发现：**Windows PS 5.1 执行无 BOM 的 UTF-8 脚本时按系统码页 GBK 解析中文字面量**（实测复现：'吸嘟嘟'→'鍚稿槦鍢?'）——auto_round.ps1 因此每 10 分钟重建乱码孪生目录+哨兵空转 5 天（ROOT-STRAY 探针首跑即捕获），已改 $PSScriptRoot 自定位+ASCII 化修复并实测复活；serve-warm.ps1 断链（0x80070002）已幂等重建。新律：OS 任务直调脚本必须 ASCII-only 或带 BOM；ASCII 脚本的中文字面量一律外置 UTF-8 数据件（root-manifest 模式）。
- [2026-09-23 14:09:53] MiniGame 命名规范统一已完成（2026-09-23·X747 批·U164 落册·commit 0d041c31 已推 master）：①OS 任务正名 MinigameOllama×2→MiniGameOllama×2（PS5.1 无 Rename-ScheduledTask，用"读定义→新名注册→注销旧名"手工搬迁+X127 查询验证，五处源引用同步）②tools 四连字符件正名（BuildDraftOrder/S3GateSweep_G04/08/13，git mv 保历史）③09号§7 命名总表扩法五行（OS 任务/工具脚本族/证据散件/款内文档/归档件）+存量 grandfather 条款④tools/NameCheck.ps1 执法件（OS 任务名实时审计+法后新增文件 pattern 审计）+Housekeeping 6d 周报接线。命名统一三律：实况优先（法描述实测定态·P 线 6 个带前缀文档引用面实测 40 文件/包=不追杀）、typo 即 bug（大小写错误即刻修+实时审计）、工具族律（PascalCase 禁连字符·变体下划线后缀）。
- [2026-09-23 14:31:46] MiniGame 全面并行启动令已执行（2026-09-23·X751 批·U165 落册·commit 957ef106）：自动化体系全面体检基线=20 任务全绿（18Ready+2Running·零禁用·零滞留锁旗·暂停位空）+持久 cron 双探测在册+GPU 保温线活；当日复活修复三线入账（AutoSentinel 哨兵 5 天空转→14:03 实测产轮、MiniGameOllamaServe 断链重建、auto_round 乱码根因）。**唯一死道=DailyDigest 邮件简报**：smtp.secret.txt 密钥从未配置→2026-09-18"每天 11 点邮件简报"令下从未发出一封（digest-sent.txt 从未存在）；密钥=QQ 邮箱 SMTP 授权码（sjs208@qq.com·smtp.qq.com:587），属 U014 账号物理件——2026-09-23 14:30 用户令「邮件简报先暂停 等我梳理好了再说」：授权码征集撤回，MiniGameDailyDigest 任务已 Disable（U166 暂停令·X753 批），恢复三步见 U166。U165 立两律：自动化全绿基线律（并行启动以体检为前置）、物理件依赖申报律（账号密钥缺失即呈报 CEO 补件·机器禁代办账号域）。
- [2026-09-23 14:31:49] MiniGame 邮件简报暂停令 U166 已执行（2026-09-23·X753 批·commit 38c251b7 已推 master）：OS 任务 MiniGameDailyDigest 已 Disable（日 11:07 触发即停）；暂停≠废除——X056 机制代码全保，恢复=CEO 一句话→三步（配 .codely-cli/mail/smtp.secret.txt 授权码〔U014 物理件〕→Enable-ScheduledTask→当班 -Force 实测试发验证）。**预期噪音声明**：暂停期看门狗 fleet 普查（X091·warn-only·不自动 Enable）每小时记一条 FLEET_WARN MiniGameDailyDigest state=Disabled——这是 CEO 有意暂停，任何会话禁当故障修、禁自愈 Enable。10号§2 通讯行已标⏸暂停中。

### Reference

