# 星晴 A 批 GFPGAN 脸修 tier 部署注记 + S7 full-route 合并表（r1058）

> id=xq-GFPGAN-DEPLOY-r1058 · 2026-10-17 13:3x–14:0x · 执行=bm-c r1058（CEO 空闲填载令 13:0x 原话「本机算力严重空闲，给我去git找工作任务单，去跑新的MV，委员会和智能体给我监督好！」）
> 范围=POOL-0017 full-route（GFPGAN 脸修 tier）试跑定标 + clean-room 部署路线存档 + S7 遮瑕链路由合并表 + MimicMotion 部署 kit 同批收编（POOL-0016 夜3 提前腿）

## 一 GFPGAN 部署路线（clean-room 最小 shim，零污染 python_embeded）

- basicsr pip 构建不可行（其 setup.py 编 CUDA 扩展 + 本机无 CUDA toolkit）→ 自建最小 basicsr shim：utils（img2tensor/tensor2img）/registry/download_util/arch_util
- **img2tensor 必须带 float64→float32 前置转换**（承 basicsr 原版行为）：OpenCV 5.0.0 CvtHelper cvtColor 拒收 float64 ndarray——首轮 3/4 ENHANCE-FAIL 根因（S0-03 无脸未进该路径故幸存）
- gfpgan 三处补丁：`__init__` 只留推理专用（from .utils import GFPGANer）、archs 去 scandir 自动扫、utils 的 arch 改懒加载
- easydict 补装；facexlib 权重双位摆放（CWD 相对 gfpgan/weights + 包内 weights）
- pylibs --target 隔离装法，不动 python_embeded 正身（ComfyUI 产线零影响）

## 二 试跑结果（3/4 脸修复成功 · 2026-10-17 13:31–13:33）

| 帧 | 耗时 | 脸数 | 结果 |
|---|---|---|---|
| S5-30_s20222 | 0.94s | 1 | **FAIL**（大特写·上游磨皮不可逆·GFPGAN 补不回） |
| S0-03_s20027 | 0.12s | 0 | 无脸·原样保留（未进修复路径） |
| S1-09_s20064 | 0.60s | 2 | PASS |
| S0-06_s20048 | 0.37s | 1 | PASS |

- VRAM 峰 3574MB（16G 卡余量充足）·模型载入 1.7s·weight=0.5·upscale=1
- 对比板=xq-AB-GFPGAN-BOARD-r1058.jpg · 机读回执=xq-gfpgan-tier-receipt-r1058.json · runner=bmc_gfpgan_trial_r1058.py

## 三 QC 定谳（投产闸）

1. **可用作轻抛光/保险层，weight 0.5 合适**；单帧成本 <1s 可忽略
2. S5-30 类大特写 FAIL → 改道：CodeFormer（fidelity 0.7-0.8）A/B 对比 或 上游解磨皮（生成端处理）
3. 脸检 <32px 跳过阈值（远景脸修复无意义且放大伪影）
4. **投产前需时序闪烁测试（连续 3-5 帧过 GFPGAN 比对一致性）**——候星晴 A 批 i2v 点火后以实拍帧补测

## 四 S7 full-route 路由合并表（POOL-0017 合并面）

| S7 遮瑕变体 | 与 GFPGAN 脸修层的关系 |
|---|---|
| A=grain 0.14 普适链 | **可后置叠加**（轻抛光位·时序闪烁测试过门后生效） |
| B=高光肩压 knee209/slope0.62（治 S0 系油光） | **可后置叠加**（油光根因链独立·与脸修不冲突） |
| C=ESRGAN x4+LANCZOS 回缩（限 6 张无人物天空帧） | **不适用**（无人物帧·GFPGAN 无操作对象；SR 重绘身份风险已隔离） |

- 合并结论：full-route 脸修=按帧脸检路由（有脸且 ≥32px 才进 GFPGAN·weight 0.5·叠加于 A/B 链后·时序测试过门前不得投产）

## 五 MimicMotion 部署 kit（POOL-0016 夜3 提前腿 · 同批收编）

