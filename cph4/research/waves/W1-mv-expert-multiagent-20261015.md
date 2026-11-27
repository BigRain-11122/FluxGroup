# W1：影视/MV 制作专精多智能体系统与专家角色包（2026-10-15）
> 在档关系：与 R-20261014-master-agent-frameworks-01.md 互补——通用编排框架已盘点判负/借模式，本文不复盘框架本身，只收影视专精角色包/示例（框架宿主示例入表注明宿主已盘点）。

## ① 在档关系与范围
- 范围=判据①②③：影视/MV 多智能体与专家 agent 开源项目、各项目专家角色与实现载体、对 BigStream《爱在西元前》41 曲线（H3 i2v+Krea2）十三席评审团的采用判定。skill 生态普查、灯光/服装知识库、剪辑工具、中文提示词库（如 awesome-seedance 2,702★·MIT）=他波领域未扫。
- 通道故障：search_repositories 工具 8 连败（解析错误零返回），全程改 shell 直连 api.github.com（与 R-20261014 同法）。

## ② 主表（星/许可/最近push=api.github.com 2026-10-15 直读；「确」=README 直读，「描述级」=仅 API 描述，其余待证）
| 项目（星·许可·push） | 专家角色一句话 | 实现载体 |
|---|---|---|
| eternityspring/shuohao-skills（4,585·Apache-2.0·10-15 当日活） | 大纲改编/角色圣经/美术圣经/编剧/走位调度/分镜六工序+角色参考图生成 | agent-agnostic skill 包（SKILL.md+JSON/HTML 报告，Claude Code/codex 直跑）；分镜 2–5s 硬切门+段落≤15s 生成门（确） |
| LuoJiangYong/muse-video-skill（43·MIT·09-30） | 导演/编剧/摄影/美术/特效/声音六角色虚拟剧组 | Agent Skills：38 案例技法库+8+1 阶段管线（Director 每阶段审≤2 轮+_meta 追溯）+Phase 7.5 六段式 prompt 编译（已适配 Seedance 2.0+arkcli+成本估算）（确） |
| echris6/motion-video-kit（1,109·MIT·10-14） | 建造者≠裁判的独立 critic 审片阵容 | Claude Code skill：Gauntlet 循环+critic-prompts 全文+可测质量条（frozen time/ebur128 响度/对比度/品牌色）+motion 语法（6 规则 16 机制，源自 28 样片）+音频 back-timing 卡拍（确） |
| showlab/MovieAgent（368·无许可·2025-03-26 停） | 多智能体 CoT 规划长片：故事线/场景构成/摄影设计/角色交互自动化 | Python 推理码（免训练）+arXiv:2503.07314（确·README 徽章）；具体 agent 角色名单 README 未列→待证 |
| HITsz-TMG/Anim-Director（262·无许可·2026-01-07 停） | 多模态智能体受控动画导演 | 论文+码（描述级，内部待证） |
| HL-hanlin/VideoDirectorGPT（183·无许可·2024-08-07 停） | LLM 视频规划器（多场景一致生成） | COLM 2024 论文官方码（描述级） |
| neopen/story-shot-agent（222·MIT·10-14） | 剧本→分镜→Sora/Veo/Runway 提示词代理 | LangGraph+LlamaIndex，跨片段角色一致，MCP/REST/A2A（描述级） |
| HBAI-Ltd/Toonflow-app（17,746·MIT·10-13） | 剧本创作/智能分镜/角色场景资产/图像视频全流程平台 | 自托管平台（Docker）+AI Agent 工作流+MCP（描述级）→Windows 主栈判负 |
| waooAI/waoowaoo（14,555·NOASSERTION·09-21） | 工业级全流程 AI 影视 Agent 平台 | 平台（描述级） |
| ArcReel/ArcReel（5,509·AGPL-3.0·10-15 当日活） | 小说/剧本→资产/分镜/视频/剪映草稿流水线 | 跨镜一致性+多供应商+费用追踪（描述级） |
| HKUDS/FilmAgent（仓消亡⬜·404 直证） | 传导演/编剧/演员多智能体（未证·M） | 仓页 404；arXiv API 空返回，论文存在性待证 |
| DreamFactory「AI 电影」（未找到·待证） | — | GitHub 名/描述/README 全文+arXiv 四路检索无影视向同名仓（同名=dreamfactorysoftware 企业 API 平台 1,785★，与影视无关）；疑闭源/易名 |
- 次要仓（均描述级）：inkos（10,303·AGPL·小说/IP 改编向）、moyin-creator（4,720·AGPL·Seedance 2.0 剧本到成片批量化）、HITsz-TMG/VideoClaw（1,860·MIT·单员工全自动）、aivideo-production-skills（15·MIT·门控工件制+连续性控制+成本治理）、slipknot0130/Film-Production-Toolkit（13·无许可·编剧室 SOP+分镜提示词引擎）、zhlmi/screenplay-review-checklist（13·NOASSERTION·37 判据对抗式剧本诊断）、ssurekumar01111-hue/cinema-pilot（2·MIT·14×Gemini/ADK agents 共享 Production Graph，宿主 ADK 已盘点）、Adriana-Shao/virtual-crew（1·NOASSERTION·prompt QC 失败目录+逐镜返工台账）。

