# 通告 OB-20261104-1435-GIMMEALL-NAMING（吸嘟嘟工程重整）

- 时间：2026-11-04 14:35
- 车道：bm-a / bm-b / bm-c / bm-m
- 来源：CEO 令「把车机版本的工程名字和小游戏版本的区别开，其他项目也是」+「git同步一轮所有的改动 并发布给机队 让他们都知道」
- 台账：`docs/orders.md` 同日行（durable）；`cph4/fleet/acks/OB-20261104-1435-GIMMEALL-NAMING.bm-a.ack.json` 为 bm-a 回执
- 说明：本件原投 `cph4/fleet/cmd/`，被 job 快照提交删除后改落此处（cmd/ 是瞬时通道，job 提交会扫走）

## 必须知道的三条

1. **正本路径变了**：`D:\FluxGroup\gaming\MiniGame\09_吸嘟嘟_GimmeAll_CAR\GimmeAll`。
   旧路径 `09_吸嘟嘟GimmeAll` 留 junction 兼容历史引用，但**新活一律写新路径**。
2. **`09_吸嘟嘟_GimmeAll_WX` 是只读镜像**（小游戏版出包用，robocopy 镜像），**禁止在里面改代码**。
3. **碰这个工程先 `git pull`**；吸嘟嘟仓 main=`2dc9aff`，工作区干净。

## 六条工程规则（都已有闸或脚本落地）

| # | 规则 | 落点 |
|---|---|---|
| 1 | 构建前强制镜像正本，缺任一 .cs 拒绝出包 | `Tools/family_line.py`（`sync_build_tree` / `--sync-only`） |
| 2 | 产品名/包名只许单点写 | `Tools/variant_identity.py`：CAR=吸嘟嘟（车机版）/`com.fluxgroup.gimmeall.car`；WX=吸嘟嘟（小游戏版）/`com.fluxgroup.gimmeall.wx` |
| 3 | 构建树是投影，不许手改 | `D:\FluxGroup\FamilyBuild_CAR`（`.variant=CAR`） |
| 4 | 提交前跑工程规范闸 | `Tools/unity_conventions_check.py`（9 断言；负控 10/10；覆盖率地板 45→46） |
| 5 | BGM 源已换 OGG（Assets 151.9→113.7MB，包体不变 150.1MB） | `Assets/_Project/Audio/Resources/bgm_*.ogg` + `AudioPackageMatrix` 档位不变 |
| 6 | 全库命名登记 | `MiniGame/_共享与总控/PROJECT-NAMING-v1.{md,json}`（19 工程，17 个撞车包名已改 `com.fluxgroup.<slug>`） |

## 未完成（不许当已完成）

- 车机包 V0.10.20 已出（150.1MB/172 文件，`WINBUILD|Succeeded|errors=0`），但**OGG 循环接缝未做人耳/真机听感复核**。
- 站 A/B 美术批、Android 4K 构建、60fps 实测、119 条用例全量跑：仍卡在无真机/未放行。