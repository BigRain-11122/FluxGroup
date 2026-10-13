# C-20261013-01 — 集团工作区清理与 git 卫生收口（委员会牵头·T1 代决）

> 令源：CEO 2026-10-13「委员会牵头进行一次清理和精简」。决策级=T1（即过即生效·预弃翻案权在册）。
> 立案窗：交互窗（委员会席）。执笔分工：安全层收口=本窗；正典层点名=导演席窗回执。

## 一、盘点结论（2026-10-13 22:3x 实测）

| 项 | 实测 | 判定 |
|---|---|---|
| 全局记忆 CODELY.md | 254KB→160KB（206→152 条） | ✅ 当日已深度精简（54 删+14 精简+2 合并），快照=cleanup-2026-10-13/ |
| docs/orders.md | 544KB | ⚠️ 审计面·全量留痕律**不物理拆分**；立监控线 >1MB 再专项 |
| docs/decisions.md | 214KB | 同上 |
| git 脏面 | 293 行（STALE>7天=105 / ACTIVE 近期=188） | ACTIVE=多窗在飞·不碰；STALE 收口见下 |
| git GONE（tracked 盘上无） | **98 件** | 他窗整理/删改后未提交的删除记录=ghost index，分两层收口 |
| cph4/labbench | 14GB（ACE-Step 模型+.venv） | ✅ gitignored 合规·模型资产不清理 |
| 30s-reel-v1 mp4 | 19 件 tracked·最大 44.7MB | ✅ 无 95MB 红线违例 |
| full_mv_v2_20261013.mp4 | 171.7MB·未 tracked·盘在 cph4 | ⚠️ 防误入：gitignore 定向规则（CEO 已令 cloudv2/cloud 类历史件保留归档不删——物理保留） |
| .codely-cli/tmp | 18.7MB/276 件·最老 09-28 | ✅ 全在 30 天内·不清 |

## 二、裁定（拍板五条）

1. **安全层 GONE 收口（本窗执行）**：产物/验证类 28 件（mv0001-handover/outbound 的 jman-lora-640 验证帧 21 件+cloud-v4-c mp4 5 件+PERFORMANCE-SPEC-v1.md+LOOKBOARD_variant_640.jpg）——盘面已删=既成事实，git add 记录删除+pathspec commit，零风险。
2. **正典层 GONE 点名（导演席窗回执）**：mv-album-001-jay 的 LAW/PANEL/SHOTLIST/local-i2v 系 ~66 件+C-20261011-01/02/03 案卷 3 件+meme-daily-v1 系 10 件——这些是正典/审计/评审件删除，**归执笔窗自决**（提交删除或恢复），本班 poke 送达；2 轮无回执按 EXECUTION-FIX 律本席接管按盘面现状收口。
3. **大件防误入**：.gitignore 增 `cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/full_mv_v2_20261013.mp4`（171.7MB·物理保留归档·git 防线防小时 chore 误扫）。
4. **台账体积监控线**：orders.md/decisions.md 属「唯一审计面」（governance §4），裁定不拆分；>1MB 触发专项归档案（历史行挪 docs/archive/·全量留痕律保真）。
5. **labbench/ace-step-15（14GB）**：gitignored 合规·ACE-Step 实验室资产不动；盘位占用呈报 CEO（若空间紧张可迁非工作区盘·属 CEO 物理件裁量）。

## 三、执行清单

- [x] ① 安全层 28 件删除收口 commit（本窗）
- [x] ② .gitignore 大件防线
- [x] ③ orders.md 落账一行 + decisions.md 台账一行
- [ ] ④ 导演席窗 poke（正典层 66+3+10 件点名·回执窗 2 轮）
- [x] ⑤ 案卷归档 cph4/council/C-20261013-01-cleanup-bill.md

## 四、依据

CEO 令 2026-10-13（委员会牵头清理精简）+U187 大文件红线+脏面两分律（C-20261009-03 基线 v1）+全量留痕律（governance §4）+cloudv2 保留归档令（O-20261013-2200 ③）。
