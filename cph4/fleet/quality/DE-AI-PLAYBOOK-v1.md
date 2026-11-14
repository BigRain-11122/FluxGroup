# 去 AI 感工艺手册 v1（DE-AI-PLAYBOOK-v1）

> 令源：CEO 2026-11-12「AI感 AI脸什么的，好好给我调研，尤其去开源社区找工具和经验，工作流什么的，给我好好去掉」。
> 与 DE-AI-SPEC-v1 的分工：**SPEC=判据（判什么）· 本件=做法（怎么消）**。冲突以 SPEC 为准，本件不另立阈值。
> 机检工具：`Tools/deai_metrics.py`（七项频域/噪声指标 + 基线标定）　人判：导演席盲评
> 素材前置：`LORA-FACE-LIB-PLAN-v1.md`（数据集脏=后期救不回来，这是第一性）

## 一、先讲清楚：AI 感是四个物理层偏差，不是一个「味道」

| 层 | 物理事实 | 人眼看到 | 我们的对策层 |
|---|---|---|---|
| **L1 高频缺失** | 扩散损失偏好低频一致，微纹理（毛孔/角质/杂发/织物纤维）被抹平 | 「蜡」「塑料」「糊」 | 数据集 + 微纹理 LoRA + Detail Daemon + 颗粒 |
| **L2 光学不成立** | 没有真实镜头缺陷：无色散、无暗角、无渐进失焦、无快门模糊、星芒形状假 | 「一眼假」「像贴上去的」 | 物理后期链（CA/暗角/bloom/运动模糊，顺序固定） |
| **L3 噪声谱不对** | 真实相机噪声=传感器噪声×CFA插值×JPEG量化；扩散输出噪声是结构化的，Nyquist 附近留峰 | 说不出哪里怪，但「不像照片」 | 重采样退火 + 真实 ISO 噪声 + JPEG 二次压缩 |
| **L4 统计过于完美** | 对称、平均脸、整排牙、瞳孔高光同形、手指等长 | 「AI 脸」本体 | 不对称提示 + 真实样本 LoRA + 局部 inpaint |

判据含义：**只做后期颗粒 = 只补了 L3 的一半**，L1/L2/L4 照旧，所以「加了噪点还是 AI」。四层要分别打。

## 二、生成前（收益最大，改这里最省算力）

### 2.1 底模与 LoRA
- 底模：Flux dev / Krea2（本线现役）；**SDXL 系只出构图草稿**（SPEC B5 已定谳）
- 必挂真实感 LoRA：社区通用做法是 FLUX 真实感 LoRA（XLabs 系 RealismLora 家族）+ 微纹理/胶片颗粒 LoRA；强度 0.35-0.6，过高会吃掉人脸结构
- 数据集必须含"瑕疵"：毛孔、杂发、轻微不对称、非完美牙——**训练集里没有的东西，模型生不出来**

### 2.2 提示词（关键：正向锚挤位，少写否定）
正写相机与胶片，不写形容词：
```
shot on 35mm film, Kodak Portra 400, 50mm lens at f/2, slight underexposure,
visible pores, fine stray hairs, subtle skin texture, natural asymmetry,
one eye slightly smaller, faint under-eye shadow, slight motion blur in hair,
soft window light, film grain, halation around highlights
```
禁用词（这几类是 AI 感放大器，写进去模型就去追那个味道）：
`8k / ultra detailed / masterpiece / hyperrealistic / perfect skin / flawless / airbrushed / beauty / bokeh balls / HDR`

### 2.3 采样
- Flux guidance 2.5-3.5（>4 开始硬、塑料）；步数 28-32
- 高分辨率放大改道：**不要单纯 latent upscale**（会在 Nyquist 留峰）→ 用 SUPIR 或分块重绘
- **Detail Daemon**（muerrilla 190★·A1111 扩展，ComfyUI 有移植）：`detail_amount` 正数加细节、负数更平滑。蜡感 → +0.3~+0.6 并把步数压低；过锐 → 负值。它改的是采样时的噪声调度，比后期锐化干净

## 三、生成后（物理后期链·顺序固定，顺序错=白做）

顺序原理：先修色彩空间，再加光学缺陷，最后才加颗粒与压缩。颗粒必须先于 JPEG，否则颗粒被当成噪声抹掉。

```
1) 解码/色彩统一 → 线性工作空间
2) 胶片模拟 LUT（Kodak 2383 / Portra 风格 .cube）——先定色，后加光
3) Halation（高光溢出）：阈值提亮→模糊→screen 叠加，暖色偏移
4) Bloom（轻，0.1-0.2）
5) 色散 CA：径向通道位移，画幅边缘 0.5-1.5px（中心为 0）
6) 暗角：cos^4 衰减，幅度 8-15%
7) 运动模糊（仅在需要时，方向性，2-6px）
8) 颗粒（最后一道加法）：逐帧变化，强度按 ISO 映射
9) JPEG 二次压缩 q88-92 + 4:2:0 色度下采样
10) 禁锐化（unsharp/sharpen = AI 感放大器）
```

