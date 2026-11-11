# AUTONOMY-V3 工位自驱阻塞面（2026-11-12 03:05 · R41 事件班实测）

> 结论先行：**换挡后没有任何工位能自驱——五个工位全部被 STATIONS.json 的状态开关关掉，且 delivery 的 16 个工序没有产物契约（unknown_output）**。这是「STARVED-EXEC 全域」的真因，不是机器懒，也不是卡少。

## 一、实测（`Tools/fleet/station_drive.py --station <id> --dry`，工作树 `_pub/wt-v727` @ d228abc68）

| 工位 | STATIONS.json status | dry-run 结果 | 自驱阻塞原因 |
|---|---|---|---|
| control | `ready_paused` | would_create=[] | 本机状态=ready_paused，不自驱（停/离线/未装） |
| visual | `blocked_no_comfyui` | would_create=[] | 本机 ComfyUI 未装/未起（`Test-NetConnection 127.0.0.1:8188` = False） |
| audio | `offline` | would_create=[] | 对应机 bm-b 整机离线（tailscale last seen 1d，节点车道回执停 11-10 00:19） |
| brain | `not_installed` | would_create=[] | 本机未装 |
| delivery | `network_ok_not_registered` | would_create=[] · unknown_output=**16** | 工位未注册；且 16 个工序缺产物契约 |

`STATIONS.json` 最后改动 = `f502fef37`（2026-11-11 17:01），即换挡当晚写定的状态，之后没有任何工位被放行。

## 二、delivery 的 16 个 unknown_output（缺 PRODUCTS 产物契约）

PROD-GAME-SUBMIT（材料套用/打包/图标/提审清单）· PROD-ASSET-PACK/图标 · PROD-FLUXVERSE-SCENE（场景装配/事件接入/演示区）· PROD-BIGHOUSE-FLOW（场景/流程）· PROD-BIGLIFE-POP（户籍/行为/资产）· PROD-CAR-GAMING（车机适配/打包）· PROD-ACCOUNT-GROWTH/人工发送。

> 注：R40 的最小接通（commit `94bca652e`）只补了提审链一段命令，其余仍缺契约——所以 delivery 即使注册，也只能产出一小部分。

## 三、逐工位解锁条件（一条一个，可验证）

1. **control**：状态改 `ready` 的唯一前提=本机确实可自驱。当前 `ready_paused` 与 AutoYield 的 pauseLite 同义，需在**非工作时段**（19:00–09:00）才许可放行；放行后判据=`station_drive --station control --once` 产生卡或写 NO-WORK 记时。
2. **visual**：本机无 ComfyUI（`D:\ComfyUI` 也不存在），视觉工位只能落在 bm-c；bm-c 的 8188 在 2026-11-11 02:19 曾被证 `route=ckpt` 可用（`cph4/fleet/asset-lib-v1/comfy-bm-c.json`），故该状态应改为「在 bm-c 上 ready」，或本机装 ComfyUI。
3. **audio**：绑 bm-b，物理离线 → 上电即解（零催办）。
4. **brain**：本机未装 → 要么装（轻模型档），要么在 bm-m/bm-c 注册。
5. **delivery**：两步——① 注册工位；② 补齐 16 个工序的 `PRODUCTS.outputs/commands`（每补一条，该机就多一道能自己干的活，V3 文档 §七原话）。

## 四、与本班其他结论的关系

- 旧派单器（`Tools/fleet-dispatcher.ps1`，2026-11-11 已退役）仍在每 10 分钟报 STARVED-EXEC / IDLE-WITH-WORK，`proxy-event-carrier.ps1:63` 又把它当新旗消费 → 每班被同一个假 P1 唤醒。**它读的旧队列在 origin 上已被 `4ced13103` 清空**，所以这些旗与真实供给无关。
- 真实供给面就是本文第一张表：五工位全关。修完任一工位，才谈得上「机器自己找活」。

## 五、证据复现命令

```
cd C:\Users\sjs20\Desktop\FluxGroup\_pub\wt-v727
python Tools\fleet\station_drive.py --station <control|visual|audio|delivery|brain> --dry
```
输出字段 `blocked` / `would_create` / `unknown_output` 即本文数据来源。
