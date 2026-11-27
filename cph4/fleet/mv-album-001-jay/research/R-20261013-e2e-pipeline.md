# R-20261013-e2e-pipeline — AI MV 端到端生产管线与量产力（MV at scale·生产管线专家席）
> 溯源：BigStream MV 产线调研令 2026-10-13（专辑 10 支 MV·全 90 分·机队 bm-a/bm-b/bm-c 本地优先云端例外）·消费方=mv-album-001-jay 排产与管线改造·判据预注册=①业界完整管线案例 ②66+ 镜素材库命名/版本/索引 ③量产 QC 采样 ④10 支级排产/瓶颈/工时 ⑤失败重试经济学

## 一、核心发现（带 URL）
- 【B·真实案例】Politrukki=已公开发布的 AI MV 全流程开源仓：9 站各成文件夹（01 创意→09 发布），每站 README+核对清单+JSON 配置；24 条 i2v+12 个有序 prompt 文件+shot_list.md+style_guide.md+HTML 进度看板；「管线随作品一起发布，下一支复用同一机器」（github.com/FoxRav/politrukki-ai-music-video-pipeline）
- 【B·制作公司口径】xinemind 2026 实操：3 分钟 MV=30-80 镜·1.5-4s/生成段·每镜 4-8 候选按 brief 打分+失败 re-roll（风格化内容首过失败率典型 30-50%）·逐镜配模（英雄镜/环境镜/表演镜各用其长）·分级工期 4-6 周/$15-35K→8-12 周/$90-250K；「跳过详细分镜=损失 30-50% 时间线」（xinemind.com/blog/ai-music-video-production-pipeline-workflow-costs）
- 【A·命名正典】Blender Studio 官方管线（开源电影实测）：全小写无空格·层级从宽到窄·资产={type}-{name}-{task}（char/set/lib/props×design/modeling/shading/rigging）·镜头={seq 3 位}_{shot 4 位步进 10}-{task}·vNNN 版本号只挂渲出/导出（工作文件靠版本库历史）·变体点记法、720p/lowres 规格做尾缀（studio.blender.org/tools/naming-conventions/introduction；例见 /examples）
- 【A·抽样法理】NIST 手册 6.2：验收抽样=「全检与免检之间的中道」，适用检验破坏性/全检成本高/全检过慢；Dodge 1942 律=「检验数量与强度随被检特征重要性正向、随已证质量水平反向调节」；手册并列 skip-lot（质量已证批次降频抽检）计划族（itl.nist.gov/div898/handbook/pmc/section2/pmc21.htm）
- 【B·一线名家】PJ Ace（Genre.ai·累计 3 亿+播放）：14 小时做 2 支广告·3 人 2 周做 5 分钟样片·25 分钟全 AI 剧集 3 个月；逐镜提示=全参数化结构模板（镜型/画幅/胶片/镜头光圈/角色/姿态/环境前中后景/氛围）（pjace.beehiiv.com；TV Show 15 步 pjace.beehiiv.com/p/make-an-ai-tv-show-in-15-easy-steps）
- 【C·中文实操】guijiagi 七阶段 SOP：风格+种子注册表（StyleConsistencyManager：seed 与参照图登记复用保一致性）·每镜 3-5 候选自动评分→top2 人审（机器筛+人终选两层）·自动 QC 四维（技术/一致性/忠实度/观感）·3 分钟片自估成本 ¥5,300 且大头是 180s×4 候选的生成费（guijiagi.com/posts/ai-video-production-pipeline/）
- 【C·共识清单】awesome-ai-video-production：图先于文=「帧定稿后才花视频额度」（便宜闸门挡昂贵段）·「生成 3-5 变体用数量换质量」·镜头编号约定（Shot 0 封面/1-N 正片/T 片头/E 片尾）·Airtable/飞书多维表做内容排产追踪（github.com/HSG020/awesome-ai-video-production）

