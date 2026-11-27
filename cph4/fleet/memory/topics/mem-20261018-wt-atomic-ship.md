# mem-20261018 — worktree 内容级原子推判例（多窗分叉热推期·bm-a 交互窗 5 连实弹）

- **场景分诊**：本地 main 与 origin 分叉（他窗在飞 11 ahead/40 behind）→ `git pull --ff-only` 必败 → 二选一：`Tools/git-atomic-push.py`（API 链·纯文件增改面）或 **worktree 内容级合并**（需 mv/删除/改名面时唯一解）。交接令「worktree 内容级合并/API 原子推既定正法」两路皆合法。
- **worktree 正法五步**：fetch → `git worktree add --detach <TEMP>\wt-* origin/main` → 内容级应用 → 反转闸 `python Tools/git-no-reversal-check.py <cand> origin/main --depth 10`（my-dels 匹配）→ `git push origin <cand>:refs/heads/main`（**必带 origin 名**·承 10-15 refspec 判例）→ 复取 `merge-base --is-ancestor` 验在链 → `worktree remove --force`。
- **坑①共享台账禁盲全文件覆盖**：orders.md/LEDGER.md/CODELY.md(L1) 这类多窗共享面，origin 侧常有本盘没有的行（实录：LEDGER 他窗两行首跑行被反转闸当场拦下；L1 有本盘已删的「子公司开线事实」指针行）→ **正法=origin 基座+只追加本盘独有行**（`| 20` 行过滤+`in base` 去重）；L1 只织自己的锚点行（复用 patch-l1 幂等锚脚本对 origin 基座跑）。
- **坑②陈旧本盘副本勿发运**：origin 已有更深版本时（实录：worker 拆除/sync 退役桩 origin 版更彻底），本盘旧副本全文件覆盖=**回退他窗成果** → 发运前 `git diff origin/main -- <paths>` 逐件判真 delta，陈旧面跳过。
- **坑③闸与编码**：大改写（整行重写）必触 REVERSAL——正法=程序化 `my_dels_of(origin_text, new_text)`（esc60 截断）供闸匹配「有意改写」；子进程管道输出在本机=GBK（`r.stdout.decode("gbk")` 勿 utf-8→\ufffd 再印 GBK 控制台炸）；闸拦先判基座新旧（origin 手术窗内又动=假阳性→fetch+重放，他窗 13:2x 判例同形）。
- **附带**：glob 工具按 .gitignore 滤文件（media 正片/full_mv 搜不到·报「N ignored」）→ list_directory/Get-ChildItem 兜底；活树收敛=卸本地 staged 改名（防他窗 commit 误吃）+磁盘副本留置走「原子推后本机副本」判例族分诊，**禁 reset --hard**（他窗 13:2x 孤儿化判例）。
- **复用件**：`home\.codely-cli\memory\curator\wt-ship-*.py` 5 件模板（memgov/council/auditwave/mvfeedback/supervisor·含 fetch-重放重试环+dedup 守卫+闸匹配）；orders/LEDGER 尾追加脚本的「已存在即跳过」幂等设计=并发孤儿找回安全的关键。
