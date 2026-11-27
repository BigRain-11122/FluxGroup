# DIRECTOR-REVIEW-V718 → 四件复验 PASS · 2026-11-02

> 承 canon/DIRECTOR-REVIEW-V718-PASS-20261031.md。本件**只记 2026-11-02 的独立复跑证据**，
> 不重复 10-31 的修复执行对账。CEO 定的规矩是「观众级四件缺一件不交片」——
> 10-31 签核时四件数据来自当日实跑，但 11-02 的日更卡一度报 FAIL，故重新逐件复验。
> 成片：`cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v718.mp4`
> （5623 帧 / 234.2917s / 24fps）

## 一、四件复验结果（2026-11-02 实跑）

| # | 观众级四件 | 回执 | 结果 |
|---|---|---|---|
| 1 | 交付闸 `mv_delivery_gate` | `queue-receipts/mv-gate-r2-20261102.json`（bm-a 13:05，65.0s） | **VERDICT: PASS** |
| 2 | 转场审计 `mv_transition_audit` | `queue-receipts/mv-transition.log`（bm-a 13:52，40.5s） | **OPPOSE=0** |
| 3 | 逐镜审计 `mv_full_audit` | `queue-receipts/mv-full-audit-20261102.json` | **unlisted 重复=0** |
| 4 | 稳定性 `mv_stability_gate` | 含于 #1 回执（`stability.seams/freezes`） | **seams=0 freezes=0** |

### 逐件读数

**#1 交付闸**（带 canon 声明的两个卡窗复跑）
```
frames 5623 @ 24.000fps   shots=83
static_shots = []          dup_pairs = 0
seams = 0                  freezes = 0
reprise_whitelisted = 8    reprise_unlisted = 0
VERDICT: PASS
```

**#2 转场审计**
```
frames=5623  cuts=118
summary: {HARD: 62, MATCH: 45, STATIC_JUMP: 11}
OPPOSE = 0
```
与 10-31 签核记的「118 切点 HARD 62 / MATCH 45 / STATIC 11，OPPOSE=0」**数字完全一致**。

**#3 逐镜审计**
```
frames=5623  shots=95  duplicates=7  duplicates_unlisted=[]
```
7 对重复镜全部落在 `MV0001-REPRISE-WHITELIST.json` 白名单内（设计性重演，非遗漏）。

**#4 稳定性**：`seams=[]`、`freezes=[]`，5623 帧断言精确命中。

## 二、11-02 那次 FAIL 的正身

日更卡在 11:29 报 `FAIL(D2 near-static shots: 2)`，**原因是卡没传 `--card`**：
canon 已声明 `38.79:40.21`（片名卡）与 `219.71:223.88`（片尾出处卡）两个设计卡窗，
不传则必然把卡窗判成死镜 —— 属**结构性假红**，不是片子变差。

补上两个 `--card` 后重跑：`static_shots=[]`、`VERDICT: PASS`。

> 记录一处我自己的误判以便后人别再犯：回执里 `static_shots` 的坐标是**帧号**
> （`[5273, 5373, …]`），5273÷24 = **219.71s**，不是「52.73 秒」。被误读成新增死镜，
> 据此派的 `R-MV-V718-STILL-5273` 已作废。

## 三、结论

**四件全绿，v718 本体可发。** 发布决定权在 CEO；本件不代作发布动作。

发布时仍按 10-30 令：**成片不加 AI 标识**，标识义务走平台上传声明位；
片尾「转载需注明出处 @大喵没鱼吃」保留。

## 四、同日修掉的三处工程缺陷（都在卡层，不在片子）

1. 三张复检卡（`R-MV-GATE-R2` / `R-MV-AUDIT-R2` / `C-MV-TRANSITION`）仍指向 **v717 旧母版**，
   等于复检错文件；另有第四张 `C-MV-STABILITY` 同样指向 v717，已一并改指 v718。
2. `Tools/mv_full_audit.py` 写死 `C:\Users\sjs20\Desktop\FluxGroup\Tools`，把卡钉死在 bm-a，
   换机必炸；已改为按脚本自身位置推导。
3. Mac 侧两张体检卡用裸 `python`，而执行器 PATH 里只有 `/usr/bin/python3`（pyenv 的 python
   不在 PATH）→ `rc=127`；已统一改 `python3`。