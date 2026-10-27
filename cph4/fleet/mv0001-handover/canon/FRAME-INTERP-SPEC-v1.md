# 插帧技术案 v1（CEO 2026-10-13 令「可以插帧·研究相关技术·保证没有掉帧的感觉」·本地机队执法）

## 一、结论（调研定谳·双源）

| 方案 | 机制 | AI 生成片实测 | 判定 |
|---|---|---|---|
| ffmpeg minterpolate（现役） | **块级**运动估计：切块→猜块位移→混合插帧 | 糊边+块缝鬼影（"AI 片上锐利边缘正是质感来源，minterpolate 恰恰糊掉它们"——block ghosting 是判定特征）；本机 10-11 实测=warp 伪影 7/10 | **降级为预览档** |
| **RIFE（rife-ncnn-vulkan）** | 神经网络**像素级**光流：逐像素预测运动轨迹→合成中间帧 | 边缘保持锐利·零块缝（real-motion 训练）；720p 24fps 8s 片≈3 分钟/条（2x） | **V3 正档** |

证据源：①redeyeautomations.com 实测对比（193 帧→386 帧 A/B·minterpolate 版可见涂抹）②github.com/nihui/rife-ncnn-vulkan（单二进制+模型·Vulkan·无 Python/CUDA 栈）③ECCV2022-RIFE 原作（2080Ti 30+FPS@720p 2x）。

## 二、部署（本地机队·零云端）

- **载体=bm-c**（16G 3070·Vulkan·i2v 车道同机）：rife-ncnn-vulkan GitHub release 单 zip（≈10MB+模型）→ 解压即用；显存占用轻（~2-3G）·与 ComfyUI i2v 车道错峰或共存。
- bm-b（8G）备援第二工位；bm-a 夜窗可跑（CEO 白天用机期间禁）。

## 三、V3 装配链改造（掉帧感根治·工程细节）

1. **管线序**：源片 → ffmpeg 抽 PNG（无损输入=RIFE 效果更好）→ rife-ncnn-vulkan 2x → ffmpeg 编回 48fps → **setpts 慢放** → fps=24 统一（慢放插值律 O-20261011 执法升级：minterpolate 位→RIFE 位）。
2. **应用面**：一切 v<0.96 慢放镜（现约 20 条）+ D08 世界翻转/Z04 定格收等慢段落；**快剪段不过插**（24fps=2001 胶片质感本体·过度插帧反而毁年代感+伪影风险）。
3. **上限纪律**：插帧有天花板——高速/复杂运动段 RIFE 也会伪影；2x 安全·4x 须两遍或显式时间步+看片；PNG 中间件用毕即删（体积爆）。
4. **验收**：慢放镜逐条 ffmpeg 抽帧对比（插值帧边缘锐度）+盲评 ≥8（无顿挫无鬼影双判据）——成片闸匀速禁检配套。

## 四、执行序（今晚 GPU 窗）

①bm-c 装 rife-ncnn-vulkan（GitHub release 直链）→ ②用现役 V2 成片慢放段 A/B 验证（minterpolate 版 vs RIFE 版各一条）→ ③通过=V3 装配链切换 RIFE 位 → ④全片慢放镜重走插值链。

*导演席 · 2026-10-13 12:1x · 本地机队令执法·插帧令收口件*
