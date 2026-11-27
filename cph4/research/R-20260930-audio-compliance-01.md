# R-20260930-audio-compliance-01 · 吸嘟嘟小游戏音频批合规依据（AI 生成 + 第三方下载两条路线）

- 调研员：B（集团后台调研）
- 日期：2026-09-30（星期三，Asia/Shanghai）
- 委托来源：CEO 令「注意要合规」「常见的音效可以去合规的网站或者github等地方去下载能商用的」
- 调研范围：中国区（大陆）法规 + 微信小游戏平台规范 + 常见音效/BGM 素材许可图谱 + AI 生成音频版权风险 + 第三方下载件证据链
- 标签约定：
  - 【确认】＝法规原文 / 官方平台文档直引（附 URL）
  - 【待证】＝有公开信源但非官方原文（附 URL）
  - 本文件不允许出现无信源断言。
- 撰写纪律：骨架先行，逐节完成即追加保存。

## 0. 摘要（先读这个）

1. **两条采购路线在中国区均可行**，但要各扛各的义务：AI 生成音频扛"**标识义务**"（《人工智能生成合成内容标识办法》2025-09-01 已生效），第三方下载音频扛"**证据链义务**"（微信要求"应要求提供权利证书或授权证明"）。
2. 《标识办法》第三条明文把**音频**列为生成合成内容五形态之一；显式标识=音频起始/末尾/中间加"语音提示或音频节奏提示"，隐式标识=文件元数据写入"内容属性+服务提供者名称或编码+内容编号"（《深度合成规定》第十六条同源）；配套强制国标 GB 45438-2025 同日施行。【确认】
3. 吸嘟嘟的角色是"**用户/内容使用者**"而非服务提供者：义务=发布时主动声明（第十条）+ 不得恶意删除/篡改/隐匿标识（第十条第二款、深度合成规定第十八条）+ 若向供应商索取"无提示音"版本则标识义务转到我方（第九条）。
4. 微信侧硬条款：小游戏特别规范 2.3"音乐应当符合国家版权管理的法律法规，不得侵犯他人著作权"；5.6 侵权音频"清空直至下架"；9.2 要求能提供**权利证书或授权证明**；实操存在"BGM 无合规商用授权"被驳回案例。
5. 许可图谱结论：🟢 白名单=CC0、CC-BY（需署名）、MIT（需留许可文本）、Pixabay、Mixkit Free、sonniss GDC bundle、Kenney、freesound 非 NC 件、带合规 LICENSE 的 GitHub 仓库；🟡 ZapSplat 免费档（须署名 ZapSplat）、freesound（逐件核对）；🔴 禁入=BBC 音效库（RemArc 仅个人/教育/研究）、一切 NC 件、爱给网免费区、无 LICENSE 的 GitHub 仓库、GPL 音频包、平台曲库翻录。
6. AI 音频版权现状：中国口径"体现人的智力投入+独创性→可为作品"（北互文生图案），美国口径"纯 AI 输出不受保护"（版权局 Part 2 报告）；训练数据风险行业已以"环球-Udio、华纳-Suno 授权和解"定调→**选已完成合规/签约的供应商**；声音权红线=不克隆真人声音（AI 声音第一案判赔 25 万）。
7. 落地总纲：**台账（一音频一行）+ 许可文本归档 + AI 生成档案与元数据标识保留 + 游戏内 AI 提示 + 提审自审报告如实声明**——详见第 6 节清单。

## 1. 《人工智能生成合成内容标识办法》对游戏音频的适用面

### 1.1 法规基本信息与"音频"的明文适用

- 发布主体：国家网信办、工业和信息化部、公安部、国家广播电视总局四部门联合印发，文号国信办通字〔2025〕2号，2025-03-07 成文、2025-03-14 公布，**自 2025-09-01 起施行**（现已生效 13 个月）。【确认】原文：https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm （同步镜像：https://www.gov.cn/zhengce/zhengceku/202503/content_7014286.htm ）
- **AI 生成音效/BGM 是否属于标识对象：属于。**《标识办法》第三条原文："人工智能生成合成内容是指利用人工智能技术生成、合成的文本、图片、**音频**、视频、虚拟场景等信息。"音频是五类被点名的生成合成内容形态之一。【确认】（同上 URL）
- 上位衔接：《互联网信息服务深度合成管理规定》（2023-01-10 施行）第十七条第一款第（二）项已把"**合成人声、仿声等语音生成**或者显著改变个人身份特征的编辑服务"列为必须显著标识的情形；第（五）项兜底"其他具有生成或者显著改变信息内容功能的服务"。【确认】原文：https://www.cac.gov.cn/2022-12/11/c_1672221949354811.htm

### 1.2 显式标识（用户可感知）的现行口径

《标识办法》第四条原文（对音频的直接要求）：

> "（二）在**音频的起始、末尾或者中间适当位置添加语音提示或者音频节奏提示等标识**，或者在交互场景界面中添加显著的提示标识；"
> "服务提供者提供生成合成内容下载、复制、导出等功能时，应当确保文件中含有满足要求的显式标识。"【确认】https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm

配套强制性国家标准 **GB 45438-2025《网络安全技术 人工智能生成合成内容标识方法》**：2025-02-28 发布、2025-09-01 实施，发布单位为国家市场监督管理总局、国家标准化管理委员会，主管部门为中央网信办，标准状态"现行"。【确认】官方标准记录：https://std.samr.gov.cn/search/stdPage?q=45438 （在线预览入口：https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=F32EA2A561F1886CD8D606513512D547 ）
网信办官网专家解读指出：该标准"通过强制性国家标准提供了清晰、统一、可操作的技术执行方案（如**显式标识的时长、尺寸，隐式标识的包含要素**等）"。【待证·网信办官网署名专家解读】https://www.cac.gov.cn/2025-09/05/c_1758792061408012.htm （标准全文量化条款本次未能直引，落地时以标准正文为准）

### 1.3 隐式标识（文件元数据）的现行口径

《标识办法》第五条原文：

> "服务提供者应当按照《互联网信息服务深度合成管理规定》第十六条的规定，**在生成合成内容的文件元数据中添加隐式标识**，隐式标识包含**生成合成内容属性信息、服务提供者名称或者编码、内容编号**等制作要素信息。鼓励服务提供者在生成合成内容中添加**数字水印**等形式的隐式标识。文件元数据是指按照特定编码格式嵌入到文件头部的描述性信息……"【确认】https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm

传播平台侧核验义务（第六条原文，四项措施）："核验文件元数据中是否含有隐式标识……用户声明为生成合成内容的……添加显著的提示标识……（四）提供必要的标识功能，并提醒用户主动声明发布内容中是否包含生成合成内容。有前款第一项至第三项情形的，应当在文件元数据中添加生成合成内容属性信息、**传播平台名称或者编码、内容编号**等传播要素信息。"【确认】https://www.gov.cn/zhengce/zhengceku/202503/content_7014286.htm

