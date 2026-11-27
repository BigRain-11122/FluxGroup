# R-20261015-prompt-rules-official — 提示词工程官方规则全典（CEO 直令·本窗·终稿）
> 溯源：CEO 原话 2026-10-15「好好去调研，提示词的各种技巧和规则，你现在写的提示词，还是容易误导AI。好好看官方文档。摸清规则，每次提示词都要过1遍提示词专家审才能开始生产。」
> 消费方：BigStream 产线（PROMPT-SPEC v1.3+提示词专家审闸）；关联件（零重复）：R-20261015-mv-i2v-prompt-params（模型×参数·他窗）/R-20261015-mv-director-craft（导演工艺·他窗）。
> 验证声明：四路波全归笼（waves/2026-10-15-prompt-rules/：llm-official 20 读·video-official 19 读 123 行超 60 帽已注记·image-official 19 读·failure-mechanisms 11 读）；A 级官方/arxiv 直读为主、M 级 0 采信；防线二独立抽验 2 处承重主张直读通过（BFL docs.bfl.ml 原文+arxiv 2406.02965 摘要原文）；失败面=各波文件尾节如实记录（Krea 负面字段官方沉默/多属性冲突取舍机制无官方明文=⚠️经验律/图像域否定反效果机制无官方直接解释=推测级）。

## 一、通用规则律（跨域 12 律·全 A 级源·细则见波文件）
1. **正向律**：否定词连同被否定概念整词删除（Qwen 改写器第 8 条+BFL「no negative prompt field」官方替换表+Anthropic「tell what to do instead」）；机制背书=arxiv 2406.02965（否定=正向先渲染后潜空间对消=迟效中和·概念仍被注入）。
2. **媒介锚前置律**：媒介显式声明且前置（Krea expansion 第 9 条「Preserve User Medium…honor it. Do not pivot」+BFL 模板第一句定调）。
3. **属性成组绑定律**：颜色/材质/动作写在所属主体旁·禁全局浮动修饰（Krea「Group subjects with their own attributes」+SynGen arxiv 2306.08877 属性错绑实证）。
4. **色板锚定律**：调色板必须绑定具体对象/区域（BFL 示范 `palette of deep purple and black shadows`）。
5. **词序前置律**：「put first whatever matters most」+正向替代放句首不放 trailing clause（BFL 原文直验）；词义+词序即全部消费面、关系追踪极弱 0.07/1（arxiv 2410.10291/2606.03715）→**关系显式命名·禁靠语序**。
6. **可见细节律**：写可区分的可见特征·不写名称级描述（BFL「Describe visible details that distinguish your subject」）；防过载=不发明输入不支持的细节（Krea 第 5 条）。
7. **密度双向律**：too little→模型即兴；too much→动作被省略或变 frantic（Seedance 2.5 官方）；长杂多场景提示词=官方认证反模式（seedance.tv/火山双源）。
8. **能力边界律**：一镜一运镜；高难运镜不获支持（Veo 官方）；缓慢轻柔细微动作优先（Seedance）；多人 ≤2-4 人（Sora/Seedance）；文字特效不可靠→改参考视频定义（火山）。
9. **起帧主导律**：i2v 起帧=特权条件（ConsistI2V/HPSD「帧1=privileged condition」/I2VEdit 三论文+Seedance 2.5「The model must adapt to that asset」+H3「fully referenced」+Sora「image as an anchor」五源）——内容决策放首帧，提示词只写运动/运镜/发展。
10. **清晰黄金法则**：给无背景同事看，他困惑模型就困惑（Anthropic）；正面指令优于否定（LLM 域三源）。
11. **评测先行律**：先立成功标准再调提示词；draft→review→refine 链；**改生产提示词前先加测试**（OpenAI）；钉模型快照。
12. **冲突显式排序律**：多条件冲突须显式排优先级（Gemini 官方代理模板）——官方无自动取舍，双真值源=掷骰子（⚠️我方经验律补位）。

## 二、误导机制分类学（八型·每型=机制→规避）
①否定注入（NEG 名单拦）②属性渗漏/错绑（成组绑定）③双真值源冲突（显式消解+词序前置）④句尾弱位（重要词前置）⑤名称级补全（可见细节+部件级形制锚）⑥起帧对抗（要改先改帧）⑦媒介/风格漂移（媒介锚显式+换模型重校）⑧能力过载（密度律+边界律）。

## 三、我方四病历归因（全部官方口径闭合）
SIL1 色相渗漏=③+④+色板未锚定对象；tiki 形制=⑤；SIL4 媒介漂移=⑦；SING3b 起帧对抗=⑥；「no K-pop」=①（Qwen 第 8 条直接预言）；「strikes with mallet」=⑥+官方 result-or-reaction 结构反面；「dimming one by one」=⑧官方特效条款直接命中。

## 四、专家审闸（本件核心交付·已建成）
`prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md`：每包提示词 lint 机核→提示词专家审（十面检查单 A-J·逐镜 verdict+改写稿）→导演席签发才烧；verdict 随包上链·无 verdict 派单=烧制侧拒收；复发=闸失效当窗升格。

## 五、结论应用表（research-protocol 强制·落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 六律 V3 病灶（色相渗漏/媒介锚/形制锚/景深显式/起帧主导/正向替代句位） | ②法修改：PROMPT-SPEC v1.3 §九（已落） | 已闭环 |
| 提示词专家审闸（CEO 令核心） | ②法新建：PROMPT-EXPERT-GATE-v1+评审团协议 §二五闸+QC 清单 §12 两行（已落） | 已闭环 |
| V3 四型病灶判例+官方技巧四条 | ②台账修改：EXPERIENCE-LEDGER 追加 J-25~28/P-14~17（本窗落·台账磁盘副本曾遭旧缓存整文件覆盖截断——已从 HEAD 恢复 J-20~24 五节判例后合并上链·J-11 同名覆盖判例复发实录） | 已闭环 |
| 密度双向律/能力边界律/多人物上限/文字特效改参考视频 | ②法修改：PROMPT-SPEC §五/§六 巡检注记+专家审 E 面执法（随首审执行） | 接线中 |
| 改生产提示词前先加测试 | ②法修改：专家审闸 §一复检环+QC §24 回流（已含 verdict 复验条） | 已闭环 |
| Krea 负面字段官方沉默/Qwen 两代改写器不一致（Edit 线锁老版） | ④判负留痕+工艺注记（波文件失败面·Edit 线按老版第 8 条执法不变） | 留痕 |

- 更新记录：T0 骨架（早落盘律）→四路波归笼→防线二直验 2 处→终稿 2026-10-15（bm-a 本窗·CEO 直令云端快车道）。
