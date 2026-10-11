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

## 切片 2（2026-09-27 03:5x · BigLife-OSLoop R416 · 承切片 1 下窗指针）

- **窗**：首窗 2026-09-26 21:40 → 2026-09-29 21:40 内第二切片（T-20260926-16 切片 2）。
- **实搜面（≥2 处·实录·全活面零死面）**：①GitHub `rapidfuzz/rapidfuzz` org 源页直验——Python 版 **4.1k★/174 forks**·多语言家族（Python/C++/Rust）；②PyPI `rapidfuzz` 项目页直验——**License=MIT**（项目页 LICENSE 节原文「RapidFuzz is licensed under the MIT license…」+License Expression=MIT）·最新版 **3.14.6 released 2026-08-30**（~4 周前=活跃）·维护者 maxbachmann·**Trusted Publishing**（GitHub Actions 签名+PyPI provenance 验证在案）·win_amd64 wheel 在供（cp311~cp315·1.8MB）·Python ≥3.11·Windows 前置=VC++ 2019 redistributable。
- **候选（五门评估）**：
  - **rapidfuzz**（源=https://github.com/rapidfuzz/RapidFuzz·MIT·4.1k★·模糊字符串匹配标准件·C++ 实现+预编 wheel）：
    - 契合门 PASS：「替谁省什么」=替基因轮近重预检省手写临时 4-gram 扫描件——R406 预检三跑拦 10 处、R413 五跑拦 12 处（临时件每轮重写·跑后即删·多跑收敛），rapidfuzz `process.extract` 阈值化近重候选一行即得（Levenshtein/ratio 族度量·确定性双跑可断言）=临时件转常设工具的机械执法面。
    - 反重复门 PASS：cph4/README.md 注册表 rg 零命中（rapidfuzz/fuzzy/近重）+本司 Tools 零 fuzzy 匹配库（rumor_chain.py「fuzz」=失真算子闭集非字符串匹配）+Art Assets 池不涉。
    - 许可门 PASS：MIT（PyPI 项目页 LICENSE 节原文直验）。
    - 健康门 PASS：4.1k★·174 forks·3.14.6（2026-08-30）·Trusted Publishing 签名链·Python 生态标准件。
    - 成本/安全门 PASS：本地 pip 纯库·win_amd64 wheel 1.8MB·零 GPU·运行时零网络零外发；本机 Python 3.14.4 满足 ≥3.11+pip 26.0.1 在位（探针实测）；前置=VC++ 2019 redistributable（若安装失败=如实记档回退手写线）。
  - **piper/kokoro 声码器族配套件**（切片 1 下窗指针候选③）：**parked 前置定谳（不采不评深）**——多声源终解已由 T-20260926-06 收口（kokoro fp32 生产默认·piper zh 单基音试点后淘汰于 T-20260925-21）·VOICE-POOL §四 余项=预留层听感验证窗 M 级待证（启用三前置=盲测 ≥5/5+T2+消费方任务单）=当前零消费方任务单（反无消费方立项律）·License 未验明即不采不触（许可门禁自洽）。
- **T-17 验收回写（切片 1 下窗指针候选①兑现）**：jsonschema 采用件验收=**T-20260926-17 整单关结（R387 分步①+R388 分步②③）**——qc_census.py --schema 结构层在役（Tools/schemas/ 四面单源复用·Draft202012Validator）·T2=CODEX §十二 v3.32；本切片复跑实弹 `python -X utf8 Tools/qc_census.py --schema`：**cards=10003 evolved=2384 problems=0 schema_rows=51883 schema_bad=0**（与 R388 交付值 51883 一致·结构漂移秒级暴露设计目的持续在役·M2 字段变更知会族 T-20260923-01 消费面受益在案）。
- **采用→落点**：**rapidfuzz 采用**——落点三面=①任务单 **T-20260927-01**（基因轮近重预检固化件·下轮起小步自领）②cph4/README.md 能力注册表加行（oss-harvest §五 采用登记·第三例）③本台账切片 2 节。
- **parked+理由**：piper/kokoro 声码器族配套件=parked（多声源已终解 kokoro fp32+零消费方任务单+预留层启用三前置未备；v1_1 扩池/听感验证窗触发再重评）。
- **下窗指针**：切片 3（窗内 ≤09-29 21:40·同文件续写）候选方向=①T-20260927-01 近重预检固化件实装后验收回写②pytest 族对照（机审门断言电池现状盘点后定采否）③池同质度复测窗新批触发时记录。

### 切片 2 结论应用表（research-protocol 强制·无表=未交付）

| # | 发现 | 判定 | 落点（工作流变更） | 后续 |
|---|------|------|------|------|
| 4 | rapidfuzz（MIT·4.1k★·模糊匹配标准件） | 五门全过→采用 | 任务单 T-20260927-01（基因轮近重预检固化件）+cph4/README.md 注册表加行 | 下轮分步实装·接线后验收回写本台账 |
| 5 | piper/kokoro 声码器族配套件 | 契合前置定谳零消费方→parked | 无变更（不采） | 多声源扩池需求触发再重评 |
| 6 | T-17 验收回写（切片 1 采用件 jsonschema） | 验收 PASS（--schema 复跑 51883/bad=0） | 已在役（R387/R388 落地） | QC 巡检随轮续跑 |
| 7 | 实搜面 2 处（rapidfuzz GitHub org+PyPI 源页直验） | 搜索面实录·零死面 | —（实录面行） | 下窗换刀方向见下窗指针 |

- 三律自检（切片 2）：①业务契合=「替谁省什么」硬问收口（rapidfuzz=基因轮近重预检临时件转常设）②不重复造轮子=反重复门三面查后过③科学使用=五门全过才采·parked 带理由禁悬空。
- 送达：本节=R416 切片 2 落账（BigLife 仓 commit 含 P-2026-09-26-08·任务单 T-20260926-16 切片 2 行+新单 T-20260927-01 留痕）。