### 1.4 吸嘟嘟（游戏开发者）在此法规下的角色与义务判定

- 吸嘟嘟**不向玩家提供 AI 生成服务**（不开放玩家端生成功能），因此不是《标识办法》定义的"生成合成服务提供者"；我们是"**用户/内容使用者**"，把 AI 生成音频嵌入游戏并通过微信平台发布。【确认·依据第二条适用范围定义】
- 直接落在头上的三条硬约束：
  1. **主动声明义务**——第十条原文："用户使用网络信息内容传播服务发布生成合成内容的，应当主动声明并使用服务提供者提供的标识功能进行标识。"【确认】
  2. **不得恶意除标**——第十条第二款原文："任何组织和个人不得恶意删除、篡改、伪造、隐匿本办法规定的生成合成内容标识，不得为他人实施上述恶意行为提供工具或者服务……"【确认】；深度合成规定第十八条同旨："任何组织和个人不得采用技术手段删除、篡改、隐匿本规定第十六条和第十七条规定的深度合成标识。"【确认】https://www.cac.gov.cn/2022-12/11/c_1672221949354811.htm
  3. **可约定承接标识义务**——第九条原文：用户申请无显式标识的生成合成内容时，"服务提供者可以在通过用户协议明确用户的标识义务和使用责任后，提供不含显式标识的生成合成内容，并依法留存提供对象信息等相关日志不少于六个月"。→ 即：若用"去提示音"的商用档位，**标识义务转移给我们**，且生成服务方须留 6 个月日志。【确认】
- 技术含义：游戏音频若从 AI 服务下载后经转码/剪辑入包，**不得剥离服务方写入的元数据标识**；合规动作是"保留元数据 + 游戏内/说明页自行提示 + 平台提审时声明"。

### 1.5 游戏产品接入 AI 生成音频的申报/标识实践案例（现行）

- 微信：2025-08-31 "微信珊瑚安全"公众号发布《关于进一步规范人工智能生成合成内容标识的公告》——平台对 AI 生成合成内容实施显式与隐式双重标识；"用户发布的内容为AI生成合成的，发布时需主动进行声明"；"用户在发布或传播 AI 生成合成内容时，不得以任何方式删除、篡改、伪造或隐匿平台添加的 AI 标识"。【待证·光明网（官方媒体）转引原文】https://m.gmw.cn/2025-08/31/content_1304131434.htm
- 抖音（同日《关于升级AI内容标识功能的公告》：AI内容标识功能 + AI内容元数据标识读写功能，核验元数据隐式标识后给作品加"作品含 AI 生成内容"标识）、B站（投稿侧"创作声明"勾选）、快手（显式"AI生成"角标+元数据隐式标识）、DeepSeek（站内标识+发布《模型原理与训练方法说明》）。【待证·县政府网转载央视财经汇总】http://www.zjxj.gov.cn/art/2025/9/9/art_1562541_59032032.html
- 游戏行业：腾讯/网易/米哈游均布局 AI 音效合成（自研工具 + 第三方 SaaS 两类格局）。【待证·约投顾行业文】https://ag.yueniuzq.com/insight/ai-assisted-sound-effect-competition-landscape/ ；行业报道称 2025-09-01 标识办法实施"对所有AI生成的内容必须添加显性或隐性标识……对于腾讯、网易这样有自研引擎和中台的大厂来说，这只是加一行代码的事"。【待证·36氪】https://m.36kr.com/p/3630617524913412
- 音乐平台侧：腾讯音乐开放 AI 作品上传通道但不提供收益（控制商业化风险）；网易云音乐对 AI 作品引入"露脸清唱+工程文件"严格审核机制自证原创。【待证·搜狐/中国社会科学网】https://www.cssn.cn/skgz/bwyc/202511/t20251106_5929871.shtml
- 版号/备案侧：行业解读称 2026 年版号申报对"新兴技术（如AI生成内容）的审查"更精细化。【待证·游企帮】https://www.youqibang.com/policy/55
- **判定**：截至调研日，未检索到针对"游戏内嵌 AI 生成音频未标识"的公开执法案例；现行实践=**平台侧自动标识与核验 + 发布者主动声明 + 产品内自行提示**三层叠加。此为检索性结论（未见公开案例≠无风险，办法已生效且处罚通道为第十三条：由网信、电信、公安、广电部门依职责处理）。【确认·第十三条原文，同 1.1 URL】

## 2. 微信小游戏提审音频相关规范

### 2.1 平台内容审核对音频的直接条款（官方文档直引）

微信官方《微信小程序平台运营规范》（小游戏须一并遵守，文档页 = developers.weixin.qq.com/minigame/product/）中与音频直接相关的条款：

> **三、小游戏特别规范 2.3 游戏音乐及音效**
> "2.3.1 **音乐应当符合国家版权管理的法律法规，不得侵犯他人著作权，不得提供非法下载服务。**
> 2.3.2 音乐不宜含有过度的惊悚恐怖等不利于身心健康的歌词、画面、乐曲及音响效果。"【确认】https://developers.weixin.qq.com/minigame/product/

> **三、小游戏特别规范 2.8 内容保证**
> "2.8.1 你应当保证所开发、运营的小游戏之内容符合法律规定，其中的任何内容均不得侵犯他人的合法权益，**包括但不限于代码包内容、美术、音乐、特技特效等**；2.8.2 小游戏应该包含完整的游戏玩法和经过设计的UI、**音效**等必要元素，而不是简单的素材堆砌。"（2.8 处理规则："如不符合游戏质量要求，提审将被驳回"）【确认】同上

> **二、5.6 侵犯知识产权行为**
> "小程序开发者不得自行或与其他第三方共同利用腾讯的服务，侵犯其他主体的知识产权，**包括但不限于：文字、图片、视频、音频、软件等**。处理规则：一经发现将根据违规程度对该小程序侵权内容清空直至下架处理。"【确认】同上

> **二、6.1.8**："未经授权，擅自使用他人商标、**版权内容**等，以及其他侵犯他人合法知识产权的"列为违规（处理：封号）。【确认】同上

> **二、9.2 商标与商业外观**："使用他人商标、**版权内容**等涉及他人知识产权的内容需要在账号申请时如实说明，并**根据要求提供相关权利证书或授权证明**等。非权利人或未经授权的，不得使用他人享有合法知识产权的内容。"【确认】同上

**小结（平台审核对音频的要求）**：微信对音频的审核点 = ①版权合法性（不得侵权、不提供非法下载）②内容健康度（惊悚恐怖音响效果不宜过度）③产品完整度（音效是"必要元素"，纯堆砌素材会被驳回）④涉第三方版权素材时"应要求提供权利证书或授权证明"。审核侧存在"BGM 无商用授权被驳回"的实操案例（个人开发者复盘：小游戏上架审核被驳回，"驳回原因就是BGM无合规商用授权"）。【待证·知乎开发者复盘】https://zhuanlan.zhihu.com/p/2063241086479479061

