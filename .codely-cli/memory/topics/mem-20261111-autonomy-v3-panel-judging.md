# 机队自驱 v3 + 专家团评审收口（2026-11-11 下午—夜）

正身指针（写这份文件时的实测状态，后续以磁盘与工具返回为准）：

## 一、判/派/验全链路换成机器判

- 任务颗粒度=`cph4/fleet/TAXONOMY-v1.json`（45 任务类型 + 59 工序映射）+ `Tools/fleet/work_matrix.py`（7/7）。实测旧账：2250 张卡 0 张带 task_type，59 道工序与 28 个能力词交集仅 4 个。
- 自驱=`AUTONOMY-V3.md` + `Tools/fleet/station_drive.py`（SENSE→SUPPLY→CLAIM→RUN→VERIFY→RECORD+HANDOFF，12/12）。主控收窄为搜集/了解/分发/模型赋能；只有三件事上报=要模型、对方工位离线、对外/花钱/不可逆。
- 本地闭环=`LOCAL-CLOSURE-v1.md` + `local_loop_check.py`（6/6，五查，三态 PASS/FAIL/SKIP，异地不许替它签字）。
- 专家团=`cph4/fleet/JUDGE-PANELS-v1.json`（34 面板，每面板绑一个 skill + 投票席位 + 逐条 rubric + 确定性否决 + quorum）+ `Tools/fleet/panel_review.py`（8/8）。流程 VETO→VOTE→QUORUM；模型答偏记 ABSTAIN 不计通过；无面板直接 BLOCK。40 道 manual_stages 已改 panel_stages，34 个任务类型的 judge 改 panel；**只剩 T-OPS-CEO 保留人工（权限非判断）**。
- 未知情况=`SITUATION-REGISTRY-v1.json` + `situation_audit.py`（6/6）：从原始数据复算次数、核落点是否在盘；声称闭环但核验不到即判 GAP。**最终 37 种：CLOSED 32 / OPEN 5 / GAP 0**。
- 运营=`OPERATING-LINES-v1.md`（九条线）+ `ACCEPTANCE-v1.json` + `master_patrol.py`（8/8，重算 sha256、人判件不许标 DONE、三级降级）。
- 席位=`AGENT-TEAMS-v1.json`（39 席：主控 8 / 交付 8 / 视觉 9 / 声音 7 / 大脑 7）+ `AGENT-CAPACITY-v1.json` + `agent_team.py`(12/12) + `agent_schedule.py`(9/9)。频率首版把 39 席全算主控=1464 次/天（超额度 5 倍）；返工为按机器分账 + 上限/预期分离 + 零模型席位不占额度 + 事件指纹 → 主控 178/300、视觉 172/400（82%，最紧），全部在额度内。

## 二、三桶与真实缺口

59 道工序：可自驱 **3**（养号草稿、复盘、资产索引）／待接命令 **55**（TOOL-PENDING，契约有命令未接）／权限 1（T-OPS-CEO，CEO 人工发送）。产物契约 58/59（剩 1 道本就不该有）。

## 三、15 个被测试抓出的真缺陷（全部已修，可当新造调度系统的必测清单）

| # | 缺陷 | 后果 |
|---|---|---|
| 1 | 一次性工序每轮重做（refresh_h 空被当过期） | 上线即无限重复劳动 |
| 2 | 离线/被暂停机器照样自驱开干 | 状态从未进判定 |
| 3 | 命令面下的卡永不执行（只跑 self-drive） | 「下令」等于空投 |
| 4 | 并发 upsert 丢写（读-改-写未锁） | 分片数据丢失 |
| 5 | 目录新鲜度取错 mtime | 永远不重做 |
| 6 | 两处目录哈希算法不一致 | 抽验恒失败 |
| 7 | 回执按 id 命名覆盖历史 | 抽验抽不到失败那次 |
| 8 | 缺抽验配置时静默零抽验 | 看着巡过了其实没验 |
| 9 | 目录型产物没有哈希 | 验收失效 |
| 10 | 交接单不带 cmd | 下游接得住跑不了 |
| 11 | 交接与自建卡重复劳动 | 同一件活干两遍 |
| 12 | 命令失败仍先跑评审 | 白烧算力 |
| 13 | 权限件在自驱报告里不可见 | 静默漏报 |
| 14 | 卡无 judge 时不回退任务类型 | 全部卡住 |
| 15 | 评审团 15 处无本方视角 + 漏配回测面板 + 正典 6 指针指向已归档路径 | 判据失效/查不到文件 |

## 四、测试面（17 套全绿）

`station_shards 7 · work_matrix 7 · station_drive 12 · local_loop 6 · agent_team 12 · schedule 9 · situation 6 · patrol 8 · view 8 · cmd 14 · voice 19 · panel 8 · make_index 5 · integrity(全链路一致性) 17 · station_qa(12 工况) 12 · rehearsal(14 场景) 14 · drama_rules 14`；分步计划=`TEST-PLAN-v1.md`。

## 五、当前阻塞（按优先级）

1. **55 道 TOOL-PENDING 接真命令**——自驱能否真跑的唯一硬阻塞。
2. 算力大脑入网（加盘、tailnet IP、驱动/CUDA、填 MODEL-COMPUTE.json 的 url、验 p50<8s）。
3. 三台机修复：传家宝 ComfyUI 未起、小钢炮离线、公司生产力机未注册。
4. 传家宝模型时间已到 82%，需决定降频或把关键帧审片挪到大脑。
5. FluxVerse / BigHouse / BigLife 是否也搬离交付工厂（现留，因同属 3D 工具链）。
6. 44 个 LaunchAgent 仍全暂停；恢复=`Tools/restore-startup.sh`，等 CEO 发话。
7. 唯一新增 OPEN=S37 git 推送失败运行时预演（需独立裸仓沙箱）。
