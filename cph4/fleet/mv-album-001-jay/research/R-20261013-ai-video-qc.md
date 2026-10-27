# R-20261013-ai-video-qc — AI 生成视频 QC 与 artifact 病理识别（QC/评审专家席）
> 溯源：BigStream MV 产线调研令（已知病灶：morph 鬼相/双胞胎克隆/文字穿帮/匀速 AI 感/块缝鬼影 minterpolate/慢放顿挫·CEO 令「图的问题不许传进视频」）·消费方=mv-album-001-jay 帧级十席审+成片闸·判据预注册=①病谱+检测特征 ②程序化 QC 工具 ③帧级检查表 ④i2v QC ⑤失败分流
> 验证声明：搜索 10 轮（7 成/3 被反爬拦）·直读 8 页·成源 15 条（A=4/B=4/C=7/M=0）·失败面详见 §三

## 一、artifact 病谱+检测法
| 病型 | 可检测特征 | 程序化/人工检测法 | 源·分级 |
|---|---|---|---|
| morph 鬼相（帧间重绘不守恒） | 物体渐变他物（手融杯/椅腿入桌/脸中途换身份）；成因「无持久物体记录」系推测 | 逐帧步进记「首漂移秒点」；短长对比（5s 净 10s 坏=长度变量）；DINO ViT-B/16 逐帧+首帧特征余弦（源码级实装） | C:8frame.co/blog/ai-video-artifacts-explained ·B:deepwiki.com/Vchitect/VBench/7.2-evaluation-algorithms |
| 闪帧 flicker | 亮度/色/纹理帧间脉动，平涂面与阴影最显 | flicker/jerkiness 指标阈值自动分类（YAML+CSV 逐帧）；VBench temporal_flickering 维度；逐帧 VMAF/PSNR/SSIM | B:github.com/MeaCuulpa/video_quality_analyzer ·A:github.com/Vchitect/VBench ·B:pypi.org/project/ffmpeg-quality-metrics |
| warping 形变 | 直线弯/地面波动，随机头运动 | 静机对照测试：静拍直线直→病灶在运动指令非模型 | C:8frame.co/blog/ai-video-artifacts-explained |
| 块缝鬼影（我方 minterpolate 病灶） | 运动残影/双边缘重影；先验源文件：8frame 实测其站内模型一律 24fps，时间线 25/30fps 帧复制/混合插值即生假鬼影 | 生成源文件 vs 时间线输出对比定位（编辑侧插值病灶≠模型病灶） | C:8frame.co/blog/ai-video-artifacts-explained ·C:ffmpeglab.com/articles/ffmpeg-optical-flow-motion-interpolation.html |
| 双胞胎克隆/背景人畸形 | 背景行人多指/肢体扭曲/步速异常/同脸复制（前景被注意力喂饱、背景欠参数化） | 重复对象查重+VBench「Human Anomaly Detection for AIGC Videos」解剖质量检测管线（2025-04 发布） | C:sealedrose.com/blog/how-to-detect-ai-video-artifacts ·A:github.com/Vchitect/VBench |
| 文字穿帮（伪字） | 招牌/背景文字降级为伪字形（仿排版不成词） | OCR 置信度辅助【C 级通用实践·待证】；行业共识=可读文字一律后期层不进生成镜（双源） | C:sealedrose.com/blog/how-to-detect-ai-video-artifacts ·C:openfilmo.com/ai-video-artifact-fixes |
| 物理穿帮+生物失真 | 脚底滑移/浮空/液体消失/穿模碰撞；两眼瞳孔反光形状位置不匹配、发丝溶并 | 人工步进查足底接触/碰撞边界/双瞳高光；VBench-2.0 五类 18 细维含 physics-based realism 与 human motion | C:sealedrose.com/blog/how-to-detect-ai-video-artifacts ·A:arxiv.org/abs/2503.21755 |
| 匀速 AI 感（plastic look） | 皮肤无毛孔/过分平滑/斑驳平滑与颗粒背景并存/缺色差与快门特征 | 质感均匀度+ISO 噪声一致性目检，辅 noise/colorfulness 指标 | C:8frame+sealedrose（同上两 URL） ·B:github.com/MeaCuulpa/video_quality_analyzer |
| 匀速慢放顿挫（stutter） | 帧重复、差分序列低差值段 | ffmpeg 抽帧→帧差分→剔场景切换→低差值段二值判定；signalstats 逐帧 luma/chroma delta 出 CSV | C:besthub.dev/articles/video-stutter-detection-via-frame-difference-analysis-using-ffmpeg-4e4418616fe1 ·B:ffmpeg-cookbook.com/en/articles/signalstats |

