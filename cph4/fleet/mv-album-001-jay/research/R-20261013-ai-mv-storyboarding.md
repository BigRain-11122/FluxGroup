# R-20261013-ai-mv-storyboarding — AI 音乐视频剧本叙事与分镜最佳实践（BigStream MV 产线调研）
> 溯源：mv-album-001-jay 任务单（AI 关键帧→图生视频→ffmpeg 装配·90 分对标专业 MV）·消费方=BigStream MV 产线
> 验证声明：中英搜索 10 轮·直读尝试 8 页（成功 7·403 一）·成源 13 条（B=4/C=9·A 级直读 0）·失败面见 §三

## 一、核心发现
### 1. 叙事结构：歌曲段落=叙事骨架（确认·多源交叉）
- 段落→视觉任务映射：Intro 立世界（1 宽镜慢推 8-12s 不切）→主歌一引角色（2-3 中景）→副歌=「家」意象（3-4 镜踩拍切，建一次每次复用）→主歌二发展不复读（同 canon 新角度）→Bridge 打破模式（1 反差长镜 10-15s：慢动作/反转/新光）→尾副歌升级复用→Outro 呼应开场首尾相扣（C：https://purposewithpresence.com/blog/how-to-storyboard-ai-music-video.html）
- 切镜按音乐结构不按句子平切：主歌叙事/副歌爆发/bridge 转折，每镜=一段歌词+一个情绪点；画面跟音乐走而非音乐配画面（C：https://suno.bi/zh-tw/blog/suno-storyboard-to-screen-workflow-2026）
- 副歌复用=最大预算杠杆：3 段副歌只建 3-4 镜可省 1/3 独立镜头；3:30 歌≈15-20 独立镜头+复用；预留 20-30% 二次生成余量（C：purposewithpresence 同上）
- 表演/氛围比例：艺人型 40-60% 表演集中在副歌，叙事型可趋零表演；唇同步=最难镜头+一致性双倍负担；宽/中景身份稳定性远好于特写（C：purposewithpresence + https://aistudio.com.sg/blog/ai-storyboarding-guide-2026.html 双源）
- 双线叙事实操：叙事线+表演线交替即「双线」；「同一个世界感」来自场景库（3-5 个：地点+时段+布景+光，每镜单选）——锁景是多数工作流漏掉的一环（C：suno.bi 同上）

### 2. 分镜表设计：关键帧=拍摄本体（确认·AI 与实拍分镜的核心差异）
- AI 分镜≠草稿而是拍摄指令：批准的关键帧=图生视频的构图参考，批准标准须高于铅笔稿；分镜阶段迭代最廉、下游最贵（C：aistudio 同上）
- 五步闸门工作流：剧本→shot list（先于任何出图）→参考集（每角色 2-3 张锁定图+每场景 1 张）→每镜 1 张关键帧→整板连读当电影审（跳过=最大浪费）→批准后逐镜生视频（C：同上）
- shot list 八字段：镜号(V1-a/CH-1/BR-1)·段落+时间戳·时长（取自生成器菜单）·景别+单一运镜·P/A（表演/氛围）·画内 canon 元素·动作注记·复用于（C：purposewithpresence 同上）；中文五行版：镜号·景别·运镜·画面内容·时长+对应歌词（C：https://aisongcover.app/zh/blog/zenme-yong-ai-zhizuo-mv-fenjing-jiaoben）
- 每镜最多一个运镜（叠加=废片主因）；图生视频提示词只写运动不重述场景（重述=重释已批准构图）（C：aistudio 同上）
- 关键帧提示词七要素序：景别→主体→动作→场景→灯光→镜头感→情绪；同场景灯光/镜头/色彩子句逐字固定，只变景别/主体/动作（风格漂移多因每次重写风格子句）（C：aistudio 同上）
- canon 三件套（角色表+场景+灯光规则）写成一段文本逐字贴进每条提示词；先出定妆照→批准→作参考图贯穿所有生成（C：purposewithpresence 同上）；中文圈同构做法=「风格圣经」统一场景/服装/色彩/光线+逐镜查人物场景运动跑偏（C：https://www.bilibili.com/video/BV1aJuJ6eEC5/）
- 计划先行 vs 即兴实测：完播率 64% vs 38%、主角一致性 ~85% vs 30%、20 分钟规划省 2-3 小时重生成（单团队数据·方向确认·数值待证）（C：purposewithpresence 同上）

### 3. 案例分析（确认）
- 首支 Sora 官方 MV《The Hardest Part》（Washed Out×Paul Trillo，2024）：连续变焦穿越一对情侣一生=4 分钟全片叙事脊柱；单条提示词 ≥1000 词；全片生成约 700 条素材（专业级抽卡率）；遭遇受众反弹，艺人以「新工具探索」框架应对（自比 Dire Straits《Money for Nothing》早期 CG）（B：https://www.rollingstone.com/music/music-features/washed-out-a-i-video-backlash-hardest-part-interview-1235017826/）
- 周杰伦抖音首条 AI 视频（1400 万赞，2025）：生活照+MV 抽帧用「首尾帧」技术串联成长线；首尾帧已成可灵/海螺/即梦标配；提示词本质=逻辑清晰的文科书写而非死模板；「穿越机视角」词模拟运镜；抽卡迭代取最佳（B：https://www.digitaling.com/articles/1381386.html）
- 全 AI 制作《The Dust》：两阶段法（先批量静态帧定构图氛围→图生视频→剪辑调色）与我们产线同构；2 天成片；先定类型（country）限定范围再测 AI 遵守力；「AI=放大器，艺术方向留人手」（C：https://washiviana.com/en/project/ai-music-video-the-dust）
- 学界 AutoMV（伦敦玛丽女王大学等四国）：首个开源多智能体「歌→完整 MV」系统（B：https://scienceblog.com/ai-film-crew-turns-songs-into-complete-music-videos/·仅摘要级·待证）

