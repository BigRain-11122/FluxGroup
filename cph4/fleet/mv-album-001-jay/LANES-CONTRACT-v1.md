# 多智能体协同契约 v1（2026-10-21）

> CEO 令：多个 agent 一起干活，**不互相抢**，共同推进。
> 核心：一资源一主人、一文件一主人、冲突时让路不重试。

---

## 一、三条车道（互不重叠）

| 车道 | 独占资源 | 写权限范围（只许写这里） | 严禁 |
|---|---|---|---|
| **A · GPU** | ComfyUI（8188）、显卡、`D:\AI\comfyui-krea` | `D:\FleetWorker\review\finals\`、`D:\FleetWorker\review\night\takes\` | 不碰 cph4 文档；不留常驻服务（跑完停） |
| **B · 剪辑** | ffmpeg CPU、`D:\FleetWorker\review\edl\` | `cph4/fleet/mv-album-001-jay/EDL-*.json`、`EDL-*.md` | 不启动 ComfyUI；不动 A 的 takes |
| **C · 文档** | 无算力 | `cph4/fleet/mv-album-001-jay/*.md`（N2/N3/台账） | 不跑 GPU；不改代码/脚本；不动视频文件 |

## 二、冲突规则

1. **GPU 只有 A 车道能碰。** B/C 需要 GPU 时**排队登记**，不得自行启动 ComfyUI。
2. **同一文件只有一个主人。** 越界写入=违规，发现即回滚。
3. **不重试对方在跑的活**：发现目标文件正在变化（mtime 在 2 分钟内更新），让路，`WAIT`。
4. **失败不互相补位**：某车道失败，由该车道自己写失败原因；别的车道不许代跑（会破坏归属）。
5. **只有共享状态文件可多车道读**：`S4-DECISIONS-20261021.json`（只读）、`LANE-STATE.md`（只由各车道追加自己的一行）。

## 三、共享状态（每车道追加一行，不改他人行）

`LANE-STATE.md` 格式：

```
2026-10-21T20:10 | A | finals 768P R1 开始 | 预计 6min
2026-10-21T20:16 | A | finals 768P R1 完成 | PASS
```

## 四、交付依赖（谁等谁）

```
A(768P 正式件) ──→ B(按正式件锁 EDL) ──→ 装配 → release_gate
C(N2/N3 文档) ── 独立，不阻塞任何人
```

B 在 A 完成前只做**结构与节奏表**（不含实际素材），A 完成后 B 才落 EDL 数值。

## 五、任务卡片（每个 agent 自含上下文）

### A 车道：768P 正式件
- 输入：`D:\FleetWorker\review\night\takes\` 里 R3b_9411、R4a；`R1_t3_s9303`、`R2_sing3`
- 输出：`D:\FleetWorker\review\finals\*.mp4`（768P）
- 必须：用 `Tools/preflight_gate.py` 先过闸；执行前后写 `LANE-STATE.md`；跑完**停掉 ComfyUI**
- 禁止：改任何 cph4 文档、改其他 take

### B 车道：节奏与 EDL
- 输入：`S4-DECISIONS-20261021.json`（只读）、`RHYTHM-DESIGN-v1`、`LYRICS-6AXIS.md`
- 输出：`EDL-DRAFT-v1.md`（逐镜时长/转场类型/取景方式）+ `EDL-DRAFT-v1.json`
- 必须：满足镜长标准差 ≥1.8s、副歌 ≤1.6s、桥段 ≥4.0s；标注"一镜两取景"的推近镜
- 禁止：渲染、跑 ffmpeg 生成成片、碰 GPU

### C 车道：前端文档补齐
- 输入：`LYRICS-6AXIS.md`
- 输出：`N2-STORY-STRUCTURE.md`（叙事四律逐条验）、`N3-SCRIPT-CHECK.md`（剧本四律+删了会怎样）
- 必须：每条判据给 PASS/FAIL 与一句理由；不确定的写"待证"
- 禁止：碰视频、跑脚本、改代码

## 六、违规处理

- 发现越界写入 → 立即停止该车道 → 回滚越界文件 → 在 `LANE-STATE.md` 记一行事故 → 上报。
- 同一车道两次越界 → 该车道停用，改单车道串行执行。