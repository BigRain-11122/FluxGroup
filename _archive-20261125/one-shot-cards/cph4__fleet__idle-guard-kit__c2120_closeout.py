# -*- coding: utf-8 -*-
"""C2120 closeout: state-c.json surgery + snapshot prepend + tick-ledger lines."""
import io
import json
import os
import time

ROOT = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(ROOT, "state-c.json")
SNAP = os.path.join(ROOT, "自动化快照-c.md")
LEDGER = os.path.join(ROOT, ".codely-cli", "engine-tick", "tick-ledger.txt")

now = time.strftime("%Y-%m-%d %H:%M")
stamp = "tick-20261020-0531@c2120-grain010-s08"
NEXT = "2026-10-20 05:47"

# ---------- 1. state ----------
with open(STATE, "rb") as f:
    raw = f.read()
has_bom = raw.startswith(b"\xef\xbb\xbf")
d = json.loads(raw.decode("utf-8-sig"))

d["current_snapshot_id"] = stamp
d["current_snapshot"] = stamp
d["last_round"] = {
    "ts": now,
    "result": (
        "C2120 M1 round (r1017 sec-5 row-1 grain endpoint + sec-8 items 2-5). "
        "(1) Step0 preflight 23 areas PASS, zero FLAG; bank was 1 pending (grain A/B claimed 04:00:59), "
        "harvested this round. (2) Grain A/B board read (2x2, 4 cells, 223,408B) + multimodal: 0.10 reads "
        "closer to 2000s Taiwan film, 0.05 dark areas slightly digital -> endpoint 0.10 adopted. "
        "(3) Six grids re-burned clean at grain 0.10 from the source (not stacked on 0.07): 6x 3840x2194, "
        "15.1-15.8MB, 8.1-10.1s each, wall ~59s; s20193/s20202 byte-identical to the A/B endpoint plates "
        "= deterministic. (4) 4K monitor recheck: star_retention 1.27-3.50 vs source (no faint-star loss), "
        "corner_dark 0.995-0.9998 consistent across six. (5) sec-8 items executed with numeric probes: "
        "item2a kite-line ringing halo_p50 4.23/4.45 grey (clean), grass-tip 4.30/6.23 (structure not halo, "
        "1:1 board issued); item2b highlight knee max step 2.03/1.93/7.44/3.84 grey with clip_frac 0 "
        "(no hard step); item3 s20160 handheld bright>=210 fraction 0.0000, largest self-lit blob 0px "
        "(no big screen = CD/MD reading supported); item4 s20105 dark block stretch -> gradient orientation "
        "entropy 4.901/5.17 bit, no isolated head/shoulder blob, refuted confidence 85%->93%; item5 s21026 "
        "butterfly silhouette fit IoU 0.779 (rot 148deg, sc 1.30, area ratio 1.086) = intermediate band, "
        "not self-adjudicated, 1:1 board to director. (6) item6 S7R label conform carried to next round. "
        "(7) Bank: p27 done + successor s527-grain-007-vs-010 pre-stowed (bank never empty)."
    ),
    "build_ok": True,
}
d["next_round_at"] = NEXT

out = json.dumps(d, ensure_ascii=False, indent=1)
with open(STATE, "wb") as f:
    if has_bom:
        f.write(b"\xef\xbb\xbf")
    f.write(out.encode("utf-8"))
print("STATE_OK bytes=%d bom=%s anchor=%s" % (os.path.getsize(STATE), has_bom, stamp))

