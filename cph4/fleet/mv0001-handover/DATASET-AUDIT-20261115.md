# 训练集体检报告 · 男女主/资产角色人脸集（2026-11-15 实测）

> 触发：给人物 LoRA 备料时先量了一遍现有两批人脸集，结论差得很远，先把证据留档，
> 免得下个会话又拿坏集去烧几小时 GPU。

## 一、结论

| 数据集 | 图像数 | dHash 重复对（≤20/256） | 判定 | 处置 |
|---|---|---|---|---|
| `media/mv-album-001-jay/mv0002-cast-work/lora-dataset/8_her` | 16 | **106/120（88%）**，中位数 9 | **FAIL 不可训** | 停用，改由设定图纸重造（见 §三） |
| 同上 `8_him` | 16 | **120/120（100%）**，含 1 对距离 0 | **FAIL 不可训** | 同上 |
| `media/asset/faces/CH01..CH08` | 各 12 | 0~2/66（0~2%），中位数 104~127 | 图像 PASS | caption 已重写后才可用（见 §二） |

dHash 是 16×16 差分感知哈希（256 位），同构图不同裁切/微表情通常 5~20 位，
不同构图/不同机位一般 60 位以上。上面两组「12 视角转面」的文件名和实际内容不符：
`HER-back_head` / `HER-profile_left` / `HER-low_angle` 全部是同一张正面中近景的近似重复。

## 二、CH01..CH08 的 caption 病灶与修法

- 病灶：12 条里有 9 条带 `background shows blurred cityscape` / `standing outdoors in natural
  daylight` 这类**场景词**——LoRA 会把环境一起学进角色，换场景就带虚影（11-09 已记过一次同型坑）。
- 病灶：首词各不相同（`Young Asian woman…` / `A young woman…`），没有可调用的触发词。
- 修法（`Tools/smoke/fix_lora_captions.py`）：真身描述一律取自正典设定表
  `cph4/fleet/asset-lib-v1/CHARACTERS-EN-v1.json`（role/face/hair/outfit 是设计事实），
  视角词由文件名映射，首词统一成 `ch0Nface`；原 caption 备份到各自 `_caption-bak/`。
- 结果：8 个角色 × 12 条 = 96 条重写，复跑体检 CH01/CH02/CH03 全 PASS。

## 三、坏集的正解：按设定图纸重造，不用成片帧

成片关键帧当训练集也不成立：实测 38 张 XQ 关键帧里只有 7 张能检出人脸
（`Tools/smoke/qc_identity_cluster.py`），双人镜的「最大脸」可能是男主也可能是女主，
按图取代表脸会把男女混在一起比，相似度必然低。

改用 `Tools/smoke/gen_cast_sheet.py`：同一身份描述块 × 12 个视角（景别×机位×表情×光位）
用 krea2 turbo 直出，再跑 `qc_identity_cluster.py` 把跑偏的脸剔掉，剩下来的才是能训的集子。
每张图配一条与图同名的 caption（触发词 + 景别 + 表情 + 服装 + 光位）。

## 四、机械闸（已入库，训练前必跑）

```bat
:: 重复度 + caption 场景词 + 触发词一致性，任一不过即 rc=2
K:\Fluxgroup\.tools\lora-venv\Scripts\python.exe Tools\smoke\qc_lora_dataset.py ^
    media\asset\faces\CH01 --token ch01face
```

判据：重复对占比 ≤10%、caption 零场景词、跨图首词一致。三项全绿才允许进
`krea2_cache_latents.py`——否则烧的是几小时 GPU 换一个只会出正面像的 LoRA。
