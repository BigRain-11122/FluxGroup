# 机队满负荷接管规则 v1（bm-m 主控 · CEO O-20261030：所有机器满负荷且归主控）

## 一、管线（每 60s 一轮，全自动）
感知(心跳/负载) → 造活(业务正典出真活) → 结构闸lint → 晋升(READY→OPEN) → 写车道 → 执行机自验认领 → 执行 → 回执/产物验证 → 守门对账

## 二、五条铁律（根治断链）
1. **真相源=git 树**：结构校验一律 `git ls-tree`，禁止用主控本机文件系统判断仓内工具（稀疏检出误杀过 5 张真卡）。
2. **跨机路径各机自验**：C:/K:/D: 开头的 when_all/requires 主控跳过校验，**由 lane_agent 在执行机本机校验后才认领**——输入不存在就不领，绝不假开工。
3. **死单不挡路**：队列里 INVALID/FAILED 的同名单据会被新活源重评顶替，禁止尸体永久堵晋升。
4. **库存地板=2**：inventory_guard 每轮核对每机可领库存，低于 2 自动回补+告警留痕（/tmp/inventory-guard.log）。
5. **白天让位唯一例外**：公司生产力机 09:00-19:00 只吃 day_ok 轻卡（CEO 工位法），其余机器 24/7 满负荷。

## 二·六、活体文件律（2026-10-30 最深根因）
6. **改代码先确认"谁 import 它"**：master/lane 把 `Tools/` 塞进 sys.path，所以**活体是 `Tools/backlog_fill.py`**；`Tools/fleet/backlog_fill.py` 已改成纯转发 shim。同名的两份实现 = 静默失效的头号来源（修了半天，执行机读的还是另一份）。改前必 `grep -rn "import <模块>" Tools/fleet/`。
7. **新模块必须进 fleet-sync 白名单**：不在清单里就同步不到 `C:\Fluxgroup\FleetRuntime`，执行机 import 失败被 except 吞掉——和 backlog_fill 缺失同一种死法。

## 三、防假忙
- DONE 必须有交付物或回执证据（deliverable_exists / receipt 在仓），无证据 = 重开。
- 主控只认「别的机器的 RUNNING/DONE + 证据」为产出，自己的回执不算机队产能。
- 活源三问（造活前必答）：工具在 git 树？输入在认领机磁盘？验收物写得出路径？

## 三·五、依赖自装（CEO 令"缺什么让他自己装啊"）
- lane 开工前调 `env_selfheal.ensure(tool)`：**在执行机自己进程内**用 winget 正典口径静默装（Gyan.FFmpeg / Git.Git / Python），装完再跑；装不上就 SELFHEAL-FAILED 响亮失败，绝不静默假开工。
- 主控绝不远程装任何东西（机队设计禁跨机执行）；缺依赖登记 CEO-DEFECT-LEDGER，由该机自愈解决。

## 四、当前夜间接力链（全自动，无需人工）
小钢炮: Q-AUD 合流 → Q-TTS-1202 配音57集(夜) → Q-MIX-1203 混音60集(when_all=TTS产物,自动接力)
传家宝: Q-GPU-BMC-001 租约点火 → POOL-0021/0022 KF 试烧(租约成功即解锁)
生产力机: 19:00 后 v718 重建链(待 CEO 人工闸裁决) + day_ok 轻卡白天挂
主控机: 35B 常驻，R-DX 诊断每轮自产