# ---------- 2. snapshot prepend ----------
BLOCK = """# 自动化快照-c（C 机·vC2120）2026-10-20 05:31 六格 4K 颗粒端点定谳 + §八终检四项闭环

- **探测时间**：2026-10-20 05:31（tick = 2026-10-20 05:31）·normal_iteration·车道=GPU DI 收官线（无 batchmode·无 MCP）

- **Step0**：preflight 23 区全 PASS 零 FLAG·银行 1 件 pending（`s527-4k-grain-ab` 04:00:59 被认领未收割）→本轮即收割轮·RAM 18.6%<40%（IDLE-CLAIM NOT-GREEN-IDLE·无领池义务）·GPU free 9.5G/comfy=1

- **头号实物（CEO 可见面）**：
  ① **六格 4K 终版按 grain 0.10 干净重烧** → `media/MV/mv0001/xingqing/s7r-4k/*_4k_grain010.png` 6 张 3840×2194（15.1–15.8MB·单帧 8.1–10.1s·总 ~59s）+ 对比板 `xq-S527-4K-GRAIN010-BOARD-c2120.jpg` 473,453B + 回执 `xq-S527-4K-GRAIN010-RECEIPT-c2120.json`（s20193/s20202 与 A/B 端点件**字节恒等**=确定性可复现）
  ② **颗粒端点 A/B 证据**：`xq-S527-GRAIN-AB-BOARD-c2120.jpg` 223,408B（0.05 vs 0.10 四格）+ 1:1 差分板 `xq-S527-GRAIN-007-VS-010-c2121.jpg`（预挂件脚本就位）
  ③ **§八终检四件证据板**：`xq-S08-KITE-1TO1-c2120.jpg` / `xq-S08-GRASS-1TO1-c2120.jpg` / `xq-S08-S423-HANDHELD-1TO1-c2120.jpg` / `xq-S08-S214-STRETCH-c2120.jpg` / `xq-S08-S213-BUTTERFLY-1TO1-c2120.jpg` + 实测 JSON `xq-S08-PROBE-c2120.json` / `xq-S08-PROBE2-c2120.json`
  ④ 4K 监看板 `xq-S527-4K-GRAIN010-MONITOR-c2121.jpg` 120,229B

- **实测判定**：
  - **颗粒端点**：0.10 采纳（多模态：0.05 暗部偏「数字干净」·0.10 暗部有真实胶片颗粒且高光不脏）——裁决行已逐项写进 r1017 §十一（导演可一句话改回 0.07·重跑确定性）
  - **§八-2a 风筝线/草尖振铃**：细亮结构旁 2px 高通振幅中位 4.23/4.45（风筝线）/ 4.30/6.23（草尖），≤6 灰阶=不可见振铃 → 风筝线**闭合**；s20039 草尖 p90 23.05 系刃状草叶真实高频结构非周期晕 → 留 1:1 板交眼判
  - **§八-2b 膝点（高光 knee）连续性**：顶部 5% 亮度曲线 0.1% 步长最大跳变 2.03/1.93/7.44/3.84 灰阶·clip_frac(≥250)=0 四格一致 → **无硬截断台阶·闭合**
  - **§八-3 S4-23 s20160 手持物**：229×119px@(611,407) 裁切内「≥210 亮像素占比 0.0000·最大自发光斑 0px」→ 无大亮屏（智能手机负向特征缺失）= **CD/MD 读法获支撑·闭合**
  - **§八-4 S2-14 s20105 暗块**：拉伸后梯度方向熵 4.901/5.17 bit（近满=纹理弥散无轮廓）+ 无头肩级孤立闭合亮块 → 第三影证伪置信 85%→**93%·闭合**
  - **§八-5 S2-13 s21026 双蝶**：轮廓拟合 IoU 0.779（rot 148°·sc 1.30·面积比 1.086 近等标度）落在 0.75–0.90 中间带 → 机械面**不自裁**，1:1 双蝶板交导演（原降级附条件状态维持）
  - **§八-1 条件①（细线幻觉/点阵残留局部修补）**：定位探针在 grain 件上每格报 130–357 个孤立高频斑，**与刚加颗粒同谱混叠、地址不可信**（已如实记档·勿照坐标修补）；正解=在未加颗粒的 ESRGAN 上采件上定位
  - **§八-6 S7R 标注 conform（A/B/C→s7rA/s7rB + ORGINAL 拼写）**：本班时间盒已尽·预挂后继

- **银行**：p27 `s527-4k-grain-ab` → done（含 done_note 全链证据）；**后继预挂 `s527-grain-007-vs-010`**（priority 28·脚本 `s527_grain_delta_c2121.py` 已就位并试跑通过·零重烧）→ 银行 28 done / 1 pending（不空）

- **门禁**：G1 不适用（本轮零 Unity 代码改动·纯媒体 DI 线）·媒体探针全 exit0·编码零 U+FFFD（追加回执块已验）

- **下轮选择**：① §八-6 S7R 标注 conform（零 GPU·纯板面重出）；② §八-1 条件① 细线修补（先在没有颗粒的 ESRGAN 上采件定位）；③ §八-5 双蝶导演定谳后回写本节；④ 银行 p28 grain 差分板可被 IdleGuard 直接点名

- **收口**：state 手术三字段全保留（ts/result/build_ok）·双锚同值 `tick-20261020-0531@c2120-grain010-s08`·next_round_at 05:47·tick-ledger 记 Step/TICK_DONE·FluxGroup 走 pathspec-only 产品提交（脚本+回执+bank+ratify 文档）·MiniGame 走收口提交 + FleetPush machine/C

"""
with open(SNAP, "rb") as f:
    sraw = f.read()
