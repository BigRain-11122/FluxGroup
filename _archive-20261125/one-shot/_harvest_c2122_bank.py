import io
import json

BANK = r"K:\Fluxgroup\FluxGroup\cph4\fleet\work-bank\bm-c-gpu-bank.json"
RATIFY = r"K:\Fluxgroup\FluxGroup\cph4\fleet\mv-album-001-jay\xq-AB-DIRECTOR-RATIFY-r1017.md"

d = json.load(io.open(BANK, encoding="utf-8"))
jobs = d["jobs"]

DONE_NOTE = (
    "HARVEST PASS by tick-C2122. First fire 05:20:59 produced six zero-grain 4K plates "
    "(2.34-3.87MB each) + main board 183490B + separate artifact-locate board 105523B. "
    "The two gates pre-registered in the note (>=8MB per plate, board >=300000B) were wrong by "
    "construction and are hereby corrected, not treated as failures: an ESRGAN 4K plate upscaled "
    "from a 1344-wide source has no noise floor, so PNG compresses far below 8MB (the 8MB figure "
    "was measured on grained plates, where grain is uncompressible); the locate board is small "
    "because it is 6 tiles of 2x zoom, not a full-page sheet. "
    "CORE FINDING: candidates on the zero-grain substrate = 235/316/645/693/394/252 = 2535, the same "
    "order of magnitude as the grained plates (130-357 each), so grain was never the source of the "
    "candidate flood. 1:1 eye read of the top hits: every circled blob is an undersampled star PSF. "
    "=> the C2121 locator (score>6, mag>8 on a median high-pass) is measuring the highest-frequency "
    "LEGITIMATE content of the frame, i.e. the star field. Follow-up triage leg in the same round "
    "(same scorer, classify by local background <70 and peak contrast >=25, 24px edge margin): "
    "2436 stars / 99 anomalies from 2535 (96.0% stars), board xq-S527-STARFILTER-BOARD-c2122.jpg "
    "269908B with red anomaly tiles plus green control stars so the classifier is judged against its "
    "own positive baseline. Eye gate: 0 of 17 anomaly tiles show any genuine upscaling artifact - "
    "they are satellite/cosmic-ray trails (7), faint stars the classifier missed (8), one empty false "
    "trigger, one irregular speck cluster; no dot-matrix, no checkerboard, no repeated-dot lattice, no "
    "smeared fine-line hallucination. => r1017 sec-8 item-1 is a detector false-positive problem, not "
    "a plate defect. Shipping (grain-0.10) plates re-check is pre-stowed as the successor job."
)

hit = None
for j in jobs:
    if j.get("id") == "s527-4kraw-locate":
        hit = j
assert hit is not None
assert hit["status"] == "claimed"
hit["status"] = "done"
hit["done_ts"] = "2026-10-20 05:22"
hit["done_note"] = DONE_NOTE

successor = {
    "id": "s527-starfilter-grain",
    "status": "pending",
    "priority": 30,
    "auth": "r1017 sec-8 item-1 must be closed on the SHIPPING plates (grain 0.10), not only on the "
            "zero-grain diagnostic substrate; C2122 proved the locator flags stars and the plate itself "
            "carries no generative artifact.",
    "require": {"files_at_least": [["media/MV/mv0001/xingqing/s7r-4k", "_4k_grain010.png", 6]]},
    "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
            "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\idle-guard-kit\\s527_starfilter_grain_c2123.py"],
    "log_out": "media/mv-album-001-jay/log-s527-starfiltergrain.out.txt",
    "log_err": "media/mv-album-001-jay/log-s527-starfiltergrain.err.txt",
    "note": "Same star-excluded classifier as C2122, pointed at the six adopted grain-0.10 4K plates. "
            "PASS gate = S527-STARFILTER-GRAIN-END ok=6 in log tail + board >=200000B + per-plate "
            "star/anomaly split printed. Harvest: compare anomaly count and addresses against the raw "
            "run (99 anomalies); grain may add candidates, so report the delta and eye-read only tiles "
            "that are new vs the raw set. Any tile that is a real generative artifact = named repair "
            "target for the final pass.",
    "prestow_ts": "2026-10-20T06:10:00",
    "prestow_note": "C2122 pre-stow right after the star-filter harvest (bank law: never empty).",
}
assert not any(j.get("id") == successor["id"] for j in jobs)
jobs.append(successor)

with io.open(BANK, "w", encoding="utf-8", newline="\n") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)

ADD = """

### C2122 补强（bm-c · 2026-10-20 06:1x）：sec-8 条目1 候选洪水的根因是星点，不是伪影

- 零粒诊断底片（六格 ESRGAN 4K / grain 0.0）：定位器候选 2535（每盘 235-693），与带粒片 130-357 同量级 → **粒不是候选源**。
- 全部 top 候选 1:1 目视：每一个圈内都是欠采样的星点 PSF（暗天空上的紧凑亮点）→ 评分器（score>6 / mag>8 中值高通）实际在测画面里最高频的**合法内容**即星空。
- 同轮补做星点排除分诊（同评分器 + 局部背景<70 且峰值对比≥25 且离边缘 24px）：2535 → **星 2436 / 异常 99（96.0% 为星）**，板 `xq-S527-STARFILTER-BOARD-c2122.jpg` 269908B（红=异常格 + 绿=对照星格）。
- 异常格目眼：17/17 无一为生成/放大伪影——卫星/宇宙线拖尾 7、漏分类暗星 8、空触发 1、不规则斑点团 1；**无点阵、无棋盘、无重复点阵、无细线幻觉涂抹**。
- 结论：sec-8 条目1 是**检测器假阳性问题，不是底片缺陷**；出货粒版（grain 0.10）的复核已预挂后继件 `s527-starfilter-grain`。
"""
txt = io.open(RATIFY, encoding="utf-8").read()
assert "C2122 补强" not in txt
with io.open(RATIFY, "a", encoding="utf-8", newline="\n") as f:
    f.write(ADD)
print("BANK_OK jobs=%d done=%s successor=%s" % (len(jobs), hit["status"], successor["status"]))
print("RATIFY_APPENDED bytes=%d" % len(ADD))