import io, os
root = r"C:\Users\sjs20\Desktop\FluxGroup"
led = os.path.join(root, "cph4", "evolution-ledger.md")
ref = os.path.join(root, "cph4", "reflection-journal.md")

block = """
### 值守轮 2026-11-08 夜（03:07 班·预算 15min）

- **水位**：盘 C: **942.8GB**（前班 11-07 21:07=944.4GB → **-1.6GB/6h ≈ -6.4GB/日**，未触 20GB/日燃烧线）；retention 增量 top＝`gaming\\MiniGame\\.git` **+170MB**（gc 权归 RepoSlim 09:03 哨）、`.codely-cli` **+108.5MB**、`quant\\bigmoney\\.git` **+66.7MB**、`cph4` **+4.5MB**，实验区/管线 cache 无点名级超帽；旗标 AUTO_SAVES_OLD **700/1266**／LOGS_OLD **97**／GIT_BIG `MiniGame\\.git` **5315MB**（>2GB 线·RepoSlim 域）；台账字节（分卷后）`orders` **228.3KB**／`decisions` **62.1KB**／`ledger` **124.6KB**／`gaming-CODELY` **31.8KB**（阈 250/200/400/60KB 全在线内）
- **抽验**：selfaudit **5/5 backed·bare=0** ✓；secret-scan 7 仓 hits=5 **P0=1＝扫描器自身样例常量假阳**（命中 `SECRET_FALSE_POSITIVE` 定义行／官方示例串，非泄露，按 FLEET-OPS 记档不呈报）；fleet-audit 03:11＝offline=**1**(bm-b 206.5h)／stale=**2**(bm-a 10.7h·与 BG-A 同物理机、BG-C 4.8h)／green_idle=0／heavy=0；**fleet-reality 03:12:06（唯一现状源）**＝bm-a tailnet+`:8790` OK·hb **16m**·skew 0m／bm-b hb **12008m**／bm-c hb **653m**／bm-m health=err（未入册对端 100.87.248.66）／bm-d tailnet=N；audit-sentinel **8 旗**（A：P-2026-11-01-04/06/07/08/10 五件 transferred **7d**>48h；B：BigDomain 432／BigCompute 125／FluxVerse 104 提交零集团闭单提及，虚荣比候选待深审；C 通过）；registry shadow `md_not_in_jsonl=**3**`（第四班同值 → **影子缺口 3 条待补**，非故障）；task-health **unhealthy=2**（UNEXPECTED-DISABLED `BigCompute-LaneTaskGuard`／STALE `HQ-SchedHarden-Batch`）＋`FluxGroup-QuantAuditProbe` Disabled（E3 白名单在册）＋BROKEN-LINK `bm-a-BiliAutoReply`（退役/改向归委员会）；mechanism-audit **flags=0**（patrol_stamp=DEREGISTERED 设计态）；utf8-guard **bad=0** ✓（分卷后复验）；**班次存活探针＝绿**（`docs/decisions.md` 11-08 行 5 条＝第 49 批、`reflection-journal` 11-08 00:00 委员会行在册）；外审日志末实际新增行仍停 **10-25 10:59**（E1 阻断在册·第 14 天）；OH 收获 **9/9 实体全超 72h**（最新 `OH-20261104-bigcompute` 龄 90h）
- **点名行（三要素·R6）**：①**OH 开源收获轮 9/9 实体停滞（最新 90h，其余 450~816h）**——已连续 ≥4 班只点名，**本班按 R6 强制改判：升 E1 并进 11-08 12:00 决策轮首项**；owner=**@HQ 收集席**，承诺 **11-08 12:00** 提交议程条目或逐实体判负收线，逾期 **CEO 直呈**；②**`BigCompute-LaneTaskGuard` 连续第二夜 UNEXPECTED-DISABLED**（11-07 16:34 起因未明）——同旗两夜，按 errors.md 熔断升 **E1**：owner=**@HQ 机队席**，承诺 **11-08 12:00** 查明来源并出「重建／登记 EXPECTED」二选一，逾期冻结该件派发并进决策轮；③**bm-b 206h OFFLINE（`:8790`=N）／bm-c hb 653m／bm-d 离线／bm-m health=err**——owner=**@HQ 机队席**，承诺 **11-08 06:00** 逐机给「在/离线」物证结论（心跳+lanes last_result；不能上=声明物理件），逾期 **E1**；④**audit-sentinel A 探针 11-01 五件 transferred 7d**——owner=**@CPH4**，承诺 **11-08 12:00** 逐件 ack 或判负收线，逾期 **E1**；⑤外审班缺位 14 天＝E1 阻断在册，本班不复述，仅记阻断未解除，待 11-08 12:00 决策轮列为常设首项
- **本轮动作**：①感知面全跑（retention／盘燃／台账字节／selfaudit／secret-scan／fleet-audit／fleet-reality／audit-sentinel／registry-shadow／task-health／mechanism-audit／utf8-guard／班次存活探针／OH＋外审＋否决窗）；②**自愈 1 件（T2 机械·本班到期项）**＝`docs/decisions.md` **231.5KB→62.1KB** 分卷波：按 `## ` 日期段把 18 段（≤2026-11-04）整段迁入 `docs/decisions-archive-2026-11.md`（300.8KB），11-05 起 6 段留主档，分卷后 `ledger-utf8-guard` 复验 **bad=0**、11-08 五行全在（见证 `Tools/decisions_split_once.py`，原件备份 `decisions.md.bak-prediv`）；③**零其他硬修**（熔断守法：Disabled/STALE 件归点名域，BiliAutoReply 断链归委员会）；④当日**无到期否决窗**；⑤**周日窗记忆梳理＋disk-sweep -Sweep 因单轮预算到期顺延**（如实记录，次班/周轮接续）；⑥commit 定向本班产出件并 push 一次
"""

line = "| 值守轮 2026-11-08 夜 | 值守轮 | 今日最弱一环=「点名簿里最长的那几条，恰恰是没人负责的领域」：OH 收获停滞 4 班、外审缺位 14 天、bm-b 黑灯 206h——三项都跨了多个值班周期，说明夜轮的 E1 升级只写进台账、没有真正逼出决策轮的议程条目 | 归属=@HQ 决策席：11-08 12:00 决策轮须把「OH 收获／外审班／黑灯机队」列为固定前三项议程并出书面裁决，本班起观察至 11-09 03:07 |\n"

with open(led, "a", encoding="utf-8", newline="") as f:
    f.write(block)
with open(ref, "a", encoding="utf-8", newline="") as f:
    f.write(line)
print("ledger_kb=%.1f ref_kb=%.1f" % (os.path.getsize(led)/1024, os.path.getsize(ref)/1024))