## 二、对我们产线的适配建议（环节→业界做法→我们改造点；本表即 P-65 结论应用表，落点=mv-album-001-jay 产线改造）
| 环节 | 业界做法 | 我们改造点 |
|---|---|---|
| 全线结构 | 9 站各成文件夹+README+核对清单+进度看板（Politrukki） | 八站①-⑧已立；把①站 24 项打勾表模式推广为每站出站清单文件；INDEX.md 升级为专辑级进度看板（10 曲×8 站矩阵） |
| 素材命名/版本 | {show}_{seq}_{shot}-{task}-vNNN，镜号步进 10；版本号只挂渲出物（Blender） | 定成法：镜号 4 位步进 10 预留插镜位；KF/视频过闸才挂 vNNN；废片禁版本号、按病灶标签直入 bad 区 |
| 机读索引 | shot_list.md+分镜 JSON（镜号/景别/时长/负面词全结构化）（Politrukki/guijiagi） | SHOTLIST 补一份机读 JSON（镜号/状态/机位/版本/白名单位），烧帧/烧片/装配脚本全按索引驱动，禁手工点名单 |
| 逐镜提示 | 全参数化模板（PJ Ace）/6 模块图像提示（awesome） | prompt 文件化入库（每镜一文件带序号，Politrukki 12 文件式），负面词栈统一维护 |
| 候选策略 | 每镜 3-8 候选自动评分→top2 人审；hero 镜才用满候选额（xinemind/guijiagi） | KF 站已同构；i2v 站按镜型分档：hero 镜云端多候选、常规镜本地 1-2 条，配额（100 任务/日）集中在刀刃镜 |
| QC 采样 | 验收抽样中道+检验强度随已证质量反向调节+skip-lot（NIST） | 逐帧三段闸为 CEO 令不动；第二曲起以病灶率数据申请试点：同族镜抽检+首末帧全检，🟡/✗ 与新镜型恒全检——省下的人眼预算转投成片闸 |
| 排产/并行 | 瓶颈在生成机力+人审：PJ 3 人 2 周 5 分钟片；xinemind 单 MV 4-6 周起 | 内测算：660 镜（10×66）÷ 双机夜窗 64 条 ≈11 夜一过；KF 660 张≈5.5h GPU 非瓶颈→真瓶颈=审帧人力，靠夜窗代理审+晨窗复核消化；10 支按「一过后即装配」流水滚动，勿等全专齐 |
| 重试经济学 | 首过失败 30-50%→按 ~1.5× 烧量排产；失败只回本站（xinemind/我们回炉律同构） | 每镜 re-roll 计数入索引：>3 次即改 prompt/参照而非盲重试；烧量预算按镜型差异化（hero 2×/常规 1.5×） |
| 种子/样本库 | seed+参照图注册表保一致性；过闸即好样本（guijiagi） | anchors/ 补风格 seed 登记位；过闸帧自动入好样本库供后续 MV 风格参照与 QC 正例；废片按病谱标签归档反训 |
| 交付 | 一个母工程多平台导出（16:9 母版裁 9:16，LUFS 分平台）（Politrukki） | build_full_mv.py 一次产出 16:9 母版+竖版切片；-14/-16 LUFS 与分辨率规格入参数表 |

## 三、验证声明
- 实读：本机文件 2 件（MV-PRODUCTION-PIPELINE-v1/R-20261013-ai-video-qc 查重）+网络成源 7 条：A=2（Blender Studio 官方、NIST 官方）、B=2（xinemind 制作公司、PJ Ace 本人 newsletter 一手）、C=3（Politrukki 仓、guijiagi、awesome 清单）；搜索 4 轮+（Bing 浏览器通道），关键主张双源：候选量与失败率三源交叉（xinemind/guijiagi/awesome），命名法 A 级单源+Politrukki 目录实践佐证。
- 失败面：DuckDuckGo（search 工具与 html 版）、Mojeek、Brave 均反爬拦截→改用 Playwright 浏览器走 Bing 绕行；runway.com/stories 404；CSDN 的 PJ Ace 拆解文半付费墙（只读到策略部分）；PJ 15 步细节在 X 视频线程未展开；NIST skip-lot 详情页未直读（仅章节 TOC 确认其存在）。
- 待证：PJ「3 人 2 周 5 分钟样片」出自其 YouTube 频道简介（一手源但未看视频核实）；guijiagi ¥5,300 为作者自估（M 级）；xinemind 工期/报价为公司口径（B 级，非第三方审计）。
- 内源对照：66 镜/支、64 条/夜窗、30s/张 KF、100 任务/日配额均引自本仓 MV-PRODUCTION-PIPELINE-v1.md，非网络源。

- 更新记录：T0 骨架落盘（早落盘律）→ T1 搜索轮 1+Politrukki/xinemind/Blender/NIST 成源 → T2 guijiagi/PJ Ace/awesome + 终稿 35 行。
