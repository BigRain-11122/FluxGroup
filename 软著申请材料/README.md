# 软著申请材料 · 全集团唯一权威面

> **权威声明（CEO 令 2026-10-08）**：本文件夹=全集团所有项目软著材料的唯一权威位。开发工程名、平台名、代码、文档一律以本位材料名为准；全部项目材料按规范归拢至此。

## 一、权威名称表（现行定名·以各项目位材料为准）

| 工程 | 软件全称 | 软件简称 | 英文名 | 定名备注 |
|---|---|---|---|---|
| G01 吸嘟嘟 | 吸嘟嘟游戏软件 | 吸嘟嘟 | GimmeAll | 未改名（位名=G09_GimmeAll 为 CEO 位标号） |
| G11 | 摸鱼也升职游戏软件 | 摸鱼也升职 | CrazyWorker | **U361 定名 2026-10-08**（原名疯狂打工人/D012候选疯狂打工人有限公司作废） |
| G15 | 萌宠开店啦游戏软件 | 萌宠开店啦 | PetWorkCrew | **U361 定名 2026-10-08**（原名猫狗打工队） |
| G16 | 我有一栋楼游戏软件 | 我有一栋楼 | CrazyEstate | **U361 定名 2026-10-08**（原名疯狂地产） |
| G19 | 我的小花园游戏软件 | 我的小花园 | BloomHaven | **U361 定名 2026-10-08**（原名花栖小筑） |
| FluxVerse 城市线 | 超体宇宙城游戏软件 | 超体宇宙城 | FluxVerse | 城市游戏线 |
| P01 镇魂师 | 存量证书 2024SR0674465（存量款） | — | — | 已登记·著作权人=盛永康 |
| P02 宿命之门 / P06 寻香记 / P08 阴差不良人 | 存量证书（存量款） | — | — | 已登记·无新申请材料 |
| G04 ScrewOut / G05 ReelRiot / G07 MobTide / G08 CrazyCampus / G10 疯狂股市 / G12 LineRescue / G13 我想有个农场 / G14 大不了开饭馆 / G17 UnboxIt / G18 PalacePlunder / G20 今夜有妖 / G23 CardRogue / G26 流放开荒 / G29 MemeCat(候补G30) | 见各自位内申请表草填 | — | — | CCPC 提交格式三件（部分在各自 owner 机仓库位） |

## 二、两种材料格式

1. **CEO 统一格式（本位原始规范·权威）**：每项目位=`{软件名}_V1.0_源程序.txt/.pdf`（60 页 50 行/页）+ `{软件名}_V1.0_软件设计说明书.md/.pdf` + `申请表填写指南.md/.pdf`。生成器=本目录 `generate_copyright.py`（`python generate_copyright.py <key>`·PROJECTS 表驱动·可复跑）。现有位：FluxVerse_FluxVerse、G09_GimmeAll、G11_CrazyWorker、G15_PetWorkCrew、G16_CrazyEstate、G19_BloomHaven。
2. **CCPC 提交格式（各工程仓库工作件归拢）**：每项目位内 `提交材料\` 子目录=源程序前后 30 页 PDF + 操作说明书草版 + 登记申请表草填 + 渲染链脚本。位名带「_CCPC提交格式」后缀者=该款两种格式并存（统一格式位为准名，CCPC 位为提交工作件）。

## 三、位置清单（19 位）

- CEO 统一格式 6 位：`FluxVerse_FluxVerse` `G09_GimmeAll` `G11_CrazyWorker` `G15_PetWorkCrew` `G16_CrazyEstate` `G19_BloomHaven`
- CCPC 归拢 13 位：`P01_镇魂师` `G04_ScrewOut` `G05_ReelRiot` `G07_MobTide` `G08_CrazyCampus` `G09_我想开个医院` `G10_疯狂股市` `G11_摸鱼也升职_CCPC提交格式` `G13_我想有个农场` `G14_大不了开饭馆` `G15_萌宠开店啦_CCPC提交格式` `G16_我有一栋楼_CCPC提交格式` `G19_我的小花园_CCPC提交格式`
- 未开面款（G17/G18/G20/G23/G26 等 S0-S2 早期款）：材料随各自 S2 备料窗由 owner 机生成后归拢至此。

## 四、维护 SOP

1. **名称一致性三处**：备案名=平台名=软著名（提审红线·任何阶段不一致即驳回）。
2. **工程/代码同步**：Unity `ProjectSettings.productName`（平台显示名）=权威简称；游戏内 About/文案引用同步。2026-10-08 已同步四款：摸鱼也升职/萌宠开店啦/我有一栋楼/我的小花园（U361）。
3. **新项目/改名**：改 `generate_copyright.py` PROJECTS（name_cn/name_short/name_en/src_dir）→ 补/改该位 `软件设计说明书.md` + `申请表填写指南.md` → 复跑生成 → 全仓名称同步（台账+登记簿+工程名+文档）。
4. **各 owner 机**：B/C 机款（G09 医院/G10/G13/G14 等）源码在各自机器——由各机窗口跑生成器把 CCPC 三件按本位规范落此（src_dir 指本机工程路径）；本位归拢件为现有存量副本。

> 索引生成：2026-10-08 · U361 软著材料正典化+四款定名同步批（orders O-20261008-1810）