### 2.2 音乐/音效的版权材料要求（著作权证明）

- IAA 小游戏资质审核官方文档："IAA 游戏进行备案时，遇以下情形需要提交《计算机软件著作权登记证书》或对应其他授权材料：1）游戏名称含有英文、或'软件'字样；2）涉及相关品牌、公众人物合作等"；材料需按模块上传，"著作权授权书上传至其他授权书"属错位上传、会被驳回。【确认】https://developers.weixin.qq.com/minigame/introduction/guide/zzsh-iaa.html
- 小游戏备案（IAA 前置审批环节）官方文档：需"确保清晰、完整、真实介绍你所备案的小游戏内容，包括但不限于场景、玩法、功能等信息；并上传对应截图"；平台初审 1-2 个工作日、主管部门 10-20 个工作日；常见驳回自查项含"前置所需的资质材料未提交或者未通过审核""小游戏备案不合规且多次驳回未更新"。【确认】https://developers.weixin.qq.com/minigame/introduction/guide/nrjs.html
- 官方文档未见"逐条提交音效授权文件"的固定表单，但运营规范 9.2/6.1.8 给了平台"应要求提供权利证书或授权证明"的抓手——即：**平时不查、投诉或抽查时必须能立即出示**。对音频批的操作含义：每条入包音频都要有可随取随交的授权证据（见第 5 节证据链）。【确认·9.2 条款 + 推断】

### 2.3 微信平台对 AIGC 素材的申报口径（现行）

- 平台总口径：微信（珊瑚安全）2025-08-31 公告——按《标识办法》对 AI 生成合成内容加显式+隐式标识；用户发布 AI 生成合成内容须主动声明；不得删除/篡改/伪造/隐匿 AI 标识；违者平台视情况处罚。【待证·光明网转引】https://m.gmw.cn/2025-08/31/content_1304131434.htm
- 若小程序/小游戏**本身向用户提供 AI 功能**（AI 问答、AI 绘图等）：需申请"深度合成"相应类目（仅企业主体）、提交算法备案材料，审核交叉验证备案信息。【待证·第三方实操文（微信开放社区有对应拒绝情形案例："服务内容涉及未开放类目【AI】"）】https://developers.weixin.qq.com/community/develop/doc/000c4c250844d02c2bd39007e6b000
- 吸嘟嘟情形（**只把 AI 音频作为素材嵌入，不提供生成功能**）：不触发深度合成类目/算法备案；现行义务 = 提审时按平台声明机制主动说明 + 产品内提示 + 不破坏文件标识。截至目前检索，微信小游戏提审后台未见公开的"AI 素材声明"专项字段，故采用"自审自查报告如实写明 + 备注栏声明"的稳妥做法。【待证·无公开字段为检索结论；自审报告模板参考】https://zhuanlan.zhihu.com/p/1938646526927828133
- 备案填写的游戏内容描述会进入出版主管部门审核，内容（含音频观感、健康度）与描述一致性是驳回点之一。【确认·备案"提交要求"条款，见 2.2 URL】

## 3. 可商用许可图谱（「下载能商用」依据）

### 3.1 一图速查：许可 × 商用 × 署名

| 许可 / 来源 | 商用 | 署名 | 关键附带条件 | 评级 | 标签 |
|---|---|---|---|---|---|
| CC0 1.0 | ✅ | 不要求 | 不得暗示作者背书 | 🟢 可直接用 | 【确认】 |
| CC-BY 4.0 | ✅ | **必须**（credit+许可链接+标明修改） | 不得暗示背书 | 🟢 用+署名 | 【确认】 |
| CC-BY-NC 4.0 | ❌ 明文禁止 | — | NonCommercial | 🔴 禁入 | 【确认】 |
| MIT | ✅（含 sell copies） | 需随副本保留版权+许可声明 | LICENSE 文本必须归档随附 | 🟢 用+留许可文本 | 【确认】 |
| Pixabay Content License | ✅（须融入原创作品） | 不强制（许可未设署名义务） | 禁原样独立转售/分发；可识别人物需 model release；商标专利不受许可覆盖 | 🟢 | 【确认/部分待证】 |
| Mixkit Free License（音效/音乐） | ✅ | 不要求 | 不得单独再分发；**逐件确认**适用的是 Free 还是 Restricted License | 🟢 | 【确认/部分待证】 |
| ZapSplat Standard License | ✅（personal/commercial/broadcast、全球、永久） | **必须** clear credit to "ZapSplat"（Gold 付费会员免除） | 音效不得构成产品主要价值、不得在项目外再分发；免费档仅 mp3 | 🟡 用+署名 | 【确认】 |
| sonniss #GameAudioGDC EULA v2.0 | ✅（无限项目、终身） | 不要求 | 不得把音效"作为音效"再分发/再许可/原样出售；**禁止用于 AI 训练** | 🟢 | 【确认】 |
| Kenney（补充白名单） | ✅ | 不要求（致谢可选） | CC0；勿用其 logo | 🟢 | 【确认】 |
| freesound.org（补充） | 按**单个声音**所标许可 | 按许可 | 每条声音单独标 CC0 / CC-BY / CC-BY-NC，NC 件禁入 | 🟡 逐件核对 | 【待证】 |
| BBC Sound Effects | ❌（默认许可不含商用） | — | RemArc 许可仅限个人/教育/研究 | 🔴 禁入 | 【确认/部分待证】 |
| 爱给网 | 仅"付费版权栏目"✅ | — | 免费下载件无授权承诺；付费件须取得可查验的《授权书》 | 🔴 免费区禁入；付费区黄灯 | 【确认·爱给网官方FAQ】 |

### 3.2 逐项条款直引与使用要点

**① CC0 1.0（公共领域贡献）**——最干净的可商用许可。
- 原文："The person who associated a work with this deed has dedicated the work to the public domain by waiving all of his or her rights to the work worldwide under copyright law... **You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.**" 注意事项原文："When using or citing the work, **you should not imply endorsement** by the author or the affirmer."【确认】https://creativecommons.org/publicdomain/zero/1.0/
- 使用要点：商用免署名；但仍建议在台账记录来源（自证清白用）。

**② CC-BY 4.0（署名许可）**——商用可用，署名是硬义务。
- 原文："Share — copy and redistribute the material in any medium or format **for any purpose, even commercially**. Adapt — remix, transform, and build upon the material for any purpose, even commercially." 义务原文："**Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.** You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use."【确认】https://creativecommons.org/licenses/by/4.0/
- 使用要点：游戏内"版权致谢/制作名单"页或官网署名页列出作者+许可链接+修改说明；台账记录署名位置。

