---
name: fleet-ops
description: 机队运维专家席。Use when any fleet or machine problem or operation: scheduled task issues, popup or black console windows, FleetLink/poke/sync failures, heartbeat stall, machine-state pause/resume, GPU/CPU lane allocation, dispatching work to bm-a/bm-b/bm-c/bm-d, waking a stalled machine, or fleet git surgery. Triggers on 机队/计划任务/弹窗/黑窗/同步/poke/心跳/停摆/让路/派单/车道/新机入网.
---

# 机队运维席速查

正典深度位：车道表=`cph4/resource-chain.md` §9.1｜调度协议=`cph4/fleet/dispatcher/CEO-PROXY/`（ROUND.md）｜机队协议=`cph4/fleet-protocol.md`｜新机=`cph4/onboarding.md`+`Tools/bootstrap-machine.ps1`｜推送纪律=`cph4/versioning.md` §4.4。本件只收高频硬律。

## 硬律速查（违例即返工族）

1. **S4U 律**：本机一切车道计划任务一律 S4U 注册（禁 InteractiveToken）——查「弹窗复发/黑窗」先 `Get-ScheduledTask <名> | % LogonType`；自愈脚本重注册的默认值=回归源（共享脚本改法走 BM 仓治理）。
2. **静默律**：建/改任务唯一正门=`Tools\task-register.ps1`（wscript //B 隐藏链+写后读回验证）；会话内执行=进程内 `&`（先 `Set-ExecutionPolicy -Scope Process Bypass -Force`），禁 spawn powershell.exe/cmd.exe 子进程。
3. **停摆唤醒**：心跳 last_round_at 冻结+拉取 .:fail=循环班停摆——空任务 poke 只修拉取不修停摆；正法=poke body 带 `tasks=[该机 wake_tasks]`（白名单=`Tools/fleet-nodes.json`）→ 3 分钟复探验 BURNING。
4. **派单律**：orders 行必带 @机名+lane+回执窗+验收物；跨机转单/POOL 开卡=交接卡九要素+`python Tools/card-lint.py` 过闸；台账追加只走 python 尾锚正法（utf-8-sig 探测·GBK 乱码禁当锚）。
5. **车道裁决**：bm-a=中枢+大内存+夜窗 GPU 备援（工作日白天 GPU 零排单·CPU 解禁）｜bm-b=声音+轻视频+回测 CPU｜bm-c=生成视觉-only GPU 主力（回测/编码 LLM 禁入其 GPU）｜bm-d=六卡机候 JOIN-REPORT。RAM>8G 分片归口 bm-d/bm-a。
6. **让路律**：CEO 原话「我要打游戏/我要工作」=立即 `machine-state.ps1 -Mode pause`（bm-a）；「全面开工」=-Mode resume+O 令广播；触发词歧义=派活语义不触发。
7. **推送纪律**：多窗脏树=pathspec 提交/外科净路；push 成败验 sha 变化（`<旧>..<新> main -> main` 才算成·PS 假红勿信）；撞钩子/竞推=worktree 内容级合并或 Git Data API 原子链；反转闸=`Tools/git-no-reversal-check.py` push 前必跑。
8. **FleetLink 判障三件**：/health 版本+tailscale direct/relay+stamp pulls——判「同步慢/监听器不动」先查三件勿盲杀进程重启（单线程 listener 阻塞=读超时问题非进程死）。
9. **长批纪律**：GPU 长批禁裸 Start-Process 承载（游戏车道轮 3-5 分钟清场击杀）——一律自愈循环 runner 范式（每 8min 检死→重启→resume→到齐自停）；烧毕手动 schtasks /DISABLE 勿依赖自停。
10. **校时律**：写 O 令/带时间戳文件前必 Get-Date 实测（跨隙挂起会话禁按上一动作顺延推算）。

## 工具速查
machine-state.ps1 -Mode status/pause/resume（机器状态一屏）｜fleet-reality.ps1（报机队现状必先跑·带实测戳）｜fleet-dispatcher.ps1（L0 巡班）｜fleet-idle-watch.ps1（防闲置）。
