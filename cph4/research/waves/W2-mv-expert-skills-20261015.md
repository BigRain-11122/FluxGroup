# W2｜影视/创意 Claude Skill 生态盘点（BigStream MV 产线·十三席位消费）2026-10-15
- 在档关系：增量档。R-20260928-agent-skills-01=官方规范+安装机制（不重复）；R-20260928-gh-install-skills=GitHub 技能普查（已盘 anthropics/skills 全 19 件、superpowers 全 15 件、capcut-edit、avoid-ai-writing、motion-skills 16 包、pixel-art-studio、trading/gamedev/scientific 组并已应用表）。本波只报其外新件：影视/创意关键词面（09-28 未查）+两官方仓新件 diff。
- 研究员 W2 ｜ 状态：完成 ｜ 消费方：BigStream 周杰伦 MV 41 曲重制线·专家评审团十三席

## ① 在档关系与范围
- 格式基线：SKILL.md 目录制与 Codely 100% 同构；装法=codely skills install 或拷单件入 .codely-cli/skills/；PROVENANCE 律照旧（详见 R-20260928-agent-skills-01）。
- 零重复圈：anthropics/skills 19 件、superpowers 15 件、capcut-edit、avoid-ai-writing、motion-skills、pixel-art-studio、create-game-assets（09-28 已盘已应用表）。
- 采点1·官方两仓 diff（api.github.com 直读 10-15）：anthropics/skills 仍 19 件、superpowers 仍 15 件（纯工程方法论），零新件零影视件→官方侧缺口只能靠社区件补。
- 本波实搜面：GitHub MCP 全端点故障→换源律=api.github.com（仓元数据/目录）+raw.githubusercontent.com（README/SKILL 内容）+DuckDuckGo（生态索引）；关键词=cinematography/screenwriting/storyboard/filmmaking/video prompt/color grading。
- 范围外（他波）：多智能体框架、灯光/服装知识库、剪辑工具运行时。

## ② 主表（新增量·星/许可/活跃三查在案）
| skill | 来源仓 | 星/活跃 | 许可 | 功能一句话 | 席位 |
|---|---|---|---|---|---|
| screenwriting-skills（26 件组） | jtydhr88/screenwriting-skills | ★1670·fork174·push 10-03 | MIT（引文 NOTICE 除外） | 47 本工艺书+23 卷剧本蒸馏的四层剧作法（通用戏剧构作/剧集/舞台/传统行业/大师语料）；正文中文、输出随语种；agentskills.io 标准 | ③⑪（⑫部分） |
| cinematography+model-routing | fal-ai-community/skills | ★251·fork35·push 09-29 | ⬜license=null 待验 | genmedia 具体视觉指导（shot-language/lighting-lens-color/examples 参考件）+生成模型路由；反「make it cinematic」空洞提示词 | ①⑥（②部分） |
| cinematography-for-ai | AmeerBashaK/claude-skills | ★0·push 10-14 | GPL-3.0 | StudioBinder 镜头表（运镜/镜头/构图）+Higgsfield/Seedance/King 运镜提示词；Vox 式解说片向 | ①⑥ |
| scriptwriter-skill+ai-storyboard-generator-skill | RainLib/AI-Storyboard | ★53·push 01-11 | GPL-3.0 | 剧本三幕九拍+视觉优先描述（为分镜师优化）→分镜关键帧图生成链 | ③分镜 |
| cinematography（仓内件） | MRCalderon3D/everything-ai-filmmaking | ★0·push 07-16 | MIT | AI 电影制作 .claude/skills 形态仓（内容未抽读⬜） | ①观察位 |
| awesome-claude-video-skills | ⬜仓主未定位（skillsllm.com 在册） | — | — | 180 个视频向 skill/工具仓索引·安全分级·中英双语 | 全席索引面 |
| 市场站：claudeskills.info／skillsmp.com／skillsllm.com／skillgild.dev／skillmd.com | — | — | — | 影视向 skill 检索/分发入口（存在经搜索快照验明·C级） | 采购目录 |
- 在册件席位补映射（09-28 已盘·零重复只映射）：capcut-edit→⑦剪辑节奏；avoid-ai-writing→⑤AI感体检；motion-skills→⑩VFX；theme-factory/canvas-design→⑨文字设计；content-skills（viral-hooks/voice-dna·★101·MIT 在档）→⑬平台运营。

