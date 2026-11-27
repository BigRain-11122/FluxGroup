# 自媒体责任状 v1（bm-c · 传家宝席）

> 令源：CEO 2026-11-27「以前我在生产力电脑建立的各种技能 经验 智能体什么的 能用就用，还有规则啊 工作流啊什么的，你肩负起自媒体的所有责任和生产 创新 改进 迭代」
> 本件是**承担责任 + 实例化**，不是新法。既有正典一条不废、一条不改（承 CEO 2026-11-21「之前的规则工作流不要推翻，能用就用」）。

## 〇、我是谁、管什么

- 本机 = `K:\Fluxgroup\FluxGroup` = **传家宝 / visual**：内容线唯一生产归属（承 `HANDOVER-20261120-CONTENT-TO-VISUAL.md`）。
- 责任面五线 + 一条横切：
  | 线 | 形态 | 现状 |
  |---|---|---|
  | L1 MV | 单曲横屏 3-5min · K 帧+i2v · 原曲配歌 | 在产（爱在西元前 v3 烧制中） |
  | L2 AI 漫剧 | 竖屏 60-90s × 80-120 集 | 60 集 v1 已出 · 目标档未达 |
  | L3 AI 短剧 | 竖屏写实 KF+i2v | EP009/EP010 推进 |
  | L4 短视频 | 热点驱动日更 | 管线 CERTIFIED，待排产 |
  | L5 切片 | 选源+重写+TTS | 管线在役 |
  | 横切 | 账号运营/发布 | **物理件=CEO 保留面**（凭据、发布动作不代决） |

## 一、复用清单（能用就用·不重造）

### 1.1 正典与工作流（读这五份就够开工）
| 用途 | 正身 |
|---|---|
| 产线总图（五线 × D0-D9 九站 × 实测接线） | `cph4/fleet/BIGSTREAM-LINE-MAP-v3.md` |
| 本机闭环命令手册（在哪台机、什么路径、什么命令） | `cph4/fleet/MV-LOCAL-LOOP-RUNBOOK-v1.md` |
| 循环蓝图（CONTENT-LOOP：轮式/自领活/簿记/闸在环内） | `cph4/fleet/CONTENT-OS-LOOP-BLUEPRINT-v1.md` |
| 生产方法论（三工位+双审 agent 化） | `cph4/fleet/BIGSTREAM-PRODUCTION-METHODOLOGY-v1.md` |
| 好配方积累（条件→配方） | `cph4/fleet/CONTENT-WINS-LEDGER-v1.md` |
| 漫剧 | `cph4/fleet/drama-dept-v1/DRAMA-PRODUCTION-SYSTEM-v1.md` + `REBUILD-PLAN-v2.md` + `QUALITY-SPEC-v2.md` |
| 短视频 | `cph4/fleet/shortvideo-dept/{DEPT-CHARTER,PIPELINE,POWERS-MAP}.md` |
| 烧片唯一闸 | `mv-album-001-jay/prompt-writing-spec-v1/PREFLIGHT-GATE-v1.md`（漫剧 profile="drama" 同闸） |
| 判例册 | `mv0001-handover/.../EXPERIENCE-LEDGER-v1.md`（J-01…J-32） |

### 1.2 技能（`cph4/skills/` 43 件 → 阶段映射·本机已装同名副本）
| 站 | 技能 |
|---|---|
| D1 选题/调研 | `content-recon` `cph4-research-dispatch` `github-repo-ops` `growth-ops` |
| D2 剧本/分镜 | `tw-mv-director` `drama-director` `mv-aesthetic-seats` `mv-edit-rhythm` `mv-intent-to-prompt` |
| D3 KF | `mv-casting` `mv-props-era` `mv-lighting` `mv-colorist` `art-critique` `gate-rigor` |
| D4 i2v | `mv-performance` `mv-big-picture` `bigstream-expert-panel` |
| D5 配音/音乐 | `drama-director`（音色档） + qwen 音色池 |
| D6 剪辑/装配 | `mv-edit-rhythm` `mv-colorist` + `build_*_final_v*.py` 范式 |
| D7 质检 | `gate-rigor` `art-critique` `compliance-guard` `qa-lead` |
| D8 发布/运营 | `growth-ops` `ship-ops`（发布动作仍候 CEO） |
| D9 迭代/复盘 | `agent-librarian` `memory-curator` `session-handoff` `cost-ledger` |

## 二、运行载体（本机实测在役）

- **循环驱动器**：任务 `SelfMedia-Hub-Tick` → `Tools/selfmedia/hub.py tick`（隐藏链·`Tools/InvisibleRunner.vbs`）。
- **车道容量**：gpu 1 / cpu 3 / io 2；挑活规则=prio 降序、`deps` 满足、`fails<3`；GPU 优先占坑。
- **投单正门**：写 `Tools/selfmedia/jobs/seed.jsonl` → `python Tools/selfmedia/hub.py add`（幂等：同 id 跳过）。
- **看板/回执**：`cph4/fleet/selfmedia/{BOARD.md,queue.jsonl,receipts/,logs/}`。
- **ComfyUI 双实例**：8188=MV 线（int8 768P）；8189=drama 线。**烧卡窗内禁两条线同时占卡**（16GB）；GPU 单子必须串行。
- **让路**：`machine-state.ps1 -Mode pause` 触发后 hub 自动停（`is_paused()`）。

## 三、质量闸（不降级·全在环内）

1. **烧前闸**：PREFLIGHT-GATE（镜/角/运动/调色/材质/场景/光七字段齐全 + 禁词 0 + 词数 ≤200）。
2. **配前闸**：调色案 + 服装案 + 道具年代案 + 歌词意象表四件齐（J-20/21/22/23）。
3. **成片闸**：逐镜核查（时长/YAVG/冻结/素材唯一）+ 全片 framemd5 查重=0 + 字幕三查 + 响度 -14 LUFS + `min_duration` 闸。
4. **双签**：导演席 + 制监席（独立席·禁自审自签）；CEO 终审只做终点。
5. **红线**：真金/账号写操作/发布=CEO 物理件；敏感题材按 compliance-guard 预商业化轻档。

## 四、创新与迭代（我主动做，不等令）

- **周格式实验（W-EXP）**：每周 1 个新形态试验（不占正片预算），先做方案+低清样，判据=完播/上头度代理。
- **复盘→判例→闸（当日回灌）**：每片收口把缺陷写进 EXPERIENCE-LEDGER，并把闸落到出生站（J-32 范式）。
- **好配方入册**：一次过/超预期的做法写 `CONTENT-WINS-LEDGER`（条件→可复用配方）。
- **跨线复用经济**：角色/声音/风格资产复用率入账（承 CONTENT-OS §五-2）。

## 五、当前在办（2026-11-27 夜）

| 件 | 状态 |
|---|---|
| 爱在西元前 v3：7 重烧 + 8 补镜（15 单） | **烧制中**（768P int8·约 8.3min/单） |
| 第二波 8 单（同脸替换 + 4 补镜） | 接力待烧 |
| v4 剪辑表（109 镜·每镜唯一素材）→ 装配 → 逐镜核查 | 自动接力已挂 |
| 星晴 PACK-B v11 / 可爱女人 KN / 龙卷风 / 简单爱 定版 | 待排（复用已烧素材） |
| 漫剧 EP009 i2v 重试 / EP010 | 上次 EP009 GPU 单 FAILED，待查因重投 |
| 短视频日更 / 切片 | 管线在役，待喂单 |

---
署名：bm-c（传家宝席）· 2026-11-27
