# 本机 agent 车道（11436）：设置、实测与用法

> 结论：本机可以跑 32k 上下文的 agent/长文请求，但**必须走独立单槽车道**——
> 机队档（11434，NUM_PARALLEL=3）下 32k 要 13.1GB 且会被调度器驱逐；单槽只要 **7.7GB**。

## 一、为什么要两条车道

| 车道 | 端口 | 配置 | 干什么 |
|---|---|---|---|
| 机队档 | 11434 | parallel=3, ctx=8192, max_loaded=4 | 机队并发小请求（分类/摘要/判重/网关借用） |
| agent 档 | **11436** | **parallel=1, ctx=32768, max_loaded=1, KV q8_0** | 长上下文单请求（DSH/agent、整份系统提示、长文阅读） |

同一台 32GB 机器上，32k 的 KV 在 3 槽下按 98,304 上下文预估 18.4GiB（触发驱逐）；
单槽只算 32,768，实测 **7.7GB**，能和机队的 4B 共存。

## 二、设置（已落地/可落地）

- 端点账本：`cph4/fleet/LOCAL-ENDPOINT.json`（唯一来源：哪个端口服务哪类活）
- 启动器：`Tools/fleet/agent_lane.sh`（`start|stop|status`，默认 11436）
- 模型：`qwen3:8b-dsh32k`（`FROM qwen3:8b` + `num_ctx 32768`），基础模型 `qwen3:8b`
- DSH 路由：`Tools/fleet/dsh_local.py install --base http://127.0.0.1:11436 --parallel 1`
  生成 `ollama-local` 路由（32k、reasoningEfforts 映射、timeout 600s）

## 三、实测（2026-11-09 14:5x，M1 Pro 32GB）

| 测试 | 输入 | 结果 |
|---|---|---|
| DSH 真实系统提示（54,909 字符） | 12,938 token | **冷启 81.1s / 热态 4.0s**，占用 7.7GB，无驱逐 |
| 工程理解（AI.md 全文 + 三问） | 4,946 token | **40.6s**，311 token；七条业务线/仓库路径、CPH4 第一职责、机队节点**全部答对** |

热态 4s 的原因：同一前缀走 Ollama 的 prefix cache，只有新增 token 需要预填。
这改变了上一轮的结论——**不是"单步 2.5 分钟"，而是冷启约 80s、之后每步几秒到十几秒**。

证据：`cph4/fleet/state/repo-map/agent-lane-test.json`。

## 四、用来读工程

```bash
Tools/fleet/agent_lane.sh status                      # 车道在不在
OLLAMA_URL=http://127.0.0.1:11436 \
  python3 Tools/fleet/repo_map.py run --tier 1 --model qwen3:8b-dsh32k --limit 20
```

`repo_map` 与 `local_model.py` 都认 `OLLAMA_URL`，换车道不用改代码。

## 五、边界（诚实版）

- **单槽**：同一时刻只服务一个请求；DSH 和长文批处理不能并行。
- **质量**：8B 能做事实抽取与摘要，但多步工具调用会跑偏；DSH 用它要有心理预期。
- **内存**：7.7GB + 机队 4B（约 5–9GB）+ 办公 ≈ 15–18GB；swap 起来就停车道。
- **上下文**：32k 刚够 DSH 系统提示（12.9k）+ 若干轮；长会话会被截断，需要在 DSH 侧控轮次。
- **35B**：本机没装；目录里的 35B 已从 8088 页面移除（假绿修复）。


## 六、已落地的设置（2026-11-09 14:5x）

| 项 | 状态 |
|---|---|
| 单槽车道 | com.fluxgroup.agentlane（launchd，KeepAlive，端口 11436），重启自动起 |
| 端点账本 | cph4/fleet/LOCAL-ENDPOINT.json |
| DSH 本地路由 | ~/.dsh/profiles/desktop/cordis.patch.yml 里的 ollama-local（baseURL 11436/v1，32k） |
| DSH 默认模型 | 已切到 ollama-local / qwen3:8b-dsh32k；重启客户端生效 |
| 回云端 | python3 Tools/fleet/dsh_local.py default --cloud（或模型选择器切 deepseek-flash） |
| 备份 | cordis.patch.yml.bak-20261109-145623 |

## 七、DSH 形态的调用测试

| 测试 | 结果 |
|---|---|
| 系统提示 54,909 字符 + 工具定义，要求调用 bash | 5.7s，返回合法 tool_calls: bash({"command":"pwd"}) |
| 系统提示热态复跑 | 4.0s（prefix cache 命中） |
| AI.md 三问（七条业务线/CPH4/机队） | 40.6s，311 token，答案与原文一致 |
| 机制总图（14KB）层级复述 | 见 cph4/fleet/state/repo-map/agent-lane-test.json |

## 八、如果 8B 跑 agent 不行

不要硬扛。按顺序退回：
1. default --cloud 恢复云端默认（一条命令）；
2. 或保留本地路由但默认云端，在模型选择器里按需切本地；
3. 想要"本地且强"：等 bm-d（3×V100，35B）上线，把它挂成第二条 pi-ai 路由即可，客户端不用改。

