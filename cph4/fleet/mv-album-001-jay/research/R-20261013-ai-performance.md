# R-20261013-ai-performance — AI 生成视频中的人物表演技巧（表演指导专家·BigStream MV 产线）
> 溯源：mv-album-001-jay 产线任务单（CEO 批「人物表演单调」·人物镜预算扩容：背影/剪影/侧影/演唱镜）·消费方=BigStream MV 产线（图生视频：首帧定构图+提示词控运动）
> 判据预注册：①表演提示词技术（情绪层次/词表/写法）②图生视频微表情可控边界 ③MV 演唱镜+背影剪影表演语言与剪辑补偿
> 验证声明：实读 18 次（网络抓取 12 成功+3 次 403·仓内查重 3 文件）·成源 10 条（A=0/B=3/C=7）·失败面：见 §三

## 一、核心发现
- 微表情写法双源定谳：①抽象情绪词 AI 不响应，须写「可视信号」——「She feels nervous」无效，「inner eyebrows rise slightly, lips press, exhale, jaw relaxes」有效（B 源 https://www.seedance.tv/blog/minimax-h3-microexpression-prompts）；②肌肉解剖词优于情绪词，FACS AU 词表直用：AU12=lip corner puller（笑）/AU15=lip corner depressor（苦）/AU1=inner brow raise（悲）/AU4=brow lowerer（怒凝）——Kling/Seedance/Gen-3/Veo 实测（C 源 https://viddo.ai/tutorial/ai-video-micro-expression-prompts）
- 表演节拍律：4-15s 一镜只装「一个主导表演节拍」，结构=中性基线→触发→反应→落定；禁全脸堆指令（眉眼鼻唇同时下令互相矛盾）；眨眼=偶尔标点非机械时刻表（seedance.tv 同上）
- 图生视频提示词分配律：首帧已锁表情与构图，「提示词空间全给运动、表情时序、眼神与不可变项」（seedance.tv 同上）
- 量化可控边界（B 源·Hailuo 官方实验室 150 次跨引擎实测 Kling/Gen-3/Luma）：92% 结构稳定上限 5.2s，>6.0s 时 45% 样本下颌/眼部融化；最优微表情平均在第 2-3 次重roll 出现（「Rule of 3」跑 3 变体选瞳孔锚定最稳 seed）；motion 值 3-5 低中档（https://hailuoai.video/pages/knowledge/micro-expressions-realistic-human-ai-video）
- 首帧表演学：极端表情首帧=网格无变形空间，须近中性+内眼微张力基线；参考图禁伦勃朗侧光（深影被误读为永久面部特征），软正光后再期补光（Hailuo 同上）
- 大情绪词破脸律：「smiling happily」被锁成固定面部形状=摆 pose 非表演；降档词：angry→jaw tight/lips pressed/controlled frustration，sad→distant gaze/slow blink/mouth relaxed downward，shy→quick glance away/fingers fidgeting with sleeve；表情须由身体动作「引起」——先写手部动作链再让笑作为副产品浮现（C 源 https://www.naviya.chat/en/blog/micro-expression-ai-video-prompts）
- 眼神单变律：5-6s 一镜只给 1 次注视转移，堆叠眼神指令=瞳孔漂移+身份漂移；景别配对：微反应中近景/眼嘴控制特写/静张力侧面特写，过宽→模型夸张面部（naviya 同上）
- 模型脾气（C 源 https://genra.ai/zh/blog/ai-video-prompts-that-actually-work-2026-guide）：可灵 3.0=「角色动画师」——精细肢体力学直写（「重心移到左脚」「缓缓转头」）+面部微表情（「浅浅的微笑」「微皱眉头」）；Seedance 2.0=「动态专家」——写节奏与能量（「干脆利落的顿点」「高能量」「逐渐升级的强度」）；矛盾指令=视觉混乱（推拉/哭笑同镜必炸）；五要素=主体/动作/场景/镜头/风格，5s=一个动作、10s=动作+反应；多镜一致性=锚定元素逐镜原样复读（C 源 https://www.550wai.cn/blog/ai-video-prompt-engineering）
- MV 演唱镜 eyeline 三选一律：开拍前定「对镜头唱/对画外对象唱/在编舞空间中移动」——eyeline/呼吸/手势小选择改变观众关系；视觉递进留给副歌最强爆发（B 源 https://inspire-station.com/blog/performance-music-video-production-guide）；「表演者的身体能量而非对口型精度承载镜头」（C 源·仅搜索摘要·待证 https://www.youtube.com/watch?v=1IB2mymTmEE）
- 剪辑救表演律（B 源 https://www.hanna-eng.com/guides/monter-un-clip-musical）：卡音乐重拍而非画面；段落-剪辑映射：主歌长镜让表演呼吸/预副歌渐进缩短/副歌最狠卡拍+最佳角度/桥段换质感；对口型镜=波形尖峰对齐+硬辅音检验；hook 用特写、器乐段用全景（C 源 https://playpause.io/blogs/controlling-pacing-and-rhythm-in-video-edits：卡上节拍后平庸素材也显 intentional；等长镜头=机械平线，3s→2s→1s 加速冲顶后长镜释放；重点句前留一拍静默）
- 背影/剪影表演律（B 源 https://flashboards.yaroflasher.com/learn/lighting/silhouette/）：观众从「姿态与轮廓 alone」读身份/动作/情绪；轮廓必须干净（交叠肢体/正面姿态/杂光补光=糊成泥）；低机位让全身切亮背景，广角低机位=顶天立地、长焦=人与落日同框；用途五式：匿名威胁/图腾图形/渺小感/无脸亲密/藏信息延后揭示；肩开胸开=自信、缩肩=溃败（C 源 https://www.scienceofpeople.com/acting-tips/）
- 战略判断（本报告综合）：背影/剪影镜=AI 表演「安全区」——无脸即绕开 AI 最弱的脸部恐怖谷（Hailuo 数据），首帧只须轮廓干净+姿态正确，成功率天然最高，人物镜扩容应优先此型

