# POOL-0016 night3 (pulled forward) - MimicMotion smoke tier receipt (r1058 FINAL)

> 2026-10-17 17:4x 手动收口·19:2x 盘面复核勘误定稿·bm-c r1058 交互窗·CEO 空闲填载令 13:0x 执行件
> 终态勘误定谳：前判「让路令（17:3x）到达时打断于解码尾段·出片未及」有误——试跑对实为 **17:30:30 跑毕自退**（16:46:49 修正版单飞起跑·去噪 57s+解码+save 全程 wall 2615s·恰于让路令前收官）：17:30:26 出片落盘+17:30:27 上游「--- Finished ---」+17:30:30 runner 自动写 PASS 回执/JSON/TRIAL-RESULT，进程消失被前窗误诊为 CLI 重启连坐击杀。**全链含出片 PASS tier=24·零补验需求**。三证=bmc_mimic_tier_r1058.json（status=PASS passed_tier=24）+runner log「TRIAL-END status=PASS」+出片实测（h264 384×640·15fps·71 帧·4.73s·487485B·ffprobe 解码计帧完整）。

## 一 部署面（全部定谳·全链可复现）

- 依赖：pylibs_mimic 隔离装（diffusers 0.27.0 + transformers 4.46.3 + hub 0.25.2 + tokenizers 0.20.3 + onnxruntime 1.31 CPU + omegaconf 2.4.0 + antlr4 4.9.3）——不污染 python_embeded 正身
- shim 三件：decord→cv2 VideoReader（demo 1059 帧实读验证）、write_video av-shim（torchvision 0.28 已移除 OSS 视频面）、safe_globals no-op monkeypatch（torch 2.13 API 变形）
- DWPose：CPUExecutionProvider 覆盖（本机 onnxruntime 为 CPU-only 包）；71 帧 pose 提取 25-32 秒（2.2-2.8 it/s）实测
- SVD 底座：**ModelScope stabilityai 同名镜像**（HF 门禁仓匿名 403 实锤→ModelScope 免门禁·1.4GB 46 秒·vae fp16 186M+image_encoder fp16 1.18G+4 config；UNet 权重由 MimicMotion_1-1.pth 本体携带·省 2.4GB）
- 试跑器：自等待（日志哨兵完成判定+自愈重拉）+OOM 阶梯+CREATE_NO_WINDOW 零窗+VRAM 采样

## 二 试跑实测（官方 demo：pose1.mp4+demo1.jpg·seed 42·零新生成）

| 档 | 结果 |
|---|---|
| 576·48 帧砖·25 步 | 去噪可跑（127-169s/步·峰 16.1GB·100% util）→ **解码段撞墙死**（分配器池钉死 16.1GB·free:0·反复 1.2-3.6GB 分配失败翻滚 26+ 分钟至 60 分钟帽被收） |
| 576·72 帧砖 | 显存可装（去噪期）·但与任何他 GPU 常驻共烧即 WDDM 分页爬行（双管线同卡实证·步 1 十分钟级）——本窗曾误诊为单管线过订阅·后经日志法证厘清为双 runner 并发污染 |
| 576·24 帧砖·6 步 | 去噪 24/24 全过·解码段同墙（24+ 分钟翻滚）判死止损 |
| **384·24 帧砖·6 步** | **全链 PASS 收官（17:30:30）**：去噪 24/24 步 57 秒（2.4s/it·零告警）+解码+save 纯算 wall 2615s（~43.6 分钟·零告警）·rc=0·runner PASS 闸（rc0+mp4≥100KB）双过·出片=outputs_tf24/pose1_20261017173026.mp4（487485B·h264 384×640·15fps·71 帧·4.73s·ffprobe 解码计帧完整；71 帧对 72 pose 预期差 1·解码完整非断尾） |

## 三 TIER 定谳（POOL-0016 交付判据）

1. **576 分辨率档在本卡不可产**：解码段为墙（解码成本与砖数无关——同 72 帧·同 8 帧块·同全分辨率 GB 级激活·叠加已钉死的分配器池）
2. **384 分辨率档全链可跑（本烟测已全程实跑收官·17:30:30 PASS）**：去噪 2.4s/步·零告警；解码+save 实测 wall 2615s≈43.6 分钟（时间 VAE 重活·3070 算力面）——短插镜可用·全片 MV 级动捕重定位判非本卡产线主力（整片需夜窗预算或更大卡）
3. 25 步官方档即便在能跑的窗型下=127-169s/步≈2.35h/砖——官方档全片级在本卡不现实
4. MusePose 对照腿仍候 10-18 夜窗（原计划不变）
5. 许可旗标：SVD img2vid-xt-1-1=Stability AI 非商业研究许可——内部试跑可用·商业发布前须过许可审查

## 四 坑录 7 枚（正典=xq-GFPGAN-DEPLOY-r1058.md §六）

pythonw flush 守卫 / _pth 禁 PYTHONPATH+脚本目录 / torchvision0.28 视频面移除 / torch2.13 safe_globals 变形 / 铺砖帧数下限（num_frames≥tile_size）/ hf-mirror 门禁仓 403→ModelScope 正源 / 探针自匹配假阳性
