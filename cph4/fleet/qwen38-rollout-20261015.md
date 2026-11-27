# 机队 Qwen 换装与 AI 大脑总体方案（O-20261015-1335 执行档·v3 终局·CEO 已批「同意，全部执行」2026-10-15 15:2x）

> 溯源：CEO 现场令 2026-10-15——「本地的大模型 给我换成最新的QWEN 能用好用顺的」+「按机队机器配置和任务科学分配」+「工作日工作时间把本机算力给我腾出来」+「同意，全部执行」（八点优化全批）。
> 根因收口实录：10-14 已删 qwen2.5 全款（38.6G），但消费方硬编码（gen_storyboard=qwen2.5:14b）与 flash 槽引用（qwen2.5:7b-instruct）把旧款自动回拉复活两度——本批消费方全部改新接线后复删，根因物理切除。
> 权威序：架构正典=cph4/fleet/FLEET-COMPUTE-ARCHITECTURE.md v2（四机一云总架构）；模型阵容正典=cph4/fleet/hardware/V100-RIG-MODELS-20261014.md；本文=换装执行+机队模型分配+八点优化落地档。

## 一、bm-a v3 终局架构（2026-10-15 实弹完成·四车道全绿）

| 车道 | 消费方 | 脑子 | 端点/参数 | 实测锚（10-15） |
|---|---|---|---|---|
| BigLife 年轮 | evolve_citizen.py / citizen_qa.py | **Qwen3.6-35B-A3B :8090** | OpenAI wire + `chat_template_kwargs.enable_thinking:false`·env `BIGLIFE_LLM_URL`/`BIGLIFE_MODEL` | 年轮在persona·排队竞发时可至 80s+（-np 2 槽·批任务预算内） |
| MV 分镜 | gen_storyboard.py | 同上 | env `STORYBOARD_LLM_URL`·max_tokens 2000·超时 600s | 2镜 JSON 10.3s 干净无泄漏 |
| 城市问答网关 | resident_qa_server.py :8792 | 同上 | env `RESIDENT_QA_LLM_URL`·荣誉席/白名单门禁照旧 | 真召见 10.8s 人味足·AIGC 标识合规 |
| BigMoney 顾问 | llm_assist.py | **qwen3:4b-instruct（Ollama）** | `BIGMONEY_LLM_MODEL`+`BIGMONEY_LLM_ROUTE=local`（bm-c C 通道 10-14 撤站后死引收口） | serve 活时秒回 |
| Codely flash 槽 | settings.json | **qwen3:4b-instruct（Ollama）** | `flashModel`·OpenAI wire | 零思考泄漏 |
| 嵌入 | 检索管线 | bge-m3 保持 | — | — |

- **旧款复删**：qwen2.5:14b / qwen2.5:7b-instruct 已 rm（白名单探针防复活，见 §三④）。
- **qwen3.8:27b 留盘休眠**（17G·bm-d 候补件）：稠密 27B 本机实测病态——prompt_eval 0.16tok/s（双 runner 互踩+与 35B+CEO 前台并存显存超卖）=「好用顺」物理不可达，判负留档。真实测数据：31tok 提示词 191.5s / 生成 3.6tps。
- **工作日白天 bm-a=CEO 专用**（铁原则①）：显存余量实测 9.6G 还给前台。

## 二、机队模型分配表（硬件 × 任务 × 模型）

| 机 | 硬件 | 分配 | 理由 |
|---|---|---|---|
| bm-a | 4070S 12G+94G | 文本四车道=:8090 35B-A3B（过渡脑·bm-d 到后迁出）；Ollama 只留 4b 速度槽+bge-m3；27b 休眠 | 12G 与 CEO 前台并存 = 稠密大模型物理不可驻（10-15 实证） |
| bm-b | 8G VRAM | 不驻大件：B站线=4b 派生（CPU-only·在位）；llm_assist 走路由 | 3.8 家族最小开源件 27B=18G>8G |
| bm-c | 3070 16G | 零 LLM 驻留维持（GPU=MV-only 红线） | O-20261014-1125 |
| bm-d（采购中） | 3×V100 16G=48G 池+256G DDR3（**无 AVX2=CPU 卸载禁用**） | 量产=Qwen3.6-35B-A3B Q4→Q8·深判=Qwen3.6-27B Q8·快档=Gemma4 26B-A4B QAT·嵌入=bge-m3 | V100-RIG-MODELS-20261014 三源正典 |
| 云端 | — | 天花板创作+失败重试（>500 积分 CEO 亲批） | 思考路由律 v2 |

## 三、八点优化落地（CEO 批「全部执行」10-15 15:2x）

