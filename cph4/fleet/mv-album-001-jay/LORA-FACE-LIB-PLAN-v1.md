# 单人面孔 LoRA 产线 v1（LORA-FACE-LIB-PLAN-v1 · 私有非商用）

> 令源：CEO 2026-11-12「你就给我生成单人 lora，我自己跑着玩不商用」「你 AI 产出来的，我个人感觉根本就不像」「法务合规专家不要加入评审」。
> 口径：**单人身份 LoRA · 本机私有 · 不发布 · 不商用 · 不外传**。此口径仅覆盖私有实验，产线正片仍走 CASTING-LAW（原创脸）+ CASTING-POOL-v1（气质族）。
> 承接：CHARACTER-LORA-STABLE-v1（双门）｜mv_lora_eval.py（六角度相似度闸）｜CASTING-POOL-v1（200 人索引）｜DE-AI-PLAYBOOK-v1（去 AI 感工艺，CEO 点名的重点）
> 素材闸：`Tools/face_lora_prep.py`　去 AI 感机检：`Tools/deai_metrics.py`

## 〇、为什么上一版「根本不像」——六个真因

上一版是**族平均**路线（多人合成一个气质族），设计上就**不可能像任何人**。这不是模型问题，是口径问题。换单人后仍会不像，若踩以下任意一条：

| # | 病灶 | 症状 | 正法 |
|---|---|---|---|
| 1 | 素材量不足 | 只有 8-15 张 → 只学到「一张照片」 | ≥40 张过闸（硬下限 20） |
| 2 | 素材太单一 | 全是同一角度/同一光/同一造型 | 角度四分法 + 四类光位各 ≥15% |
| 3 | 素材不清晰 | 截图/压缩/远景 → 学不到骨相 | 脸区 ≥512px，Laplacian 过闸 |
| 4 | caption 写错 | 把「大眼睛/高鼻梁」写进 caption → 身份进不了触发词 | caption 只写**非身份**内容（服装/场景/光/角度/表情） |
| 5 | 训练不足/过头 | rank 8 欠拟合；步数超量 → 烧脸、底模污染 | rank 32 / 1200-1600 步 / 每 200 步存档 |
| 6 | 推理只给文字 | 纯 prompt 出图波动大 | 加参考图锁（Redux/IP-Adapter 或 Kontext 编辑） |

**关键认知**：LoRA 学的是「素材里重复出现的差异」——素材越杂越像，越干净越像，越像证件照越呆。目标不是「拍得美」，是「信息够」。

## 一、工具链（GitHub 实测·2026-11-12 核）

| 用途 | 仓库 | 星 | 许可 | 本机定位 |
|---|---|---|---|---|
| LoRA 训练主力（Flux/SDXL/SD3） | kohya-ss/sd-scripts | 7,260 | Apache-2.0（LICENSE.md） | **主用**·`flux_train_network.py` / `sdxl_train_network.py` |
| 训练（新模型快·Krea2 线） | ostris/ai-toolkit | — | **MIT**（LICENSE 实读 2024 Ostris LLC） | 备选·Krea2/Flux 实验 |
| 一站式 GUI | Nerogar/OneTrainer | 3,266 | 接入前核 LICENSE | 不想写命令时用 |
| 多卡大吞吐 | ttddee/diffusion-pipe | — | 接入前核 | 单卡 12G 不用 |
| 人脸检测/关键点/embedding | deepinsight/insightface | 30,204 | MIT 代码·预训练权重非商用 | 素材闸 & 相似度（私有实验可用） |
| 画面质量评估（NIQE/BRISQUE/MUSIQ） | chaofengc/IQA-PyTorch | 3,448 | 接入前核 | 清晰度与 AI 感代理 |
| 去重 | idealo/imagededup | — | 接入前核 | pHash 已内置自写实现，够用 |
| 自动打标 | 1038lab/ComfyUI-JoyCaption | 335 | 接入前核 | 可选，默认走人工模板 |

寻源结论：训练面有成熟轮子（kohya 直接上），**素材筛选面没有能直接用的成品**（要么过重、要么绑云），所以自写 `face_lora_prep.py`，只做四件事：检测、过闸、去重、切图出配置。

## 二、素材标准（「她年轻时候」的量化定义）

