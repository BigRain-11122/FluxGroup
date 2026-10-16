# 提案：patrol-fleet digest 探针 v1.1 修法（受保护件·CEO 令通道·提名面正身）

> 提名链：NJ group E2（2026-10-14 23:37 域席旗班·假旗深挖后立）→ NEED-JUDGMENT pending → HQ-CEOProxyEventCarrier 10-17 01:26 事件班（R2.5）承载核验后升格落地本件。
> 通道依据：`Tools/protected-hash-register.ps1` 注册表 law＝「changes to protected files are finalized by CEO order ONLY - panel signatures are nomination; no order = restore + report」——`Tools/patrol-fleet-carrier.ps1` 与 `Tools/patrol-fleet-config.json` 均在注册表 strict 基线（meta.order=O-20261014-2250）。**CEO 批准后：本件即贴补丁落盘 + `-Register` 重锚（meta.order 记 CEO 令号）**。
> 历史注：10-14 23:38 域席 SHIFT-DONE 曾记「本班并载 v1.1 修复提案 reviews/ 目录」，实际未落盘（reviews/ 仅 W2/W4/WAVE1 三件）＝提名欠账；10-14 23:41 事件班承载半途死（event-carrier out.log 证据）——本件补齐，10-17 本班为首次完整承载。

## 一、病理（R2.5 事件班 2026-10-17 01:2x-01:5x 亲验·全部 ✓ 级证据）

| # | 病 | 证据 |
|---|---|---|
| ① | **假阳性真根因＝瞬态竞态，非「路径层误标」**：10-14 23:14:18 载体单次运行内 Test-Path 对全局文件返回 False→旗「…CODELY.md: missing」→发射 pid 42800 深挖班（成本实锚）。全局记忆文件每日多窗被平台改写（21:47 周审＋各班末记忆写入；10-17 01:35 实测 mtime 距今 8min＝写入活跃期），改写存在亚秒空窗，单次 Test-Path 可落入＝假阴性。勘正原诊断：config 传感路径本就是全局绝对路径，旗面无误标；「项目级 .codely-cli\CODELY.md 缺位」＝平台常规位，本仓正典项目卡＝根级 CODELY.md（结构律·在盘），非真缺位 | shiftlog 10-14 23:14:18 同秒 DIGEST done＋LAUNCHED 实锚；10-15 09:14 / 10-16 19:28 digest 实产均无此旗＝瞬态性佐证 |
| ② | **digest age 格式毒**：`.ToString('hh\.hh\ \m\i\n')` 把小时重复两遍错标为「min」且吞 >24h 天数——30h 龄显示「06.06 min」、5h 显示「05.05 min」＝本地 35B digest 把陈旧读成新鲜，误导十域日报 verdict（此雷当前在役） | 本班 PS 亲测（FromHours(30)→「06.06 min」）；10-16 19:28 实产 prompt「[传感状态] …=> 00.00 min」 |
| ③ | **全局/项目两路径未分开探**：group 域传感仅全局 L0 一条；项目层 L1 卡（根级 CODELY.md）零传感＝digest 无项目层读数（NJ 处方「全局/项目两路径分开探＋旗面标真缺者」的缺口面） | patrol-fleet-config.json group.sensors 实读 |

## 二、即贴补丁（四处·含受保护双件）

### ① Tools/patrol-fleet-carrier.ps1 — 新增瞬态容差助手（插入于 Resolve-SensorPath 函数后、`$flags = @()` 前；顺带头部注释版本注记 v1.1）
```powershell
# v1.1: transient-gap tolerance - the global memory file is rewritten in place by the
# platform several times a day; a single Test-Path can land inside the sub-second gap
# (10-14 23:14 false 'missing'). Double-probe before flagging anything missing.
function Test-PathStable([string]$p) {
    if (Test-Path $p) { return $true }
    Start-Sleep -Seconds 5
    return (Test-Path $p)
}
```

### ② 同文件 — 旗段两处改用稳定探测（旗文本格式刻意不变＝保 snooze 前缀兼容）
```powershell
    if ($s.type -eq 'must_exist') {
        if (-not (Test-PathStable $abs)) { $flags += ($s.path + ': MISSING (must_exist)') }
        continue
    }
    if ($s.type -eq 'mtime') {
        if (-not (Test-PathStable $abs)) { $flags += ($s.path + ': missing'); continue }
```

### ③ 同文件 — digest 传感状态行重写（分辨绝对路径＋诚实分钟龄）
```powershell
    $sensState = @()
    foreach ($s in @($dom.sensors)) {
        # v1.1: label each probe with its own resolved absolute path (global L0 vs project
        # L1 card cannot be conflated), double-probe missing, honest minute ages (the old
        # 'hh\.hh\ \m\i\n' format mislabeled hours as min and dropped >24h days).
        $abs = Resolve-SensorPath $s.path
        if (Test-PathStable $abs) {
            $ageMinD = ((Get-Date) - (Get-Item $abs).LastWriteTime).TotalMinutes
            $sensState += ($s.path + ' [' + $abs + '] => age ' + [math]::Round($ageMinD,0) + 'min')
        } else {
            $sensState += ($s.path + ' [' + $abs + '] => MISSING')
        }
    }
```

### ④ Tools/patrol-fleet-config.json — group 域补项目级传感（根级 CODELY.md＝L1 项目卡正身位）
```json
      "sensors": [
        { "path": "C:/Users/sjs20/.codely-cli/CODELY.md", "type": "mtime", "max_age_min": 2880, "weak": true },
        { "path": "CODELY.md", "type": "must_exist" }
      ],
```
（相对路径经 Resolve-SensorPath 解析至仓根＝正典 L1 卡；must_exist＝真缺位才旗、零 mtime 噪声。旗面按传感自带路径分开标注＝「旗面标真缺者」处方落地。）

## 三、批准后落地程序（≤10 分钟·回滚=revert＋重锚）
1. ①②③④ 按上文即贴落盘。
2. `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\protected-hash-register.ps1 -Register`（meta.order 记 CEO 令号＋本提案指针·重锚）。
3. 下一拍载体自验（PT30M：group 域零旗零发射；09:00 后 digest 首产核验新格式 `[路径] => age Nmin`）。
4. 回执行入 PATROL-FLEET/LOG.md＋NEED-JUDGMENT 结案。

## 四、成本/收益
- 成本：一次 CEO 令（一句话）＋四处小改＋一次哈希重锚。
- 收益：瞬态假阳性类全灭（每次误发射深挖班 ≈25 调用实锚成本归零）；十域 digest age 诚实化；项目层 L1 卡入传感面。
- 过渡止血（R2.5 已落地·不待批）：`media/logs/patrol-fleet/group-snooze.json` 增条 until 2026-10-18 01:50（前缀 `C:/Users/sjs20/.code`·拦截同旗误发射；真缺位则移除 snooze 升级处理）。
