# KN 粗剪收据 c2180 · 2026-10-24 13:00 · 《可爱女人》26/30 官定粗剪落地

- **本轮时间**：2026-10-24 12:55（tick = C2180，快照 id tick-20261024-1300@C2180，normal_iteration）
- **Step0**：preflight 全 PASS（仅 INFO：GPU_COMFY_MISSING / NOT-GREEN-IDLE / 35 个 foreign guid meta）
- **运行模式**：normal_iteration（10 分钟）

## 司实况（CEO 过程可见面·三行）

- **当前活**：《可爱女人》KN 768P A 波 26/30 在盘（KN24 12:45 落地，PID 29056 仍占 GPU）；本轮做 CPU 射线——把 26 单拼成一条可看的粗剪
- **最近实物**：`K:\Fluxgroup\FluxGroup\media\mv-album-001-jay\assembly-packA-KN\KN-ROUGH-CUT-26of30-C2180.mp4`（170.42s / 4090 帧 / 1344×768 / 47.9MB，12:5x），时间轴单一真值同目录 INDEX JSON
- **下个里程碑**：KN25/28/29/30 落地 → 30/30 重拼 → 交装配站（调色/转场/字卡/歌），窗 ≤35h

## 本轮实质产出

- **粗剪站（新）**：`cph4/fleet/mv-album-001-jay/kn_packa_assembly_c2180.py`——单一真值=manifest（顺序/窗长/速度），每单 trim→速度变换→窗长强裁→fps24→统一 1344×768，concat 无音轨（画面配歌律）。缺单不填占位。
- **真缺口实测**：首拼 167.875s / 4029 帧，比应有的 170.10s 短 2.23s——控制到单元层：KN04 缺 2.06s（声称 8.14s 窗 @1.20x，源只 7.29s），KN05/KN10/KN12 各缺 0.11-0.28s。**这是 manifest 自身算术漏**：窗长超过源能填的量，逐单门禁看不见。
- **修法=auto-fit**：源够长时放慢去填窗（need=src/win，地板 0.85），不再丢帧留洞；need<0.85 才判真 GAP 并报。重编码 **170.42s / 4090 帧**，时间轴 170.10s 对齐；旧带洞版存为 `KN-ROUGH-CUT-v0-gapped-26of30-C2180.mp4` 供对照。
- **门禁**：framing 扫 26 单（flat 3 / undecided 1）regress_diff=0；新落地 KN22b/KN23/KN24 均 PASS 或 NOT-JUDGED（非缩放镜）；hygiene 上轮 4/4。

## 资产台账

- **i2v 片**：《可爱女人》768P **26/30**（缺 KN25/KN28/KN29/KN30）；《星晴》PACK-B v9 母版待导演席复核
- **粗剪**：170.42s（26 单连续前段，无调色/转场/字卡/音轨）
- **门禁**：framing 26 单（新定 FLAT 3）+ pseudo-text + hygiene 4/4；覆盖率断言本轮入站
- **缺口**：pending = 30/30 齐片 + 4 单 480P 验证波收割 + KN31-KN32 KF

## 问题清单

- (黄) manifest 窗长超过源能填（KN04 最重）——建管时加断言 src_kf ≥ win×speed，已记 P2-4
- (黄) KN04 自适应 0.896x 在ー动可读边缘，配站时人眼判定，读成慢镜头则该单重烧
- (蓝) KN08 1.09x 估计器不稳（人眼位）；KN03/KN11/KN21 宣称推镜实测平镜（已排 480P 验证波）

## 资源与工具状态

- GPU：KN 768P 波占卡（PID 29056）；本轮 ffmpeg 走 CPU，未抢卡
- RAM/VRAM：preflight 8.7G / 13.7G；ComfyUI 8188 + sidecar 8199 在听
- 云端 token：本轮零云端、零 MCP

## 下轮选线

1. KN25/28/29/30 落地 → 30/30 重拼（脚本已验数学）→ 导演席拉片
2. 新落地单位逐单过三门 + 每 3-4 单一张人眼板
3. 4 单 480P 验证波收割（kn_waveend_chain_c2179 已装弹）

## 对方机摘要（A 机）

A 机以自动化快照与 orders.md 尾行为准（本机未新增对 A 派单）。