seol = "\r\n" if b"\r\n" in sraw[-600:] else "\n"
stext = sraw.decode("utf-8")
lines = stext.split("\n")
# drop the old first header line (vC2119 header) and prepend the new block
while lines and lines[0].startswith("# 自动化快照-c"):
    lines.pop(0)
new_text = BLOCK.replace("\n", seol if seol == "\r\n" else "\n") + "\n".join(lines)
with open(SNAP, "wb") as f:
    f.write(new_text.encode("utf-8"))
print("SNAP_OK bytes=%d" % os.path.getsize(SNAP))

# ---------- 3. tick-ledger ----------
with open(LEDGER, "rb") as f:
    lraw = f.read()
leol = "\r\n" if b"\r\n" in lraw[-400:] else "\n"
rows = [
    "[%s] [Step0 完成] preflight 23 areas PASS zero FLAG; bank 1 pending (grain A/B claimed 04:00:59) -> harvest round; RAM 18.6%% IDLE-CLAIM NOT-GREEN-IDLE" % now,
    "[%s] [Step4 完成] line=GPU DI r1017 sec-5 row-1 grain endpoint + sec-8 items 2-5 (no batchmode, no MCP; GPU free 9.5G)" % now,
    "[%s] [Step5 完成] grain A/B harvested (board 223,408B, 0.10 adopted) -> six grids re-burned clean at 0.10 (6x 3840x2194, wall ~59s, deterministic)" % now,
    "[%s] [Step5 完成] sec-8 probes: 2a kite halo_p50 4.23/4.45 clean; 2b knee max step 2.03/1.93/7.44/3.84 clip 0; 3 handheld bright frac 0.0000; 4 dark-block entropy 4.901/5.17 refuted 93%%; 5 butterfly IoU 0.779 -> director" % now,
    "[%s] [Step6 完成] state three-field surgery kept + snapshot vC2120 prepended + bank p27 done, successor s527-grain-007-vs-010 prestowed" % now,
    "%s TICK_DONE C2120 grain 0.10 endpoint adopted + six 4K re-burn + sec-8 items 2/3/4 closed, 5 to director, 6 deferred; bank 28 done/1 pending" % now,
]
add = "".join(r + leol for r in rows)
with open(LEDGER, "wb") as f:
    if not lraw.endswith(b"\n"):
        f.write(leol.encode())
    f.write(add.encode("utf-8"))
print("LEDGER_OK rows=%d bytes=%d" % (len(rows), os.path.getsize(LEDGER)))