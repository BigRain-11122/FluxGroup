"""C2119 closeout: bank pre-stow + state surgery + tick-ledger + snapshot + board row.

Order matters: bank first (producer pre-stow law), then state (indent=1, no BOM,
build_ok preserved), then ledger, then snapshot prepend, then board row.
"""
import io
import json
import os

REPO = r"K:\Fluxgroup\FluxGroup"
MG = r"K:\Fluxgroup\MiniGame"
BANK = os.path.join(REPO, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")
STATE = os.path.join(MG, "state-c.json")
LEDGER = os.path.join(MG, ".codely-cli", "engine-tick", "tick-ledger.txt")
SNAP = os.path.join(MG, "\u81ea\u52a8\u5316\u5feb\u7167-c.md")
BOARD = os.path.join(MG, "Design", "configs", "GLOBAL", "\u6863\u6848", "\u673a\u961f\u534f\u4f5c\u770b\u677f.md")

SNAP_ID = "tick-20261020-0401@c2119-s527-4k-esrgan"
NOW = "2026-10-20 04:01"
NEXT = "2026-10-20 04:15"

RESULT = ("C2119 M1 round (r1017 sec-8 item-1 / sec-5 row-1 DI leg): six-grid 4K line for S5-26/27/28. "
          "(1) Step0 preflight 23 areas PASS, zero FLAG; bank was 26/26 done = empty-bank producer exposure, "
          "successor pre-stowed in this round. (2) Burned six grids through ComfyUI RealESRGAN_x4plus (5376x3072) "
          "-> LANCZOS 3840x2194 -> +0.07 film grain; 8.1-10.0s per frame, wall ~55s, all six PNG 12.6-13.6MB. "
          "(3) Board xq-S527-4K-BOARD-c2119.jpg 2352x1880 438,073B; first build used fixed-pixel crops on two "
          "resolutions (different FOV) and the eye gate reported 'stars missing' on S5-28 -> rebuilt with an equal "
          "field-of-view fractional crop, re-read 6/6 PASS (constellation links/star nodes continuous, no new line "
          "or dot artifacts, no wax/oversharp, corners stay near-black). (4) Native probe xq-S527-4K-PROBE-c2119.json "
          "carries mad/corr/bright counts as the mechanical counter-check (B1145: probe before accepting an eye-gate FAIL). "
          "(5) sec-5 pre-condition 1 (local line-hallucination/dot-matrix cleanup) intentionally NOT applied this leg - "
          "the 4K monitor recheck came back clean, so cleanup is not needed for these six grids; grain band decision "
          "still open (pre-stowed as next job). build_ok=True")

SUCCESSOR = {
    "id": "s527-4k-grain-ab",
    "status": "pending",
    "priority": 27,
    "auth": "r1017 sec-5 row-1 pre-condition 2 open band: grain 0.05-0.1; C2119 produced 0.07 and passed the 4K monitor recheck, director may still want the band endpoints",
    "require": {"files_at_least": [
        ["media/MV/mv0001/xingqing/s7r-4k", "S5-27_s20193_s7rC_4k.png", 1],
        ["media/MV/mv0001/xingqing/s7r-4k", "S5-28_s20202_s7rC_4k.png", 1]]},
    "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
            "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\s527_4k_grain_ab_c2120.py"],
    "log_out": "media/mv-album-001-jay/log-s527-grainab.out.txt",
    "log_err": "media/mv-album-001-jay/log-s527-grainab.err.txt",
    "note": ("Grain band A/B from the already-upscaled 4K plates (zero re-burn): two grids x grain 0.05 / 0.10 "
             "+ a 2x2 compare board, so the director picks the band endpoint for the adopted six grids. "
             "PASS gate = GRAIN-AB-END ok=4 in log tail + 4 PNG + board >= 100KB. "
             "Harvest = next round: board read + grain decision line into r1017 sec-5 row-1."),
    "prestow_ts": "2026-10-20T04:01:00",
    "prestow_note": "C2119 pre-stow right after the six-grid 4K leg landed (bank law: never empty).",
}

