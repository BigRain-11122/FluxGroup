# R-20260929-animation-gap-report — 城市动画缺口呈报件（CEO 令 2026-09-29 动画线盘点·bm-a 机）
> 溯源：CEO 令 2026-09-29「3D 资源禁云端生成·资源库=唯一来源·真缺口=呈报 CEO 填库」（任务简报转述）·消费方=CEO 填库决策·判据=①AD-042/Kaykit 在库实况 ②需求×在库映射 ③缺口清单

## ① 在库清单（实测）
- **City3D 九包**（Assets\lowpoly 实测 9）：AD-015 植被 / AD-025 白盒 / AD-048 起始 / AD-022 现代城市 / **AD-042 都市人物** / AD-018 科幻城 / AD-020 太空 / AD-010 粒子 / AD-039 图标——人物包仅 AD-042 一包。
- **AD-042 逐件**：19 prefab，全部带 SkinnedMeshRenderer（骨骼蒙皮）+ Animator 组件但 m_Controller=fileID:0（空控制器·19/19 实测）+ 0 AnimationClip；共享 Character.fbx 且 clipAnimations:[]（零内嵌动画）：
  - Biker / FastFoodGuy / FireFighter / GamerGirl / Gangster / Grandma / Grandpa / HipsterGirl / HipsterGuy / Hobo
  - Hotdog / Jock / Paramedic / PunkGirl / PunkGuy / Roadworker / ShopKeeper / SummerGirl / Tourist
  - 同包镜像存在于 P3D_Spike 与 Art Assets（Test-Path 双 True·同构无增量动画件）
- **库内动画件实测**：City3D 全 Assets=.anim×1（AD-010 Pivot_Spin 特效旋转）+.controller×0；P3D_Spike=.anim×26+.controller×12 全为特效/道具件（灯脉冲/旋转/齿轮/无人机/水轮·AD-031 角色控制器=空壳状态）；唯一真实动画角色=AD-003 狗（四足·非人形）→ **人形角色骨骼动画 0 条**；Art Assets\lowpoly 48 包动画件×38 同类。
- **Kaykit 盘点结果**：全 FluxGroup 物理检索 ×0 命中 → **在册未入库=最大缺口（路径无）**。台账承接（R-20260928-alive3d-04·CC0 已核验·仅类名无逐类精确计数）：161 条 humanoid=移动(走/跑/跳/爬/潜行/闪避/蹲)·通用(待机/被击/死亡/生成/交互)·近战(一/双手/双持/格挡)·远程(射击/瞄准/装填/弓/法术)·emote(挥手/欢呼/坐/躺)·工具(掘/撬锁/钓/锤/通用工作/挖矿)；FREE 档 150+ 条零成本·FBX+GLTF；rig 注意=Kaykit 自有 Rig_Medium/Large≠Mixamo≠Synty rig，入库后须 retarget 方可挂 AD-042。

## ② 需求 × 在库映射（居民形态 C 混合双态：L1 假动画 / L2 骨骼动画）
| 需求 | 在库现状 | 判定 |
|---|---|---|
| L1 行人假动画（无骨骼·首选） | AD-042 19 件定姿+位移即可（脚本自研件） | ✅ 已覆盖 |
| idle 待机系（站立/看手机/交谈） | 库内 0；Kaykit 有基础待机（未入库），无看手机/交谈 | ❌ 缺口（基础随③-1 解·特化归③-2） |
| walk 行走系（常速/匆忙） | 库内 0；Kaykit 走/跑/潜行（未入库） | ❌ 缺口（随③-1 解） |
| work 工作系（打字/搬运/售卖） | 库内 0；Kaykit 仅锤/掘/通用工作 | ❌ 缺口（③-1 后仍缺都市类） |
| 社交系（两人交谈/聚会） | 库内 0；Kaykit 仅单人 emote（挥手/欢呼/坐） | ❌ 缺口（双人互动全缺） |
| 通勤系（上下班/候车） | 库内 0；walk+idle 组合可近似，特化件缺 | 🟡 部分（组合代·特化归③-2） |

## ③ 缺口呈报表（应用表·落点=决策呈报：CEO 填库令·本机禁自行补）
| # | 缺口 | 用途 | 建议来源类型 |
|---|---|---|---|
| 1 | Kaykit 161 条动画包物理未入库 | L2 实体城全部骨骼动画底座 | CEO 填库：kaylousberg.itch.io「KayKit Character Animations」FREE 档（CC0 台账已核验·零成本·下载即解） |
| 2 | 都市日常特化动画：看手机/打字/售卖/搬运/候车 | L2 都市活感（Kaykit 161 清单无此四类） | CEO 填库方向：Kaykit 扩展包若无·则 itch.io CC0 都市生活动画包（Mixamo 免费但许可非 CC0·按 CC0 律不采） |
| 3 | 双人社交动画（两人交谈/聚会互动） | L2 社交面 | CEO 填库方向：CC0 双人互动包（市场稀缺·请 CEO 裁是否降级为单人 emote 对摆替代） |
| 4 | （工程件·非填库）Kaykit→Synty retarget+城市 AnimatorController 编排 | ③-1 落地到 AD-042 的施工件 | 自研工程件·不占填库决策 |

## ④ 一句话结论
库内人形骨骼动画为 0（AD-042 仅 19 具空 Animator 骨架），最大缺口=Kaykit 161 条在册未入库（FREE 档零成本·CEO 一句话即可填库），都市特化与双人社交为 Kaykit 之外真缺口待 CEO 定填库方向。

## 验证声明
- 实测路径：City3D\Assets\lowpoly 九包枚举；AD-042 逐 prefab 19/19（m_Controller=fileID:0·Character.fbx clipAnimations:[]）；P3D_Spike\Assets 全量 .anim×26/.controller×12 逐件；Art Assets\lowpoly 48 包+动画件×38。
- 实测命令：Get-ChildItem -Recurse（枚举/分组/清单）；rg --no-ignore --hidden --glob-case-insensitive -g "*kaykit*"/"*anim*.fbx"/"*.blend"/"*kaylousberg*"/"*skeleton*" 全 FluxGroup（含 gaming 子仓·×0 命中）；rg --no-ignore 直读 .prefab/.controller/.fbx.meta。
- 防线二（承重负主张独立复核）：「Kaykit 不在库」四法交叉验证一致（Get-ChildItem 目录名 *aykit* 两域+rg 全域文件名+备名法 anim.fbx/blend/kaylousberg/skeleton）；Kaykit 161 条分类=R-20260928-alive3d-04 web 核验台账承接（本次未重访 web·零下载零云端生成）。
- 更新记录：T0 双法盘点采集 → T1 AD-042 逐件+全库动画件清点 → T2 Kaykit 多法检索定谳「在册未入库」→ 终稿 38 行（node 字节级复核 ≤60）。
