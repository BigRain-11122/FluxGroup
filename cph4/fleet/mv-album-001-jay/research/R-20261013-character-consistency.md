# R-20261013-character-consistency — AI 视频角色/世界一致性系统调研（BigStream MV 产线·一致性管理专家席）
> 溯源：mv-album-001-jay 产线任务单（多镜 MV 人物必须同一人）·消费方=BigStream MV 产线·判据预注册=①2026 跨镜 ID 工业方案对比 ②10-20 分钟长篇一致性工作流 ③服装/道具/场景等脸外维度 ④漂移检测与修补 ⑤LoRA 强度×相似度权衡
> 验证声明：实读成源 10 条（A=5/B=3/C=2）+Bing 摘要级 3 条（不计承重）·检索 5 轮（DDG 全线风控失败 6 次→Bing 浏览器 4 轮 EN+1 轮 CN）·失败面见三

## 一、核心发现（带 URL）
- 漂移根因（C 级，A 级旁证）：视频扩散模型**无状态**，无「与上一镜同人」原语；提示词身份=类别而非身份（同 prompt+同 seed 也漂：noise scheduling/attention dropout 不完全遵守 seed）；单张参考图第 3-4 镜起衰减、第 6 镜失守——https://juying.art/zh-CN/blog/character-consistency-ai-video-guide ；Wan2.2 官方 README 亦以社区模型 Helios「不依赖常规 anti-drifting 策略做分钟级长片」佐证漂移治理为公认难题——https://github.com/Wan-Video/Wan2.2
- 五路线横评（C 级直读）：①prompt+seed 固定=失效；②每镜塞同一参考图=3-4 镜起漂；③角色 LoRA=2024-25 单工具最强，但视频端需 20+ 训练图、单角色训 30min-2h、静态图训练→动作僵硬、多角色组合差；④IP-Adapter/Reference-only=5-10 镜中等、20+ 镜崩；⑤逐帧蒙版人工修=不可放量——https://juying.art/zh-CN/blog/character-consistency-ai-video-guide
- 2026 收敛方案 **character-as-asset 角色资产化**（C 级）：特征抽取（ArcFace 脸 embedding+体型+肤发+风格）→绑定 character_id→**注入 conditioning 而非提示词**（绕开提示词漂移）→漂移负面词目录（眼色/下颌线/发际线/肤色/不对称五模式逐项负面词）→事后相似度校验（业内示例阈值：身份 embedding cosine 0.85，低于即重生该镜）→角色库跨项目复用；QC+选择性重生算力 ≈1.2-1.5×——https://juying.art/zh-CN/blog/character-consistency-ai-video-guide
- 官方工业面（A 级）：Kling 3.0 Subject Binding=4 参考图（正/侧/背/特写）或 3-8s 视频引用或 5-30s 声纹，合成「Visual DNA」；**AI Multi-Shot 单次 15s 出 6 机位且绑定下角色恒定**；遮蔽复脸；Elements 可把**场景/服装**设为一致性元素——https://klingai.com/blog/kling-3-subject-binding-character-consistency + https://kling.ai/quickstart/ai-video-character-consistency ；Google 2026 默认视频模型 Gemini Omni Flash 主打原生角色一致性+多轮对话编辑，Veo 3.1 转场景延伸/尾帧——https://ai.google.dev/gemini-api/docs/video
- 长篇工作流（B 级）：「**别让 AI 一部生成长片**——短受控镜头+参考资产+动作交叠+声桥+精剪拼长」；连续性**六层表**=身份/服装道具/地点/动作/光色/剧情信息（「长片先死于外套换色、门口移位，才轮到脸变」）——https://www.media.io/creative-tips/how-to-make-long-ai-videos-with-consistent-characters.html ；选角律（C 级）：4-6 候选取 **1 张锁死**（多锚混喂=模型取平均→脸向中点漂）、4K 精修参考防漂更强、视频提示词**永不重述角色**（图=身份契约·词=运动契约）、>5-10s 漂移=模型极限须尾帧交接、并行扇出、只重跑弱镜——https://astorie.ai/workflows/character-consistency
- LoRA 强度实证（B 级）：0.5=痕迹级；**0.8=多数角色 LoRA 甜点**（身份清晰且提示词仍可变）；1.0=最大保真（参考卡用）；1.5=过拟合伪影；低档 0.3-0.6=基模主导（灵活）、高档 1.0-1.3=LoRA 主导（保真）——https://blog.pixai.art/en/lora-weight-settings-guide/ ；**一致性天花板由数据集定而非权重定**：数据集内漂移永久烙进 LoRA（三成图鼻子微异≠取平均，是学会「这角色鼻子不确定」）；过拟合 LoRA 极易误判为好 LoRA（脸锐利且完全一致但僵）；20-30 帧、rank 16-32、curation 律「要眯眼看的帧一律砍」——https://github.com/mikeabakumoff/sdxl-character-lora-guide
- 修补兜底（A 级开源）：FaceFusion（30.2k★）face swap+口型同步、headless/batch 作业系统可整片流水线救脸——https://github.com/facefusion/facefusion ；**许可红线**：PuLID/InstantID/FaceID 均建于 InsightFace 非商用许可，商用管线须先核——https://github.com/mikeabakumoff/sdxl-character-lora-guide

