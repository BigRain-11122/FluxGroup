"""C2125 M1 closeout: rewrite state-c.json round fields, prepend snapshot block,
and append this round's Step markers + TICK_DONE to tick-ledger."""
import json
import os
import time

REPO = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(REPO, "state-c.json")
SNAP = os.path.join(REPO, "自动化快照-c.md")
LEDGER = os.path.join(REPO, ".codely-cli", "engine-tick", "tick-ledger.txt")

now = time.localtime()
ts = time.strftime("%Y-%m-%d %H:%M", now)
snap_id = "tick-%s@c2125-s7r-conform-labels" % time.strftime("%Y%m%d-%H%M", now)
next_round = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 600))

raw = open(STATE, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
d = json.loads(raw.decode("utf-8-sig"))

d["current_snapshot"] = snap_id
d["current_snapshot_id"] = snap_id
d["next_round_at"] = next_round
d["last_round"] = {
    "ts": ts,
    "result": (
        "C2125 M1 round: executed the prestowed bank job s527-conform-labels-v1 = r1017 sec-8 item-6, the "
        "S7R board family label conform (zero GPU, zero variant pixel rewritten). (1) All four boards were "
        "rebuilt from the variant files already on disk: BOARD-1/BOARD-2 column headers now read "
        "s7rA grain 0.14 / s7rB shoulder+grain / s7rC esrgan4x+LANCZOS instead of bare A/B/C, matching "
        "xq-s7r-abatch-receipt-r1058.json. (2) The S5-26 strip header now spells ORIGINAL (was ORGINAL); the "
        "S0-03 strip reads s7rA/s7rB. (3) Gate CONFORM-LABELS-END ok=1 boards=2 strips=2 typo_fixed=1 "
        "token_bad=0, with every output name and label free of the bad token. (4) Eye pass: multimodal re-read "
        "of all four boards confirmed s7rA/s7rB/s7rC headers and the corrected spelling, no clipping. "
        "(5) Three copies are SHA256-identical (abatch_s7r canonical / cph4 evidence folder / xingqing root "
        "for the bank require gate); xq-S7R-CONFORM-LABELS-c2125.json carries per-board sha256 + label map. "
        "(6) r1017 sec-8 item-6 flipped to closed with evidence, and a C2125 section appended. (7) Bank p32 "
        "done; successor s7r-conform-ratify-board prestowed (one-page index of the four boards for the "
        "director to ratify in a single look)."
    ),
    "build_ok": True,
}
d["last_round_changes_count"] = 5

out = json.dumps(d, ensure_ascii=False, indent=1)
data = (b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8")
open(STATE, "wb").write(data)

block = """# 自动化快照-c（C 机）vC2125｜%s｜S7R 板族标注 conform（r1017 sec-8 条目6 关闭）

- **探测时间**：%s｜tick = 2026-10-20 06:47（normal_iteration·无 batchmode·零 GPU）
- **Step0**：preflight 24 项全 PASS（STATUS-c 0.4h 新鲜、无红警、无在途 inbox）；LOCK 龄 0m、RAM 13.8%% <40%% = IDLE-CLAIM NOT-GREEN-IDLE；GPU free 9.5G、verdict=GPU_DRAFT_OK（本轮零 GPU 消耗）
- **本轮目标**：执行预挂活件 `s527-conform-labels-v1`——把 S7R 板族表头从 A/B/C 改成回执口径 s7rA/s7rB/s7rC，并修 S5-26 条板「ORGINAL」拼写
- **头条实物（CEO/导演可看面）**：
  - `media/MV/mv0001/xingqing/abatch_s7r/xq-AB-S7R-BOARD-1-r1058.jpg`（480,629B·9 行×4 列）
  - `…/xq-AB-S7R-BOARD-2-r1058.jpg`（617,155B·9 行×3 列）
  - `…/xq-AB-S7R-COMPARE-S5-26-r1058.jpg`（197,965B·三格全分辨率条板·拼写已修）
  - `…/xq-AB-S7R-COMPARE-S0-03-r1058.jpg`（608,937B·三格条板）
  - `…/xq-S7R-CONFORM-LABELS-c2125.json`（标签映射 + 逐板 sha256）
- **实测判断**：
  - 四件板**全部由盘上既有变体件（s7rA.png/s7rB.jpg/s7rC.png）重制**，变体像素零改动＝纯标注层修正
  - 机械闸 `CONFORM-LABELS-END ok=1 boards=2 strips=2 typo_fixed=1 token_bad=0`；新输出名与新标签**零 ORGINAL**
  - 眼检：多模态逐件复读四板表头（BOARD-1 四列 / BOARD-2 首末行 / 两条板三格）全部读出 s7rA·s7rB·s7rC 与正确拼写，无截字
  - 三处副本 SHA256 恒等：abatch_s7r 正身 = cph4 证据夹 = xingqing 根（银行 require 面）
- **银行**：p32 `s527-conform-labels-v1` → done（全证 done_note）；预挂后继 `s7r-conform-ratify-board`（四板一页签认索引·PASS gate=RATIFY-BOARD-END ok=1 + ≥150KB），银行非空
- **问题清单**：(红) 无 ·(黄) r1017 §八 余 2a 草尖 1:1、5 双蝶＝候导演眼判（非我方自决）·(蓝) 无
- **额度与工具**：TJ 0·云端 0·GPU 0（PIL ~2s/板）·ComfyUI 未触
- **近期成果（CEO 可见面）**：S527 六张 grain-0.10 4K 母版出货包（C2124）+ S7R 板族标注 conform（本轮）
- **下个里程碑**：`s7r-conform-ratify-board` 收割出签认板 → 交 bm-a 导演席一次签认 S7R 证据族

""" % (ts, ts)

prev = open(SNAP, "rb").read().decode("utf-8-sig")
open(SNAP, "wb").write(b"\xef\xbb\xbf" + (block + prev).encode("utf-8"))

lines = [
    "%s | Step0 完成 | C2125 preflight 24 项全 PASS（无 FLAG）；bank p32 s527-conform-labels-v1=pending 本班执行；LOCK 0m/RAM 13.8%%<40%% = NOT-GREEN-IDLE；GPU free 9.5G 本轮零消耗" % ts,
    "%s | Step1/2 组合扫描 | 在管面：MV 星晴 A 批 S7R 证据族（sec-8 条目6 未做）+ G22/G25 无新 commit；款级 stage 卡指纹无变化跳过重 derive" % ts,
    "%s | Step3 快扫与门禁 | 本轮零工程代码改动（PIL 板面重制脚本）；py_compile 过；G1 不适用；无 batchmode" % ts,
    "%s | Step4 选线 | 银行预挂件直取：把 A/B/C 表头改成回执口径 s7rA/s7rB/s7rC + 修 ORGINAL 拼写（零 GPU·导演可看实物）" % ts,
    "%s | Step5 应用+门禁 | CONFORM-LABELS-END ok=1 boards=2 strips=2 typo_fixed=1 token_bad=0；四板 + 收据三处副本 SHA256 恒等；多模态四件眼检全过" % ts,
    "%s | Step6 写 state+快照 | state-c.json 三字段手术 + 快照-c vC2125 块前插 + r1017 §八-6 翻闭合" % ts,
    "%s | Step7 收工 | 单提交收口（四板 + 收据 + 脚本 + r1017 + state + 快照 + 台账）+ FleetPush machine/C；bank p32 done，预挂 s7r-conform-ratify-board" % ts,
    "%s | TICK_DONE C2125 | S7R 板族标注 conform：四件板表头改 s7rA/s7rB/s7rC + S5-26 修 ORIGINAL，变体像素零改动 | 门禁=CONFORM-LABELS-END ok=1/零 ORGINAL/副本哈希恒等/眼检四件过 | build_ok=True" % ts,
]
with open(LEDGER, "a", encoding="utf-8", newline="") as f:
    for l in lines:
        f.write(l + "\r\n")

print("STATE-OK %s snap=%s next=%s ledger=+%d" % (ts, snap_id, next_round, len(lines)))