# GitHub 风向简报 #1（研究室 · 2026-10-04）

> 范围：近一周新建爆星仓全量判读（两窗合计 106 件·created:>09-20 与 >09-27 双窗 search API·star>300/400）+ trending 抽样。口径=api.github.com 结构化数据（非页面爬取）。

## 一 本周风向大主题（研究室综合判断）

1. **「Jev / System 1 决策模型」生态爆发**——两窗 106 件中 ≥12 件同族（jev-chat-jarvis 6,990★ 榜首/jevgrep 1,499★/AnyJev/ollaya「决策模型的 Ollama」/jeff 0.8B 毫秒决策/rizzo-flow/shapeshift/CLM 2,324★…）：社区在把「LLM 生成」降级为「轻量类型化决策引擎」——毫秒级、本地、可校准概率。**对集团**：这是 local-first L2 层的下一代形态候选（快决策走 0.8B 模型·慢思考走大模型），BigCompute 本地推理栈值得开研究线。
2. **游戏 × AI 模组时代开启**——universal-modder（2,887★·「让 Claude 给你拥有的任意 PC 游戏做模组」：侦察+逆向+fal 生成美术/3D/音频+游戏内测试一条龙）；SkyCraft（Minecraft 物理塞进 Skyrim 821★）；卡普空把下一代引擎的 REDox 数据层直接开源（1,014★·Apache）——**工业风向标**：大厂开始开源引擎核心组件。**对 Biggame**：AI 模组管线=小游戏快速增益方向；REDox=Unity 外的 token 化数据引擎参照。
3. **AI 自媒体内容管线全自动化**——AIHOT（自动找热点自动写日报的网站框架）**5 天 1,400→5,694★（日增 ~860 持续爆发）**；reelmimic（喂一段你爱的视频→AI crew 产出同风格新视频 1,247★）；onetake（连续镜头产品片）；short-video-generator-AI（LLM+Whisper 竖版视频流水线）。**对 BigStream**：这套组合=从找题到成片的全自动管线参照（合规面：内容源按搁置令内档管理）。
4. **官方 MCP 插件化**——openai/mcp-extensions（ChatGPT 官方插件 SDK 742★·Apache）+ CopilotKit OpenDots（always-on AI 同事 2,992★）+ dots（自带浏览器不被封的 agent 2,593★）：agent 生态从「工具调用」走向「常驻同事」形态。

## 二 有趣分享（好玩面 Top 6）

| 项目 | ★ | 一句话 |
|---|---|---|
| **lipflow** | 473 | 「嘴唇打字机」：按住键无声动嘴型，文字就打出来（本地 Mac）——无声语音输入新形态 |
| **SkyCraft** | 821 | 在 Skyrim 里当 Minecraft 玩家：把方块物理/物品栏/合成搬进天际世界 |
| **disktree**（tobi/Shopify 创始人手作） | 1,837 | 磁盘空间变成一棵可点击的矩形树，找到吃掉你硬盘的东西 |
| **tidewater** | 925 | 「用 Opus 5.5 造了一座海边小镇」——AI 生成完整小城的展示 |
| **Wind-Waker-Recomp** | 464 | 塞尔达风之杖静态重编译到 iPhone/iPad（GPL·同好工程） |
| **yomiyasu** | 1,369 | 把 AI 生成的「机翻味日语」润色成自然日语的 Agent Skill |

## 三 业务契合与处置（高频点赞→落实）

| 件 | 直中哪条线 | 处置 |
|---|---|---|
| VoiceStudio（trending 日榜 #1·**一周 44.9k→52.9k★**） | BigLife 语音/BigStream 配音 | 许可直验=**AGPL-3.0** → 红线注记：**本地工具面可用（Blender 同律）·禁服务化（§13）·禁入对外算力包**——接线单已带此注记派 @BigLife/@BigStream |
| universal-modder（2,887★·MIT） | Biggame（AI 模组管线） | 接线单 @Biggame：评估「AI 模组工坊」面（游戏快速内容增益·fal 集成参照） |
| AIHOT（5,694★·MIT） | BigStream（热点日报自动化） | 接线单 @BigStream（已从 09-29 窗升级：爆发确认·优先级升） |
| jeff 0.8B System 1（1,361★·MIT·本地毫秒决策） | BigCompute 本地推理栈/量化快决策 | 接线单 @BigCompute：与 Bonsai 波并轨实测（0.8B 显存包络全机可跑） |
| hypoarena 假说竞技场（560★·MIT·CPU-only） | BigMoney 研究方法论（假说-证据图+Elo 锦标赛） | 转办参照 @BigMoney（与 edge 假说线同题·学实现优先） |
| CAPCOM REDox（1,014★·Apache） | Biggame/引擎面 | 学实现不搬件（token 化结构数据引擎·性能参照基线） |
| Strata（125B MoE on 8GB·MIT） | BigCompute（bm-c 16GB 档） | 接线单维持（09-29 已派） |
| AutoCad/Windows-Optimizer/SolidWorks-CAD（三项 null 许可+模板化描述） | — | **疑似 SEO 垃圾仓**——爆星榜的水分样本·判负留痕（诚实面：star ≠ 质量） |

## 四 诚实面与节律修复

- **断窗承认**：雷达首扫 09-29 完成后，09-30→10-03 四天无 CPH4 切片（值守轮点名面应已记录）——「每窗必扫」的立法节律没有被执行到位，本简报=补扫+恢复点。修复=当前窗起恢复 72h 节律+周简报呈你（本件 #1）。
- 数据口径：search API 两窗（09-20+/09-27+·star>300/400）合计 106 件全量+ trending 双通道失败面在案（web_fetch 带偏/fetch_content 部分解析→结构化 search 为主源）。
- 未验明不用：elpis/jevbox/fsiaonma 等 null 许可件全判负留痕。
