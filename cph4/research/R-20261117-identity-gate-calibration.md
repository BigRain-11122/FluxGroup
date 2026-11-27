# R-20261117 身份闸标定外部锚点（委员会第 69 批依据件）

**用途**：D-20261117-01 依据（SFace 身份闸 0.55 是否高于仪器量程 / B 路线可行性）。
**调研时点**：2026-11-17 00:0x。**性质**：外部公开文档直读，三条全部命中原文，无二手转述。

---

## 一、SFace 官方同人判定阈 = 0.363（三级），现行 0.55 超 51%

出处：OpenCV 官方教程 `tutorial_dnn_face.html`（dnn 模块人脸识别），原文：

> "For example, two faces have same identity if the cosine distance is greater than or equal to **0.363**, or the normL2 distance is less than or equal to 1.128."

同一页示例代码里该值写作 `cosine_similarity_threshold`，注释 "higher value means higher similarity, max 1.0"。

**判读**：我方 0.55 比官方校准线高 0.187（+51%）。这不是「更严」而是**超出仪器判读区间**——本管线自身的同提示词双种子只有 0.52，等于把闸设在噪声带之上，读数不可信（承 gate-rigor「阈值不得高于仪器量程」）。

## 二、InstantID / IP-Adapter FaceID = SDXL 专用，与 krea2（FLUX 系）不兼容

出处：InstantID 官方仓 README，代码如下：

```
pipe = StableDiffusionXLInstantIDPipeline.from_pretrained(base_model, controlnet=controlnet, ...)
base_model = 'wangqixun/YamerMIX_v8'   # SDXL
```

**判读**：正典第四节把 IP-Adapter FaceID / InstantID 列为「本机可行性=需装 custom_node」的提能力手段，但其预期 0.6–0.8 建立在 SDXL 基座上。我方 KF 源头为 krea2（FLUX 系），**直插这两条=无效工时**，除非整体换基座。

## 三、PuLID-FLUX 支持 FLUX 基座、12GB 可跑，但官方自陈男性身份保真不足

出处：PuLID 官方仓 Model Zoo：

| 版本 | 基座 | 官方描述 |
|---|---|---|
| PuLID-FLUX-v0.9.0 | FLUX | "ID fidelity is **not high enough for some male inputs**" |
| PuLID-FLUX-v0.9.1 | FLUX | 较 v0.9.0 "better ID fidelity… improvement is about **5 percentage points**" |

同仓 updates 段：「Local gradio demo supports 12GB graphic card now」；依赖含 insightface + antelopev2 + EVA-CLIP；`flux-dev-fp8` 需 PyTorch ≥ 2.4.1。

**判读**：三条提能力路线里只有 PuLID-FLUX 与本管线基座同源且 12GB 可跑；但官方明确点名「部分男性输入身份保真不足」，而本片主角为男性 → B 路线**不得承诺一次到位**，须预置「两轮不达即转云端身份参考出片」。

## 四、与仓内实测的交叉核对（不自证，仅对照）

| 项 | 数值 | 出处 |
|---|---|---|
| 管线自证天花板（同提示词三种子） | 0.68 / 0.47 / 0.52，中位 **0.52** | MALE-IDENTITY-CEILING-20261116.md §一 |
| 跨场景四镜 | **0.361**（换场景吃掉 0.16） | 同上 |
| 不同人（负控） | **<0.30** | 同上 |
| 显存 | 12282MiB 总 / **free 1813MiB**（00:00 实测，桌面常驻 ~10.2GB） | `nvidia-smi` 本轮直读 |
| krea2 int8 本体 | 12.57GB | 同上 §五 |

**结论支撑**：0.47（=0.52×0.9）落在「不同人 0.30」与「自证 0.52」之间且留 10% 余量，是可判读的有效闸；0.55 落在自证天花板之上，属不可达。

## 五、诚实边界

- 本节只取「阈值标定」与「方案可行性」两类事实，未调研观感侧的业界基准（CEO 眼感终审，非本轮射程）。
- 三条外部结论均随附原文引文；未能直读的（如 SFace 阈的标定方法学、PuLID 具体相似度数值）**未编造**，标注为「未取得」。
