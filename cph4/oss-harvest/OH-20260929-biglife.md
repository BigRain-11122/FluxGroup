# OH-20260929-biglife — 开源收获轮·BigLife 第二窗切片 1

- **窗**：第二窗 2026-09-29 21:40 → 2026-10-02 21:40；本切片=2026-09-29 21:4x（BigLife-OSLoop R696·P-2026-09-26-08 常设令·T-20260926-16 新窗首片·承上窗切片 3 下窗指针①ruff 族对照）。
- **实搜面（≥2 处·实录·全活面零死面）**：①GitHub `astral-sh/ruff` 仓库源页直验——License 原文「Ruff is released under the MIT license.」+「This repository is licensed under the MIT License」·维护方=Astral（uv/ty 同门）·源页使用者名录=Apache Airflow/Apache Superset/FastAPI/Hugging Face/Pandas/SciPy；②PyPI `ruff` 项目页直验——**0.16.9 released 2026-09-24**（5 天前·周更节奏 3 年+在产·release history 实录）·License Expression=MIT·win_amd64 wheel 10.6MB·Python 3.14 兼容·**Trusted Publishing**（uv/0.12.18 上传签名链+PyPI provenance 验证）；③本机 uvx 实弹面——`uvx ruff@0.16.9`（244ms 装载 10.1MiB·零永久依赖）扫 Tools 产线（22 件=R517 盘点在册）。
- **候选（五门评估·ruff）**：
  - 契合门 **弱过（advisory 形实测定谳）**：上窗预注册硬问「每轮交付前手工复审可否由 linter 拦截类缺陷」**实测定谳=可拦截类存在但低危**——默认扫 **700 命中**（噪声地板=UP031 printf 风格 245+BLE001 77/S110 22 有意静默惯用法+DTZ 族本地时区有意 naive+I001 32 风格）vs **curated 真信号基线 44**（SIM115 开文件无 with 25+F401 未用 import 10+F841 未用变量 5+RUF059 未用解包 4·F811 0）；高严重类 B023（函数捕获循环变量）6 处逐处复核=**同迭代定义即用惯用法良性误报**（generate_census.py take() 定义并在同一循环迭代内调用·ruff 无法证明调用域）。「替谁省什么」=替交付前手工复审省死代码/句柄卫生类的逐眼扫描——新工具交付节奏快（近两日 +citizen_anchors/+citizen_assembly 两件）→ **增量门（新/改 .py 交付前 advisory 扫）有持续消费面**；**存量 44 处=豁免记档零回改**（稳定工具 churn 风险律·--qc 电池为回归主层不变）。
  - 反重复门 PASS：cph4/README.md 注册表 rg 零命中（ruff/lint/py_compile 全零·PSScriptAnalyzer=FluxVerse PS 域异语言非双建）+本司 Tools 零 linter 层零 py_compile 惯例（运行时 --qc 电池=既有回归层·静检层=新增非重复）+Art Assets 池/docs 域零命中。
  - 许可门 PASS：MIT（GitHub 源页+PyPI License Expression 双源原文直验）。
  - 健康门 PASS：0.16.9（2026-09-24 发布）·周更节奏 3 年+·Trusted Publishing 签名链·pandas/scipy/fastapi/HF 在用·Rust 实现 Python 生态标准件。
  - 成本/安全门 PASS：uvx 临时执行零永久依赖（版本锚 ruff@0.16.9=确定性）·10.1MiB 一次性装载·零 GPU（P-17 矩阵不涉）·运行时零网络零外发·扫描毫秒级。
- **采用→落点**：**ruff 采用（advisory 增量静检门）**——落点三面=①任务单 **T-20260929-07**（静检门接线：curated 规则集 `F401,F811,F841,SIM115,RUF059`·增量面=新/改 .py 交付前 `uvx ruff@0.16.9 check --select F401,F811,F841,SIM115,RUF059 <files>`·advisory=命中即修或一行记档·不 fail-fast 不断产线·存量 44 豁免基线记档）②cph4/README.md 能力注册表加行（oss-harvest §五 采用登记）③本台账文件。
- **parked+理由**：①**ruff 默认全规则集**=parked（噪声地板 700 命中——风格类/有意静默惯用法/本地时区有意 naive=本司惯用法域·advisory 增量门只采 curated 子集）；②**Ollama 生态评测 harness 重扫**（上窗指针②）=parked 承下片（本片预算让位首片·promptfoo Node 栈判例 standing·机审门 v0.43 断言自足性复评留下片）。
- **下窗指针**：切片 2（窗内 ≤10-02 21:40·同文件续写）候选方向=①Ollama 评测 harness 重扫（机审门断言自足性复评·promptfoo 判例参照）②T-20260929-07 增量门首轮实弹验收回写（下一件新/改工具交付时·命中数+处置行入实录）。

## 切片 1 结论应用表（research-protocol 强制·无表=未交付）

| # | 发现 | 判定 | 落点（工作流变更） | 后续 |
|---|------|------|------|------|
| 10 | ruff（MIT·0.16.9=2026-09-24·Rust linter 标准件·Trusted Publishing） | 五门过（契合=advisory 弱过实测定谳）→**采用 curated 增量门** | 任务单 T-20260929-07（交付前新/改 .py advisory 扫·规则集五类）+cph4/README.md 注册表加行 | 下一件新/改工具交付时实弹验收回写 |
| 11 | ruff 默认全规则集形态 | 噪声地板 700 命中（风格/静默/naive 惯用法域）→parked | 无变更（不采全规则） | 契合类新需求触发再评 |
| 12 | 实搜面 3 处（GitHub 源页+PyPI 项目页+本机 uvx 实弹扫） | 搜索面实录·零死面 | —（实录面行） | 下片换刀方向见下窗指针 |

- 三律自检（切片 1）：①业务契合=预注册硬问实测定谳（可拦截类=低危真信号 44·adopt 收窄 advisory 增量门防噪声）②不重复造轮子=反重复门三面查后过（静检层=新增非重复·--qc 电池回归层不动）③科学使用=五门全过才采·parked 带理由禁悬空。
- 送达：本文件=R696 新窗切片 1 落账（BigLife 仓 commit 含 T-20260926-16 新窗首片行+新单 T-20260929-07 留痕）；本实体单文件制+集团仓终接件零接触（跨仓写入遵 CEO 令法源·oss-harvest §六）。
