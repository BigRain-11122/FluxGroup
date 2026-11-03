# 本地推理栈优化面全表（2026-11-03 实测）

> 起因：CEO 两次问「本地算力/MLX 的优化做了吗」，我两次都只做了被点名的那一项。
> 这里把**整条本地推理栈的优化面**一次列全并逐项实测，以后被叫去调研就照表扫，
> 不再等 CEO 一项一项点。
> 机器面：`cph4/fleet/LOCAL-MODEL-POLICY.json`｜每日复验：`Tools/fleet/model_radar.py run`

## 一、已实测并已生效

| 项 | 原来 | 现在 | 实测依据 |
|---|---|---|---|
| 推理引擎 | llamacpp（Metal） | **MLX**（qwen3.5:4b-mlx，nvfp4） | 38.1–40.0 vs 35.9–37.4 tok/s，黄金集同为 6/8 |
| 模型名来源 | 散在 6 个工具里 | `LOCAL-MODEL-POLICY.json` + `model_policy.py` | 改策略后四处调用点实测全部跟随 |
| 前缀缓存 | 未治理 | 已生效（命中时预填 15k tok/s） | 同一前缀第二次调用 420 → 15,615 tok/s，墙钟 2.89 → 0.45s |
| 结构化输出 | 怀疑 MLX 不支持 | 已验可用 | `format=json` 返回可解析，取到 action/why |
| 并发（NUM_PARALLEL） | 3 | **1** | 并发 3 个 4.15s vs 串行 4.13s，解码同为 34.5 tok/s → 并发不加速，只多占 KV |
| 常驻（KEEP_ALIVE） | 默认 5m（每 5 分钟正好过期） | **15m** | 冷载 load 1.42s / 总 2.23s vs 温态 0.73s |
| 服务归属 | Ollama.app 的 job 占着 127.0.0.1:11434，**我调的环境变量全都没生效** | 我们的 launchd job 独占 11434，app job 已 disable | `lsof` 实证；`launchctl print-disabled` 里 com.ollama.ollama=disabled |
| 向量层模型 | nomic-embed-text | **qwen3-embedding:0.6b** | 80+80 对：间隔 .586 vs .380；真重复三例 .953/.939/.830 全中；旧模型在真队列上把「MV 交付闸」和「音色数据集」误聚，新模型 0 假聚 |
| 去重阈值 | 报告 .61 / 挡活 .75 | **.72 / .80** | 同上实测；挡活阈值偏保守（误杀丢真活，漏判只多跑一张卡） |

## 二、已实测但**不改**

| 项 | 实测 | 为什么不动 |
|---|---|---|
| 提示词顺序（稳定块前置） | 新写法墙钟 0.59–0.66s vs 旧 0.77s | 只值 0.1–0.2s，且 ollama 已自动命中前缀缓存；改所有提示词不值得 |
| num_ctx 8192 | 我们的提示词 ≤1.2k token | 降 ctx 省的内存不足以补偿长文卡被截断的风险 |

## 三、还没做（列明触发条件，不许假装做了）

| 项 | 现在 | 什么条件下做 |
|---|---|---|
| `iogpu.wired_limit_mb` | 默认 0 | 只有在要跑 22GB 封存档（35B-A3B）且实测换页时；需 sudo，改完要回读验证 |
| KV cache 量化 | llamacpp 用 q8_0；MLX runner 不暴露 | 若 ollama 后续暴露 MLX KV 参数 |
| prefill_step_size / draft 投机解码 | 不暴露 | 只有转 mlx_lm 直跑路线才谈；先测「直跑比 ollama 快多少」再决定要不要多维护一条链 |
| MLX 下并发批处理收益 | 已测 4B 无收益 | 换更大模型（8B+）时重测一次 |
| mlx_lm 直跑 vs ollama | 未测 | 当出现「ollama 不支持的采样/量化需求」时 |

## 四、方法铁律（都是踩坑换来的）

1. 比版本：用 manifest 自身 digest 跟本地比；拿 `config.digest` 比会永不相等 → 每个模型都报“有更新”。
2. 比速度：先预热；只算 `eval_duration/eval_count` 的解码段；多次取中位；绝对值跨 session 不可比。
3. 比质量：黄金集题目必须**自带证据**，测“照做/拒答”，不测它认不认识我们的项目。
4. **先查 runner 实况再答**（`ollama ps` 的 RUNNER 列 / server.log），别按版本号猜。
5. 同一台机上「谁在监听 11434」决定环境变量生不生效——先用 `lsof` 确认再调参。