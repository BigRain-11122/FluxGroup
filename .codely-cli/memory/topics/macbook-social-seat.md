# MacBook 养号工位 · 全盘实盘与判据（2026-11-26 实测）

> 装载面：这台机器的角色、5 条链结构、三个系统性缺口、真实并行上限。
> 数字均为 2026-11-26 11:2x–11:5x 实测，过期就地复测，不外推。

## 一、角色定谳

MacBook = **养号工位**（不是主控）。主控脉冲 `com.fluxgroup.pulse` 与一屏 `com.fluxgroup.console`
已按 CEO 2026-11-20 令停用，plist 在 `~/Library/LaunchAgents/disabled/20261120-ceo-stop/`。

账号 8 个（`cph4/fleet/social/ACCOUNTS-REGISTRY-v1.json`）：
- 在养 B站 2 个：bili-1「大喵没鱼吃」（9/天）、bili-2「许大喵去喵星」（8/天）→ 合计 17 条/天配额
- 起号 1 个：gzh-1 公众号（0.4/天，每周 2-3 篇）
- 只读采号 5 个：头条/车家号/知乎/小红书/抖音（read-only，不动账号，守 CEO「不做群控」令）

判据只有三条：号有没有变大 / 像不像真人 / 料够不够它自己长。目前只做到第二条的一半。

## 二、5 条链（23 个常驻作业）

1. **主环（对外）**：agent-acct1(60s)、agent-acct3(60s)、browserd、practicetick(30m)、practice10、
   replytick(15m)、socialloop(5m)、socialhealth(10m)
2. **马达一 供料**：sociallearn(20m,2并发)、gzhloop(30m)、selfgen(6h)、corpusbake(30m,7 worker)
3. **马达二 练模型**：trainloop(5m)、trainpipeline(15m)、qualityagent(15m)、socialaudit(6h)
4. **观测**：loopreg(30m, 12 段回归)
5. **服务**：ollamamodel、llmgateway、mlxlora(8788)、modelqueue、resalloc

## 三、三个系统性缺口

### 1. 结果没有仪器（最严重）
- `Tools/fleet/own_videos.py` 是唯一能取播放量的工具，实测可用：mid=388497033，25 条作品，最高 2.1 万播放。
- 三个坏点：①没接进任何常驻作业；②字段解析坏——title 写成 `3156006:45`（播放数+时长粘连），
  取到数但不可用；③裸 `python3` 跑必 `ModuleNotFoundError: playwright`，只有 `.venv-housing/bin/python` 能跑。
- 后果：12 段回归全是过程量，没有一段是结果量。**整台机器是开环的。**
- 正法：修字段 → 接 30 分钟常驻 → 立第 13 段回归（播放/粉丝/回评三条曲线，日环比 0 且无解释即红）。

### 2. 内存越界（违反 CEO「不触发 swap」令）
- `sysctl vm.swapusage`：total 5.12G / used **4.49G**。
- 常驻占用：ollama 4b-mlx 3.4G + ollama 2b 2.7G + 本 Cowork 会话 ≈2.4G + Chrome for Testing 0.9G + WebKit 1.6G。
- 结论：并行的上限是内存不是调度，再加任何东西都是拿 swap 换。
- 还款：2B 改按需拉起（腾 2.7G），只留 4B 常驻；烘焙 7 worker 与实战错开。

### 3. 供给抢实战
- profile 让路比：acct1 让路 105 / 开场 267；acct3 让路 76 / 开场 214；最近 200 行日志 61 次让路，
  原因均为「profile 在采集手里」。
- 配比荒：配额 17 条/天，今日实发 **1 条**（11 小时前），利用率 6%；采集入料 1153 条。
- 正法：实战优先、采集让路；采集只在实战窗口外跑。

### 附带：训练在退化，不是偶发
- 今日 9 轮：留 2 否 7（留率 22%）；全期 127 轮留 51（40%）。
- 失败形态统一是「候选分低于基座」：peer_pro 基座 51.8→候选 41.6、feeler 56.5→47.9、craft_learner 85.5→78.0。
- 正法：连 3 轮 REJECT 自动停、转人工查配方，不许继续烧。

## 四、真实并行上限

- 可持续：1 个实战会话 + 1 个采集（不同 profile）+ 4B 常驻。就这一套。
- 不可并行：两个号的「动手」（同 IP 最强关联）／训练与实战（rollback 打断）／7 worker 烘焙与实战（内存）。

## 五、仓况（这台机器同时是代码主本）

- `git fetch` 后实测：本地领先 origin/main **524** 条、落后 **63** 条。不推＝等冲。
- 待 CEO 一句：两个号的目标是「像真人活着」还是「涨到某个数」（粉丝过千／单条过万）。
  答"活着"→只修闭环不设增长指标；答"要涨"→增长曲线升为第一考核，其他让路。
