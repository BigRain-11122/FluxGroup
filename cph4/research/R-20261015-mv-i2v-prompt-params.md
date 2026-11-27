# R-20261015-mv-i2v-prompt-params — MV 产线 i2v 提示词与参数配合 playbook（CEO 令 O-20261015-1600 扩面·产线参数波）
> 溯源：CEO 原话「提示词技巧，模型和参数的配合」·消费方=mv-album-001-jay 产线·判据=三问预注册
> 验证声明：实读 19 次（仓内 7 文件直读+4 目录列举定位·外部 3 检索+5 抓取）·成源 12 条（A=2/B=2/C=1/M=7）·失败面：①「H3 Context-IR」仓内配置面无此名🟡最近匹配=R2V②「INT8」管线口语 vs 配置实底 pruned_int4 不一致🟡③本地 H3 三字段结构是否强制未独立验证🟡④2.5 长片分段细节源遇会员墙→以 A 级 API 文档兜底
## 一、我方 V3 提示词层根因诊断（bmc 弹药库实读：V3 prompt 里运镜词存在率/结构缺陷·带实例指针）
- 实弹面=i2v-wave-manifest.json 53 条生产 i2v_prompt（mv-album-001-jay·engine=minimax_h3 first_frame 768P）+h3 两档配置 prompt 字段+星晴-SHOTLIST-v3 运镜字段（Motion-幅度-速度）——[M 仓内直读]
- 「prompt 里没有运动词」假设**判负**：53/53（100%）含运镜子句；但 14/53（26%）="holds a perfectly static shot" 定机位；动词集仅 9 种（push/pull/tilt/pan/track/slide/crane/handheld/hold）
- 真根因=**运动参数空间自坍缩（四重同一律）**：①36/53 显式 "with small amplitude"·0 条用 large·0 条用 fast（官方幅度/速度高档从未触达）②速度仅 slow（27）/steady（9·"steady" 非官方词表词🟡·官方速度档仅 slow/fast·中档=省略）二值 ③53/53 收尾一律挂 "Restrained continuous motion...only" 抑制条款+shotlist「全片禁快甩」——动势天花板自我压平 ④显式运镜落点（toward/until/revealing）仅≈9/39 动镜·官方例句必带落点半句
- 实例指针：KN_KN04「掷出（burst 快）」镜 prompt 仍写 "tracks alongside with small amplitude at steady speed"——生成端零速度表达·快慢全靠装配端 speed 1.2 倍速（win_s=src_s×speed）后置补救 [M manifest]
- 本地链另病：h3_t2v_local_768p_bmc.json prompt 用 "dollies in"（非 H3 官方 20 运镜词表词·官方警告近义词=赌运气[C]）+Start/End framing（首尾帧格式）·且未挂官方三字段结构——[M]
- 一句话结论：**运动词全有、参数全空**——幅度/速度两旋钮锁死最小档+落点锚缺失+prompt 内零时长表述（pacing 全后置装配）→运镜单调是提示词参数自坍缩·非词汇缺失
## 二、各模型提示词结构（H3 本地/Seedance 云端·运动词位置/时长表述/负面词/风格锚·逐条带源）
**H3 本地链（MiniMax H3·ComfyUI·UNET 实底=fl2va pruned_int4·文编=qwen3vl_32b AWQ）——英文正身·官方三字段** [B docs.comfy.org 引 MiniMax 官方指南]
- 结构：I2VA 首行固定对齐句 `For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.`+空行→`integrated_multimodal_description: [Shot 1]…`→`overall_soundscape:`→`non_diegetic_music:`；对白 `<d>` 标签·说话人 (S1) ID·屏内文字英文双引号原样照抄 [B]
- 运动词位置=镜头描述内自然动作句·官方 20 词表照抄：Static Shot/Push In/Pull Out/Zoom In·Out/Pan L·R/Truck L·R/Tilt Up·Down/Pedestal Up·Down/Arc/Tracking/POV/Roll/Shake；句式=运动类型→幅度（small/large·中等省略）→速度（slow/fast·常速省略）→**落点半句**（toward X/revealing Y/as Z exits frame）；一镜一运镜·同镜双指令互抵→几乎不动·变向=[Shot N]+时间戳 `At 00:04.000, the camera cuts to…` [C minimax3 收录官方指南 §4.3]
- 负面词清单=**无负通道**：BasicGuider 采样于 cfg=1 跳过无条件分支——点名不想要元素=把它登记进画面（"no subtitles" 会生出字幕）→一律正向改写（"the sign above the door is blank"）[B]·我方 SHOTLIST「提示词零否定词」✓同律 [M]
- 时长表述=prompt 内零时长词；length=24fps 帧数·向上吸附 17 帧块网格（17k+5）·默认 124≈5.17s；云 API 4-15s·>15s 自动分段（H3 Max 档=更长单镜）[B/C]
- 风格锚=写在 [Shot 1] 开头（整体风格+开场构图先行）[B]；警示判例：SIL4 两换种子仍 cel-shading 崩坏——prompt 风格锚敌不过 checkpoint/LoRA 先验·风格破裂查生成侧非提示词侧 [M QC-r977b]
**Seedance 2.x 云端（中文可用·first_frame/首尾帧/全模态参考）**
- 2.0 进阶公式=精准主体+动作细节+场景环境+光影色调+**镜头运镜**+视觉风格+画质+约束条件；分镜时序=镜头 1/2/3 编号·每镜=运镜+主体动作表情+空间变化+音频·不强制每段时长 [A ark 官方指南]
- 2.5 基础公式=主体+动作/事件（必写）+场景环境/视觉风格/运镜切镜/声音（可选·不需就省）；三高频句式：「只采用…不采用…」（素材职责）·「**结束时画面里能看到…**」（收尾帧锚）·「X 对应@图片N」（主体映射）[B 收录字节官方 2.5 指南]
- 运镜/动作词：标准术语直用（中景/特写/缓慢推镜/平稳横移/固定镜头）；动作=肢体细化+程度量化（缓慢抬手/快速转头/用力蹬地）+**优先低缓连续小动作**+过渡衔接（借着转身惯性顺势抬手）+情绪具象外化（「悲伤」→低头/肩颤/攥衣角）[A]
- 负面清单=正向约束句·官方模板：「保持无字幕」「避免生成任何文字或字幕」「不要生成Logo」「不要生成水印」[A]——**与 H3 反律：Seedance 官许「不要」·H3 禁点名**（跨模型迁移必查行）
- 时长表述=官方明令「生成参数（时长、比例）不写进提示词」·由 API/页面设置 [B]；符号：台词{}·音效<>·音乐()·字幕【】；素材四角色=角色锚定图+场景定调图+**运镜参考视频**+节奏氛围音频·推荐 4-5 素材 [A]
**H3 Context-IR 🟡**：仓内配置面未见此名；最近匹配=ComfyUI R2V 全参考模式（主体定义+`<Picture N>` 条目+保留分析 fully/partially_preserved·attribute_transfer·weak_reference+多格参考图单列）[B]——消歧前按 R2V 正身套用
## 三、参数配合矩阵（模型×分辨率×时长×两段制档位·代价与效果·逐条带源）
| 链/模型 | 分辨率档 | 时长/帧 | 关键参数 | 两段制位·代价 | 源 |
|---|---|---|---|---|---|
| H3 本地·短验档 | 864×480 | length 124 帧@24fps≈5.17s（17×7+5 网格吸附） | seed 20261009·steps 4（turbo LoRA）·res_multistep·simple·denoise 1.0 | 构图/运镜方向抽检·与正片同 seed=可比对 | M h3_t2v_local_480p.json |
| H3 本地·正片档 | 1344×768（短边 768·32 倍数吸附） | 同 124 帧 | 同 seed 同参 | 正片·17.5min/条（16G GPU）·双机夜窗 64 条/晚 | M 768p_bmc.json+PIPELINE |
| H3 云端（产线现用） | 768P（平台另有 2K 档） | 政策带 5s / 8-15s（API 4-15s） | first_frame 模式·≤10 单/波·100 任务/日全队 | 正片·配额封顶 1-2 天·装配端 speed 0.82-1.2 补 pacing | M manifest+PIPELINE |
| Seedance 2.0 云 | 480p/720p/1080p/4k·默认 720p | duration [4,15]·-1 智能选·frames 优先 | seed 参数+**camera_fixed**（API 级定机布尔）+role first/last_frame | **draft 样片两步制**=天然「短验→正式」 | A ark API 文档 |
| Seedance 2.5 云 | 480p/720p/1080p·默认 720p（无 4k） | duration [4,30]·-1 | 全模态参考 0-30 图+0-10 视频+0-10 音频·可纯音频·edit/extend 型参数约束 | 30s 长片连贯直出·局部编辑档 | A ark API 文档 |
- 档位效果律：幅度 large=大开大合揭示·small=构图微调；幅度×速度**互相独立**（大幅慢速≠小幅快速·两档均应排产）；中等档=省略不写（多写抢落点注意力）[C 引官方]
- seed/重试我方实底：KF 试构图 672×384 每镜 1 种子先行截杀构图漂移→正档 1344×768 [M SHOTLIST]；**换种子救不了系统性失败**（SIL4 s9013→s9017 连续 cel-shading）·t2i 重烧两轮仍漏核心件→改外科局部修 QwenEdit inpaint [M QC-r977b]；i2v 单条回炉 15 分钟·回炉律只回本站·档位污染检每波跑·未过闸帧白名单外物理不可达 [M PIPELINE]
- 量级锚：KF 批 35 张≈20 分钟 GPU·KF 引擎=Krea2 turbo 1344×768·8 步·jman LoRA 0.6 [M]；「INT8 i2v」口语 vs 配置实底 pruned_int4——以配置为准🟡 [M]
- 两段制映射：本地「480P 短验→768P 正片」=同 prompt 同 seed 跨档比对 [M]；Seedance 对应物=draft 样片两步制（Step1 验→Step2 正式·部分参数自动复用）[A]；云端 H3 无中间验档→依赖逐条 QC+单条回炉 [M]
## 四、KF→i2v 交接标准（首帧动势设计/留白方向/接力提示词模板·消费方直接接线件）
- 三律：①首帧构图=运镜**起点**（官方：写清景别·运镜才有起点 [C]）②**留白方向=运镜落点方向**——首帧须在运镜终点侧留负空间（判例：KN16 云海月晕帧留天→"until the moon halo fills the sky" 落点可执行 [M]）③一镜一运镜·变向=切镜 [C]
- 静帧 vs 动势帧：定机位帧（我方现状 14/53）→i2v 只写主体动势（低缓连续小动作+动作量化+过渡衔接 [A]）；动势帧→运动词+幅度+速度+**落点半句**（toward/revealing/as…exits [C]）——落点正是我方最缺半句（≈9/39）
- 接力模板·H3 first_frame：对齐句（0.00s·Picture 1 fully referenced）→`[Shot 1]` 开场构图+风格锚→`The camera <20 词表动词> with <small|large> amplitude at <slow|fast> speed toward <首帧留白侧落点物>`→主体一句低缓动作→soundscape/music 字段（MV 纯画面轨→写 N/A）[B/C 拼装]
- 接力模板·Seedance first_frame：图 role=first_frame→主体+动作（必写）+运镜切镜（可选）+「结束时画面里能看到<落点>」收尾帧锚 [B]；时长/比例走 API·不写 prompt [B]；参考视频已定运镜节奏→只写继承不复述（复述与素材打架）[B]
- 现状接线（消费方直接可用）：KF 产物 frames/*.png→i2v-wave-manifest `i2v_prompt` 字段直发已通 [M]；改版点=①幅度/速度档位调度表（按镜头情绪排 small/slow×large/fast）②落点半句强制位 ③"steady"→官方中档省略写法 ④本地链 "dollies in"→"pushes in" 词表归一
- 时长接力律：两模型 prompt 内均零时长表述 [B/C]——pacing 由参数档+装配端 speed 表达·我方现行为合规；Seedance 延长拼接修补官方律=前段末删 6 帧+后段首删 1 帧 [A]
## 五、结论应用表（强制·落点四选一：任务单/法文修改/决策呈报/判负留痕）
| 结论 | 落点 | 状态 |
|---|---|---|
| V3 运镜单调根因=幅度/速度档自坍缩+落点锚缺失（非缺运动词） | 任务单：mv-album-001-jay i2v_prompt 正身改版——挂幅度/速度调度表+落点半句强制位（manifest 生成器改） | 接线中 |
| H3 无负通道须正向改写 vs Seedance 官许「不要」——负面词分模型执法 | 法文修改：SHOTLIST「提示词零否定词」加注「限 H3 链·Seedance 链可用官方约束句」 | 待产线接 |
| 参数矩阵：480P 864×480 短验→768P 1344×768 正片（同 seed 同参）·Seedance=duration API+draft 两步+camera_fixed 定机 | 任务单：PIPELINE ⑤站挂「参数档位表」注 draft 样片制与档位污染检 | 接线中 |
| KF→i2v 交接标准：两条接力模板（H3 对齐句+词表落点句 / Seedance 收尾帧锚）+首帧留白方向律 | 任务单：星晴-KF-PACK 增「i2v 交接正身」字段·④b 白名单带出 | 接线中 |
| 「H3 Context-IR」仓内无此名配置·最近匹配=R2V 全参考模式 | 判负留痕：命名消歧后回灌（🟡）·消歧前不按未验证命名接线 | 已留痕 |

- 更新记录：T0 骨架落盘（早落盘律）→ T1 仓内证据面（bmc 弹药库+h3 两档配置+产线正典·一节落盘）→ T2 外部面（ark A×2·comfy B·xiaohu B·minimax3 C）→ 终稿 53 行·自查纠偏 2 处（速度档计数 33→27·落点 8→9）
- 防线二：待独立抽验两承重主张——①53 条 i2v_prompt 运镜词统计（i2v-wave-manifest.json）②H3 无负通道（docs.comfy.org BasicGuider cfg=1 段）
