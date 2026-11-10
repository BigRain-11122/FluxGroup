# Tools 知识页

> 自动生成 2026-11-11 04:27，来源 906 份摘要

# 🛠️ Fleet & Media Operations Directory Overview

## 1. 目录功能定位
本目录是**“巡逻舰队”（Patrol Fleet）监控系统**的核心逻辑库，专为多业务域（游戏、量化交易、内容产线等）提供自动化状态追踪与合规检查。主要职责包括：
*   **基础设施运维**：机器初始化、Git 仓库同步/迁移、磁盘清理、集群心跳监控。
*   **业务合规审计**：量化回测数据一致性校验、禁开策略拦截、决策文档归档。
*   **内容生产质检**：视频剪辑稳定性分析（抖动/闪烁检测）、AI 生成痕迹识别、资源资产规范审查。
*   **资源调度与治理**：显存/内存动态分配、任务队列分发、本地沙箱测试执行。

---

## 2. 关键模块与入口 (Key Modules)

### 🚀 基础设施与部署 (Infrastructure & Deployment)
| 文件 | 核心功能描述 |
| :--- | :--- |
| `Tools/bootstrap-machine.ps1` | **新机器自动化初始化**：检查依赖、生成 SSH 密钥、注册任务，确立机器身份。 |
| `Tools/fleet-link.ps1` | **分布式同步服务**：监听 Git 状态变化，通过 HTTP 接口实现代码库双向同步与健康检查。 |
| `Tools/fleet-hot-sync.ps1` | **热同步保护**：在保留本地工作前提下同步至主分支，防止重排冲突遗留（强制 `--ff-only`）。 |
| `Tools/migrate-fluxgroup-to-d.ps1` | **仓库迁移与回滚**：将 FluxGroup 仓库从 C 盘迁移至 D 盘，含 Git Bundle 备份与 MD5 校验。 |
| `Tools/git-atomic-push.py` | **原子化推送**：防止多窗热推环境下的竞态冲突，构建临时索引并执行安全闸检查。 |
| `Tools/disk-sweep.ps1` | **磁盘清理**：统计可疑文件/缓存，自动删除超过 7 天未修改的废弃文件。 |
| `Tools/fleet-poke-worker.ps1` | **后台唤醒进程**：执行代码拉取、健康检查及任务注册，通过锁机制防止并发冲突。 |
| `Tools/register-fleet-link.ps1` | **服务注册**：以非特权用户身份注册并启动监听任务，配置 S4U 凭据实现无交互运行。 |
| `Tools/oversight_deploy.ps1` | **版本部署校验**：比对源文件与已部署文件字节内容，解决逻辑漂移问题。 |

### 📊 量化审计与合规 (Quant Audit & Compliance)
| 文件 | 核心功能描述 |
| :--- | :--- |
| `Tools/quant-audit-probe.ps1` | **独立回测审计**：检查权益一致性、未标记仓位及年化指标异常（Q1-Q3）。 |
| `Tools/banned-direction-gate.ps1` | **禁开策略拦截**：依据正则模式检测并拒绝包含被禁策略方向的预注册文件。 |
| `Tools/quant-nav-recompute.ps1` | **权益曲线重算**：从原始行情数据独立重算关键指标，验证公司报告准确性。 |
| `Tools/quant-audit-cadence.ps1` | **审计节奏执行器**：自驱动循环调用探针，定期计算交付指标差异并追加至账本。 |
| `Tools/quant-oversight-digest.ps1` | **监督摘要生成**：扫描预注册文件与数据资产，计算引用率、单起点风险及缺口状态。 |
| `Tools/rename_resubmit_detector.py` | **语义规避检测**：利用 bge-m3 模型检测通过同义替换规避“已判负”清单的重提内容。 |
| `Tools/decisions-arch-certify.py` | **决策归档迁移**：将《decisions.md》中特定日期且状态为"executed"的段落迁移至归档文件。 |
| `Tools/orders_append_cloudoff_r1020.py` |