**③ CC-BY-NC 4.0（非商业）**——**商业游戏禁用**。
- 原文："**NonCommercial — You may not use the material for commercial purposes.**"【确认】https://creativecommons.org/licenses/by-nc/4.0/
- 注意：吸嘟嘟是带广告变现（IAA）与/或内购的商业产品，任何 NC 件（含 freesound 上的 NC 上传件）一律不得入包。

**④ MIT License**——GitHub 仓库常见，商用友好，但许可证文本必须随附。
- 原文："Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, **and/or sell copies** of the Software..." 条件原文："**The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.**"【确认】https://opensource.org/licenses/MIT
- 使用要点：MIT 本为软件许可证，仓库将其适用于音效资产时同样有效；**LICENSE 全文必须拷入我方仓库归档**，副本/发布物（如官网素材页）附许可声明。

**⑤ Pixabay Content License**
- 商用原文："So long as you've created a unique, original creative work, **the Pixabay license does allow use for both non-commercial and commercial purposes.**"
- 限制原文："Under the Pixabay Content License, **you can't sell or distribute content (either in digital or physical form) on a standalone basis** (i.e., where no creative effort has been applied to the content and it remains substantially the same form as it exists on the Pixabay website)."
- 风险提示原文："It is best to contact the artist and inquire about a model release if a person is recognisable. Please note that the patent or trademark rights of any person are not affected by our license, so we encourage our users to always check whether they have all rights to use such content."
- AI 说明原文："AI content is welcome on Pixabay, but it must be **original, clearly labeled**, and free from copyrighted styles, trademarks, or depictions of real people. You must check the 'AI-generated' box when uploading..."【确认】https://pixabay.com/service/license-summary/
- 署名：许可摘要未设署名义务（无强制署名），第三方解读一致确认"不强制要求"。【待证·官方页面该句未能直引，多来源一致】https://tools.cmdragon.cn/zh/apps/pixabay-library/wiki/license-usage
- 使用要点：音效可商用、免署名；但 Pixabay 站内也**混有已标注的 AI 生成内容**——下载时把"是否AI生成"一并记录（影响我方AI申报口径）；涉及人声/可识别人物的素材不用。

**⑥ Mixkit Free License（Sound Effects Free License / Music Free License）**
- 官方原文："Download unlimited assets for free, **with no attribution or sign-up required**." / "Assets under the Mixkit Free License can be used in both **commercial and non-commercial projects**." / "On Mixkit, we have a specific license for each of our item types. **Be sure you are aware of which license applies to the item you have downloaded.**"【确认】https://mixkit.co/license/
- 限制：音效/音乐不得脱离项目独立再分发、不得构成产品主要价值（音效类站点的通用红线；具体条款页为动态渲染未能直引）。【待证·第三方评述】https://designers.ac/design-resources/mixkit-free-sound-effects 、https://www.creativevault.net/mixkit
- 使用要点：逐件确认适用的是 Free 还是 Restricted License；入包文件在台账标注许可类型。

**⑦ ZapSplat Standard License**
- 免费档权利原文："You may download and use our sound effects and music tracks in an unlimited number of **personal, commercial, and broadcast projects worldwide, in perpetuity**, on a non-exclusive basis. Free users can only access mp3 formats of our sound effects and music and are subject to download limits."
- 署名原文："**Attribution Required: You must provide clear credit to 'ZapSplat' wherever reasonably possible in your project** (e.g., in end credits, descriptions, acknowledgements, or documentation)."
- 限制原文："our sounds must not constitute the primary value of a product (for example a sound effects app) or be redistributed outside of your project"；项目转让条款原文（确认游戏可用）："Where the Licensed Audio has been incorporated into a completed project or production, **including but not limited to a video game**, film, application, software product... the rights granted under this Agreement shall continue with that specific completed project in the event the project is sold, assigned, transferred, licensed or distributed to another party, publisher, distributor or platform."【确认】https://www.zapsplat.com/license-type/standard-license/
- 使用要点：可用但**必须署名**（游戏内 credits/说明文档致谢 ZapSplat），或购买 Gold 免署名；免费档仅 mp3（音质需评估）；商用免费路线里它属于"黄灯"。

**⑧ sonniss GDC Game Audio Bundle（#GameAudioGDC EULA，现行为 2.0 版，2026-08-27 起）**
- 授予原文："the Licensor grants the Licensee, a **worldwide, non-exclusive, royalty-free license**"；"Licensee may use the licensed sound effects on an **unlimited number of projects for the entirety of their life time**"；"may use and modify the licensed sound effects for **personal and commercial projects without attribution** to the original creator."
- 限制原文："Licensee **may not distribute, publish, sub-license or otherwise supply the sound effects as sound effects** to any other person... This applies whether the sound effects are unmodified, modified or re-designed..."; "Licensee **may not sell any of the sound effects as they come.** (Although the sound effects **may be sold as incorporated into licensee project**.)"
- AI 训练禁令原文："the Licensee is **expressly prohibited from using any sound effects licensed under this Agreement for the purpose of training artificial intelligence technologies**."
- 担保原文："Sonniss LTD warrants that it has full authority to license and distribute all of the sound effects libraries under the terms of this agreement and that our products do not infringe on the rights of any third party."【确认】https://sonniss.com/gdc-bundle-license/ （历年 bundle 下载页：https://gdc.sonniss.com/ ，官方宣传口径："No attribution is required and you can use them on an unlimited number of projects for the rest of your lifetime"【确认】https://gdc.sonniss.com/ ）
- 使用要点：对游戏最优的免费商用音效源之一（游戏即"licensee project"）；**绝对禁止拿这些音效去训练/微调音频生成模型**——与我方"AI生成音频"流程严格隔离。

**⑨ Kenney（补充推荐，CC0）**
- 官方原文："Yes, all game assets on the asset pages are **public domain licensed (CC0)**. You're free to use them, even in commercial projects." / "**Attribution is not required**, but if you choose to give credit you can do so by mentioning 'Kenney'. Do not use our logo..."【确认】https://kenney.nl/support （Kenney 资产含音效包；其在 GitHub 的镜像仓库同样以 CC0 声明署名要求。）

**⑩ freesound.org（补充，黄灯）**
- 许可模式：站内每条声音由上传者单独选择 CC0 / CC Attribution / CC Attribution-Noncommercial 三类许可，下载前必须查看该声音页面标注的具体许可；NC 件对商业产品禁用。【待证·站点为动态应用未能直引条款；模式为公开常识且与第三方横评一致】https://freesound.org/help/faq/ 、https://blog.csdn.net/2501_94325940/article/details/163669501
- 使用要点：可用，但逐件核对+登记许可类型；只取 CC0/CC-BY 件；CC-BY 件照 ② 履行署名。

