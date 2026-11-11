# 工作流改造总计划（2026-11-11 起）

> 令源：CEO 2026-11-11「先修机制和规则」「git 同步的机制也要改了」「你自己列好计划 自动推进」。
> 原则：先规则、再结构、后机器；每批都可逆；不新增机制文件（只合并与收口）。

## 批次与状态

| 批 | 内容 | 状态 | 证据 |
|---|---|---|---|
| B1 | 同步机制 v2 定稿；取消全量 union；完整性检查修正 | ✅ 完成 | `SYNC-DESIGN-v2.md`、`.gitattributes`、`queue_integrity.py`、commit `21e280f55c` |
| B2 | 工位分片读写模块；同步面 `--station`；线注册表与自治配置补工位口径 | ✅ 完成 | `Tools/fleet/station_shards.py`（自检 7/7）、`state_sync.py --station`、`PRODUCTS.json`/`STATIONS.json`、commit `5f9f76aa96` |
| B3 | 存量 41 张卡归位；旧队列黑洞清零；只读汇总视图 | ✅ 完成 | `rt/*/queue.jsonl`、`rt/MIGRATION-20261111.md`、`station_status.py`、commit `72c12fb186` |
| B4 | 派单器读分片；旧队列冻结；首批真卡（带验收判据） | ⏳ 待做 | — |
| B5 | 机器修复与上岗验收（小钢炮上线、传家宝 ComfyUI、公司生产力机接回） | ⏳ 待做 | — |
| B6 | 一周度量：元工作占比、STALLED 段、可发布物 | ⏳ 待做 | — |

## B4 的具体内容（下一步）

1. `master_agent` 增 `load_queue()`：若 `AUTONOMY.sync.mode == station_shards` 且分片非空，
   则读五份分片；否则回落旧队列（只读兜底）。写回按卡所属工位分片。
2. 旧 `PRODUCTION-QUEUE.jsonl` 标记 `frozen_at=2026-11-11`，写手（master_agent/supply 系列）
   全部改指向分片；旧文件保留读取兼容。
3. 按产品工序生成第一批真卡（每张带可执行验收判据）：
   - delivery：39 款提审材料（先 3 款）→ 判据=四件套齐全 + 图标尺寸 + 包可启动。
   - visual：MV 单曲关键帧（先 1 支）→ 判据=张数 + 分辨率 + 人脸一致性抽检。
   - audio：配音母版（先 1 段）→ 判据=时长 + 采样率 + 无爆音。
   - brain：回测报告 → 判据=同命令可复现 + 三项指标齐。

## B5 的前置（机器侧）

1. 小钢炮：先恢复在线，再补 TTS venv，跑一段 30 秒配音验收。
2. 传家宝：起 ComfyUI(8188)，系统内存腾到 ≥10G，跑 3 张 1024 关键帧验收。
3. 公司生产力机：起 FleetLink/认领口，跑一个安装包验收。
4. 算力大脑：装机 + 加盘 + 入网，之后才进排产。

## 风险与边界

1. 三台 Windows 仍按旧逻辑写 `PRODUCTION-QUEUE.jsonl`；B4 完成前不要并行改旧队列，避免分叉。
2. 本轮所有改动可逆：`.gitattributes`、配置、分片数据全部在 git 内，一行退回。
3. 不引入外部调度系统；不新增第三、第四件注册表。
