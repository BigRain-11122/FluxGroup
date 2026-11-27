# 本地大模型最新进展速报 · 2026-11-19

> 距上次盘点 10 天。只记**会影响你选择**的变化，不罗列榜单。

## 一 结论先行

**你的 `qwen3.5:9b` 仍然是最优选择，不用换。**
理由是三条新证据，不是惯性。

## 二 这 10 天发生了什么

### 1. Qwen3.6 上线，但**只有大档位**
实测 Ollama 注册表：

| 模型 | 大小 | 能否进你 12GB |
|---|---|---|
| qwen3.6:27b | **17.77 GB** | ❌ 只能进内存（慢） |
| qwen3.6:35b / latest | **22.62 GB** | ❌ 只能进内存（慢） |
| qwen3.6 的 9b / 14b / 4b | — | **尚未发布** |

**⇒ 新一代来了，但没有适合 12GB 的档位。** 这一条很关键：**别以为新就一定好，尺寸不匹配就是跑不动。**

### 2. Qwen3.5 被外部独立确认为"8–12GB 显存的标准推荐"
第三方评测（2026）明确写：**"Qwen3.5-9B is the default recommendation for a modern computer with 16 GB RAM or a GPU with 8–12 GB VRAM"**。
**这和我上次给你实测的结论一致**——不是我说了算，是两条独立证据指向同一答案。

### 3. 11 月 17–18 日两家国内厂商发了新模型，但**还没进 Ollama**
- **商汤 SenseNova-Loop-9B**（11-17 开源，9B，32 层权重循环执行 56 次，同日上 AWQ 量化）
- **范式智能 Phai-A1**（11-18，百万 token 上下文，**声称可在个人电脑本地部署**）

**⇒ 值得盯，但现在装不了。** 等它们进 Ollama 或出 GGUF 再测。

### 4. 新出的、能进 12GB 的只有 gemma4
| 模型 | 大小 | 备注 |
|---|---|---|
| **gemma4:12b** | **8.02 GB** | 唯一新增可选项 |
| gemma4:latest | 6.58 GB | 同上系列 |
| glm4:9b | 5.46 GB | 中文强，老选项 |
| phi4:14b | 9.05 GB | 数学/推理强，中文一般 |

**gemma4 中文能力大概率不如 Qwen**，且 8GB 在你现在只剩 1.5GB 空闲显存的情况下也塞不进。

### 5. 大模型继续膨胀，和你无关
`ripple-preview` 38.8GB、`nemotron` 42.5GB、`lfm2` 14.4GB —— 都要 24GB+ 显存。

## 三 所以你的选择没变

| 档位 | 模型 | 状态 |
|---|---|---|
| **主力** | **qwen3.5:9b** | ✅ 已有，最优 |
| 快速 | qwen3.5:4b / 2b | ✅ 已有 |
| 夜间批量 | qwen3.5:27b | ⚠️ 已有但慢（单次 >20 分钟） |
| 备选（可试） | gemma4:12b | 新，中文待验证 |
| 待观察 | qwen3.6 小档 / SenseNova-Loop-9B / Phai-A1 | 未上 Ollama |

## 四 真正该做的事还是一件

**腾显存。** 上次实测：你的显存 12GB 里 **11.6GB 被飞书/Edge/4×EdgeWebView/Tuanjie 占着**，只剩 0.3–1.5GB。

**新模型再多，塞不进去也没用。**
关掉浏览器类程序 → 释放 8–10GB → **qwen3.5:9b 立刻从 0.6 tok/s 恢复到全速**。

## 五 建议动作（按性价比）

1. **不换模型**（省时间，省钱，没收益）
2. **用前腾显存**（唯一真正提升体验的动作）
3. **删掉上一代**：`qwen3:8b`、`qwen3:4b`、`qwen3:4b-instruct`（省 10GB 磁盘）
4. **27b 留着做夜间批量**，嫌占磁盘（17GB）可以删
5. **两周后再看**：qwen3.6 小档、SenseNova-Loop-9B、Phai-A1 是否进 Ollama

## 六 来源
- [Qwen3.5 发布与消费端 App（2026-11-17）](https://www.techjuice.pk/alibaba-qwen-app-launch-chatgpt-rival/)
- [本地模型消费级硬件推荐（Qwen3.5-9B 为 8–12GB 显存默认推荐）](https://shop.zimaspace.com/blogs/tech-ai-hub/best-ai-models-for-running-locally-on-consumer-hardware)
- [商汤 SenseNova-Loop-9B 开源（2026-11-17）](https://hub-assets-cache.baai.ac.cn/view/59775)
- [范式智能 Phai-A1 / Phai-M1（2026-11-18）](https://w.geekpark.net/news/374133)
- [Ollama 更新日志（2026-11-10）](https://raw.githubusercontent.com/duanyytop/agents-radar/refs/heads/master/digests/2026-11-10/ai-infra.md)
- 模型尺寸：本机实测 Ollama 注册表（2026-11-19）
