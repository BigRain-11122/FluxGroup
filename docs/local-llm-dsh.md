# DSH × 本机 Ollama：决策与证据（2026-11-08）

> 问题：要不要把 DeepSeek Harness（DSH）的模型从云端 `deepseek-flash` 换成本机 Ollama，做到"尽量不走云端"。
> 结论先行：**不换默认，也不装 32k 路由**。本机装不下 DSH 需要的上下文，硬切会驱逐机队模型。
> 机器面 = `Tools/fleet/dsh_local.py`（含体检/实测/安装/回滚，install 默认拒绝不安全配置）。

## 一、决定

| 项 | 决定 |
|---|---|
| DSH 默认模型 | 保持云端 `deepseek-flash` |
| 本地 32k 路由 | 不安装（`install` 会拒绝，需 `--force` 才写） |
| 本地模型用途 | 继续只做轻活：分类/摘要/判重/嵌入（现有 `Tools/fleet/local_model.py` + 11435 网关） |
| 何时重开 | 见 §四 的触发条件 |

## 二、四条硬证据

**1）直连会被静默截断。**
本机 plist 设 `OLLAMA_CONTEXT_LENGTH=4096`；DSH 一次请求的系统提示 5.7 万字符（≈1.9 万 token）。
OpenAI 端点**忽略** body 里的 `num_ctx`（带/不带，`/api/ps` 都是 4096/8192）——不报错，只是没读到指令和工具表。

**2）32k 变体装得上，但和机队抢内存会被驱逐。**
`qwen3:8b-dsh32k`（`FROM qwen3:8b` + `num_ctx 32768`）实测装载成功：`context_length=32768`、13.1GB。
但服务端 `OLLAMA_NUM_PARALLEL=3`，调度器按 32768×3=98,304 上下文预估 **18.4GiB**：

```
msg="llama-server model predicted to exceed available memory, evicting"
predicted="18.4 GiB" predicted_num_ctx=98304 available="16.8 GiB"
```

结果是刚装上的模型被踢掉，实测调用因此没跑完。**这不是配置错误，是内存装不下。**

**3）速度：单步分钟级。**
预填实测 140 tok/s → 1.9 万 token ≈ 136 秒；解码约 10–14 tok/s → 300 token 回复 ≈ 25 秒。
单步 ≈ 2.5 分钟；一次 20 步的 agent 回合 ≈ 40–50 分钟。云端同等工作量是秒级。

**4）违反本机章程。**
CEO 已定：bm-m 只做调度/监督/协调 + 常驻轻量模型（4B，≤8GB），重活 ROUTED。
一个 13GB+ 的 32k 模型会挤掉机队常驻档和办公内存，属于"硬扛 swap 换假绿"。

## 三、留下了什么

- `Tools/fleet/dsh_local.py`：`probe / prepare / bench / verify / status / install / uninstall`。
  `install` 读到 `NUM_PARALLEL` 与 ctx 的乘积超线时**拒绝执行**（本次就是被它拦下的），`--force` 可越过。
- 变体 `qwen3:8b-dsh32k` 保留（仅清单，不复制权重）。删：`ollama rm qwen3:8b-dsh32k`。
- 待应用配置已撤下：避免有人手滑 `cp` 进 `~/.dsh` 后驱逐机队。需要时 `install --force` 会重新生成。

## 四、什么条件下重开

1. **bm-d 上线**（3×V100，35B 在局域网 `<bm-d>:8090`）——DSH 路由到 bm-d，不走公网也不占本机；
   这是"不走云端"的正解，等它入网。
2. 本机内存 ≥64GB，或服务端 `NUM_PARALLEL` 降到 1 且机队接受吞吐下降。
3. 出现能在 ≤10GB 内跑 32k 的模型（当前 8B 需 13GB+）。

## 五、如果现在就要切（知情选择）

```bash
python3 Tools/fleet/dsh_local.py install --force   # 生成待应用配置
# 备份后覆盖 ~/.dsh/profiles/desktop/cordis.patch.yml，重启 DSH
```

代价：机队模型被驱逐、请求排队、单步分钟级、8B 多步工具调用易跑偏。
切回：`uninstall` 后重启，或模型选择器切回 `deepseek-flash`。

## 六、附：本机本地模型的正确用法

- 轻活优先：分类/打标/一句话理由 → `local_model.generate(cls="triage")`；判重/检索 → `embed()`。
- 结构化输出用 GGUF 变体；MLX 变体静默忽略 `format`（JSON schema）。
- 机队借用走 11435 网关（token + 并发 + 白名单 + 内存闸），不要直连 11434。
