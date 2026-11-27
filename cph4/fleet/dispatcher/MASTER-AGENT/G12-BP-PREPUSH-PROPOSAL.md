# G12 台账机核提案 — Branch Protection 轻档 + 全机 pre-push 钩子（候 CEO 一次同意·未同意零执行）

> 溯源：主AGENT 蓝图 v2 §九 G12+§十二 Phase 1-β-③（O-20261014-1745）。**账号治理面=CEO 保留域**（governance §4 物理件族）——本件=提案+命令级实施稿，已登记 DEADLINES.md §二 waiting-CEO 区，**零催办·同意即三机同夜落地**。
> GitHub 高星律字段：本提案无现成轮子可代（branch protection=GitHub 平台原生 API；pre-push 钩子=git 原生机制）——自定义面仅反转闸脚本（已 tracked）与哈希注册表（已 tracked），零新依赖。

## 一、提案两件套

1. **GitHub branch protection 轻档（10 仓 main）**：禁 force-push + 禁分支删除 + enforce_admins=false（CEO 保留应急通道）。**不开 required-PR**——机队三机+多窗原子推全部直推 main，required-PR 会让全集团工作流停摆（诚实工程取舍：我们要防的是历史改写与误删，不是自家人直推）。
2. **三机 pre-push 钩子（`git config core.hooksPath .githooks`）**：每次 push 前机核两道——
   - **反转闸**（Tools/git-no-reversal-check.py --depth 10）：近 10 笔 origin 增行不消失才放行——把三次丢行案的事后闸升为**结构性必跑**（pre-push 物理层·不靠任何窗口自觉）。
   - **受保护件哈希闸**（Tools/protected-hash-register.ps1 -Verify -SkipMissing）：strict 件漂移=拒推并提示「受保护件改动=CEO 令唯定谳——登记令号+重注册基线（-Register）后 `PROTECTED_ALLOW_DRIFT=1` 重推」；应急通道用环境变量显式放行（留审计面）。

## 二、为什么（危害序）

- 三次丢行案（10-09 吞暂存/10-11 clobber-1365/10-14 陈旧树回退）全部发生在 push 侧——pre-push 钩子=把反转闸从「窗口自觉跑」升「不跑就推不出去」。
- 禁 force-push 已在 cph4/versioning.md 成法——branch protection 把这条法从文档面升到 GitHub 平台机核面。
- 受保护件哈希锚基线已就位（Tools/protected-hash-registry.json·18 件·2026-10-14 22:38 基线）——pre-push=执法层第三道闸（蓝图 §九 哈希锚的机核出口）。

## 三、命令级实施稿（同意后执行）

### ① Branch protection（bm-a 一次执行·10 仓循环 ≈1 分钟）

仓库清单（BigRain-11122/）：FluxGroup·MiniGame·BigMoney·BigMoney-data·Bigmedia·Biglife·FluxVerse·BigDomain·BigCompute·BigHouse

```powershell
# 凭据=Windows 凭据管理器 git credential fill 通道（进程内即弃·零落盘——同 BigHouse 建仓件先例）
# 逐仓（gh 或 curl+token 皆可）：
PUT /repos/BigRain-11122/<repo>/branches/main/protection
{"required_status_checks":null,"enforce_admins":false,
 "required_pull_request_reviews":null,"restrictions":null,
 "allow_force_pushes":false,"allow_deletions":false}
# 验收：GET /repos/.../branches/main/protection 逐仓读回 allow_force_pushes=false+allow_deletions=false
```

### ② pre-push 钩子（随 git 分发·三机激活各一条命令）

`.githooks/pre-push`（POSIX sh·Git for Windows 自带 sh 执行·tracked 入库）：

```sh
#!/bin/sh
# pre-push gate: reversal check + protected-hash verify (G12, O-20261014-1745)
python Tools/git-no-reversal-check.py origin/main origin/main --depth 10
if [ $? -ne 0 ]; then
  echo "PUSH-BLOCKED: reversal gate (origin history lines disappearing)"
  exit 1
fi
powershell -NoProfile -ExecutionPolicy Bypass -File Tools/protected-hash-register.ps1 -Verify -SkipMissing
if [ $? -ne 0 ]; then
  if [ "$PROTECTED_ALLOW_DRIFT" = "1" ]; then
    echo "protected drift ALLOWED via PROTECTED_ALLOW_DRIFT=1 (registry meta.order must carry the CEO order)"
  else
    echo "PUSH-BLOCKED: protected-file drift needs CEO order + baseline re-register"
    exit 1
  fi
fi
exit 0
```

每机激活（幂等）：`git config core.hooksPath .githooks`
验收：本机故意构造一次反转（tmp 分支删行推主）→ 被 PUSH-BLOCKED 拦截的证据行 + 正常推全通过。

### 执行序（同意后一窗收口）

bm-a：①10 仓 protection API 落地+逐仓读回验收 → ②`.githooks/` 入库+原子推 → ③本机 hooksPath 激活+拦截实弹证据 → ④orders 行回执。
bm-b/bm-c：git pull（.githooks 随 git 到位）→ `git config core.hooksPath .githooks` → 一次试推回执（orders 行+HEAD sha）。

## 四、影响面与风险（诚实面）

1. 首版只护集团总控+九产品仓；嵌套产品内仓（BM 车道等）按需后续扩。
2. pre-push 每次多 ~1-3 秒（python 启动×2）——多窗热推期可接受（这两道闸本就该每次跑）。
3. dynamic 两件（硅基生命元宇宙.html/-data.js 每 5min 再生）哈希报告不拦——真闸待 generate.ps1 织入「每次生成留哈希档」（MiniGame 车道后续件·已在注册表 meta 注记）。
4. 三机均有 python；未来新机 onboarding 加一行 hooksPath 检查（cph4/onboarding.md 后续并档）。
5. 钩子只拦「历史增行消失」与「无令受保护件漂移」两类已知事故面·其余推流照常——不为拦截而拦截。

## 五、同意面

CEO 一句话（如「同意」「做」）= 同意令 → bm-a 当窗执行序 ①→④ + 派单 bm-b/bm-c 激活 → 回执窗 24h → 10-19 回访判据⑨（哈希基线在位+机核面数据）补全。
