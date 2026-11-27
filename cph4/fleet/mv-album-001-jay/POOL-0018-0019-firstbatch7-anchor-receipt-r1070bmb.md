# POOL-0018 / POOL-0019 first-batch-7 anchor receipt — r1070 bm-b

- 轮次: r1070（2026-10-20 12:5x+08:00）· 机器: bm-b
- 溯源令: O-20261019-1935（机队 B/C 满负荷执行令）+ O-20261020-1124 sec.3（@bm-b 锚点滚动 + 7 曲校准面回填）
- 正身指针: `cph4/fleet/mv-album-001-jay/anchors/`（词面/鼓点/校准/镜头网格四件）+ `POOL-0018-0019-anchor-matrix.json`

## 1. 本轮新增实物（可跑脚本 + 产物）

| 件 | 类型 | 内容 |
|---|---|---|
| `anchor_shotgrid.py` | 可跑脚本 | 词面行窗 × madmom 鼓点网格 → 镜头网格；吸附容差 0.10s（超差保留词窗）、镜长上限 3.0s、超限按 beat 等分给建议切点；`--selftest` 7/7 PASS、`--matrix` 就绪矩阵；确定性幂等（重跑字节恒等，本轮实测 6/6 一致） |
| `anchors/<曲>-shotgrid.json` ×6 | 数据产物 | 每曲每行一镜候选：原词窗 + 吸附窗 + 吸附偏差 + 建议切点；advisory 标记（不判定、不改词窗） |
| `anchors/<曲>-shotgrid.md` ×6 | 人眼可读表 | 1 行 1 镜表格，剪辑席直接对照 |
| `anchors/星晴-calibrated.json/.txt` | 数据产物 | 7 曲校准面回填补齐（星晴 mode=whisper exact=36/approx=15/none=4/total=55） |
| `POOL-0018-0019-anchor-matrix.json` | 就绪矩阵 | words/beats/calibrated/shotgrid 四件在位性 + ready 计数 |

## 2. 就绪矩阵（本轮实测）

| 曲 | words | beats | calibrated | shotgrid | BPM | 行 | 吸附 | 需切 |
|---|---|---|---|---|---|---|---|---|
| 可爱女人 | ✓ | ✓ | ✓ | ✓ | 136.4 | 51 | 39 | 44 |
| 安静 | ✓ | ✓ | ✓ | ✓ | 72.3 | 51 | 18 | 42 |
| 开不了口 | ✓ | ✓ | ✓ | ✓ | 69.8 | 49 | 23 | 32 |
| 星晴 | ✓ | ✓ | ✓（本轮补） | ✓ | 89.6 | 55 | 16 | 33 |
| 晴天 | ✓ | ✓ | ✗ | ✗ | — | — | — | — |
| 简单爱 | ✓ | ✓ | ✓ | ✓ | 96.8 | 72 | 32 | 41 |
| 龙卷风 | ✓ | ✓ | ✓ | ✓ | 72.3 | 49 | 16 | 39 |

ready = 6/7。

## 3. 诚实缺口（不掩盖）

1. **晴天 校准面缺件**：`lyrics/晴天.txt`（官方词面）不在仓，whisper 词面不可替代官方词面（词面正身律），故 calibrated/shotgrid 双缺；补件输入=官方歌词文件，落位后 `python anchor_shotgrid.py 晴天` 一条命令补齐。
2. **余 34 曲无音源**：本机 staged 音频仅 first-batch 7 件（`C:\Fluxgroup\Tools\mv-audio-bmb`），K: 盘未挂载，全盘扫描无其余曲目音源 → POOL-0018/0019 的「余 34 曲续跑」为**供给依赖态**，非可执行态；音源到位（Taildrop 或 media 树落位）后按既有 idempotent 生成器（`anchor_words_gen.py` / `anchor_beats_gen.py`）当日可推进。
3. **吸附率偏低如实**：安静 18/51、星晴 16/55 等行窗多在 ±0.10s 容差外（whisper 行边界与鼓点天然错位）——按 V5.11 规格「>0.10s 词窗优先保留」故不吸附，镜头网格同时给出两侧值，剪辑席按副歌踩鼓点需要再取 beat 切点。

## 4. 消费面

- 下游=bm-a 导演席/剪辑席（V5.11 收口批的 beat 吸附审计与镜长 ≤2-3s 拆切），bm-c 装配线可直接读 `-shotgrid.json` 的 `grid[].t0_used/t1_used/splits`。
- 契约：`grid` 按 `i` 升序、`t0_used < t1_used`；`splits` 全部落在 `beats[].t0` 上；无墙钟字段 → 内容级幂等。