# 训练并发互斥 + 段专用件验收（2026-11-19 实锚）

## 一、并发训练：最隐蔽的"看起来在跑"

- 现象：同一份 `train-shallow` 上有两份 ~10GB 训练同时跑（18:14、18:55），
  随后又冒出第三份（18:58）。swap 顶到 6.3GB/7.2GB（总 7.2GB），
  free 页只剩约 800MB；**mlx_lm 一句错都不报**，唯一症状是"训练变慢"。
- 根因两层：
  1. `train_run.sh` 与 `train_lora.py` 全链路**没有任何互斥**——调度器 40 分钟内两次调用，
     第二次把第一份的 10GB 又叠了一层；
  2. 第三份来自 `launchctl submit -l com.fluxgroup.trainrun` 的**临时提交任务**：
     不落 plist、可被反复重提交，撤了还会再来（同族坑见 topics/gpu-squeeze-ceiling-20261118.md）。
- 正法（两层，都要）：
  1. `train_run.sh` 起手 `mkdir` 原子锁（`.codely-cli/state/TRAIN-RUNLOCK`，内含 pid），
     持有者存活则打印 `SKIP-ALREADY-TRAINING` 并 exit 0；持有者已死则接管（否则一次崩溃永久锁死）；
  2. `train_lora.py` 在 spawn mlx 之前扫 `ps` 判活进程，有则 rc=3——挡的是绕过包装直调的路；
  3. 上游把"跳过"记成 **WAIT 而不是 FAIL**：记 FAIL 会触发重试，越重试越叠。
- 验收方式：伪锁 pid=1 → 必须拒绝；死 pid → 必须接管；直调训练器 → 必须 rc=3。
- 通用判据：**并发不会报错，只会变慢**。凡是"同一份数据/同一块显存"的活，
  必须在唯一汇合点加锁，并给"跳过"与"失败"两种不同返回码。

## 二、段专用适配器：用全量题判会误杀

- 同一件权重两个口径（2026-11-19，同题同闸）：
  - 全量 43 题：候选 26/43、中位 80.5；基座 27/43、中位 88 → 更差；
  - shallow 段内（`train_eval.py --per-segment --segs shallow`）：
    候选 81.0 分 / PASS 100%，基座 48.0 分 / PASS 67% → **+33 分**。
- 结论：段专用件只能用段内指标判；且 8788 一次只挂一个适配器，
  段件全局上线会拖累其它段（全量分就是证据）→ **没有分段路由就不许段件上线**。
- 段级合格线**尚未标定**：只有一组对照（48 vs 81）不足以定阈值，
  至少要再来两个段的对照才能说"多少分算真增益"。不许临场发明阈值。

## 三、回滚假绿三形态（本轮实锚）

1. **回滚目标写死且已消失**：`accept_run.py` 的 FALLBACK 指向
   `RUNS/20261118-113014/best`，该目录已随清理丢失 → REJECT 后 `lora_switch.sh` rc=2，
   被否的候选继续在线，"已回滚"只写在输出里。正法=回滚目标每次现算，算不出来就回 base。
2. **只改指针不写依据**：`lora_switch.sh` 只写 `adapter`，`ACTIVE.json` 里留着上一次
   craft_learner 的 25/43 给新权重背书。正法=依据与指针同批写入，并清掉上一件的 eval/archive。
3. **回滚失败当成功**：切换 rc≠0 时账上仍记 rollback。正法=记 `ROLLBACK-FAILED` 并吼出来。

## 四、环境备忘

- `~/.venv-housing` **没有 mlx_lm**；跑训练/分段评测要用
  `/Users/junsheng.sun/.pyenv/versions/3.13.18/bin/python3`。
- 全量回归 `Tools/fleet/run_all_tests.py` 约 380s，必须用工具自带后台模式跑；
  `nohup &` 会在工具调用收尾时被回收（日志 0 字节、进程消失）。

## 五、证据指针

- 结果文档（已入库）：`cph4/fleet/social/train/RESULT-SHALLOW-20261119.md`
- 运行卡：`cph4/fleet/social/train/RUNS/20261119-181430/RUN.json`（val 2.285@400、2.304@500）
- 归档权重：`~/.fluxgroup/lora-archive/20261119-181430-all` 与 `-ckpt400`
- 提交：`5e2229971`（训练互斥）、`8617cc213`（段件验收与回滚修复）


## 2026-11-19 并发训练只会变慢（L1 迁入原文）
[2026-11-19 19:31:31] 并发训练不会报错、只会变慢（2026-11-19 实锚：三份 ~10GB 训练叠跑，swap 6.3/7.2GB，mlx 零报错）：同一份数据的活必须在唯一汇合点加互斥（`train_run.sh` mkdir 锁 + `train_lora.py` 进程判活 rc=3），且"跳过"要记 WAIT 不记 FAIL——记 FAIL 会触发重试叠加；临时 `launchctl submit` 任务可反复重提交，撤 job 后仍要靠锁兜住。段专用适配器只能用段内指标判（shallow 段内 81/100% vs 基座 48/67%，全量却 26/43<27/43），没有分段路由就不许全局上线；回滚目标必须现算并可回 base，只改指针不写依据、回滚失败记成功都属假绿。全文=`.codely-cli/memory/topics/train-concurrency-segment-acceptance.md`。