### 3.3 GitHub 路线判定规则（回应 CEO「github 等地方下载」）

- GitHub 官方文档原文："**You're under no obligation to choose a license. However, without a license, the default copyright laws apply, meaning that you retain all rights to your source code and no one may reproduce, distribute, or create derivative works from your work.**"【确认】https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- **判定规则（可直接执行）**：
  1. 无 LICENSE 文件的仓库 = 默认保留所有权利 = **一律不用**；
  2. 有 LICENSE 但许可仅声明覆盖"代码/软件"（如 MIT 仅提 Software），未明示覆盖音频资产 = **不用**（除非 README/资产目录另有针对素材的许可声明）；
  3. LICENSE 为 CC0 / MIT / Unlicense 且（README）明示覆盖音频资产 = 可用，**LICENSE 全文 + commit hash 存档**；
  4. GPL/CC-GPL 等强传染性许可的音频包 = 不用（分发闭源游戏与 GPL 条款冲突）。【待证·依据 GPL 条件条款】https://choosealicense.com/licenses/gpl-3.0/
  5. fork 的仓库看原仓库许可，不看 fork 者自述。

### 3.4 避雷清单（禁入/慎用，含 CEO 点名的源）

| # | 来源 | 结论 | 依据 |
|---|---|---|---|
| 1 | **BBC Sound Effects 库** | 🔴 禁入。首页直引："You can search over 30,000 BBC sound effects... **use them in your own personal/educational projects, or licence them for use**"——免费许可（RemArc）只覆盖个人/教育/研究用途，商业使用须另行购买授权（"For commercial use you can access and license the whole collection through a third party"）。【确认·首页直引】https://sound-effects.bbcrewind.co.uk/ ；【待证·RemArc 名称与商用限制】https://musictech.com/news/music/the-bbc-sound-effects-archive-over-33000-free-samples/ 、https://www.bbc.com/archiveservices/archive-access-for-non-commercial-use/ |
| 2 | **一切 CC-BY-NC / NC 素材**（含 freesound NC 件） | 🔴 禁入。"You may not use the material for commercial purposes."【确认】https://creativecommons.org/licenses/by-nc/4.0/ |
| 3 | **爱给网"免费下载区"** | 🔴 禁入。官方 FAQ 只承诺**付费**"版权配乐/版权音效栏目"的作品"由爱给网签约的音乐人或合作的版权代理机构提供...素材购买完毕后，提供专门的版权授权书，授权用户合法进行商用"，对免费下载素材**无任何授权承诺**；免费区素材版权链不明。【确认·爱给网FAQ直引】http://www.aigei.com/faq/doc/29.html —— 如必须用爱给网：只走付费版权栏目+索取可查验《授权书》（其FAQ称可通过授权代码在查询系统核验）。 |
| 4 | **无 LICENSE 的 GitHub 仓库 / 许可不覆盖素材的仓库** | 🔴 禁入。见 3.3 规则与 GitHub 官方文档。【确认】 |
| 5 | **GPL 等传染性许可的音频包** | 🔴 禁入。【待证】https://choosealicense.com/licenses/gpl-3.0/ |
| 6 | **流媒体/短视频平台曲库翻录**（B站、抖音、网易云等下载歌曲当 BGM） | 🔴 禁入。无授权链即落入微信运营规范 5.6"侵犯知识产权行为"（处理：清空直至下架）与 6.1.8（封号）。【确认·微信条款】https://developers.weixin.qq.com/minigame/product/ |
| 7 | **"仅供个人学习交流使用"类兜底条款的中文免费素材站**（办公资源/淘声网等同类） | 🔴 禁入。"个人学习交流"明确排除商用。同类中文站若拿不出逐件许可文本，一律按许可不明处理。【待证·爱企查对免费素材版权归属的解读】https://aiqicha.baidu.com/qifuknowledge/detail?id=10080705303 |
| 8 | **要求注册且附加额外限制的源** | 🟡 慎用判定法：注册墙本身不构成否决（freesound、ZapSplat 都要注册），否决线是**条款里的附加限制**——"禁止商业用途 / 禁止游戏或应用内使用 / 强制外链水印 / 禁止修改"任一命中即弃用；"要求署名"不属否决线（可履行），记入署名台账即可。【推断·依据上述各站条款综合】 |

### 3.5 署名页落地实践

- 需要署名的许可（CC-BY、ZapSplat 标准版、含声明的 CC-BY 类）统一进"游戏内版权致谢页/制作名单"或游戏官网说明文档；MIT 类许可把 LICENSE 文本随仓库归档即可。
- 致谢页样例字段：素材名 · 作者/来源站 · 许可名+版本 · 许可链接。这样可同时满足 CC-BY 的"credit + license link + 标明修改"三要素。【确认·依据 CC-BY 4.0 条款原文】

## 4. AI 生成音频的版权/风险现状

### 4.1 成品可版权性：中国认"人的智力投入"，美国认"人类作者身份"

- **中国（北互"AI文生图"第一案，(2023)京0491民初11279号，2023-11-27 宣判、12 月底生效）**：法院认为"该案中的人工智能生成图片**体现了人的智力投入，具备'独创性'要素，并且体现了人的个性化表达，应当被认定为作品，受著作权法保护**"，使用者李昀锴享有著作权。【确认·中国法院网/北京知识产权公共服务平台官方发布】https://www.chinacourt.cn/article/detail/2024/02/id/7796864.shtml 、https://www.beijingip.cn/jopm_ww/websiteArticle/detailArticle.do?id=401fe2c28cd87548018d1a4b6f7f00b6 ；评析：法院强调"AI模型不能成为作者"，但结果体现自然人个性化表达的可认定为作品。【待证·搜狐评析】https://www.sohu.com/a/975223898_121236277
- **美国（版权局《Copyright and AI》Part 2《可版权性》，2025-01-29）**：官方专页载明该报告"addresses the copyrightability of outputs created using generative AI"（2025-01-29 发布）；主流报道口径：**纯生成式 AI 输出因缺乏人类作者身份不受版权保护，人类使用 AI 工具且有创造性控制的部分可获保护**。【确认·报告存在与发布日】https://www.copyright.gov/ai/ ；【待证·商务部知识产权保护网译文口径】https://ipr.mofcom.gov.cn/article/gjxw/gbhj/bmz/mg/202502/1990307.html
- **Thaler 案**：哥伦比亚特区联邦上诉法院 2025-03-18 裁定 AI 生成的视觉作品无法受版权保护（"AI并非自然人，无法成为作品作者"）；2026-03 美国最高法院拒绝受理该案上诉，"人类作者身份是版权登记底线"的判断继续有效。【待证·台湾资策会解析/知产律师网/盛峰律所】https://stli.iii.org.tw/article-detail.aspx?no=64&tp=1&d=9327 、https://www.ciplawyer.cn/articles/158553.html 、https://www.cnlaw.org.cn/24038.html
- **对吸嘟嘟的操作含义**：① AI 生成音效/BGM 的可版权性=**视我方投入的独创性而定**（prompt 工程、多轮筛选、剪辑改编、混音设计越充分，越接近北互口径下的"作品"）；② 无法把 AI 音效当作能强力维权的排他资产（护城河 ≠ 版权）；③ 对外（发行/联运/素材库）声明权属时用"由我方制作并拥有全部使用权益"而非绝对化"著作权归我方"，除非确有充分创作记录佐证独创性。

