---
name: mv-intent-to-prompt
description: 立意→关键词转译技能（把导演意图变成模型能执行的词面，并验证它真执行了）。Use when a script/idea is good but the generated frames don't match — writing generation prompts from design intent, auditing prompt specificity, or measuring execution hit rate. 正身=cph4/fleet/mv-album-001-jay/INTENT-TO-KEYWORD-v1.md
---

# 立意→关键词转译（mv-intent-to-prompt）

## 一句话
**AI 不执行立意，只执行可见证据。** 立意→场面事实→可见证据→词面，跳过第三层就是把导演的活交给模型。

## 四步（每镜一次）
1. **立意**（一句话·永不进提示词）
2. **场面事实**：谁·在哪·做什么（三要素缺一不算事实）
3. **可见证据** ≥2 项：光/物/动作/构图，每项都要能被摄影机或测光表拍到
4. **词面**：主体 40% → 动作表演 25% → 光 20% → 环境时代 10% → 媒介 5%（顺序即权重）

## 具体性四级（写不到几级，AI 补到几级）
L1 品类（`an old bicycle`→AI 自己发明形制）→ L2 形制 → L3 部件 → **L4 状态痕迹**（主角物件与关键道具必须 L3/L4，背景 L2 即可，防提示词过长漏项）。

## 执行契约卡（每镜一张）
```
必须出现（3）：…
必须不出现（2）：…
可判失败点：…
```
烧后逐条打勾，**执行准确率 = 打勾数 / 必须出现数**；<2/3 不进批量；连续两包 <2/3 = 标尺本身复盘，禁止继续重摇。

## 好例子（词面里没有立意词）
- 立意"思念是重复劳动" → `seven aged paper airplanes along a ledge, one crumpled; a fresh white one held between two fingers; late side light raking the paper grain`（不出现"思念/每天/孤独"）。
- 立意"把星连起来是人在许愿" → `hand enters from the lower edge, index finger settling on one star then the next; the stars hold still; mouth shapes a count without sound`（"连线"不写，错觉由观众完成）。

## 禁用
情绪/氛围标签词（cinematic/dreamy/sad）｜"要更自然"类验收语｜把多个真值源塞进同一属性（材质色 vs 调色词）｜起帧对抗动作｜否定词堆砌（改成正向锚挤位）。

## 分轨
Krea2=八块序/权重 3-5/零否定；H3=三字段+时间戳；Seedance=中文八要素 60-100 词/单镜单运镜/禁秒数。**跨模型禁套用。**

## 验收
提示词专家审十一面 + 契约卡 + 准确率记账（QC §12 v1.7）。