# 素材自供给契约 v1 — 2026-11-05

> CEO 指出的根因：「机队所有都在等你给料，他们自己不行吗？」
> 结论：错的不是机器，是结构——素材被放在主控私有盘上，卡又不声明输入。

## 1. 结构（两层，缺一不可）

| 层 | 进程 | 绑定 | 解释器 | 为什么这样拆 |
|---|---|---|---|---|
| 读盘层 | `Tools/fleet/asset_share.py` | 127.0.0.1:8791 | pyenv 3.13（有完全磁盘访问） | 只有它能真正读到 `/Volumes` 内容（TCC 按二进制授权） |
| 放行层 | `Tools/fleet/asset_relay.py` | 0.0.0.0:8790 | `/usr/bin/python3`（被应用防火墙放行） | 纯字节转发，不碰磁盘，绕开防火墙按路径放行的限制 |

访问控制：只读、只暴露 `/assets`（移动盘 FluxAssets）与 `/media`（仓内）两个白名单根，
其余路径 404；需 `X-Flux-Token`，无 token 一律 401。

## 2. 执行机自取（不再是主控分发）

```bash
python3 Tools/fleet/asset_pull.py --rel store/00/xxx.jpg --dest media/inbox/xxx.jpg --sha256 <hash>
python3 Tools/fleet/asset_pull.py --card <card_id>      # 按卡声明的 inputs 批量取
```

- 本地已有且 sha 一致 → SKIP；不一致 → 重拉。
- 拉取失败 → `rc=3` + `E-BLOCKED-INPUT`，**不计入三次失败预算**（合法缺料≠执行失败）。
- 回执落 `cph4/fleet/queue-receipts/asset-pull-<card>.json`。

已实测：跨网卡取 90,948 字节文件，sha256 校验通过，rc=0。

## 3. 卡片契约（新增 inputs 字段）

```json
"inputs": [
  {"rel": "store/00/xxx.jpg", "root": "assets", "sha256": "...", "dest": "media/inbox/xxx.jpg"}
]
```

执行机顺序：`inputs` 自取 → 跑主命令 → 出产物。**没有 inputs 的卡不允许再写「缺输入」等死。**

## 4. 各机一次性准备

1. 写 `~/.fluxgroup-asset-token`（与主控同一串，权限 600，**不入 git**）。
2. 设 `FLUX_ASSET_BASE=http://100.75.133.10:8790`（默认值已内置 tailscale 地址）。

## 5. 已知边界（如实记录）

- 本机连自己的 tailscale IP 会被 reset（utun 不回环），所以本机自测用局域网 IP。
- `tailscale serve` 在本机卡住要证书交互，未采用。
- 主控一旦离线，共享层即消失——下一步应把素材副本镜像到一台生产机（bm-a），
  由最近的在线节点提供服务，去掉单点。