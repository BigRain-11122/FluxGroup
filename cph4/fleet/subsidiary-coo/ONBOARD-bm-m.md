# bm-m 现状与自检（子公司运营主控）

> 2026-10-29 实测。**不要按"从零装机"理解本文件**：Mac 已经在网、已经是总控，这里只写"怎么确认它在干活、卡在哪"。

## 一、已就位的件（origin 正身）

| 件 | 路径 | 说明 |
|---|---|---|
| 总控声明 | `cph4/fleet/MASTER-NODE.json` | `"node": "bm-m"` —— 2026-10-29 由 bm-a 切到 Mac，bm-a 转热备/工作机 |
| 安装包 | `Tools/fleet/mac-setup/setup-mac.sh` | 稀疏克隆（`--filter=blob:none`），**只拉控制面**，几十 MB，不拉媒体 |
| 一键一轮 | `~/FluxGroup/tools-run-once.sh` | 心跳 + 主控一轮 + 领一件轻活；默认不常驻 |
| 主控 | `Tools/fleet/master_agent.py` | 每轮造活/路由/派活/盯租约 |
| 车道执行 | `Tools/fleet/lane_agent.py` | 领本机活、执行、回执、上报 |
| 条线正身 | `cph4/fleet/LINE-REGISTRY.json` | 七司 + 内容线 + 工段 |
| 本席 | `cph4/fleet/subsidiary-coo/` | 条线判读/归因/升级（BLUEPRINT+AGENTS） |

## 二、三件自检（各一行，跑完即知有没有在管）

```bash
bash ~/FluxGroup/tools-run-once.sh
# 1) 看自己那一行：STANDBY/ACTIVE node=bm-m declared_master=bm-m
cat ~/FluxGroup/cph4/fleet/lanes/bm-m.json
# 2) 看 jobs 是否非空、idle_reason 是什么
tail -3 ~/FluxGroup/cph4/fleet/dispatcher/MASTER-LOG.md
# 3) 看队列 q=OPEN/DONE/... 和 flags（LINE-STALLED / IDLE-CONFIRMED）
```

判定口径：
- `q` 第一段长期 0 + `bm-m IDLE-CONFIRMED xN` 递增 = **主控活着但没活干**（2026-10-29 曾连续 288 轮）。
- `LINE-STALLED` / `LINE-BLOCKED` = 某司断在某道工序，要出归因，不是加机器。
- `bm-a OFFLINE` = 工作机没上线，夜间产能少一台，不代表 Mac 有问题。

## 三、让它常驻（可选，不建议）

```bash
INSTALL_DAEMON=1 bash ~/FluxGroup/Tools/fleet/mac-setup/setup-mac.sh
```
装的是每 10 分钟醒一次的服务。**不建议**：笔记本合盖/带走即断，且旧定位令要求随身机不 24h 插电长跑。要用时手动跑一轮就够。

## 四、红线

1. 不装本地大模型以外的重型算力件（ComfyUI/训练栈）；无 CUDA，不接 GPU 活。
2. 不克隆九个子公司仓（媒体/美术/模型都在别的机器上，拉下来纯占盘）。
3. 不写他司仓：只读条线与证据目录，产出只写 `cph4/fleet/queue-receipts/`、`cph4/fleet/subco/`、`cph4/fleet/dispatcher/`。
4. 不碰资金/发布/账号写操作（CEO 保留面）；凭据只进 Keychain。
5. 单件写入 >20GB 不接（`role_class=control` 硬拒）。

## 五、当前已知缺口（2026-10-29 22:57）

| 缺口 | 证据 | 谁修 |
|---|---|---|
| 主控空转 288 轮 | `MASTER-LOG.md` cyc=537 `bm-m IDLE-CONFIRMED x288` | 队列里没活→已补 3 条子公司运营规则（`WORK-RULES.jsonl` R-SUBCO-*） |
| bigstream-drama 堵死 | `LINE-BLOCKED bigstream-drama` | 归因件 `queue-receipts/bm-m-drama-unblock.md` |
| bm-b/bm-c 工作树落后 | `MASTER-AGENT-v1.md §十` 第三条 | 各自本机跑 `Tools/fleet-hot-sync.ps1`（禁远程） |
| bm-a 离线 | `flags=bm-a OFFLINE` | 该机自起（工作机白天让路属正常，夜间应上线） |