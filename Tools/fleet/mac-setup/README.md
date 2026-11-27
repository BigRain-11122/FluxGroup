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

它做三件事：克隆（稀疏）→ 生成一个**按需运行**的 `tools-run-once.sh` → 打印用法。

**默认不常驻**（CEO 2026-10-29：笔记本不当 24/7 机器）。要用的时候跑一次：

```bash
bash ~/FluxGroup/tools-run-once.sh
```

它做一轮：上报心跳 → 跑一次调度（现在会打 STANDBY）→ 领一件轻活干完就退出，不驻留任何后台服务。合上盖子就停，插电后就接着用。

真的想让它常驻（不建议），才加 `INSTALL_DAEMON=1 bash setup-mac.sh`，那会装一个每 10 分钟醒一次的服务。

## 三、装完还要手动一件

**Tailscale**：装好、加入同一个 tailnet，把机器名告诉我（我写进机队名册，它才会被当成在线）。

不需要 `caffeinate`，也不改电源设置——不常驻就不需要一直醒着。

## 四、验证

```bash
bash ~/FluxGroup/tools-run-once.sh
# 期望看到：STANDBY node=bm-m declared_master=bm-a
```

STANDBY 是**正确状态**：总控现在还是 bm-a。Mac 只读、不写队列，先观察一段时间。

## 五、什么时候切主控

观察 24 小时没问题后，改 `cph4/fleet/MASTER-NODE.json` 一行：

```json
{"node": "bm-m"}
```

commit 之后，bm-a 下一轮自动打 STANDBY，Mac 接管。**同时只有一个总控**，不会两边抢活。

## 六、本地模型（32GB 统一内存，可以放大）

32G 统一内存能跑 14B～27B 的量化模型（4-bit 约 8–16GB），文本/摘要/改写这类活质量会明显好于 4B。按需装一个主用模型即可：

```bash
brew install ollama && ollama serve &
ollama pull qwen3:14b        # 或 27B 的 4-bit 量化；车道自动取本机最大的那个
```

模型名**不用写进配置**——车道会自动取那台机器上最大的模型。要省空间就别多装，一个够用。

## 七、不要装在 Mac 上的东西

ComfyUI / Unity / 模型权重全集 / 媒体素材 / 游戏工程。这些属于 bm-a/bm-b/bm-c/bm-d。