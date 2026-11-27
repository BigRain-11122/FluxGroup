# 星晴女主选角候选板 · c2136 判读与闸结论

> 执行=b m-c C2136 tick · 2026-10-20 08:31–08:52 · 承 `XQ-选角案-v1.md`（「候选板烧制 GPU 批·排 MV V3 之后」；V3 早已收官，故本步到期）
> 素材=16 张试构图（v1·4 型 × 黄昏/夜 × 2 种子，672×384）+ 8 张修正版（v2·4 型 × 2 光位 × 1 种子）
> 回执=`xq-CASTING-RECEIPT-c2136.json` / `xq-CASTING-RECEIPT-c2136-v2.json`（生成参数、种子、lint、逐格文件名全在）

## 一 产物

| 件 | 路径 | 规格 |
|---|---|---|
| v1 候选板 | `xq-CASTING-BOARD-c2136.jpg` | 4 行 × 4 列（448×256/格）·326,558B |
| v2 修正板 | `xq-CASTING-BOARD-c2136-v2.jpg` | 4 行 × 2 列·148,025B |
| 原图 24 张 | `media/MV/mv0001/xingqing/xq-casting-c2136{,-v2}/` | 672×384 PNG，逐张 >200KB |

## 二 v1 判读（多模态，逐行）

| 型 | 分 | 判 |
|---|---|---|
| A 高马尾 | 7 | 夜格马尾存在感消失、跨种子骨相差偏大 |
| B 长直发 | 8.5 | 四张最稳、辨识度最高 |
| C 齐下巴短发 | 7 | 全板最小、露齿笑待放大 |
| D 低双辫 | 7.5 | 四张鼻梁/脸宽漂移，不像同一人 |

**两处硬伤（当轮即修，未流入下一站）**：①骨相年龄 14–17，不到 19；②夜场皮肤过磨/蜡感（现代 AI 味主源）。

## 三 v2 修正（同站拦截）

- 年龄面：`a woman of about nineteen or twenty, first-year university student ... mature facial structure with a defined jawline`；A 型 `soft rounded cheeks` → `soft rounded cheekbones`。
- 皮肤面：`natural skin texture with visible pores and subtle unevenness`；夜光改 `practical warm street-lamp light with soft falloff ... film grain visible in the shadows`。
- 判读结果：**年龄感 A/B/C 落 19–21 通过，D 仍 17–18**；夜景颗粒回归、蜡感未清零（A/C 夜格额头鼻梁轻微高光蜡面）；四型区分度全程成立。

## 四 闸结论

- **反向测试（选角案三门禁之③）**：两轮均「无指向性接近任何真实艺人」→ **过**（不撞脸，无肖像风险；正式签约仍走法务核查）。
- **年代门（②）**：素颜、无韩式平眉/网红唇/修容、白衬衫＋稻田＋低饱和星空，2000 年前后台湾学生氛围成立 → **过**。
- **受众门（①）**：B「安静干净、夜里看星星」= 名字即人设（星晴）最贴；A 次选（元气主动型）；C 偏成熟；D 偏学妹。
- **可用于定脸正档阶段**（v2 评分：A 8.0 / B 8.0 / C 7.5 / D 6.5）。

## 五 下一步（进正档前）

1. **主推 A、B 双线**，各出 1344×768 × 3 种子定妆照（锁定 1–2 张作定脸基准，解决「行内跨种子不是同一人」）。
2. B 需补夜格带刘海变体（v2 s729175 微调）；D 若要保留须再增龄或改定位为回忆线角色。
3. 定脸后 → `KF-PACK-B`（S1-08 / S3-17 / S3-21 / S5-31 四帧 + B 补 2 帧）→ B 批 6 帧补齐后，A+B 合装可覆盖全曲时间轴（现 A 包样片 196.14s / 全表 238s / 原曲 259.4s）。

*bm-c C2136 · 逐格参数见两份 receipt JSON（可完全复现）*