### 4.2 训练数据风险：行业已用"诉讼→授权和解"定调

- **RIAA 代表三大唱片起诉 Suno/Udio（2024-06）**：指控两家 AI 音乐平台"大规模使用受版权保护的音乐训练 AI 模型"，每首侵权歌曲索赔上限 15 万美元。【待证·行业复盘】https://post.smzdm.com/p/awwxqrkg/
- **和解收官（2025）**：新华网报道——华纳音乐集团与 Suno 达成合作协议、撤销诉讼，"Suno 获得华纳旗下艺人的音乐和肖像授权，双方之间的版权诉讼随之撤销"；此前环球音乐已与 Udio 和解。【确认·新华网】https://www.news.cn/tech/20251126/1aebe71159524b32a85f6b52395f2505/c.html 【待证·IT之家】https://www.ithome.com/0/900/245.htm
- **主流认知结论**：用 AI 音乐工具的风险主要沿"训练数据是否获授权"传导——选择**已与版权方签约/已完成合规**的服务商，风险由供应商吸收；用未授权训练的自部署模型/来路不明开源音频模型，训练数据风险自担。
- **中国法下供应商义务（选型依据）**：《生成式人工智能服务管理暂行办法》（2023-08-15 施行）第七条原文——提供者应当依法开展训练数据处理活动："（一）使用具有合法来源的数据和基础模型；（二）**涉及知识产权的，不得侵害他人依法享有的知识产权**；（三）涉及个人信息的，应当取得个人同意..."；第十二条原文："提供者应当按照《互联网信息服务深度合成管理规定》对图片、视频等生成内容进行标识。"【确认】https://www.gov.cn/zhengce/zhengceku/202307/content_6891752.htm
- **输出相似度风险**：AI 生成 BGM 仍可能与既有歌曲实质性相似（Suno/Udio 诉讼正是围绕训练曲库）→ 落地动作：每条 AI 音频入包前人工听审 + 与已知曲目比对抽查，记录听审结论。

### 4.3 声音权（人格权）红线：AI 声音第一案

- **全国首例 AI 生成声音人格权侵权案（殷某某诉北京某智能科技公司等，北京互联网法院，案号 (2023)京0491民初12142号，2024-04-23 一审宣判）**。法院认定原文要点：
  - "明确认定**在具备可识别性的前提下，自然人声音权益的保护范围可及于AI生成声音**。AI生成声音可识别性的认定应综合考虑行为人使用情况，并以**相关领域普通听众能否识别**作为判断标准。"
  - "该AI声音与原告的音色、语调、发音风格等具有高度一致性...能够将该声音联系到原告本人...因此，原告声音权益及于涉案AI声音。"
  - 关键认定："被告二对录音制品享有著作权等权利，但**不包括授权他人对原告声音进行AI化使用的权利**...在未经原告本人知情同意的情况下，授权...AI化使用原告声音的行为无合法权利来源。"
  - 判决：被告一、三赔礼道歉，被告二、三**赔偿损失共计 25 万元**。【确认·北京政法网（北京市委政法委官网）原文】https://www.bj148.org/yck/zzdt/202405/t20240510_1664690.html （案号出处【待证】https://www.marks-clerk.com/zh-hans/%E8%A7%82%E7%82%B9/... ）
- **反例（边界参考）**：另有法院认定 AI 声音**不**侵犯人格权的案例（因声音不具备可识别性）——"可识别性"是胜负手。【待证·涉外律所解析】（同上 marks-clerk URL）
- **对吸嘟嘟的红线**：① 不用任何 AI 工具克隆/仿制真实自然人声音（配音师、明星、主播）；② prompt 白名单化——禁写具体人名/在世歌手/组合名与"某某风格"表述；③ 如未来用 AI 配音，只用平台提供的授权声音库并留存其授权说明；④ 本批若纯音效/BGM（无人声克隆），该风险项主要为提示性约束。

### 4.4 国内游戏公司使用 AI 生成 BGM/音效的行业做法与判例现状

- **格局**：腾讯、网易、米哈游均已布局 AI 音效合成，呈"游戏大厂自研 AI 工具"与"第三方音效合成 SaaS"两类玩家并行。【待证·约投顾行业洞察】https://ag.yueniuzq.com/insight/ai-assisted-sound-effect-competition-landscape/
- **标识落地**：行业报道称 2025-09-01《标识办法》实施后"所有AI生成的内容必须添加显性或隐性标识"，对有大厂"只是加一行代码的事"——即游戏侧在**生成管线/资产管理系统中自动写入标识**。【待证·36氪】https://m.36kr.com/p/3630617524913412
- **音乐平台侧做法**（反映行业对 AI 音频商用的谨慎度）：腾讯音乐开放 AI 作品上传通道**但不提供收益**（控制商业化风险）；网易云音乐对 AI 作品引入"露脸清唱+工程文件"审核机制自证原创。【待证·搜狐】https://www.sohu.com/a/970238163_122066678 ；学术侧建议：平台部署"AI+区块链"双轨监测，**要求创作者留存完整创作记录以自证贡献程度**。【待证·中国社会科学网】https://www.cssn.cn/skgz/bwyc/202511/t20251106_5929871.shtml
- **判例现状**（截至 2026-09-30 检索）：与"游戏内嵌 AI 生成音频"直接相关的公开判例/处罚案例**未检索到**；最接近的两条判例线为 4.1 文生图案（可版权性）与 4.3 AI 声音人格权案（声音红线）。版号/备案侧：行业解读称 2026 年版号申报对"AI生成内容"的审查更精细化，但未见要求逐条申报音频来源的公开官方文件。【待证·游企帮】https://www.youqibang.com/policy/55
- **总体风险评级（B 组判断，供决策）**：AI 音频路线的合规重心= **标识义务（第 1 节）+ 供应商选型与记录（第 4.2/4.3）+ 权属证据留存（第 5 节）**；"可版权性弱"是商业属性问题而非合规障碍，不构成禁用理由。

## 5. 第三方下载件入包的证据链要求

### 5.1 为什么必须留证据链

