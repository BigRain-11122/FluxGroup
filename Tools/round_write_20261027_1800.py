import io
from pathlib import Path

R = Path(r"C:\Users\sjs20\Desktop\FluxGroup")

dec_rows = """
| 2026-10-27 18:00（校时 18:00） | D-20261027-14 收取面第 24 批：五司双面读＋回执核销（FluxVerse D-20261026-20 收尾／bigmoney CODELY 验收／BigStream 生产面 vs 反馈面） | 五司 HQ-FEEDBACK 当日行＋各司 STATUS 尾行＋git 实读 | ①FluxVerse F-20261027-01（P2）=D-20261026-20 回执，三任务实测 FluxVerse-DevLoop=Running／FluxVerseTick=Ready／HQ-Patrol-FluxVerse=Disabled（按裁决保留），r682 冒烟 8/8+实库 CLEAN=属**已回执**而非新问题；②bigmoney 当日零新行，但 D-20261027-08 三条验收实测通过=38,786B／LF 69／PUA 0（no-op 销账）；③BigLife 当日行 open=0（无待裁项）；④MiniGame 无 HQ-FEEDBACK 但有 STATUS.md 尾行 X2890（mtime 10-27 14:05）＝D-20261027-10 双面口径下判活；⑤BigStream HQ-FEEDBACK 仍 10-24 06:45，生产面 mv 线 10-27 11:24（v717 高码率重建 5623 帧）＝D-20261027-13 双面判据判活，反馈面死线 10-28 12:00 不变 | ①FluxVerse 回执核销 executed，不重派；②bigmoney D-08 销账 executed；③BigLife/MiniGame no-op 销账；④BigStream 维持 D-13（不阻塞产线） | T2（收取面·零新法条） | executed |
| 2026-10-27 18:00（校时 18:05-18:20） | D-20261027-15 台账分卷执行（承 D-20261027-12 具名交付·补录 D-20261027-06 要件） | 本班实读＋`Tools/ledger_split_20261027.py` 干跑/实跑＋零丢行 Counter 对账 | ①改前实测 orders=387,089B／decisions=291,616B（连续第 5-6 班越 250KB=256,000B 硬线）；②迁档口径＝日期 `<2026-10-20` 且不含 dispatched/executing/ceo-pending/escalated 标记的行（在途令一律留主档，避免热窗丢活）；③实跑结果：orders 迁出 106 行→`docs/orders-archive-2026-10.md`（append-only·git diff 108 insertions 无整档改写）后主档 **231,288B**；decisions 迁出 30 行→新立 `docs/decisions-archive-2026-10.md`（40,760B）后主档 **251,696B**；④两档均已落索引行（主档「分卷索引」指向分卷件）；⑤零丢行对账：`git show HEAD:` 行 vs 主档+分卷 Counter 差集 **missing=0**（orders/decisions 双测；extra 仅新增索引/表头行）；⑥误改回滚留痕：首版脚本把已存在的 orders 月卷整档重写为 CRLF（2331 行伪 diff）→ 以 `Tools/ledger_vol_fix_20261027.py` 从 HEAD 字节还原后仅追加 106 行，教训入册「改既有大件前先查同月卷是否已存在」 | ①热窗定谳=7 天（`<2026-10-20` 迁档）+在途标记保护；②分卷件命名=月卷 `*-archive-<YYYY-MM>.md`，只行级追加不改写；③后续班只追加不重排 | T2（治理件·判据可机械核验） | executed |
| 2026-10-27 18:00（校时 18:22） | D-20261027-16 D-20261027-11 的 E1 单源修复落地：量化族并入 `machine-state.ps1` 同一声明（停用集/侧车/复活集三面同源） | D-20261027-11（@HQ 机制面 18:30 限时）＋本班实读实改 | ①修复前 `$tasks` 仅 9 件，量化族 8 件不在声明内→10-27 04:36 停用后 19:00 resume 不会复活（D-11 根因面）；②本班 18:2x 实测量化族 10 件 State 全 Disabled（工作日让路窗内属预期，但复活面缺声明）；③改动＝`$tasks` 增 Bigmoney-Autofill/IntradayMarks/IterationLoop/LoopWatchdog/PoolWorker/ResidentDispatcher＋FluxGroup-QuantAuditProbe/QuantOversightDigest（pauseLite 停用集＝resume 复活集＝同一数组）；④语法校验 `Parser::ParseFile`=PARSE-OK；⑤**未手动硬启**（遵熔断律），候 19:00 AutoYield WorkEnd 自然复活 | ①验收点 **2026-10-27 19:07**：`Get-ScheduledTask Bigmoney-*` 六件+两探针 State 应为 Ready/Running，且 resume 输出含 `[resume] enabled: Bigmoney-*`；逾期动作=夜轮 03:07 计点名（机制面 owner）；②HQ-Patrol-BigMoney 不入复活集（保持人工裁决面） | T1-v2（机制面·否决窗 7 天·git 即回滚） | dispatched（@HQ 机制面·19:07 自验） |

> 本批（第 24 批·18:00 班）3 行＝executed 2／dispatched 1；ceo-pending=0（D-20261027-07 外审收线仍候 CEO·零催办）；escalated=0；overruled 复扫=0（五司当日行全扫：FluxVerse F-20261027-01 为回执非驳回）。本批实体动作三件＝①台账双档分卷落地（orders 231,288B／decisions 251,696B 均回硬线内·零丢行）；②E1 单源修复（量化族并入声明·PARSE-OK·19:07 验收点）；③收取面五司双面读（CODELY D-08 销账）。physical-reminder 不变：BigDomain bootstrap 四件与定价确认权仍在 CEO 面（R1669 在册，禁催办）。
"""

ref_row = """
| 委员会·2026-10-27 18:00 班·第 24 批 | 委员会 | ①拍板实况=3 行（executed 2／dispatched 1·ceo-pending 0／escalated 0／overruled 0）＋1 件操作事故自纠（分卷件首版整档改写→字节级还原，伪 diff 2331→108 行）；②chronic 扫描=已读点名件均在途（BigStream 反馈面死线 10-28 12:00／D-20261027-07 外审候 CEO 零催办／量化族复活候 19:07）→只审不处，违例 0；③反思行消费=当日 02:3x 与 12:00 两班行已在各自班内路由，本班零新增处置项（如实标因：无未路由行）；④迭代核销=上批两迭代项本班闭环（D-27-12 分卷交付实测／D-27-11 单源修复待 19:07 实证）＋新迭代 ≤2（分卷后「热窗体量回归」纳入 19:07 复判；audit-sentinel dangling-decision-ref 探针待夜轮 03:07 接线）。台账指针=docs/decisions.md D-20261027-14/15/16。
"""

dpath = R / "docs" / "decisions.md"
with open(dpath, "ab") as f:
    f.write(dec_rows.encode("utf-8"))

rpath = R / "cph4" / "reflection-journal.md"
with open(rpath, "ab") as f:
    f.write(ref_row.encode("utf-8"))

print("decisions", dpath.stat().st_size, "journal", rpath.stat().st_size)