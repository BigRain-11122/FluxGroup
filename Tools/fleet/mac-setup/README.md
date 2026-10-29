# MacBook 控制面安装包（bm-m）

> CEO 2026-10-29：Mac 只做**调度与 Agent 中心**，不干重活、不占硬盘。
> 本目录是唯一需要拷到 Mac 上的东西。

## 一、克隆哪个仓

**只克隆一个：`FluxGroup`。** 其余九个子公司仓（MiniGame / BigMoney / BigStream / BigDomain / BigCompute / BigLife / BigHouse / FluxVerse / BigMoney-data）**一律不要在 Mac 上 clone**——它们的媒体、美术、模型都在别的机器上，拉下来纯占空间。

`setup-mac.sh` 用 `--filter=blob:none` + sparse-checkout，只落地控制面：

| 落地 | 用途 |
|---|---|
| `Tools/fleet/` | 调度器、车道执行器、心跳、共享库 |
| `Tools/queue_claim.py`、`Tools/backlog_fill.py` | 车道领取与积压填充 |
| `cph4/fleet/*.json` `*.jsonl` `*.md` | 条线登记、模型策略、队列、总控声明 |
| `cph4/fleet/dispatcher/`、`lanes/`、`queue-receipts/` | 状态、派单、回执 |
| `docs/orders.md`、`AI.md` | 令台账与全局速览 |

不落地：`media/`、`gaming/`、`quant/`、`mv0001-handover/`、任何图片视频模型。**预计占用：几十 MB。**

## 二、装法（三行）

```bash
bash setup-mac.sh                      # 默认装到 ~/FluxGroup
ROOT=~/work/FluxGroup bash setup-mac.sh # 或自定义路径
```

它会做四件事：克隆（稀疏）→ 写两个 launchd 服务（调度每 2 分钟、心跳每 5 分钟）→ 加载 → 打印自检命令。

## 三、装完还要手动两件

1. **Tailscale**：装好、加入同一个 tailnet，把机器名告诉我（我写进机队名册，它才会被当成在线）。
2. **防休眠**：`caffeinate -dimsu &`（插电时常驻；合盖会睡，需要 `sudo pmset -c disablesleep 1`）。

## 四、验证

```bash
tail -n 20 /tmp/fluxgroup-master.log
# 期望看到：STANDBY node=bm-m declared_master=bm-a
```

STANDBY 是**正确状态**：总控现在还是 bm-a。Mac 只读、不写队列，先观察一段时间。

## 五、什么时候切主控

观察 24 小时没问题后，改 `cph4/fleet/MASTER-NODE.json` 一行：

```json
{"node": "bm-m"}
```

commit 之后，bm-a 下一轮自动打 STANDBY，Mac 接管。**同时只有一个总控**，不会两边抢活。

## 六、可选：本地模型

只做文本类活用，一个 4B～9B 足够（约 3–6 GB）：

```bash
brew install ollama && ollama serve &
ollama pull qwen3:4b-instruct
```

模型名**不用写进配置**——车道会自动取那台机器上最大的模型。要省空间就别多装，一个够用。

## 七、不要装在 Mac 上的东西

ComfyUI / Unity / 模型权重全集 / 媒体素材 / 游戏工程。这些属于 bm-a/bm-b/bm-c/bm-d。