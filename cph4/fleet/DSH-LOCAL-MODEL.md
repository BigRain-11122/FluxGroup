# DSH × 本机 Ollama 接入说明（2026-11-08）

> 目的：让 DeepSeek Harness（DSH）客户端能在本机模型上跑，尽量不走云端。
> 机器面 = `Tools/fleet/dsh_local.py`；本文件只写结论、约束与操作，不复制阈值。
> 单一事实源：模型职责/阈值仍在 `cph4/fleet/LOCAL-MODEL-POLICY.json`，这里只做「接入」。

## 一、结论先说

本机 Ollama 可以用，但**不能直连**：DSH 一次请求的系统提示约 5.7 万字符（≈1.9 万 token），
而本机 Ollama 默认上下文只有 4096。直连的结果不是报错，是**静默截断**——模型只看到末尾一小段，
看起来在答，其实没读到指令和工具表。

所以适配分两步，都在 `Tools/fleet/dsh_local.py` 里：

1. **上下文变体**：`ollama create qwen3:8b-dsh32k`（`FROM qwen3:8b` + `PARAMETER num_ctx 32768`）。
   不改 plist、不重启 Ollama、不动机队正在用的常驻档。
2. **本地路由**：往 `~/.dsh/profiles/desktop/cordis.patch.yml` 写入一条 `dsh-llm-pi-ai` 路由
   `ollama-local`（OpenAI 兼容 `/v1`），**默认模型保持云端不变**；重启 DSH 后在模型选择器里手动切。

## 二、实测事实（2026-11-08 00:0x–00:2x）

| 事实 | 证据 |
|---|---|
| Ollama 0.40.13，OpenAI 兼容 `/v1/chat/completions` 可用 | 直接 curl 200 |
| 工具调用可用（OpenAI 格式 `tool_calls`） | qwen3.5:4b / qwen3:8b 均返回合法 `list_dir` 调用 |
| **OpenAI 端点忽略 `num_ctx`** | body 带 `num_ctx` / `options.num_ctx` 均无效，`/api/ps` 仍是 4096/8192 |
| 默认上下文来自 plist `OLLAMA_CONTEXT_LENGTH=4096` | `~/Library/LaunchAgents/com.fluxgroup.ollama.plist` |
| 常驻档实测上下文 8192 | `/api/ps`（`qwen3.5:4b`，约 11.7GB） |
| `PARAMETER num_ctx` 变体可覆盖默认值 | 见 `dsh_local.py prepare` 建出的 `qwen3:8b-dsh32k` |
| 本机模型当时被机队占用 | 日志里 17–42s 的 `/api/chat` 连续不断，外部请求排队 |

补充：MLX 变体（`-mlx`）会静默忽略 `format`（JSON schema），要结构化输出用 GGUF 变体；
这条与 `cph4/fleet/LOCAL-LLM-ROLE-20261103.md` 一致，不在这里另立规则。

## 三、怎么用

```bash
python3 Tools/fleet/dsh_local.py probe       # 只读体检：版本/模型/驻留/上下文告警
python3 Tools/fleet/dsh_local.py prepare     # 建 qwen3:8b-dsh32k（幂等，已存在就复用）
python3 Tools/fleet/dsh_local.py install     # 写入 DSH 本地路由（自动备份 cordis.patch.yml）
python3 Tools/fleet/dsh_local.py status      # 看装了没、默认模型是什么
python3 Tools/fleet/dsh_local.py uninstall   # 移除本地路由（同样先备份）
```

写入后：

1. 完全退出并重开 DeepSeek Harness（配置在启动时装载）。
2. 模型选择器里出现 **「本地 Ollama（bm-m）」→ `qwen3:8b-dsh32k`**，选中即走本机。
3. 想回云端：切回 `deepseek-flash`；或 `uninstall` 后重启。

### 想直接把默认模型改成本地

把 `cordis.patch.yml` 里 `agent-default-model` 的 `provider/model` 改成：

```yaml
- id: agent-default-model
  name: "@deepseek-ai/dsh-agent-default-model"
  config:
    provider: ollama-local
    model: qwen3:8b-dsh32k
    reasoningEffort: off
```

再重启。**不建议现在切**：本机模型正被机队自动化占用，且 8B 的 agent 能力明显弱于云端。

## 四、边界（诚实版）

- **竞争**：走 `127.0.0.1:11434` 的请求不经过 `Tools/fleet/local_model.py` 的「让路」信号，
  也不会经过 11435 网关的并发/白名单闸。机队忙时，DSH 的本地请求会排队。
- **速度**：qwen3:8b 在本机实测解码约 12–21 tok/s（受负载影响），一次 agent 回合可能几十秒。
- **能力**：4B/8B 做多步工具调用容易跑偏；适合轻量会话、离线、隐私场景，不适合替代重活。
- **内存**：32k 上下文的 KV 会明显大于 8k；`OLLAMA_NUM_PARALLEL=3` 会按槽位放大占用，
  切换前先看 `probe` 与 `vm_stat`，swap 起来就退回云端。
- **卸载**：`ollama rm qwen3:8b-dsh32k` 可删变体（不影响 `qwen3:8b` 本体）。

## 五、下一步（待 CEO 定）

1. 只想「能调」：按上面 install 即可，默认仍云端。
2. 想「默认本地」：改 `agent-default-model`，并接受速度/能力下降。
3. 想让本地调用也受机队优先级保护：把 DSH 的 baseURL 指到一个注入 `num_ctx` +
   `local_model.hold()` 的小代理（本次未做，避免多一个常驻进程）。
