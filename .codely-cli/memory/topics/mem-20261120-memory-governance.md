# 记忆与规则面梳理（2026-11-20）

CEO 令：「梳理我最新的规则和产出什么的，没用的过时的删了」。

## 一、两个面先分清（这是本轮最重要的一条）
| 面 | 文件 | 性质 | 治理前 | 治理后 |
|---|---|---|---|---|
| 注入面 | 仓根 `CODELY.md` | 每会话强制注入（User/Feedback/Project/Reference 四段） | 41,584B / 47 条 | **36,825B / 47 条**（回到预警线 35.8KB 附近） |
| 平台记忆面 | `.codely-cli/memory.md` | `read_memory(scope=project)` 读的库 | 70,099B / 99 条 | **50,913B / 99 条** |
| 主题库 | `.codely-cli/memory/topics/` | 一切长文 verbatim，按需读 | 38 个文件 | 38 个 + 本轮迁入 27 段 |

**预算闸默认扫错对象**：`Tools/memory-budget-gate.py` 的默认 `path` 是 `~/.codely-cli/CODELY.md`（本机是 **0 字节**），所以它长期报 `bytes=0 entries=0 / GATE-OK`，而真实注入面 `CODELY.md` 一路涨到 41.5KB 没人管。CLI 下必须显式 `--path CODELY.md`（脚本注释 v2.4 里也写了"闸一直是 `--path <repo>/CODELY.md` 跑的"）。→ 结论：任何"预算/体积"闸先验"它到底打开了哪个文件、那文件多大"。

## 二、注入面（CODELY.md）压了什么
1. **本地模型雷达**（2206B）→ 480B：补现役 v2-20261114 策略（4b-mlx 常驻、9b-mlx 为 big、8b 退役、deepseek 本机禁跑且 11-15 已删），机制细节指 `topics/local-inference.md`。
2. **自启暂停**（1417B）→ 380B：原文写"fluxgroup 0 项"，但 11-19 实测已有恒定 4 项白名单（pulse/console/ollamamodel/llmgateway）——这是**已被现实推翻的陈述**，改成现状+历史指针。
3. **堵点五类 / 16 类闭环**（1533B + 1360B）→ 各约 480B：保留判据与正身文件路径，删掉逐条 case 复述。
4. **吸嘟嘟夜批实况**（1357B）→ 420B：属"已消费的批次叙事"，按治理规则不留过程，只留仍有效的口径。
5. **机队级定案**（1414B）→ 560B：保留自驱四条边界与算力大脑端点阶梯。

## 三、平台记忆面（memory.md）做了什么
按"超 300 字落主题库、记忆面只留指针"逐条搬迁 **27 条**（两批 12 + 13，加第三批 2 条）：
- 训练/评测 → `lora-train-quality-20261118.md`、`training-verdict-noise-and-power.md`
- 养号/语料 → `social-practice-20261118.md`、`social-publish-verify-chain.md`、`social-loop-conductor-20261120.md`
- 机队/运维 → `fleet-dispatcher.md`、`tool-pitfalls.md`、`agent-ownership-mechanism.md`、`mechanism-alive-but-idle-20261116.md`
- 算力/训练调度 → `gpu-squeeze-ceiling-20261118.md`、`compute-scheduling-time-slicing.md`、`train-concurrency-segment-acceptance.md`
- 闸/git → `gate-integrity.md`、`git-surgery.md`
- 本轮新增 `BM-M-MEDIA-LANE` 的 whisper 权重已删说明（见 11-15 清理文件）

## 四、产出面清理
1. `auto-saves` 93 份 → 剩 32 份：删掉 7 天以前的 **61 份 / 243MB**，清单落 `cph4/fleet/state/auto-save-prune-20261120.json`（含每份 path+bytes 可回查）。依据：这些是聊天 JSON 副本，正身是 `~/.codely-cli/tmp/<hash>/chats`，且 `memory-slim.py` 明确跳过该目录、`disk-sweep.ps1` 只报体积。
2. 记忆快照 `cleanup-gate-2026-11-03/04/08` 删除，保留最近两套（11-15、11-17）作为回滚点。
3. 中间备份（b2/b3）与 `/tmp` 下的一次性脚本清理。

