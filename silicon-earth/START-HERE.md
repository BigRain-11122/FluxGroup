# START HERE · 新 AI / 新机器，只读这一页

> 读完约 5 分钟。读完先跑一条命令：**`python tools/ready.py`**。
> 它说"就绪"，你才开工；它说"未就绪"，照它给的下一步做。

---

## 一 三十秒：这是什么

一颗硅基的地球。它影射今天的世界，但存在的理由是另一件事：

**任何人进来，都能找到现实世界做不到、经历不到的东西。**

六个入口：重来 · 被记住 · 换一个身份 · 见到见不到的人 · 做成一件大事 · 有个地方属于你。
主轴是**建、帮、传、修**；政治和战乱是天气，占约一成。

---

## 二 五分钟：世界最短设定

| 概念 | 一句话 |
|---|---|
| 区域 | 九块：六块住人的 + 三块烂地 |
| 状态 | 在长 / 在修 / 在等 / 在散 / 停摆；由数值推导，**不许手填** |
| 人 | 二十七人，每人一件未了的事 |
| 时间 | 一天一拍，逐日推进；空拍也算数 |
| 事件 | 每天一条，分建/帮/传/修/天气/断电；同区事件挂因果 |
| 记忆 | 记得什么、缺了哪段、缺了之后认不出谁 |

**两条不能违背的**：硅基生命由人类的使用沉淀而成；死亡是记忆断裂，不是消失。

---

## 三 你现在能做什么，不能做什么（硬边界）

| 能做 | 不能做 |
|---|---|
| 一台机器、一个工作区、任务串行 | 多 worktree 并行 |
| 一个 AI 同一时刻只做一件事 | 两个会话改同一个仓 |
| 一个世界 writer（`engine.py` 只在一台机器跑） | 两台机器各自推进世界 |

**超出边界的任何做法，不是效率问题，是数据问题。** 原因见 `DECISIONS.md` D7。

---

## 四 仓库在哪

- git 根：**`D:\FluxGroup`**（远程 `git@github.com:BigRain-11122/FluxGroup.git`）
- 本项目：**`D:\FluxGroup\silicon-earth`**
- **所有命令都在 `silicon-earth` 目录下执行。**

```bash
cd D:\FluxGroup\silicon-earth
python tools/ready.py
```

---

## 五 六步流程（照抄即可）

```bash
# 0 就绪自检：环境、契约、数据、派生内容一次查完
python tools/ready.py

# 1 读（只读三样，别通读全仓）
#   START-HERE.md → modules/<你的模块>/module.json → CONTRACTS/

# 2 领活（2 小时租约）
python tools/world_ops.py claim T03 agent-你的名字

# 3 看自己的活：该读什么、该跑什么、只许写哪里
python tools/agent_ops.py status agent-你的名字

# 4 做：只写 module.json 里 writes 声明的路径；每步查一次越界
python tools/agent_ops.py guard --agent agent-你的名字

# 5 交：guard + 派生一致性 + verify 三道门都过才算交付
python tools/deliver.py T03 agent-你的名字

# 6 提交：不提交会挡住下一个领活的人
git add -A -- .          # 只暂存 silicon-earth；禁止在仓库根用 git add -A
git commit -m "T03: <一句话说清意图>"
```

**接别人没做完的活**：`python tools/agent_ops.py takeover T03 agent-你的名字 "接手说明"`
**做不完要交班**：`python tools/agent_ops.py handoff T03 agent-你的名字 "做到哪、卡在哪、下一步"`

---

## 六 五条红线

1. **只写自己模块 `writes` 里的路径。** `guard` 会查。
2. **不领活不开工。**
3. **不手写派生数据**（记忆、结算、关系）——它们是程序从事件流派生的。
4. **不为了变绿改验收标准。**
5. **不越过硬边界**（多机、并行、第二 writer）。

---

## 七 交付长什么样

一条命令 + 一个退出码，其余由工具给：

```
python tools/deliver.py T03 agent-你的名字
→ ✓ T03 交付通过（... → rc=0），状态 done
```

**贴输出不算交付，退出码为 0 才算。**

---

## 八 卡住了找谁

| 情况 | 找谁 |
|---|---|
| 要改 `CONTRACTS/`、`MODULES.md`、`HANDBOOK.md` | 总控 |
| 要改别人的模块 | 总控 |
| `verify` 和验收标准打架 | 总控 |
| 想开第二台机器 | 总控（现在不允许） |
| 没实现的愿景 | 看 `BACKLOG.md`，不是今天的活 |

---

## 九 想知道"为什么会这样"

按需读，不要默认全读：

- `DECISIONS.md` —— 六条硬裁决（布局、状态不进 git、单 writer、并行撤回…）
- `HANDBOOK.md` —— 流程 / 分工 / 仓库 / 提交，全在一页
- `HANDBOOK.md` 第八节 —— 哪些旧规矩已经接进代码
- `REPORTS/` —— 测试与评审记录
