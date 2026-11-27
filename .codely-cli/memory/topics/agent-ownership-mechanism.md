# 智能体负责制：失败语义与复算判据（2026-11-19 实锚）

CEO 令「智能体给我负责起来」后的落地形态。核心：**责任要能被审计，失败要能被区分，被让路不能变成常绿。**

## 一、责任落点（机读，不靠报告口述）

- 每个周期任务在 `cph4/fleet/social/SOCIAL-AUTOMATION-MATRIX-v1.json` 里必须有：
  `owner`（席）/ `retry`{max_attempts, backoff_s} / `blocked_rc` / `event_driven` / `evidence_paths` / `ok_rc`。
- 监控屏 `social_agent_monitor.py` 读这些字段并在板上显示负责人；**未指派 → 判负**（板上单列一段）。
- 主控自身另有 36 项职责账：`MASTER-DUTIES-v3.json` + `duties_audit.py`（executor + evidence + 周期三倍内）。

## 二、失败语义三分（本轮新增）

| 语义 | 码 | 板上 | 处置 |
|---|---|---|---|
| 成功 | 0 | OK | — |
| **被让路**（同 profile 被占、训练在跑） | blocked_rc（如 3） | BLOCKED / amber | 不重试，下轮再来 |
| 真失败 | 其它非 ok_rc | FAIL / red | `retry` 当场重试，仍失败才记红 |

铁律：**BLOCKED 不是免死金牌**——连续被让路且产出超周期 3 倍，仍判 STALE/red，否则"一直被挡住"会洗成常绿。

## 三、事件驱动任务不能用 mtime 判红

threads_tick 挂了 49 小时假红：它是"结算会话"任务，没有会话就没有新事件，产出文件当然不涨。
正法=任务声明 `event_driven: true`，判据改成"跑了且 rc 正常"，说明里写清"本次 0 条待处理"。
反例警戒：不要为了让它绿而去 touch 一个心跳文件——那正是"心跳冒充产出"。

## 四、本轮抓到的三只假绿（可直接套用）

1. **`except: continue` 吞异常**：采集起 profile 失败时只留一句"可能被别的浏览器进程占用"，
   排查两小时查不出根因。正法=把每个候选 profile 的 `类型: 首行错误` 收集起来一起抛。
2. **字符串排序选"最新"**：`latest_run()` 用 `sorted()`，`CMP-204622-500` 排在 `2026...` 之后，
   于是选到没有 adapter 的临时目录、对拍没跑，却打印"全流程完成"。
   正法=只认 `<日期-时间>` 命名 + 必须有权重文件 + 按 mtime 取最新；对拍失败直接 rc=1，不许报完成。
3. **周期过长把瞬时故障变成长期红**：周训被并发事故 TERM 一次就红一周。
   正法=500 步 + 三闸的今天，节拍改日训；一次失败次日自然重来。

## 五、并发采集的 profile 锁

同一 user_data_dir 两开必失败。`social_collect._acquire_profile_lock`：锁文件只记 pid，
进程活着＝占用中（后来者排队等，`FLUX_PROFILE_WAIT` 默认 180s），进程不在＝残留可接管（无需手工清理）。
负控：伪造占用 → 必须打印"等锁超时（别的采集进程占着 profile）"而不是笼统的"可能被占用"。

## 六、验证基线（同日）

- 职责审计：36 项 / OK 35 / IDLE 1 / STALE 0（F04 存储分级由真跑 `storage_curator.py` 刷新，未放宽阈值）。
- 养号板：9 项 / 8 OK；唯一红是 train_weekly 的旧失败记录，按纪律不抹。
- 全量回归：57 项 / 过 56（唯一红=fleet_doc 文档漂移，属另一条线）。
- 提交：`c6a78de10`（负责制机制）、`f52339a11`（周训改日训）。

## 七、已知缺口

launchd 常驻进程（pulse/console/mlxlora/modelqueue/corpusbake/practice10/practicetick/trainlock/traindone/acceptrun）
到席位的映射目前只写在报告里，**尚未机读**——这是下一步要补的账。


## 2026-11-19 智能体负责制三条判据（L1 迁入原文）
[2026-11-19 20:03:19] 智能体负责制的三条可复用判据（2026-11-19 实锚）：①责任必须机读——每任务带 owner/retry/blocked_rc/event_driven，未指派判负；②失败三分：成功0 / 被让路(blocked_rc，amber，下轮再来) / 真失败(当场重试后再红)，但"连续被让路+产出超周期3倍"仍判红，BLOCKED 不许当免死金牌；③事件驱动任务（如会话结算）不能用产物 mtime 判 STALE，否则永远红，判据改"跑了且 rc 正常"且不许 touch 心跳文件。另两坑：`except: continue` 吞掉 profile 启动异常会让日志只剩"可能被占用"；`latest_run()` 用字符串排序会被 `CMP-` 前缀污染，选到无权重目录而对拍没跑却报"全流程完成"。全文=`.codely-cli/memory/topics/agent-ownership-mechanism.md`。
