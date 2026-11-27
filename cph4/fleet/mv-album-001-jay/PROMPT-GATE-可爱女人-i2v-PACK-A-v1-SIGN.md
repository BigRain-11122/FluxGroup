# PROMPT-GATE-可爱女人-i2v-PACK-A-v1-SIGN（第 3 层导演席合并签发）

- **gate id**：PROMPT-GATE-可爱女人-i2v-PACK-A-v1 · 2026-10-24 04:5x（Get-Date 实测）
- **承令**：O-20261023-2325-bm-a「其余 MV 交机队重跑」· 站序=站1 首帧闸 → 站2 提示词闸 → 站3 480P→768P
- **审对象**：`可爱女人-i2v-PACK-A-v1.json`（30 单 · `可爱女人-shots-v2.py` **v2.8** · 1344×768 int8 正档）
- **分权**：**审=独立评审席 ×2**（B1+B2 席 / B3+B4 席，均非作者席非导演席，只报发现）· **改=作者席（v2.8 落位 18 项）** · **复核=机核（lint+guard 三跑零命中）+ 导演席逐条对首帧复读**（按三次代理重读禁令：不重开第三席重读）
- **签=导演席（本窗）**

## 一、第 1 层 机械闸回执

见 `PROMPT-GATE-可爱女人-i2v-PACK-A-v1-L1.md`：30/30 lint（video）零命中 · 30/30 `preflight_gate.guard(kf_verified=True, kf_note=FRAME-GATE-KN-PACKA-c2166, kinds=[])` 返回空列表 · 词数 72–117 · 总窗 196.35s · 30 帧全在位。

## 二、第 2 层 四块 verdict 合并表

| 块 | units | verdict 文件 | 计数 | 备注 |
|---|---|---|---|---|
| B1 | KN01-08 | `-B1.md` | PASS 5 / FIX 3 / REJECT 0 | 大机五镜构图偏差、纸面两族、红尾时机、水塔四版 |
| B2 | KN09-15 | `-B2.md` | PASS 2 / FIX 5 / REJECT 0 | KN15 整段色彩链风险、排除式措辞记机制 |
| B3 | KN16-23 | `-B3.md` | PASS 5 / FIX 5 / REJECT 0 | 尾挂身份句=系统性缺陷；KN22b 水塔=木质圆筒实测 |
| B4 | KN24-30 | `-B4.md` | PASS 0 / FIX 5 / REJECT 0 | 纸面两族按帧打标；KN24 抬眼三检；KN30 末段硬静 |

**合计：PASS 12 / FIX 18 / REJECT 0。**

## 三、FIX 落位记（v2.8 · 18/18 全落）

| 类别 | 落位 |
|---|---|
| 身份口径 | **删除全批尾挂身份句**（PAPER_LOCK/TOWER_LOCK 撤；原句与各帧纸色/水塔形制冲突）→ 改「按帧对齐」：KN21/24/28 cream+红在尾尖；KN29 左机横格纸/右机 cream 红在尾；KN30 横格白机+cream 红尾；KN22b 水塔=dark wooden water tank on steel legs；KN16 删 unruled/small |
| 景别机位 | KN09 head-and-shoulders→medium framing；KN11 nose-on→three-quarter 爬升；KN15 破云 tilt-up→云上 near-static 微升（运镜改 static） |
| 构图功能 | KN02 加视线偏移（去 6.5s 对视）；KN07 tiny→holding high；KN13 single pale point→holding high；KN20b 凝形→「frame 的金机缓入下坠」；KN25 两盏「far warm lights」→左暖窗/右冷白路灯+中间的城 |
| 人物一致 | 男主四镜（KN02/03/09/23）批级补骨相正向锚（blunt rounded jaw / flat wide nose tip / heavy-lidded monolid / matte unretouched skin） |
| 机核元数据 | KN18 move static→track（词面 slides laterally）；KN15 texture 跟帧 film_day；KN21/22a/22b 词锚按 anchors 时间窗重算；NIGHT 光块集补 cloud_moon/streak |

落位后复跑：**lint 0 命中 · guard 0 fail**（与落位前同一脚本同口径）。

## 四、烧后帧检注册表（两席跨块意见合并 · 烧制端逐项执行）

1. KN22b 水塔形制：木质圆筒钢架不得被烧成铁皮筒；同检 KN22a 双塔是否被「统一」成同一座。
2. KN16/KN19/KN29左/KN30右：横格线不得被抹平；KN21/24/28 米色纸不得被洗成纯白。
3. 红标记：只在尾尖、不得提前出现在折纸阶段、不得涨成半机红（KN08/KN24/KN29/KN30 重点）。
4. KN07/10/11/12/13「大机」：本批 i2v 不缩机，装配端缩放/裁切或 B 批补远景帧（不得靠词面逼缩）。
5. KN24 露脸三检：视线真抬向夜空 / 哑光唇与自然肤质不被磨皮 / 年龄感不得幼化。
6. KN25：路灯必须冷白且与左暖窗分居两侧、其间是全城；装配 +0.04EV 后复查钠灯暖点仍在。
7. KN20b：机首朝下、不得出现「先散后聚」倒放感、不得回弹为平飞/上升。
8. KN15：色温必须留在白日晴蓝，不得烧成日出/月夜而污染 89–141s 夜段。
9. KN30：末 0.5s 绝对静止（定格收口），有微漂即废。
10. 长静止单（KN22a 8.2s / KN25 5.4s / KN29 7.1s）：查静帧拖时长与 768P 微抖，必要时补极微呼吸（不改构图）。
11. KN02：男主不得直视观众（全片唯一对视风险镜）。
12. KN08：抬手五指融合（首帧灰区）在灯窗内动 2s 是最易被抓穿帮位——避帧或让手尽快出画。
13. KN29：翼尖距≥一掌、薄纸折痕不得退化为真机蒙皮。
14. KN01/KN04：机与手不得出现额外红；KN04 离手瞬间必须成立（首帧闸 F8 项）。
15. 全包：零音轨（CEO 音轨禁令）·零现代穿帮·保留 35mm 颗粒与 2000 台式奶黑调性。

## 五、放行范围（条件式准烧）

- **准烧顺序**：① 先烧 **480P 验证片 3 单**（`local-i2v/run-bmc-kn-verify480.json`：KN21 特写 / KN04 动作 / KN22b 大远景，672×384 int4，落 `clips-verify-480`）；② 验证 verdict 给 **GO** 后才准烧 768P 全批 30 单（`local-i2v/run-bmc-kn-i2v.json`，1344×768 int8）。
- **未过 guard 不得起烧**：每条提示词以包内 `i2v_prompt` 逐字烧；改词=必须复跑 lint+guard 并回写本签发档。
- **不回头重烧 KF**：纸面两族/水塔四版/大机五镜=帧层既成事实，交装配端打标与 B 批补帧处理（承 FRAME-GATE §五）。
- **移交下批**：`everything still except the living light and air` 换正向句（LX 共享词表级改动，需单独批次）；KN21 源长 14.85s 已贴 15s 上限。

—— 导演席（bm-c 本窗）· 2026-10-24 04:5x · 审=独立席发现·签=导演席