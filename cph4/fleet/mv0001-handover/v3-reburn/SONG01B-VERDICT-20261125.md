# SONG_01B 验收 · 演唱锚修正版（2026-11-25）

> 首帧换成 `AN_05_LOWANGLE` 仰拍帧，动作改「仰头到喉部完全暴露」。判定：**✅ 成功**。

## 一、六帧动作弧

```
0.1s  侧脸起势，眼睛睁开
1.0s  转正，闭眼，头开始抬
1.9s  仰头，喉部完全暴露，闭眼          ← 演唱态峰值
2.8s  保持仰头，喉部暴露，闭眼
3.7s  仰头略降，仍闭眼
4.4s  回正，睁眼，嘴闭合                ← 收得干净
```

**三段式完整**：起势 → 峰值停留 1.9–3.7s（1.8 秒）→ 回正。

## 二、为什么这次成立

| 因素 | 第一版（失败） | 本版（成功） |
|---|---|---|
| 首帧角度 | 正面平视（模型倾向保持） | **仰拍**（天然适合仰头） |
| 动作幅度 | `chin lifts a few degrees`（太小） | `head tips back until the throat is fully exposed`（明确终点） |
| 手的处理 | 未指定 | 双手交叠胸前（给人"握持"的暗示） |
| 口型 | — | **全程闭眼 + 不碰嘴 + 4.4s 回正时嘴闭合**，0 口型 |

## 三、可复制的配方（演唱锚 v1）

```
首帧：仰拍 15–25°，喉部在画面内
词面：head tips back until the throat is fully exposed → eyes close →
      chest lifts → holds a beat → head comes level → eyes open
手：   loosely clasped at the chest（古代线无麦，避免穿越）
光：   strong warm uplight on the throat and jaw（单光源）
禁写：singing / humming / lips / mouth / breathe through mouth
```

**核心**：演唱态用"仰头+喉部暴露+闭眼+胸腔起伏"表达，**不给模型任何嘴部指令**。

## 四、A 档四必需件 —— 全部达成

| # | 必需件 | 素材 | 状态 |
|---|---|---|---|
| 1 | 副歌主唱演唱镜 | `SONG_01B_THROATUP` + `SONG_02_BACKLIT` | ✅ |
| 2 | 对手戏 | `HANDGLASS` + `L01` 伸手 | ✅ |
| 3 | 明确因果链 | `L01_ENTRY_DOLLY`（走进→找到→伸手） | ✅ |
| 4 | 大场面运动调度 | `HALL_PAN` + `L01` 推轨 | ✅ |

**素材层已经够 A 档了。** 现在缺的不是拍摄，是**重剪**——把这些新镜装进 30s 结构里。

## 五、下一步（v15 重剪）

建议结构（合计 ≈30.5s）：

```
L01_ENTRY_DOLLY    8.0s   她走进 → 找到 → 伸手（现代·因果建立）
SONG_01B_THROATUP  4.5s   男主仰头（古代·演唱锚 1）
HALL_PAN           4.5s   神殿横移（古代·大场面）
AN_07_STAND        4.5s   男主正面（古代·演唱锚 2 的姿态基础）
HANDGLASS          4.5s   手贴玻璃 + 倒影（现代·对手戏）
SONG_02_BACKLIT    4.5s   剪影（古代·演唱锚 3 / 收尾）
```

对位关系：**她在一个空间里找 ↔ 他在另一个时空里唱**。
这一版如果成立，是真正的"人—物—人—物"而不是"物—物—物"。
