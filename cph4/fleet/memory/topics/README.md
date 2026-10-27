# L2 主题层跨机只读镜像（CEO 令 2026-10-24「彻底同步·共享所有记忆和文档」）

## 这是什么
各机 L2 主题文件（`<home>\.codely-cli\memory\topics\*.md`）的 git 侧只读镜像，
目的是让 L1 `CODELY.md` 里那些指向 home 路径的主题索引在**任何机器上都能取到原文**。

## 这不是什么（治理红线，承 memory-curator 二节/五节）
- **不是 L0 联合正本**：L0 注入层仍各机本地治理（`Tools/memory-budget-gate.py` + 4h 闸），
  联合回灌/union replace-down 机制**永久退役、永不复活**（CEO 令 2026-10-18，正身
  `cph4/fleet/memory/README.md`）。
- 镜像文件**不参与注入**，不被任何闸读取，不会重新撑大 L0。
- 单一写者：只有权属机器（见每文件头部来源行）写自己的主题文件；他机只读。
  冲突时以权属机器 home 目录版本为准，重新镜像覆盖本目录。

## 刷新方式（手工，低频）
```
Copy-Item "$env:USERPROFILE\.codely-cli\memory\topics\*.md" <repo>\cph4\fleet\memory\topics\ -Force
```
新机部署：`Tools\agent-library-sync.ps1` 装 skill；本目录随 git 自动到件。

## 机器快照
各机 L0/L1 全文快照在 `..\machine-snapshots\<node>\`（同样只读，供跨机考古与交接）。