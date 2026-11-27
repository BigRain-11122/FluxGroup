# 漫剧 EP001 全链本地产出回执（bm-c · 2026-11-20/21）

- 剧集：`drama-001-stockera` · EP001「牛市没有眼泪」· 60 集正典第 1 集
- 机器：bm-c（RTX 3070 16G）· **全链本地，零云端**
- 产物：`cph4/fleet/out/drama/EP001/ep001-72s.mp4`（1080×1920 / 30fps / 77.3s / 63.6MB）

## 一、链路（每站都跑通）

| 站 | 工具 | 实测 |
|---|---|---|
| D1/D2 剧本+分镜 | `drama-001-stockera/episodes/EP001.json`（21 非卡镜） | 在库 |
| D3 关键帧 | `drama_kf_plan.py` → `drama_kf_batch.py`（animagine-xl-4.0·832×1472·28 步） | 21/21 出图·20s/张 |
| D4 i2v | `drama_i2v_plan.py` → `h3_i2v_album.py`（H3 int4 480P） | 21/21 出片·平均 155s/镜 |
| D6 配音 | piper `zh_CN-huayan-medium` × 18 句 + `drama_av_manifest.py --mix` | 单轨 72.2s，与时间线对齐 |
| D7 装配 | `drama_assemble.py`（1080×1920@30 + loudnorm + 烧字幕） | 一次成型 |
| D8 闸 | `drama_quality_gate.py --subs-burned` | **PASS** |

## 二、闸面读数

```
DRAMA-QA PASS  ep001-72s.mp4
  1080x1920 30.0fps 77.3s audio=True loud=-14.08 motion3s=0.023 cuts=19 avg_shot=3.9s
```

七条硬指标全过：竖屏 1080×1920 / 帧率 30 / 有音轨且 -14.08 LUFS（±2 内）/ 时长 77.3s（10–90）/ 前 3 秒有运动 / 平均镜长 3.9s（≤4.0）/ 字幕已烧。

## 三、已知问题（v2 要修的）

1. **构图漂移**：D3 提示词里的复杂场景（交易所大厅/翻牌大屏）常被模型简化成楼梯/走廊——场景词权重不足。
2. **人物年龄读感偏小**：部分镜的少年感比设定（22 岁）更幼。
3. **伪文字**：招牌/翻牌屏有低概率出现纹理化假字（本集未爆，但属高发面）。
4. **配音单一音色**：18 句全是同一把 piper 女声，与「旁白 / 父 / 门卫」多角色设定不符 → 需 IndexTTS-2 或 GPT-SoVITS（bm-b 侧，未接）。
5. **480P 验证档**：未上 768P 正片（成本墙：21 镜 × 768P ≈ 3.5 小时）。

## 四、耗时账（可用来排产）

| 段 | 时长 |
|---|---|
| D3 21 帧 | 约 7 分钟 |
| D4 21 镜 | 约 54 分钟 |
| D6 配音 18 句 | 约 1 分钟 |
| D7 装配 | 约 40 秒 |
| **合计** | **约 1 小时** |

即：**单机 16G 卡，一天可出 8–10 集 480P 验证档**；768P 正片约 2.5 倍。

## 五、复跑命令

```powershell
python Tools\fleet\drama_ep_chain.py --ep 1 --stages plan,kf,i2v-plan
python cph4\fleet\mv-album-001-jay\local-i2v\h3_i2v_album.py --repo K:\Fluxgroup\FluxGroup `
  --lane bmc --manifest cph4/fleet/out/drama/EP001/i2v_manifest.json `
  --out cph4/fleet/out/drama/EP001/i2v `
  --wf cph4/fleet/mv-album-001-jay/local-i2v/wf_h3_i2v_480p_int4.json
python Tools\fleet\drama_av_manifest.py --ep 1 --mix
$env:ASSEMBLE_ENCODER='libx264'
python Tools\fleet\drama_assemble.py --manifest cph4/fleet/out/drama/EP001/assemble_manifest.json --out cph4/fleet/out/drama/EP001/ep001-72s.mp4
python Tools\fleet\drama_quality_gate.py --in cph4/fleet/out/drama/EP001/ep001-72s.mp4 --subs-burned
```

—— bm-c · 2026-11-21