## 二、表演词表+适配建议
| 情绪/镜型 | AI 可执行身体动作（提示词粒度） | 成功率经验/来源 |
|---|---|---|
| 悲伤 | distant gaze/slow blink/嘴角 AU15 下垂/呼吸停半拍/低头+肩微塌 | naviya 稳定词+与仓内官方外化法同构 |
| 喜（真笑） | 唇角上升 3mm+眼轮匝收缩 AU6（鱼尾纹） | Hailuo Duchenne 律：双 AU 才可信，缺眼部=面具脸 |
| 压抑怒 | jaw tight/lips pressed/narrowed gaze/肩保持不动 | naviya 降档词；禁「angry」原词 |
| 羞/心动 | quick glance away/手指捻衣袖/重心微移/抿唇后浅笑 | naviya「动作引出表情」模板 |
| 藏紧张 | 内眉微抬+抿唇<1s+浅呼吸抬胸+手指松开物件 | seedance.tv 四模板之一·节拍化实测 |
| 私人失望 | 鼻翼收紧/眼睛眯/闭嘴+鼻呼吸/回视任务 | seedance.tv 模板：禁 disgust face |
| 释然带忧 | 眼先亮/肩松/浅笑将现/一次安静呼气/下眼睑留忧 | seedance.tv 模板 |
| 聆听反应 | 保持注视/关键词后眨一次/单侧嘴角抬而眼含悲 | seedance.tv 对话模板 |
| 演唱镜 | eyeline 三选一+身体能量律（手势/重心/头点）+呼吸可见 | inspire-station；能量>口型精度（待证） |
| 背影镜 | 肩线开合/头角度倾转/步伐节奏/手部动作入轮廓 | flashboards+scienceofpeople：姿态独扛情绪 |
| 剪影镜 | 侧面轮廓/低机位全身切亮背景/exposed for the sky | flashboards AI 提示词范例直用 |

适配建议→落点表（P-65 应用表·落点四选一）：
| 结论 | 落点 | 状态 |
|---|---|---|
| 表演节拍律+一镜一节拍+Rule of 3 重roll | 任务单：mv-album-001-jay 表演外化表 v2 每镜标注节拍+眨眼/呼吸支撑 | 接线中 |
| 背影/剪影=表演安全区优先扩容 | 任务单：分镜表镜头预算分配·无脸镜占比上调 | 接线中 |
| 剪辑卡点映射表救静态表演 | 法文修改：AUTO-POLISH-LOOP-v1 增「卡拍重切+等长镜头检测」步骤 | 接线中 |
| 演唱镜 eyeline 三选一律 | 决策呈报：MV-PREPRO-MASTER 表演栏增 eyeline 必填项 | 接线中 |

## 三、验证声明
- 实读：网络抓取 15 次（12 成功+3 次 403）+仓内查重 3 文件（ALBUM-QUALITY-BAR-v1 L13 官方外化法定谳·既有 R-件·R 骨架模板）；搜索 9 轮（5 命中/4 限流空返·中英文各半）
- 成源 10 条分级：B=3（Hailuo 官方实验室/flashboards 电影教学/hanna-eng 专业剪辑指南）·C=7（seedance.tv/viddo/naviya/genra/550wai/playpause/inspire-station）；「微表情写法」「量化边界」双源交叉确认
- 三态标注：其余=单源直读确认；「能量>口型精度」=单源搜索摘要·待证；知乎「60 表情词表」=403 未直验·待证
- 失败面：imagestudio.com 403（MV 实拍全指南未入库）、zhuanlan.zhihu.com 403（中文 60 表情词表）、DuckDuckGo TLS 指纹限流 4 轮空返（换简化查询补救后命中）
- 更新记录：T0 骨架落盘→T1 微表情域（viddo+seedance.tv）→T2 边界域（Hailuo+naviya）→T3 中文+剪影域（genra+550wai+flashboards）→T4 终稿补 MV/剪辑域（inspire-station+hanna-eng+playpause）