BANK_DONE = {
    "id": "s527-4k-esrgan",
    "status": "done",
    "priority": 26,
    "auth": "r1017 sec-8 item-1 / sec-5 row-1 (DI group 100% final-check transfer list) six grids ESRGAN x4 + LANCZOS",
    "done_ts": NOW,
    "done_note": ("HARVEST PASS by tick-C2119: six 4K PNG 3840x2194 (12.6-13.6MB) in media/MV/mv0001/xingqing/s7r-4k + "
                  "board xq-S527-4K-BOARD-c2119.jpg 438,073B + receipt/probe JSON. Eye gate 6/6 PASS after the board FOV fix; "
                  "native probe carries corr/mad/bright counters. sec-5 pre-condition 1 (local cleanup) not needed on this pass."),
}

# --- 1. bank ---
with io.open(BANK, encoding="utf-8") as f:
    bank = json.load(f)
jobs = bank["jobs"]
assert not any(j["id"] == "s527-4k-esrgan" for j in jobs), "job already present"
jobs.append(BANK_DONE)
jobs.append(SUCCESSOR)
with io.open(BANK, "w", encoding="utf-8", newline="\n") as f:
    json.dump(bank, f, ensure_ascii=False, indent=1)
print("BANK_OK jobs=%d" % len(jobs))

# --- 2. state ---
with io.open(STATE, encoding="utf-8") as f:
    st = json.load(f)
prev = st.get("current_snapshot_id")
st["current_snapshot_id"] = SNAP_ID
st["last_round"] = {"ts": NOW, "result": RESULT, "build_ok": True}
st["last_round_changes_count"] = 3
st["next_round_at"] = NEXT
with io.open(STATE, "w", encoding="utf-8", newline="\n") as f:
    json.dump(st, f, ensure_ascii=False, indent=1)
with io.open(STATE, encoding="utf-8") as f:
    json.load(f)
print("STATE_OK prev=%s now=%s" % (prev, SNAP_ID))

# --- 3. ledger ---
lines = [
    "[%s] [Step0 完成] preflight 23 areas PASS zero FLAG; bank 26/26 done = producer exposure, successor pre-stowed" % NOW,
    "[%s] [Step4 完成] line=GPU DI leg r1017 sec-8 item-1 (six-grid 4K ESRGAN) - RAM 11.9%% closed batchmode lane, GPU free 9.5G" % NOW,
    "[%s] [Step5 完成] s527_4k_esrgan_c2119.py fired detached PID 42788 -> S527-4K-END ok=6 wall ~55s" % NOW,
    "[%s] [Step6 完成] board rebuilt with equal-FOV crop -> 6/6 PASS; native probe written" % NOW,
    "[%s] TICK_DONE C2119 six-grid 4K ESRGAN line PASS 6/6 (board 438,073B), bank pre-stow s527-4k-grain-ab" % NOW,
]
with io.open(LEDGER, "a", encoding="utf-8", newline="") as f:
    f.write("\n".join(lines) + "\n")
print("LEDGER_OK +%d" % len(lines))