- 微信官方运营规范 9.2："使用他人商标、**版权内容**等涉及他人知识产权的内容需要在账号申请时如实说明，并**根据要求提供相关权利证书或授权证明**等。"——平台是"应要求出示"模式：平时不收、查时必须有。【确认】https://developers.weixin.qq.com/minigame/product/
- 第三方素材的许可是**合同性文件**：各站条款随时可能改版（如 sonniss EULA 已迭代到 2.0、2026-08-27 生效），所以证据要固定"**下载当日适用版本**"。【确认·sonniss "WHICH VERSION APPLIES" 条款】https://sonniss.com/gdc-bundle-license/
- 行业共识："完整的授权凭证，是创作者应对版权争议的核心依据。"【待证·第三方横评】https://blog.csdn.net/2501_94325940/article/details/163669501
- AI 件另有"创作记录=独创性自证"价值：留存 prompt/参数/筛选过程，一旦需要主张作品属性可自证智力投入。【待证·中国社科网"留存完整创作记录自证贡献"建议】https://www.cssn.cn/skgz/bwyc/202511/t20251106_5929871.shtml

### 5.2 标准做法：四件套

1. **台账（audio_assets_ledger）**——每个入包音频一行，字段建议（第 5.3 节模板）。
2. **许可文本归档**——下载当时的许可条款原文：
   - 网站类（Pixabay/Mixkit/ZapSplat/freesound）：把该站许可页**另存为 PDF/HTML 快照**（含抓取日期）；
   - 打包下载类（sonniss GDC bundle、Kenney）：**原样保留压缩包内的 LICENSE 文件**，与音效文件同目录归档；
   - GitHub：LICENSE 全文 + **commit hash** + 仓库 URL 一并记录；
   - MIT/CC-BY 件：许可文本副本放入我方仓库 `Assets/AudioThirdParty/LICENSES/`（随代码走版本管理）。
3. **来源记录**——素材详情页 URL（不是首页）、作者名、下载日期；许可证版本号。
4. **署名义务闭环**——需署名的件登记"署名位置"（credits 页行号/官网致谢文档链接），验收时能定位到。

AI 生成件附加三件：生成服务名+模型版本、生成日期与 prompt（含参数/种子）、**入包前确认文件元数据标识未被剥离**（对照《标识办法》第五条与第十条"不得恶意删除、篡改、伪造、隐匿标识"）。【确认·条款见第 1 节】

### 5.3 台账模板（可直接建表）

| 字段 | 说明/示例 |
|---|---|
| 文件名 | `sfx_suck_pop_01.mp3` |
| 用途 | 吸嘟嘟：吞噬触发音效 |
| 获取路线 | 下载 / AI 生成 / 自制 |
| 来源 URL | 素材详情页完整链接 |
| 来源站/作者 | sonniss GDC 2025 Bundle（vendor: XXX） |
| 许可名称+版本 | #GameAudioGDC EULA v2.0（2026-08-27 生效版） |
| 商用判定 | ✅（引用台账内许可关键句） |
| 署名义务 | 无 / 需署名→署名位置：credits 页第 3 行 |
| 许可文本存档路径 | `Assets/AudioThirdParty/LICENSES/sonniss_gdc2025_LICENSE.pdf` |
| 下载/生成日期 | 2026-09-30 |
| AI 服务与模型版本 | （AI 件）Suno v4.5 / 自研管线 vX |
| AI 元数据标识确认 | 是（metadata 含生成属性信息）/ 否（自制件不适用） |
| 听审/比对结论 | 无相似争议 / 与《XXX》副歌片段疑似相似→弃用 |
| 审核人/复核人 | 两签 |

### 5.4 入包前五步检查（流程）

1. 查许可 → 命中 3.4 避雷清单任何一条 → 弃用换源；
2. 快照/归档许可文本；
3. 台账登记（含署名义务）；
4. AI 件核验元数据标识 + 听审；
5. 提审材料同步：自审报告写明素材来源类型分布（AI 生成 N 条/第三方下载 N 条/自制 N 条）与授权依据，遇平台质询可 5 分钟内出示台账。

## 6. 对吸嘟嘟的落地清单（动作 + 验收判据，可直接执行）

### A. AI 生成音频路线

| # | 动作 | 验收判据 |
|---|---|---|
| A1 | **供应商白名单选型**：只用已完成备案且训练数据合规有公开承诺的 AI 音频服务（核验其备案信息与服务协议商用条款；对照《生成式AI暂行办法》第七条供应商义务） | 台账"AI 服务与模型版本"字段 100% 填写；每个供应商附备案编号/合规声明 URL；无"来路不明开源模型"入流程 |
| A2 | **全量生成档案**：每条 AI 音频记录 prompt、参数/种子、生成日期、模型版本 | 抽查 3 条 AI 音频，均可凭台账记录追溯生成过程（prompt 与参数齐全） |
| A3 | **保留元数据标识**：入包转码/剪辑流程禁止剥离服务方写入的文件元数据标识（《标识办法》第五条、第十条第二款） | 抽查 3 条入包文件：元数据含生成合成属性信息；转码脚本/管线文档中无"清除 metadata"步骤；确需转码的留"标识未清除"检查记录 |
| A4 | **游戏内 AI 内容提示**：在设置/关于/版权信息页加固定文案"本产品部分音效与音乐由人工智能生成" | 提审包截图中可见该提示；文案与实际素材构成一致（有 AI 件必有提示） |
| A5 | **提审如实声明**：在小游戏备案内容描述、提审自审报告与备注中写明"含 AI 生成音效/BGM N 条，已按《标识办法》保留标识" | 自审报告含专门段落；备注栏声明文字可截图留档；备案描述与实际内容一致 |
| A6 | **声音权红线**：prompt 白名单审查——禁止出现真实人名、在世歌手/组合名、"XX风格"表述；不用任何克隆/仿声功能（AI 声音第一案口径） | 台账 prompt 字段抽检零命中真人名；人声类素材 0 条来自克隆；语音功能（如有）仅用供应商授权声音库并留存授权说明 |
| A7 | **相似度听审**：每条 AI 音频入包前人工听审并与已知曲目抽查比对，记录结论 | 台账"听审结论"字段 100% 填写；"疑似相似"件一律弃用换源；听审记录有审核人签字 |

### B. 第三方下载音频路线

