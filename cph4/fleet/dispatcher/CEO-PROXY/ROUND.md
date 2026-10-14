# ROUND — CEO 总调度代理席·每轮巡班协议

> 班次：durable cron `43 0,3,6,9,12,15,18,21 * * *`（8 班/日）·7 天物理到期→每轮步7自检重建。
> 每轮目标：三机正常运转+死线在轨+CEO 关注点零违例+台账闭合。**零判断件时一轮收敛（≤10 次工具调用）**，禁为跑而烧 token。
> 全程纪律：进程内 `&` 禁 spawn 控制台子进程；一切路径用绝对地址；台账追加只走 python 尾锚正法。

## 步0 读入（并行做）
- 本目录 CEO-DIRECTION-BRIEF.md + DEADLINES.md
- docs/orders.md 尾部 ~30 行（read_file·offset=总行数-30）
- cph4/fleet/dispatcher/ 下 DISPATCH-LOG.md 尾 10 行 + NEED-JUDGMENT.md + POOL.json

## 步1 三机实测（先实测后结论·新鲜验证律）
```
Set-ExecutionPolicy -Scope Process Bypass -Force
& "C:\Users\sjs20\Desktop\FluxGroup\Tools\fleet-dispatcher.ps1"   # L0 探针拿旗
& "C:\Users\sjs20\Desktop\FluxGroup\Tools\fleet-reality.ps1"      # 三机全景（在网/心跳新鲜度/同步头）
```
- 心跳停摆判读：bm-c 10-14 判例——poke 空 body 只修拉取不修停摆；**停摆=poke 带 tasks 白名单唤醒**：
```
Invoke-RestMethod -Method Post -Uri "http://<tailnet_ip>:8790/poke" -Body '{"reason":"<ASCII短串>","tasks":[<该机 wake_tasks>],"repos":[]}' -ContentType 'application/json'
```
（IP/wake_tasks 取 Tools/fleet-nodes.json；bm-b 打盹=重试即可勿判死；PS5.1 取 /status 的 '.' 属性走 .PSObject.Properties['.']）

## 步2 五雷达扫描（判读标准=BRIEF §二/§三）
1. **满载雷达**：三机 GPU/CPU 空转（util 0% 且队列空 >30min）→按自链/排产表/POOL 点火或补卡；bm-c GPU=生成视觉-only·bm-a=工作日白天 GPU 零排单（CPU 解禁）。
2. **死线雷达**：DEADLINES.md 逐行对 orders 最新回执核态；at-risk（距窗 <2×剩余工时）→重排/催办/如实披露 ETA（禁砍闸换速度）。
3. **回执雷达**：近 24h @机名 派单行——>2h 无回执=poke 唤醒；>24h=升 E1 委员会通道。
4. **关注点雷达**：BRIEF §二 每轮抽 5 项轮查（质量闸执行/匀速与剪口/本地引用计数/成本台账/意义门/年代穿帮/活人感…）；违例→执法单。
5. **盲区雷达**：BRIEF §三 抽 3 项（派单≠被消费/守护件存活 cron_list/后台批日志新鲜度/竞态收尾）。

## 步3 落单（只有真要派时）
- orders 行格式=现役三段式（时间戳|命令/事件|执行态）·行内必带 **@机名+lane+回执窗+验收物**。
- 台账写入：python 脚本（utf-8-sig 探测 BOM·newline=''）读尾部→锚定当前最后一行→追加；**禁从 GBK 乱码复原中文当锚**（用 unicode_escape 打印核对真尾）。
- 提交：真 git 路径 `& "C:\Program Files\Git\cmd\git.exe" commit -m "..." -- <pathspec>`（pathspec 形式防吞他窗暂存面）；push 带 origin；PS 假红以 `<旧sha>..<新sha>` range 行为准；push 被拒→fetch 后 worktree 内容级合并正法（git show <sha>:file→worktree 尾追加→推→reset --soft+定向 checkout 收敛）。
- poke 目标机（步1 正法）→POOL.json 开卡/改 status=assigned+claimed_by（commit 即锁）。

## 步4 决策
- T1 代决即生效（常设授权令）；物理件/保留面→DEADLINES.md waiting-CEO 区登记（零催办）；云端 >500 积分=不创建·呈 CEO 真金闸。

## 步5 记账
- LOG.md 每机一行（时刻+verdict+行动）+本轮订单行摘要；DEADLINES.md 状态列随 orders 新回执翻新；一并 pathspec 提交推送。

## 步6 出声纪律
- 正常=静默（只记账）。仅 CHARTER §五 三条件向 CEO 出声（大白话+绝对路径+已决方案）。

## 步7 cron 自续（每轮必做）
- cron_list 查本席班次（cron `43 0,3,6,9,12,15,18,21 * * *`·recurring·durable）——缺失或临期（≤2 天）即按 CHARTER §四 原参重建；顺带清过期一次性 cron 残留。

## 附：已知停摆唤醒白名单（fleet-nodes.json 为正身）
- bm-c=Bigmoney-IterationLoop/SaturationEngine/ResidentDispatcher/Autofill/PoolWorker+MiniGame 系 tick
- bm-b=Bigmoney-IterationLoop；bm-a=各司 OSLoop+Bigmoney-IterationLoop
- 常驻 LLM 驻卡堵生成道（free<2G 非烧制态）→ollama stop+pin 任务 disable·整卡还生成线（10-14 判例）
