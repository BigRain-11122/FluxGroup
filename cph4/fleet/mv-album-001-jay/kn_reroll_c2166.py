# -*- coding: utf-8 -*-
# kn_reroll_c2166.py - 《可爱女人》KF 定向重摇（C2166 首帧闸修复腿）
# 复用 kf_batch_v21 的 graph()（krea2 turbo 8 步 + 可选 jman LoRA），只做「指定镜 + 种子偏移 + 旧帧归档」
# 用法:
#   python kn_reroll_c2166.py --only KN02,KN03 --strength 0.7 --seed-offset 1
#   python kn_reroll_c2166.py --only KN05 --seed-offset 2 --dry-run
# 律: SKIP 判据在 kf_batch_v21 里是「目标存在且 >100KB 即跳过」——本脚本先归档旧帧再烧，避免空跑。
import argparse, os, shutil, sys, time, importlib.util, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

V21 = _load("kf_batch_v21", os.path.join(HERE, "kf_batch_v21.py"))
KN_M = V21.KN_M

FRAMES = V21.REPO_MEDIA
ARCH = os.path.join(FRAMES, "_reroll-c2166")

def seed_map():
    """与 kf_batch_v21.main() 完全同口径：sorted(jobs) 顺序，XQ base 40100001 / KN base 40200001"""
    jobs = V21.build_jobs()
    seed_of = {}
    for trk, base in V21.SEED_BASE.items():
        i = 0
        for key in sorted(jobs):
            if key.startswith(trk + "|"):
                seed_of[key] = base + i
                i += 1
    return jobs, seed_of

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--only", required=True)
    ap.add_argument("--strength", type=float, default=0.6)
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    jobs, seed_of = seed_map()
    ids = [x.strip() for x in a.only.split(",") if x.strip()]
    os.makedirs(ARCH, exist_ok=True)

    print("REROLL plan: ids=%s strength=%.2f seed_offset=%d dry=%s" % (ids, a.strength, a.seed_offset, a.dry_run), flush=True)
    for sid in ids:
        key = "KN|" + sid
        if key not in jobs:
            print("MISS", sid, flush=True); continue
        prompt = jobs[key][0]
        base_seed = seed_of[key] + a.seed_offset
        dst = os.path.join(FRAMES, "KN_%s.png" % sid)
        print("PLAN %s seed=%d jman=%s dst=%s" % (sid, base_seed, "jman" in prompt, dst), flush=True)
        if a.dry_run:
            continue
        if os.path.isfile(dst):
            shutil.move(dst, os.path.join(ARCH, "KN_%s_prev.png" % sid))
            print("ARCHIVED prev -> %s" % os.path.join(ARCH, "KN_%s_prev.png" % sid), flush=True)
        import urllib.request, uuid
        g = V21.graph(prompt, base_seed, "jman" in prompt, a.strength)
        req = urllib.request.Request(a.server + "/prompt",
                                     data=json.dumps({"prompt": g, "client_id": str(uuid.uuid4())}).encode(),
                                     headers={"Content-Type": "application/json"})
        pid = json.loads(urllib.request.urlopen(req, timeout=120).read())["prompt_id"]
        t0 = time.time(); ok = False
        while time.time() - t0 < 900:
            time.sleep(3)
            try:
                h = json.loads(urllib.request.urlopen(a.server + "/history/" + pid, timeout=30).read())
            except Exception:
                continue
            if pid in h:
                for _nid, out in h[pid]["outputs"].items():
                    for img in out.get("images", []):
                        data = urllib.request.urlopen(
                            "%s/view?filename=%s&subfolder=%s&type=%s" % (a.server, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                            timeout=60).read()
                        open(dst, "wb").write(data)
                        ok = True
                break
        print("BURN %s %s (%ds) -> %s" % (sid, "OK" if ok else "FAIL", int(time.time() - t0), dst), flush=True)
    print("REROLL DONE", flush=True)

if __name__ == "__main__":
    main()