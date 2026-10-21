# MSG-1350-bma-biliops-migrate — B站运营线迁移 bm-b 执行案（备料·候通道）

> 入单口：`cph4/fleet/inbox/`（本件=席起草的迁出票·目标机 bm-b）
> 令源：CEO 2026-10-21「迁移」（承同日红线令「这台机器禁止干金融类的，敏感的」）
> 状态：**BLOCKED-CHANNEL**——tailscale stopped，bm-b 不可触达。本件只备料，通道恢复后 poke 生效。

## 一、迁出物清单（实测）

| 项 | 现位（bm-a） | 去向（bm-b） | 性质 |
|---|---|---|---|
| 代码/规格 10 件 | `cph4\fleet\bili-ops\`（AGENT-SPEC-v3/REPLY-VOICE-SPEC-v3/Modelfile.v3.6/.v3.7/reply_gates_v2.py/bili_sim_v41.py/CORPUS-SOURCES/LLM-35B-WORKLOADS/before-after×2） | bm-b 同名仓路径（git 同步=通道恢复后自然到件） | 仓内件·走 git |
| 执行体 | `C:\Users\sjs20\bili-bot\`（bili_bot/bili_dm/bili_qc/bili_outreach/gate_lib/config/replied.json/dm-replied.json） | bm-b `C:\Fluxgroup\bili-bot\` | **仓外件·须 Taildrop** |
| **凭据** | bm-a 侧仓外 auth-handoff.json（B站 cookie·零入 git） | bm-b 侧 config.json（旧档已定此位） | **敏感·见 §三** |
| 计划任务 | `bm-a-BiliAutoReply/BiliDM/BiliQC/BiliOutreach/BiliSlowDel`（5 个·现全 Disabled） | bm-b 注册同名任务（走 task-register 静默链） | 任务面 |

## 二、执行序（通道恢复后·预计单窗完成）

1. bm-b 侧 `git pull` 确认 bili-ops 10 件到件（含 10-21 v3.2 定稿批）。
2. Taildrop 送执行体包：`bili-bot\` 除凭据外全量（脚本+replied.json 台账）→ bm-b 落 `C:\Fluxgroup\bili-bot\`，逐件字节校验。
3. **凭据交接=CEO 亲动**（见 §三·本席不过手 cookie 明文）。
4. bm-b 注册 5 任务（task-register.ps1·静默链+S4U+写后读回+点火验证），初始 `enabled=false`，候 CEO「开工」口令再 Enable。
5. bm-a 侧注销 5 任务 + `bili-bot\` 留存 30 天后按 R3 级清理（不即删·留回退窗）。
6. 回执：本目录 `RCPT-<HHMM>-bma-biliops-migrate.md`（含逐件字节校验值+任务注册实证+fleet-live-status 读数）。

## 三、凭据红线（照现行律，一步不越）

- 凭据仓外、零入 git、不经 AI 过手明文——**cookie 续登由 CEO 在 bm-b 浏览器侧完成**，旧判例=10-14「浏览器扩展提取·凭据=CEO 已交接·仓外 auth-handoff.json」。
- bm-a 侧凭据文件在迁移完成**且 bm-b 首轮回执验证通过后**才删除；删除前先在 bm-a 隔离区留 7 天（§三 资源保留律 R2 源资产）。
- 护栏参数随件迁移不重设（每轮 ≤5/日帽 15/条间随机 30-90s/replied.json 永不重发/R1 五信号熔断自禁）。

## 四、失败回退口径

- bm-b 8G 显存不足跑 Qwen3-8B 海选+回复双职 → 回复面降 Qwen3-4B（吞吐优先），海选让给 bm-a 夜窗；不影响迁移动作本身。
- Taildrop 两面性坑（CLI 静默空≠未交付·判例 R2.13）→ 验收看 bm-b 盘实存+字节，不看 CLI rc。
- 任一步 FAIL=停止后续、bm-a 任务维持 Disabled 不复活、本票转 BLOCKED 呈报，**不猜着干**。

## 五、验收判据（缺任一项不算迁完）

1. bm-b 上 5 任务 Ready 且首跑留痕（日志行+时刻）；
2. replied.json 在 bm-b 侧非空且与 bm-a 末态行数一致；
3. 一次真实回复成功（CEO 过目门：首条人工看后再放自动）；
4. bm-a 侧无残留执行体进程、凭据已进隔离区；
5. 回执行上链（本目录+orders 回执节）。

---
*起草：千问席 · 2026-10-21 · 目标机=bm-b（100.82.175.0）· 状态 BLOCKED-CHANNEL 候令*
