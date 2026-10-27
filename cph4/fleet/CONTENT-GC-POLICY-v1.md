# CONTENT-GC-POLICY v1 — 自媒体线废资源清理机制（BigStream 四线+MV 通用）

> CEO 令 2026-10-16 21:3x：「自媒体还要做清理机制，一遍遍迭代，打造了很多废资源产生，要及时地去做清理。」
> 科学翻译：内容产线=迭代密集型——每次迭代产生中间产物（会话快照/旧版成片/QC 拼板/帧抽取/试烧废片/干跑日志/日志），无 GC 则磁盘耗尽+检索污染+版本混淆。机制四件=**判据→分级→周期→安全闸**。
> 执行器=`Tools/content-gc.ps1`（默认 WhatIf 报表·`-Apply` 才动刀）。报表落 `cph4/fleet/gc-reports/`。

## 一、废料判据（四类）

| 类 | 内容 | 处置 |
|---|---|---|
| W1 会话噪声 | `.codely-cli/auto-saves/`、`tmp/`、`t22-*`、`_trash*`、`.c3-tmp`、`.aihot-tmp` | **保留 3 天**·超期删 |
| W2 迭代废件 | 被新版本替代的旧成片/代理剪；已消费的帧抽取目录/QC 拼板（上链或复核毕）；干跑日志（正典吸收毕）；`_superseded/`；试烧败选片（审定选完成即废） | S2 保留 N-1（见下） |
| W3 日志 | `media/BigStream/logs/`、`media/logs/` | **保留 7 天**·超期删 |
| W4 空壳重复 | 空目录、同内容重复大件 | 报表列示→删 |

## 二、分级与安全白名单

- **S0 禁删白名单（硬规则·脚本内置）**：
  - `media/MUSIC/`（无损音源库·CEO 2026-10-10 亲指正典位·ape→320k 生产正法源）
  - `media/BigStream/data/assets/`（cosyvoice/piper/models 运行时——**基础设施非废料**）
  - 在飞/未交付资产（delivery-watch 在监件、v5redo 收片、装配源件库如 frames_full）
  - 判例/签章证据（签章档与 DIRECTOR-REVIEW 引用的 PNG/board——删本地前必须已上链）
  - 成片正身（已发布/待发布 final）+ CEO 裁决本地媒体区（`media/drama-pilot-out/`、`media/mv-album-001-jay/`——处置须单独呈报）
  - CEO 物理件（软著材料等·非本线亦不碰）
- **S1 立即删**：W1/W3 超期件、tmp 类——脚本 `-Apply` 自动执行
- **S2 保留 N-1**：旧版本成片/代理剪——只保留最新上一版（回看对照）·更旧删
- **S3 候选待裁**：拿不准件（未上链旧 QC 板/老素材）——脚本列清单·治理窗或 CEO 裁

## 三、执行节奏

1. **片级 GC**：每片 DIRECTOR-GATE 终审签章收口时，该片的废试烧/废帧/旧代理剪**当场清**（产线自清·勿堆积到轮级）
2. **轮级 GC**：治理窗/夜班跑 `Tools/content-gc.ps1`——先 WhatIf 报表，S1 确认后 `-Apply`
3. **报表律**：每次 GC 落 `gc-reports/GC-<日期>.md`（类别/件数/释放量/S3 清单）·轻量上链

## 四、安全闸（五条·违者=P0）

1. **删前引用检查**：候选件名先 rg 正典区——被签章档/判例引用的先上链再删
2. **禁手工递归删除**：一切批量删除走 content-gc.ps1（bm-b r834 整树删除 P0 事故判例）——脚本内路径白名单写死
3. **先 WhatIf 后 Apply**：报表先落盘核过再动刀
4. **gitignored 区删除不碰 git；tracked 证据先 commit 再删本地**
5. **单批 >500MB 删除当窗呈报 CEO**（透明律）

## 五、首扫实锚（2026-10-16 21:3x·bm-a）

- 自媒体面总量≈21GB：BigStream 工作区 14.5GB（其中 data/assets 模型运行时 9.8GB=S0 禁碰）+MUSIC 3.3GB（S0）+MV/mv0001 687MB+mv0001-handover 1GB
- **废山首案=BigStream `.codely-cli/auto-saves` 2.2GB/1,285 件**（10-08 起日增 150-240 件·.gitignore 早已定义噪声但盘上零清）——首清对象
- logs 7,418 件（09-23 起）·BigStream storylines 478MB/2,651 件（S3 候选）·output 1.75GB（S3 候选）

—— bm-a · 2026-10-16 立法·随行修订升 v2
