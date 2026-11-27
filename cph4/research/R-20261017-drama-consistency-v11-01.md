# R-20261017-drama-consistency-v11-01 — 《一路长虹》v1.1 人物一致性升级评估（StoryDiffusion 双仓研审 + LoRA 自蒸馏路线定谳）

> 溯源：CEO 令 2026-10-15 17:2x「人物的一致性是重中之重，受众群特别看重的！如果你做不好，可以继续训练lora，或者去github等地方找现成的」（BigStream 长期律）；消费方=批一呈报残留清单（anything-v3 代际残留=R-20261017-drama-ep-qc-anchorfix-01 §十）+ 60 集收官后 v1.1 烧制器升级。
> 验证声明：代码结论=2026-10-17 对盘上克隆仓实读（media/drama-tools/repos/·gitignored）；五门基础=R-20261015-drama-oss-stack-01（StoryDiffusion 6.5k★/停更 2024-09、ComfyUI_StoryDiffusion 518★/2025 仍推、一致性正解=LoRA 为主工具为辅——零重复调研，本件只做代码级深化+落地路线）。
> 现役链参数正身：anything-v3.0-pruned-fp16（SD1.5 系）·512×768·24 步·CFG7·确定性种子 91000000+ep*100+n·expand_c CLIP 预算层（drama_ep_burn.py 实读）。

## 一、现役链体检（v1.0 一致性机制盘点与天花板）

| 机制 | 状态 | 说明 |
|---|---|---|
| 文本锚（expand_c 压缩锚） | 已拉满 | 每人物 10-12 词骨相/服装锚前置+STYLE_C 13 词，1236 镜 max 71 tok 全绿；批一验=画风统一+XIONG 三签名全中 |
| 确定性种子 | 在役 | 同镜可复刻，跨镜无一致性贡献 |
| 视觉参照/注意力共享/LoRA | **零** | v1.0 唯一一致性来源=文本 |

**天花板实锚（批一 QC 残留）**：年龄词遵从弱（young man 22 → 偏嫩脸）·双人组合偶错位（服装串人）·场景词偶漂。根子=anything-v3 代际老（2023 底模·CLIP ViT-L 文本面弱）+纯文本锚无像素级人物参照。**结论：文本锚已到 CLIP 预算内工程极限，v1.1 必须引入视觉一致性机制。**

## 二、候选路线评估（四路线）

### 路线 A：StoryDiffusion CSA 移植（training-free·「找现成轮」面）
| 项 | 判定 |
|---|---|
| 原理 | Consistent Self-Attention：同批 N 张图在 UNet self-attn 层共享 K/V，批内人物脸/服装互参锁一致（NeurIPS 2024） |
| 正身代码 | **app.py L66 `SpatialAttnProcessor2_0`（~100 行·torch2 sdp·跨批 K/V）+ `set_attention_processor`（挂 up_blocks attn1）+ utils/gradio_utils cal_attn_mask**——模型无关 hot-pluggable；README 明言「compatible with all SD1.5 and SDXL-based models」→ anything-v3 可直接挂 |
| 克隆瑕疵 | 根 storydiffusionpipeline.py=**0 字节空壳**；utils/pipeline.py=PhotoMaker SDXL 参照管线（非 CSA）→ 移植唯一正身源=app.py |
| 8G 可行性 | SD1.5 512×768 批 6-8 张 fp16 ≈3-4G —— bm-b 8G 可跑 |
| 能力边界 | ①CSA=批内一致；**跨集一致需「参照批」注入**（正典三视图 noised 至 t 步混入批内；SDXL low_vram app 已用 id 参照思路，SD1.5 notebook 未实现=自写 SDEdit 注入·工程量小）②仓停更（代码成熟无依赖风险·Apache-2.0）③动漫底模无公开先例=必须冒烟验 |
| 适配面 | 烧制器按「人物组合签名」分组批烧（同组合镜一批），与 expand_c 文本锚叠加零冲突 |

### 路线 B：ComfyUI_StoryDiffusion 节点群（smthemex）
| 模式 | 判定 |
|---|---|
| story（photomaker v1/v2） | SDXL 向+真人照片训练——SD1.5/anything-v3 不适配·漫画风脸适配存疑 → **判负** |
| classic（多角色 CLIP 拼接 77×N） | 纯文本面增强（无视觉锁）且与我们 77-token 预算层路线冲突 → 只取思想不装机 |
| Flux 系（UNO/InfiniteYou/DreamO/PuLID/OmniConsistency） | 需 Flux 级显存（8G 装不下或极慢）+真人向 → **判负** |
| 结论 | 对 SD1.5 线价值有限；**采其多角色 cond 管理架构思想，不装机** |

### 路线 C：角色 LoRA 自蒸馏（五门研报既定主线·CEO 亲点「训 lora」）
- 训练器=GitHub 高星现成轮 kohya sd-scripts（SD1.5 LoRA 512px rank8-16·8G 卡可训·bm-b 本机即训；装机时按律先验星数/license）
- 数据自举=新管线图池各角色最稳帧（批一已验帧+批二起逐批验收帧），每角色 20-30 张（脸/半身多视角），逐字 trigger（changhong/xiong/mancang/hongli）
- 烧制器消费=expand_c 头锚换 trigger 词+LoraLoaderModelOnly 挂载——**跨集/跨批一致（权重全局生效）**，年龄/服装串色类残留一并压
- 风险=自举数据集小（20-30 张/角色）→ 过拟合走样；对策=低 rank/低 dim+多视角采样+单角色单训+验证板（4 场景×3 强度）

### 路线 D：IP-Adapter FaceID（SD1.5 plus v2）——判负备选
真人脸向训练·动漫脸适配差·每镜带参照图装配面复杂化——不采，留真人间短剧线备援。

## 三、定谳：A 验证先行（零成本快赢）·C 主线正解（跨集一致）

1. **A=冒烟单**：CSA 移植（app.py 百行处理器+挂载函数）→ 同角色 4 镜批 vs 现役 4 镜基线盲评；≥9/10 → 进 v1.1 作「双人组合镜/主角重镜」批内锁辅助面
2. **C=主线**：批一/二池稳定后建 CH/XTC/MC/HL 四角色数据集 → kohya 训 LoRA → EP001-003 三集试点重烧（对照现役版）→ 跨镜比对板验收 → 全线切 LoRA 烧制
3. 验收判据（两轨通用）：同角色跨镜比对板（≥3 镜并排）盲评 ≥9/10 + 年龄违例/服装串人=0；试点=EP001-003 重烧对照
4. **GPU 排班律：一切冒烟/训练排在 60 集烧制收官之后**（产线优先·单车道律）；LoRA 训练窗=夜窗 bm-b 独占

## 四、落地工单（收官后执行序）
| # | 工单 | 产出 |
|---|---|---|
| 1 | CSA 冒烟：venv(--system-site-packages 复用 comfy 便携 torch)+diffusers+anything-v3 挂 SpatialAttnProcessor2_0 | 冒烟板+verdict |
| 2 | 参照批注入（正典三视图 SDEdit t 步混入） | 跨集一致验证板 |
| 3 | 角色数据集收割脚本（图池→角色帧分拣/裁切/打 trigger 标） | 四角色数据集 |
| 4 | kohya sd-scripts 装机（星/license 双查）+首训 CH | LoRA v0+验证板 |
| 5 | drama_ep_burn.py 挂 LoraLoader 分支+trigger 词换头部锚 | v1.1 烧制器 |
