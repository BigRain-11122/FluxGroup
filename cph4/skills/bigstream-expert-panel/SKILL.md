---
name: bigstream-expert-panel
description: BigStream 内容产线专家评审团机制（十三席两波评审+四闸流水+经验台账回灌）。进行 BigStream/MV/短视频/图像的创意生产、专家评审、关键帧生成、图生视频提示词撰写、剪辑装配、发布合规检查时使用。
---

# BigStream 专家评审团产线技能

## 何时用
一切 BigStream 内容生产任务（MV/短视频/海报/角色/场景）：从立意到成片的任何一段。当前实施面=mv0001《爱在西元前》产线。

## 铁序（CEO 令链定谳·违反即返工）
1. **先磨后产**：立意逐句级分析过闸→剧本过盲评→才放生产；禁跳过创作核心直接拉分镜/出图。
2. **五闸流水**：提示词闸（每包 prompt lint 机核→**提示词专家审**[PROMPT-EXPERT-GATE-v1 十面检查单·CEO 令 O-20261015「每次提示词都要过1遍提示词专家审才能开始生产」·零豁免·无 verdict 派单=拒收]→导演席签发才烧）→设计闸（正典包过十三席）→关键帧闸（帧级六检 QC·<8.5 换种子重摇）→视频闸（逐镜画质/运镜执行/AI 崩坏）→成片闸（盲评 ≥9 全席）→**CERTIFIED 才呈 CEO**（CEO 只看认证终件+大白话评审团结论）。
3. **运镜=i2v 提示词内调度**（Motion+Amplitude+Speed 三维）；禁后期缩放/移动冒充运镜。
4. **音轨禁令**：一切成片=画面+歌（原曲/后期配乐）；AI 原生音轨一律剥离（-an）。
5. **提示词按 spec**：词表 lint 三名单（零否定/零模糊/零概念注入）+官方组装顺序+ID 块逐字复用律+**V3 四型病灶禁律**（材质色×调色双真值源消解/起帧对抗动作禁写/媒介锚显式前置/器物形制锚到部件级）。

## 正典五件（git 权威·本 skill 只是指针）
1. 评审制：`cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/EXPERT-PANEL-PROTOCOL.md`（十三席两波编制+五闸+认证规则+模型/skill 分工+§六经验回灌律）
2. **提示词专家审闸**：`cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md`（CEO 令 O-20261015·每包必过·十面检查单+席位 brief 模板）
3. 经验台账：`cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/EXPERIENCE-LEDGER-v1.md`（判例册 18+技巧册 13——**动手前必查，同病不二犯**）
4. 提示词规范：同目录 `PROMPT-SPEC.md` + `prompt_lexicon.py`（词表/组装器/lint 三名单）
5. 项目正典：`30s-reel-v1/30s-立意案-v4-定稿.md`（当前案权威）+`PUBLISH-CHECKLIST.md`（发布合规）

## 经验回灌纪律（CEO 令 2026-10-10 13:2x）
- 每闸收口→席位回报新判例→台账追加行（病→例→闸→日）；**判例必须落闸**（检查单/lint/QC 检项/脚本断言）——躺着=没修
- 复发=闸失效→当窗升格（能机核不靠人记）
- 席位评审派单必含：只读指定文件数+终稿字数上限+禁复述文件内容（评审代理超限中断两轮实锚）
- 新提示词技巧须正反例齐才入台账；复用锚词优先回灌 prompt_lexicon

## 机队分工速记
bm-c（16G）=帧+int8 768P i2v 主力·bm-b（8G）=480P animatic 备援·bm-a=低清试验+CPU 剪辑+金融回测（CEO 授权面）；派单=正典包+orders 行+fleet-dispatch poke。
