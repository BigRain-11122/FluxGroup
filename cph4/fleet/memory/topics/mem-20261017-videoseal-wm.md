# VideoSeal 隐形视频水印·bm-a 部署与判决（2026-10-17·O-20261017-1020 水印令）

> L2 主题文件（本机域细节）。L1 引用行待收尾 commit 字节补丁补挂（本机 append/update 记忆工具 project-scope EEXIST 在册）。
> 触发令：CEO 2026-10-17 11:0x「MV记得给我打上暗水印…内容是 大喵没鱼吃，不要影响画面，去github看看研究下」。

## 一、选型判决链（负结果全留档·勿重试）

1. **blind_watermark（guofei9987·DWT-DCT-SVD）→ 弃**。png 内存/PNG 往返提取全过，但 x264 视频编码全灭：crf16/22/28、yuv420p/444p、双嵌强度×2、Y 单通道共 20 组矩阵全 GARBAGE（诊断矩阵=`30s-reel-v1/wm_diag_r1017.py` 留档）。根因=其 kmeans 提取对 x264 量化+psy 天生脆弱，README 的 JPEG 抗性不迁移到 H.264。另实证其内部为跨通道分片结构（Y 通道均值法直接报 hex 错）。
2. **RivaGAN（DAI-Lab）→ 弃**。无预训练权重须自训 GAN（Hollywood2 300 epochs·Python3.7 古栈）；tucaodashen 产线的 TEXT_RIVAGAN=ONNX 随 GUI 工程自带，vendor 成本高。
3. **VideoSeal（facebookresearch/videoseal·Meta·MIT）→ 定谳**。pip 1.0.1、权重自动下载、256bit、is_video=True 时序一致、lowres_attenuation JND 感知衰减、逐帧软预测全片均值解码、抗 H.264 重压缩=训练目标（Meta 平台 provenance 实战）。

## 二、bm-a 部署坑律（comfyui embedded python 3.13.14 + torch 2.14+cu130·CUDA 可用）

1. `pip install videoseal --no-deps`（保护 ComfyUI 环境）+ 手补依赖：omegaconf/calflops/lpips/pandas/pycocotools/pytorch_msssim/scikit-image/tensorboard/**timm==0.9.16**（pin·原环境无 timm 无冲突）。
2. **decord 无 cp313 轮子**→`sys.modules.setdefault("decord", types.ModuleType("decord"))` stub 后再 import videoseal（官方 README 注 inference 可缺）。
3. **pip 包 CWD 坑**：cards（`videoseal/cards`）、configs、ckpts 全是相对路径，须**临时 chdir 到 site-packages 根**再调 `videoseal.load("videoseal")`（调回后权重缓存照常）。
4. **pip 包缺 `configs/attenuation.yaml`**（sdist 排除）：从 GitHub raw 抓取放进 `<site-packages>\configs\attenuation.yaml`（内容=4 组 jnd in/out channels，极小）。
5. 权重从 `dl.fbaipublicfiles.com/videoseal/y_256b_img.pth` 直下（国内网络可通·不走 HF）→ 落 `<site-packages>\ckpts\`。

## 三、生产工具与实证

- 工具=`cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/mv_videoseal_wm_r1017.py`（smoke/embed/extract/stress/psnr/board 六模式；16 帧分块 GPU 嵌入·cv2 解码→RGB→管道回编码·音频直拷）。
- 消息=「大喵没鱼吃」utf-8 120bit 装 256bit 槽（余位填零·提取按槽位约定无密钥交换）；逐帧全片嵌入=任何 ≥16 帧盗版片段可解。
- 冒烟实证（48 帧小样）：embed-PSNR **48.16dB**（对比 blind_watermark 35.29）；内存回环 100%；**crf22 编码回环 100% 原样读出**；crf28 小样 94.2%（仅 3 块软预测平均——全片 5622 帧=351 块平均会显著回升，全片实测为准）。
- 出库闸已入 PUBLISH-CHECKLIST §二（`_wmvs` 交付件+extract 全片 100%+stress 两级达标+发布文案「内嵌隐形水印盗用必究」声明=事前威慑补位）。

## 交付链序判例（2026-10-18 V5.7 交付窗）
- **N1 音频修复必须先于 watermark embed**：embed 管道 `-map 1:a -c:a copy`=音频从输入件**直拷继承**——喂未修件=水印成片带着超标 TP 出库。正序=视频定版→N1 音频修复件（*_n1.mp4）→embed（输入=N1 件）→四闸（extract 100%/stress crf23·28/psnr/目检板）→出库。
- 交付档 embed 参数=crf18/preset medium（冒烟与全片 PSNR≈47.4-48.2dB·三级解码 100%）；KFT 封面帧=四候选帧拼板判读选金字 bloom 峰值（39.60s·顶部暗带干净为硬条件）再叠鎏金曲名（PUBLISH-CHECKLIST §三 首选 KFT 的执行正法）。
