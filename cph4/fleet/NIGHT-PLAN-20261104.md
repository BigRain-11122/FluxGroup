# 今夜机队排班（2026-11-04 19:20 · 主控自动排，无人值守）

> CEO 下班，本班不等人。此文件是明早核对用的唯一一屏：谁跑什么、跑多少、卡在哪。
> 判据全部是"盘上产物"，不看心跳、不看自述。

## 一、本机（bm-m·MacBook·32G 统一内存）

| 任务 | 量 | 预期产出 | 轮次 |
|---|---|---|---|
| 资产打标（caption） | 待打 **~450 张** | 每图同名 `.txt` + `cph4/fleet/asset-lib-v1/CAPTIONS.jsonl` | 脉冲每 5 分钟一轮，约 6 分钟 8–12 张，整夜可跑完 |
| 审片代理（720p） | 待转 **~118 条**（备份盘镜头） | `media/review-720p/*-720p.mp4` | 与打标并行，CPU 槽 2 路 |
| 字幕 ASR | `media/drama-out` 6 条 | `cph4/fleet/drama-dept-v1/subs/*.srt` | 今日日期闸已放开，夜间一次 |
| 轻活（分类/摘要） | 当日告警与缺料 | `cph4/fleet/state/local-tasks.jsonl` | 每轮最多 3–12 件，串行 |

关键修正（今晚已生效）：打标提示词原来只问「头发/外套/表情」，而资产库里是**道具物件**，所以抽 20 张全部被判"空话"；改成物件词表后 **4/5 通过、6 秒/张**。

## 二、执行机（各自领卡，主控只派不代做）

| 机 | 在办/待办 | 内容 | 卡点 |
|---|---|---|---|
| bm-a | 10 张 | mv 稳定性/转场、biggame 可玩包、模型雷达 | `MiniGame` 目录缺失 → biggame-playable 反复 E-ARTIFACT；`full_mv_v721.mp4` 盘上没有 |
| bm-b | 6 张 | 量化信号 CSV、模型雷达、日计划 | 量化仓在本机不可见（独立仓），需 bm-b 本地出件 |
| bm-c | 6 张 | 漫剧 TTS 质检、BigLife 计划、模型雷达 | 音色语料 inbox 为空 → 已加投料闸，不再出空卡 |
| bm-d | 1 张（离线） | bigmoney-backtest | 自 10-29 离线，禁派（已按铁律拦） |

## 三、今夜不做的（避免造假活）

1. 不为"满负荷"灌体检卡——CEO 2026-11-02 决定。
2. 不替内容线出片/渲染/回测（主控边界）。
3. 不加并发第二模型、不碰 swap（内存余量留 6G 给办公）。

## 四、明早核对清单（3 分钟）

1. `bash Tools/fleet/disk_release.sh status` → 盘挂载、0 句柄占用。
2. `python3 Tools/fleet/mac_farm.py --dry` → 应看到 caption 待打数大幅下降。
3. `find "/Volumes/移动硬盘/FluxAssets/store" -name "*.txt" | wc -l` → 昨晚基数 78，目标 ≥400。
4. `ls media/review-720p | wc -l` → 昨晚基数 20，目标 ~138。
5. `cat cph4/fleet/SYNC-BOARD.md` → 各机是否上报、谁产了什么。
6. `cat cph4/fleet/WAIT-MAP.md` → 是否还有"无人生产"的产物。
7. `cat cph4/fleet/CEO-QUEUE.md` → 有没有到期待你裁决的件（对外/花钱/不可逆才拦你）。

## 五、今夜已知风险

1. 打标首次跑完全新一代仍需抽检 5 张（明早我出一份抽检表，不给"全绿"结论）。
2. bm-a 单车道一次一件，内容卡会挤掉回传；回传已改为节点日常站，不再排队等车道。
3. 若 macOS 提示盘问题，用户侧跑 `disk_release.sh release` 后拔线即可；机队已认旗标让路。