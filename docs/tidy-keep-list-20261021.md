# TIDY-KEEP-LIST 2026-10-21 — 历史文件腾挪保留清单（实测版·只方案不执行）

> 令源：CEO 2026-10-21「我准备腾挪历史文件了，你看哪些需要保留」。
> 性质=腾挪**建议清单**。本席未移动/未删除任何文件。所有"可再生"判定带证据；动手前必过 §五 三道保险。
> 现状：C: 剩 837G／D: 剩 3511G（腾挪目的地首选 D 盘——今天 11:27 的 `_offload→D:\FluxGroup-Offload` junction 做法正确，沿用同法）。

## 一、体量实测（腾挪目标=这三座山）

| 目录 | 实测 | 构成 |
|---|---|---|
| gaming\MiniGame | **90.4G** | projects 47.6G（其中 **Library 缓存 40.4G**）＋ Art Assets 27.3G ＋ 吸嘟嘟 5.2G ＋ .codely-cli 3.2G |
| _offload | 54.8G | 已是 junction→D 盘（实际不在 C 占用内，gitignore+MANIFEST 齐，**勿再动**） |
| media\BigStream | 13.7G | 大头=data\assets 9.8G 模型运行时 |

## 二、必须保留（S0·一个字节不碰）

1. `media\MUSIC\`（3.2G）=41 曲无损音源——唯一源，不可再生。
2. `media\BigStream\data\assets\`（9.8G）=ComfyUI 模型运行时——重下要一天，正典 S0 禁删。
3. `gaming\MiniGame\Art Assets\`（27.3G）=美术源资产——git 仅 88 文件在册，其余是 gitignore 大源件，**删=不可恢复**（除非先验备份逐字节，见 §五）。
4. `life\BigLife\census\`（3.8G 内）=10109 居民户籍源+behavior 轨迹——城的命根子。
5. `软著申请材料\`（37 项目）——CCPC 申报口径权威面。
6. `docs\` 全部台账+正典、`cph4\` fleet 正典与 MV 审读链——集团记忆，记录删=伪造（正典律）。
7. `gaming\FluxVerse\City3D\Assets\`（城源+Synty 包）+ `City\`（2.1G 旧 2D 存史）——正典封存位。
8. `_offload\MANIFEST.md`+`ROLLBACK.ps1`+`00-config-backup`——今天的回滚链。

## 三、可直接清理（可再生·腾挪零风险）

| 项 | 体量 | 再生方式 | 代价 |
|---|---|---|---|
| `MiniGame\projects\*\Library\` | **≈40.4G** | 团结引擎重开工程自动重建（有判例：暖库 60-90s/轮 起步，整工程首开 10-30min） | 重建耗时，款多则分批；**门禁/出包前先别清当轮要用的款** |
| 各仓 `Logs\`、`tmp\`、`qa\` 截图帧散件 | 数 G | 日志滚动件；帧图可由 RT 产线重拍 | 低 |
| `MiniGame\projects\*\Build\`/出包中间件 | ~1G | BuildPackage.ps1 重产（版本权威在 build_versions.json，不在包件） | 低 |
| `media\logs\`、`cloud-off-suppressed.log` 类 | 0.1G | 滚动日志 | 无 |
| `.codely-cli\tmp\`、`retention\` 快照旧代 | ~1G | 运行时缓存 | 无 |

## 四、可迁 D 盘（保留但离开 C·junction 同法）

1. `Art Assets\` 27.3G（若 §五 备份校验过）→ D:\FluxGroup-Offload\40-art-assets
2. `吸嘟嘟 5.2G` 内 sweep/tour_evidence 证据件（非工程本体留 C，证据迁 D）
3. `FluxVerse\design\` 历史探索 png（正典注记"不必翻"件）
4. `quant\bigmoney\` 内 legacy/Money02-Money0923 旧实验仓面（先查 git 在册再迁）
5. MV **非 v511 家族**段件：CANON-INDEX 判例="v511 家族唯一保留"，v56_v511_final 以外的装配段=过程件候选（迁 D 不删）
6. 旧 2D `City\` 2.1G：存史封存不再新产→可迁 D 留 junction

**不建议动**：`Software\`（1.4G 便携工具）、`.codely-cli` 活运行时、projects 各款的 `Assets\+_Game` 源码面（在 git，但工程打开态别挪走底层文件=团结会重导入抖动）。

## 五、动手前三道保险（顺序不可乱）

1. **备份覆盖先验**：昨日 `D:\FleetBackup-20261020`（91.15G/871,221 文件·repos 镜像 62.69G 排除 Library/Temp）已覆盖 8 仓工作树——**对 §二 3/4 项和 §四 1 项抽 md5 逐字节校验**（沿用 10-20 校验判例：路径映射剥分类前缀防假警报）。校验过才允许动原件。
2. **bm-c 的 K 盘镜像**：C 机八仓项目在 `K:\Fluxgroup\`（不在本机）——本次只理 bm-a 面，别把"我这边没了"当"没了"。
3. **移动用 junction+留 ROLLBACK**（今天 _offload 的既有做法），全程禁永久删除；清理 Library 走"逐款关编辑器再删"（活锁判例）。

## 六、净效果预估

三座山 158G → 清缓存 43G（立即可得）+ 迁 D 约 35G → **C 盘回收约 75-78G**，剩余 gaming 面压回 ~12G 活跃工程。若只要 C 盘空间：**光删 Library 就回 40G，风险最低，第一批就做这个**。

---
*千问席 · 2026-10-21 · 实测=Get-ChildItem 全递归统计（本件含时间戳读数）；执行候令，腾挪动作逐批呈报*
