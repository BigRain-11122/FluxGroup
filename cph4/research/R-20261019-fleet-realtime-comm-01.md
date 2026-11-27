# R-20261019-fleet-realtime-comm-01 — 机队毫秒级实时通信与信息同步选型+实测（CEO 令 2026-10-19）
> 溯源：CEO 直令 2026-10-19「去调研机队间如何建立实时快速的通信，去查github，我要不受限制的毫秒级的通信和同步信息，git只是云端备份！」·消费方=机队通信线改造（fleet-link/poke/dispatcher/idle-watch 全消费面）·判据预注册=①三机 Windows 高星轮子选型（毫秒级+自托管零配额+状态同步）②本机实测延迟数③git 降级备份面双轨方案
> 验证声明：实读 13 源（A=10：10 张 GitHub 仓页 HTML 直读〔星数/许可〕；B=2：本机 nats bench 实测+tailscale netcheck/ping 诊断；C=1：nats.io 文档页定性 high-performance）·失败面=GitHub MCP token 401（12 调用全亡·物理件登记）·api.github.com 匿名配额 403·releases/latest/download 固定资产名 404（资产带版本号·已改 HTML 解析）·nats.io/about 无具体延迟数值（由本机实测补位）

## 一、现状病根（git 被当通信线用）
- 现行=双通道：poke（HTTP 8790 唤醒+git pull·亚秒 ack）+数据面 git fetch/push 周期（分钟级）；「signals only, data stays in git」=现行法锚（fleet-nodes.json/worker 头注）
- 病：git=版本控制非通信系统——分钟级周期/index.lock 竞态/陈旧面误报（SYNCED 空真判例 10-17）/心跳新鲜度靠远端 blob 读/5min 新频次下轮询 churn 更重（10-19 提速令对照）
- CEO 令语义：数据面脱离 git→毫秒级总线；git 降级=云端备份+审计史

## 二、选型矩阵（星数=2026-10-19 github.com HTML 直读·三查=星级/许可/活跃）
| 轮子 | 星数 | Windows | 持久化/KV | 判 |
|---|---|---|---|---|
| nats-io/nats-server | 20.9k | ✅ 原生单 exe（Go） | JetStream 流+KV+对象桶（文件持久化·本机实测） | **选定** |
| nsqio/nsq | 25.8k | Go（今日 release 未验=待证） | 磁盘队列·无 KV/无请求应答 | 3 组件重 |
| etcd-io/etcd | 52.4k | 非官方 | KV+watch（共识库非总线） | 错配 |
| redis/redis | 76.6k | 官方无 Win（B级） | 强 | Windows 面死 |
| emqx/emqx | 16.8k | Docker/Linux（B级） | 强 | 非原生死 |
| eclipse/mosquitto | 11.3k | 官方 Win 件 | retained+QoS·无 KV/watch | 轻备选 |
| zeromq/libzmq | 11.0k | 库（NetMQ 绑定） | 无持久化无发现 | 兜底 |
| syncthing/syncthing | 89.4k | 原生 | 文件同步·秒级 | 非 ms 通信 |
| winsw/winsw | 14.3k（MIT） | 服务化包装器 | — | 部署件✅ |
- NATS 胜出理由：单 exe ~15MB·常驻 28.3MB RAM 实测（零 GPU·不触让路律）·pub/sub+请求应答（poke 正身）+KV watch（状态同步正身）+JetStream（命令/事件史持久化）一套全占·nats.exe CLI 全功能（pub/sub/kv/bench/监控）PS5.1 直调零依赖·Apache-2.0·今日最新 v2.15.1 官方 Windows 件（下载 13.2s）·natscli 官方 README bench=1.17M msgs/s（A 级）