| # | 优化点 | 落地件 | 状态 |
|---|---|---|---|
| ① | **让路排班自动化**：工作日 09:00 自动让 / 19:00 自动复工 | machine-state.ps1 **v5 新增 pauseLite 档**（重活全停·保 4b 轻面）+ 计划任务 `bm-a-AutoYield-WorkStart`(一~五 09:00) / `bm-a-AutoYield-WorkEnd`(一~五 19:00)；手动「pause/全面开工」两词照旧 | ✅ 已部署实弹验证（pauseLite OK heavy-clean vram 3176） |
| ② | **bm-d 前加 LiteLLM 网关**：统一入口+按业务记 token 账+优先级排队（直令>巡班>代理>批量）+本地失败自动转云+思考升档阶梯（35B 不思考→35B 思考→27B→云端） | bm-d 装机周接线标准（写入装机清单 §五）；现成轮子=codely 平台同款技术 | 🟡 待 bm-d 到货接线（规格已定） |
| ③ | **白天故障接管序修正**：bm-d 白天挂→云端经济档先顶门面（QA/裁决）→夜窗 bm-a 才接重批量 | 本档 §四 接管优先序（替代原「bm-a 承接」） | ✅ 本档定谳 |
| ④ | **旧模型复活探针**：每小时 Ollama 清单对白名单（bm-a={qwen3:4b-instruct, bge-m3:latest}）·旧款家族(qwen2.5/qwen3-8b-ud)自动删·白名单外新款只报不删（防误删） | Tools/model-whitelist-probe.py + 计划任务 `bm-a-ModelWhitelistProbe`(每小时)·日志 media/logs/model-whitelist-probe.log | ✅ 已部署 |
| ⑤ | **消费方全改 env 驱动**：bm-d 切换=每机改一行环境变量零改码 | STORYBOARD_LLM_URL / RESIDENT_QA_LLM_URL / BIGLIFE_LLM_URL（BigLife 两件已带）+ BRAIN_URL/FLASH_URL/QA_URL（冒烟件⑥） | ✅ 全部接线完成 |
| ⑥ | **换装回归冒烟常备化**：任何换模型五分钟出四车道绿红 | Tools/model-lane-smoke.py + 计划任务 `bm-a-ModelLaneSmoke`(周日 21:33)·四车道 A 年轮/B 分镜 JSON/C flash/D QA 网关 | ✅ 已部署 |
| ⑦ | **Qwen3.8-27B 到货双验**：sm_70 兼容+**视觉面**同验——过关=质量档升级+美术本地预审升级（3.8 原生看图） | 写入 bm-d 装机清单验收步（§五⑤） | 🟡 待 bm-d 到货 |
| ⑧ | **pause 分级**（CEO 已批）：pauseLite 档保 4b 轻面（城市参观问答工作日白天不黑窗）·手动 pause 仍全停 | machine-state.ps1 v5（同①） | ✅ 已部署 |

## 四、故障接管优先序（替代原「bm-d 挂→bm-a 承接」）

1. bm-d 白天挂 → **云端经济档**（豆包/DeepSeek 便宜档）临时顶门面车道（QA 网关/裁决/巡班判断）——花小钱保 CEO 随时看的面不断
2. 夜窗 → bm-a :8090 35B 承接重批量（:8090 服务与 pauseLite 兼容：白天让路自动停、夜里自动回来）
3. 他机照常运转；降智监控月度审计照旧

## 五、bm-d 装机周接线清单（增补·承接 V100-EXPANSION-SPEC/MODELS 正典）

1. 验机+驱动（CUDA ≤12.9·R580·禁 Ollama·llama.cpp 自编 sm_70）
2. 单卡 Gemma4 ≥80字/秒 → 双卡 35B Q4 全驻留 ≥70字/秒 → 三卡 Q8 跑通（验收线正典）
3. **② LiteLLM 网关**装在 bm-d：三 key + 按业务计量 + 优先级队列 + 云端 failover + 思考升档阶梯
4. 各机改 env 指向 bm-d（BRAIN_URL 族·一机一行）；bm-a :8090 退役→bm-a 释放纯中枢
5. **⑦ Qwen3.8-27B 双验**：sm_70 兼容 + 视觉面（mmproj）——过关→质量档升级+美术本地预审升级
6. 10 件真实任务盲测（本地 vs 云端·记档呈 CEO）→ 降智监控月度常设

## 六、10-15 工程坑实录（防复发·入档）

- Ollama keep_alive=-1 钉驻模型 `ollama stop` 卡死 "Stopping..." → 须强杀 Ollama 侧 llama-server runner（保 :8090 llamacpp 件）
- Ollama 按 options 差异（num_predict 等）各 spawn 独立 runner → 同模型双实例互踩（27B 0.16tok/s 病灶）
- 已删模型仍被 settings/脚本引用会被自动回拉 → 删旧必先切消费方（探针④兜底）
- wscript 壳计划任务 `schtasks /end` 杀不死孙进程 pythonw → PID 直杀
- PS5.1 会吃 python -c 内联引号 → 中文/复杂参数一律落 .py 文件跑（编码律同源）