## 二、对我们 QC 链的适配建议（CEO 令「图的问题不许传进视频」落点）
- 帧级十席审扩查表（gist 固定审序 [C:gist.github.com/coolcbq/37da4e5d990864b2ec408770357a0646]）：brief match→主体准确（形状/身份/数量/比例）→构图→光（高光阴影须与设定光源一致）→edges/anatomy（手指/发丝/珠宝/文字痕迹/产品边/重复对象）→material（玻璃/金属/布料/皮肤/食物行为一致）→brand safety（伪字/撞 logo）→交付规格。即帧侧闸表。
- i2v 双侧 QC：输入=approved start image（先定稿图再跑视频 [C:8frame]）+gist preserve/change 分离（身份/比例/Logo 位/机位/材质/对象数=必保；背景/光向/服装/调色=可变）；输出=首帧对源图逐帧 PSNR/SSIM/VMAF 比对 [B:pypi.org/project/ffmpeg-quality-metrics]+尾 1/4 段抽帧查「结尾崩坏」；VBench-I2V 为 i2v 专设 3 维 [B:deepwiki 确认存在]；人脸 ID 漂移用 ArcFace/InsightFace 嵌入余弦【C 级通用实践·本轮未 A/B 直验】。
- 视频级程序化红线入成片闸：全片跑 video_quality_analyzer（flicker/jerkiness/blockiness 超阈自动分箱）+对参考片逐帧 VMAF——超阈闸停转人工；CSDN 验收 SOP「先完整观看→画面/声画/内容逻辑/字幕/模板感五维专项」[C:blog.csdn.net/weixin_29061821/article/details/167718773] 中「模板感」与我方「匀速禁检」同向，可并项双查。
- 帧率纪律成文：源 24fps≠时间线帧率=假鬼影来源——成片闸增设「先验生成源文件」前置步骤（我方 minterpolate 块缝鬼影属编辑侧插值病灶，非模型病灶）；插值/慢放操作前强制帧率核对 [C:8frame]。
- 失败分流决策树（openfilmo [C:openfilmo.com/ai-video-artifact-fixes]）：①5s 短渲染先行诊断 ②命名病型再改（全面重写会毁掉已好部分+引入新病）③只改一变量（时长/主体数/运动量/景别/参考图）④同 prompt 重跑一次（间歇性故障=采样问题非 prompt 问题）⑤构图规避（手藏口袋/文字出画/背景阴影——合法手段非妥协）⑥后期修补仅限：文字/Logo/字幕后期层、轻闪帧 grain/调色掩蔽【效果未量化·待证】⑦全败才弃用镜头。
- 结论应用表（落点四选一）：| 病谱+程序红线→成片闸法文修改|接线中 |帧级扩查表→十席审表法文修改|接线中 |i2v 双侧 QC→AUTO-POLISH-LOOP 任务单|接线中 |分流决策树→MV-PRODUCTION-PIPELINE 法文修改|接线中 |

## 三、验证声明
- 实读：8 页直读（8frame/sealedrose/VBench GitHub README/VBench 项目页/video_quality_analyzer/openfilmo/gist/DeepWiki 算法页）；4 条仅按搜索摘要引用（CSDN/besthub/PyPI/ffmpeglab）。搜索 10 轮 7 成 3 拦。
- 分级：A=VBench GitHub+项目页+arxiv 2503.21755（经 README 引文直验）+arxiv 2411.13503 ·B=DeepWiki/video_quality_analyzer/ffmpeg-quality-metrics/ffmpeg-cookbook ·C=8frame/sealedrose/openfilmo/gist/besthub/CSDN/ffmpeglab ·M=0（ArcFace 人脸度量、grain 掩蔽效果两项挂 C 级待证）。
- 承重主张直验（防线二）：①subject_consistency=DINO ViT-B/16 逐帧+首帧余弦（DeepWiki 带源码行号 L30-69）②video_quality_analyzer 指标清单（README 直读）③VBench 16 维全名+Human Anomaly Detection 管线+VBench-I2V 3 维存在（GitHub README/DeepWiki 直读）。
- 失败面：zhihu.com/p/2080346922750160904 返回 403（分流主张改由 openfilmo 承担）；DuckDuckGo 连拦 3 组查询（分批重试后 7 轮成功）；8frame 挂 2026-10-02 自我修正声明（撤回模型优劣断言——本件只引其「现象+检查法」，不采其模型排名）；闭源模型病发率横向无 A 级数据（不采信 8frame 站方未测量的同类断言）。
- 更新记录：T0 骨架落盘→T1 病谱双源→T2 工具+VBench（A 级）→T3 中文源+分流→T4 终稿（node 实数 31 行·行数帽 ≤60 达标）。