| 项 | 判据 | 备注 |
|---|---|---|
| 年龄段 | 集中在目标期（如 18-26），跨度 ≤8 年 | 跨度过大=身份漂移，宁可少 |
| 数量 | 过闸 ≥40 张（下限 20，上限 60） | >60 只增过拟合风险 |
| 角度 | 正面 40% / 左 3-4 20% / 右 3-4 20% / 侧脸 10% / 仰俯 10% | 侧脸超 45° 不进训练集（可留作测试） |
| 光位 | 日光 / 室内暖 / 闪光硬光 / 夜景 各 ≥15% | 只有柔光=训练出的脸放不进任何场景 |
| 表情 | 中性 60% / 微笑 30% / 大笑 10% | 大笑过多会把「表情」学成身份 |
| 分辨率 | 脸区短边 ≥512px | 全身远景一律判负 |
| 清晰度 | 1024 归一后 Laplacian 方差 ≥ 标定线 | 阈值见 §四（首轮用正负控标定） |
| 禁项 | 重滤镜/磨皮/美颜/贴纸/水印/多人脸/遮挡>20%/压缩伪影 | 磨皮素材训出来必带 AI 感 |

广纳纪律：**先广后挑**——候选池 ≥120 张，过闸留 40-60，不达标不上训练。宁缺毋滥，20 张精料胜 100 张杂料。

## 三、训练配方（本机 RTX 4070S 12G）

| 项 | Flux 档（主） | SDXL 档（备） |
|---|---|---|
| rank / alpha | 32 / 32 | 32 / 16 |
| 学习率 | UNet 1e-4，TE 关 | UNet 1e-4，TE 5e-5 |
| 步数 | 1200-1600（每 200 存档） | 1200-1600 |
| batch / 分辨率 | 1 / 1024（bucket 开） | 1 / 1024 |
| 显存 | fp8 base + grad checkpointing | fp16 + grad ckpt |
| 选模 | 六角度相似度打分取最优 epoch | 同 |
| 触发词 | 固定稀词（如 `ohwx_woman`） | 同 |

caption 铁律（第 4 号病灶的解）：**只写不随人变的东西**——服装、场景、光线、角度、表情、画质。禁写五官、禁写体型、禁写年龄形容词。身份必须全部压缩进触发词，否则 LoRA 学不到人。

过拟合自检：触发词关掉后出图**不应**像目标人（像=底模被污染，立即回退上一存档）。同 prompt 换种子出 8 张，脸漂 → 欠拟合；8 张几乎一模一样 → 过拟合。

## 四、双闸（训完先过闸，过了才算有 LoRA）

**闸一·像不像（机检，复用 `Tools/mv_lora_eval.py`）**
- 六角度考卷：正 / 左 3-4 / 右 3-4 / 低角 / 侧脸 / 暖暗
- 判据：中位 SFace 余弦 ≥0.40、最差 ≥0.28（要更严可提到 0.45 / 0.32）
- 未过 = REVISE（补素材或调步数重训），不是「差不多能用」

**闸二·去AI感（人判 + 代理指标，CEO 点名重点）**
- 工艺口径与后期链顺序见 `cph4/fleet/quality/DE-AI-PLAYBOOK-v1.md`
- 机检：`python Tools/deai_metrics.py check <图或片> --baseline <真实基线.json>`（七项频域/噪声指标，偏离真实基线 ≥2σ 判 SUSPECT）
- 压力测试：同 prompt × 20 张，10 人盲评「这是 AI 吗」→ 判为 AI ≤2/10
- 代理指标：皮肤高频能量（蜡感）、高光裁剪比例、对称度、发丝碎片率
- 否决项：蜡感 / 平均脸 / 塑料皮 / 眼神无焦点 / 现代妆发穿越 —— 任一项命中直接打回，不进加权

## 五、群审七席（去合规席·去AI感与否决席）

| 席 | 看什么 | 权限 |
|---|---|---|
| 素材席 | 数量/多样性/年龄带/清晰度是否够信息量 | 建议 |
| 训练工程席 | rank/步数/lr/过拟合与欠拟合证据 | 建议 |
| **相似度席** | 六角度是否「像本人」（机检分只作参考，眼感最终） | 建议 |
| **去AI感席** | 蜡感/平均脸/皮肤/眼神/发丝 | **否决** |
| **年代席** | 妆发服装是否穿越到现代 | **否决** |
| 选角/面孔席 | 有没有记忆点、能不能当角色用 | 建议 |
| 导演席 | 进片能不能用、与词境是否匹配 | 建议 |