- 文件：dl_mimic_r1058b.py（主权重+DWPose 取件·断点续传）/ dl_svd_r1058.py（SVD fp16 底座预取·ModelScope 源）/ bmc_mimic_launcher_r1058.py（路径注入+DWPose CPU provider 覆盖+safe_globals monkeypatch+write_video shim 注入）/ bmc_mimic_trial_r1058.py（自等待试跑器·OOM 阶梯 72→48→24）/ decord-cv2-shim-r1058.py（cv2 后端 VideoReader shim）/ bmc_tv_writevideo_shim_r1058.py（av 写视频 shim）
- **SVD 底座需求勘误**：MimicMotion 的 UNet 权重来自 MimicMotion_1-1.pth 本体（loader 仅读 SVD unet 的 config.json）→ SVD 只需 vae fp16（186M）+image_encoder fp16（1.18G）+4 个 config 件 ≈1.4GB，**比原计划省 2.4GB**
- **SVD 取件通道定谳**：HF/ hf-mirror 上 stabilityai/stable-video-diffusion-img2vid-xt-1-1 为**门禁仓**（须网页接受许可+token，匿名 resolve 恒 403——本窗并发假说两轮证伪后实锚）→ 正源=**ModelScope stabilityai 同名镜像**（免门禁·国内直连·本窗实测 1.4GB 46 秒 ≈25MB/s）
- 试跑=官方 demo（pose1.mp4+demo1.jpg·576 分辨率·25 步·seed 42·零新生成）；**sample_stride=15 定谳**（=71 视频 pose+1 图 pose=恰 72 帧=单整砖——上游铺砖数学要求 num_frames ≥ tile_size，stride16 的 68<72 必炸 IndexError）；回执落 cph4/fleet/mv0001-handover/outbound/krea2/kf-demo-20261012/bmc/mimic_smoke_r1058/（随试跑毕上链）
- 许可旗标：SVD img2vid-xt-1-1 权重=Stability AI 非商业研究许可——内部试跑可用，**商业发布前须过许可审查**

## 六 本窗新坑录（机队通用）

1. **pythonw/无控制台进程 import diffusers 0.27 崩溃**：内置 print 对 sys.stdout=None 有 write 守卫但 **flush=True 无守卫** → `AttributeError: 'NoneType' object has no attribute 'flush'`。修法=脚本顶部 `sys.stdout/stderr is None → open(os.devnull,"w")` 双守卫（runner+launcher 均已焊）
2. **python_embeded `python313._pth` 隔离模式禁掉 PYTHONPATH 与脚本目录自动入 sys.path**——一切旁挂 pylibs/shim 必须 `sys.path.insert` 显式注入（GFPGAN 判例的机制级根因面）
3. **torchvision 0.28 移除 OSS 视频面**：`torchvision.io` 无 write_video/read_video（io/__init__ 只剩图像面+Meta 内部 fb import；残留 video.py 也是 fb 死桩）→ 依赖 `from torchvision.io import write_video` 的上游代码（MimicMotion save_to_mp4）须 launcher 级注入 av-shim（bmc_tv_writevideo_shim_r1058.py）
4. **torch 2.13 `torch.serialization.safe_globals` API 变形**（上下文管理器→装饰器类）——MimicMotion loader 的 `with safe_globals(*mods)` 用法 TypeError；checkpoint 为纯张量 weights_only 加载，no-op 上下文 monkeypatch 即正解
5. **MimicMotion 铺砖数学要求 num_frames ≥ tile_size**（indices 由 `range(0, num_frames - tile_size + 1, ...)` 构造，num_frames<tile_size → 空列表 → IndexError）——短测必须凑满帧数（本窗 sample_stride=15 凑 72）
6. **hf-mirror 门禁仓 403** 与下载并发限流是两型病：门禁=恒 403 有响应体；限流=403/SSL 超时与主流并存——先探 api/models/<id> 判 gated 再选源；**ModelScope 同名镜像=国内门禁仓首选替代源**（8-25MB/s 级）
7. **Get-CimInstance 进程探针自匹配假阳性**：探针命令行文本自身含模式串=匹配到自己（记忆在案的坑，本窗复踩一次——「runner alive」实为探针 powershell 自身）；判活必须排除自进程或以日志心跳为准