## ③ 内容增量评述（对自研席位补强点）
- screenwriting-skills vs tw-mv-director：自研导演席有台湾 MV 审查+分镜定稿工艺，缺**剧作文学法底座**——此件补三幕/节拍/人物弧/对白（McKee/Truby/Snyder/Egri/Field 全谱）、人物心理（Indick《Psychology for Screenwriters》+Freud/Jung/Campbell 动机论→⑪正对口）、大师语料（契诃夫/小津/Succession 全剧拆表）；正文即中文=零翻译成本；41 曲歌词→剧情结构化正缺此件；sw-chinese-series-practice 自带内容红线/审查链→⑫部分补位。
- fal cinematography+model-routing vs 现栈：⑥席现只有 generate_prompt_from_media（还原型），此件补「按模型路由提示词」+反空洞词律+灯光/镜头/色彩判据文件（①席判据面·②调色部分）；与 Codely generate_video（Seedance 栈）直连。⬜license=null→仅借鉴直至补验。
- GPL 两件：AmeerBashaK（Seedance/King 运镜提示词表=与我栈同模型生态）与 RainLib（三幕九拍→分镜链）工艺可学，但 GPL 染疫禁拷入司仓，只能采思想自研；AmeerBashaK 系 Vox 解说片向+★0 契合再降。
- 缺口如实⬜：②调色（仅 fal 参考件部分覆盖）/④年代考据/⑧服装造型/⑨专向字体/⑫法务主体/音乐叙事结构专件——SKILL.md 生态无专件命中；sw 剧集层可适配补位音乐叙事。

## ④ 应用表（资产→席位→判定→理由）
| 资产 | 席位 | 判定 | 理由 |
|---|---|---|---|
| jtydhr88/screenwriting-skills | ③⑪ | **直接采用** | MIT·★1670·10-03 活跃·agentskills.io=Codely 同构；先装 sw-workflow/sw-story-structure/sw-dialogue/sw-character-conflict/sw-scene-craft 五件试点，避免 26 件全装摊薄触发面 |
| fal-ai-community cinematography+model-routing | ①⑥② | 适配·待许可 | ⬜license=null：根 LICENSE 补验为 MIT/Apache→升级直接采用；先以参考件工艺作判据借鉴 |
| AmeerBashaK cinematography-for-ai | ①⑥ | 仅借鉴 | GPL-3.0 染疫+★0+解说片向非 MV 向 |
| RainLib scriptwriter+storyboard | ③ | 仅借鉴 | GPL-3.0+2026-01 后停更 |
| MRCalderon3D everything-ai-filmmaking | ① | 观察 | MIT 可装但 ★0·内容未抽读⬜·07-16 后停更 |
| awesome-claude-video-skills | 全席 | 索引采编 | ⬜仓主未定位；后续波按 180 仓目录补扫②⑧⑩空席 |
| capcut-edit/avoid-ai-writing/motion-skills/theme-factory | ⑦⑤⑩⑨ | 已装/在档 | 09-28 应用表在案，零重复 |
| ②⑧⑫④席专件 | — | ⬜自研待办 | 无对口开源件命中（用 skill-creator 自造） |

## ⑤ TOP-3 安装建议 + 验证声明
1. **screenwriting-skills**：`codely skills install jtydhr88/screenwriting-skills` 或拷 plugins/screenwriting/skills/* 子集入 .codely-cli/skills/；PROVENANCE 记 MIT+引文 NOTICE 例外；装后用户 /skills reload 新会话生效；接入点=bigstream-expert-panel ③⑪席判据源+tw-mv-director 分镜前置结构化。
2. **fal cinematography+model-routing**：先 1 次读取补验根 LICENSE→MIT/Apache 则拷件装（①⑥席）；null 则只借鉴 shot-language/lighting-lens-color 工艺入 tw-mv-director 附则。
3. **awesome-claude-video-skills**：1 次读取定位仓主→纳 W3 采购目录，按 180 仓补扫调色/服装/VFX 空席。
- 验证声明：读取 20/20（成功 12·失败 8：GitHub MCP 全端点「Could not parse tool response」×7→按换源律全量改 api.github.com/raw/DuckDuckGo 补验；DDG 零结果×1）。源分级：A=8（api.github.com 六仓元数据+两官方仓 listing+raw README 一手直读）、B=1（jtydhr88 许可=API 字段+README 声明双源互证）、C=3（claudeskills.info/skillsmp/skillsllm 市场站快照）、M/⬜=3（awesome 索引仓主未定位·MRCalderon3D 内容未抽读·fal 许可未验明）。零断言三态在案，关键结论均有 api.github.com 直验。失败面=GitHub MCP 服务整波不可用（工具面留档）；预算尽致 3 项⬜未闭（各 1 次读取可闭，已列 TOP-3 行动项）。