quorum ≥5 且 **去AI感席 + 年代席必须在场**。席位结论各自留档，禁一人代签全部。

## 六、一键流程

```bash
# 1 素材过闸（候选池先扫一遍，看够不够）
python Tools/face_lora_prep.py scan  D:\faces\<人物>\raw

# 2 生成数据集（裁脸/去重/出 caption）
python Tools/face_lora_prep.py build D:\faces\<人物>\raw \
    --out D:\faces\<人物>\dataset --trigger ohwx_woman

# 3 出 kohya 配置
python Tools/face_lora_prep.py config --dataset D:\faces\<人物>\dataset \
    --trigger ohwx_woman --base flux --out D:\faces\<人物>\train.toml

# 4 训练（kohya sd-scripts 目录下）
accelerate launch --num_cpu_threads_per_process 2 sd-scripts/flux_train_network.py \
    --config_file D:\faces\<人物>\train.toml

# 5 验收（六角度相似度）
python Tools/mv_lora_eval.py --lora D:\faces\<人物>\out\<name>.safetensors \
    --ref D:\faces\<人物>\ref\front.png --char her --out D:\faces\<人物>\lock.json
```

## 七、排产与工时（实测口径）

- 素材 120 张过闸（含人工取舍）：1-2 小时
- Flux LoRA 1400 步 @1024：约 1.5-2.5 小时/人（12G，夜间窗）
- 验收 + 群审：30 分钟
- **单人全流程 ≈ 半天**；首个人物含环境搭建，按 1 天算

## 八、失效条件（出现即停，别硬扛）

1. 过闸素材 <20 张 → 不出训练，先补素材（20 张以下的 LoRA 只能出「神似别人的脸」）
2. 六角度中位 <0.40 连续两次重训无改善 → 换素材源或换底模，别加步数硬磨
3. 盲评「是 AI」>4/10 → 回素材层查是否全是精修图
4. 触发词关掉仍像本人 → 底模被污染，回退存档并降 lr

## 九、素材自动采集（不用人给图）

```bash
python Tools/face_source_collect.py collect --person 徐若瑄 --pages 5 --target 45 \
    --min-side 600 --out media\faces\<人物>
```
一条命令：多关键词翻页取直链 → 下载 → 过闸 → `keep/` 与 `reject/` 分拣。**按「可用张数」循环补采**，不是凑下载数。

### 实测口径（2026-11-12 首例）

| 轮次 | 动作 | 结果 |
|---|---|---|
| 首轮 | 5 组关键词、110 张 | 可用 **14/110** —— 一半图没有人脸（`no_face` 55） |
| 修因 | 加必应 `filterui:face-portrait` 人像过滤 + 补关键词（高清/脸部/近照/剧照）+ 按可用数补采 | 见当轮回执 |

### 闸标定的两处修正（原先错在拿证件照标准套老照片）

1. 人脸短边下限 **384 → 200px**（老照片现实值；≥320 才算理想，低于只 WARN）
2. 清晰度改在**原生尺度**量（≤512 才降采样，禁放大后测）——放大插值会凭空造高频，把糊图量成清晰

### 四个已探明的通道事实（2026-11-12 实测）

- **360 图片 `image.so.com/j`：主力源**。JSON 接口、`pn` 翻页有效、单人总量 800+、几乎不限流。取 `list[].img` 原图地址；必须带 `Referer: https://image.so.com/`
- 必应图片 `cn.bing.com/images/async`：可用但**限流严重**（连续查询大量返回空页），仅作备源；结果卡片 `murl` 即原图直链，`qft=+filterui:face-portrait` 人像过滤有效
- 百度图片 `acjson`：封爬虫（`antiFlag:1`）；搜狗图片：`{"status":1,"info":"forbid"}`；DuckDuckGo `i.js`：返回 challenge —— 三个都不用
- 维基共享 API：可用且授权干净，但 90 年代华语艺人覆盖极少，只作补充
- Civitai 模型下载：多数已收紧，需 `CIVITAI_TOKEN`；无 token 会明确报错（不再写出坏件）

### 采集命中率的现实值

