# mem-20261018-softc-maintain — 软著材料维护工艺链（全量刷新 SOP·bm-a 10-17 夜批实录）

> 溯源：CEO 令 2026-10-17 23:xx「按最新的进度更新一遍所有项目的游戏软著材料，要精读和审查到位」（二批·承 10-13 一批）。commit 99c7919。

## 1. 软著材料面结构速览

- 权威位=`软著申请材料/`（全集团唯一权威面·CEO 令 2026-10-08）·37 位 32 款（A 机 14+B 机 10+C 机 8+封存）。
- 生成器=`generate_copyright.py`：PROJECTS 表 32 款注册（name_cn/name_short/name_en/src_rel/out_dir/owner）·一键复跑幂等；**src_rel 九根跨机解析**（gaming\MiniGame/gaming/projects/../projects/REPO/K:\\C:\\ 等）——本机有源码=源程序全量产出（txt 60 页 50 行+pdf·不足 60 页诚实标注）·无码=跳源程序仍渲说明书/指南 pdf。
- 三件套=`{英文名}_V1.0_源程序.txt/.pdf`+`{英文名}_V1.0_软件设计说明书.md/.pdf`+`申请表填写指南.md/.pdf`；报审提交区=`_报审提交区/班1-5/{款名}/01_源程序.pdf+02_说明书.pdf+03_指南.pdf`（部分款带签名页/委托附件）。

## 2. 关键坑：说明书手写行数漂移（本次 4 处实证）

- 生成器只自动回写**指南 md** 的「| 源程序量 | N行（M个.cs文件） |」行——**说明书 md §1/§2 的行数是手写的**，代码推进后必漂移。本批实证：P08 7558→7961（+403·双处）、FluxVerse 8300→8377、P01 9500→9570。
- 正法=审计器对账：`audit_copyright_r1017.py`（软著申请材料/根）——32 款四查：三件套齐全性/说明书行数 vs 指南回写值（±0.5% 容差）/名称一致性（说明书首行含软著全称）/pdf 落后 md 检。复跑 ISSUES=0 为收口判据。
- 附带发现：B/C 机 18 款源程序 10-15 bm-c 批已产（B 机 10 款=10-15 16:44·C 机 8 款=10-15 01:06）——README 台账「待 owner 机复跑」过时已修正；owner 机复跑令走 orders 派单行（机队生成律：各机窗口跑一遍生成器·材料随 git 归拢）。

## 3. P 系双位坑（工程位 vs 归拢位）

- `gaming\MiniGame\01_提灯斩鬼~08_奈何桥`（中文数字目录）=**提交材料归拢位**（设计 md+截图+素材·无 Unity 工程）——不要当工程位找。
- P 系/G 系 A 机款工程位=`gaming\MiniGame\projects\P01_LanternReaper…P08_GhostMarshal/G11/G15/G16/G19`（生成器 src_rel「projects/xxx/Assets/_Game」由 gaming\MiniGame 根命中）。G09 吸嘟嘟=`gaming\MiniGame\09_吸嘟嘟GimmeAll/GimmeAll/Assets`。列目录超 30 项会被截断——projects 目录易被误判 MISSING。

## 4. 进度联动判例（哪些款说明书要改）

- 10-13 批后逐款核 git log：**只有真实功能推进才改说明书内容**——P08 新增 ExploreView/SceneConfig/PuppetMicroMotion（Runtime 新模块→说明书补描述+微动升格）；X2566/X2569 类构建/包体/版本阶梯提交（P06/P01/P02）=无功能面变化→说明书不动。
- 说明书只补玩家可见功能；Editor 工具（P08VideoRig/CheckBundle）不入说明书功能面。

## 5. 维护 SOP 五步（下次「按最新进度更新」直接复跑）

1. `python 软著申请材料/generate_copyright.py`（无参数=32 款全量·A 机面）；
2. `python audit_copyright_r1017.py` 拿漂移清单；
3. 修说明书 md 行数/新模块描述→`python generate_copyright.py <key>` 重渲该款 pdf；
4. 内容变化款跑 `sync_submit_area_r1017.py`（按款名关键字 walk 提交区）换新三件套；
5. README 台账行更新（脚本 patch_readme_r1017.py 模式：批记录段+行数表+状态行）+orders 补行+git pathspec 提交（commit 前非过滤视图核 staged——多窗污染判例执法）。