### 4. 专业 MV 导演方法→AI 产线适配（确认）
- treatment 正典：MV 业「treatment 之于 MV=剧本之于电影」，地基/路线图/排错三合一，先在案上磨掉创意漏洞再开机；AI 对应=先 shot list 后出图（C：https://robinpiree.com/blog/how-to-write-music-video-treatment·职业 MV 导演一手经验）
- AI MV 四大廉价感=流程病非提示词病：音画不同步·镜头语言扁平·角色场景乱飘·无叙事弧——没有一个能靠「写更好的提示词」解决（C：suno.bi 同上）
- 景别三分工+转场卡拍：远景交代环境·近景给情绪·特写给细节；机位=态度；转场放鼓点/强拍=音画同步关键一招（C：suno.bi 同上）
- 邝盛基线（本专辑对标导演）：台湾 MV 第一高手，周杰伦《以父之名》《三年二班》《最后的战役》《开不了口》等代表作，多次金曲奖最佳 MV 导演奖（2004《三年二班》）；其作品=mv-album-001-jay 的参照系本体（B：https://baike.baidu.com/item/%E9%82%9D%E7%9B%9B/2983237 + https://taiwancinema.bamid.gov.tw/Staff/StaffContent/?ContentUrl=61548）

## 二、对我们产线的适配建议（落点=mv-album-001-jay 任务单接线）
| 发现 | 怎么用 |
|---|---|
| 段落→视觉任务映射+副歌复用 | 每首歌先做「段落拆解表」：各段落配视觉任务+镜头预算（3:30≈15-20 独立镜）；副歌只建 3-4 镜升级复用，直接省 1/3 生成量 |
| 关键帧=拍摄本体·五步闸门 | 产线改闸门制：shot list→参考集→关键帧→整板连读审→逐镜图生视频；整板不过审禁进下一环（分镜阶段迭代最便宜） |
| canon 三件套/风格圣经 | 每首歌建 canon 文本（角色表+场景+灯光规则）逐字贴全提示词；定妆照先出先批作参考图贯穿；同场景灯光/镜头/色彩子句逐字固定 |
| 景别运镜纪律 | 每镜单运镜；景别三分工（远=环境/近=情绪/特=细节）；图生视频提示词只写运动；宽中景优先护一致性，特写控量 |
| 首尾帧技术（周杰伦案例） | MV 抽帧/老照片做首尾帧串联叙事，prompt 写两帧间动作+运镜，加「穿越机视角」词——周同学账号已验证此路线的受众接受度 |
| 转场卡拍+首尾呼应 | ffmpeg 装配时转场对齐鼓点/强拍；副歌情绪高点配全片最强镜头；Outro 首帧呼应 Intro 尾帧做 bookend |
| 抽卡预算现实 | 常态预留 20-30% 二次生成；对齐 90 分目标的关键镜允许高抽卡（Trillo 700:1 先例）；设每镜抽卡上限防预算失控 |
| AI 反弹风险管理 | 发布文案用「新技术探索/致敬经典」框架（Washed Out 教训+Money for Nothing 先例），回避「AI 取代导演」叙事 |

## 三、验证声明
- 查了什么：10 轮中英搜索（叙事结构/AI 分镜工作流/获奖与爆款案例/导演方法论四域）+ 直读成功 7 页（purposewithpresence·aistudio.com.sg·washiviana·robinpiree·suno.bi·digitaling·rollingstone）
- 源等级：B=4（Rolling Stone 专业媒体访谈·数英创意行业媒体·scienceblog 学术新闻·百度百科/台湾电影网人物条目）；C=9（purposewithpresence·aistudio·suno.bi·aisongcover·bilibili·ars.electronica 摘要级等创作者/工具方经验）；A 级直读=0——行业尚无官方一手分镜规范文档，此本身即发现
- 关键结论分级：分镜工作流/段落映射/一致性方法=确认（≥3 源交叉）；64% 完播率与 85% 一致性数值=待证（单团队自测）；AutoMV 细节=待证（仅摘要级）
- 失败面：nofilmschool.com 直读 403；「Peter Gabriel AI MV」查询 0 结果（疑限流）；邝盛方法论专文未获（仅人物背景核验，其剪辑思维经通用导演法间接覆盖）；DuckDuckGo 两轮限流
- 防线二：本件为调研员自报；呈 CEO 前建议抽验两根承重主张——Rolling Stone（700 条素材/1000 词提示词）与 purposewithpresence（段落映射表）
- 更新记录：T0 骨架落盘 → T1 方法论文（2 篇）→ T2 案例与中文工作流（4 篇）→ T3 邝盛基线+终稿 52 行