## 五、附带修好的两处假红（顺手验证得到）
- `docs_curate.py`：从"dup-or-empty-left 10 条"变为 **2161 个文档全 KEEP / 0 DELETE**——根因就是快照目录里的 `CODELY-pre.md`、`memory.md.bak` 被算成重复文档。
- `fleet_doc.py --check`：从"第 248 行节点表不一致"变为 **源间漂移 0 处 / 文档与配置一致**。
- 两者都不需要 `--apply` 就能显示干净，属"删掉重复件后判据自然绿"，不是调阈值调出来的。

## 六、留下的判断（下一轮可继续）
1. `CODELY.md` 现在 36.8KB，仍在预警区（35.8KB）边缘；最深的两条已是 1205B/1200B，再压要动法条本体，需 CEO 点头。
2. `queue-receipts` 3,049 份 / 24MB：最新到当天，属活体审计链，**未删**；若要瘦身应按 14 天窗口归档而非删除。
3. `state/*.json` 140 份里有 11-03 的一次性市场探针结果，但删了会让审计判 NO-EVIDENCE，**未删**。

## 七、本轮另外抓到的两件事（都不是我制造的）
### 1) 退役模型会被雷达自动拉回来（已修）
2026-11-15 删掉的 `qwen3:8b`（5.2G）在 11-20 又回到盘上——`model_radar.py` 的 auto_pull 把它当 `NEW-TAG` 拉回来了。修法两处：
- `cph4/fleet/LOCAL-MODEL-POLICY.json` → `auto_pull.retired = ["qwen3:8b","deepseek-r1:14b"]`
- `Tools/fleet/model_radar.py` → pull 循环里加一条 `if row["model"] in (ap.get("retired") or []): continue`
- 已再删一次并 `ollama list` 复核；雷达 `status` 自检正常（qwen3:4b-instruct KEEP）。
**通用判据**：凡是"删掉的东西会自动长回来"的清理，先找自动补给口，把"退役"写进策略机读件，光删不封渠道等于白删。

### 2) 训练权重进了版本库（3.0G/3.1G 被 git 跟踪，未处理）
`cph4/fleet/social/train/RUNS` = 3.1G，其中 **3.0G 是 git 跟踪文件**：27 个 `adapters.safetensors` + 14 个 `0000100_*` + 13 个 `0000200_*` + `ckpt300`。50 个 run，`TRAIN-LOOP-LEDGER.jsonl` 只引用 8 个（11-19 20:05 之后）。
这正是"运行时产物入库"的老毛病（此前是 2612 份回执），但这里入的是模型权重，代价更大：每次 clone/分发都背着 3G，且多机会持续分叉。
**未执行**，因为删它要跨机 git 手术（bm-a 等机器持有同名权重）。建议方案（待 CEO 一句批准）：
1. `.gitignore` 加 `cph4/fleet/social/train/RUNS/*/adapter/`、`.../ckpt*/`；
2. `git rm -r --cached` 只保留 `RUN.json`/`train.log`/`AB.jsonl` 这些小证据件；
3. 工作区只留台账引用到的最新 KEEP adapter（当前 `20261120-152218`），其余本地删；
4. 清完在 bm-a/bm-d 各跑一次 `git gc --prune=now` 收敛 pack。

### 3) 磁盘为什么反而涨了 32G（不是回滚）
11-15 清理后可用 287G → 11-20 晚上 252G，增量来自机队在跑（`station_drive --loop` + `llm_gateway` 在进程里）：`FluxGroup` 2.3G→8.9G（`cph4/fleet/social/train/RUNS` 3.1G、`mv0001-handover` 268M、`state` 94M）、`~/.fluxgroup` 新增 4.9G（models 2.9G + bilibili 浏览器 profile 1.2G）、`.fluxgroup-state-wt` 464M→3.4G、模型重拉 5.6G。
→ 结论：**"清完就变多"要先查机队是不是在跑**，别把它当成清理失败。
