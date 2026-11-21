# 养号线职责表 v2.2（27 项 · 故障驱动 · 内容级判据 · 内存环 · 演进环）

> 机读正身：`AGENT-SPEC-v2.json`　审计器：`Tools/fleet/agent_audit.py`
> 判据提供者：`Tools/fleet/social_guard.py`（只读，不产内容、不占 GPU）
> 总入口：`Tools/fleet/social_audit.py`（守卫 → 闸回归 → 账本 → 自检 → 履职）
> 2026-11-21 立。v1 的教训：只判「执行体在、证据在、证据新鲜」会得到 **12/12 全绿而当天 0 条评论**。

## 一、为什么升版（v1 的三个假绿）

| 假绿 | 实况 | 修法 |
|---|---|---|
| S01 出稿：证据 = `USER-AGENT-LEDGER` mtime 0.0h → OK | 当天只有 watch/like/danmaku，**评论 0 条**；最近一条在 79.3h 前 | 出稿判据改成「24h 内 action=comment 且 ok=true」 |
| S10 闸回归：证据 = `GATE-REGRESSION.json` | 那是**输入集**，不是运行结果；有人编辑它就"新鲜" | `gate_regression.py --save` 落 `GATE-RESULT.json`，断言 pos_rate/neg_rate |
| S12 评测：证据 = `SEGMENT-EVAL.json` 0.5h → OK | 里面 `n=10`，而 n=10 的噪声大于判定阈值（同一件 79.9 vs 55.9） | 断言 `samples ≥ 30` |

通用问法：**这个绿是谁写的？它写的是"碰过文件"还是"做对了"？**

## 二、三层判据

1. **执行体存在** —— 谁做（真实工具路径）
2. **证据在 stale 内** —— 做了，且不是很久以前
3. **assert 通过** —— 做对了（内容断言，全部来自 `GUARD-ALL.json` 的 pass 映射）

六态：`OK / STALE / MISSING / NO-EXECUTOR / NOT_PASS / SKIP`。
**SKIP = 量不到，不算通过**（缺 mid、缺样本、缺落盘都要显式写原因）。

## 三、分级（一票否决只给红线）

- **P0 红线（5）**：出稿闸回归、不做引流、夜间静默、跨号隔离、统一内存不换页 → 失守 `exit 2`，停线排查
- **P1 产能（13，含 M02、E01 反思、E02 审查）**：采集、语料卫生、烘焙、简报、训练轮次、租约、自举、评论出稿、副动作、发送归因
- **P2 体检（9，含 M03、E03 迭代、E04 创新）**：健康、账本、多样性+生成质量、训练体检、调度一致性、自审、服务端唯一、迭代节奏、创新落地

## 四、20 项业务职责（故障 → 判据 → 失效症状；内存环另见八点五）

