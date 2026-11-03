# -*- coding: utf-8 -*-
"""mv_lora_eval.py - 角色 LoRA 验收闸。训完先过这道，过了才准开 MV。

为什么有它：2026-11-03 CEO 令「以后 MV 开始前，先把男女主和路人的 LoRA 给我烧出来，
周杰伦的可以一直更新直到最稳」。光有 LoRA 文件不等于脸稳——必须用同一套脸判据
（SFace 余弦）在多个角度/光线下量出来，量不过就当没训。

做法：拿指定 LoRA 在现场跑 6 张固定测试图（正 / 左 3/4 / 右 3/4 / 低角 / 侧脸 / 暖暗），
逐张与定妆参考算人脸相似度，中位与最低值双判，结果写 lock 文件。

用法：
  python Tools/mv_lora_eval.py --lora jman_v1_rank32.safetensors \
      --ref cph4/fleet/mv0001-handover/canon/refs/HIM-ref-20261103.png \
      --char him --out cph4/fleet/mv0001-handover/canon/MV-LORA-LOCK.json
退出码：0 PASS / 2 REVISE（重训）/ 3 BLOCKED（输入缺失）
"""
import argparse, json, os, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mv_kf_batch as KF          # noqa: E402
import mv_shot_gate as G          # noqa: E402

TH_MEDIAN = 0.40      # 六个角度的中位相似度
TH_MIN = 0.28         # 最差一档（侧脸/低角允许掉一点）

# 六个角度的固定考卷：换角度=换考法，让 LoRA 不能只背一个构图
FRAME_CUE = ", the whole head and shoulders inside the frame"

ANGLES = [
    ("front", "A close-up at eye level of {id}, facing the lens straight on, calm neutral expression" + FRAME_CUE),
    ("q34_left", "A close-up at eye level of {id}, head turned three-quarters to the left, eyes to the left of frame" + FRAME_CUE),
    ("q34_right", "A close-up at eye level of {id}, head turned three-quarters to the right, eyes to the right of frame" + FRAME_CUE),
    ("low", "A close-up from slightly below eye level of {id}, chin lifted, looking off frame" + FRAME_CUE),
    ("profile", "A profile close-up at eye level of {id}, exact side view, looking ahead" + FRAME_CUE),
    ("warm_dim", "A medium close-up at eye level of {id} in dim warm tungsten light, face half in shadow" + FRAME_CUE),
]

DEFAULT_ID = {
    "him": "a 20-year-old Taiwanese man of 2001 with heavy-lidded single-lidded eyes, thick lower lip, "
           "wide flat rounded jaw, natural unretouched skin, thick black hair with a blunt fringe",
    "her": "a young Taiwanese woman of 2001 with a softly rounded youthful face, large dark eyes, "
           "long straight black hair with a full blunt fringe, natural unretouched skin",
    "extra": "a museum visitor in their thirties, ordinary everyday face, natural skin",
}


def post(server, payload):
    req = urllib.request.Request(server + "/prompt", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(server, path):
    return json.loads(urllib.request.urlopen(server + path, timeout=30).read())


def gen_one(server, prompt, seed, lora, strength, outdir, tag):
    g = KF.graph(prompt, seed, "krea2_turbo_int8_convrot.safetensors",
                 "qwen3vl_4b_fp8_scaled.safetensors", 1344, 768, lora, strength)
    pid = post(server, {"prompt": g, "client_id": str(uuid.uuid4())})["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(3)
        h = get(server, "/history/" + pid)
        if pid in h:
            for out in h[pid]["outputs"].values():
                for img in out.get("images", []):
                    url = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                        server, img["filename"], img.get("subfolder", ""), img.get("type", "output"))
                    dst = os.path.join(outdir, tag + ".png")
                    open(dst, "wb").write(urllib.request.urlopen(url, timeout=180).read())
                    return dst
            return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", required=True)
    ap.add_argument("--ref", required=True, help="定妆参考脸（一张清晰正脸）")
    ap.add_argument("--char", default="him", choices=["him", "her", "extra"])
    ap.add_argument("--id-text", default="", help="角色基础描述；留空用 --char 的内置描述")
    ap.add_argument("--strength", type=float, default=0.8)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--out", default="")
    ap.add_argument("--seed", type=int, default=9700)
    a = ap.parse_args()

    if not os.path.exists(a.ref):
        print("BLOCKED: reference not found", a.ref)
        return 3
    ref_feat, ref_n, ref_ratio, ref_clip = G.face_detect_full(__import__("cv2").imread(a.ref))
    if ref_feat is None:
        print("BLOCKED: no usable face in reference (ratio=%.2f clipped=%s)" % (ref_ratio, ref_clip))
        return 3

    id_text = a.id_text or DEFAULT_ID[a.char]
    outdir = os.path.join(os.path.dirname(a.ref), "..", "lora-eval",
                          os.path.splitext(os.path.basename(a.lora))[0])
    outdir = os.path.normpath(outdir)
    os.makedirs(outdir, exist_ok=True)

    rows = []
    get(a.server, "/system_stats")
    for i, (tag, tpl) in enumerate(ANGLES):
        dst = gen_one(a.server, tpl.format(id=id_text), a.seed + i, a.lora, a.strength, outdir, tag)
        if not dst:
            rows.append(dict(angle=tag, sim=None, note="generation failed"))
            print("%-10s FAILED" % tag)
            continue
        feat, n, ratio, clipped = G.face_detect_full(__import__("cv2").imread(dst))
        if feat is None:
            rows.append(dict(angle=tag, sim=None, note="no face (ratio=%.2f clipped=%s)" % (ratio, clipped)))
            print("%-10s NO-FACE ratio=%.2f clipped=%s" % (tag, ratio, clipped))
            continue
        sim = float((feat * ref_feat).sum())
        rows.append(dict(angle=tag, sim=round(sim, 3), file=dst))
        print("%-10s sim=%.3f" % (tag, sim))

    measured = [r["sim"] for r in rows if r.get("sim") is not None]
    missing = [r["angle"] for r in rows if r.get("sim") is None]
    if not measured:
        print("BLOCKED: no measurable face in any test image")
        return 3
    # 测不出的角度按 0 计：LoRA 在这类角度产不出可辨的脸，本身就是缺陷，
    # 不能让它从分母里消失（首跑就是这样被抬成 PASS 的）。
    sims = [r["sim"] if r.get("sim") is not None else 0.0 for r in rows]
    sims_sorted = sorted(sims)
    med = sims_sorted[len(sims_sorted) // 2]
    lo = sims_sorted[0]
    coverage = len(measured) / float(len(rows))
    ok = (med >= TH_MEDIAN and lo >= TH_MIN and coverage >= 1.0)
    verdict = "PASS" if ok else "REVISE"
    print("median=%.3f min=%.3f coverage=%d/%d -> %s (need median>=%.2f, min>=%.2f, all angles measurable)"
          % (med, lo, len(measured), len(rows), verdict, TH_MEDIAN, TH_MIN))
    if missing:
        print("UNMEASURABLE angles (counted as 0): %s" % ", ".join(missing))

    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump({"lora": a.lora, "char": a.char, "ref": a.ref, "strength": a.strength,
                   "verdict": verdict, "median": round(med, 3), "min": round(lo, 3),
                   "thresholds": {"median": TH_MEDIAN, "min": TH_MIN},
                   "coverage": "%d/%d" % (len(measured), len(rows)), "unmeasurable": missing,
                   "rows": rows, "tested_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                  open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("lock ->", a.out)
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())