# 机队主控粘滞锁存判例（R2.55·2026-10-31 bm-a）

## 判例一：`reset --mixed` 不重挂分支 = 后续提交全落游离头
R2.54（17:31）用 `git reset --mixed origin/main` 收口分叉，但**没有 `git checkout -B main`**。结果 HEAD 留在 detached 状态，下一轮 `master_agent.py` 的提交全部落在游离头上，永远无法与 origin 收敛。R2.55（20:45）接手时实测：`## HEAD (no branch)`、93 behind / 8 ahead、`UU Tools/task-s4u-backlog.md`。
**正法**：`git reset --mixed origin/main` → 定向 checkout → **`git checkout -B main`**（关键补步）→ `git rev-parse --abbrev-ref HEAD` 必须返回 `main`。

## 判例二：`master_agent.py:489-499` 粘滞锁存（sticky masquerade latch）
```python
stale = age > fallback_stale_s
if prev_by and prev_by != owner_node:
    stale = True   # the last tick was itself a fallback: the real master is still dark
```
本机一旦 masquerade 写过一次 `MASTER-TICK`（`last_tick_by=bm-a`），下一轮 `prev_by != owner_node` 必然为真 ⇒ 永远再判 stale ⇒ 永远 masquerade ⇒ 每轮再写 tick。**唯一解锁路径 = pull 到 origin 的 bm-m tick**，而分叉+detached 的树永不 pull ⇒ 自证死循环：每 20 分钟多一笔提交、分叉单调加深、盘上文件永久冻结、L0 探针永久报警。
**处置**（不改受保护代码）：把工作树对齐 origin/main 并把 tick 恢复成 bm-m 版，下一轮即 standby。实测 20:46:47 / 20:51:47 两轮 steward 均未产提交、未写 tick。
**正法候选（候 CEO 令·受保护件）**：①删该分支，只用 `age > fallback_stale_s`；②或增 `last_real_master_ts` 字段，只由真主控刷新。

## 判例三：产出者不是 HQ-MasterFallback
无任何计划任务执行 `master-fallback.cmd`；`HQ-MasterAgent` 自 10-29 15:46 Disabled。实际产出链 = **HQ-Steward（PT5M）→ steward.cmd → steward.py → master_agent.py**。追 master-agent 提交来源时先看 `HQ-Steward`。

## 判例四：L0 探针谓词与班表天然冲突
`DISPATCH-LOG.md age > 3h` 测「有没有人写日志」，而班表相邻班间隔可达 4.2h（17:31→21:43）⇒ 每个 4h 级间隙必然报警，与机器健康无关。建议改测 `MASTER-TICK` 新鲜度，DISPATCH-LOG 降二级（受保护件，候裁）。

## 台账追加的两个技术坑（本班实锚）
1. **混排换行制式**：`DISPATCH-LOG.md` / `CEO-PROXY/LOG.md` 仓库内本就是 CRLF 与 LF 混排。用 `io.open(...,'w',newline='')` 或全量 CRLF 归一化会把 500+ 行历史行判成改写（实锚：516 insertions / 515 deletions）。**追加一律二进制 `open(path,'ab')` + 仅补 `sep + body`**，追加后 `git diff --numstat` 必须只见 `N 0`。
2. **Python `-c` 双引号字符串吃反斜杠**：`\`` `\r` `\b` 会被解释（实锚：`reset`→`eset`、`backup`→`ackup`）。含反斜杠/反引号的正文一律先写临时文件再二进制追加。