| ID | 级 | 职责 | 是哪次故障逼出来的 | 判据（红线 = 数） | 坏了你会看到 |
|---|---|---|---|---|---|
| G01 | P0 | 出稿闸回归 | 拿品味分当闸，亲笔句 88% 被误杀；我们的坏句 9/17 漏网 | pos_rate ≥ 0.90、neg_rate = 1.0 | 好话发不出去 / 烂话能出去 |
| G02 | P0 | 不做引流 | 老 AI 评论「壶关我分享给你呀」 | DRAIN 回归 3/3 拦住 | 评论里出现互关/私信/加群 |
| G03 | P0 | 夜间静默 | 真实评论 1–6 点≈0，深夜开窗最像脚本 | 近 7 天 1–6 点动作 = 0 | 凌晨台账还有动作 |
| G04 | P0 | 跨号隔离 | 同 mid 两 profile = 两套指纹；两号摸同一条视频 | 24h 同 aid 单号、同 mid 单活跃 profile | 两号在同一视频前后脚 |
| C01 | P1 | 采集与学习 | 语料只减不增，模型吃老本 | 24h 内有 collect/learn | 训练集规模停滞 |
| C02 | P1 | 语料卫生 + 人设隔离 | 实战回流 20 条里 8 条 AI 腔；无门槛回填 +4.4 REJECT | AI 腔率 ≤5%、亲笔样句命中 = 0 | 越训越像客服 / 新号说话像老号 |
| C03 | P1 | 烘焙与分段 | 分段塌成 generic，新语料进不了训练面 | 6h 内、rows>0、段≥6 | 账本在涨但训练集没变 |
| C04 | P1 | 内容简报 | 忘传简报时 content_fit 25% vs 53.6% | 覆盖率 ≥90% | 评论全是"这视频真好" |
| T01 | P1 | 训练轮次与上线指针 | ANSI 色码让 val_min 静默记 None 还判 KEEP | verdict 合法 + KEEP/REJECT 有 val_min + BLOCKED 有 why | 训练"成功"但指标是空的 |
| T02 | P1 | GPU 单点租约 | 3 消费者互抢：10 步/分 → 3.3 步/分；野锁让全队永久让路 | 持有者 ≤1 且 pid 活着 | 一直 GPU-BUSY、训练不动 |
| T03 | P1 | 自举补语料 | 回填稀释；自举是唯一高质扩量来源 | 12h 内 ≥1 条 selfgen | 训练集停滞、闸通过率低 |
| B01 | P1 | 评论出稿 | 12/12 全绿而当天 0 条评论（79.3h） | 24h 内 ≥1 条 ok 评论 + 同视频 7 天 ≤1 | 只有赞和弹幕，没有一句话 |
| B02 | P1 | 副动作与活人节奏 | acct3 进程 alive 但 14.7h 没动作，健康表仍 green | 看/赞/弹幕齐 + 活动时段 ≤2h 有动作 | 进程在跑但账号不动 |
| B03 | P1 | 发送失败归因 | 3 条 fail 里 2 条其实是"距上帖 8 分钟"的自家节律 | 失败必有 why + 真失败连续 <2 | 把节律拒绝当封号，或反之 |
| S01 | P2 | 健康哨兵 | 电池时 18.6s/步 vs 接电 4s；僵尸训练哨兵卡住出稿 | level ≠ red | 出稿一直 skip why=training-gpu |
| S02 | P2 | 量化账本 | 主控只判得了自己盘上的东西 | runs ≥1、corpus.rows ≥1000 | 账本全是 0（读错路径） |
| S03 | P2 | 多样性 + 生成质量 | 真实 陈述49/短评38，我们 77/6；AI 腔 10% | 陈述≤60%、短评≥25%、跨度≥12、AI 腔/缺陷 ≤5% | 每句话都一个腔调、一样长 |
| S04 | P2 | 训练体检 | 1.1 epoch 白跑；v5 配方没落到各段；n=10 判不准 | epoch 3–5、配方=RECIPE、n≥30 | 训得越久越差 / 判词随机跳 |
| S05 | P2 | 调度一致性 | 一次性十轮任务留在列表会再发十条；selfgen 10800s vs 表 21600s | 声明=实载、退役未复活、rc 正常、节拍一致 | 改配置没改表，让路逻辑全乱 |
| S06 | P2 | 职责自审 | 审计器自己只认 mtime，也会假绿 | `--self-test` = PASS（含改坏必翻负控） | 全绿但产出为 0 |

## 五、判据由谁产出（不许互相洗白）

```
social_guard.py（只读：领域规则 + 阈值 + 取样）
    → state/GUARD-{CORPUS,TRAIN,ACCOUNTS,SENDS,SCHED}.json + GUARD-ALL.json（合并面）
gate_regression.py --save → state/GATE-RESULT.json
social_metrics.py / diversity_audit.py → METRICS.json / DIVERSITY.json
agent_audit.py --self-test → state/AUDIT-SELFTEST.json
agent_audit.py（只判：执行体/新鲜/assert）→ AGENT-AUDIT.json
```

合并面的理由：B02 的 `SD06` 在 SENDS、`AC01` 在 ACCOUNTS，跨文件断言读不到字段会**静默变 SKIP**。

## 六、当前实况（2026-11-21 23:00 首跑）

- **P0 5/5 通过**（红线未破）
- **P1 2 项未过**：B01 评论出稿（SD01 79.3h 无评论；AC05 同视频 7 天 2 条）、B02（acct3 14.7h 无动作）
- **P2 3 项未过**：S03（陈述 77%/短评 6%/AI 腔 10%）、S04（epoch 1.63/7 段旧配方/n=10）、S05→已修（selfgen 节拍对齐、practice10 已停用）
- 首跑即修掉的两个真卡点：**僵尸 `TRAIN-EXCLUSIVE`**（pid 20909 已死，出稿让路 1 小时+，判据从"等 3 小时"改为"pid 死了立刻清"）、**一次性十轮实战仍挂 launchd**（下次 bootstrap 会真发十条）

## 七、怎么跑

```bash
python3 Tools/fleet/social_guard.py --all          # 只算判据，落 GUARD-*.json
python3 Tools/fleet/agent_audit.py                 # 21 项履职，P0 失守 exit 2
python3 Tools/fleet/agent_audit.py --tier P0       # 只看红线
python3 Tools/fleet/social_audit.py                # 总入口（定时 com.fluxgroup.socialaudit 每 6h）
python3 Tools/fleet/agent_audit.py --self-test     # 9 个状态/断言 + 3 条负控
python3 Tools/fleet/social_guard.py --self-test    # 8 类判据的改坏必翻
python3 Tools/fleet/mem_probe.py --gen 3           # 统一内存：真实生成前后 swap 增量
python3 Tools/fleet/evolve_audit.py                # 反思/审查/迭代/创新
python3 Tools/fleet/evolve_audit.py --snapshot     # 审查通过后记参数基线
```
