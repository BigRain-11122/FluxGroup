# 断点裁定：节点永远拿不到新码（2026-11-06 17:50 实测）

## 一句话

三台 Windows 的仓库里都有**不在任何远端分支上**的本地提交，而 poke worker 只做
`git merge --ff-only origin/<本机分支>`。ff-only 遇上分叉必然失败，于是主线推多少次、
工具改多少版，机器上跑的还是几个月前的旧码——这就是「来来回回修了多少次还是有问题」
的结构性原因。

## 实测证据（rollout.py 四环体检，17:47）

```
机器     L1 可达   L2 会拉   L3 是新码                      L4 会跑
bm-a   PASS     PASS     FAIL(node HEAD=c99a468 我方=42eb585) -
bm-b   PASS     PASS     FAIL(node HEAD=e7c3459 我方=42eb585) -
bm-c   PASS     PASS     FAIL(node HEAD=f1bbe72 我方=42eb585) -
```

- 三台 HEAD 与远端分支的祖先关系：`c99a4687f` 虽在 origin 对象库里但**不在 main 历史**；
  `e7c345993`、`f1bbe7291` 在 origin **根本不存在**（纯本机提交）。
- 旁证一：bm-a 在 17:33 仍报 `HQ-ProductionClaim:deny` —— 它的 `Tools/fleet-nodes.json`
  还是"该任务不在白名单"的旧版（新版 b683ab246 已把它加进 wake_tasks）。
- 旁证二：bm-c 在 17:37 仍报 `HQ-ProductionClaim:off-skip` —— 它的 worker 还是旧码，
  没有 b683ab246 里的 `:REENABLED` 分支。
- 拉码不是没跑：三台都回报 `pulls [.:updated]`，但 HEAD 分毫不动（ff-only 失败被吞）。

## 后果（两件坏事同时成立）

1. **改码=零效果**：所有 Tools/*.py、*.ps1 的修复都停在 origin/main，机器上永远旧码。
2. **执行器禁用后无法自愈**：`silence-enforce.ps1` 的兜底会把执行器任务 Disable（bm-a
   六条 prod 循环全 Disabled、bm-c 的 HQ-ProductionClaim Disabled），而 poke 设计上对
   Disabled 一律 `off-skip`，没有任何远程入口能把它拉回来。结果=**机队静默停产而心跳照常绿**。

## 一次修复（每台执行一次，需在机器上跑）

```powershell
# bm-a: C:/Users/sjs20/Desktop/FluxGroup
# bm-b: C:/Fluxgroup/FluxGroup
# bm-c: K:/Fluxgroup/FluxGroup
git -C <root> branch salvage-20261106 HEAD   # 先留一条救命分支，本地提交不丢
git -C <root> fetch origin main
git -C <root> reset --hard origin/main
```

重置后**全自动，不用再碰机器**：
`/poke`（reason 含 `enable-tasks`）→ worker v2.0 启用 HQ-ProductionClaim →
车道按 origin/main 的队列领卡。

## 已随本文件一起上线的修复（b683ab246，尚未生效）

- `fleet-poke-worker.ps1` v2.0：三条件同时成立才 `Enable-ScheduledTask`
  （roster 的 `enable_tasks` 名单 + reason 含 `enable-tasks` + 启用/启动分开记账），
  其余仍 `off-skip`，CEO 冻结面保护不变。
- `fleet-nodes.json`：bm-a/bm-b/bm-c 加 `enable_tasks=["HQ-ProductionClaim"]`，
  bm-a 白名单补回该任务。
- `silence-enforce.ps1`：`$NeverDisable` 名单，wrap 失败一律保留运行（宁可一次闪窗，
  不可一条线停一天）。

## 仍需补的一刀（未做）

worker 的 ff-only 失败被静默吞掉（只记 `pull-fail` 日志）。应改为：ff 失败时把
`forked=true / ahead / behind` 写进 status stamp，让 rollout L3 之外还能一眼看出
"这台机已经分叉"，而不是等下一个人再花半天重新发现。