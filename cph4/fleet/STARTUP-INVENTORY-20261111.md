# 开机自启留档 2026-11-11（CEO 令：全部暂停，等他梳理工作流）

> 机器：bm-m（MacBook Pro M1 Pro）。时间：2026-11-11T11:15:50+0800。
> 令源：CEO 2026-11-11 11:15「都记录在案然后全部暂停，等我梳理工作流」
> 范围：本机 bm-m 的用户级自启（LaunchAgents + 登录项）。系统级 /Library 需 sudo，未动。

## 一、暂停方式（可逆）

plist 全部移入 `~/Library/LaunchAgents/disabled/20261111-pause`，不删除；`launchctl bootout` 停掉已加载实例。
恢复：`bash Tools/restore-startup.sh`（把 plist 移回并 bootstrap）。

## 二、清单（44 项）

| # | label | 常驻 | 触发 | 暂停时 PID | 暂停时退出码 | 程序 |
|---|---|---|---|---|---|---|
| 1 | `com.fluxgroup.agentlane` | 是 | RunAtLoad | 1412 | 0 | `/bin/bash ~/FluxGroup/Tools/fleet/agent_lane.sh start` |
| 2 | `com.fluxgroup.analyst` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/local_analyst.py` |
| 3 | `com.fluxgroup.assetrelay` | 是 | RunAtLoad | 1399 | 0 | `/usr/bin/python3 ~/FluxGroup/Tools/fleet/asset_relay.py --listen 8790 --target 127.0.0....` |
| 4 | `com.fluxgroup.assetshare` | 是 | RunAtLoad | 1447 | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/asset_share.py --host 127...` |
| 5 | `com.fluxgroup.auditor` |  | RunAtLoad,每600s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/local_auditor.py --limit 8` |
| 6 | `com.fluxgroup.caffeinate` | 是 | RunAtLoad | 1450 | 0 | `/usr/bin/caffeinate -s -i` |
| 7 | `com.fluxgroup.console` | 是 | RunAtLoad | 1449 | 0 | `/usr/bin/python3 ~/FluxGroup/Tools/fleet/console_server.py --port 8787` |
| 8 | `com.fluxgroup.dailybrief` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/daily_brief.py` |
| 9 | `com.fluxgroup.dashboard` |  | RunAtLoad,每20s | - | 0 | `/usr/bin/python3 ~/FluxGroup/Tools/fleet/fleet_dashboard.py` |
| 10 | `com.fluxgroup.deepreason` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/deep_reason.py --limit 1` |
| 11 | `com.fluxgroup.embeddedupe` |  | RunAtLoad,每3600s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/embed_dedupe.py` |
| 12 | `com.fluxgroup.fleetbus` | 是 | RunAtLoad | 14435 | 1 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/fleet_bus.py` |
| 13 | `com.fluxgroup.gateway` | 是 | RunAtLoad | 14408 | -15 | `/usr/bin/python3 ~/FluxGroup/Tools/fleet/model_gateway.py --port 11435` |
| 14 | `com.fluxgroup.grid` |  | RunAtLoad,每300s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/grid_run.py --apply` |
| 15 | `com.fluxgroup.intake` | 是 | RunAtLoad | 1420 | 0 | `/usr/bin/python3 ~/FluxGroup/Tools/fleet/artifact_intake.py` |
| 16 | `com.fluxgroup.kbbuild` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/kb_build.py --limit 100` |
| 17 | `com.fluxgroup.labelfill` | 是 | RunAtLoad | 1423 | 0 | `/bin/bash ~/FluxGroup/Tools/fleet/fill_loop.sh` |
| 18 | `com.fluxgroup.llmgateway` | 是 | RunAtLoad | 1429 | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/llm_gateway.py --host 0.0...` |
| 19 | `com.fluxgroup.loadwatch` |  | RunAtLoad,每60s | - | 1 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/supply_guard.py --apply` |
| 20 | `com.fluxgroup.locallane` |  | RunAtLoad,每60s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/lane_agent.py --node bm-m...` |
| 21 | `com.fluxgroup.localworker` |  | RunAtLoad,每60s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/local_worker.py --limit 4...` |
| 22 | `com.fluxgroup.loopclose` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/loop_close.py` |
| 23 | `com.fluxgroup.modelwatch` |  | RunAtLoad,每1800s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/model_watch.py` |
| 24 | `com.fluxgroup.ollama` | 是 | RunAtLoad | - | 1 | `~/bin/ollama serve` |
| 25 | `com.fluxgroup.patrolseats` |  | RunAtLoad,每300s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/patrol_seats.py` |
| 26 | `com.fluxgroup.planner` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/local_planner.py` |
| 27 | `com.fluxgroup.pulse` | 是 | RunAtLoad | 13208 | -15 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/master_pulse.py --loop 45` |
| 28 | `com.fluxgroup.rehearsal` |  | 每14400s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/rehearsal.py --scenarios` |
| 29 | `com.fluxgroup.repodeep` |  | RunAtLoad,每300s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/repo_deep.py --limit 300 ...` |
| 30 | `com.fluxgroup.resilience` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/resilience.py --json ~/Fl...` |
| 31 | `com.fluxgroup.resourcegov` |  | RunAtLoad,每60s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/resource_governor.py --apply` |
| 32 | `com.fluxgroup.reviewer` |  | 日历 | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/local_reviewer.py` |
| 33 | `com.fluxgroup.seats` |  | RunAtLoad,每180s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/seat_runner.py --auto` |
| 34 | `com.fluxgroup.selfdrive` |  | RunAtLoad,每900s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/selfdrive.py --limit 4` |
| 35 | `com.fluxgroup.selfwatch` |  | RunAtLoad,每300s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/selfwatch.py --apply` |
| 36 | `com.fluxgroup.serviceguard` |  | RunAtLoad,每300s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/service_guard.py --apply` |
| 37 | `com.fluxgroup.soak` |  | RunAtLoad,每15s | - | 1 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/soak_watch.py --auto` |
| 38 | `com.fluxgroup.statesync` |  | RunAtLoad,每60s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/state_sync.py` |
| 39 | `com.fluxgroup.tailnethub` | 是 | RunAtLoad | 1402 | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/tailnet_hub.py --port 8791` |
| 40 | `com.fluxgroup.toolwatch` |  | RunAtLoad,每600s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/tool_watch.py` |
| 41 | `com.fluxgroup.usefulload` |  | RunAtLoad,每3600s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/useful_load.py` |
| 42 | `com.fluxgroup.watchdog` |  | RunAtLoad,每120s | - | 0 | `~/.pyenv/versions/3.13.18/bin/python3 ~/FluxGroup/Tools/fleet/pulse_watchdog.py --apply...` |
| 43 | `com.fluxgroup.webai` | 是 | RunAtLoad | 1448 | 0 | `/usr/bin/python3 ~/FluxGroup/Tools/fleet/web_ai.py --port 8088` |
| 44 | `com.user.weeklymaint` |  | 日历 | - | 0 | `/bin/bash ~/Library/Scripts/weekly-maint.sh` |

## 三、暂停后必然停掉的能力（须知）

1. `com.fluxgroup.pulse` = 主控脉：停后不再派单、不再做账本同步与 git 推送。
2. `statesync` / `gateway` / `fleetbus` / `tailnethub`：机队同步与指令面停止，Windows 三台将收不到新卡。
3. `llmgateway` / `ollama`：跨机与本地模型网关停止，Agent 侧模型调用会失败。
4. `console` / `dashboard` / `webai`：可视面与页面停止。
5. `caffeinate`：防休眠守护停止，合盖会正常睡眠。

## 四、系统级未动（需 sudo）

`/Library/LaunchAgents`：com.microsoft.entraidentitybrokerxpc、com.microsoft.update.agent、com.netease.uuremote.agent
`/Library/LaunchDaemons`：com.apphousekitchen.aldente-pro.helper、com.crystalidea.macsfancontrol.smcwrite、com.microsoft.autoupdate.helper、com.netease.uuremote.daemon、sh.brew.tailscale

## 五、登录项（9 个，见同目录 STARTUP-INVENTORY 的 login_items 字段）

