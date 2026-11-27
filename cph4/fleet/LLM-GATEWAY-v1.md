# 本地大模型对机队开放 · 网关 v1 — 2026-11-08

> CEO 原话：「我希望机队也能调用你的本地大模型能力」。
> 正身代码 = `Tools/fleet/llm_gateway.py`（服务）· `Tools/fleet/llm_selftest.py`（机检）
> 白名单唯一源 = `cph4/fleet/LOCAL-MODEL-POLICY.json`（代码内不写模型名）
> 守护断言 = RG-28（过网关/白名单/驻留策略）· RG-29（四态可机检）

## 1. 为什么不是直接把 11434 开出去

| 风险 | 裸 11434 | 网关 8792 |
|---|---|---|
| 无认证 | tailnet 上任何设备都能请求 35B（24GB）→ 主控换页 | `X-Flux-Token` 校验，无令牌 401 |
| 无白名单 | 机队写死的老模型名（`qwen3:4b-instruct`/`qwen3.5:4b`）会**另拉一份 4B 顶掉常驻主力** | 只放行策略里声明的模型，其余 403 |
| 无驻留策略 | 远端一句 `keep_alive=30m` 就把模型钉在内存 | `keep_alive`/`num_ctx` 由策略强制覆盖 |
| 无并发上限 | 多机同时打满，主控与 CEO 办公抢同一池内存 | 并发 2，超出 429 |

**11434 只绑回环，对外只有 8792 这一道门。**

## 2. 端点

- 服务地址：`http://100.75.133.10:8792`（bm-m 的 tailnet IP；改动后须同步本文件与 `fleet_lane.py`）
- 可通过路径：`/api/generate` `/api/chat` `/api/embed` `/api/embeddings` `/api/tags`（其余一律 404）
- 认证头：`X-Flux-Token: <令牌>`
- 服务：launchd `com.fluxgroup.llmgateway`（KeepAlive）；无令牌文件时**拒绝启动**（不许裸奔）

## 3. 允许清单（取自策略，勿手改此表）

| 模型 | 座位 | 用途 | 实际情况 |
|---|---|---|---|
| `qwen3.5:4b-mlx` | resident | 摘要/抽字段/写理由 | 常驻，ctx8192，约 3.9GB |
| `qwen3.5:9b-mlx` | big | 代码/评审/长文/评审团判卷 | 常驻，ctx32768，约 8.4GB |
| `qwen3-embedding:0.6b` | embedding | 向量 | 常驻，约 0.6GB |
| `qwen3.5:2b` | triage | 归类/打标/过筛 | 按需（MLX 不能写 0，`keep_alive=1m`） |

禁放行：`qwen3.5:35b-a3b`（驻留即 swap，已封存）、`qwen3:4b`/`qwen3.5:4b`（对照档，会顶掉主力）。

注：本表由策略推导，2026-11-14 随 `duties.big` 换档同步（原 `qwen3:8b` 已退役）。

## 4. 各机一次性准备（三行）

```bash
printf '%s' '<与主控同一串>' > ~/.fluxgroup-llm-token && chmod 600 ~/.fluxgroup-llm-token
export FLUX_LLM_BASE=http://100.75.133.10:8792     # Windows: setx FLUX_LLM_BASE ...
python3 Tools/fleet/llm_selftest.py                # 必须看到 OK
```

令牌**不入 git**、权限 600、与主控 `~/.fluxgroup-llm-token` 同一串（和 `~/.fluxgroup-asset-token` 同一套做法）。
本轮没有可用的加密分发通道（无 SSH/WinRM，卡片内容进 git=泄漏），所以这一步只能是**一次性带外准备**；
这是当前真实边界，不假装已有自动分发。

## 5. 机检：`llm_selftest.py`

四态返回码，**原因必须分清**，否则「没令牌」会被记成「网关坏了」：

| rc | verdict | 含义 | 该做什么 |
|---|---|---|---|
| 0 | `OK` | 生成成功且白名单负控通过 | 无 |
| 3 | `E-NO-TOKEN` | 本机没令牌文件 | **缺料**，去准备，不算故障 |
| 1 | `E-UNREACHABLE` | 连不上 8792 | 查 tailnet / 网关服务 |
| 1 | `E-BAD-TOKEN` | 401 | 本机串与主控不一致 |
| 1 | `E-MODEL-DENIED` | 403 | 档位不在策略里，改座位不要改网关 |
| 1 | `E-WHITELIST-LEAK` | 封存档被放行 | 严重：远端能拉野模型顶掉常驻，立刻查策略 |

`--json <path>` 出卡回执；`--skip-deny-test` 只在非主控机跑时用（少判一项）。
缺令牌返 3 而不是 1，是按「缺输入不计三次失败预算」的同一口径。

## 6. 已知边界

1. **主控离线即不可用**：模型在 bm-m 上，CEO 关机/休眠时网关跟着消失。要长期给机队用，得把 4B 镜像到一台 24h 生产机（bm-a）另起一门，这是下一步，不是当前状态。
2. **这是脑子不是画室**：4B/8B 只做分类/摘要/理由/短代码评审。批量出图、i2v、4K 转码一律不在本门后（会把办公挤到换页）。
3. **算数不交模型**：实测 4B 两次算术全错，任何数字由规则算，模型只给解释。
4. 并发 2：第 3 路 429。机队批量任务要排队，不许把 429 当失败重试轰炸。