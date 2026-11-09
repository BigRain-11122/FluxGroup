# 本地大模型盘点（2026-11-09 实测）

> 机器：MacBook Pro M1 Pro / 32GB（bm-m，集团主控）。
> 服务：Ollama 0.40.13，`127.0.0.1:11434`，plist 托管（`OLLAMA_CONTEXT_LENGTH=4096`、`NUM_PARALLEL=3`、`MAX_LOADED_MODELS=4`、KV q8_0）。
> 速度口径：预热后解码段，2 次取第二次；当时机队有并发，绝对值只做同批比较。

## 一、能用的模型

| 模型 | 大小 | 量化/引擎 | 能力 | 实测解码 | 适合 |
|---|---|---|---|---|---|
| `qwen3:1.7b` | 1.36GB | Q4_K_M / ggml | tools, think | **49–54 tok/s** | 批量分类、打标、快筛 |
| `qwen3:4b-instruct` | 2.50GB | Q4_K_M / ggml | tools, think | **19.3 tok/s** | 结构化输出、摘要、判读（`format` 生效） |
| `qwen3:4b` | 2.50GB | Q4_K_M / ggml | tools, think | 未单测（同 4B 档） | 通用轻任务 |
| `qwen3.5:4b-mlx` | 3.97GB | nvfp4 / **mlx** | vision, think, tools | **24.0 tok/s** | 常驻主力（策略 `resident`） |
| `qwen3.5:4b` | 3.97GB | nvfp4 / mlx | vision, think, tools | 未单测（同族） | 与 mlx 同档 |
| `qwen3.5:2b` | 3.12GB | mxfp8 / mlx | vision, think, tools | 未测 | 更轻的视觉/快答 |
| `qwen3:8b` | 5.23GB | Q4_K_M / ggml | tools, think | **13.1 tok/s** | 质量档、长文/复核（策略 `big`） |
| `qwen3-embedding:0.6b` | 0.64GB | Q8_0 / ggml | embedding | **1024 维，L2=1.0** | 判重/检索 |
| `qwen3:8b-dsh32k` | 5.23GB | Q4_K_M + `num_ctx 32768` | tools, think | 单槽 7.7GB | **agent 车道默认**（11436，见 `docs/local-llm-agent-lane.md`） |

实测批次（10:12–10:15，同一提示"用一句话说明什么是缓存穿透"，`num_ctx=4096`、`num_predict=96`）：

| 模型 | 第 1 次（冷） | 第 2 次（热） |
|---|---|---|
| qwen3:1.7b | 9.9s / 49.4 tok/s | 0.8s / 53.6 tok/s |
| qwen3:4b-instruct | 14.3s / 11.8 tok/s | 2.2s / 19.3 tok/s |
| qwen3.5:4b-mlx | 1.8s / 23.7 tok/s | 1.7s / 24.0 tok/s |
| qwen3:8b | 8.5s / 7.4 tok/s | 2.7s / 13.1 tok/s |

## 二、策略里的座位（单一源：`cph4/fleet/LOCAL-MODEL-POLICY.json`）

| 座位 | 模型 | 用途 |
|---|---|---|
| `resident` | `qwen3.5:4b-mlx` | 摘要/抽字段/短判定（未知 cls 都走这里） |
| `triage` | `qwen3:1.7b` | 归类/打标/过筛 |
| `big` | `qwen3:8b` | 质量复核、长文改写、代码审查 |
| `longform` | `qwen3:8b` | 长文/改写按需 |
| `embedding` | `qwen3-embedding:0.6b` | 语义判重/检索 |
| `sealed` | `qwen3.5:35b-a3b` | 封存（驻留即 swap，未安装） |

**重要缺口**：`Tools/fleet/web_ai.py` 的目录把 `qwen3.5:35b-a3b` 标成 `available: true`，但 `ollama list` 里**没有这个模型**。
8088 页面选它会在拉取/调用时失败——和 R3"看起来绿"同类，建议把 `available` 改成按 `/api/tags` 实测。

## 三、能干什么、不能干什么（结合实测）

- **能**：批量摘要/分类（1.7B 50 tok/s）、结构化 JSON（4B-instruct，GGUF 的 `format` 生效）、向量判重（0.6B，1024 维）、24 tok/s 的常驻轻问答。
- **不能**：当 DSH/MSH 这类 agent 的主脑——需要 1.9 万 token 系统提示 + 32k 上下文，
  32k 变体要 13.1GB，和 `NUM_PARALLEL=3` 叠加会被调度器驱逐（见 `docs/local-llm-dsh.md`）。
- **MLX 坑**：`-mlx` 变体静默忽略 `format`（JSON schema）；要结构化输出走 GGUF。
- **默认上下文只有 4096**：任何长文任务必须显式传 `num_ctx`（OpenAI 端点不认这个参数，得走 `/api/chat`）。

## 四、建议的用法边界

1. 机队/脚本：一律 `Tools/fleet/local_model.py`（带让路信号）或 11435 网关（token+并发+白名单）。
2. 批量读文档/分块理解：`Tools/fleet/repo_map.py`（tier1 用 4B，tier3 用 1.7B），单并发、可断点续跑。
3. 重活/长上下文/agent：仍走云端或等 bm-d（3×V100，35B 局域网）上线。
4. 别直连 11434 跑长上下文：会绕过并发与内存闸，且 4096 默认值会静默截断。