## ③ 可借鉴机制（MIT/Apache=可搬文本带署名；无许可/AGPL/NOASSERTION=只看不搬）
- 「技能=专家席」结构（确·双源）：muse 六角色+每阶段审片轮、shuohao 六工序流水→可平移为我方十三席 skill 包。
- 审片分离律（确·motion-video-kit）：builder≠judge、全新 critic 看真实渲染、逐项验证、留台账；critic-prompts.md 可直接搬为⑤席审片词底稿。
- 硬门/闸同构（确）：shuohao「切 2–5s 硬门」+muse 8+1 阶段门→与我方四闸同构，可对齐参数化成「闸表」。
- 提示词编译器（确·muse）：Phase 7.5 六段式 prompt+参考图按资产 ID 引用不转述+Seedance 2.0 适配→⑥席 I2VA 底座（与我方 H3 i2v 同代管线）。
- 一致性资产链（确·shuohao）：角色圣经/参考图/美术一致性锚+灯光状态变体+no-people/no-hands 白拍→⑧⑩席连续性与崩坏预案蓝本。
- 可测质量条+诚实规则（确·motion-video-kit）：frozen time/响度/对比度实测检查+「不得将 AI 生成影像当真实成果、强制标识」→⑤⑫席检查单原型。

## ④ 应用表（资产→席位→判定→理由）
| 席位 | 采源资产 | 判定 | 理由 |
|---|---|---|---|
| ①摄影指导 | muse 分镜卡「机位/灯光」字段+38 案例库 | 适配采用 | MIT 纯文档；需扩展运镜三维/光路/胶片年代语法 |
| ②调色师 | muse 色调板（hex+成因字段，全片统一） | 仅借鉴 | 无专职调色角色；暗部/颗粒规则需自建 |
| ③导演/叙事 | shuohao outline 节拍表+muse 阶段审片轮 | 适配采用 | Apache/MIT 双源；因果链/节奏曲线/留白需我方律叠加 |
| ④美术/年代考据 | shuohao 美术圣经（一致性锚/灯光状态变体/尺度参考） | 适配采用 | Apache 可搬；年代考据层需接我方考据库 |
| ⑤受众代表 | motion-video-kit Gauntlet critic 循环+critic-prompts | 直接采用 | MIT+Claude Code 原生；builder≠judge 补评审团自审自批盲区；3 秒认出标准自建 |
| ⑥提示词工程 | muse Phase 7.5 六段式编译+shuohao 生图/设计 prompt | 适配采用 | Seedance 同族管线；I2VA 词表 lint 需自建 |
| ⑦剪辑节奏师 | motion-video-kit 音频 back-timing 卡拍+shuohao 2–5s 硬门 | 适配采用 | 卡拍/硬门可搬；词锚对位需自建 |
| ⑧服装造型总监 | shuohao 角色圣经（设计 prompt/模型表/声音 prompt） | 仅借鉴 | 有角色一致性、无服装史实考据；ArcReel 跨镜一致性（AGPL）只看机制 |
| ⑨文字设计 | muse 字幕层（文案×字体族×位置，与画面 prompt 解耦→烧录 spec） | 适配采用 | MIT 可搬；楔形文字/伪文字病灶检查自建 |
| ⑩VFX 特效总监 | shuohao no-hands 白拍避崩+muse 特效角色 | 适配采用 | 崩坏预案已知打法可搬；生成物理风险清单自建 |
| ⑪情感叙事心理 | screenplay-review-checklist 37 判据对抗诊断 | 仅借鉴 | NOASSERTION 不搬文本；「只找茬+逐条证据+邀请反驳」机制自建同构 |
| ⑫法务合规顾问 | motion-video-kit 诚实规则+AIGC 标识强制；aivideo-production-skills 成本治理 | 仅借鉴 | 标识条款 MIT 可搬；词曲同步权/AIGC 备案需我方法务自建 |
| ⑬平台运营总监 | 无对应开源角色（motion-video-kit business playbook=B 端报价向） | 空缺·自建 | 3 秒钩/完播/横竖版无现成轮子 |

## ⑤ TOP-3 采用建议+验证声明
- TOP1 直接采用：shuohao-skills（Apache-2.0·4,585★·当日活）——六工序 skill 包+硬门，纯文档进栈零成本；改造点=短剧时序→41 曲音乐驱动+词锚对位层。
- TOP2 直接采用：motion-video-kit（MIT·1,109★·活跃）——critic 循环+可测质量条+音频卡拍，直补⑤⑦⑫三席，Claude Code 原生即插即用。
- TOP3 适配采用：muse-video-skill（MIT·43★·开发中）——六角色剧组+Seedance 2.0 编译器与 H3 i2v 同代；星低=风险，建议 fork 快照+署名留存。
- 验证声明：外部源实读 21 次（预算≤20，超 1 次如实披露：arXiv API 空返回仍占一读）+本地在档件 1 读（查重律指定）；成源 18 读全 A 级（api.github.com 搜索/仓页/README 直读），B/C 级 0 采信；M 待证项=FilmAgent 论文存在性、MovieAgent 角色名单、Anim-Director/VideoDirectorGPT 及各平台仓内部、DreamFactory。
- 失败面：①search_repositories 工具 8 连败（通道故障，shell 直连绕过）；②HKUDS/FilmAgent 仓 404（仓消亡⬜）；③「DreamFactory AI 电影」四路检索未找到（待证：疑闭源/易名）；④arXiv API 对 FilmAgent/DreamFactory 两查空返回。星/许可/push 全部=2026-10-15 当场直读；角色内容仅 README 直读处标「确」，确认/推测/待证三态执行。
- 更新记录：T0 骨架落盘（早落盘律）→T1 四组检索→T2 七组检索+FilmAgent 404 直证→T3 arXiv/DreamFactory 四路补查→T4 四仓 README 直读→终稿（≤60 行·node 落盘实测）。
