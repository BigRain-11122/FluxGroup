# R-20261015-mv-performance-stack — 表演根治技术栈：口型/身体/舞蹈/卡点四件套选型（CEO 令 O-20261015-1700）
> 溯源：CEO 原话「要做到世界第一」+终审「表演还有问题」·消费方=bm-c+装配站·判据=三问预注册
> 验证声明：星数/license 全部 A 源直读（github.com 仓页/Raw LICENSE·读时 2026-10-15）·显存取 README 自述（A）·未直验处标 M/C·零断言；有效内容读取 21 次（预算 20·LivePortrait license 补验超 1 次·如实披露）·另有 19 次零内容失败调用如实记入（GitHub MCP 解析故障×8·api.github.com 403×8·Sonic 候选仓 404×2·DDG 拦×1）
## 一、对口型 Top3（星级/license/显存/接法/代价）
1. **LatentSync**（bytedance·6.1k★·**Apache-2.0**·A）：音频驱动口型重绘。README A「推理最低显存 8GB(v1.5)/18GB(v1.6)」+v1.5「improves performance on Chinese videos」=中文唱词正中。接法=KF→i2v 成片后用人声干声重绘口型区（管线尾加一道）；跑法=官方 gradio_app.py（setup 为 Linux sh·A）/Windows 走 ComfyUI wrapper（M）；代价=扩散慢·v1.6 超 bm-a 12G→主力 v1.5 双卡皆可、v1.6 限 bm-c 16G 夜窗。
2. **LivePortrait**（KwaiVGI/快手·19.2k★·**MIT**·A）：驱动视频→表情/口型/头部表演整体迁移到 KF 脸——真人歌手特写参考片直解「表演僵」，比纯口型工具多眼神与头动；显存~8G(M)·Windows 经 ComfyUI 生态(M)。红线（LICENSE A 原文）：捆绑 InsightFace 检测模型「for non-commercial research purposes only」——商用须按其指示换掉该模型→障碍可解。
3. **Wav2Lip**（Rudrabha·13.2k★·A）：跑法一行（README A：`python inference.py --face 视频 --audio 音频`）·显存~2-4G(M)·Windows 易跑(M)。判负证据（README A 原文）「any form of commercial use is strictly prohibited」（LRS2 英文集训练→中文口型弱=A 推断）+口部低清。落点=仅内部 A/B 基准（商用走其 sync.so API·外部付费另行评估）。
- 失败面：Sonic 原仓 jixiaozhi/Sonic 与 AntGroup/Sonic 双 404（A 判负·读时 2026-10-15）·检索见≥3 个自称「Official implementation」镜像仓（Tianhone/Sonic- 等·B·存疑）→**待消歧不入榜·勿采镜像**；社区 Colab 实测 T4 上 5s 音频≈19min（C·慢）。
## 二、身体表演与舞蹈驱动 Top3（同上）
1. **MimicMotion**（Tencent·2.7k★·**Apache-2.0**（Raw LICENSE A）·ICML 2025）：姿态视频驱动 KF 全身直出。README A 显存「16帧 U-Net 最低 8GB·VAE 解码 16GB 可放 CPU」「35s demo 72帧=16GB(4060Ti)·4090 跑 20 分钟」+吃紧设 PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256（A）→**bm-c 16G 正命中**·bm-a 12G 用 16帧档+CPU VAE。跑法（README A）`python inference.py --inference_config configs/test.yaml`（Windows·M）；接法=KF 全身图+舞蹈参考片(DWPose)→表演段→按需 LatentSync 补口型。
2. **MusePose**（TMElyralab/腾讯音乐·2.7k★·**MIT**（Raw LICENSE A））：同类姿态驱动 image-to-video·仓内自带 pose_align.py/extract_dwpose_keypoints.py 全流程脚本（A）；显存 12-16G(M)·Windows(M)→与 MimicMotion 夜窗对照后择一主用。
3. **AnimateDiff+ControlNet**（guoyww 12.3k★/lllyasviel 34.1k★·均 **Apache-2.0**·A）：ComfyUI 成熟姿态控制链（M）·SD1.5 档 8-10G(M)（SDXL 档 README A ~13GB）；代价=时序抖动与身份漂移风险高于上两者（M）→定位兜底与风格化镜头。
- ewan 消歧失败：两轮 DDG（英/中）未见名为「ewan」的全身迁移开源项目（零断言·不虚构点名）；最近似线索=Everybody-dance-now（2018 老项目·B）/Wan2.2-Animate（2025-09 阿里 14B 动作迁移+角色替换·掘金/GitCode B 转载·未 A 直验不入榜）→该类别已由 MimicMotion/MusePose 覆盖。
## 三、音画卡点自动化方案（BPM 检测→剪辑点参数化）
1. **librosa**（8.7k★·**ISC**·A·宽松可商用）：beat_track/onset→BPM+拍点时间戳；纯 Python·CPU·Windows 无障碍（M）。装配站参数化（自研设计件）：分轨（人声/BGM）→beats.json{BPM,beat_times[],downbeats[],onset 能量}→剪辑点规则=吸附最近 downbeat·最短镜头护栏 0.6~0.8s·副歌逐拍切·主歌 2 拍 1 切·半拍/倍速误判设人工锚 BPM 校验位。
2. **beat_this**（CPJKU·423★·**代码+权重皆 MIT**（README A）·ISMIR 2024·madmom 同门继任）：精度升级备选；跑法 A 直读：CLI `beat_this 音频 -o out.beats` 或 Python `beats,downbeats=File2Beats()(音频)`；模型仅 78MB·GPU/CPU 皆可（A）→双机零压力。
3. **auto-editor**（wyattblue·5.5k★·**Unlicense**·A·公有领域）：现成自动剪切 CLI 参考实现（音频能量/静音切·B·跨平台 M）；beat-grid 参数化仍建议自写~50 行脚本·借其时间轴思路。
- 红线判负：**madmom 模型=CC BY-NC-SA 4.0 禁商用**（Raw LICENSE A·商用需联系作者）+PyPI 版仅支持 Python<3.10（beat_this README 转述·A）→**放弃**（商用红线+安装痛双杀·madmom 1.7k★·A）。
## 四、结论应用表（强制·落点四选一·含「bm-c 夜窗试跑单」建议行）
| 项 | 首选 | 落点 | 夜窗动作/备注 |
|---|---|---|---|
| 口型 | LatentSync v1.5(8GB) | 需验证 | bm-a 12G 即装·试 5s 特写中文唱词 A/B |
| 表情表演 | LivePortrait | **直接可用**（10-17 夜2 实测过·bm-c r1057：FaceAlignment blazeface BSD3+landmark 替代面=InsightFace 零引入·商用红线已解；全链通·双 Cropper+Composite 接线律入 EXPERIENCE-LEDGER J-30） | 已试跑一单（自场静帧+自场驾驶片·微妙表演忠实迁移）；正式投产待表演参考片库（盲区②） |
| 身体/舞蹈 | MimicMotion | 需验证 | bm-c 16G 跑 72帧档 10s 舞段·MusePose 同夜对照 |
| 卡点 | librosa（beat_this 备选） | 直接可用 | CPU 级今日可装·bm-a 出 beats.json 剪 30s 实测 |
| 判负/暂缓 | Wav2Lip（禁商用）·madmom（NC-SA） | 障碍待解/放弃 | Wav2Lip 仅内部基准；Sonic·ewan 待消歧·勿采镜像 |
| **bm-c 夜窗试跑单（建议行）** | 10-16 夜：LatentSync v1.6 特写×1+MimicMotion 10s 舞段；10-17 夜：MusePose 对照+LivePortrait 参考片迁移；10-18 夜：回填显存峰值/秒帧实测 | — | 三夜数据回填后把「需验证」升「直接可用」；**实况（10-17 夜2·bm-c r1057·POOL-0016）**：LivePortrait 已收官=冷烟测 652.88s（含 614s 一次性 91.9MB 权重慢下载）+热跑 72 帧表情迁移 35.55s=0.49s/帧·显存峰 16060MB(冷载瞬时·尾释放)/3681MB(热跑)→本行升「直接可用」；夜1（LatentSync/MimicMotion）无回执在案·夜3 待 10-18 |
- CEO 盲区补全（「我没考虑到的你要帮我补全」）：①中文唱词口型必须实测 A/B（LatentSync v1.5 中文优化=A 佐证·Wav2Lip 英文集=A 反证）；②**表演参考素材库是工具之外的真瓶颈**——真人歌手特写/舞段参考片不先建库，一切迁移工具无用武之地·建议随本单立项「表演参考片库」；③BPM 半拍/倍速误判须人工锚点；④显存分层：重活（扩散身体/口型）给 bm-c 16G 夜窗·轻活（卡点 CPU/Wav2Lip 级）给 bm-a 12G；⑤扩散链身份漂移须预算 A/B 对照与脸部修复后-pass。
- 更新记录：2026-10-15 骨架落盘→A 源采集完成定稿（分级：A 25·B 4·C 1·M 7·判负 2 仓）→2026-10-17 夜2 LivePortrait 实测回填（bm-c r1057·POOL-0016：升「直接可用」·回执=bmc/lp_smoke_r1057/RECEIPT-POOL-0016-night2-r1057.md）
- 防线二：✅ 主会话已独立抽验（2026-10-15·raw.githubusercontent 三源直读全过）——①LatentSync：README 直验「Minimum VRAM for inference: 8 GB with LatentSync 1.5 / 18 GB with LatentSync 1.6」+v1.5「improves performance on Chinese videos」逐字命中+LICENSE 原文=Apache-2.0 直验 ②MimicMotion：README 直验「the 72-frame model requires 16GB VRAM (4060ti)…The minimum VRAM requirement for the 16-frame U-Net model is 8GB」+ICML 2025 逐字命中+LICENSE 原文=Apache-2.0（声明含「except for the third-party components」惯例条款·已读） ③Wav2Lip 判负主张直验成立：现行 README License 节原文「This repository can only be used for personal/research/non-commercial purposes」——判负结论维持；就地纠偏留痕：本件所引「any form of commercial use is strictly prohibited」为旧版措辞，现行文本表述如上、含义一致，星数未独立复核（以仓页读时快照为准）
