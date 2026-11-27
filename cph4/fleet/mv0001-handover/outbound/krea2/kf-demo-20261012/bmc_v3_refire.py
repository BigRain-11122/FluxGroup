# -*- coding: utf-8 -*-
# bmc_v3_refire.py -- O-20261013-1205 V3 回炉 5 槽派单执行件（V3-REFIRE-PACK-v1 · @bm-c 本地 INT8 768P）
# CEO 12:0x 本地机队令执法（「不要靠云端能力」重申）· v2 提示词律首批量产 · 纯画面无音轨（音轨禁令）。
# 血统 = bmc_night_factory verbatim 复用（r952 addon 范式）：run_i2v + cdn_upload + I2V-URL-INDEX 追加。
# 帧源律：不换帧——帧病槽（C03/C04）用 track-2 04:3x 修复帧 v2；余槽用 archive frames_full 定版帧。
# 版本梯（I2V-URL-INDEX 在册面核毕）：C02 v4->v5 · C03 v2->v3 · C04 v2_NEW->v3 · R05 v2->v3 · E03 v1->v2。
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmc_night_factory as nf  # __main__ guard in place; import side-effect-free

ARCH = r"K:\Fluxgroup\archive\mv0001-kf-frames-bmc-r840\frames_full"
FRAMES_DIR = os.path.join(HERE, "bmc", "i2v_frames")
OUT_DIR = os.path.join(HERE, "bmc", "archive_i2v")

ALIGN = ("For the target video, at 0.00 seconds into the target video, "
         "<Picture 1> (from [Shot 1]) is fully referenced.")
TAIL = (" overall_soundscape: quiet room tone with faint air and dust settling"
        " non_diegetic_music: N/A (song laid in post)"
        " About 5.2 seconds, 16:9 aspect.")

SLOTS = [
    ("C02_sand_bury_v5", os.path.join(ARCH, "C02_sand_bury.png"),
     "Locked-off medium shot. Wind-blown sand moves in intermittent gusts across the base of the stone: "
     "each gust lays a thin film of grains over the lowest row of carved wedges, the exposed carving "
     "shrinking from the bottom up, one row swallowed every second or so. Loose grains roll along the "
     "ground in the foreground. The stone itself stays unmoved. Preserve the original amber palette and film grain."),
    ("C03_dig_reveal_v3", os.path.join(FRAMES_DIR, "C03_dig_reveal_v2.png"),
     "Locked-off close shot. At the start the carved band is fully covered by compacted pale sand. "
     "A soft brush enters from frame left and sweeps right in one slow continuous pass: the bristles "
     "push the sand off in a rolling wave, and a clean margin of wedge marks emerges behind the stroke, "
     "growing column by column, until half the band reads legible. Sand grains fall from the bristles "
     "after the pass. The carved surface stays rigid. Preserve the original amber palette and film grain."),
    ("C04_words_alive_v3", os.path.join(FRAMES_DIR, "C04_words_alive_v2.png"),
     "Locked-off close shot. A narrow row of wedge-shaped marks rests on the black stone. A low warm "
     "light rakes across the band from the front left: as it travels, each shallow stroke brightens "
     "one by one and holds its thin edge of light, already-lit sections keeping a steady glow rather "
     "than blooming, the section ahead staying dark until the edge reaches it. Fine dust lifts where "
     "the light passes. The carved surface and framing stay unmoved. Preserve the matte black stone "
     "and the original amber palette."),
    ("R05_gold_threads_v3", os.path.join(ARCH, "R05_gold_threads.png"),
     "Locked-off close shot. A thin gold seam runs down the carved wall. The gold brightens in one slow "
     "continuous travel from the top of the seam to the bottom: the glow stays a narrow moving edge, "
     "passed sections settling to a steady warm shine, the unlit section ahead staying dark until the "
     "edge reaches it, no section freezing. A few dust motes drift in the lit seam. The carved rows "
     "stay rigid. Preserve the film grain and the original amber palette."),
    ("E03_gaze_meet_v2", os.path.join(ARCH, "E03_gaze_meet.png"),
     "Locked-off close shot through the display glass. The young woman's lit profile holds steady in "
     "the foreground, carried in the glass reflection. Behind the glass the man's faint silhouette "
     "surfaces in the amber light: his head turns a few degrees toward her reflected face, then stills, "
     "his gaze resting on her. She gives one slow blink, nothing else moves. Both positions and the "
     "dust layer on the glass stay unchanged. Preserve the film grain and the original amber palette."),
]


def main():
    results = {}
    for i, (tag, frame, prose) in enumerate(SLOTS):
        if not (os.path.isfile(frame) and os.path.getsize(frame) > 100000):
            nf.log("[%s] FRAME MISSING %s -- skipped (disclosed)" % (tag, frame))
            results[tag] = "FRAME_MISSING"
            continue
        prompt = ALIGN + " integrated_multimodal_description: " + prose + TAIL
        out = os.path.join(OUT_DIR, tag + ".mp4")
        ok = nf.run_i2v(frame, prompt, 9230 + i, out, tag)
        if ok:
            furl = nf.cdn_upload(out, tag)
            results[tag] = furl or "BURNED_UPLOAD_FAIL"
        else:
            results[tag] = "BURN_FAIL"
    nf.log("V3 REFIRE COMPLETE: %s" % results)


if __name__ == "__main__":
    main()
