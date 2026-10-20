# 本机清空清单（bm-a · 上传网盘后执行 · 2026-10-20）

> 目标：CEO 把成品传网盘后，本机不留残料。**执行顺序不可颠倒**：先传 → 再校验 → 再删。
> 原则：**只有「上传已核验」的件才可删**；可重建的权重/缓存随时可删；正典、记忆、凭据、工单面永不动。
> 工具：`Tools/local_cleanup_r1020.ps1`（默认只报表，`-AfterUpload -Purge` 才动手；先跑 `-WhatIf` 无副作用）。

## 一、A 类：必须上传（本地删了就没了）

### A1 交付成品（3 件·合计 3.43GB）

| 件 | 大小 | 说明 |
|---|---|---|
| `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v511_wmvs_aigc.mp4` | 875MB | **对外交付版**（含 AIGC 显著标识） |
| `.../full_mv_v511_n1.mp4` | 1278MB | 审看版（n1 链） |
| `.../full_mv_v511.mp4` | 1276MB | 无字/母版 |

### A2 历史版本（15 件·合计 ~4.3GB·**建议传完即删本地**）

`30s-reel-v1/full_mv_v4.mp4`、`v51`–`v59`、`v58a_s1fix`、`v510` 及各自 `_n1` 变体（单件 214–290MB）。
这些已被 v511 取代；网盘留档后本地无再用价值。

### A3 分段与中间件（可选·~2GB）

`media/MV/mv0001/kf-demo-20261012/segments/_cut/v56_v511_final/*.mp4`——成品可由这些段件重装。若网盘已存成品，段件可一并删。

> **注意**：星晴/可爱女人的 KF 帧与板图**不在本机**（在 bm-c 的 `K:/Fluxgroup/FluxGroup/media/mv-album-001-jay/`）。本机清空不涉及它们；bm-c 侧另开清单。

## 二、C 类：可删（可重建/可重下，不占交付价值）

| 目标 | 实测 | 为什么可删 |
|---|---|---|
| `cph4/labbench/` | **15.62GB** | 实验台（ace-step 检查点 + venv），权重可从上游重下 |
| `life/BigLife/.codely-cli/labbench/` | **7.24GB** | bonsai 量化权重等实验件，同上 |
| 全仓 `.venv` / `node_modules` / `__pycache__` | **6.72GB** | 依赖可重装；bytecode 可再生 |
| `media/hardware-staging/` | **2.00GB** | 采购到货暂存件，装机完即成废料（删前确认无未验货） |
| `%USERPROFILE%\.codely-cli\tmp\` | **1.67GB** | 会话临时件（上次清理后新长出来的） |
| `%LOCALAPPDATA%\Temp\` | **1.17GB** | 系统临时 |
| `Tools/nats/data/` | 小 | JetStream 运行态，重建即空 |

**C 类合计 ≈ 34.4GB**（不含 A2 的 4.3GB）。

## 三、D 类：静默保留（清空后仍要能干活）

- `.git/`（973MB·唯一历史源）与各子仓 `.git`
- **`media/MUSIC/`**（无损音源库·CONTENT-GC S0 禁删）
- **`media/BigStream/data/assets/`**（9.8GB 模型运行时·S0 禁删，非废料）
- `.codely-cli/memory/`、`settings.json`、`cph4/fleet/inbox/`
- 凭据：环境变量/密钥文件**不在仓内**，清空动作不触碰
- 在用脚本与任务注册（任务计划程序项）
- 云道正典 `cph4/fleet/CLOUD-OFF-*`、`MACHINE-ROLE-bm-a-EXECUTOR-20261020.md`

## 四、「干净」的验收判据

清完当场验四条，全过才算干净：

1. `git status --porcelain` 为空（工作树无脏件；未跟踪物已被 `.gitignore` 拦住）。
2. C 类目录逐个 `Test-Path` = False。
3. `C:` 可用空间 ≥ 清空前 + 34GB。
4. 仍能开工：`python Tools/cloud_lane_lint.py` 跑得通、`cph4/fleet/inbox/` 与 `memory/` 都在。

## 五、执行命令（照抄可用）

```powershell
# 1) 先看账（只读，不删）
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\local_cleanup_r1020.ps1

# 2) 上传完成、逐件核对无误后：写一个上传凭据文件
#    %USERPROFILE%\Desktop\FluxGroup\.uploaded-ok.json
#    内容形如 {"uploaded":["cph4/fleet/.../full_mv_v511_wmvs_aigc.mp4", ...],"at":"2026-10-20T19:30:00+08:00"}
#    （只有清单覆盖全部 A 类件，脚本才允许进入删除态）

# 3) 预演删除（仍不真删）
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\local_cleanup_r1020.ps1 -AfterUpload -Purge -WhatIf

# 4) 真删
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\local_cleanup_r1020.ps1 -AfterUpload -Purge
```

## 六、诚实边界

- 本件体积均为**本机当场实测**，非估算；数值会随新产出变化，执行前脚本会重算。
- 脚本**不会**自动判断「网盘真的传上去了」——它只认 `.uploaded-ok.json` 这份人工签字的凭据。这是故意留的人工闸：删不可逆，宁可多一道手。
- A2/A3 属「建议删」，不是「必须删」；不放凭据文件里就不会删。

---
*bm-a · 2026-10-20 · 承 CEO「上传网盘后本机要干净」*