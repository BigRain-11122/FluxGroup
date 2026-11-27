# W3 · 电影语言领域知识资产与语料库 — 20261015

> 在档关系：与 R-20261015-prompt-rules-official.md（H3/Seedance 官方提示词规则在档）及 R-20261015-mv-i2v-prompt-params.md（I2V 参数在档）互补——官方规则已覆盖模型侧提示词语法；本件只收**官方规则之外**的电影语言领域资产（术语本体/镜头语言词库/电影级提示词语料/灯光知识/服装史实/调色资产/剪辑语法）。消费方=BigStream MV 产线十三席评审团（周杰伦 41 曲重制，H3 i2v+Krea2 关键帧管线）。波次边界：只做领域知识资产与语料库；agent 框架、SKILL.md 生态、剪辑工具、中文社群提示词库不碰。

## ① 在档关系与范围
- 在档已覆盖：H3 I2VA 三字段结构+官方 20 运镜词表（幅度/速度/落点句式）、Seedance 2.x 公式、跨域 12 律+八型误导分类学（R-…-prompt-rules-official / R-…-mv-i2v-prompt-params）。
- 本件增量=官方规则之外的电影语言领域资产：电影级提示词语料与模板、镜头语言词表/术语本体、灯光词表、服装史实考据参考、调色资产（LUT/OCIO）、剪辑语法实证数据集。
- 不碰（他波）：agent 框架、SKILL.md 生态包装层（个别高星仓内含 prompt 语料本体，只取语料层注明）、剪辑工具、中文社群提示词库。
- 采集通道注记：GitHub MCP 仓搜索连败（疑配额）→ 依技能纪律切换 DDG 定位+仓页直读（github.com 服务端渲染可验星/许可/内容）；DDG 中途限流→ fetch_content 直读收口。

## ② 主表（资产｜仓或来源｜星｜许可｜活跃｜内容一句话｜席位映射）——已直读=A 级
| 资产 | 仓/来源 | 星 | 许可 | 活跃 | 内容一句话 | 席位 |
|---|---|---|---|---|---|---|
| OCIO-Config-ACES | AcademySoftwareFoundation | ⬜未截到 | New BSD（README 明文） | 95 commits·CI 在维 | ACES 官方 OCIO 配置生成器：Reference/CG/Studio 三档全色域变换=行业标色彩管理底座 | ②调色师 |
| cameraluts | cgardev | ⬜未截到 | 有 LICENSE 文件·类型待核 | 12 commits | Sony S-Log3→709/LC-709TypeA 数学精确 .cube LUT（技术转换+电影感 look，含技术白皮书文档） | ②调色师 |
| awesome-ai-video-prompts | geekjourneyx | 84 | MIT（仓页徽章） | 末推 2026-01-04·后静默 | 官方指南+提示词模板+电影语言章（Shot Types/运镜/构图规则/术语表/视觉元素描述），双语 | ⑥提示词工程+①摄影 |
| ai-shortfilm-prompts | jnMetaCode | 474 | ⬜ | 末更 2026-10-12·活跃 | 21 类型模板+5 阶段结构电影级视频提示词（Sora/Kling/Veo/Seedance，eval-tested，蒸馏自获奖 AI 短片导演） | ⑥提示词工程（skill 包装归他波） |
| ai-video-prompts | donghaozhang | ⬜DDG 定位未直读 | ⬜ | ⬜ | X/Twitter 实测语料（Seedance 2.0/Kling 3.0/Midjourney） | ⑥提示词工程 |
| dark-cinematic-movie-still-prompts | CSd0109 | 0 | ⬜ | 2026-09-25 | Nolan/Villeneuve/Fincher 风格 2.39:1 变形宽银幕暗调电影剧照提示词集 | ⑥+①摄影 |
| Sora-prompts gist | gupsammy（fork 自 ruvnet 原作） | 0⭐ | 无许可（gist 默认） | 2025-12-17 建 | 「Crafting Cinematic Sora Video Prompts」69,346 字符直读验真：镜头/运镜/灯光/色彩情绪章+300+ 提示词附录 | ⑥+①摄影 |
| Met Open Access | metmuseum/openaccess | ⬜未截到 | CC0（README+LICENSE 明文·unrestricted commercial use） | 321 commits·在维 | 470,000+ 藏品元数据 MetObjects.csv（含 Ancient Near Eastern Art=1900BC 参考面；图片另走官网 CC0 标识，不入 CSV） | ④美术考据+⑧服装 |

