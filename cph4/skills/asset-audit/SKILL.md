---
name: asset-audit
description: 集团资源规范审核技能（Unity/团结引擎资产：命名硬规则、切图尺寸、UI alpha 通道、导入设置 meta、同内容冗余→Atlas 候选；上游包豁免）。当需要对游戏项目 Assets 做资源审核、批量切图/生成资产入库把关、或发布前资产体检时使用。执行 Tools/asset-audit.ps1，把英文报告渲染成中文审核结论。
---

# Asset Audit（资源规范审核）

工具=`Tools/asset-audit.ps1` v1.1（ASCII-only·编码律·只读·PS5.1 安全）。产物=报告 md（UTF-8 无 BOM）。

## 规则基线 v1.1（2026-09-28 立·当日即校准——v1.0 采样过窄把混大小写误判 FAIL，经 City 1565 件全量首扫实证后修正）

1. **命名硬规则（FAIL 级）**：仅禁中文/非 ASCII/空格/首尾及连续分隔符——这才是真断链风险面（URI/工具链/GBK）。
2. **混大小写 = INFO 级**：罗盘方位/结构语义后缀（NE/NW/H/V/T_E）是本道既有惯例（td-tileset.py 产出即此风格）；**新第一方资产仍建议全小写**（导向不追溯）。
3. **上游包豁免**：`ArtPacks/`、`Art/CleanCityv3/` 等第三方包根保留原名（许可台账可溯源+代码路径稳定）；`-ExemptDirs` 可扩展。**禁止返工级改名 churn**：GUID/meta 扰动与多窗撞车风险 > 零功能收益（2026-09-28 判例：788 项"违规"经分类全为大小写/包原名，零改名为正解）。
4. **切图尺寸**：≤128px 图标类自由尺寸；>128px 纹理建议 2 的幂（WARN 级 advisory，不拦）。
5. **UI 资产 alpha**：`\UI\` 路径或 UI 前缀件必须有 alpha 通道（FAIL 级）。
6. **格式**：png/jpg 白名单；BMP/TGA 等=FAIL；PNG >4MB=WARN。
7. **导入设置**：`.meta` 在盘时 UI 类校验 `textureType=8`(Sprite)（上游包豁免）；无 meta=PENDING——编辑器导入刷新后重审转正，禁虚报。
8. **同内容冗余**：MD5 全同对 → WARN + Sprite Atlas 合并候选；注意 U276 官方判例（团结多纹理压缩不支持图集）——合并动作走项目决策面，勿 CLI 批量擅动。

## 用法

```
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\asset-audit.ps1 -Path "gaming\FluxVerse\City\Assets" [-ExemptDirs "ArtPacks,CleanCityv3"] [-Report "<path>"]
```

- `-Path`：单个资产文件或目录（目录=递归扫全部 png+冗余扫描）。
- 退出码：0=无 FAIL；1=有 FAIL；2=路径不存在。

## 报告纪律（诚实律映射）

- PASS→✓ / WARN·INFO→🟡 / FAIL→✗ / PENDING→🟡（待编辑器导入；刷新后重跑方可转 ✓，禁虚报为已导入）。
- 报告文件为 ASCII 英文（编码律），向 CEO 呈现时译为中文并逐行附证据。
- **呈 CEO 一律绝对路径（C:\ 起头）+当场打开+桌面 bat 一键入口**（交付路径可靠律 09-28 立法）。
- 子仓路径（gaming/FluxVerse、gaming/MiniGame 等为 gitignored 子仓）本脚本走原生文件系统无检索跳坑问题；用 glob/search 工具核证相关文件时须记得子仓跳坑律。

## 关联正典（交叉引用）

- UI 单件生成母版制：`MiniGame/_共享与总控/UI元件生图风格母版SOP.md`（U284·生图禁裸跑必垫母版）——审核发现无母版出处的 UI 件时标记锚渗漏风险，勿当风格参考采信。
- 资产分类/规格/密度：`MiniGame/_共享与总控/小游戏2D资产全景图谱与规格要点.md`（U275·D1-D7 密度律）。
- 证据截图入仓一律 JPEG q88 化（MiniGame GitBloatGate 律·SOFT 1.5MB/HARD 6MB）。

## 已知事实（实测累积）

- TJGenerators `generate_image` 传小尺寸（如 48x48）会被服务端上采样（实测 48 请求→1920 输出），小图交付须本地下采样（System.Drawing·HighQualityBicubic）。
- 分割模式（is_segmentation）输出带 alpha 透明 PNG ✓。
- 2026-09-28 City 全量首扫附产：城内文字文案面=0（4 个场景/预制体+42 个脚本均无 CJK 文案行）——文案迭代无存量；未来参观端开门帧 AIGC 标识落地时纳入审核面。
- PS5.1 无 `-notcmatch` 运算符，正确拼写=`-cnotmatch`（2026-09-28 实证解析错误）。
