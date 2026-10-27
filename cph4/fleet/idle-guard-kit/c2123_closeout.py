"""C2123 M1 closeout: merge M5 lane inbox, rewrite state-c.json round fields, prepend snapshot block."""
import json
import os
import time

REPO = r"K:\Fluxgroup\MiniGame"
STATE = os.path.join(REPO, "state-c.json")
SNAP = os.path.join(REPO, "自动化快照-c.md")
INBOX = os.path.join(REPO, ".codely-cli", "engine-tick", "lane-inbox-M5.json")

now = time.localtime()
ts = time.strftime("%Y-%m-%d %H:%M", now)
snap_id = "tick-%s@c2123-shipping-adjudication" % time.strftime("%Y%m%d-%H%M", now)
next_round = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 600))

raw = open(STATE, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
d = json.loads(raw.decode("utf-8-sig"))

merged = []
if os.path.exists(INBOX):
    inbox = json.load(open(INBOX, encoding="utf-8-sig"))
    for k, v in (inbox.get("state_patch") or {}).items():
        d[k] = v
        merged.append(k)
    for a in inbox.get("snapshot_alerts") or []:
        d.setdefault("snapshot_alerts", []).append(a)

d["current_snapshot"] = snap_id
d["current_snapshot_id"] = snap_id
d["next_round_at"] = next_round
d["last_round"] = {
    "ts": ts,
    "result": (
        "C2123 M1 round: harvest s527-starfilter-grain (claimed 06:00:59 by the idle guard, END ok=6 at 06:01:19 "
        "while the M1 window was closed) and close r1017 sec-8 item-1 on the SHIPPING grain-0.10 plates. "
        "(1) Harvest, not a re-run: registry candidates 1605 / stars 1571 / anomalies 34 vs the zero-grain "
        "substrate 2535 / 2436 / 99 -- grain does not create candidates, it reduces them. "
        "(2) 33 of 34 anomalies sit on the frame border (x>=3817 or y>=2173 on 3840x2194 plates) = stars clipped "
        "by the frame edge, which the classifier marks as anomalies by design. "
        "(3) The two interior hits (s20193 @1888,1740 / s20205 @2615,649) are diffuse blue nebula clumps: native "
        "r5->r20 means fall smoothly 67,106,153 -> 46,81,124 with no periodic or duplicated structure. "
        "(4) Products on disk: shipping contact sheet 298392B, 12-tile anomaly crops 300104B, lossless 3-panel "
        "native check 1011840B, adjudication receipt, and a C2123 section in xq-AB-DIRECTOR-RATIFY-r1017.md. "
        "(5) Verdict 0 defects / 0 repair targets; bank p30 done and successor s527-shipping-pack-v1 prestowed. "
        "(6) M5 lane inbox C2123 merged (audit_health + daily_review)."
    ),
    "build_ok": True,
}
d["last_round_changes_count"] = 4

out = json.dumps(d, ensure_ascii=False, indent=1)
data = (b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8")
open(STATE, "wb").write(data)

if merged:
    os.remove(INBOX)

block = """# 自动化快照-c（C 机）vC2123｜%s｜出货底片（grain 0.10）星点排除复核 → r1017 sec-8 条目1 关闭

- **探测时间**：%s｜tick = 2026-10-20 06:06（normal_iteration·无 batchmode·无 MCP）
- **Step0**：preflight 22 项 PASS + 1 FLAG（M5 lane-inbox 待合并）、INFO 若干。`s527-starfilter-grain` 06:00:59 被 IdleGuard 认领、06:01:19 已 END ok=6（上一轮窗口已关，本轮为收割非重跑）；LOCK 龄 1m、RAM 15.9%%<40%% = IDLE-CLAIM NOT-GREEN-IDLE（无认领义务）。GPU free 9.5G / comfy=1 / verdict=GPU_DRAFT_OK
- **本轮目标**：把 sec-8 条目1 的结论从「零粒诊断底片」推进到**出货底片**，并交出 CEO 可直接看的联系表
- **头条实物（CEO 可看面）**：
  - **六盘出货联系表** = `media/MV/mv0001/xingqing/xq-S527-SHIPPING-CONTACT-c2123.jpg`（298,392B·2 列×3 行·每盘标注 grain 0.10 4K）
  - **异常 12 格目眼板** = `xq-S527-ANOM-CROPS-c2123.jpg`（300,104B）
  - **原生无损三格复核板** = `xq-S527-NATIVE-CHECK-c2123.png`（1,011,840B）
  - **判读收据** = `xq-S527-SHIPPING-ADJUDICATION-c2123.json`
- **实测判断**：
  - 出货粒版候选 **1605 / 星 1571 / 异常 34**；对比零粒底片 **2535 / 2436 / 99** → **粒不是候选源，带粒后候选与异常同步下降**
  - **34 异常中 33 张在画幅边缘**（x≥3817 或 y≥2173，盘面 3840×2194）=被裁切的星点；分类器按设计把贴边点判异常
  - **画幅内 2 张**（`s20193 @1888,1740`、`s20205 @2615,649`）：原生像素 r5→r20 均值平滑下降（67,106,153→46,81,124）=蓝色弥漫星云团；**无点阵/无周期/无重复结构**
  - **目眼两轮**（12 格拼板 + 原生 PNG 3 格）：未见点阵、棋盘、细线幻觉涂抹；局限如实记（频谱峰值试验对紧凑星点无区分力，unconclusive）
  - **结论**：**0 个修补目标**，r1017 sec-8 条目1 关闭（检测器假阳性族，两种底片同结论），补强段已追加进 `xq-AB-DIRECTOR-RATIFY-r1017.md`
- **银行**：p30 `s527-starfilter-grain` → done（全证 done_note）；预挂后继 `s527-shipping-pack-v1`（出货目录 + SHA256 清单 + 一页 README·PASS gate=SHIPPING-PACK-END ok=6 且清单 6 条 SHA256 复验），银行非空
- **问题清单**：(红) 无 ·(黄) 频谱试验判据无区分力（已记局限，不作缺陷依据）·(蓝) sec-8 条目1 已闭，待 bm-a 装配席消费出货盘
- **额度与工具**：TJ 未消耗·本地 GPU 未占（PIL 全链 ~1min）·ComfyUI 8188 未触
- **下轮选线**：等 `s527-shipping-pack-v1` 收割 或 S7R 六镜 conform 注记 / 装配端 bm-a 导演席 33 单元复检

""" % (ts, ts)

prev = open(SNAP, "rb").read().decode("utf-8-sig")
open(SNAP, "wb").write(b"\xef\xbb\xbf" + (block + prev).encode("utf-8"))

print("STATE-OK %s merged=%s snap=%s next=%s" % (ts, merged, snap_id, next_round))