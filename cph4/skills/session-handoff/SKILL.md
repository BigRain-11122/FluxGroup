---
name: session-handoff
description: 会话交接书（跨会话/跨机接续：在产、待判、阻塞、下一步、已试并失败的路、决策与理由）。Use when ending a session, when context is about to be compacted, when another agent or machine must continue the same work, when a new session starts and must pick up where the last one stopped, or when the same mistake keeps being repeated across sessions. Triggers on 交接/接手/接续/换会话/上下文压缩/压缩后失忆/上个会话做到哪/继续之前的活.
---

# 会话交接书（session-handoff）

## 为什么存在

上下文一断就要重读几千行文档，等于每次重新上岗。
更贵的是**重走已经失败的路**：2026-11-03 夜里我三次以为 git 坏了，实际是并发会话把工作区回退——
如果上一份交接书写了"试过 reset、无效，真因是并发覆盖"，那三次可以省掉。

## 现成机制（先跑，不要手写重复内容）

```bash
python Tools/fleet/handoff.py            # 生成 cph4/fleet/HANDOFF.md
python Tools/fleet/handoff.py --json     # 机读
```

自动段（来自磁盘事实，不写判断）：**在产 / 待判 / 阻塞 / 下一步**。

## 自动段之外必须人手补的两段

自动脚本只能读到"状态"，读不到"为什么"，所以交接书必须补：

1. **已试并失败的路**（一行一条：attempt → 结果 → 结论）
   例：`reset --hard origin/main → 文件被并发会话回退 → 真因是多写者，不是分支坏`
2. **决策与理由**（一行一条：决定 → 依据 → 失效条件）
   例：`音色闸阈值改为两档（source/delivery） → 依据=10 条真实 TTS 实测分布 → 失效=换成 48k 素材后需重标`

## 写完后三件收口

1. 交接书进 git（`cph4/fleet/HANDOFF.md` 随仓分发），否则下个会话在别的机器上看不到；
2. 文件里出现的路径必须真实存在（死指针等于没写）；
3. 若本轮有"别人会踩的坑"，同时写进记忆或对应的 LAW 文档，不只留在交接书里。

## 自检（交接前逐条过）

1. 新会话只看这一页，能不能在三分钟内知道"现在在产什么、卡在哪、下一步做什么"？
2. 有没有写"试过但失败的路"？没有的话，下个会话大概率重走。
3. 有没有写关键决策的依据？只写结论会让下个会话推翻你。
4. 每个提到的文件路径是否真实存在（`python Tools/gate_rigor_check.py` 可顺带体检引用）？
5. 是否已提交进 git（未提交的交接书在别的机器上不存在）？

## 与其他机制的分工

- 长期事实 → 记忆（CODELY.md L0/L1）
- 项目正典 → `cph4/fleet/**` 下的 LAW/SPEC/CANON
- **本会话的现场** → HANDOFF.md（只保留最近一轮，旧轮次由 git 历史承载）

## 可跑自查（自动生成·2026-11-03）
判据：下面这条命令必须能在本机真跑起来（rc∈{0,1,2} 且有输出）；跑不起来说明技能指向的工具已失效，先修工具再谈技能。

```
python3 Tools/fleet/handoff.py --help
```
实测：rc=0，输出 35 行，首行 `# 交接一屏（2026-11-04 12:15）`。
