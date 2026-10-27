"""C2179: append the machine-C board row."""
import io
import time

P = r"K:\Fluxgroup\MiniGame\Design\configs\GLOBAL\档案\机队协作看板.md"
raw = open(P, "rb").read()
raw.decode("utf-8")
now = time.strftime("%Y-%m-%d")
row = ("| C | " + now + " | **C2179 运镜闸把「整条静止」洗成 UNDECIDED（已修）+ 重烧 480P 已装弹**（12:0x-12:2x tick·批次 C2179）"
       "｜**正在干**=《可爱女人》KN 768P A 波 22/30 在盘（PID 29056 独占 GPU），本轮纯 CPU 审闸"
       "｜**最近交付**=`kn_framing_drift_gate.py` 新增 still_frac 规则（≥90% 采样 ≤1.005x 且最大 ≤1.03x → FLAT，不再被单个相关峰噪声翻成 UNDECIDED）"
       "+ 全量复扫 23 条 flat 1→3 / undecided 3→1 零回退 + `kn_reburn_manifest_c2179.py`→`local-i2v/run-bmc-kn-reburn480-c2179.json`（KN03/KN11/KN21/KN15 四单·提示词从作者层重派生·hygiene 4/4 PASS）"
       "+ `kn_waveend_chain_c2179.py` 后台装弹链（波退出 25s 自动起 bmcverify 480P）+ `KN-GATE-FINDINGS-c2179.md`"
       "｜**下一步**=收割 4 单 480P 验证片（framing 必真推 ≥1.10x、KN15 必无布景）→ 过闸排 768P；KN22b-30 落一件闸一件 → 30/30 → 装配端 |")
with io.open(P, "a", encoding="utf-8", newline="") as fh:
    fh.write("\n" + row + "\n")
print("BOARD_OK bytes_appended", len(row))