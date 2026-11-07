---
id: eng.tools
title: 工具目录（职责速查）
layer: engineering
questions: ["做某件事该用哪个脚本", "有哪些自动化"]
facts: ["Tools/**/*.py"]
generated_at: 2026-11-08T00:59:40
generator: Tools/kb/build_kb.py
written_by: template
---
## 一句话
主控与机队全部自动化脚本目录：`Tools/fleet/`（228 个），根 `Tools/`（116 个）。

## 工具清单（按文件名字典序，职责取自模块首行）
| 工具 | 职责 |
|---|---|
| `Tools/fleet/artifact_review.py` | artifact_review.py - 三层审核 + 入档 + 入库（真读内容，不看存在性）。 CEO 2026-11-07：「不仅要查文档，还要真实的审核产出，要几层审核，确定后入档入库， 入机队里面的仓库。」 DONE 只表示执行结束，不表示产物合格。本工具把 DONE 卡真正打开、读内容、交叉核对， 三层都过才 |
| `Tools/fleet/asset_board.py` | asset_board.py - contact-sheet board + inventory receipt for image-set audits. DE-AI-SPEC B1/B2/B3: the anti-AI-face gate is a HUMAN gate (director's seat), but |
| `Tools/fleet/backlog_fill.py` | Shim. The LIVE implementation is Tools/backlog_fill.py -- that is the one master_agent.py and lane_agent.py import (they put os.path.dirname(HERE)=Tools on sys. |
| `Tools/fleet/brain_brief.py` | brain_brief.py - the control plane's own one-page brief, computed from facts. Why (CEO 2026-11-01: 大脑要「及时、准确、创新、严格」): * 及时 - it runs on the pulse, so the page i |
| `Tools/fleet/brain_service.py` | brain_service.py - bm-m as the fleet's SECOND BRAIN (CEO 2026-10-30 令). Master was already dispatch + judgment seat. This adds the production leg: every busines |
| `Tools/fleet/cadence.py` | cadence.py - 节奏表的校验器与排期器（不执行任务，避免与主控脉双调度）。 三个问题它必须能回答： 1. 这张表本身科不科学：周期/相位/依赖/撞车/预算/环。 2. 表与执行体是否一致：表里的 stage 在 master_pulse.STAGES 存在吗？脉在跑的阶段 有没有漏登记？（两处各写一套是所有漂 |
| `Tools/fleet/cadence_build.py` | cadence_build.py - 从主控脉的 STAGES 生成细分节奏表（v3）。 为什么生成而不是手写：脉里 86 个阶段在跑，手写的表只登记了 32 条，剩下 54 条的 周期/判据没人管——"节奏表"就成了部分真相。这台机器负责把两边对齐： * STAGES 有的、表里没有 -> 补条目（周期取代码，域按规 |
| `Tools/fleet/ceo_pilot.py` | ceo_pilot.py - 带 CEO 做事：一次只推一件，带理由、命令、耗时与验收。 CEO 2026-11-07：「我要做的事情非常多…让常驻大模型带我去做，监督/派发/雷达/找工具/ 验收/审查…高频率的科学频次」。高频不等于频繁打扰：候选全进池子，规则打分取最高一条， 同一个题不重复刷屏（除非它变坏）。 Si |
| `Tools/fleet/ceo_three.py` | ceo_three.py - 每天只交 CEO 三件事（其余自决）。 CEO 2026-11-06：「代替我做好各个指挥工作」。指挥里唯一不能代签的就是三类： 不可逆、对外发布、花钱超限；再加「同一根因三次未解」和「必须人上机的物理动作」。 Rules decide, model only words it. Orde |
| `Tools/fleet/commander.py` | commander.py - 指挥层一屏（CEO 只看这一屏）。 按 cph4/fleet/COMMAND-CADENCE-v1.json 的六个节拍做结论，不重复跑工具： A 值守四件 / B 机队实况 / C 线与产出 / D 一屏 / E 指挥质量 / F 手交 CEO。 Iron rules it obeys: |
| `Tools/fleet/demand_audit.py` | demand_audit.py - 逐条核验 CEO 需求总账，把缺口变成卡。 Why 需要它：CEO 的命令散在 319 行台账和 22 条口头指令里，靠人记必然漏，靠文档声称 必然假绿。这台机器只做一件事——每条需求一个可判定的探针，判不了的明确标 UNVERIFIED 并写清谁判，绝不含糊过关。 Usage: d |
| `Tools/fleet/dr_check.py` | dr_check.py - 灾难恢复体检：这台机器坏了之后，多久能重新站起来。 不真做恢复（危险且耗资源），只核对三件会被忽略的事： 1. 备份是否新鲜、是否可解析（备份存在但打不开 = 没有备份）； 2. 关键配置是否都在 git 里（不在 git 的配置 = 机器死了就永久丢失）； 3. 接管清单是否可执行（新机要 |
| `Tools/fleet/env_selfheal.py` | env_selfheal.py - a node installs its own missing dependencies (CEO 2026-10-30: "缺什么让他自己装啊"). Runs ON THE WORKER BOX, by the lane agent, before a job starts. Th |
| `Tools/fleet/fact_check.py` | fact_check.py - 审查情报本身是否可信（不是审查产物，是审查结论的来源）。 Why: OSS 雷达自己会标「⚠星数超 10 万需人工核实」，但没人核。情报不可信 → 选错工具 → 整条线白干。这台机器只做一件事：把雷达里越界的数字拿去 GitHub API 对一遍，差异超阈值 判 STALE，对得上判 V |
| `Tools/fleet/fleet_lane.py` | fleet_lane.py - shared lane vocabulary for the master agent and the lane executors. Why: the 2026-10-27/28 post-mortems all landed on the same sentence - "there |
| `Tools/fleet/fork_close.py` | fork_close.py - 一台机自己收口它与本仓 origin/main 的分叉。 Why: poke worker 只做 `merge --ff-only`（fleet-hot-sync 也禁 rebase，C-20261104 硬法）。 一台机一旦 ahead>0（本地攒了记账提交），ff 永远失败 -> 它 |
| `Tools/fleet/inventory_guard.py` | inventory_guard.py - the "no machine may sit idle" gate (bm-m master). Root cause it closes (2026-10-30): supply, promotion and claiming each broke silently at  |
| `Tools/fleet/local_judge.py` | local_judge.py - answer the smart-tier judgment queue, and escalate what is beyond it. CEO 2026-11-01: 「你做的事情不要超过你的能力，要上云还是上云，不要频繁触发硬盘交换，合理使用 你 macbook 的算力」。So  |
| `Tools/fleet/model_plan.py` | model_plan.py - 模型侧排班体检：现在驻留多少、超没超预算、矩阵与策略是否一致。 Why: 2026-11-07 实测三模型同时驻留 10.4GB（其中 3.7GB 是不该常驻的备用档），根因是 两份策略文件各写一个"现役模型"，且驻留判据用同族前缀。这台机器每天核对三件事， 让"合理安排"不靠人记： 1 |
| `Tools/fleet/ops_metrics.py` | ops_metrics.py - 三块缺失维度的度量：允许失败率(SLO)、产物质量(rubric)、成本归因。 为什么要有它：此前只有二元绿。偶发失败会误触发停线，系统性劣化却每轮都"绿"。 外部调研（LangChain/StackAI/Google SRE）一致的三条： 1. 故障常藏在 HTTP 200 背后 - |
| `Tools/fleet/prompt_en.py` | 把 ASSET-PROMPTS 里的中文提示翻成 SDXL 读得懂的英文标签，结果落 PROMPTS-EN-v1.json 缓存。 SDXL 的 CLIP 基本读不懂中文，直接用中文提示出图会跑题（实测把道具画成街景）。 本机有 ollama 时用它做转换；没有就直接跳过，调用方回落中文原文。 用法： python T |
| `Tools/fleet/regression.py` | regression.py - 回归用例集：把踩过的每个坑变成一条会自动跑的断言。 为什么要有它：这几天修了上百处，每次都靠当场验证。改一个地方碰坏另一个地方没人知道， 于是"修了 13 次还是老问题"。这个文件把历史故障固化成用例，每次改码后跑一遍。 用例设计原则（负控优先）： * 每条都必须能在 3 秒内跑完、不联 |
| `Tools/fleet/repo_layers.py` | repo_layers.py - 管住"新文件落在哪一层"，而不是搬家。 背景：6102 个跟踪文件里 4300 个在 cph4/fleet，根下平铺 164 个且还在长；冲突 96% 来自 状态与代码混放。批量搬家会制造一波断链（这些文件被脉/卡/文档引用），所以先用闸管增量。 检查项（都能在本地算）： C1 根下小 |
| `Tools/fleet/rmbg_matte.py` | 用本机 BRIA RMBG-1.4 权重给图片抠出透明底（离线，无需登录）。 ComfyUI 的 BRIA 节点需要登录，但 models/rmbg 下的权重是完整可用的， 直接用 ComfyUI 自带的 torch 环境加载即可。GPU 被 ComfyUI 占满时可 --cpu。 用法（必须用 ComfyUI 的 p |
| `Tools/fleet/root_cause_audit.py` | root_cause_audit.py - 六条根因的复验器（判「已治」只认这台机器）。 为什么要有它：这段时间修了几十处，但每次都是"修完自己说修好了"。根因账不靠声明， 靠每天复验——治好了是 PASS，没治好就点名是哪条根因复发、证据是什么。 R1 单一真相源 R2 生成态进 git R3 假绿判据 R4 修复未 |
| `Tools/fleet/security_ledger.py` | security_ledger.py - 安全与供应链台账：把写在文档里的红线变成每天可算的数字。 四类检查（都能在本地算，不联网）： 1. 凭据泄漏：git 跟踪文件里出现 sk-/ghp_/AKIA/xoxb/私钥块 -> 高危 2. 越权动作：队列卡的命令触碰受保护路径（凭据目录、.git 内部、系统目录） 3. |
| `Tools/fleet/self_improve.py` | self_improve.py - 机队自改（runs ON THE WORKER BOX, by the lane agent). CEO 2026-11-06: "你不仅要自己改进，主要是拉着机队一起改。" Each box fixes its own three chronic defects instead o |
| `Tools/fleet/skill_rollout.py` | skill_rollout.py - 一台机上的技能对齐（质检 → 安装 → 回执）。 为什么要有它：技能源在 cph4/skills/（随 git 分发），但只有装进本机激活面 （~/.codely-cli/skills/）才会被真正激活——"仓里写得再好，没装=不存在"。 机队每台机都要能自己跑这一步，并且留下** |
| `Tools/fleet/tts_batch_check.py` | tts_batch_check.py - prove a TTS batch actually produced audio, from any box. Why: on 2026-10-31 a claim (Q-TTS-1202R) sat in RUNNING for two hours with no lane |

## 怎么用这份清单
先按职责关键词找工具，再用 `--help` 看参数；工具缺输入时应当 rc=3 而不是伪造产物。

## 我不知道的
各工具在远端机器上的实际版本可能落后于本仓。
