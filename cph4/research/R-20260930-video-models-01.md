# R-20260930-video-models-01 — 本地 12GB 档 I2V 视频模型重研究+提示词+取帧（CEO 令 O-2026-0929-034·C 腿 v2）

> 溯源：C2-任务书（CEO 判 v1「观感接近可行·可以更好」·MOTION_WEAK 短板）·消费方=C 腿 v2 实弹选型 ·判据预注册=①12GB 卡 offload 实况下最优 I2V 件 ②I2V 动作提示词技巧 ③取帧组 GIF 技巧
> 验证声明：fetch 成源 11（A=10：HF 卡×4/HF API blobs×3/diffusers 0.40.0 官方文档×1/GitHub README×2；B=1 RIFE 系）+本地核验 3 次（diffusers 管线类清单·LTXConditionPipeline 源码 randn_tensor·T5 四分片 SHA256）。失败面：LTX prompting_guide.md raw 404（仓重构）；GitHub Lightricks README 已改 API 营销页（无 VRAM 表，弱源如实降级）；LTX-2 API 401。

## 一、候选谱系对照矩阵（双源核验·数字带出处）
| 候选 | 参数/下载面 | I2V | VRAM 口径 | 步速 | 许可 | 判 |
|---|---|---|---|---|---|---|
| LTX-0.9.8-13B-distilled | 13B bf16；transformer 24.3GB+VAE 2.32GB+T5 17.75GB（**T5 与本地 0.9.5 SHA 四分片全等→复用**） | ✓ LTXConditionPipeline(image=,frame_index=) | 未标（走 offload 律） | 蒸馏 4-10 步·guidance=1.0·timesteps=[1000,993,987,981,975,909,725,0.03] | LTX Open Weights(other)·gated:false | **主选** |
| LTX-0.9.7-distilled | 同构（VAE 同件 sha 3419989c·transformer 旧权重） | ✓ 同 | 同 | 同（文档同 timesteps 注） | 同 | 备选回退位 |
| Wan2.2-TI2V-5B | 5B；~25GB 级 | ✓ 单模 TI2V | 官方地板=24GB（4090 档），4090 上 720p5s<9min | 720p@24fps 原生 | Apache-2.0 | 弃：本机 diffusers 0.40.0 无 TI2V 专用管线类（实测）+720p×121f 超本机 3.5GB/45min 帽 |
| Wan2.1-I2V-14B-480P | 14B；~40GB+（14B+CLIP+umt5） | ✓ WanImageToVideoPipeline | offload 可低显存 | 50 步·guidance 5（官方例） | Apache-2.0 | 弃：14B 每步全重流经 offload×50 步→小时级超帽 |
| CogVideoX-5B-I2V | 5B(标 6B)；~21GB | ✓ CogVideoXImageToVideoPipeline | diffusers BF16 全优化「5GB 起」·INT8 4.4GB 起 | 50 步·A100 180s（卡表） | CogVideoX License | 弃：5GB 起地板>3.5GB 红线·锁 720×480@8fps·本机 offload 更慢 |
| LTX-2-13B-distilled | 13B | ✓ | gated | - | gated | 弃：HF API 401 匿名不可下 |

## 二、判定面
- 主选 0.9.8-13B-distilled 五理由：①gated:false 匿名可下（API 直读）②diffusers 0.40.0 在库支持（本地 ltx 模块 LTXConditionPipeline+LTXI2VLongMultiPromptPipeline 实证，文档含 0.9.8 专节）③蒸馏 4-10 步把 13B offload 流量压进 45min 帽④I2V 首帧硬条件保 identity（卡例 image_cond_noise_scale=0.025·decode_timestep=0.05·decode_noise_scale=0.025）⑤T5 复用省 17.75GB（SHA 全等实测）。
- 0.9.8 仓有 vae/ 嵌套重复树（API blobs 实查：vae/transformer、vae/text_encoder 整套重复再挂一份）→ 下载必须 allow_patterns 白名单（只取 model_index/scheduler/tokenizer/transformer/vae 两件/LICENSE），media* 与 vae/ 子树全排除。
- 兜底链：0.9.8 两轮败→0.9.7-distilled（同管线同参数文档位）→0.9.5 2B@512px+提示词升级（零下载保底）。