- 首轮（纯必应、无过滤）：可用 **14/110 ≈ 13%**
- 二轮（必应+人像过滤）：可用 **13/54 ≈ 24%**，但池子太小（大量查询被限流）
- 结论：**池子大小决定成败**，所以要 360 这种能翻页的大源；命中率 20% 意味着凑 45 张要备 220+ 条候选

## 十、2026-11-13 首次点火实操复盘（八个断点，全部已修）

首轮训练在 11:02 起跑后 35 秒静默死亡，日志停在 `caching latents...`，`output` 目录从未生成。复盘出八个断点，**都不是模型问题，是管线问题**：

| # | 断点 | 症状 | 正法 |
|---|---|---|---|
| 1 | 训练是临时手敲命令行 | 进程死后既无法续跑也还原不出参数（日志只剩被裁断的 `python sd...`） | 新增 `Tools/face_lora_train.py`（可复现，参数全落 argv） |
| 2 | `repeats = 1200/n` 配方错 | 40 张图要跑满 1200 步才过一个 epoch，`max_train_steps=1400` 实际只训 1.17 轮，身份学不进去 | `repeats` 恒为 1，epochs = steps / 图片数（40 张 → 35 epochs 正常量级） |
| 3 | caption 全数据集同一句 | 48 张 caption 完全相同（`guess_tags` 靠文件名猜，爬来的 `p0000.jpg` 永不命中）→ 模型把「这张脸+这套光」当固定搭配 | 新增 `detect_face_detail/pose_label/light_label/smile_label`，用 YuNet 5 点算头朝向、用脸部/背景亮度+色温算光位；40 张产出 11 种 caption |
| 4 | dataset `resolution` 写成字符串 | `resolution = "1024,1024"` 被 voluptuous 拒（`expected int`）——上次的 `resolution is required` 同源 | 必须是整数 `resolution = 1024`（bucket 处理长宽比） |
| 5 | `--num_repeats` 当命令行参数 | 该参数只存在于 dataset config，源码里没有 CLI 入口，传了即 unrecognized | 数据集描述全走 toml，训练超参全走 argv |
| 6 | `media/faces` 与 `media/lora` 实际未被忽略 | memory 记「已入 gitignore 并实测生效」是**假绿**，`git check-ignore` rc=1；700+ 张明星脸照片与 219MB 权重差点入库 | `.gitignore` 补 `media/faces/`、`media/lora/`，回验 rc=0 |
| 7 | 非管理员注册不了 S4U 任务 | `Register-ScheduledTask` 报 0x80070005（本机 `DASHENG\sjs20` 无 SeTcbPrivilege） | 改 InteractiveToken + `pythonw.exe` 承载，训练器给子进程加 `CREATE_NO_WINDOW`——同样零黑窗 |
| 8 | `pythonw` 下 `print` 直接崩 | 无窗口解释器 `sys.stdout is None`，任务一触发就静默死 | 入口先把 stdout/stderr 接管到 `face_lora_train_stdout.log` |

**同时修掉的假绿**：`register_lora_train_task.ps1` 原先 Register 失败仍照打 `[ok] 已注册`，现已改为回读 `Get-ScheduledTask` 校验、失败 `exit 1`。

### 本轮实测数据（徐若瑄·私有实验）

- 采集三轮（v2/v5/v6 室内向 + v8 户外向）：单轮命中率 **23%~29%**（360 源，比必应稳）
- 合并 77 张候选 → pHash 去重后 **41 张可用**（去重掉的 19 张全是跨轮重复）
- 排除侧脸 4 张 → 最终数据集 **40 张 / 11 种 caption**，daylight 17.5%（达标 ≥15%），暖室内 75%（老照片现实，缺闪光灯/夜景类）
- 训练配方：SDXL base 1.0 · rank 32 / alpha 16 · 1400 步 · fp16 + SDPA + grad checkpointing + cache_latents · 12G 单卡
- 点火方式：`bm-a-LoRATrain-her_xuruoxuan` 计划任务，工作日 19:05 起每 15 分钟巡检，让路态/显存不足自动拒跑，权重产出后自动跳过

### 验收前置（训完必须做，别急着说"像了"）

```powershell
python Tools/face_lora_train.py status --log C:\Users\sjs20\train-lora\train_her_xuruoxuan.log
# 六角度相似度（闸一）
python Tools/mv_lora_eval.py --lora <out>\her_xuruoxuan.safetensors --ref <定妆图> --char her --out lock.json
```
