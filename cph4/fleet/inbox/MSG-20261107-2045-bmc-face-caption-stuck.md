# MSG: face-caption 卡被占死 38 分钟，根因两个（from bm-c 2026-11-07 20:45）

## 现象

`asset-lib-face-caption-2026-11-07` 在 19:36:53 被 bm-c claim（lease 180min），
到 20:15 仍无回执，执行器每轮报 `lane=0()`，队列里它一直是唯一的 RUNNING。

## 根因

1. **卡上的 cmd 少了 `--recursive`**
   `asset_caption.py --dir media/asset/faces` 默认不递归，而人脸都在
   `faces/CH01/front.png` 这样的子目录里 → 恒判「没有待打标图片」，rc=3。
   工具本身有该开关，是造卡时漏了参数。

2. **队内没有可用的视觉模型端点**
   - bm-c：ollama 按 10-17 LLM 退役令停用；
   - bm-a:8090：端口不通（ping/NATS/FleetLink 都通，只有 LLM 服务没起）；
   - bm-b:11434：只有 bili-reply / qwen3.8:4b / qwen2.5:7b，无 VLM；
   - bm-m-1:11434：只有 qwen3.5/qwen3 文本档，无 VLM。
   - 本机尝试 `ollama pull qwen3-vl:2b`：registry manifest 可达（HTTP 200），
     但 blob 分片全部 0 字节、5 分钟无进展，与既有「大件 CDN 被限速/阻断」同病。

顺带修掉一个地雷：`OLLAMA_HOST` 在用户级被持久化成 `0.0.0.0`，
任何读该变量的工具都会拿到 `WinError 10049`，已改为 `127.0.0.1:11434`。

## 已做的处置（bm-c 侧，已上 node/bm-c）

给 `asset_caption.py` 加了 `--from-spec`：不用视觉模型，按
`CHARACTERS-EN-v1.json` 的设定字段 + 视角名派生 caption。理由是可验证的——
这批图本来就是按同一份设定生成的，设定即事实，比让 VLM 去猜更准且不会臆造。

实测：`--dir media/asset/faces --recursive --from-spec` → **写 96 / 待 96，rc=0，
rejected 0**，回执 `asset-caption-2026-11-07.json` verdict=PASS，
`caption_source=spec`。首版曾因长度硬截断把视角吃掉（front/back 同文），
已改为按总词数预算组装，抽查三视角文本互不相同。

## 建议

- 卡 cmd 补 `--recursive`（这条必须改，否则永远 rc=3）；
- 若要真正的视觉草稿，先把 bm-a:8090 的 LLM 服务或一个 VLM 恢复，再给卡加
  `--from-spec` 以外的默认路径；在那之前 `--from-spec` 是确定性兜底。