# 专家团评审（JUDGE-PANELS-v1）· 2026-11-11

> 令源：CEO 2026-11-11「不要人判，你给我找好 skill 和专家团，并让他们科学决策和审查」。
> 机器面=`cph4/fleet/JUDGE-PANELS-v1.json`（**34 个面板**）；执行器=`Tools/fleet/panel_review.py`（自检 8/8）。
> 一句话：**判断不再找人，交给 skill 的判据 + 席位投票 + 确定性否决。**

## 一、三步，顺序不能换

1. **VETO 客观否决**（先跑，不进投票、不花算力）
   - `no_artifact` 证据在不在、非空
   - `hash_mismatch` 有回执哈希时必须一致
   - `voice_gate_fail` 语感闸有没有 BLOCK 项
   - `off_redline` 有没有碰红线文件（cookie/密钥）
2. **VOTE 席位投票**：每个席位按该 skill 的 rubric 逐条判 PASS/FAIL 并给证据；席位经本地模型通路（本机→大脑→主控）。
3. **QUORUM 定谳**：够票= PASS；有 BLOCK 票= REVISE 并列理由；票不够= REVISE。

**铁律**：模型答偏或不可用 → 该票 ABSTAIN，**ABSTAIN 不计入通过票**；没有评审团配置 → 直接 BLOCK。宁可返工，不许假绿。

## 二、谁判什么（34 面板按任务类型挂）

| 领域 | skill | 席位 |
|---|---|---|
| 剧本/镜表/台词 | `drama-director`、`tw-mv-director` | C-GATE · V-SHOT · V-CUT · C-VOICE |
| 选角/音色/一致性 | `mv-casting` | A-CAST · A-VOICE · V-KF · V-CONSIST |
| 剪辑/字幕/配乐/调色 | `mv-edit-rhythm`、`mv-colorist` | V-SUB · V-CUT · A-BGM · A-MIX |
| 合规/发布/提审 | `compliance-guard`、`ship-ops` | C-LEGAL · C-GATE · D-ADMIT · D-BUILD |
| 游戏/车机/资产规范 | `game-asset-ship`、`asset-audit` | D-SUBMIT · D-ICON · D-CAR · D-BUILD |
| 城市/场景/事件 | `silicon-city-ops` | D-BUILD · V-CONSIST · C-MATERIAL |
| 量化/回测 | `quant-backtest-gate` | B-QUANT · B-AUDIT |
| 竞品拆解/配方 | `content-recon` | C-MATERIAL · C-GATE |
| 文案/增长 | `growth-ops` | C-VOICE · C-LEAD · C-LEGAL |
| 复盘/账本 | `memory-curator` | C-BOOK · C-LEAD |

## 三、人判清零，但有一类保留

- 40 道原来标 `manual_stages` 的工序，全部改为 `panel_stages`，由评审团判。
- `TAXONOMY` 里 34 个任务类型的 judge 从 `manual` 改成 `panel`。
- **只剩 1 类保留人工**：`T-OPS-CEO`（发送/注册/备案/采购/对外承诺）。这不是判断，是权限边界——机器可以审内容，但不能替你以你的名义发出去。

## 四、实测

1. 自检 **8/8**：全员 PASS→PASS；产物缺失→BLOCK 且不进投票；有 BLOCK 票→REVISE；模型答偏→ABSTAIN 不算通过；没有评审团→BLOCK；合规面板 quorum=1 也不会被答偏蒙过。
2. 真实产物实跑：`PROD-ACCOUNT-GROWTH/复盘`（skill=memory-curator，2 席）→ **PASS**，两席各自给出证据指针与逐条判定，结论写进 `state/panel-ledger.jsonl`。

## 五、还没解决的

1. **TOOL-PENDING 56 道**：判断会自动发生，但**产物还没人生产**——因为执行命令没接。评审团能判，前提是先有东西可判。
2. 评审团本身耗模型：已纳入 `AGENT-CAPACITY` 的额度核算（review 档），超过预算会排队而不是硬跑。
