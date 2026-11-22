# bm-c 本机总控排号器（BMC ORCHESTRATOR）v1

> CEO 令 2026-11-22：「本机的各种任务要做好排序，不要互相打架抢资源，要有本机的总控
> 智能体去负责排号，科学利用本地算力。」
>
> 正身：`Tools/fleet/bmc_orchestrator.py` · 状态：`cph4/fleet/state/bmc-orchestrator.json`
> 节律：计划任务 `Bmc-Orchestrator` 每 1 分钟 `--tick --quiet`

---

## 一、为什么要有这一层（2026-11-22 实测病灶）

| 病灶 | 实测 |
|---|---|
| 两个 ComfyUI 实例同时活着 | 8188（i2v 主渲染）+ 8189（PuLID 工厂）共享一张 16GB 卡 |
| 显存被打满 | 15657 / 16384 MB，util 100% |
| 内存见底 | avail 1.9–2.7 GB / 56 GB（load 95%） |
| 共享租约在 Windows 不可用 | `gpu_lease.py` 用 `fcntl` → `ModuleNotFoundError`，本机**从未有过真正租约** |
| 点火器不看资源 | `BmcIdleGuard` 空闲 10 分钟直接 `Popen` 银行里的活，不看谁在跑、不看优先级 |
| 重复任务 | `FluxGroup-ComfyGuard` 与 `FluxGroup-ComfyGuard-bmc` 跑同一脚本、同一端口、各 3 分钟 |

结论：本机此前只有"守卫"和"观测器"，**没有裁决者**。谁先起谁占，任务之间靠运气不冲突。

## 二、职责边界

```
        ┌──────────────── Bmc-Orchestrator (每分钟) ────────────────┐
        │  资源快照  →  租约裁决  →  死证回收  →  空闲归还  →  排号  │
        └───────────────┬──────────────────────────────────────────┘
                        │  acquire / yield (rc=0 / rc=3)
        ┌───────────────┴───────────────┐
   BmcIdleGuard（点火器）         未来接入：i2v runner / KF 批 / 训练
```

- **orchestrator 只裁决，不点火**：它决定"谁能跑、谁让路、下一个该谁"，不自己起批，
  避免与既有生产者形成双头。
- **生产者必须先拿租约**：拿不到就退出（rc=3 让路语义），不排队硬闯。
- **租约绑真实 pid**：点火器 Popen 后把子进程 pid 回填，子进程死 → 下一轮自动释放。

## 三、lane 模型

| lane | 名额 | 语义 |
|---|---|---|
| `gpu-exclusive` | 1 | 独占整卡（i2v、训练、KF 批） |
| `gpu-shared` | 2 | 轻量 GPU（需显存预算相加不超） |
| `cpu-heavy` | 2 | 多核 CPU 活（语料、装配、审计） |
| `cpu-light` | 4 | 单核簿记 / 探针 |

准入闸（按顺序）：
1. `machine-state.flag=paused` → 一律拒绝（CEO 让路首）
2. 同 name 重入 → 放行并续租（可换绑 pid）
3. GPU lane：已有 `gpu-exclusive` 持证 → 拒；`gpu-shared` 需相加不超余量
4. 显存：`free - 已预留 < need_mb` → 拒（银行 gpu 活没写 need_mb 时按 10000MB 估）
5. 内存：`ram_free < 3.0GB` → 拒
6. CPU lane：各自名额

## 四、优先级

`P0` 主控派卡 / CEO 直令 → `P1` 已立项批次 → `P2` 自驱备货 → `P3` 维护扫描。
同权按来源（lane 卡先于银行）与入队时间。银行 `prio` 字段接受 `"P1"` 或 `1` 两种写法。

## 五、回收

- **空闲实例归还显存**：任一 ComfyUI 端口连续空闲 5 分钟且不是当前持证端口 →
  `POST /free {"unload_models":true}`。**不杀进程**，服务保留，下次提交重新加载。
- **RAM 见底**：记 `ram-low` anomaly；不自动杀进程。
  本机 ollama serve 虽已退役（10-17 令），但 `11434` 被十余个工具当默认端点，
  停掉收益小风险大，因此只登记为「可回收候选」，仅在人工 `--reclaim --ollama` 时执行。

## 六、用法

```powershell
# 观测
python Tools/fleet/bmc_orchestrator.py --status     # 一屏现状
python Tools/fleet/bmc_orchestrator.py --plan       # 排号结果（NEXT / RUN / WAIT）

# 生产者接入（点火器/批脚本）
python Tools/fleet/bmc_orchestrator.py --acquire <name> --lane gpu-exclusive `
       --need-mb 12000 --ttl 7200 --prio P1
# rc=0 拿到；rc=3 让路

# 子进程已起，回填 pid（续租）
python Tools/fleet/bmc_orchestrator.py --acquire <name> --lane gpu-exclusive --pid <child_pid>

# 完成
python Tools/fleet/bmc_orchestrator.py --release <name>
```

## 七、已接入 / 已清理

| 项 | 处置 |
|---|---|
| `Bmc-Orchestrator` 每 1 分钟 | ✅ 已注册（S4U 被拒 → Interactive 降级 + 入 `Tools/task-s4u-backlog.md`） |
| `BmcIdleGuard` | ✅ 点火前 `--acquire` 闸；拿不到让路且不占银行状态 |
| `FluxGroup-ComfyGuard-bmc` | ⛔ 已禁用（与 `FluxGroup-ComfyGuard` 完全重复） |
| `bmc_supervisor.py` SEATS | ✅ 改指 `FluxGroup-ComfyGuard`，并新增 `Bmc-Orchestrator` 席位 |

## 八、已知缺口（后续）

1. **8188 无自动守卫**：`comfy_guard.py` 只认 8189；8188 挂了由 orchestrator 报
   `comfy-8188-down（无自动守卫）`，不自愈。是否给 guard 加 `--port` 另议。
2. **高频簿记任务未接租约**：ProdFinalize(10m)/ProductionRouter(5m)/ChainPublish(5m)/
   Supervisor(10m)/Autodrive(10m)/IterationLoop(5m)/LoopWatchdog(2m)/SatEngine(1m)
   属 CPU 簿记面，暂按"轻活可共存"处理，未逐条接入 acquire。
3. **`gpu_lease.py` 仍不可用于 Windows**：本机用 orchestrator 自带锁；共享脚本的
   跨平台修法另立单（不动 macOS 侧行为）。
4. **Interactive 降级**：注销后 tick 停摆，需提权转 S4U。
