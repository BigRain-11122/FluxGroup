# LoRA 训练 nan 的真根因：窗口饿死（2026-11-20 实锚）

## 一、现象

- `peer_pro` 与全量卡 `__all__`：**iter 5 就 nan**，连跑两轮都一样。
- `tech_nerd`：同一脚本、同一超参、同一机器——正常收敛。
- 直觉会把锅甩给 lr / 数据质量 / 段内样本少，全部错。

## 二、根因

我上一版把"人味要求"写进 `train_build.INSTRUCTIONS`（训练与线上单源），user 侧样本
涨到 **369 字**。而训练参数是 `--mask-prompt` + `--max-seq-length 224`：

> user 段先把 224 个 token 吃满 → **assistant 整段被截掉** → 该条样本里没有一个
> 可学习的 token → loss 无定义 → nan。

nan 出在 iter 5 而不是 iter 1，是因为随机采样先抓到几条短的；一旦连续凑齐几条长样本就炸。

## 三、为什么"只有某几个段 nan"

不是"这几个段数据差"，而是**这几个段的 user 侧更长**（指令 + 视频标题/简介/话题更啰嗦）。
所以判据是：

- 逐段出现的 nan → 先打印**该段样本截断后的 user/assistant token 数**，不要先调 lr；
- `--mask-prompt` 会全额吃掉 user 侧长度，永远要预留 assistant 的空间预算。

## 四、修法（不砍内容）

1. 序列上限 **224 → 320**；实测 RSS 3.5GB、val 3.76 正常收敛（16 层 @320 仍在 32GB 内）。
2. 造集侧加硬上限 `MAX_USER=240`，超了截断而不是让训练器去截 assistant。
3. 两层都要：只抬 seq 会随指令变长再次触顶，只加 MAX_USER 会切掉必要上下文。

## 五、通用判据

**loss=nan 时第一问不是"学习率多少"，而是"这一条样本的窗口里还剩几个 assistant token"。**
配套：任何"把要求写进指令"的改动，都必须同时检查**指令长度 × 序列上限 × mask 策略**三者乘积，
否则改文案就能把训练跑挂，而且报错信息只有 `nan`。

## 六、证据指针

- 训练台 `Tools/fleet/train_lora.py`（`--max-seq-length`、`--mask-prompt`）
- 造集 `Tools/fleet/train_build.py`（`INSTRUCTIONS`、`MAX_USER`）
- 急停：loss 出现 nan/inf 立刻杀进程记 `rc=4`（见 `topics/compute-scheduling-time-slicing.md`）