# --- 4. snapshot prepend ---
block = """# 自动化快照-c（C 机快照·vC2119·2026-10-20 04:01 六格 4K ESRGAN 线）
- **探测时间**：2026-10-20 04:01（tick = %s；normal_iteration；车道=GPU DI 终检线·零 batchmode·零 MCP）
- **Step0**：preflight 23 面全 PASS 零 FLAG；**银行空态**（26/26 done by C2117）=生产者违例风险→本轮同窗预挂后继 `s527-4k-grain-ab`；号池 C2119；RAM 11.9%% 波窗关（batchmode 线维持让路）·GPU free 9.5G/comfy=1→GPU 道可产
- **本轮实物（CEO 可见面）**：`media/MV/mv0001/xingqing/s7r-4k/` 六张 4K 帧（S5-26×2/S5-27×2/S5-28×2·3840×2194·12.6-13.6MB）+ 对照板 `xq-S527-4K-BOARD-c2119.jpg`（2352×1880·438,073B）+ 回执 `xq-S527-4K-RECEIPT-c2119.json` / 原生探针 `xq-S527-4K-PROBE-c2119.json`
- **工艺**：ComfyUI RealESRGAN_x4plus 5376×3072 → LANCZOS 3840×2194 → grain 0.07（r1017 §五 行1 采纳链）；单帧 8.1-10.0s·整批 ~55s
- **判读**：眼闸 6/6 PASS（星座连线/星节点连续·零新增细线点阵·零蜡感·四角近黑）；**首版对照板用固定像素裁切跨分辨率=视野不等→眼闸误报 S5-28 星缺**，改等视野分数裁切后复读全绿；原生探针（corr/mad/bright 计数）留档作机械对拍面（B1145 探针先行律）
- **口径**：§五 前置补修①（细线幻觉/点阵清理）本腿未做且**判读后不需要**（六格 4K 监看洁净）；grain 带宽 0.05-0.1 端点选择=已预挂 A/B 件
- **门禁**：G1 无 batchmode（RAM 闸关）；本批零编译面（纯媒体/DI）；回执与探针可复跑
- **下轮选线**：①s527-4k-grain-ab 收割（grain 端点定档→r1017 §五 行1 回填）②X2670 sec-6 装配解锁候 bm-a 导演席复看 33 单板 ③G25 T001c 波（watcher r7·RAM 窗开即燃）④G30 slice-c 满盒候选
- **收口**：state 手术（双锚同值 %s·build_ok=true·写后 json.loads 复验）+ 台账 TICK_DONE + 银行预挂 + 看板 C 行 | commit 随批
""" % (NOW, SNAP_ID)
with io.open(SNAP, encoding="utf-8") as f:
    old = f.read()
if SNAP_ID in old:
    print("SNAP_SKIP already present")
else:
    with io.open(SNAP, "w", encoding="utf-8", newline="\n") as f:
        f.write(block + "\n" + old)
    print("SNAP_OK prepended %d bytes" % len(block.encode("utf-8")))

# --- 5. board row (insert after the newest C row) ---
row = ("| C | 2026-10-20 | **C2119 S5-26/27/28 六格 4K ESRGAN 线✅（r1017 §八 终检清单第1项/§五 行1·DI 组）**｜03:52-04:0x·占号 C2119 | "
       "工艺=ComfyUI RealESRGAN_x4plus 5376×3072→LANCZOS 3840×2194→grain 0.07（单帧 8.1-10.0s·整批 ~55s）·"
       "产物=六张 4K 帧（12.6-13.6MB）+对照板 xq-S527-4K-BOARD-c2119.jpg 438,073B+回执/原生探针 JSON·"
       "眼闸 6/6 PASS（星座连线星节点连续·零新增细线点阵·零蜡感·四角近黑）·坑=对照板首版固定像素裁切跨分辨率=视野不等致眼闸误判「S5-28 星缺」→等视野分数裁切重建即全绿·"
       "§五 前置补修①判读后不需要·**银行空态预挂 s527-4k-grain-ab（grain 0.05/0.10 端点 A/B）** | 最近交付=s7r-4k 六张 4K 帧+对照板 | 下一步=①grain A/B 收割定档→r1017 §五 回填 ②X2670 sec-6 装配解锁候 bm-a 复看 33 单板 ③G25 T001c 波 watcher r7 候 RAM 窗")
with io.open(BOARD, encoding="utf-8") as f:
    bt = f.read()
if "C2119 S5-26/27/28 六格 4K ESRGAN" in bt:
    print("BOARD_SKIP already present")
else:
    bl = bt.split("\n")
    idxs = [i for i, l in enumerate(bl) if l.startswith("| C |")]
    pos = idxs[-1] + 1
    bl.insert(pos, row)
    with io.open(BOARD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(bl))
    print("BOARD_OK inserted at line %d" % (pos + 1))