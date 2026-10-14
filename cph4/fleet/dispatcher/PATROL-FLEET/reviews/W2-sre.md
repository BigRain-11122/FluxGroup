# W2 — 运维/SRE 评审席（PATROL-FLEET v1 轻审波）

> 溯源：O-20261014-2250·v1 轻审波 W2。**席位运转异常如实披露**：评审子代理于成文前预算中断终止（同 W1-2b 范式）——分析原文完整回收于任务转录，本件=记分员代录（主窗代成文·判定归席位分析本身）。红旗处置状态=本窗实测标注。

## 评分

7.0/10——闸门骨架成立（锁/防抖/日帽·与事件班前辈同构）+今夜十域实弹全通过；但初版存在两处真 bug（状态损毁崩溃环+digest 假 done）与一处文档-实现漂移（同签闸缺位）。

## 红旗（问题+证据+修法·处置状态）

1. **同签闸缺失（文档-实现漂移）**：头注与蓝图均称「同签 90min」但代码无该闸（前辈 proxy-event-carrier.ps1 有 `if (($sig -eq $lastSig) -and (…lt 90)) skip`）——持续同旗组会 40min 连发烧到日帽。**处置=本窗评审期内已修**：360min 同签重发窗+state.last_sig 字段（比 90min 收紧为 6h 一次复检·常设行防烧）。
2. **state.json 损毁=永久崩溃环+心跳说谎**：§3 `digest_date` 回读子表达式 `((Get-Content…|ConvertFrom-Json).digest_date)` 无 try/catch——损态在 EAP=Stop 下终结错误→脚本死于 Set-Content 之前→损态永不被覆写→该域每 30min 必崩；且心跳在文件头已写→P-1 SLI 新鲜=掩蔽失效（心跳活着、旗/班全死）。**处置=已修**：`$digestPrev` 预读带 try/catch（损态回退 ''→状态自愈覆写）。
3. **digest 未查 `$LASTEXITCODE`=假 done**：`& python … 2>&1 | Out-Null` 后直接标 done——python 零 stderr 干净退 1 时误标完成（P-3 产出率失真）；且 2>&1 在 PS5.1+EAP=Stop 下任何 stderr 行皆可掷终结错→误标 unreachable。**处置=已修**：改 `2>$null`+显式 `if ($LASTEXITCODE -ne 0) { throw }`。
4. **十域同拍齐发风暴（无 jitter/无跨域并发闸）**：十任务同相 PT30M+全部 digest_hour=9→同拍 10×digest+最坏 10×无头云端班并发（日帽为计数非并发·域锁不跨域）。**处置=留 v1.1**：今夜 23:13 首扫实锚=10 并发 digest 全成（L1 串行承载 OK）+9 班齐发工作正常；v1.1 建议=config digest_hour 分域错峰（9/9.5/10…）+跨域并发闸（fleet 级信号量）评估。
5. **状态写非原子（Set-Content 直写）**：崩半写=损态→喂红旗 2 成链。**处置=红旗 2 修复后自愈**（损态不再砖死·原子写 tmp+move 留 v1.1）。
6. **门段 TOCTOU**（锁检→Start-Process→写锁之间窗）：单域单任务串行=低危；Start-Process 失败时未写锁未计数=安全侧。**处置=判可接受·不修**。

## 建议项（非红旗）

- schtasks 多实例策略（IgnoreNew vs Parallel）依 task-register 注册面待证——若 Parallel 且运行 >30min 会双载体重入（今夜实锚：运行均 <30min=未触发）。
- digest 语义=「≥digest_hour 后当日首拍」非「指定时刻」——开 机于 23:xx 时 digest 落在 23:xx（当日一次·可接受·语义注记）。
- L1 长期不可达时 digest 每 30min 重试（每次 ~1s python 启动+拒连）=成本可接受；降级链按 G1+ 已走通（今夜 23:10-23:13 实锚）。
- `& python` 在 schtasks 环境的 PATH 解析待证（今夜任务环境实跑全通=已实证）。

## 判定

**PASS（修复后）**——初版三红旗全修（①②③当窗）+风暴面留 v1.1 错峰；今夜十域实弹（48 扫/日节奏首拍·10 digest·9 域班·锁门双跳验证）=可靠性面实证通过。
