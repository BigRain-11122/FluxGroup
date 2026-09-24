# R-20260924-silicon-watch —— 硅基生命元宇宙窗·真链接架构案 v1（CPH4 Labs 规划件）

> 溯源=CEO 令 2026-09-24 ~16:45「`gaming/MiniGame/硅基生命元宇宙.html` 是我的唯一指定整体可视化观测窗口，其他都给我暂停了，然后你可以规划迭代这个，这个可视化方向我是认可的」+~16:50「这个只是整个硅基城市的运转监视窗口，让我 CEO 一目了然，但硅基城市真正的建设要持续！我可以通过这个窗口去看。你好好研究下这个可视窗口，和城市，集团，子公司，集群等，真正链接起来，能看到及时的可信的信息」。台账=ledger P-2026-09-24-59。

## 一、定位三分（令义裁定）

**窗=监视层（唯一）·城=建设本体（照建不停·P0 倾斜令不变）·面板=数据面（保留维护·不再作独立观测入口）**。暂停面=CityWatch 观城台+BigMoney 三面板（bigmoney/town/dashboard.html）+PixelTownBoard（U175 已停役确认）——零计划任务变更（全部为按需件·停役=正典+入口动作）；FluxVerse 引擎城与其内景窗机制=城建本体**不在暂停面**。

## 二、现件体检（读件实证·26707B）

1. **数据 100% 写死**：CEO 队列/六司卡/里程碑/机队/天气全为 JS 常量；页脚宣称「数据实时取自机器心跳和自动化快照」=**不实宣称**（诚实律红灯·首修项）。
2. **队列三过期实锤**：19.9 已锁价（委托决策令 v2）/商业化总管已定指算力司（13:15 位阶令）/荣誉市民三席已点（大圣/Qiqi/Rain·16:20+勘误令）——仍列为待拍板。
3. **里程碑失真**：写死 M1=done/M1.5=done vs 正典 `watch/milestones.json` M1=building/M1.5=partial（M2=next）。
4. **方向认可保留**：视觉/布局/中文叙事/CEO 视角设计零改——只重建数据层。

## 三、真链接架构（三件套·MiniGame 仓·维护面=HQ 观测线·权源=CEO 直令）

| 件 | 角色 |
|---|---|
| `硅基生命元宇宙.html` | 展示层：消费 `window.SILICON_DATA`；加 10min 页面自刷新+数据缺失横幅+每块源戳；中文 UTF-8 展示件 |
| `硅基生命元宇宙-data.js` | 数据层（生成物）：全部块数据+每块 `src`+`ts`+新鲜度 |
| `tools/siliconwatch/generate.ps1` | 生成器：L1 确定性零 LLM·**纯 ASCII 码体**（编码律）；循环 SiliconWatchTick 10min 静默（MiniGame InvisibleRunner.vbs U060 范式） |
| `tools/siliconwatch/strings.json` | 策展层（UTF-8）：公司叙事卡/部门文案/云端+笔记本静态卡/CEO 队列——唯一人工维护面·带快照日期戳 |

## 四、数据源接线表（块→实盘源→规则）

| 块 | 源（实测在盘） | 规则 |
|---|---|---|
| 顶栏统计 | 公司数=6（strings 校验 BRAND §8）；游戏=18（Phase1 策展）；居民=`life/BigLife/census/export/citizens-light.jsonl` 行数（实测 10003）；机器=心跳 5+静态 2 | 全派生禁写死 |
| 天气 | 上海=`gaming/FluxVerse/world/world-state.json` reality（探针 10min·temp/kind/wind 实证 28℃/cloud/11.1）；苏州=生成器 Open-Meteo 直取（零 key·30min 缓存·超时 10s） | 断网=上次值+陈旧标 |
| 里程碑 | `gaming/FluxVerse/watch/milestones.json` 直读 | M1=building 如实 |
| CEO 队列 | strings.json 策展（HQ 维护）+夜轮对账步（与 orders.md 对账·已拍板项剔除） | 剔除三过期项起版 |
| 机队 | MiniGame `Design/configs/GLOBAL/fleet/{a,b,c}.json`（A=bm-a 详情/GPU 栈/进程清单·b=BG-B·c=BG-C）+BigMoney `fleet/machines/bm-{a,b,c}.json`（current_task/负载实值） | badge 派生律：心跳>30min=断（黑灯区律同源）/GPU util>80% 或 ram_free<15%=忙/batchmode>0=干重活/否则有空；显示 verdict_line 原文=原始证据 |
| 六司卡 badge | 各仓 `git log -1` 派生：最近 commit<90min=在转/<24h=待命/>24h=静默（F3 派生律·禁写死） | 部门文案=策展层带快照戳（Phase2 各司状态导出·见§六） |
| 页脚 | 生成时间戳+各源新鲜度一行 | 移除不实宣称 |

**红线继承**：敏感面律（world-state 的 market/fx 字段**刻意不消费**·禁行情汇率入界面）/静默律/诚实律（每数字带源戳）/2D/零服务器（纯本地文件+file:// 直开）。

## 五、入口与分发

- bm-a 桌面：`超体宇宙城.lnk` 改指本窗（生成器先刷后开·或直开+后台 10min 刷）。
- BG-B/C：随 MiniGame 既有 pull **零新部署**（P-26 观城台分发批改道）；bm-b/bm-c：fleet 令发三件套（<100KB·inbox/croc）。

## 六、迭代路线（批）

- **批1（本批·HQ 施工）**：三件套+调度+入口+暂停落法。判据=①断数据横幅可见②每块源戳+新鲜度③里程碑如实④队列无已拍板项⑤双司机队 5 卡实值+断跳卡灰显⑥无头 Edge 截图多模态验图绿。
- **批2（接线深化·转办）**：各司状态导出规范（一行 JSON：部门状态+产出计数·六司自报）替代策展层；CEO 队列自动对账；城市活动块（world-state zones/flows/residents 消费·黑灯区律视觉自证）。
- **批3（体验）**：城 Canvas 鸟瞰引入窗内（可选·FluxVerse 探针数据复用）·参观端脱敏版随 M4。

## 七、派工（P-59 转办面）

①@HQ 承建窗=批1 施工（CEO 直令权源·Biggame 侧仓内 commit 可见勿双改）；②@Biggame=Phase2 组合登记簿→18 款 chips 导出+BG-B/C pull 即得；③@FluxVerse-DevLoop=CityWatch 停役注记+P-26 改道；④@BigMoney=三面板停役注记（数据面保留）。
