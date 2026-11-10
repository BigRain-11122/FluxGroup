# 本机模型选型（2026-11-10 实测）

> 硬件：M1 Pro 32GB，Metal 池 ~25GB；Ollama 0.40.x。
> 场景：会话 agent（工具调用/长系统提示）+ 机队批处理（判读/摘要/验收）。

## 一、实测对比

| 模型 | 工具调用 | 摘要质量 | 摘要耗时 | 预填 4.6k token | 结论 |
|---|---|---|---|---|---|
| qwen3.5:4b-mlx（think=false） | ✅ | 好 | **3.1s** | ~15s | **首选** |
| qwen3.5:4b-mlx（think=true） | ✅ | 内容为空（全在 thinking） | 5.5s | — | 必须关思考 |
| qwen3:4b-instruct | ✅ | 好 | 6.1s | 14.9s | 备选/结构化输出 |
| qwen3:8b（GGUF） | ❌ 不发 tool_calls | — | — | — | 不适合 agent |
| qwen3:8b-dsh32k（GGUF） | 未通过（预填过慢） | — | — | >120s | 仅离线批处理 |

## 二、结论

- **会话模型**：qwen3.5:4b-mlx，**必须 think=false**（MLX 思考模式只出 reasoning、不出 content）；
- **机队批量**：同模型 + think=false；需要严格 JSON 时退回 qwen3:4b-instruct；
- **8B 不用在 agent 上**：工具调用不支持，且 32k 预填太慢；
- 上下文统一 32k，maxTokens 4096；会话首轮 15s 级预填，之后靠前缀缓存加速。

## 三、工作流优化（已落地/待落地）

1. 所有本地调用显式 `think:false`（fleet_lane 默认由 True 改 False）；
2. DSH 会话 `reasoningEffort: off`，避免把预算耗在思考上；
3. 车道 keep_alive 30m，避免反复冷加载；
4. 机队 4B 常驻 + 3 并行槽；会话用单槽，互不抢占；
5. 提示词保持稳定前缀（系统提示不变），让 Ollama 前缀缓存生效；
6. 会话超过 32k 前主动压缩（thresholdRatio 0.75）。

## 四、DeepSeek 开源蒸馏版（2026-11-10 决策）

- 满血 V3/R1 671B：Q4 约 380–400GB，32GB 机器无法加载，直接排除；
- 蒸馏版（R1-Distill-Qwen 8B/14B/32B）：内存可行，但属于**推理模型**，工具调用能力弱、预填慢；
- 定位：**只做夜间离线深度分析**，不参与 agent 会话；
- 车道：`deep_reason.py`，model=deep-reason 的卡，每天 00:40 起用 deepseek-r1:14b 跑，产出交付物；
- 与白天的 4B agent、机队批处理互不抢资源。

## 五、最终定型（2026-11-10 19:2x）

| 用途 | 模型 | 车道 | 参数 |
|---|---|---|---|
| 机队批量 | qwen3.5:4b-mlx | 11434 | 6 并行 / ctx 4096 / KV q8 / flash attention / keep_alive 30m |
| 会话 agent | qwen3.5:9b-mlx | 11436 | 1 并行 / ctx 32768 / KV q8 / keep_alive 30m / think=false |
| 夜间深度推理 | deepseek-r1:14b | 11436（00:40 起） | ctx 16384 / think=true / 单请求 |
| 向量 | qwen3-embedding:0.6b | 11434 | 按需加载，用完即卸 |

已删除：qwen3:8b、qwen3:8b-dsh32k、qwen3:4b、qwen3:5:2b、qwen3:1.7b、qwen3:4b-instruct、qwen3.5:4b（非 mlx 重复）。

内存：4B 约 12.6GB + 9B 约 9.0GB 常驻；向量仅在判重时加载；32GB 机器上不再额外驻留第三个大模型。
