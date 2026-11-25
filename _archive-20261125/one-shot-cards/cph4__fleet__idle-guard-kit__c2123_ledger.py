"""C2123 ledger rows (UTF-8 append, real timestamps)."""
import time

p = r"K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\tick-ledger.txt"
now = time.strftime("%Y-%m-%d %H:%M")
rows = [
    "%s | Step0 完成 | C2123 preflight 22 PASS + 1 FLAG（M5 lane-inbox 待合并·已并入）；p30 starfilter-grain 06:00:59 认领 / 06:01:19 END ok=6 = 收割非重跑" % now,
    "%s | Step1/2 完成 | 增量：无新竞品信号；本机在管 G22/G25 卡片无新 commit（指纹跳过）；S5-27 出货底片线=r1017 sec-8 条目1 收口位" % now,
    "%s | Step3 完成 | 本轮无代码改动，无 batchmode 波次；G1 不适用（PIL 脚本已 py_compile 过）" % now,
    "%s | Step4 完成 | 选线=收割 p30 星点排除（出货粒版）→ 原生像素复核 → 出 CEO 可看联系表 → 关闭 sec-8 条目1" % now,
    "%s | Step5 完成 | 产物：SHIPPING-CONTACT 298392B / ANOM-CROPS 300104B / NATIVE-CHECK 1011840B / ADJUDICATION json；34 异常=33 贴边星点 + 2 星云团，0 修补目标" % now,
    "%s | Step6 完成 | state-c.json 已手术（M5 inbox 合并·snapshot vC2123·last_round 三字段）·state_guard STATE_OK 双锚同值·快照 C 机已前置" % now,
    "%s | Step7 完成 | 收口提交 + 银行 p30 done / 预挂 s527-shipping-pack-v1" % now,
    "%s | TICK_DONE C2123 | 收割星点排除（出货粒版）：候选 1605/星 1571/异常 34（零粒底片 2535/2436/99）→ 33 贴边星点 + 2 星云团、0 修补目标 → r1017 sec-8 条目1 关闭 + CEO 可看六盘联系表 298KB + 原生复核 PNG + 判读收据 | 门禁：G1 不适用（纯图像分析链·py_compile 过）| build_ok=True" % now,
]
raw = open(p, "rb").read()
if not raw.endswith(b"\n"):
    raw += b"\r\n"
data = raw + ("\r\n".join(rows) + "\r\n").encode("utf-8")
open(p, "wb").write(data)
print("LEDGER-APPENDED rows=%d ts=%s" % (len(rows), now))