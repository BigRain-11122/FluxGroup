# 设备端（模拟器）登录与采集 — 2026-11-23 实锚合订

> 只收仍然有效的判据与坑；过程叙事看 git log 与 `cph4/fleet/state/android-collect/`。

## 一、B站 App 密码登录被拒（别再重试）

- 服务端 toast 原文：**「用户名或密码错误」**——是凭据错，不是网络/风控话术。
- 实测两个候选都被拒：台账里存的 10 位带尾符号那份，以及去掉尾符号的 9 位那份。
  （密码原文只在 `~/.fluxgroup/bili-accounts.json`，权限 0600、仓库外，**任何仓库文件都不写明文**。）
- 台账 `~/.fluxgroup/bili-accounts.json` 的 password 字段**对 App 无效**；同一账号的网页
  cookie（mid 388497033 / 大喵没鱼吃，2026-11-20 核验）仍有效。
- 结论：**台账密码 ≠ App 可登录密码**。不要再拿台账密码反复试——3 次失败后点「验证登录」
  会直接弹马赛克点选验证码，越试越重。App 端登录取 CEO 口头给的码或走短信。

## 二、验证码 = 设备指纹被识别的证据

- 同样账号在网页端 20 天未被要求验证；在 arm64 模拟器上账号密码失败 3 次即要求点选验证。
- 因此「两实例 `ro.serialno`(EMULATOR37X3X10X0)/`model`(sdk_gphone64_arm64)/`brand`(google)
  完全相同」不是理论风险，是**已在挡登录的真实成本**——P1 指纹改造有实证优先级。

## 三、短信登录可复算路径

首页 →「我的」→「手机号登录/注册」→ 填手机号 → 勾协议 →「验证登录」。

- 协议勾选框**不是 checkable 控件**：是 index=5、text 为空、clickable=true 的
  `android.view.View`（本例 bounds `[19,2020][145,2146]`）。按 text 找会漏。
- 该页「验证登录」在手机号合法（11 位）且协议已勾前是浅色不可点状态。

## 四、设备端抽文本必须按卡片结构配对

- 错法（2026-11-23 实锚）：把 `uiautomator dump` 里所有 text 都收 → 82 条里混进
  「直播/推荐/热门/动画/影视」和「295.1万」「5163」「29:44」。
- 正法：B站 首页是两列卡片，**统计行在标题上方 40–160px、作者在下方 60–200px、同一列**；
  判据 = 标题（len≥8）必须配得到统计行才算一条内容，配不到的自然排除（顶栏横幅/导航）。
- 实测：修后两轮落盘 7 条，全为真标题＋作者＋播放量。
- 修前的脏数据隔离在 `cph4/fleet/social/raw/_quarantine/bilibili.feed.jsonl.bad-20261123`。

## 五、两条会白烧一轮的工具坑

1. **软键盘打开时 `input tap` 的坐标落在键盘上**（本例想点 y=2083 的协议框，实际敲到数字键，
   把手机号打成 12 位）。要操作页面下半部控件，必须先 `keyevent 4` 收键盘再算坐标。
2. **验证输入长度要用 `len(预期串)`，不要数掩码点数**。我把 9 位的密码当成 8 位，
   于是每轮都在"纠正"一个本来正确的输入，白烧一轮并误导了归因。

## 六、凭据库与网页登录态（2026-11-23 补）

- **本仓库在 GitHub 上是 Public**（页面标题 + `Public` 徽章实测；未认证 API 返 403 属限流，不能据此判私有）。
  ⇒ 明文凭据/私密资料一律不入库；凭据只落 `~/.fluxgroup/credentials/vault.json`（目录 700、文件 600）。
- 凭据库工具 `Tools/fleet/cred_vault.py`：`add/list/get/mark/import-legacy/doctor`。
  写入前校验路径不在仓库内（负控已验：仓库内文件判 True、凭据库判 False）；`list` 只出掩码。
  除手机号密码外，每个账号记**各通道实测状态**（device_login / web_session = ok|rejected|needs_human）。
- **登录态判据坑**：`~/.fluxgroup/<platform>-state.json` 的 `isLogin` 可能是旧快照。
  实锚：`bilibili-state.json` 判 isLogin=False，但同一时刻真实浏览器里 acct1/acct3 都在跑、
  `social_health` 的 today.need_login=0。真实登录态看三处：①`ps` 里正在跑的 `--user-data-dir`
  ②`social_health.py --json` 的 need_login ③用该 profile 开无头页查平台自己的登录 cookie。
- 登录 cookie 判据：bilibili=`SESSDATA`+`bili_jct`；xiaohongshu=`web_session`；zhihu=`z_c0`；
  公众号=`slave_sid|bizuin`；抖音=`sessionid|sessionid_ss`；微博=`SUB`。
- 登录通道 `Tools/fleet/login_pass.py`：`check` 无头实测六平台；`login` 有头依次弹窗，
  检测到登录 cookie 即 `ctx.storage_state()` 落到 0600 状态文件并回写凭据库 web_session=ok。
- **公众号不要走扫码**：后台登录约 4h 过期，扫一次 4h 后又要扫，违背"别来烦我"。
  正法=AppID+AppSecret 走官方接口（后台配 IP 白名单），一次性配置换永久可用。
- 2026-11-23 晚实况：B站网页 acct1/acct3 活跃；小红书 web_session 有效；
  知乎、公众号未登录；抖音/微博无 profile；B站 App（模拟器）仍需一次人工（点选码+短信码）。
