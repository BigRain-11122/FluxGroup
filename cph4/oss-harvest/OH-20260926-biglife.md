# OH-20260926-biglife — 开源收获轮·BigLife 首窗切片 1

- **窗**：首窗 2026-09-26 21:40 → 2026-09-29 21:40；本切片=2026-09-26 22:2x（BigLife-OSLoop R381·P-2026-09-26-08·T-20260926-16 首片）。
- **实搜面（≥2 处·实录）**：①GitHub `python-jsonschema/jsonschema` 源页直验——License=MIT（源页 Resources 原文「MIT license」）·5.0k★·682 forks·3,128 commits·uv.lock/pre-commit/readthedocs 在树=活跃维护；②GitHub `promptfoo/promptfoo` LICENSE 页直验——License=MIT（原文标注）·Node.js 全栈坐实（package.json/pnpm-workspace/vitest 在树）·**健康面部分如实记**：该页视图未含 stars/最近 push/issue 数，候选判 parked 故不补抓（节流律）。
- **候选（五门评估 2 项）**：
  - **jsonschema**（源=https://github.com/python-jsonschema/jsonschema·MIT·JSON Schema 规范 Python 标准实现）：
    - 契合门 PASS：「替谁省什么」=替 BigLife QC 巡检（qc_census/pool_audit/make_digests 全手写结构断言）省重复断言——R3 再生面（citizens-light/citizen-behavior/citizen-needs/citizen-tasks）schema 一处定义行级校验复用；M2 消费面字段变更知会族（T-20260923-01 v1.2/v3.19）加 schema 漂移秒级暴露。
    - 反重复门 PASS：cph4/README.md 能力注册表 rg 零命中（jsonschema/schema/pytest/promptfoo 全零）+本司 Tools 21 py 全手写断言零 schema 库+Art Assets 池不涉（非美术件）。
    - 许可门 PASS：MIT=直用（源页原文直验）。
    - 健康门 PASS：5.0k★·682 forks·3,128 commits·Python 生态标准件。
    - 成本/安全门 PASS：纯 Python 本地库·零 GPU（P-17 矩阵不涉）·运行时零网络零外发·依赖面轻。
  - **promptfoo**（源=https://github.com/promptfoo/promptfoo·MIT·LLM prompt 评测 harness）：
    - 契合门 弱过：年轮 prompt 回归 harness 方向契合，但机审门断言集（27+ 断言 v0.34）已在 gate 内建自覆盖——增益集中在多模型对比矩阵，当前单模型栈（qwen2.5:7b）边际小。
    - 成本/安全门 FAIL（主判）：Node.js 全栈依赖引入 vs 本地纯 Python 断言栈·单模型 7b 无多模型对比需求。
- **姊妹线咬合注记（禁双轨·只供源）**：模型类发现本切片未触（未访 Ollama/HF 模型面=P-17/P-19 无触发）；AI 会话技能类未触（本机制只供源·归建走 P-2026-09-26-01 技能律）；美术资产未触。
- **采用→落点**：**jsonschema 采用**——落点三面=①任务单 T-20260926-17（QC schema 校验面接线·分步：R3 四面 JSON Schema 落件→qc_census --schema 接线→断言回归·下轮起小步）②cph4/README.md 能力注册表加行（oss-harvest §五 采用登记）③本台账文件。
- **parked+理由**：promptfoo=parked（成本门主判：Node 全栈依赖+单模型栈边际小+机审门断言自覆盖；若未来开多模型对比线重评）。实搜面 2 处全活面零死面。
- **下窗指针**：切片 2（窗内 ≤09-29 21:40·同文件续写）候选方向=①T-17 schema 接线实装后验收回写②`rapidfuzz`（基因轮近重防线自动化·对照 extend-gene-pool SKILL 手写 4gram 扫描面）③piper/kokoro 声码器族配套件（VOICE-POOL §四 多声源挂账次窗件对照）。

## 结论应用表（research-protocol 强制·无表=未交付）

| # | 发现 | 判定 | 落点（工作流变更） | 后续 |
|---|------|------|------|------|
| 1 | jsonschema（MIT·Python JSON Schema 标准件） | 五门全过→采用 | 任务单 T-20260926-17（QC schema 校验面接线）+cph4/README.md 注册表加行 | 下轮分步实装·接线后验收回写本台账 |
| 2 | promptfoo（MIT·prompt 评测 harness） | 成本门 FAIL 主判→parked | 无变更（不采） | 若开多模型对比线重评 |
| 3 | 实搜面 2 处（jsonschema/promptfoo 源页直验） | 搜索面实录·零死面 | —（实录面行） | 下窗换刀方向见下窗指针 |

- 三律自检：①业务契合=「替谁省什么」硬问收口（jsonschema=QC 巡检结构断言面）②不重复造轮子=反重复门三面查后过（注册表/本司工具清单/资产池）③科学使用=五门全过才采·parked 带理由禁悬空。
- 送达：本文件=R381 切片 1 落账（BigLife 仓 commit 含 P-2026-09-26-08·任务单 T-20260926-16/T-20260926-17 留痕行）；本实体单文件制+集团仓终接件零接触（跨仓写入遵 CEO 令法源·oss-harvest §六）。
