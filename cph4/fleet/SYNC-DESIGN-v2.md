# 同步机制 v2（SYNC-DESIGN-v2）· 2026-11-11

> 令源：CEO 2026-11-11「git 同步的机制也要改了」「MacBook 主要是轻量工作和主控」「先修机制和规则」。
> 状态：T2 自决件（可一行退回）。本件只定"什么进 git、谁写哪一块、怎么读"，不改治理法条本义。

## 一、现在为什么必须改（现状实测）

1. 四台机共用一个 `PRODUCTION-QUEUE.jsonl`，同步面每 60s `git add -A cph4/fleet` + 仓库级 commit + `pull --ff-only`，失败退 `merge -X ours`（本地胜）。
2. `-X ours` 会**静默丢弃远端行**——不报错、但没同步过去。这是"状态看着同步了其实没有"的根。
3. `.gitattributes` 末尾 `cph4/fleet/*.jsonl` 与 `**/*.jsonl` 两条通配给**队列、备队列、车道**也套了 union，而同一文件上方注释明写"状态型账本绝不用 union"。实测后果：`INTAKE-PENDING.jsonl` 16826 行、唯一 id 仅 238。
4. 工作树只要出现 `Tools/` 或 `docs/` 脏文件，同步面**整轮 skip**（2026-11-11 04:26/04:27 实测）——手写代码被改一次，全队状态停摆。
5. 并发的 `git merge` 抢 `.git/index.lock`（04:01/04:18/04:23/06:21/10:12 五次实测），每次冲突都靠人。
6. 状态文件与代码同分支同目录，导致每次同步都在跑 git 的写路径；一天 1400+ 次提交，历史被状态淹没。

## 二、新原则（五条）

1. **git 只承载需要版本化的东西**：代码、规则、配置、注册表、文档、产物清单（manifest）。
2. **运行态不进主分支**：队列、车道、回执、心跳、缓存、日志一律进 `cph4/fleet/rt/<station>/`，且**每台机只写自己那一份**。
3. **一机一写者**：同一路径只有一个写入者 → 冲突在物理上不可能发生，不再需要"谁先谁后"的裁决。
4. **读方不改工作树**：主控读别人的分片只 `git fetch` + `git show origin/main:<path>`，不 checkout、不 merge。
5. **冲突必须显性**：运行态文件禁止自动合并（不用 union、不用 -X ours）；真撞上就报出来，不静默吞掉。

## 三、目录与归属（新的唯一布局）

    cph4/fleet/
      rt/                        ← 运行态（每机一片，唯一写者）
        delivery/                ← 交付工厂（公司生产力机）
          queue.jsonl            ← 本工位队列（只有它写）
          receipts/              ← 本工位回执
          state.json             ← 心跳与容量
        visual/                  ← 视觉工位（传家宝）
        audio/                   ← 声音工位（小钢炮）
        brain/                   ← 大脑工位（算力大脑）
        control/                 ← 主控（MacBook）
      products.json              ← 产品注册表（新，唯一产品口径）
      stations.json              ← 工位档案（新，唯一硬件/产能口径）
      rt/README.md               ← 分片约定（谁写谁读）

老文件处置：`PRODUCTION-QUEUE.jsonl` / `PRODUCTION-BACKLOG.jsonl` / `lanes/*.json` / `queue-receipts/*`
在迁移期**冻结为只读**（不再有新写入），迁移完成后移入 `cph4/fleet/archive/legacy-queue-20261111/`。

## 四、谁写什么、谁读什么

| 角色 | 写 | 读 | 禁止 |
|---|---|---|---|
| 各工位执行器 | `rt/<自己>/` + 自己产物的 manifest | `git show origin/main:cph4/fleet/rt/<自己>/queue.jsonl` | 不写别家分片、不写 main 上的规则文件 |
| 主控（MacBook） | `rt/control/`、账本、一屏、注册表 | 五份分片（只读 blob） | 不写产物、不写业务队列 |
| 会话/人 | 规则、配置、注册表、代码 | 全部 | 不改运行态分片 |
| 同步面 | 只推自己工位目录 | — | 不 `add -A`、不 `-X ours`、不整轮 skip |

## 五、同步面 v2 的规则（state_sync 改造口径）

1. 提交范围：`git add cph4/fleet/rt/<station>` + 本工位产物 manifest；**用 pathspec 提交**（`git commit -- <path>`），不再 `add -A`。
2. 不再因 `Tools/`、`docs/` 脏而整轮放弃：脏文件不在本次 pathspec 内，天然不会被带进去。
3. 拉取：`git fetch origin main` + 读 blob；**不 pull、不 merge** 到工作树（读侧无冲突）。
4. 推送：失败重试 2 次；仍失败保留本地、记一行、下轮再推；**禁止回滚自己的分片**。
5. 频率：状态变更后 15s 内合并一次提交；固定上限每 60s 一次（避免 1400 次/天的噪声）。
6. 日志按天分卷：`rt/<station>/log/<YYYYMMDD>.jsonl`，一天一个文件，便于归档与对比。
7. 熔断：连续 3 次推送失败 → 记 `E-SYNC` 并降频到 5 分钟，不再每轮重试。

## 六、主控怎么读（去掉 -X ours）

    git fetch origin main
    git show origin/main:cph4/fleet/rt/visual/queue.jsonl | python3 ...

- 只读 blob，不动工作树 → 主控本机永远不脏，也就不存在"脏树挡同步"。
- 五份分片合并成视图只在内存里做，不落盘成第六份文件。

## 七、冲突策略

1. `rt/**` 设置 `-merge`（禁用自动合并）与 `-text`（不做换行归一）。
2. 回执类只追加内容（append-only）保留 union，但只限 `rt/<station>/receipts/**` 与归档台账。
3. 同一文件出现冲突标记 = 有人跨工位误写，按 E1 处理并当场纠正归属，不改合并策略。
4. 规则/配置类文件（products/stations/autonomy/card-policy）走普通提交，冲突必须人工解决，不允许 any-side-wins。

## 八、MacBook 的定位（写入规则）

1. 只做四类活：文本与判读、剪辑与字幕、验收与抽验、账本与一屏。
2. 不接 GPU 生成、不接媒体素材落盘（磁盘只剩 210G）、不接大文件写入。
3. 主控不再执行产线卡；`rt/control/queue.jsonl` 只放账本/验收/对外材料类卡。
4. 本地模型只服务主控自身与机队借用的 8792 网关；不常驻 >8GB。

## 九、迁移步骤（可逆）

1. 建 `cph4/fleet/rt/` 五份空分片 + README（本批）。
2. 改 `.gitattributes`：删两条全量 union 通配；`rt/** -merge -text`（本批）。
3. 改 `queue_integrity.py`：关键文件路径修正 + 纳入 dispatcher/*.json（本批）。
4. 改造 `state_sync.py` 支持 `--station`（下一批，需实机验证）。
5. 各机切换写入路径，老队列冻结只读。
6. 观察 48 小时：冲突数应为 0，重复 id 应为 0；否则回滚 .gitattributes 与 sync 参数。

## 十、验收判据

1. 48 小时内 `git merge` 冲突 = 0，`index.lock` 失败 = 0。
2. 队列重复 id = 0（每片唯一写者）。
3. 主控读五份分片耗时 < 2s，且不产生工作树改动。
4. 任一台机的工作树脏文件数不影响同步成功。
