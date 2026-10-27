# 表演 A/B 试烧包（2026-10-20·表演席判据落地·@bm-c 执行）

> 目的：验证 `AI-ACTOR-PERFORMANCE-v2` 的「意图动作 + 时序」写法到底有没有用。
> **不过线就回炉改法，不许把规则当成果。**
> 成本控制：480P 短验（O-20261014-1325 低清验证律），同 KF 同参数，8 条短片。

## 一、实验单位（用现有 KF，不新烧帧）

| 单元 | 类型 | 为什么选它 | KF 种子 |
|---|---|---|---|
| `XQ_S5-30` | 单人脸镜（演唱锚②） | 现行词面把三个位移写在同一条 held 句里 = "同帧位移"典型样本 | s20222 |
| `XQ_S3-18` | 双人镜（数步顿半拍） | 双人镜没有"谁先谁后" = 反应延迟缺失典型样本 | 在册帧（B3 块） |

## 二、A/B 词面对照

### 单元 1 · XQ_S5-30（侧脸低唱·"它一定实现"）

**A（现行写法·从 i2v 包原样复制）**：包内 `XQ_S5-30` 条目原文，不改一字。

**B（8 维动作版）**：
```
The camera holds a locked-off tripod frame.
His chest lifts with one slow breath (frames 0-8), then the fine creases at the outer corner of his eye deepen and ease (8-18), then his lips part a hair and close again (18-26), then the eye corner flattens first and the lip settles last (26-40).
He is not singing to the camera; he keeps the note from spilling.
Only these two micro-gestures; the shoulder and head do not move.
One full blink near the end (eyelid closed 8-10 frames).
Indigo night, starlight rim along the cheek.
```

### 单元 2 · XQ_S3-18（双人数步·他顿半拍）

**A（现行写法·原样复制）**：包内 `XQ_S3-18` 条目原文。

**B（时序版）**：
```
The camera holds a locked-off tripod frame.
His leading foot stops on the white line; four to six frames later her chin begins to turn; his mouth corners move before his eyes follow her by two or three frames.
Her head keeps turning after his eyes have already arrived.
Neither of them turns at the same time.
Dusk rim light, halation along her hair edge; the grass does not move.
```

## 三、烧制参数（必须完全一致，否则实验作废）

- 分辨率 **480P**（试烧档）· 时长 4-5s · 24fps
- 同一 KF 文件 · 同一种子 · 同一采样器/步数 · 同一模型档位
- 每版 **2 条 take**（A1/A2、B1/B2），共 8 条
- 输出：`bmc/ab-performance-20261020/{A1,A2,B1,B2}_{S530,S318}.mp4`（-an 剥音轨）
- 回执：文件名 + 大小 + sha16 + 实际参数，写 orders 一行

## 四、判读（先机检，再人看）

| 指标 | 阈值 | 怎么测 |
|---|---|---|
| ① 时序：双人镜两脸起始帧差 | **3-8 帧**（同帧 0-2 判负） | 光流起始帧差 |
| ② 单人镜：事件帧→身体起始帧 | ≥3 帧 | 同上 |
| ③ 表情 onset/offset | onset 12-20 帧 / offset 8-16 帧；onset<6 帧判负 | 眼/唇区域逐帧差 |
| ④ 同帧位移数 | ≤2 | 人工逐帧点数 |
| ⑤ 眨眼 | 4-6s 脸镜 ≥1 次完整眨眼 | 眼开合曲线 |
| ⑥ 意图可读（盲评） | 5 人静音看，"他在做什么/想要什么" ≥4 人一致 | 盲评 |
| ⑦ "像 AI 吗"（辅判，不定生死） | ≥3/5 投"像"→回看①② | 盲评 |

**判定**：B 在 ①②③④ 至少三项优于 A 且⑥达线 → 表演法成立，升硬门。
若 B 未显著优于 A（尤其①③无差）→ **本方法不成立，回炉改法**，禁止照抄规则。

## 五、诚实声明

- 两个单元都是已交付片的镜，试验件只作判据用，不进正片。
- 盲评人数 5 人偏少，结论只作"成立/不成立"的粗判，不作精度声明。
- 480P 会削弱微表情可判性——若①③在 480P 上不可判，改 768P 单条复核，不整批重烧。