# 本地会话开工简报（自动生成）

> 新会话第一条指令：读本文件，按「下一步」继续；不要依赖上一段对话的上下文。
> 重生成：python3 Tools/fleet/session_brief.py

## 盘上事实

| 项 | 值 |
|---|---|
| 生成时间 | 2026-11-10 16:32:14 |
| 主控脉 | 158s 前，一拍 130.1s，git=skipped |
| 状态同步 | 321s 前 |
| 常驻服务 | 35 |
| 在线节点 | bm-a,bm-b,bm-c,bm-m（hub=True） |
| 队列 | {"DONE": 627, "UNVERIFIED": 3, "CANCELLED": 805, "FAILED": 3, "ARCHIVED": 366, "null": 3, "BLOCKED": 6, "OPEN": 5} |
| 产出 | 产品 3 / 内部 561 / 缺失 45 |
| 自愈 | stale=[] |
| 发布包 | MV-REVIEW-20261110 |

## 下一步（按顺序做，不需要问）

1. 看 cph4/fleet/CAPABILITIES.md：谁在线、能接什么；
2. 处理 OPEN/BLOCKED（见下表），能改派就改派，需要人判的留在队列并写原因；
3. 每完成一件，必须留下可核验产物（文件 + sha256），用 pack_release.py 打成交付包；
4. 本地模型优先：4B 做判读/摘要，8B 做综合；云只走 Codely 且非必要不用。

## 待办卡（前 8 张）

- **BLOCKED** [VCORP-GEN-r1202-EP001-060-20261108] — 2026-11-08 00:0x：bm-b 的 FleetLink /health=000（tailnet 通但 8790 不答），3 天零回执 ⇒ 不钉死一台
- **OPEN** [MV-DIRECTOR-PACKET-20261109] — deliverable-not-on-disk(local)
- **BLOCKED** [biggame-accept-2026-11-09] — 
- **OPEN** [R-NEXT-BIGSTREAMD-TTS-QC-20261109] — 
- **BLOCKED** [PATROL-bighouse-20261109] — 
- **BLOCKED** [asset-lib-asset-gen-2026-11-10] — CEO-PROXY 事件班 2026-11-10 02:5x: retries=3 error_class=E-ROOTCAUSE-3X、progress_by
- **BLOCKED** [asset-lib-asset-gen-scenes-2026-11-10] — scenes | CEO-PROXY 事件班 2026-11-10 02:5x: retries=3 error_class=E-ROOTCAUSE-3X、pr
- **BLOCKED** [biggame-accept-2026-11-10] — 

## 本地模型

- 4B：qwen3.5:4b-mlx @ 11434（常驻，判读/摘要）
- 8B：qwen3:8b-dsh32k @ 11436（32k，工具调用已验证，按需加载）
- 共享：http://100.75.133.10:8792（Tailscale 内网免令牌，白名单 4B/4B-instruct/向量）

## 红线

- 只认盘上产物，不认「进程活着」；
- 单写手：队列只由 master_agent 写，台账只由 CEO-PROXY 写；
- 取消/停线必须写原因；远端交付物必须带 sha256；
- 模型不得替 CEO 对外沟通、不得发密钥。
