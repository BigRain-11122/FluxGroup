# R-20261015-mv-expert-agent-sourcing — MV 全链专家 agent/skill 开源资产大搜罗（四波合流·防线二全验）
> 溯源：CEO 直令 2026-10-15「给我去找MV涉及的方方面面的那些专家agent，skill等比如说提示词专家，skill，灯光，服装，导演等，去github啊开源社区啊等等」·消费方=BigStream MV 产线（爱在西元前 V4 收口+41 曲重制线）十三席评审团
> 判据预注册：①开源社区有哪些 MV 全链专家资产（星/许可/活跃三查·当场直读）②对十三席的增量③采用判定（直接采用/适配/仅借鉴/判负）
> 波次底稿（verbatim）：waves/W1-mv-expert-multiagent-20261015.md（多智能体）·W2-…-skills…（Skill 生态）·W3-…-film-language…（电影语言资产）·W4-…-tools-community…（工具+中文社群）——本件=合成与验收层

## 一、防线二抽验（2026-10-15 17:0x·api.github.com 直读·8/8 成立）
- shuohao-skills ★4585·Apache-2.0·10-15 当日活 ✓｜screenwriting-skills ★1670·MIT·10-03 ✓｜allin1 ★860·MIT ✓｜seedance-2.0 ★7691·MIT ✓｜Met openaccess **CC0-1.0** ✓（商用无障碍明文）｜**jnMetaCode/ai-shortfilm-prompts=MIT 闭口（W3 ⬜→升级为可直接采用）**｜fal-ai-community/skills 顶层许可=空 确认（维持仅借鉴·LICENSE 补验前不升级）｜HKUDS/FilmAgent HTTP 404 证伪 ✓（W1「仓消亡」成立）
- 工具面留档：GitHub MCP 全端点「Could not parse tool response」在四波与本席一致复现（服务端故障）——全程走 api.github.com shell 直连（R-20261014 同法）。
- 三处待证闭口余留：DreamFactory「AI 电影」四路未寻得（疑闭源/易名·CEO 补线索）；即梦专项提示词仓未寻得（仅 GPL 反代=判负）；「AI 视频崩坏检测 agent」成熟开源件不存在（⬜）。

## 二、直接采用清单（TOP 定谳·全部过防线二）
| 资产 | 星·许可 | 席位 | 增量一句话 |
|---|---|---|---|
| eternityspring/shuohao-skills | 4585·Apache-2.0 | ③④⑧⑨ | 六工序 skill 包（大纲→角色/美术圣经→剧本→走位→分镜）+切 2-5s 硬门+一致性资产链/避崩白拍——短剧时序改造为 41 曲音乐驱动 |
| jtydhr88/screenwriting-skills | 1670·MIT | ③⑪（⑫部分） | 47 册工艺书蒸馏四层剧作法+心理编剧学+大师语料·正文即中文——补剧作文学底座；先装 5 件试点 |
| Emily2040/seedance-2.0 Skill OS | 7691·MIT | ⑥③① | 镜头表→提示词→续拍/重拍协议+「一镜一动作+镜尾锁线重申光/人/位」=i2v 跨镜连续性实弹经验·中文文档 |
| mir-aidj/all-in-one（allin1） | 860·MIT | ⑦ | 一件出 BPM/节拍/强拍/主副歌分段标签——41 曲「结构锚」与 whisper 词锚构成双轴剪辑锚 |
| metmuseum/openaccess | 1440·CC0-1.0 | ④⑧ | 470k 藏品 CSV 建 1900BC 美索不达米亚服化道/器物考据索引——爱在西元前考据面开源最优解 |
| geekjourneyx/awesome-ai-video-prompts | 84·MIT | ⑥① | 电影语言章（景别/运镜/构图/术语表·双语）=官方 20 运镜词表之外的 lint 词表扩展面 |
| jnMetaCode/ai-shortfilm-prompts | 474·MIT（防线二闭口） | ⑥ | 21 类型模板+5 阶段结构——41 曲类型片提示词骨架库 |
| cclank/lanshu-awesome-ai-video-kit | 421·MIT | ⑥⑬ | 中文 411 prompt/15 模型工具包 |
| echris6/motion-video-kit | 1109·MIT | ⑤⑦⑫ | builder≠judge 独立 critic 审片循环+critic-prompts 全文+可测质量条（frozen time/ebur128）+音频 back-timing 卡拍 |

