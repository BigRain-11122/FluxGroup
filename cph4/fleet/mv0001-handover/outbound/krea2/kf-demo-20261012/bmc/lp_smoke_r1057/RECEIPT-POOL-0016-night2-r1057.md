# POOL-0016 夜窗第 2 夜回执 — LivePortrait 表情迁移实测（bm-c r1057·2026-10-17 02:0x-02:2x）

> 三夜计划（10-16/17/18·每晚一工具）之**夜 2=LivePortrait**。夜 1（LatentSync/MimicMotion）无回执在案；夜 3（MimicMotion/MusePose 对照）待 10-18。GPU 与日间烧制错峰=夜窗执行 ✓

## 一、跑成两件

| # | 件 | 内容 | 判定 |
|---|---|---|---|
| 1 | `lp_smoke_r1057_00001_.png` + `lp_smoke_receipt_r1057.json` | 自驱动恒等重建烟测（源=驾驶同图·单帧）——FaceAlignment/blazeface→torch landmark→motion extraction→warping→spade 全链过 | **PASS**（输出 512 裁块重建·多模态复检无撕裂/无融合/无结构缺陷） |
| 2 | `lp_expr_night2_r1057.mp4`（1344×768·72 帧·3.0s·459KB·-an）+ `expr_frames/`72 帧 + `lp_expr_receipt_r1057.json` | 表情迁移样片：源=C01_carver_face 静帧@1.0s·驾驶=C01_carver_face_v5.mp4 前 72 帧——静帧身份+驾驶片表演 | **PASS**（头姿+口型随驾驶真动·零伪影零变形·身份一致；幅度微妙=忠实还原驾驶源本身的微妙表演） |

## 二、实测档位（bm-c RTX3070 16G·ComfyUI 0.36.0·torch 2.13）

| 指标 | 冷烟测（含模型冷载） | 热跑 72 帧迁移 |
|---|---|---|
| 墙钟 | 652.88s（其中 **614s=一次性 91.9MB 权重下载**@hf-mirror 150-300kB/s） | **35.55s = 0.49s/帧** |
| 显存峰（nvidia-smi used） | **16060MB**（torch 缓存分配器冷载瞬时占满·prompt 尾已释放·闲时基线 1774MB） | **3681MB** |
| 权重六件 | appearance 3.36MB / motion 112.5MB / warping 182.2MB / spade 221.8MB / stitching 0.9MB / landmark 114.9MB（字节账入 smoke receipt） | 同左已驻 |

**读法**：冷载显存峰 16GB 是 torch 分配器瞬时行为非稳态；热态真峰 3.7GB=16G 卡富余充足，夜窗跑 512 档多人脸批无压力。

## 三、合规面（R-stack L23 障碍→已解）

- 检测走 **FaceAlignment blazeface_back_camera（BSD3）+ landmark_model torch_gpu**；mediapipe / onnxruntime / **InsightFace 全家零引入** → R-stack 记的 InsightFace「non-commercial only」红线**绕开**（不换也能商用·因为根本没用它）。

## 四、接线律（本窗踩坑定谳·后续照此接）

1. **driving 帧必须先过 Cropper 预裁脸**：Process 节点对 driving 强缩 256×256 且**无内部检测**——喂原始全幅帧=脸缩成渣。正法=双 Cropper 接线（源静帧一张 Cropper + 驾驶帧批一张 Cropper），官方视频示例同构。
2. **Process 返回的是 512 裁块**：贴回原幅必须再过 **LivePortraitComposite** 节点（单静源自动复用于 N 帧）。
3. torch≥2.6 weights_only 默认坑：blazeface 权重加载需 safe_globals allowlist（blazeface_detector.py 已补）·landmark_runner.py weights_only=False。
4. ComfyUI 0.36 目录型节点按**全路径**注册 sys.modules：节点包内相对导入必须用 `__package__`（api.py 已修）。
5. 首发慢下载 91.9MB@10 分钟：torch hub checkpoints 预下正法（blazefaceback.pth 594KB+anchorsback.npy 28.8KB 已入位）。

## 五、瓶颈注（不变）

工具已通=真瓶颈回到**表演参考片库**（R-stack 盲区②）：真人歌手特写/强表演参考片不建库，迁移无处发力——下窗候选=参考片库立项。

## 六、升格

R-20261015-mv-performance-stack §四应用表「表情表演 | LivePortrait」行：障碍待解 → **直接可用**（本回执为据）。
