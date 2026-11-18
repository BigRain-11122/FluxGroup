"""本机 ASR 语料抽检（Windows / CUDA，openai-whisper 后端）。

faster-whisper 1.2.1 与本机 huggingface_hub 1.33 接口不兼容
（open() got an unexpected keyword argument 'metadata_error'），故走 openai-whisper。

判据：
  - 转写出的中文字符 >= 4 且非重复噪声 = 有人声可识别
  - 纯 BGM / 只有音效 / 只有尖叫 = 判 FAIL，不进训练集

用法：
  python Tools/fleet/asr_qc_win.py --dir <sliced> --n 0 --model base --json <out>
      --n 0 = 全量
"""
import argparse
import json
import os
import random
import re
import sys
import time


def is_noise(text):
    """重复单字/标点堆叠视为无声识别。"""
    t = re.sub(r"[\s\W_]+", "", text)
    if len(t) < 4:
        return True
    # 同一字重复超过一半
    from collections import Counter
    c = Counter(t)
    return c.most_common(1)[0][1] / len(t) > 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--n", type=int, default=0, help="0=全量")
    ap.add_argument("--model", default="base")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(a.dir) if f.lower().endswith(".wav"))
    if not files:
        sys.exit("no wav in " + a.dir)
    if a.n and a.n < len(files):
        random.seed(20261104)
        files = random.sample(files, a.n)

    import whisper
    t0 = time.time()
    model = whisper.load_model(a.model)

    rows, ok, bad = [], 0, 0
    for name in files:
        p = os.path.join(a.dir, name)
        try:
            r = model.transcribe(p, language=a.lang, fp16=True)
            text = (r.get("text") or "").strip()
        except Exception as e:
            rows.append({"file": name, "error": str(e)[:100], "verdict": "ERROR"})
            bad += 1
            continue
        good = not is_noise(text)
        rows.append({"file": name, "chars": len(re.sub(r"\s", "", text)),
                     "text": text[:120], "verdict": "PASS" if good else "FAIL"})
        ok += 1 if good else 0
        bad += 0 if good else 1

    out = {"dir": a.dir, "model": a.model, "checked": len(rows),
           "pass": ok, "fail": bad, "elapsed_s": round(time.time() - t0, 1),
           "rows": rows}
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 只保留 PASS 的清单，供后续入库
    keep = [r["file"] for r in rows if r["verdict"] == "PASS"]
    if a.json:
        kp = a.json.replace(".json", "-keep.json")
        json.dump({"dir": a.dir, "count": len(keep), "files": keep},
                  open(kp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("checked=%d pass=%d fail=%d  %.1fs" % (len(rows), ok, bad, out["elapsed_s"]))
    for r in rows[:8]:
        print("  %-24s %s" % (r["file"][-24:], r.get("text", r.get("error", ""))[:60]))


if __name__ == "__main__":
    main()