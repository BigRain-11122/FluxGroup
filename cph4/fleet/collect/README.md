# 采集线（COLLECT）：三条通道，按平台选，不按习惯选

> 2026-11-25 立。CEO 令：「你采集的不止公众号哦」「采集也要去 GitHub 找技能和工具」。
> 上游调研与许可裁决见 `UPSTREAM-HARVEST-v1.json`（含拒绝项，别重复调研）。

## 先读这一句
**换一个站 = 给一个域名，不是写一个解析器。** 手写解析器的站一改版就死——
2026-11-25 盘点：59 条源里 21 条 degraded、8 条 dead，几乎全是手写解析器熬死的。

## 三条通道

| 通道 | 工具 | 适用 | 代价 | 现状 |
|---|---|---|---|---|
| A 公众号原文 | `Tools/fleet/wechat_article.py` | 已有文章链接的公众号 | 要浏览器；发现通道全封 | 可用（受浏览器时段租约） |
| B 公众号订阅 | `Tools/fleet/harvest_weread.py` | 想持续跟的几个对标号 | 要人贴一次微信读书 Cookie | **等凭据** |
| C 任何站点 | `Tools/fleet/harvest_generic.py` | 专业站/官网/科学站/垂类媒体 | 无（纯 HTTP） | 可用 |

## A：公众号原文（浏览器）
- 抓谁：池里的 `mp.weixin.qq.com` 与车家号镜像链接。
- 硬约束：单拍 540 秒预算、尝试上限、死链 2 次进黑名单；静态垂类源一律跳过（`STATIC_HOSTS`）。
- 别指望它自己找料：搜狗微信第 1 页就验证码，必应 `site:` 返回 0 条。

## B：公众号订阅（微信读书）
- 机制：`/api/mp/cover?bookId=` 取最新一篇 → `/web/mp/content?reviewId=` 取正文。
- **能力边界**：只拿最新一篇，历史补不回来（旧列表接口已废弃，恒 -2041）。
  所以它解决「往后每篇自动进语料」，不解决「补 200 篇差额」。
- 要人做两件：①浏览器登录 weread.qq.com 复制 Cookie → `~/.fluxgroup/weread-cookie.txt`；
  ②在微信读书里订阅对标号 → 把 bookId 写进 `~/.fluxgroup/weread-books.json`。
- 失效表现：返回 `-2012`/`-2041` → 脚本判 `AuthError` 并停手（退 5），不重试、不静默。

## C：任何站点（通用）
```bash
.venv-housing/bin/python Tools/fleet/harvest_generic.py --probe https://example.com/   # 先探活
.venv-housing/bin/python Tools/fleet/harvest_generic.py --feed    https://sspai.com/   # 自动找 feed
.venv-housing/bin/python Tools/fleet/harvest_generic.py --list    https://www.stats.gov.cn/sj/zxfb/
.venv-housing/bin/python Tools/fleet/harvest_generic.py --sitemap https://www.miit.gov.cn/
.venv-housing/bin/python Tools/fleet/harvest_generic.py --url     <一篇文章>
.venv-housing/bin/python Tools/fleet/harvest_generic.py --seeds   list.txt --limit 20
```
- 探活先跑，`verdict` 五档任选其一：
  `feed`（有 RSS）｜`sitemap`｜`list`（列表页，官方站最常见）｜`article`（页面本身就是文章）｜不可采。
- 实测（2026-11-25）：
  - 少数派 `--feed` → 3 篇 / 平均 4176 字 / 0 失败
  - 国家统计局 `--list` → 7 篇 / 平均 1838 字（官方一手数据）
  - 第一电动单篇 8549 字；懂车帝与易车首页 0 字 → 判不可采（JS 壳，无 feed 无 sitemap）
- 两个实测踩到的坑（已修 + 有负控）：
  - `gtj2023_base.css` 里的 2023 是 4 位数字，被当成文章链接，一次抓 9 条 CSS 全失败 → 按静态资源后缀排除；
  - 统计局把标题写在 JS 里（`var title1 = '...'`），元数据抽取把代码当标题入库 → 出关键字就回退 `<title>` 并剥站名尾巴。
- 输出：`cph4/fleet/collect/ARTICLES-GENERIC.jsonl`（`genre=unspecified`，默认不进文笔训练）。

## 口径（三条通道共用一句）
- 语料分两类：**风格语料**（公众号/车家号，能进文笔训练）与**产业语料**（垂类/通用，只做形态与事实）。
- 两本账分开数；混着数会造出假待办（实锚：71 条已采完的链接被当待抓，一次跑爆 900 秒）。
- 许可先于功能：非商业 / NOASSERTION / 禁止大规模抓取的一律不装（MediaCrawler 就是这样被否的）。

## 依赖
- `trafilatura`（Apache-2.0，2.4.0）**只在 `.venv-housing` 里**，系统 python 没有。
  所以通用采集器与微信读书客户端都要用 `.venv-housing/bin/python` 跑。
