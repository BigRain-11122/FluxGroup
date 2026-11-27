# WM-VERIFICATION-RECEIPT-r1017 — MV 暗水印「大喵没鱼吃」代理版四闸验证回执

> CEO 令 2026-10-17 11:0x「MV记得给我打上暗水印…内容是 大喵没鱼吃，不要影响画面…去github看看研究下」·执行 bm-a。
> 选型判决链（负结果留档）：blind_watermark DWT-DCT-SVD→x264 全灭（wm_diag_r1017.py 20 组矩阵）；RivaGAN 无预训权重；**VideoSeal（facebookresearch·Meta MIT）定谳**。
> 实测对象：full_mv_v51_proxy_wmvs.mp4（V5.1 代理版 540P·5622 帧·crf22·音频直拷·GPU 嵌入 67s）。

## 四闸结果（2026-10-17 11:3x-11:4x 全绿）

| 闸 | 判据 | 结果 |
|---|---|---|
| ① 全片解码 gate | bit-acc vs 「大喵没鱼吃」120bit 槽位 | **100.0%** |
| ② 平台重压 L1 | 960×540 re-encode crf23 后解码 | **100.0%** |
| ③ 恶劣档 L2 | 960×540 re-encode crf28 后解码 | **100.0%**（48 帧小样 94.2%→全片 351 块软预测均值拉满） |
| ④ 视觉透明性 | 最坏情形目检板（纯黑/内容/金字黑底/收尾黑 4 帧×多模态） | **4/4 肉眼不可辨**·嵌入 PSNR 48.16dB·残差 1-3 级（峰值 4）在胶片颗粒底噪下·JND 衰减参数保持现状 |

## 取证解码法（盗版追责用）

```
PY = C:\Users\sjs20\comfyui-krea\ComfyUI_windows_portable\python_embeded\python.exe
& $PY cph4\fleet\mv0001-handover\outbound\krea2\30s-reel-v1\mv_videoseal_wm_r1017.py extract <疑似盗版视频.mp4>
# 输出 DECODE bit-acc=xx% text='…'（消息=「大喵没鱼吃」utf-8 120bit 装 256bit 槽·余位零·逐帧全片嵌入）
```

- 嵌入法（终版出库）：同脚本 `embed <in.mp4> <out.mp4> [crf] [preset]`——终版 768P 用 crf 17/preset medium。
- 出库闸=脚本 extract 全片 100% + stress 两级达标（PUBLISH-CHECKLIST §二）。
- 发布文案威慑句（声明面）：「本片内嵌隐形版权水印，盗用搬运必究」——纯暗水印仅事后取证力，声明补事前威慑。

—— bm-a · 2026-10-17 11:4x
