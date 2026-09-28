# R-20260928-agent-skills-01 · 智能体 Skills 官方规范研读+公司技能生态审计

> CEO 令 U289（2026-09-28·「你好好再去研究一下相关的智能体 skills，研读官方规范和文档等。」）
> 四源：①skill-creator 内置件全文（Codely 一手编写规范）②Anthropic 官方 Agent Skills（code.claude.com/docs/en/skills + docs.anthropic.com best-practices 页）③Codely 文档站（/features-introduction/skills-experimental + /faq/common-questions）④本机三级生态盘点。

## 一、官方规范核心（四源合一）

### 1.1 格式与结构
- Skill = 目录 + SKILL.md（必需）+ 可选 scripts/ references/ assets/。**Agent Skills = Anthropic 原创的开放标准**（开放贡献·跨 agent 产品采纳）。
- SKILL.md = YAML frontmatter（**仅 name+description 两字段**·禁其他字段）+ Markdown 指令体。
  - `name`：≤64 字符，小写字母/数字/连字符，动词短语优先，目录名=技能名。
  - `description`：≤1024 字符，单行，**= 唯一触发面**：必须同时含「做什么+何时用」；body 里的 When-to-Use 无效（body 只在触发后才加载）。
- 体量预算：body **<500 行 / <5k 词**；超限即拆分到引用文件。

### 1.2 渐进披露（Progressive Disclosure·三层）
1. **元数据**（name+description）常驻上下文 ~100 词——一切技能的固定税；
2. **SKILL.md body** 触发时加载；
3. **打包资源**按需加载（脚本可不读入上下文直接执行=无限容量）。
- 引用文件**只许一层深**（直接链自 SKILL.md·禁深嵌套）；>100 行的引用文件加目录；>10k 词的文件在 SKILL.md 里配 grep 检索模式。
- 官方哲学：**context window = public good**——默认「模型已经很聪明」，只写模型不知道的；常驻面（CODELY.md 等）同样受此律约束。

### 1.3 三类资源分域
| 资源 | 用途 | 入上下文 |
|---|---|---|
| scripts/ | 确定性操作（脆弱/重复代码） | 可不读（直接执行）·stdout 须 LLM 友好（分页/截断/无 traceback） |
| references/ | 大文档按需读 | 按需 |
| assets/ | 输出资源（模板/字体/图标） | **永不** |
- 禁冗余文件（README/CHANGELOG/INSTALLATION 等）——技能只装 AI 干活要用的。

### 1.4 自由度三档
- 高自由（文字启发式）：多解开放任务；
- 中自由（伪代码+参数）：有偏好模式；
- 低自由（具体脚本少参数）：脆弱易错操作（窄桥加护栏）。

### 1.5 反模式（官方点名）
- **Windows 反斜杠路径禁用**（一律正斜杠 `scripts/helper.py`·跨平台）；
- 避免并列多方案（非必要不给选项）；
- 避免时效性信息（或归入 old-patterns 节）；
- 示例要具体不要抽象；术语全篇一致。

### 1.6 工具链与生效
- `init_skill.cjs`（模板化建件）→ 编写 → `package_skill.cjs`（自动验证：YAML/TODO 残留/命名/结构→打包 .skill）→ `codely skills install <path> --scope workspace|user [--consent]`。
- **物理件律：装后必须由用户手动 `/skills reload` 且新技能仅在新会话生效**（agent 不能代 reload）。

### 1.7 Codely 平台发现路径与优先级
- 工作区（`<CWD>/.codely-cli/skills/` 或 `.agents/skills/`·团队共享随项目）> 个人（`~/.codely-cli/skills/`）> 扩展技能；同层 `.agents` 优先。
- Skills ≠ 执行环境（只提供指令+模板，执行者是 agent）；不适合=纯内置命令。
- GUI：/skills 管理面板；@ 快速引用。

## 二、公司技能生态实况（2026-09-28 盘点）

| 层 | 数量 | 明细 |
|---|---|---|
| 用户级 | 42 件 | OSS 安装波（P-15）·**PROVENANCE.md 合规在册**：anthropics/skills(Apache-2.0)/obra-superpowers(MIT)/gamedev-skills(Apache-2.0)/trading(MIT)/avoid-ai-writing(MIT)/pixel-art-studio(MIT) |
| 内置 | 43 件可用 | Temp\codely-builtin-skills（含 skill-creator/codely-guide 等官方件） |
| 项目级（公司自建） | 13 件 | FluxGroup 根 7（asset-audit/city-3d×4/cph4-research-dispatch/lowpoly-city-3d）+FluxVerse 2（bake-pipeline/city-sandbox）+MiniGame 4（asset-config/audit-loop/research-loop/tick-loop） |

**结构合规审计（13/13 过关）**：全有 SKILL.md✓、frontmatter 仅 name+description✓、体量 12-123 行全 <500✓、描述含「做什么+触发场景」✓、无冗余文件（1-5 文件/件）✓。
**合规红线**：anthropics 官方 docx/pdf/pptx/xlsx = source-available **禁再分发、禁入公司仓**（PROVENANCE 已声明·git add 前查 PROVENANCE）。
**工作区隔离事实**：技能按 CWD 工作区生效——gaming 工作区自建技能此前 0 件（本批补 1）。

## 三、判例七律（U289 落册）

1. **分域四律**：skill=触发式工作流封装（触发词驱动·按需加载）/ 正典文件=制度与判据长存权威面 / CODELY.md=项目常驻规则（每会话必载·受 public-good 律克制）/ MCP=工具能力面。选择法：重复工作流+明确触发场景→skill；制度判据→正典；全局常驻约束→CODELY.md；新工具能力→MCP。
2. **描述=唯一触发面律**：what+when 全进 description；body 的 When-to-Use 段无效。
3. **渐进披露预算律**：body<500 行；引用一层深；大文件配目录+grep 模式。
4. **正斜杠律**：技能内路径一律正斜杠。
5. **新装生效物理件律**：装技能→提示用户手动 /skills reload→新会话生效。
6. **合规律**：外部技能入公司盘必记 PROVENANCE；source-available 件禁入公司仓。
7. **入库验证律**：公司技能定稿跑官方 validate 工具链（package_skill.cjs 校验面）后再装。

## 四、首件应用：五闸审查体系 skill 化（U288 执法载体）

`gaming/.codely-cli/skills/five-gate-review/`（本工作区游戏 UI 生产会话自动可见）：
- SKILL.md=五闸执行工作流（正典指针·不重复制度文本=分域律执法）；
- scripts/precheck_boards.py 随包（预检镜像闸·含 z 序覆盖探针）；
- 触发面=呈审前/审查复核/上线前检查类请求。
- 正典=MiniGame/_共享与总控/游戏UI交付五闸审查体系.md（判据唯一权威面·skill 只带行为）。

## 五、源指针

- https://code.claude.com/docs/en/skills （含 Quickstart+完整 Specification 入口）
- https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/best-practices
- https://codely-docs.tuanjie.cn/features-introduction/skills-experimental
- 本机 skill-creator 内置件（一手规范全文）+ PROVENANCE.md