| # | 动作 | 验收判据 |
|---|---|---|
| B1 | **只从白名单源采购**（第 3 节🟢：CC0 / CC-BY / MIT / Pixabay / Mixkit Free / sonniss GDC / Kenney / freesound 非 NC 件 / 带 LICENSE 且覆盖资产的 GitHub 仓库） | 台账中每条下载件的"许可名称+版本"∈白名单；来源 URL 可打开且与登记一致 |
| B2 | **执行避雷清单**（第 3.4 节：BBC、NC、爱给网免费区、无 LICENSE 仓库、GPL 包、平台曲库翻录、附加限制源） | 采购渠道清单与台账交叉核对，零命中避雷项；发现即换源 |
| B3 | **LICENSE 归档**：每个来源的许可文本存入 `Assets/AudioThirdParty/LICENSES/`（快照含抓取日期；打包类保留包内 LICENSE；GitHub 留 LICENSE+commit hash） | LICENSES 目录文件数 = 使用来源数；每个文件可读、含版本/日期；git 有提交记录 |
| B4 | **署名义务闭环**：CC-BY / ZapSplat 免费档等需署名件，进游戏内版权致谢页（素材名+作者+许可链接+是否修改） | 每条需署名件在台账"署名位置"字段定位到致谢页具体行；提审包截图可见致谢页 |
| B5 | **sonniss 等包的附加禁令**：第三方音效严禁用于训练/微调任何音频 AI 模型 | 若存在自训练管线：出具"第三方音频与训练集物理隔离"说明；无管线则记"不适用" |
| B6 | **Pixabay/Mixkit 逐件确认**：下载时记录该件适用的具体许可类型（Free/Restricted、是否标注 AI 生成） | 台账"备注"含许可类型标记；Restricted 件不入包 |

### C. 通用（两路线共通）

| # | 动作 | 验收判据 |
|---|---|---|
| C1 | **建立台账**（第 5.3 节模板，一音频一行，双人签审） | 台账文件在项目库内且随版本管理；行数 ≥ 入包音频数；无空字段 |
| C2 | **提审材料同步**：自审报告写明素材构成（AI 生成 N 条/第三方下载 N 条/自制 N 条）+授权依据汇总页 | 材料齐备；遇平台质询 5 分钟内可出示台账与许可文本 |
| C3 | **驳回应急通道**：若审核驳回"BGM/音效无授权"→凭台账即时举证，或 24 小时内换源（白名单库）重提 | 完成一次演练（模拟驳回→出示台账）；换源候选清单 ≥ 每类 3 条备选 |
| C4 | **新音频进包流程固化**：任何新增音频必须先过 5.4 节五步检查，未过检查不进包 | PR/入库检查单含五步项；抽查最近 5 次新增均有记录 |

### 风险提示（B 组判断）

- 最大现实风险不是"AI 不能用"，而是：① 用了 NC/无授权素材被投诉 → 微信清空素材直至下架（5.6 条款）；② AI 音频未声明/被剥离标识 → 违反已生效的《标识办法》（处罚通道：网信/电信/公安/广电四部门）；③ 爱给网免费区/BBC 这类"看起来免费"的源混入采购单。以上均已通过本清单 A1–C4 封堵。

## 7. 参考信源汇总

**法规与国标（官方直引）**
- 《人工智能生成合成内容标识办法》全文（网信办）：https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm
- 同文（中国政府网镜像）：https://www.gov.cn/zhengce/zhengceku/202503/content_7014286.htm
- 《互联网信息服务深度合成管理规定》全文（网信办）：https://www.cac.gov.cn/2022-12/11/c_1672221949354811.htm
- 《生成式人工智能服务管理暂行办法》全文（中国政府网）：https://www.gov.cn/zhengce/zhengceku/202307/content_6891752.htm
- GB 45438-2025 官方标准记录（全国标准信息公共服务平台）：https://std.samr.gov.cn/search/stdPage?q=45438 ；在线预览：https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=F32EA2A561F1886CD8D606513512D547
- 网信办专家解读（标识新规）：https://www.cac.gov.cn/2025-09/05/c_1758792061408012.htm

**微信官方平台文档（直引）**
- 微信小程序平台运营规范（含小游戏特别规范 2.3/2.8/5.6/6.1.8/9.2）：https://developers.weixin.qq.com/minigame/product/
- 小游戏资质审核(IAA)：https://developers.weixin.qq.com/minigame/introduction/guide/zzsh-iaa.html
- 小游戏备案：https://developers.weixin.qq.com/minigame/introduction/guide/nrjs.html
- 微信珊瑚安全《关于进一步规范人工智能生成合成内容标识的公告》（光明网转载）：https://m.gmw.cn/2025-08/31/content_1304131434.htm
- 平台公告汇总（县政府网转载央视财经）：http://www.zjxj.gov.cn/art/2025/9/9/art_1562541_59032032.html

**许可文本（官方/权利人直引）**
- CC0 1.0：https://creativecommons.org/publicdomain/zero/1.0/
- CC BY 4.0：https://creativecommons.org/licenses/by/4.0/
- CC BY-NC 4.0：https://creativecommons.org/licenses/by-nc/4.0/
- MIT：https://opensource.org/licenses/MIT
- Pixabay Content License：https://pixabay.com/service/license-summary/
- Mixkit License：https://mixkit.co/license/
- ZapSplat Standard License：https://www.zapsplat.com/license-type/standard-license/
- sonniss #GameAudioGDC EULA：https://sonniss.com/gdc-bundle-license/ ；历年包：https://gdc.sonniss.com/
- Kenney Support（CC0 声明）：https://kenney.nl/support
- BBC Sound Effects：https://sound-effects.bbcrewind.co.uk/ ；licensing：https://sound-effects.bbcrewind.co.uk/licensing
- 爱给网版权FAQ：http://www.aigei.com/faq/doc/29.html
- GitHub Licensing 官方文档：https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- GPL-3.0 条款参考：https://choosealicense.com/licenses/gpl-3.0/

**判例与行业（信源如文内标注，关键者）**
- AI 文生图案（中国法院网）：https://www.chinacourt.cn/article/detail/2024/02/id_7796864.shtml ；北京IP平台说法：https://www.beijingip.cn/jopm_ww/websiteArticle/detailArticle.do?id=401fe2c28cd87548018d1a4b6f7f00b6
- AI 声音人格权第一案（北京政法网）：https://www.bj148.org/yck/zzdt/202405/t20240510_1664690.html
- 华纳×Suno 和解（新华网）：https://www.news.cn/tech/20251126/1aebe71159524b32a85f6b52395f2505/c.html
- USCO Copyright and AI（官方）：https://www.copyright.gov/ai/ ；商务部译文口径：https://ipr.mofcom.gov.cn/article/gjxw/gbhj/bmz/mg/202502/1990307.html
- 行业格局/标识落地/音乐平台做法/版号新政（均为【待证】信源，URL 见第 1、4 节正文）

---

**局限声明**：① GB 45438-2025 的量化条款（显式标识时长/尺寸、元数据字段格式）未能直引标准正文（PDF 镜像不可解析、官方在线预览需交互），落地执行以标准正式文本为准；② 微信小游戏提审后台的 AIGC 声明字段为"检索未见"性结论，实际以后台当期界面为准；③ 各许可条款随时可改版，采购时以**下载当日**版本为准并存档快照。

状态：完成