## 二、对我们产线的适配建议
| 场景 | 推荐方案 | 成本 |
|---|---|---|
| 男主跨镜 ID（现状 jman LoRA 0.6+ID 块） | 双保险升三保险：+Seedance 参考图模式喂「4 图 DNA 包」（正/侧/背/特写）；LoRA 分镜分档：特写/静态镜试 0.7-0.8、大动作/群舞镜守 0.5-0.6（静态图训练的 LoRA 高强度→动作僵硬，勿盲目上调） | 参考包 4 图制图费；生成量不变 |
| 女主定脸（现状每曲独立选角） | astorie 选角法：每曲 4-6 候选→锁 1 锚定图→4K 精修→转面表入参考包；锚定图登记角色库，后续曲目可复用=character-as-asset | 每曲 0.5 天→锁定后边际≈0 |
| 提示词层 | ID 块保留但降级为辅助；每角色写五模式漂移负面词目录常驻 negative | 0（一次性写） |
| 帧链与长镜 | 帧链保留（5-10s 漂移极限双源证实）+相邻镜动作交叠+声桥 | 0（编排纪律） |
| 服装/道具一致性 | 分镜表**预注册状态变体**（湿身/破损/换装各配 1 图入参考包）；ID 块加服装常量段；「服装/场景元素化」思路移植进 Seedance 多参考 | 每变体 1 图 |
| 场景一致性 | 每场景锁 1-2 张场景参考图入参考包；光色统一交调色阶段（六层表第 5 层） | 每场景 1-2 图 |
| QC 检测 | 每镜对照角色圣经查 4 项（眼色/发长/下颌线/标志物）+接触表缩略图扫查（漂移在缩略图级显形）；条件允许上脸 embedding 阈值（业内示例 0.85 cosine） | 每镜 +1 次检视 |
| 修补梯队 | L1 只重跑弱镜（改运动词、不改身份词）→L2 换更近脸部参考→L3 加漂移负面词→L4 FaceFusion 批量换脸兜底（商用先核 InsightFace 许可） | 重跑预算 1.2-1.5× |
| 男主+女主同框镜 | 同框镜 QC 加严（业内数据：多角色场景约 10% 需人工补救） | 同框镜重点复检 |

- 落点（四选一）：任务单——mv-album-001-jay 产线一致性规程接线（状态：接线中）。

## 三、验证声明
- 检索与成源：5 轮（DDG 工具+html/lite 端被风控=6 次失败→Bing 浏览器 4 轮 EN+1 轮 CN）；实读 10 源：A 级 5（klingai.com×2/ai.google.dev/GitHub Wan2.2/FaceFusion）、B 级 3（media.io/pixai.art/GitHub sdxl-character-lora-guide）、C 级 2（astorie/juying）；Bing 摘要级 3（purposewithpresence/atlascloud/ltx.io）未直读、不作承重。
- 承重双源核验：漂移机理=juying(C)+astorie(C)+media.io(B) 三源互证；帧链 5-10s 极限=astorie+juying；LoRA 档位=pixai(B) 数值+juying(C) 视频端僵硬旁证；juying 自评工具横评表（Seedance 2.0 跨镜=中等）带供应商立场，仅作参考。
- 失败面：Runway help 403/act-one 500、Midjourney docs 403、atlascloud 直读 404、ltx.io 正文 JS 壳不可读、雷达日报 7 天窗无相关、CN Bing 快照文件丢失、Mojeek 403。
- 更新记录：T0 骨架落盘→T1 官方面（Veo/Kling）→T2 长篇+astorie→T3 LoRA/中文面→终稿（约 47 行，行数帽内）。