## 三、适配采用（实装验证后切换）
whisperX（24553·BSD-2）+faster-whisper（25863·MIT）=词锚精度/速度升级路径（A/B 过 lyric_calibration 底座再切）；auto-editor（5522·Unlicense）素材粗剪；demucs（10382·MIT 已归档·代码成熟）人声分离反哺词锚；ffsubsync（7900·MIT）；VBench（1822·Apache-2.0）+t2v_metrics/VQAScore（603·Apache-2.0）=q88 抽帧板→半自动视频闸（阈值标定先行）；OCIO-Config-ACES（New BSD）留全片色彩标准化阶段；muse-video-skill（43·MIT 开发中·fork 快照）六角色剧组+Seedance 2.0 六段式 prompt 编译器。

## 四、仅借鉴（机制学习·文本不入库）与判负
仅借鉴：fal-ai-community/skills（许可空·shot-language/lighting-lens-color 工艺）；AmeerBashaK+RainLib（GPL 染疫）；HYV Prompt Rewrite Normal/Master 改写经验（社区自定义许可）；无许可提示词合集（Sora gist 69,346 字符·awesome-video-prompts·shuixian-prompts）；screenplay-review-checklist 37 判据对抗式诊断（NOASSERTION）；madmom（非标许可）。判负：stable-ts（archived）、jimeng-free-api-all（GPL-3.0+逆向=法务）、Toonflow/waoowaoo（Docker 平台=Windows 栈判负）、ArcReel/inkos/moyin（AGPL）、MovieAgent/Anim-Director/VideoDirectorGPT（无许可+停滞→只借 CoT 结构）、FilmAgent（仓消亡）。

## 五、空缺自建面（开源无件·产线自建清单）
⑬平台运营总监（3 秒钩/完播/横竖版无现成轮子）；②调色专职与②灯光光路结构化速查（GitHub 只到词表级）；⑧2001 台湾街头服装数据集（Met CC0 补古代面·现代面自建参考板）；③剪辑语法实证数据集（MovieNet DNS 失败·M 级不采信·列重访）；⑩专用崩坏检测 agent（以续拍锁线协议+VQAScore 双评分闸替代）；⬜ 成熟「文生 MV/歌词驱动管线」不存在（41 曲继续自研链·MoneyPrinterTurbo 编排思想可借鉴）。

## 六、试点安装顺序（PRODUCTION-SYSTEM-v2 §四接线）
P0（纯文档·即装）：screenwriting-skills 5 件试点+shuohao-skills 六工序+seedance-2.0 Skill OS+lanshu kit+awesome-ai-video-prompts 词表→.codely-cli/skills/（PROVENANCE 律：许可+来源+日期随件）。P1（本周末窗实装验证）：allin1 跑 3 曲结构锚样例+whisperX A/B 对齐精度。P2（标定后启用）：VQAScore 每批轻量对齐分→VBench 多维阈值标定。P3（考据基建）：Met CC0 克隆建 1900BC 索引+2001 台湾服装参考板自建。

## 七、验证声明（防线二口径）
四波落盘件重读确认稳定态（五节齐全·无占位残留）；本席 8 仓独立直读全数与波次主张一致（含两处升级与一处证伪确认）；波次自身验证声明见各件（读数 19-21/波·A 级成源为主·失败面透明留档：GitHub MCP 通道故障×4 波一致·DDG 限流·arXiv 空返回）；三处 ⬜ 待证余留列 §一；行数=node 实测 ≤60。
