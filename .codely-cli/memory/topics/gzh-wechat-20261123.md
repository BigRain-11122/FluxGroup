# 汽车类公众号线（采集/训练/养号）2026-11-23 立

> 正身计划＝`cph4/fleet/social/GZH-PLAN-v1.md`（10 张任务卡）；候选号＝`GZH-ACCOUNTS.json`；
> 采集器＝`Tools/fleet/wechat_article.py`；语料＝`cph4/fleet/social/gzh/*.jsonl`（已 gitignore）。

## 一、CEO 定案（2026-11-23）

1. **定位＝新能源/智能驾驶「选购 + 避坑」**，面向 25-40 岁准备换车的人。
2. **口吻＝主理人第一人称、有立场**：正文陈述事实，结论段必须给明确建议。
   代价：涉及具体车型的负面结论必须有可引用依据（配置表/实测/官方数据），拿不到就只写结论不写原因。
3. 号名单＝我先调研候选、CEO 圈。
4. **先做大量训练**（他的原话），所以先堆语料再谈模型。

## 二、平台硬事实（实测，别再试错）

| 事实 | 含义 |
|---|---|
| 服务端/无头请求 `mp.weixin.qq.com` → **"环境异常，完成验证后即可继续访问"** | 云端抓、urllib、headless 一律无效 |
| 本机真 Chrome（住宅 IP）→ 可读，**3.0 秒/篇** | 采集只能走本机浏览器 |
| 网页版**不显示阅读数/点赞/在看** | 判据只能用结构代理（标题类型/开头承诺/小标题/结尾动作/同题对比/盲评），**不许估数据** |
| 搜狗微信搜索 `weixin.sogou.com` → **第 1 页就验证码** | 不能作为建池主路 |
| 公众号无公开文章列表接口；历史页要微信客户端 | "大量采集"的真瓶颈是**先有 URL**，不是抓取 |

## 三、采集器能力（已跑通）

`wechat_article.py`：`--url` 单篇 / `--harvest N` 批量 / `--self-test`（6 条，含去重与空结构）。
落字段＝title / account / publish_ts / words / paras / imgs / heads / lead / text / url / _uid / fetched_at。
实测：单篇 3.0 秒；批量 4 篇→入库 3 篇（1 篇被公众号折叠判空）。
**架构决定**：采集器自己起 `~/.fluxgroup/browser-gzh` 独立 profile，**不碰养号线的共享浏览器**。

## 四、把新动作塞进共享 browserd 会把它整个卡死（重要教训）

现象：给 `browser_daemon.py` 加 `article`/`serp` 动作后，一次异常页面导航让整个守护进程
不再响应——后续 `nav` 连续 25/30/40 秒超时，日志只有重复的 "listening"，看不出错。
影响面：B 站养号线的浏览/发帖也走这个身体，等于全线停摆。

根因两条：
1. `browserd` 是**单线程** `HTTPServer`：任何一次长导航/goto 卡住，后面所有请求永久排队；
2. `pkill -f 'chrome-mac-arm64'` **匹配不到**真实进程名，11 个 chrome 残留继续占着 profile，
   于是重启后 `launch_persistent_context` 一直等锁 → 看起来"服务起了但不回话"。

恢复配方（已验证，`nav` 恢复到 2.6 秒、登录态完好）：
1. `launchctl bootout gui/$(id -u)/com.fluxgroup.browserd`
2. `pkill -9 -f 'Chrome for Testing'`（**这个 pattern 才对**）
3. 清 `~/.fluxgroup/browser-*/Singleton*` 与 `DevToolsActivePort`
4. `launchctl bootstrap …` 后等 30-35 秒（冷启动），再探 `nav`

架构结论：**公共服务只服务它自己的业务**；新业务的长任务另起独立 profile/进程，
不要往共享单线程服务里堆。

## 五、当前卡点与下一步

卡点：**没有 URL 可抓**（搜狗被拦、必应会把共享浏览器拖死、历史页要客户端）。
两条解法：①CEO 给号/链接（最快，1 篇也能从"相关阅读"滚出一批）②我去验聚合源（新榜/清博付费，免费镜像多失效）。

节奏：200 篇 → 标题模型（同题 20 变体）+ 开头 300 字模型；1000 篇以上 → 才谈全篇结构。
模型分工：标题/摘要 4B、开头 9B、正文交云。
