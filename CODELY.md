# FluxGroup · 项目识别卡（L1 自动注入面 · 2026-11-24）

> 用法：本卡每会话自动注入，负责"一屏认出"。完整记忆清单=`.codely-cli/memory.md`；判例原文=`.codely-cli/memory/topics/mem-20261124-*.md`；历史快照=`.codely-cli/memory/snapshots/`。
> 维护：只有「在产线 / 在飞待决 / 常设法条 / 触发词」变化时改本卡，细节不进本卡。
>
> **开场三步**：①读 §5 待决，看有没有要接的活；②按 §2 路由只读那一个主题文件，不要全量读记忆；③写记忆前过 memory-curator 五问（同题改写不新增 / >300 字下沉 topics / 跨机价值走 git）。

## 1. 在产线（CEO 11-24 口径：游戏侧只剩吸嘟嘟）

| 线 | 状态 | 正身 |
|---|---|---|
| 吸嘟嘟 GimmeAll（FAMILY-CAR-001·儿童+车机） | 唯一在产游戏；HMI Android，UI 定 2560×1600(16:10) | `D:\FluxGroup\gaming\MiniGame\09_吸嘟嘟_GimmeAll_CAR\GimmeAll`（团结 2022.3.62t17） |
| E541 儿童模式入口模型 | 已交付「拓扑版」，贴图 2048、不做 LOD | `C:\Users\sjs20\Desktop\E541\儿童模式\儿童模式_入口模型_拓扑版.blend` |
| 硅基城市（FluxVerse/City3D + BigLife/BigHouse） | 居民产线 24h 自跑；值守席 `life/BigLife/Tools/resident_steward.py` | `cph4/`、`life/BigLife/` |
| 机队（公司生产力机/传家宝/小钢炮/算力大脑 + MacBook 主控台） | 5 台常态；任务一律 S4U 注册 | 节点映射=`cph4/fleet/STATIONS.json` |

已关线（勿投入、勿自动复活）：地产 `house/`（11-16 收口）、fold-001（CEO 11-23 停）、MV `cph4/fleet/mv-album-001-jay/`（代码移交 `media/BigStream` 独立仓）、HMI 独立线（09-20 废止）。

## 2. 任务 → 先读哪个文件（省一轮检索）

> 下表省略了前缀：`topics/x` = `.codely-cli\memory\topics\x`；`memory.md` = `.codely-cli\memory.md`。

| 你要做 | 先读 |
|---|---|
| 资产建模/重拓扑/UV/烘焙/贴图 | `topics/mem-20261124-blender-asset-hardrules.md`（9 条硬律） |
| 写闸/判绿红/定阈值 | `topics/mem-20261124-gate-rigor-cases.md`（8 条）+ skill `gate-rigor` |
| 人脸一致性/LoRA/选角/素材 | `topics/mem-20261124-face-lora-material.md`（8 条）+ skill `mv-casting` |
| 数据对账/估算/回测 | `topics/mem-20261124-data-reconcile.md`（5 条） |
| git 推送/分叉/锁 | `topics/mem-20261124-git-push-surgery.md` |
| 视频交付/截图/抽帧 | `topics/mem-20261124-video-verify-capture.md` |
| 软著材料/AIGC 双闸 | `memory.md` 内工具链条 + `topics/mem-20261124-softcopyright-ai-tells.md` |
| BigLife 居民/文案质量 | `topics/mem-20261124-biglife-research-index.md` |
| 本地模型/显存/调度 | `topics/mem-20261124-local-model-pool.md` |
| 车机 16:10 适配 | `memory.md` 内「Play 设定与 16:10 布局约束」+ `D:\FluxGroup\media\family-assets\car-16x10\` |
| 记忆治理/写入 | skill `memory-curator` + `cph4/memory.md` §8-§10 |

## 3. CEO 常设法条（硬门·违反=返工或事故）

1. **静默**：零弹窗；禁 spawn 控制台子进程（用进程内 `& script.ps1`）；计划任务一律 S4U，禁 InteractiveToken。
2. **不许控制我的鼠标**（原话），自己静默完成。
3. **改前先 git 更新**（`python Tools/...` 前置），改 `.py` 禁 PS 内联，改完 `py_compile`+`import` 双验再 commit。
4. **决策**：科学理性、不要顺着说；重复令先查盘上现状再答；矛盾令点明冲突并选可逆一侧。
5. **一切测算按悲观档**（AI 时代供给爆棚），禁爆款假设。
6. **汇报**：大白话、结论先行、交付件给绝对路径、问题解决后才呈（禁中间态）。
7. **质量门**：导演席自审「自己挑不出毛病」才算过；数字过闸≠人眼过。
8. **效率**：低清验证→高清终版；同批不逐条重载；同配方抽检 10%。
9. **寻源**：动手前先搜 GitHub 高星现成轮子（星级/活跃度/license 三查）。
10. **云 token**：默认本地；云端=例外面；>500 积分等真金须 CEO 亲批。
11. **合规**：内部跑零介入，发布前才介入；真金法定红线与账号安全两条恒不变。
12. **账号安全**：写操作出事第一动作=停任务；清理方案先呈 CEO。
13. **音轨**：MV 成片只配歌，禁 AI 原生音轨。
14. **让路**：CEO 说「我要打游戏/我要工作」→ 立即 `machine-state.ps1 -Mode pause`（派活语义不触发）。

## 4. 触发词表（AI 识别用·同义归一）

- 吸嘟嘟 = GimmeAll = FAMILY-CAR-001 = 车机版 = G09
- E541 = 儿童模式入口模型 = 熊头彩虹置物架
- 硅基城市 = FluxVerse = City3D；BigLife = 居民/年轮；BigHouse = 安家
- 机器名 → 节点名只在命令里出现：公司生产力机/传家宝/小钢炮/算力大脑/MacBook
- 造闸 = 假绿·假红·负控·标定；幻影复用对 = 交付闸误报；幻影复用/自锁/僵尸锁 = 产线假活
- 导演席 = 强制自审门；D 产物链 = D1 叙事图→D7 终审；低清验证 = 480P 先验
- 软著双闸 = `softcopyright_audit` + `aigc_trace_audit`（豁免须附真实证据）

## 5. 在飞待决（下次会话先看这里）

- **吸嘟嘟**：16:10 布局未适配（A 翼压 144+键变窄变高 / B 缩玩法框 / C 键移框底，待选）；软著缺图鉴·商店·伙伴·独立签到四界面截图，现有截图带 Trial 水印须用正式包重拍；真机 launcher 未验；车机四风险中「Wx SDK 混入」已判误判，剩 PlayerPrefs 存档、性能零证据、文档入口缺失。
- **E541**：UV 面级纹素密度 CV 0.813（xatlas 重参数化 vs 人工接缝，待选）。
- **机队**：算力大脑（bm-d）双 CPU 不 POST，单 CPU 可跑。
- **记忆面**：全局 L0 仍 41KB（法条面，摘要需 CEO 点头）。

## 6. 不变量（写死·勿试）

- 事实必须工具实证：未跑过的不说"已完成"（已有三个假绿判例：commit ok / landed / SELFTEST PASS 之后仍为假）。
- 大文件红线：>95MB 绝对禁入 git；单件 >20MB 由 pre-commit 闸拦。
- 不杀他窗/他线进程；清孤儿锁前先验零持锁者（按命令行匹配，勿只看"有无 git.exe"）。
- 删改记忆/台账走「快照+归档」双通道，法条永不自动截断。
