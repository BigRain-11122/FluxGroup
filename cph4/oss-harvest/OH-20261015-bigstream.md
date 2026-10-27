# OH-20261015-bigstream — OSS 收获轮切片（BigStream 实体·漫剧/短剧部门窗）

- **窗**：2026-10-15 20:40 → 10-18 20:40（CEO 令当日开线·首窗并入）
- **实搜面**：GitHub API 主题搜索 8+ 轮（comic/manga/tts/lip-sync/i2v/video-gen/story-consistency）+ 仓库页直读 33 次率（star/license/活跃度逐件核）+ HuggingFace 权重页抽查；失败面如实记：知乎/头条部分 403（行业报告已注明）、manga panel 专项搜索全 <5★=判负自建。
- **候选**（名称·源URL·许可·契合点）：15 仓全档=R-20261015-drama-oss-stack-01 §四克隆清单（正身·此处不复述）；头部=index-tts/index-tts（24.5k★·bilibili 许可·D6 配音主力）、RVC-Boss/GPT-SoVITS（62.9k★·MIT·角色音色固化）、KlingAIResearch/LivePortrait（19.2k★·MIT·漫格口型）、Wan-Video/Wan2.1（17.2k★·Apache·i2v·官方 1.3B=8.19G 压 8G 卡）、bytedance/LatentSync（6.1k★·Apache·中文口型 1.5 档 8G）、harry0703/MoneyPrinterTurbo（131.4k★·MIT·装配脚手架）。
- **采用→落点**：①能力注册表加行（cph4/README.md 开源采用·漫剧短剧工具栈 15 件）②克隆落地=media/drama-tools/repos/（gitignored·本窗 P0 前 8 仓+P1 后 7 仓·depth-1·gh-proxy https 走公网快道）③工作流接线=DRAMA-PRODUCTION-SYSTEM-v1 §三接线表（每站主力/备选/机位/许可全标注）④skill 面=CHARTER §三分配律（直用装/禁直用/待建三分类）⑤本窗无工作流变更未落地的悬空发现=零。
- **parked+理由**：ddean2009/MoneyPrinterPlus（GPL-3.0·染疫律只学不搬）；FujiwaraChoki/MoneyPrinter（2026-03 停更·被 MoneyPrinterTurbo 取代）；OpenTalker/SadTalker（停更·兜底位 parked 观察）；ai-comic-factory（已归档·只学架构）。
- **红线注记**：LivePortrait 商用前换 InsightFace 检测模型；IndexTTS-2 禁改进其他商业模型；两停更件（StoryDiffusion/SadTalker）采「思路+移植件」非主干依赖。
- **下窗指针**：①15 仓克隆完成度+首次试跑回执（IndexTTS/LatentSync/Wan 1.3B 三件优先·bm-b GPU 复工后）②W6 一致性轮子调研归位后的 ArcFace 脸相似度闸接线③「本地提效面」候选=whisperX 词锚（MV 双锚批共用件·bm-b 在产）。