## ③ 内容增量评述
- 术语本体/词表：geekjourneyx 电影语言章=在档官方 20 运镜词表之外的景别/构图/术语表/视觉元素补面（双语）；gist 含灯光/色彩情绪词表。**灯光域在 GitHub 只到词表级**——结构化光路速查库（三点光/伦勃朗/年代光路图）未找到=⬜。
- 服装史实：Met CC0 覆盖 1900BC 美索不达米亚（爱在西元前）器物/浮雕服装参考面+跨年代服装史；**2001 台湾街头服装无开源数据集=⬜**（建议产线自建参考板）。
- 剪辑语法：预算内未验得实证数据集（MovieNet 站点 DNS 失败·M 级线索不采信）=⬜；MovieNet/ClipShots 列失败面待重访。
- 提示词语料：474⭐ 类型模板仓+gist 300+ 实录语料=提示词专家审闸（A-J 面）lint 对照集的「大水量」素材；X 语料仓（donghaozhang）合规三查未做。

## ④ 应用表（资产→席位→判定→理由）
| 资产→席位 | 判定 | 理由 |
|---|---|---|
| OCIO-Config-ACES→②调色师 | 适配 | New BSD 无商用障碍；但引入需 OCIO 色彩管理流程，产线当前 H3/Krea2 直出+装配调色，留待全片统一调色标准化阶段启用 |
| cameraluts→②调色师 | 仅借鉴 | LICENSE 原文类型未直读；技术面错配（我方素材非 S-Log）——仅 LC-709TypeA 式 filmic 曲线思路可参考 |
| awesome-ai-video-prompts→⑥提示词+①摄影 | 直接采用 | MIT 无碍；电影语言词表章喂专家审闸做 lint 词表底座；84⭐ 活跃弱但词表类资产不衰减 |
| ai-shortfilm-prompts→⑥提示词 | 适配（前置=许可核验） | 474⭐ 21 类型模板+5 阶段结构=类型片骨架库，匹配 41 曲类型分布；skill 包装归他波；许可 ⬜ 核验前先按仅借鉴执行 |
| ai-video-prompts→⑥提示词 | 仅借鉴 | DDG 定位未直读星/许可/活跃；X 实测语料价值高，三查通过才可升级 |
| dark-cinematic-movie-still-prompts→⑥+① | 仅借鉴 | 0⭐ 小仓；Nolan/Villeneuve/Fincher 风格锚+2.39:1 画幅写法可参考 |
| Sora-prompts gist→⑥+① | 仅借鉴 | 69,346 字符验真但 gist 无许可=不可复制入库，只可作 lint 对照参考 |
| Met Open Access→④美术+⑧服装 | 直接采用 | CC0 明文商用无障碍；1900BC 考据+服装史直接建参考索引；2001 台湾面自建补齐 |

## ⑤ TOP-3 采用建议 + 验证声明
1. **Met Open Access**（直接采用·CC0）：克隆 MetObjects.csv，按 Department「Ancient Near Eastern Art」+服饰类 Object Name 建 1900BC 服化道/器物年代索引——爱在西元前考据面的开源最优解、零许可风险。
2. **geekjourneyx/awesome-ai-video-prompts**（直接采用·MIT）：电影语言章双语入提示词专家审闸，作官方 20 运镜词表之外的词表 lint 扩展面（景别/构图/术语表）。
3. **jnMetaCode/ai-shortfilm-prompts**（适配·许可待核）：474⭐ 21 类型模板对照 41 曲分布选型，许可直读核验后作类型片提示词骨架库。备选第 4 席：OCIO-ACES 留色彩标准化阶段启用。
- 验证声明：读数 20/20 触顶（数据返回 11+失败 9：DDG 限流 4·curl 后端缺 1 批 4 调·MovieNet DNS 1）；成源 A=仓页/gist/主题页直读 6 件+在档 2 件，B=DDG 定位线索 3 件未升级，M=MovieNet/ClipShots/MiraData/Fashionpedia/Smithsonian 未采信；失败面：灯光结构化速查库⬜·2001 台湾服装数据⬜·剪辑语法实证数据集⬜·cameraluts 许可与 OCIO/Met 星数未截到⬜。