## 三、提示词技巧（I2V 动作显式化·源=0.9.7/0.9.8 卡例+diffusers 文档例）
- 词序律：主体特征→动作时序分解（身体部位+方向+幅度，如卡例 "she reaches the top of the stairs and turns left... knocks on it with her right hand"）→相机句→风格后缀；卡 General Tips 原话 "The more elaborate the better"。
- 相机静止措辞："The camera remains stationary, focused on..."（卡例反复出现）——锁相机防漂移吞动作。
- identity 保真：蒸馏档 guidance=1.0 下负词失效（文档参数注 "Ignored when not using guidance"）→保真靠首帧图硬条件+提示词如实描母版（v1 教训：写 yellow feathers 而母版为薰衣草紫）；非蒸馏档可用负词 "worst quality, inconsistent motion, blurry, jittery, distorted, discontinuous motion"（LTX 例）+Wan 官方负词 "static, still picture, deformed, misshapen limbs"。
- 三动作显式=每动作独立完整句+时序词 then/finally 串接（呼吸 puff/shrink+挥手 lift/wave+Q 弹 squash-stretch hop）。

## 四、取帧技巧
- fps 12 vs 16：LTX 原生 24/25fps，121 帧@24fps=5s。12fps（magick -delay 8）逐帧可读性高/GIF 小；16fps（-delay 6≈16.7fps）流畅。判据：帧间 RMSE 大（动作快）取 16，柔和取 12——本次双组实测目检定夺。
- 漂移帧过滤：magick compare 双 RMSE 序列（相邻帧+对首帧累计）；累计 RMSE 破离群阈值=漂移嫌疑帧→剔除或截停；相邻 RMSE≈0 死帧剔除收紧循环。
- 动作峰值对齐抽帧：相邻帧 RMSE 序列找动作峰窗，选帧集须含各动作峰（呼吸峰谷/挥手最高位/Q 弹触底腾空）；循环起止取 RMSE 最近似对（循环缝最隐）。
- RIFE 可行位：MIT；vs-rife 需 VapourSynth R69+（重依赖·沙盒不引入）；rife-ncnn-vulkan 独立 exe=免依赖位（未实测）。判：原生 24fps 帧源充足本轮不需要；仅 8fps 源（CogVideoX 类）才启用——待证。

## 五、结论应用表（落点四选一）
| 结论 | 落点 | 状态 |
|---|---|---|
| 主选 LTX-0.9.8-13B-distilled（白名单下载 ~26.6GB） | 任务单：C 腿 v2 沙盒实弹 | 接线中 |
| 提示词三动作显式+相机静止+如实描母版 | 任务单：C2 正式生成 | 接线中 |
| 取帧 RMSE 双序列驱动（12/16fps 双组对比） | 任务单：C2 GIF 组装 | 接线中 |
| Wan2.2-TI2V/Wan2.1-14B/CogVideoX/LTX-2 弃选留痕 | 判负留痕：本件 | 已闭环 |
| 云端对照 TJGenerators generate_video（Seedance 2.0 系·观感上限参照） | 任务单：out\C2_cloud_demo.gif | 接线中 |

- 更新记录：单会话连续采集 12 源（未分段落盘·如实注记）→ 终稿一次落盘 44 行。
- 防线二：独立抽验两承重主张——①「T5 可复用」本地 SHA256 直验=0.9.8 API lfs.sha256 四分片全等（7a68b2c8/b8ed6556/c831635f/02a5f2d6）✓；②「0.9.8 非 gated」API gated:false 直读✓。行数=node/肉眼双计（无 BOM UTF-8）。
