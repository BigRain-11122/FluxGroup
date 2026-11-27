# 今夜派活与待机说明（2026-11-03 19:00 · CEO 下班前令「自己去派活」）

## 一、现在机器是什么状态（19:00 实测）

| 机器 | 心跳 | 判定 |
|---|---|---|
| bm-m（Mac 主控，本机） | 活 | 唯一在跑的：调度、闸、编目、硬件编码、ASR、本地 4B |
| bm-a | 6442s 未更新 | agent 已停（不是忙，是没在跑） |
| bm-b | 5719s 未更新 | 同上 |
| bm-c | 5982s 未更新 | 同上（ComfyUI 侧也就不可派） |
| bm-d | 466361s（5 天） | 未入网 |

**结论**：今晚不会有远端产出。派下去的卡会停在 OPEN，等机器醒来接。这不是失败，是如实的等待态。

## 二、今晚已经派下去的活（醒来就接）

| 卡 | 钉在 | 干什么 | 判据 |
|---|---|---|---|
| `asset-lib-asset-gen-<date>` | bm-c（硬钉） | 吃 128 份规格里的**道具**，出 4 件 | 回执 made 非空；透明底会标 alpha_missing 由主控补 |
| `asset-lib-asset-gen-scenes-<date>` | bm-c（硬钉） | 出 3 件**场景**竖屏底图 | 短边 ≥1080 |
| `asset-lib-char-probe` / `char-gen` | bm-c（硬钉） | 先问机器有哪些模型，再出角色 | 缺模型写 BLOCKED，不猜 |
| `bigmoney-backtest-2026-11-03-v3` | bm-a/bm-b/bm-d | 生产候选策略回测 | JSON 在盘含 cagr/sharpe/maxdd |
| `bigmoney-signal-<date>` | 同上（依赖回测） | 下月持仓 CSV | 含代码/权重/因子值/指纹 |

三张 bm-c 卡都已硬钉（hard_nodes），醒来之前谁也不会回落去跑——之前 char-probe 落 Mac 报"ComfyUI 不可达"的假失败就是缺钉子。

## 三、本机（Mac）今晚会自己跑的（脉冲慢批）

1. `review_proxy`：新成片自动出 720p 审片副本（每条约 1.2 秒）。
2. `asr_subs`：新成片自动补字幕源（一次最多 2 条，一天只跑一次）。
3. `asset_prompts`：P0 规格已 128/128 出齐（113 合格/15 缺），缺件会自动重排。
4. `decide` / `squeeze` / `orgs`：每轮报"哪条线该加算力、哪条有台账无产物、哪家设计缺哪一问"。
5. `memory_nightly`：02:00–05:00 归纳记忆（窗外自动跳过）。

## 四、今晚不会发生的事（别明早误判）

- **不会有新成片**：i2v/关键帧在 bm-c，机器没醒。
- **不会有新道具图**：云生成要我（会话）在，脚本没有调用生成服务的通道；ComfyUI 那条要等 bm-c。
- **量化信号不会有**：要 bm-a/bm-b/bm-d 上的量化仓。
- **城市/商业线不会有产物**：四仓不在本机，等投影。

## 五、明早第一件该看的东西

1. `cph4/fleet/state/org-decide.json` — 四条判断：可加算力 / 有台账无产物 / 建议停 / 证据看不见。
2. `cph4/fleet/queue-receipts/` 里最新回执 — 机器醒没醒，看有没有今天的新 rc。
3. `media/review-720p/` — 成片有新的就直接点开看，不用等原片。
4. `cph4/fleet/asset-lib-v1/ASSET-PROMPTS-v1.json` — 128 件规格，可直接当"下一批做什么"的清单。

## 六、需要 CEO 的只有一件（不催办）

音色语料要联网批量拉 CC 白名单（Common Voice / LibriTTS / VCTK / AISHELL-3 / LibriVox），批一句我就开拉、四机分片；不批就继续等，不影响上面任何事。