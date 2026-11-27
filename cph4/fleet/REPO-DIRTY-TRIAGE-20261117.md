# 收敛后工作树差异分类（D-20261117-09·2026-11-17 06:2x）

## 一、口径

- 来源：`git reset --mixed origin/main` 收敛后（ahead/behind 实测 0/0）的 `git status --porcelain` 快照
- 总数 **781** 件（另 2 条为重命名行，已归并到目标路径计数）
- 全量逐行清单：`cph4/fleet/dirty-inventory-20261117.txt`（格式 `class | size_bytes | status | path`）
- **本轮不清理、不删除、不批量 add**（承 D-20261117-09 ①），本文件只做分类与执行配方

## 二、分类结果

| 类 | 含义 | 件数 | 说明 |
|---|---|---|---|
| **A** | 应入 git 的配置/台账/脚本/文档 | **629** | cph4 382／Tools 127／.codely-cli 25（memory topics）／docs 10／media 6／house 2 |
| **B** | 产物/媒体，留盘或走 gitignored `media/` | **95** | .png 71／.jpg 17／.zip 4／.mp4 3 |
| **C** | 运行时状态/日志（不入 git） | **57** | cph4/fleet 56（rt、state、dispatcher 快照）／docs/audits 1 |

## 三、硬阻塞（必须先处理，1 件）

- **136.8MB** `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/_superseded/full_mv_v727-oldlineage-20261108.mp4`
  - 超 U187 的 95MB 绝对红线，也超 pre-commit 的 20MB 出生级闸
  - 处置：**移入 gitignored `media/` 或留在原盘不入库**（`_superseded/` 本身是废弃线素材，无需入库）；交付以绝对路径直给 CEO（承 10-08 交付地址令）
  - 禁止：`git add -f`、`--no-verify` 强推

## 四、执行配方（交付工位·11-18 12:00）

1. **A 类（629 件）分批入仓**：按顶层目录分 6 批（cph4／Tools／.codely-cli／docs+media+house+根 3 件），每批一次 commit，消息带 `repo-triage(A 批N/6)`；每批后跑 `git status --porcelain | wc -l` 递减验证
   - 判据：A 类全入仓后 `git status` 只剩 B/C 与未分类项；单件 >20MB 零命中（pre-commit 未被 `--no-verify` 绕过）
2. **B 类（95 件）**：图片/视频/zip 一律**不入库**；其中仍被代码引用的（按 `rg` 反查路径）登记到 `cph4/fleet/ASSET-VAULT.json` 或对应产物清单，未引用的原地留盘
   - 判据：`git status` 中 B 类零 staged；`rg "<文件名>"` 命中项均有登记行
3. **C 类（57 件）**：确认 `.gitignore` 已覆盖 `cph4/fleet/rt/*/log/`、`state/`、`dispatcher/MASTER-*.json`；未覆盖的补规则，**不删除文件**
   - 判据：`git check-ignore -v` 对 57 件全部命中（未覆盖项已补规则且复验）

## 五、复验

- 三批完成后：`git rev-list --left-right --count HEAD...origin/main` = `N 0`（behind 恒 0）
- `git status --porcelain | Measure-Object` 应收敛到 B 类未登记项数量，且全部有归属
- 逾期动作：夜轮 03:07 记 chronic；下一轮禁止在脏面上 `git add -A`
