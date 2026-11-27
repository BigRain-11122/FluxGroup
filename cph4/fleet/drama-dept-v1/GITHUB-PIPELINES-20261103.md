# GitHub 现成管线盘点（2026-11-03）

> 目的：不重复造轮子。只看"能不能直接搬进我们 MV 同链（KF→i2v→剪辑→配音→字幕）"。
> 判据：许可能不能商用、是不是同一品类（短剧/漫剧/电影，不是解说混剪）、有没有"一致性 + 门禁"。

## 一、直接相关（短剧/漫剧/电影）

| 仓库 | 星 | 许可 | 能力 | 我们怎么用 |
|---|---|---|---|---|
| **TengXianhai/ai-short-drama-agent** | 新 | 未标注（**只学不搬**） | 七步流水线：立项→剧本→拆解→资产→分镜提示词→关键帧→逐镜视频；每步有 QC 门禁、断点状态 `.drama-state.json`、**身份锁三件套（脸部图+角色身份串+seed）**、`frame_diff.py` 一致性检测、`DEFECTS_CATALOG` 缺陷字典 | **搬模式**：这套七步与我们的工序表同构，缺的正是「身份锁 + frame_diff + 缺陷字典」三件，直接抄设计，代码自己写 |
| shijue-aid/aid-studio | 1.3k | MIT | 开源 AI 漫剧/短剧/电影/漫画平台：剧本、角色场景、智能分镜、图/视频生成、配音、成片预览；多模型接入，可自部署（Java17+Spring Boot+MySQL，另有 Web 端） | **参考产品形态**（无限画布/导演台/模型池）；不整体部署，太重且会绕过我们的闸 |
| junjamrk/OpenCinema | 124 | MIT | local-first 画布式 AI 影视工作室，13 个节点插件，故事板/资产/3D previs/生成/剪辑；MCP 让 agent 用同一套工具接管手工步骤；接 ComfyUI 工作流与多家 provider | **看它的 MCP 节点设计**；我们的工序表+执行器已是同类，暂不引入第二套编排 |
| JerrIsTheBesta/AI-Short-Drama-Studio | 33 | 未核实 | 剧流 Studio：LLM/视觉理解/生图/图生视频/配音/字幕/剪辑 | 只作界面参考 |
| Dralo-Studio | 10 | 未核实 | 短剧工坊：无限画布、3D 分镜导演台、多轨剪辑 | 只作界面参考 |

## 二、我们缺的那一环：口型（可直接装）

| 仓库 | 星 | 许可 | 关键参数 | 结论 |
|---|---|---|---|---|
| **bytedance/LatentSync** | 6.2k | **Apache-2.0** | 扩散式端到端口型同步，**推理约 6.5GB 显存**；真人与动画角色都支持；带帧率重采样/人脸对齐/音画同步置信度/画质评分 | **装到工作机做"接口型站"**：说话镜必须过口型，否则不许进成片 |
| ShmuelRonen/ComfyUI-LatentSyncWrapper | — | 未核实 | LatentSync 的 ComfyUI 节点封装（可选 lips_expression / steps / seed） | 我们走 ComfyUI 就装这个封装 |
| boat2moon/infinitetalk-comfyui-workflow | — | 未核实 | InfiniteTalk + WanVideo 中文口型，Q8 GGUF，32GB 显存，含调参表（V2 参数最佳） | 显存 32GB 门槛高，作备选；参数表可借鉴 |

## 三、不适用（别浪费时间）

| 仓库 | 为什么不用 |
|---|---|
| MoneyPrinterTurbo / Pixelle-Video / MoneyPrinterPlus / Short-video-factory | 解说/混剪/营销批量向，不是剧情叙事；且多为 GPL 或重分发逻辑 |
| NarratoAI | 解说+剪辑，非生成剧情 |
| Story-flicks | 故事短视频（图文+旁白），没有镜头级生成与一致性 |

## 四、要搬进我们工序的三件（零采购，只改代码）

1. **身份锁三件套**：每个角色固定「脸部图 + 身份串（固定描述词）+ seed」，每镜生成都带这三件；跨镜脸不一致就判红重烧。
   → 补上我们样片里"第 1 镜蓝衬衫、第 3 镜深色西装"的问题。
2. **frame_diff 一致性检测**：相邻镜/跨镜的角色区域做像素差，超阈值即疑换人；比人眼早发现。
3. **缺陷字典（DEFECTS_CATALOG）**：把"崩脸/伪文字/多手/穿模/匀速/首帧失真/速度线穿帮"写成可判条目，逐条给判据；对应我们已有的 mv 四闸，扩到漫剧。

## 五、结论（一个）

**不引入任何一套现成平台；只搬三件设计（身份锁 / frame_diff / 缺陷字典）+ 直接装 LatentSync 做口型站。**
理由：现成平台的编排层会绕过我们的闸与账（又是"绿了但没产物"的老路）；它们的价值在工序设计与一致性做法，这两样我们缺，且可以零成本抄。

## 六、来源

- ai-short-drama-agent（七步流水线/QC/身份锁）：https://github.com/TengXianhai/ai-short-drama-agent （抓取 2026-11-03）
- aid-studio（MIT，AI 漫剧平台）：https://github.com/shijue-aid/aid-studio （抓取 2026-11-03）
- OpenCinema（MIT，画布+MCP）：https://github.com/junjamrk/OpenCinema （抓取 2026-11-03）
- bytedance/LatentSync（Apache-2.0，6.5GB 显存口型）：https://github.com/bytedance/LatentSync （抓取 2026-11-03）
- ComfyUI-LatentSync 封装：https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper （抓取 2026-11-03）
- ai-short-drama / ai-drama-generator 主题页（用于找同类）：https://github.com/topics/ai-short-drama （抓取 2026-11-03）