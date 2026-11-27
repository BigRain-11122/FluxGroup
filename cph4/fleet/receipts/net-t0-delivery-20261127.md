# T0 令投达回执 — 2026-11-27 17:45 令

CEO 原话：「你传过去让他们执行，ceo最高级别命令」
令义：bm-a / bm-b / bm-c / bm-m-1 立即执行 `cph4/fleet/AGENT-NET-UNIVERSAL-PROMPT.md` + Windows 管理员跑 `Tools/fleet-fix-admin.ps1` + 写回执；全文=`cph4/fleet/T0-ORDER-NET-SELFHEAL-20261127.md`（同文 `docs/`）。

## 投达结果

- **bm-c**：`POST /sync path=docs/orders.md mode=union gz` → `{"ok":true,"applied":204,"kind":"union"}`（T0 行已并入令账）。`POST /poke` → accepted 17:52:50。`repo_heads['.']` 由 `2d4d0e37` 变为 `ef7287d0`（拉取已发生）；`last_pull.ts` 仍显示 17:37:41（worker 戳记滞后，非未拉）。
- **bm-b**：8790 down（无执行入口）。Taildrop 投达 `T0-ORDER-NET-SELFHEAL-20261127.md`、`T0-ROW.txt` 均 rc=0（此前另有 6 文件工具包 rc=0）。需其本机 `tailscale file get` 后执行。
- **bm-m-1**：直连；Taildrop 投达 T0 全文 + 令行均 rc=0（此前提示词+README 已投）。
- **bm-a**：T0 行已追加到本机两份令账（C 53,579B / D 181,828B）；`unattended=true`；管理员脚本在 main。

## 必须披露的事故与修复（同一窗口）

我用 GitHub Git Data API 建树时，取 base 提交的 JSON 因**中文作者名导致 ConvertFrom-Json 失败**，`base_tree` 变成空值 → 提交把 main 整棵树替换为少量文件（8,047 文件被删）。另一会话先以 `restore canon` 提交（27977a54）修复；我在追加 T0 令时**再次复现**（1fa57f15）。现已再次恢复：

- 以恢复父树 `801e0989`（29 个根条目）为 `base_tree`，加入 T0 全文与回执 → 提交 `a3605114`，`main` 根条目 **29**（与恢复前一致）。
- 修复手法：所有树/提交 SHA 改用 `gh api --jq .tree.sha` 读取（不再解析带中文的提交 JSON）；建树前先取 base 根树并**要求条目数 ≥20 否则中止**。

## 执行侧仍未满足的部分（不在投达面）

- bm-c 的 `task_states` 多数 Disabled，`Bigmoney-IterationLoop` 为 Ready；OrderSentinel 只按映射唤醒公司 loop，无“执行任意提示词”的席位。
- bm-b 无 8790、无 SSH/WinRM/RDP 凭据；Taildrop 只能送文件不能执行。
- 因此“令已投达”成立，“令已在本机自动执行”需要它们本机有运行中的 Codely/loop；否则需在那两台各跑一次（README 已给两行命令）。

## 验证

- main `a3605114`：根树 29 项；`Tools/fleet-*.ps1` 4 件、`cph4/fleet/{AGENT-NET-UNIVERSAL-PROMPT.md,FLEET-NET-AUDIT-20261127.md,T0-ORDER-NET-SELFHEAL-20261127.md}`、`docs/T0-...` 均在树。
- bm-c /sync：`applied=204`；/poke accepted 17:52:50。
- Taildrop：bm-b 2/2 rc=0、bm-m-1 2/2 rc=0。