ffmpeg 可直接落地的片段（按需拼，非一条通吃）：
```bash
# 胶片颗粒（t=时间变化 u=均匀）：强度按画幅与 ISO 调，起手 6-10
-vf "format=yuv420p,noise=alls=8:allf=t+u"

# 色散（边缘通道位移）
-vf "rgbashift=rh=1:bh=-1"

# 暗角
-vf "vignette=PI/5"

# 胶片 LUT
-vf "lut3d=kodak2383.cube"

# 二次压缩（照片感的关键开关）
-c:v libx264 -crf 18 -pix_fmt yuv420p
# 静帧则: ffmpeg -i in.png -q:v 3 out.jpg  （JPEG q≈90）
```

## 四、七项机检指标（`Tools/deai_metrics.py`）

| # | 指标 | 物理含义 | AI 方向 |
|---|---|---|---|
| M1 | noise_sigma | 高通残差的中位绝对偏差=传感器噪声底 | AI 偏低 |
| M2 | hf_ratio | 高频（>0.35 cyc/px）能量占比=微纹理量 | AI 偏低 |
| M3 | spectral_slope | 径向功率谱 log-log 斜率（自然像 ≈ -2） | AI 偏离 -2 |
| M4 | nyquist_peak | 0.42-0.5 环 / 0.2-0.3 环 能量比=重采样棋盘伪影 | AI 偏高 |
| M5 | chroma_noise | 色度高通 / 亮度高通=CFA 与色噪 | AI 偏低 |
| M6 | lap_var | 拉普拉斯方差（整体锐度） | AI 常偏高（过锐） |
| M7 | clip_ratio | 高光/死黑裁剪占比 | AI 偏高（HDR 味） |

**阈值不许拍脑袋**：先跑 `--calibrate` 用真实照片集（真人年代照片/MV 实拍帧）出均值与标准差，AI 图偏离 ≥2σ 才判 SUSPECT。基线文件入 canon，跨机复用。

## 五、验收（顺序不能反）

1. **机检**：七项相对真实基线，SUSPECT ≤1 项
2. **检测器复核**（可选）：开源取证模型（UniversalFakeDetect / NPR 系）判 AI 概率降到真实区间；**只作旁证**，不作为唯一依据（探测器会被新模型绕过，人眼才是终审）
3. **盲评（终审）**：10 人、只看图不听解释、问「这是 AI 生成的吗」→ 判 AI ≤2/10
4. **CEO 眼感**：最终门（他的原话「我自己感觉根本就不像/很烂」=判负，不看我们机检多绿）

## 六、群审席位（去合规席）

| 席 | 职责 | 权限 |
|---|---|---|
| 去 AI 感席 | 四层逐一验（L1-L4），蜡感/平均脸/塑料皮 | **否决** |
| 版面/后期席 | 后期链顺序与参数是否对、有无锐化 | 建议 |
| 年代席 | 形制与调色是否穿越 | **否决** |
| 摄影席 | 光学是否成立（光源/景深/高光） | 建议 |
| 导演席 | 成片能不能用 | 建议 |

quorum ≥5，**去 AI 感席 + 年代席必须在场**。

## 七、工具表（GitHub 实测·2026-11-12）

| 用途 | 件 | 星 | 许可 | 用法要点 |
|---|---|---|---|---|
| 细节量控制（反蜡感主力） | muerrilla/sd-webui-detail-daemon | 190 | 接入前核 LICENSE | `detail_amount` 正加细/负平滑 |
| 真实感放大（替代 latent upscale） | Fanghua-Yu/SUPIR | 5,698 | 接入前核 | 分块+低 denoise，宁可慢 |
| SUPIR 的 ComfyUI 封装 | kijai/ComfyUI-SUPIR | 2,315 | 接入前核 | 节点式接入现役流 |
| 画质评估（NIQE/BRISQUE/MUSIQ） | chaofengc/IQA-PyTorch | 3,448 | 接入前核 | 与我们的七项并用 |
| AI 取证旁证 | UniversalFakeDetect / NPR 系（学术件，星数低） | — | 研究用途 | 只作旁证，不作判据 |
| 底模真实感 LoRA | XLabs RealismLora 家族（权重不托管在 GitHub） | — | 权重许可单独核 | 0.35-0.6，过高吃结构 |

诚实边界：Civitai / Reddit 的一线调参经验本轮**未能直接抓取**（DuckDuckGo 反爬拦截，两次尝试均空）；本手册的工艺结论来自**仓库一手件 + 频域可验证事实**，不引用未验证的"大佬配方"。抓取通道恢复后补一轮社区参数对照，回填 §2.3/§3。

## 八、失效条件

1. 机检全绿但盲评判 AI >4/10 → 指标不覆盖该病灶，**立刻新增指标**，不许调阈值凑绿
2. 靠加颗粒掩盖蜡感 → 判负（颗粒补 L3 不补 L1）
3. 后期链顺序错（先颗粒后 LUT）→ 重做，不叠加补救
4. 用锐化"提质感" → 直接判负（AI 感放大器）
