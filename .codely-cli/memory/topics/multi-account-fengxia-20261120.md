# 多号养号与风控（2026-11-20 立）

## 一、账号事实（先看这条，别搞错）

- CEO 2026-11-20 给的第二个号（手机号 18068440109）**与现有号是同一个 mid=388497033、昵称「大喵没鱼吃」**。
  → 目前**只有一个真实账号**；`acct1`（主 profile）与 `acct2`（备用 profile）指向同一账号。
- 因此"两个号同时养"当前不成立；要真的有第二个号，必须换一个**不同 mid** 的账号。
- 加号流程（密码永不进代码/日志/git）：
  1. `python3 Tools/fleet/bili_login.py --new acct3`（登记 + 建独立 profile，不登录）
  2. `python3 Tools/fleet/bili_login.py --account acct3`（开有头浏览器，**人工点完**，脚本只核验）
  3. `--check` 只核验不开窗口
  凭据只落 `~/.fluxgroup/bili-accounts.json`（0600、仓库外）。

## 二、四条防关联规则（已在代码）

| 规则 | 实现 | 为什么 |
|---|---|---|
| 不同时动手 | `cross_gap_ok()` 两号动作错开 ≥10 分钟 | 同 IP 同时活跃是典型关联特征 |
| 不碰同一条视频 | `video_owned_by_other()` 互动级互斥（看可以看） | 两号在同一视频下同时出现最容易被串起来 |
| 同号只一场 | `_mid_lock()` 按 mid 单实例锁 | 两 profile 同 mid 也不许并行 |
| 每场只像一个号 | `pick_account()` 选"今天跑得最少"的号 | 两号都养，但一次只动一个 |

**关键教训**：同一个 mid 在两个 profile 间轮转 = **自造两套设备指纹**，比单 profile 更像"多设备同号"。
所以同一 mid 只保留一个 primary profile，其余降为备用（只在主 profile 损坏时切）。

## 三、动作配额（比平台限流更保守）

- 评论 3/天、弹幕 5/天、点赞 20/天（账号级，落 `USER-AGENT-LEDGER`）。
- 重复内容闸：同账号 7 天内 6-gram 重合 ≥60% 判重——"重复的内容"是官方明写的折叠原因。
- 刷脸上限：同一 UP 主 7 天 ≤2 次。

## 四、登录态：登一次，长期复用

- 登录态存在浏览器 profile（每号固定目录），**不要求重复登录**。
- 每场开头轻量核验 `bili_jct` + `nav.isLogin`（`user_agent.login_state()`）；
  失效只记 `NEED-LOGIN`、本轮**只看不动手**，不开窗口反复试。
- 为什么不先核验就动作：登录失效会表现为"点赞全失败/弹幕发不出/评论被吞"，
  很容易被误判成账号被限流，进而触发错误的止损。

## 五、踩过的坑

- 新号第一次用：profile 目录不存在 → profile 锁文件写不进去（FileNotFoundError）。
  正法=`social_comment._launch` 里先 `os.makedirs(PROF)` 再上锁。
- 账号表里混入说明字段（字符串）会让"遍历账号"崩（AttributeError）；
  遍历时必须过滤 `isinstance(v, dict) and v.get("mid")`。

## 六、调度口径

- 已停 `com.fluxgroup.practicetick`（300s 一拍、每拍试图发一稿＝队列思维）。
- 改 `com.fluxgroup.usersession`（600s）→ `user_agent.py --session`：在会话窗口内且本窗口没跑过，
  才开一场；一场内"浏览→偶尔赞→偶尔弹幕→极偶尔评论"，跑完即退。

## 七、两个号 = 两个 24h 智能体（2026-11-20 立）

- `Tools/fleet/agent_daemon.py --account <alias>`：**一进程只养一个号**，按该号人设活跃时段开窗，
  场间随机歇 15–60 分钟，2–6 点不活动，异常不退出（记一笔继续）。
- 常驻：`com.fluxgroup.agent-acct1` / `com.fluxgroup.agent-acct3`（KeepAlive，崩了自动重启）。
- 并行的边界（CEO 要"能并行就并行"，但风控仍要守）：
  **浏览可并行**（不同 profile、不同视频）；**动手不碰同一条视频**（`video_owned_by_other`）。
  10 分钟时间硬错峰**已撤**——两个号是兴趣不同的人，靠话题隔离足够，排班式错峰反而不像人。
- 账号强制：`FLUX_ACCOUNT=<alias>`；`pick_account(force_alias)` 支持只取指定号。
- 停掉的重复调度：`usersession`/`social24x7`/`socialagentday`（与双智能体重复，会抢浏览器锁与配额）。

## 八、"像两个人"的可执行判据（2026-11-20）

| 维度 | 老号 acct1 | 新号 acct3 |
|---|---|---|
| 人群段 | peer_pro（从业者） | shallow（泛娱乐） |
| 领域 | 自媒体/AI/短剧漫剧/数码科技 | 游戏/人工智能/AI影视/娱乐 |
| 弹幕风格 | point：点评手法/卡点/想试 | feel：心里一动/看了两遍/戳到 |
| 字数 | 12–35 | 8–25 |
| 时段 | 10/12/16/21 | 9/13/20/23 |
| 配额 | 评论8/弹幕20/赞50 | 评论5/弹幕14/赞40 |

- **两号绝不许共用弹幕模板**——共用模板是"一个人开两个号"的最大破绽。
- 同场句式去重（用满一轮再重置）；关键词兜底取**最长中文片段**（"电影最TOP生化危机"→"生化危机"），
  纯数字/纯英文标题不发（自检里有一条负控守它）。

## 九、运维坑（2026-11-20 夜）

- 手动跑 `--session` 会与智能体抢 profile 锁 → 已改为"profile 被占用=记 `profile_busy` 让路"，
  不抛栈、不打红；**日常不要再手动跑非 dry 会话**。
- 崩溃的 playwright 会留下整棵 Chromium 进程树占着 profile（实测 7 个进程），
  需 `pkill -f "user-data-dir=.*browser-bilibili"` 清理并删死锁文件。
- 训练必须接电（电池+低功耗 18.6s/步 vs 接电 ~5s/步）；卸掉闲置 ollama 模型后 swap 从 3.5GB 降到 1.84GB 且不涨。
