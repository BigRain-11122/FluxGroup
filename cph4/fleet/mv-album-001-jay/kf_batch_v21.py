# -*- coding: utf-8 -*-
# kf_batch_v21.py - 《Jay》专辑 星晴/可爱女人 KF 批客户端 v2.1（bm-c 主力岗·CEO 令 10-11「能先做的先做」）
# 用法:
#   python kf_batch_v21.py --grid                 # jman LoRA 强度网格（阻断件·0.6/0.7/0.8/0.9）
#   python kf_batch_v21.py --min                  # 第一波最小可产集（不含女主脸级押后镜）
#   python kf_batch_v21.py --only XQ07,KN01      # 指定镜
# 律=判决二可7: jman 数据集=2001-03 范特西期 vs 2000《Jay》期有漂移 → strength 0.6-0.8 先网格定档
#    jman 触发词已由 v2.1 全量前挂（shots py 内 HIM 常量）；无 jman 镜不挂 LoRA 节点（strength 0 等价·省显存）
import argparse, json, os, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
XQ_M = _load("xq_shots", os.path.join(HERE, "星晴-shots-v2.py"))
KN_M = _load("kn_shots", os.path.join(HERE, "可爱女人-shots-v2.py"))

REPO_MEDIA = os.path.normpath(os.path.join(HERE, "..", "..", "..", "media", "mv-album-001-jay", "frames"))
os.makedirs(REPO_MEDIA, exist_ok=True)

# 女主脸级/近身押后镜（待 CEO 点选定版——判决二最小可产集口径·v2.1 编号）
XQ_HOLD = {"XQ01", "XQ03", "XQ04", "XQ06", "XQ09", "XQ11", "XQ12", "XQ16", "XQ22", "XQ27", "XQ29"}
KN_HOLD = {"KN24"}  # v2.2 修正：§六 认证集=53 单（押后 12=XQ11+KN24·选A 升 med=女主定版依赖）——旧版漏押多烧 1 单
# XQ17a-d 共用一帧（装配切分）→ 只产 XQ17a 一帧，标记别名
ALIAS = {"XQ17a": "XQ17", "XQ17b": "XQ17", "XQ17c": "XQ17", "XQ17d": "XQ17"}

def build_jobs():
    jobs = {}
    for s in XQ_M.NEW:
        sid = ALIAS.get(s[0], s[0])
        jobs["XQ|" + sid] = (s[5], "XQ")
    for s in KN_M.NEW:
        jobs["KN|" + s[0]] = (s[5], "KN")
    return jobs

GRID_SHOT = "XQ13"   # 网格镜：他看她（jman 正脸侧光·足够判脸）
SEED_BASE = {"XQ": 40100001, "KN": 40200001}

def graph(prompt_text, seed, use_jman, strength):
    g = {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["11", 0]}},
        "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
        "3": None, "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "jay_kf"}},
    }
    if use_jman:
        g["20"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"lora_name": "jman_v1_640_rank32_final.safetensors",
                   "strength_model": strength, "model": ["10", 0]}}
        g["3"] = {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                  "scheduler": "simple", "denoise": 1.0, "model": ["20", 0], "positive": ["6", 0],
                  "negative": ["13", 0], "latent_image": ["5", 0]}}
    else:
        g["3"] = {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler",
                  "scheduler": "simple", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0],
                  "negative": ["13", 0], "latent_image": ["5", 0]}}
    return g

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--strength", type=float, default=0.8)
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--min", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    jobs = build_jobs()

    def post(url, payload):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=120).read())

    def get(url):
        return json.loads(urllib.request.urlopen(url, timeout=30).read())

    def gen(key, prompt, seed, use_jman, strength, dst):
        pid = post(a.server + "/prompt", {"prompt": graph(prompt, seed, use_jman, strength),
                                          "client_id": str(uuid.uuid4())})["prompt_id"]
        t0 = time.time()
        while time.time() - t0 < 900:
            time.sleep(3)
            h = get(a.server + "/history/" + pid)
            if pid in h:
                for nid, out in h[pid]["outputs"].items():
                    for img in out.get("images", []):
                        data = urllib.request.urlopen(
                            "%s/view?filename=%s&subfolder=%s&type=%s" % (
                                a.server, img["filename"], img.get("subfolder", ""), img.get("type", "output")),
                            timeout=60).read()
                        open(dst, "wb").write(data)
                        return True
                return False
        return False

    if a.grid:  # 强度网格（阻断件先行·4 帧）
        prompt = jobs["XQ|" + GRID_SHOT][0]
        for st in (0.6, 0.7, 0.8, 0.9):
            dst = os.path.join(REPO_MEDIA, "GRID_XQ13_s%d.png" % int(st * 10))
            ok = gen("grid", prompt, 40100001, True, st, dst)
            print("GRID s=%.1f %s -> %s" % (st, "OK" if ok else "FAIL", dst), flush=True)
        print("GRID DONE -> 观察 GRID_XQ13_s*.png 四帧判 jman 定档（判据=2000《Jay》期钝感脸·零韩化·眉眼像度）")
        return

    # 常规批
    queue = []
    if a.only:
        for x in a.only.split(","):
            x = x.strip()
            trk = "XQ" if x.startswith("XQ") else "KN"
            queue.append("%s|%s" % (trk, ALIAS.get(x, x)))
    elif a.min:
        for key in jobs:
            sid = key.split("|")[1]
            if key.startswith("XQ|") and sid in XQ_HOLD:
                continue
            if key.startswith("KN|") and sid in KN_HOLD:
                continue
            queue.append(key)
        queue = sorted(set(queue))
    else:
        queue = sorted(jobs)
    seed_of = {}
    for trk, base in SEED_BASE.items():
        i = 0
        for key in sorted(jobs):
            if key.startswith(trk + "|"):
                seed_of[key] = base + i; i += 1
    done, fail = [], []
    for key in queue:
        prompt, trk = jobs[key]
        sid = key.split("|")[1]
        dst = os.path.join(REPO_MEDIA, "%s_%s.png" % (trk, sid))
        if os.path.isfile(dst) and os.path.getsize(dst) > 100000:
            done.append(key); print("SKIP", key, flush=True); continue
        use_jman = "jman" in prompt
        ok = gen(key, prompt, seed_of.get(key, SEED_BASE[trk]), use_jman, a.strength, dst)
        (done if ok else fail).append(key)
        print("[%d/%d] %s %s (%s)" % (len(done), len(queue), key, "OK" if ok else "FAIL",
                                      "jman" if use_jman else "plain"), flush=True)
    print("BATCH DONE %d FAIL %d -> %s" % (len(done), len(fail), REPO_MEDIA), flush=True)

if __name__ == "__main__":
    main()