## 三、实测证据（本机 bm-a 2026-10-19 11:5x·nats-server v2.15.1/nats v0.5.0·件留 %TEMP%\nats-pilot）
- 请求应答往返 2000 次：**avg 0.11ms**（max 0.78ms·P99 0.54ms·8,854 条/s）——poke 类命令链毫秒级实证
- KV put 1000 次（JetStream 文件持久化）：**avg 0.068ms**（14,523 ops/s）；KV get：**avg 0.060ms**（16,378 ops/s）——状态同步毫秒级实证·KV 桶跨重启保留实测（文件持久化）
- 服务端 RAM=28.3MB（JetStream 开）；JetStream 默认开启零配置
- **传输层真相（本调研最关键发现）**：bm-a↔bm-b/bm-c 全走 DERP(**旧金山**) 中继 **364-424ms**·「direct connection not established」=UDP 直连打洞全失败（netcheck：MappingVariesByDestIP 硬 NAT；bm-a 网关 10.86.96.1=多租户网·疑 AP 隔离〔推测〕）·而 bm-a 最近 DERP=新加坡 65.6ms——对端 home DERP 锁在 sfo 225.8ms；bm-b↔bm-c 互连路径未测（待证·若同址可 LAN 直连）
- **毫秒级阶梯（全链=网络 RTT+~0.1ms 总线）**：①选区修复→新加坡 ≈130-190ms（配置级零成本·推测：需各机 netcheck 实测+home DERP 迁移验证）②自建国内 DERP（需云服务器=CEO 物理件域）≈20-60ms ③直连修复（同址换自有路由/交换机绕 AP 隔离 → <1ms；跨城路由器端口映射 → 10-40ms）=真毫秒级·CEO 物理件域
- 判定：总线层毫秒级 ✅ 已实证；跨机全链=传输层修复决定档位（百毫秒→十毫秒→毫秒）

## 四、落地方案（双轨过渡·零扰动产线）
- 架构：bm-a 起 nats-server（WinSW 14.3k★ 服务化或 S4U 任务正门·开机自启·28MB）·4222 端口仅绑 tailnet 面（防火墙规则限 100.64.0.0/10）·三机 nats.exe 客户端直调
- Subject/KV 命名：orders.>（命令流 JetStream 持久化）/poke.<node>（请求应答带 ack）/hb.<node>（心跳 KV+TTL）/state.<node>（KV watch=毫秒推送）
- git 降级：orders.md 照写（CEO 审计正典不动）+夜间定时 commit+push=云端备份；hot path 全离 git
- 迁移三步：P1 bm-a 服务端+KV 心跳上线（idle-watch 改读 KV=根治陈旧面误报）→P2 poke 平移 nats request（HTTP 保留兜底）→P3 双轨验证一周后 git 退出 hot path
- 二期：bm-c 加第二 server 组 cluster（R>1 双活·bm-a 重启不断线）
- 红线保持：大文件（mp4/贴图/KF）不入总线（载荷默认 ≤1MB 级可调）·git=正典史+云端备份照旧·自托管=零配额零计费（不受限制令满足）

## 五、结论应用表（research-protocol §二.1 强制·落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| NATS 选定+总线毫秒级实证（0.06-0.11ms） | 任务单：铺装批 P1（bm-a 服务端+三机客户端+KV 心跳） | 待派 |
| DERP 中继 364-424ms+直连失败=毫秒级真瓶颈 | 任务单：各机 netcheck 诊断批（同址性+DERP 可达性实测） | 待派 |
| 自建国内 DERP 需云服务器 | 决策呈报：CEO 物理件域（服务器保留面） | 候裁 |
| 同址换自有路由/端口映射（直连 1-40ms 档） | 决策呈报：CEO 物理件域（路由器/机房操作） | 候裁 |
| GitHub MCP token 401 过期 | 物理件：CEO 侧刷新（WorkBuddy Phase4 同项） | 已登记 |
| git 降级为备份面 | 法文修改：fleet-nodes.json「data stays in git」律修订（随铺装 P3） | 接线中 |

- 更新记录：T0 骨架→T1 选型矩阵→T2 本机实测→T3 传输层诊断→终稿 51 行
- 防线二：本窗自研自审（CEO 直令快车道）——星数 HTML 直读可复核·延迟数字全本机实测可复跑（%TEMP%\nats-pilot）·未验项已标（nsq release/redis-emqx Windows B级/bm-b↔bm-c 互连/同址性）
