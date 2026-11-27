type=judgment
audience=all
urgency=P1

# 策略转向后旧申报卡继续被车道执行——撤卡三件套判例

## 现象
CEO 2026-11-09 定谳「停 16 声线学术训练」之后，转向前(11-09 23:0x)挂的 15 张
Q-VCORP-TRAIN-*-R7 申报卡仍在队列；bm-b 车道 11-10 00:11 自动领卡开训 aishell3-z04
（vb_train_card+vb_build+4 worker，GPU lease 12GB），00:23 二次领同卡撞单飞锁。
训练产物已被 CEO 判负=纯空烧（z04 训了 14 分钟被杀）。

## 根因
策略转向只落了会话记忆与定谳，没有撤卡动作：申报行(PRODUCTION-BACKLOG)、
队列卡(PRODUCTION-QUEUE)、在跑进程三层都没动。车道按队列法定执行，对策略变化无感。

## 修法
①杀在训进程树+释放 GPU lease（keepwarm 双任务恢复）；
②CAS 撤 R7 队列卡+backlog 同名申报行（state=CANCELLED + cancel_reason 引 CEO 令）；
③判例入册：**策略转向必须带撤卡三件套=撤申报行+撤队列卡+杀在跑进程**，
否则旧策略卡会自己复活吃 GPU。

## 证据
进程表：vb_train_card(31428/33292)→vb_build(4556/30052)→4×spawn worker，00:11:49-00:13:56 起；
gpu_lease --job Q-VCORP-TRAIN-z04-R7-20261109（12GB，已 release）；
queue-receipts/Q-VCORP-TRAIN-z04-R7-20261109-bm-b.json（E-ARTIFACT FAIL，单飞锁）；
撤卡 commit=见本推送 HEAD。
