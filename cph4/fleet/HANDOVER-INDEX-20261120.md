# 交接包落地索引 v1（2026-11-23 · bm-c）

> 来源：`C:\Fluxgroup\handover-selfmedia-20261120\`（生产力机 DASHENG 导出的自媒体资产）
> 清单原件：`交接清单.md`（7 包 / 17.45 GB 设计口径）
> **实际到达：3 包 / 0.5 GB**（01/03/04/07 四个包不在本机）

## 一、到达情况

| 包 | 设计大小 | 到达 | sha256 |
|---|---:|---|---|
| 01-内容线代码与文档 | 2.31 GB | ❌ **未到达** | — |
| **02-MV与短视频成品** | 0.20 GB | ✅ | `ee406171…` SHA-OK |
| 03-人脸语料与角色LoRA | 7.66 GB | ❌ **未到达** | — |
| 04-音源MUSIC | 3.19 GB | ❌ **未到达**（版权件） | — |
| **05-角色LoRA与关键帧试验** | 0.29 GB | ✅（有一份带时间戳的重名副本） | `5383ac6f…` SHA-OK |
| **06-漫剧工具链** | 0.03 GB | ✅ | `a554ad32…` SHA-OK |
| 07-可复用资产库 | 3.78 GB | ❌ **未到达** | — |

> 缺的四个包（尤其 03 人脸语料 7.66G / 04 音源 3.19G / 07 资产库 3.78G）如果要，得再传一次。

## 二、解压落地位置（按清单建议的 `media\...` 层级）

| 包 | 落到 | 规模 |
|---|---|---|
| 02 | `media\MV\`, `media\mv-test\`, `media\covers\`, `media\drama-pilot-in\`, `media\meme-daily-v1\`, `media\mv-album-001-jay\`(10 件) | 约 1.2 GB |
| 05 | `media\lora\`, `media\kf-ab\`, `media\mv-test\` 部分 | 约 340 MB |
| 06 | `media\drama-tools\` + `media\drama-tools\repos\index-tts`（已挪走，见下） | 38.6 MB |

## 三、有价值的东西（分类）

### A 级 · 直接补上我们的缺口

| 件 | 位置 | 为什么值钱 |
|---|---|---|
| **爱在西元前 版本镜头全集** | `media\MV\mv0001\`（cloud-v4 / v718-v730 / xingqing / v5redo / jayredo） | 这是 v730 那 76 镜的实际素材——**之前卡在「拿不到 bm-a 的片段」的正是它** |
| **IndexTTS 源码** | `K:\Fluxgroup\.tools\index-tts`（22 项·含 infer/infer_v2/infer_v2_5） | 多角色配音的另一条腿（权重未随包，需另下） |
| **2000s Flash Portrait LoRA** | `media\lora\readymade\2000s_Flash_Portrait.safetensors`（219 MB） | 2000 年代人像风格锁——MV/短剧的年代底可直接用 |

### B 级 · 素材库

| 件 | 位置 | 说明 |
|---|---|---|
| 龙卷风选角片 | `media\MV\mv0002\cast-her-20261103\` | 女主候选 |
| 星晴（mv0001\xingqing） | 724 件 / 588 MB | 星晴 PACK-A/B 的中间件 |
| 关键帧试验 | `media\mv-test\{keainvren,xingqing,check-20261102}`、`media\kf-ab` | AB 对照 |
| 封面 | `media\covers\{fanren-bs-bili,wanyao-s13-bili}.jpg` | B 站封面 |
| 短视频素材 | `media\meme-daily-v1\`（363 件 / 80 MB） | 梗图线 |
| 漫剧试点 | `media\drama-pilot-in\`（14 件 / 56.6 MB） | 试点样片 |

### C 级 · 脚本工具（与仓内已有重叠，仅留作参考）

`media\drama-tools\*.py/.ps1`（8 件小脚本）——与 `cph4/fleet/drama-dept-v1/epburn-handover/`
的 60 集工具链同源，**不重复入库**，保留在原地作对照。

## 四、已做的整理动作

1. IndexTTS 源码从 `media\drama-tools\repos\index-tts` → **`K:\Fluxgroup\.tools\index-tts`**（源码不该躺在 media 里）
2. 解压全部用 **GBK 文件名修正**（Windows zip 默认 cp437 解码会满屏乱码）
3. 三包 sha256 全部对 MANIFEST 校验通过后才删除源包

## 五、删除记录

| 件 | 处置 |
|---|---|
| `02-MV与短视频成品.zip` | 删除（内容已落地并抽检） |
| `05-角色LoRA与关键帧试验.zip` | 删除 |
| `05-角色LoRA与关键帧试验(20261123125015).zip` | 删除（与上同 sha 的重复件） |
| `06-漫剧工具链.zip` | 删除 |
| MANIFEST / build.log / 交接清单 | **保留**（审计凭据） |

—— bm-c · 2026-11-23
