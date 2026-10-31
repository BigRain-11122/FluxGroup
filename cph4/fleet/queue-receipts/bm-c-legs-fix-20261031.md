# bm-c 机队腿全链修复回执（2026-10-31 14:0x）

CEO 令「拉起机队，符合主控机策略」当窗执行。四条腿全部实测，两处是真 bug。

## 一、认领腿（HQ-ProductionClaim）：**真 bug，已修**

- 症状：任务每 5 分钟起，但 `cph4/fleet/queue-receipts/_lane_task.log` 从不生成，主控看到 bm-c 的 job 永远 `last_result=null`。
- 根因：`Tools/hq-lane-claim.bat` 被生成器拆行——每一行都被写成两行（`cd /d "` 换行再接 `K:\Fluxgroup\FluxGroup`），cmd 第一行就语法失败；且文件是 LF 行尾，隐藏链下解析更不稳。
- 处置：重写为干净批处理 + CRLF，并用单实例锁思维清掉卡死的僵尸实例（旧实例 Running 时任务策略会忽略新点火）。
- 验证：13:57:20 计划任务自己落账 `claim round start → HB → claim → lane_agent → round end rc=0`；`Q-TRIAGE-BIGSTREAMMV` 判 `DONE rc=0 deliverable=True`。

## 二、回执腿（FluxGroup-FleetAgent）：**缺装，已补**

- 症状：`cph4/fleet/cmd/` 里 10 条主控令零 ack，主控无法确认 bm-c 收到任何令。
- 处置：手工补跑一次（2 条 done / 5 条 received），并用 task-register 注册 `FluxGroup-FleetAgent`（every:5m，隐藏链，点火 rc=0）。

## 三、供给面（POOL）：**两处陈旧阻塞，已清**

- `POOL-0024` 挂着 `blocked_by: CEO-PHYSICAL:bm-c-desktop-ram`，但该卡开卡时内存只有 0.6–1.3G，现在实测 9.2–11.8G、ollama 无模型驻留、8188 正常 → 判 done 并清阻塞。
- `POOL-0021`（qwen21 提速批）同样挂着同一阻塞，实际 leg1/leg2 早在 10-20 就跑完（部署 4/4、盲评 Krea2 胜 2.5/3、许可判定在档）→ 判 done + 指向 `POOL-0021-CLOSURE-bm-c-20261030.md`。
- 结果：bm-c 的 open 卡从 2 张（全被假阻塞锁死）变为 0 张，`queue_claim` 从 `POOL-EMPTY + blocked=[...]` 变为空池可补货。

## 四、判读面（line_triage）：**跨机路径假缺口，已修**

- 修成三态（本机 / 重定位到仓根 / OFF-NODE），mv-i2v 由「0 文件」纠正为「1/1 · 111 文件 · 10.9h」。
- 六条线体检已跑：duanju 328.8h、recon 166.8h、car-gaming 108.6h 超阈值；biggame/bigmoney/fluxverse 正常。

## 五、GPU 生产面：已真实开烧

- ComfyUI 8188 在线，`MiniGameComfyKeepAlive` Ready。
- KN21 死镜处理：旧首帧在 768P 两路皆判负（int8=字形噪声、int4=中式纸雕漂移）→ 按「两版同首帧皆负必换首帧」重出三张实景首帧（Krea2，27–67s/张，均 >1.16MB），选用 `frames-retry-c2173/KN21_r2_s770341.png`（真实老楼天台、锈管暖窗水塔、纸机停矮墙，无摆拍感无中式装饰）。
- 正在用该新首帧重烧 768P（后台常驻，`run-bmc-kn21-retry-c2173.json`）。

## 六、仍待主控/CEO 的

- 六条线里的三条超期（duanju/recon/car-gaming）不属于 bm-c 车道，需要主控改派给持有仓库的机器。
- `R-LLM-BMC-PROBE` 在队列里仍记 FAILED，但交付物早已在仓（`queue-receipts/bm-c-local-llm-probe.md`），属旧账。