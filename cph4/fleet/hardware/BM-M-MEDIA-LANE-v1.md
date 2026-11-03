# bm-m（MacBook M1 Pro）算力用法 v1（2026-11-03）

> CEO 令：「好好利用本地的算力去支持各个公司的业务，尤其是 MacBook」。
> 本件只写**能干什么、干多少、什么不许干**，数字都是本机实测，不引用别处。

## 一、硬件与实测天花板

| 项 | 事实 |
|---|---|
| 芯片 | Apple M1 Pro，10 核 CPU（8P+2E）/ **16 核 GPU** / 32GB 统一内存 |
| 当前余量 | CPU 空闲 69.6%，空闲内存 11.9GB（2026-11-03 18:22 实测） |
| 硬件编码 | h264/hevc/prores videotoolbox 全有；12 秒竖屏 1080×1920 片，wall **6.1s**、CPU 时间 **9.9s**（软件编码同片 11.9s / 87.6s，SSIM 0.990） |
| 审片副本 | 720p 一条 12 秒片 **1.16s**，6 条合计 7s |
| 语音转写 | whisper-large-v3-turbo（MLX/Metal），12 秒片 **2.5s**，约实时 12 倍 |
| 常驻模型 | 4B 量化 4.0GB 保活；再大的模型不驻留（32GB 与办公共用同一池） |

## 二、该干的五类活（对应各家业务）

1. **交付编码（全部公司）**：成片/代理片/审片副本一律 `h264_videotoolbox` 优先；只有交付兼容性问题才退回 `libx264`（`ASSEMBLE_ENCODER=libx264`）。
2. **字幕与语音质检（BigStream / 资产库）**：`subs_asr.py` 出字幕源、跑 CER 与语速抽检；脉冲 `asr_subs` 站每天只补缺的，一次最多 2 条。
3. **审片副本（CEO 视角 / 全公司）**：`review_proxy.py` 出 720p，脉冲 `review_proxy` 站一次最多 6 条，幂等。
4. **闸与编目（CPH4）**：所有机器可判的闸、索引、压榨度、决策层都在这里跑——不产出画面，只判真假。
5. **资产后处理（CPH4 / 内容线）**：抠边、规格归一、sha 入库、联系表；都是 CPU/GPU 轻活。

## 三、不许干的（占用大且没有性价比）

- **i2v / 关键帧生成**：归 bm-c（ComfyUI）；Mac 做等于用 16 核 GPU 硬扛，且拿不到稳定模型。
- **LoRA / 人脸训练**：MPS 太慢，归 bm-c 或云端。
- **大模型驻留**（22GB/35B）：会把 32GB 统一内存压到 swap，已判 DOWNGRADE。
- **多租户对外服务**：这是主控机，不是服务器。

## 四、产能政策（写成数，不写口号）

- 保底 **6GB** 空闲内存；低于此线只允许闸与调度，不接媒体活。
- 同时最多 **2 个** ffmpeg（硬编 1 个也能打满引擎，多开只增加切换开销）。
- ASR 一次只跑 1 条（模型 1.6GB + 激活占用），不与编码并发抢 GPU。
- 脉冲慢批里这些活**都有上限**（asr_subs 2 条 / review_proxy 6 条），避免一轮吃满。

## 五、怎么保证不被空转（这才是 CEO 真正在意的）

- 供给不足时，Mac 优先接：`review_proxy` → `asr_subs` → 资产后处理 → 闸与索引。
- 判断依据=`Tools/fleet/squeeze.py`：Mac 的可再派件数长期不为 0，说明供给没喂到，属流程缺陷。
- 各公司产物要进 Mac 视野：城市/量化仓不在本机时，靠**每日投影**（company/<org>/projection-*.json），不靠台账口述。

## 六、已验证的可用命令

```
# 审片副本（幂等，最多 6 条）
python3 Tools/fleet/review_proxy.py --src media/drama-out --out media/review-720p --max 6
# 字幕补缺（一天一次，最多 2 条）
python3 Tools/fleet/subs_asr.py --sync-dir media/drama-out \
  --subs-dir cph4/fleet/drama-dept-v1/subs --days 7
# 压榨度（看 Mac 还剩多少、是不是被饿着）
python3 Tools/fleet/squeeze.py --out cph4/fleet/state/squeeze.json
```