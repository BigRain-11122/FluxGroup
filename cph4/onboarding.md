# Onboarding — 新机器一键部署机制（CPH4 Labs）

> CEO 令（2026-09-23）：「建立好新机器一键部署的能力」
> 集团层编排器 = `Tools/bootstrap-machine.ps1`（幂等·静默·角色化）；本文件=机队部署章程（`governance.md` §8 接线）。

## 0. 三层模型（什么自动化、什么永属 CEO）

| 层 | 内容 | 归属 |
|---|---|---|
| **L0 CEO 物理件层**（刻意不自动化=安全律同源） | SSH key→GitHub 授权（身份/钥匙刻意不备份，FLEET-OPS §4）；Tuanjie Cowork 安装（codely CLI 载体）；Tuanjie Hub 登录+MCP 授权；引擎版本安装；账号域 | CEO/装机人 |
| **L1 一键脚本层** | `Tools/bootstrap-machine.ps1` 六相：P0 前置检查（git/python/codely/磁盘水位）→ P1 身份（key 生成+GitHub auth 实测）→ P2 拉仓（HQ+各产品仓按角色）→ P3 环境（**全局 git 身份写入[versioning §4.1 所有者身份·幂等]**+引用各司自件）→ P4 计划任务（静默律注册）→ P5 验证报告（READY/PARTIAL+物理件清单） | 集团仓 |
| **L2 各司自件层**（引用不复制） | bigmoney=`bootstrap.py`（依赖+smoke20+仪表盘）+`Tools\register_loop_task.ps1`；biggame=`tools\MachineBoot.ps1`（08 号自举：skills/引擎模块/运行时目录/任务注册，环境全绿才开门禁）+`machine.json`（本机身份，刻意不入库）；fluxverse=`Tools\devloop\register_loop_task.ps1`+FluxVerseTick 直注；fleet 登记=FLEET-OPS §2 接入五步+`TRANSFER.md` 大资产通道 | 各产品仓 |

## 1. 一键用法（新机三步）

```
1. git clone git@github.com:BigRain-11122/FluxGroup.git      # 前提：装 git + SSH 授权（CEO 物理件）
2. powershell -NoProfile -ExecutionPolicy Bypass -File FluxGroup\Tools\bootstrap-machine.ps1 `
       -Roles group,bigmoney,biggame,fluxverse,media -MachineId <新机编号>
3. 读 .codely-cli\onboarding\onboarding-*.md：READY=机器就绪 / PARTIAL=按 CEO 物理件清单逐项补，补完重跑
```

角色表：`group`=集团层（FluxGroup-EvolutionTick 周轮·自含 HQ VBS）/ `bigmoney` / `biggame` / `fluxverse` / `media`——按机器使命选装；缺什么补什么。

## 2. 五条部署纪律

1. **幂等律**：一切动作已就绪即 PASS 跳过；`Register-ScheduledTask -Force` 重注册=自愈刷新非破坏；**已部署机重跑=全机体检**（报告在 `.codely-cli\onboarding\`，gitignored）。
2. **静默律**：一切任务注册必须 `InvisibleRunner.vbs` 包装（U060 范式·本仓 `Tools\InvisibleRunner.vbs`=集团件），零弹窗零闪窗。
3. **引用不复制**：各司自举件永远调用它们自己仓里的（版本随其仓演进），编排器只做检查/编排/报告——禁在集团层重写任何产品自举件。
4. **身份律**：SSH key 缺则自动生成，但 GitHub 授权=CEO 物理件；`machine.json` 永不入库（跨机合并覆写坑=其 pit #48）。
5. **归属律**：集团任务（EvolutionTick）用集团仓内 VBS 自含注册——2026-09-23 修正：该任务此前曾引用 FluxVerse 仓内 VBS=跨仓耦合，编排器重注册即自愈。

## 3. 验证判据（deployed = READY + 首拍心跳）

- 编排器报告 **RESULT: READY**（exit 0）——P0-P5 全 PASS/FIXED，零 NEEDS_USER
- 各司心跳首拍入台账（fleet 心跳 / 自动化快照 / engine-tick ledger）——机器进机队以台账为证，不以「装完」为证
- PARTIAL 态：按报告「CEO 物理件清单」逐项补齐后重跑，直至 READY

## 4. 与既有法的关系（反重复 · 引用不复制）

- `FLEET-OPS.md` §2 接入五步 = bigmoney 角色的 fleet 登记面；§4 三级备份模型 = 「git clone 即全量重建」的既有依据。
- MiniGame `tools/AUTOMATION.md`「新机器接入」节 = biggame 角色的权威说明书（其 `MachineBoot.ps1` 2026-09-18 已立，先于本机制）。
- `scheduling.md` §2 = 部署后算力上工（verdict 驱动）；`retention.md` §2 机队面 = 部署后水位监测。
- `governance.md` §8 = 本机制接线位；编码律=脚本 ASCII-only 全员适用。
