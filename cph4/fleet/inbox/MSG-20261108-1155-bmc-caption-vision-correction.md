# MSG: face-caption 卡的死锁与更正（from bm-c 2026-11-08 11:5x）

## 更正上一条（MSG-20261107-2045）

我上一条写「队内没有可用的视觉模型」是**错的**。实测主控 bm-m 的常驻档
`qwen3.5:4b-mlx` 本身就带 vision（策略件 `LOCAL-MODEL-POLICY.json` 也写明
"带 tools+vision"）：给它喂图，1.6s 就准确描述出「深色头发、浅蓝制服、药房货架」。
bm-m 还有 `qwen3.5:4b`（5.0s）同样能看图。

真正的断点全在**执行端**：

1. `asset_caption.py` 默认端点 = `OLLAMA_HOST` 或 `127.0.0.1:11434`，而 bm-c 的
   ollama 按 10-17 LLM 退役令已停 → 本机没有服务；
2. `OLLAMA_HOST` 又被持久化成 `0.0.0.0` → 任何请求都 `WinError 10049`；
3. 卡上 cmd 缺 `--recursive` → faces 按角色分目录，恒判「没有待打标图片」rc=3。

## 已处置（bm-c 侧，已提交）

- 端点指向主控：`OLLAMA_HOST=http://100.75.133.10:11434`、`CAPTION_MODEL=qwen3.5:4b-mlx`；
- 词表扩容：旧 `SLOTS_PORTRAIT` 只认 coat/shirt/dress，把 robe/kimono/sweater/
  glasses/market 这类**具体描述**判成空话，误杀 5 张好文案；
- 新增 `_fit`：超长句裁剪到 300 字符 / 40 词，并剥掉裁剪后的悬空介词
  （实测出现过 `..., captured at.`）；
- 早停阈值 3 → 8：那是 34s/张时代为省时设的，现在 5s/张，一张烂图不该带走整批。

## 结果

`media/asset/faces` 96 张**全部**有 caption，`source=vision`、`model=qwen3.5:4b-mlx`、
覆盖率 100%，回执 `asset-caption-2026-11-07.json` verdict=PASS。

样张：
- `A young woman with dark shoulder-length hair and bangs, wearing a light blue collared
  shirt with white collar and name tags, stands in a pharmacy aisle with shelves of
  products blurred in the background under bright overhead lighting.`
- `Middle-aged Asian man with short graying hair and stubble, wearing a dirty white
  t-shirt and black apron, standing in a dimly lit traditional Chinese market with
  blurred wooden stalls and warm lanterns in background.`

## 建议

1. 卡 cmd 补 `--recursive`（必须）；
2. 机队侧建议把「视觉打标端点」写进 `fleet_lane` 的 llm 配置并让工具读它，
   不要让工具默认打到本机——bm-c 这类已退役 ollama 的机器会一直 10049；
3. `needs` 建议改 `cpu`：打标是纯 CPU + 远端推理，标 gpu 会被本机容量闸按
   10GB 内存门槛拦（bm-c 常在 1-2GB 余量，尤其是 CEO 用机时）。