### 切片 2 验收回写（R418·2026-09-27）

- T-20260927-01 分步②③ 交付=结论应用表 #4 落点闭环：Tools/gene_nearcheck.py v1.0（Layer A=候选 4-gram 对基因库全文本池重叠扫描+Layer B=同型池 rapidfuzz fuzz.ratio 阈值层〔cp92/ho95/tp44=R417 三池基线定谳〕·--qc 15/15·--baseline 漂移监控）·实弹验收=灵敏度门 R406/R413 手写件拦截实录 10 片段全数回收+负对照 2/2 CLEAN·exit 1 fail-fast·基因轮 extend-gene-pool SKILL 查一接线（手写临时 4-gram 件退役）·T2=CODEX §十二 v3.41（否决窗至 2026-10-04）——回写即闭环，切片 2 交付链（采用→立单→实装→验收）全毕。

## 切片 3（R517·2026-09-27 21:4x·pytest 族对照·下窗指针②兑现）

- **窗**：首窗 2026-09-26 21:40 → 2026-09-29 21:40 内第三切片（窗内义务 ≥1·三切片超额完成）。下窗指针①（T-20260927-01 验收回写）已随 R418 并入切片 2 节·③（池同质度复测窗）未触发（池 1440 满额自停态·R408 B 片复测 4/4 在案）→本片=指针② pytest 族对照。
- **实搜面（3 处·1 死面 2 活面·实录）**：①PyPI `project/pytest` 项目页=**死面如实记**（JS 墙拦截·页面不可达·不重试不臆测版本数据）；②GitHub `pytest-dev/pytest` 仓库 About/License 节直验——**License=MIT 原文**（「Copyright Holger Krekel and others, 2004. Distributed under the terms of the MIT license…」）·**14.5k★·3.4k forks·195 watching·17,784 commits**·维护方=pytest-dev org；③GitHub Releases 页直验——**Latest=9.1.1**（8.4.1=2025-06-17·8.4.0=2025-06-02 可验锚·8.4.x→9.0.x→9.1.x 多大版本序列在产=活跃维护）。
- **候选（五门评估·机审门断言电池现状盘点先行）**：现状盘点实测=Tools 22 件工具内建 `--qc` 断言电池（rg 实测 22 文件命中）+交付期临时自测件惯例（跑后即删·断言随后折叠入工具 --qc 电池=常设回归层·如 resident_intake 137/137·city_chronicle 23/23·interchat_ledger 16/16）——**pytest**（源=github.com/pytest-dev/pytest·MIT·14.5k★·Python 测试框架标准件）：
  - 契合门 **不过**：「替谁省什么」硬问无强解——现役回归需求已由 22 件 --qc 电池覆盖（随 git 分发·每轮实跑·确定性双跑断言内建·exit-code 集成无人值守轮自动化面自足）；临时自测件的最后一个真实痛点（基因轮近重预检每轮重写）已由切片 2 rapidfuzz 采用件 gene_nearcheck v1.0 收口（R418·手写临时件退役）；pytest 边际价值（测试发现/富报告/参数化/并行）无对应消费方痛点=反无消费方立项律同源。
  - 反重复门 **不过**：pytest 测试层与 --qc 电池层双轨并存=惯例级双建（22 件在役电池零迁移收益·双测试惯例维护成本净增）。
  - 许可门 PASS：MIT（仓库 License 节原文直验）。
  - 健康门 PASS：14.5k★·3.4k forks·17,784 commits·9.1.1 Latest·多大版本序列活跃。
  - 成本/安全门 技术面 PASS：本地 pip 纯库·运行时零网络零外发·零 GPU；如实记=新增工具链依赖+T2 面+轮内调用面改动=流程成本非零。
- **采用→落点**：无（零采用）。
- **parked+理由**：pytest=parked——主判=契合门（零消费方痛点）+反重复门（惯例级双建）；许可/健康/成本技术面三门过如实记。**重开窗三触发器**：①多工具跨件联合回归需求出现（--qc 单件电池不敷跨件编排时）②--qc 电池维护成本实测上探③交互开发会话频度上升使富报告/失败定位产生边际价值。
- **下窗指针**：新窗 2026-09-29 21:40 起=**新台账文件 OH-20260929-biglife.md**（一窗一文件律）·候选方向=①ruff 族对照（代码静检面——py_compile 只查语法不查语义·契合硬问=「每轮交付前手工复审可否由 linter 拦截类缺陷」待实测定谳）②年轮/池产线 Ollama 生态评测 harness 候选重扫（机审门断言自足性复评·promptfoo Node 栈判例参照）。

### 切片 3 结论应用表（research-protocol 强制·无表=未交付）

| # | 发现 | 判定 | 落点（工作流变更） | 后续 |
|---|------|------|------|------|
| 8 | pytest（MIT·14.5k★·测试框架标准件） | 契合/反重复双主判不过→parked | 无变更（不采） | 重开窗三触发器（上列） |
| 9 | 实搜面 3 处（PyPI 死面+GitHub About/Releases 活面） | 搜索面实录·1 死面 2 活面 | —（实录面行） | 下窗换刀方向见下窗指针 |

- 三律自检（切片 3）：①业务契合=硬问诚实收口（无痛点不采·禁为采而采）②不重复造轮子=反重复门惯例级双建拦下③科学使用=parked 带理由禁悬空+重开窗触发器预注册。
- 送达：本节=R517 切片 3 落账（BigLife 仓轮末 commit 含 T-20260926-16 切片 3 关结行留痕）。
