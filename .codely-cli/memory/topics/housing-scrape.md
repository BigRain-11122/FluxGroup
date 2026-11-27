# 二手房数据抓取：贝壳 / 我爱我家（2026-11-16 实测，苏州+上海）

工具正身：`Tools/housing/housing.py`（子命令 `login / discover / probe / scrape / csv / dump`）。
产物落 `data/housing/<YYYYMMDD>/`；会话在 `Tools/housing/.state/storage_state.json`（含 cookie，已 gitignore）。

## 一、可达性矩阵（全部来自真跑，不是推测）

| 目标 | 免登录 | 备注 |
|---|---|---|
| 贝壳城市列表 `{su,sh}.ke.com/ershoufang/` | ✅ 200 | 30 条/页，标题/价格/户型/面积/朝向/标签/关注数全在 |
| 贝壳区域筛选页 `/ershoufang/<slug>/` | ❌ 302 → `clogin.ke.com/login` | 登录后 200 |
| 贝壳成交 `/chengjiao/<slug>/` | ❌ 302 → `hip.ke.com/captcha` | 登录后可用 |
| 贝壳小区 `/xiaoqu/` | ❌ 302 → clogin | 登录后可用 |
| 我爱我家 `{sh,sz,bj}.5i5j.com` 列表页 | ❌ 302 → `/user/login/` | 首页可匿名访问 |

**我爱我家城市域名**：苏州 = `sz.5i5j.com`（不是 `su`；`su.5i5j.com` 会跳回北京站）。城市清单：bj/hz/nj/sh/sz/tj/太原…

## 二、两个平台各一处"计数"陷阱

- 苏州类贝壳页有 `h2.total` = 「共找到 14595 套 工业园区二手房」，可直接当板块热度。
- **上海页没有这句文案**（body 只有 ~6.4KB），只能用 `.house-lst-page-box` 的
  `page-data={"totalPage":100,"curPage":1}` 当量级代理（贝壳封顶 100 页 → 下限 3000 套）。
- 上海列表还是 **JS 渲染**：`domcontentloaded` 读完只有 5.7KB 无房源，
  必须 `wait_for_selector("ul.sellListContent")` 才拿得到 30 条。
- 区域/板块作用域：都藏在 `div[data-role="ershoufang"]` 里，且该块内混着地铁线
  （`/ditiefang/…`）。判定区域用 href 严格形态 `^/ershoufang/[a-z0-9]+/?$`；
  板块 = 同块内去掉本城区域 slug 后剩下的项（否则会把户型/朝向/价格区间筛选项误当区域，
  曾一次解析出 69 个"区域"）。

## 三、Playwright 在国内落地的四个坑（都当场踩到）

1. **pip 直连 PyPI 极慢**：6 分钟下不完；改 `-i https://pypi.tuna.tsinghua.edu.cn/simple` 秒装。
2. **`playwright install chromium` 卡死**：它要的 `cdn.playwright.dev/builds/cft/...` 返回 307
   然后挂住。正解 = 从 `https://cdn.npmmirror.com/binaries/chrome-for-testing/<版本>/mac-arm64/chrome-mac-arm64.zip`
   直接下（实测 4.4MB/s），解压后用 `chromium.launch(executable_path=...)` 驱动，
   不必让 playwright 自己管浏览器目录。版本用 `playwright install --dry-run chromium` 查。
3. **headless 默认 UA 会被贝壳判 Forbidden**（页面 title 就是 "Forbidden"，2026 字节）。
   必须显式 `user_agent`（正常 Chrome UA）+ init script 抹掉 `navigator.webdriver`。
4. **后台 shell 任务会被系统停止，并把有头浏览器一起带走**，登录白做。
   正解 = `subprocess.Popen(..., start_new_session=True)` 起独立会话（macOS 没有 `setsid`），
   且登录循环里**每 20 秒增量 `storage_state(path=...)` 落盘**，进程被杀也留得住 cookie。

## 四、登录判定只认行为，不认 cookie 名

`_landed_ok()`：真开一个区域/列表页看落点——URL 里有没有 `clogin` / `captcha` / `/user/login`，
以及 HTML 长度是否达阈值。这比猜 `lianjia_token` 之类的 cookie 名稳，
也自然覆盖了"登录了但还需要多点一次才下发权限"的情况。

## 五、恢复步骤

```
.venv-housing/bin/python -u Tools/housing/housing.py login      # 有头，人工登录（幂等）
.venv-housing/bin/python -u Tools/housing/housing.py discover   # 区域/板块拓扑
.venv-housing/bin/python -u Tools/housing/housing.py probe --districts 3
.venv-housing/bin/python -u Tools/housing/housing.py scrape --top 6 --pages 3
.venv-housing/bin/python -u Tools/housing/housing.py csv
```

截至 2026-11-16 16:32（CEO 令停止）：贝壳苏州已登录、拓扑齐（苏州 10 区 151 板块 / 上海 17 区 234 板块），
探针与挂牌/成交未完成，我爱我家未登录。
