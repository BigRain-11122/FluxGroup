# -*- coding: utf-8 -*-
"""角色一致性锁（cast lock）：把「女主/男主是同一个人」变成可执行、可核验的契约。

为什么需要它：本机没有 IPAdapter / InstantID / PhotoMaker 权重（只有 clip_vision 底座），
SDXL 靠提示词生成时脸会逐镜漂移。能落地的做法只有三件，必须一起做：
  1. 锚图（cast/<ROLE>/ref.png）—— 唯一权威外观，所有镜头以它为准；
  2. 锁定串（appearance tokens + outfit + seed）—— 每镜提示词都必须带同一段；
  3. 生成后核验（verify）—— 用主控 VLM 两图比对，判 SAME / DIFFERENT，不是靠肉眼抽查。

用法：
  python Tools/fleet/cast_lock.py add mv0002-longjuanfeng HER --ref <png>
  python Tools/fleet/cast_lock.py show mv0002-longjuanfeng
  python Tools/fleet/cast_lock.py prompt mv0002-longjuanfeng HER --scene "sits by the window"
  python Tools/fleet/cast_lock.py verify mv0002-longjuanfeng HER <shot1.png> <shot2.png> ...
Exit: 0 全 SAME；1 有 DIFFERENT；3 无法核验（模型/图缺失）
"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
FILMS = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay")
HOST = os.environ.get("OLLAMA_HOST") or "http://100.75.133.10:11434"
VLM = os.environ.get("CAST_VLM") or "qwen3.5:4b-mlx"


def cast_dir(film, role):
    return os.path.join(FILMS, film, "cast", role)


def contract_path(film, role):
    return os.path.join(cast_dir(film, role), "cast.json")


def ask(images, prompt, timeout=180):
    body = {"model": VLM, "prompt": prompt, "images": images, "stream": False,
            "think": False, "options": {"temperature": 0.1, "num_predict": 120}}
    req = urllib.request.Request(HOST + "/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return " ".join((r.get("response") or "").split())


SCENE_WORDS = ("window", "rain", "street", "room", "background", "wall", "standing", "sitting",
               "before", "behind", "in front of", "outdoors", "indoors", "light", "scene")


def strip_scene(desc):
    """锁定串里只能有人物属性：场景/姿态/光线一律剔除，否则每镜都被钉在同一个环境。

    2026-11-08 实测：VLM 会把「stands before a rain-streaked window」一起写进来。
    """
    keep = []
    for part in (desc or "").split(","):
        low = part.strip().lower()
        if not low:
            continue
        if any(w in low for w in SCENE_WORDS):
            continue
        keep.append(part.strip().rstrip("."))
    return ", ".join(keep)


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def cmd_add(a):
    role_dir = cast_dir(a.film, a.role)
    os.makedirs(role_dir, exist_ok=True)
    ref = os.path.join(role_dir, "ref.png")
    shutil.copyfile(a.ref, ref)
    # 外观描述由 VLM 读锚图得出，避免我手写一份可能和真人对不上的词
    desc = ""
    try:
        desc = ask([b64(ref)],
                   "Describe only the visible appearance of the person in this photo, for use as a "
                   "fixed appearance prompt in an image generator: apparent age, gender, hair, "
                   "face features, clothing. One sentence, English, under 40 words, no names.")
    except Exception as e:
        print("[cast] 外观描述失败（不阻塞）：%s" % str(e)[:80])
    seed = int(hashlib.sha1((a.film + a.role).encode("utf-8")).hexdigest()[:8], 16) % 100000
    rec = {
        "film": a.film, "role": a.role, "ref": os.path.relpath(ref, ROOT),
        "seed": seed,
        "appearance": strip_scene(desc),
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "law": ("每一镜都必须带同一段 appearance 与同一 seed；镜头内的场景/动作可以变，"
                "发型长度、脸型、年龄段、服装基线不许变；改锚必须走 add 重锁并重验全片。"),
    }
    json.dump(rec, open(contract_path(a.film, a.role), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[cast] 锁定 %s/%s seed=%d" % (a.film, a.role, seed))
    print("       ref ->", rec["ref"])
    print("       appearance:", rec["appearance"] or "(空)")
    return 0


def cmd_show(a):
    base = os.path.join(FILMS, a.film, "cast")
    if not os.path.isdir(base):
        print("[cast] 该片还没有定型")
        return 3
    for role in sorted(os.listdir(base)):
        p = contract_path(a.film, role)
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        print("== %s  seed=%s" % (role, d.get("seed")))
        print("   ref:", d.get("ref"))
        print("   appearance:", d.get("appearance"))
    return 0


def cmd_prompt(a):
    p = contract_path(a.film, a.role)
    if not os.path.exists(p):
        print("[cast] 未锁定 %s/%s" % (a.film, a.role))
        return 3
    d = json.load(open(p, encoding="utf-8"))
    locked = d.get("appearance") or ""
    text = "%s, %s" % (locked, a.scene) if a.scene else locked
    print(json.dumps({"seed": d.get("seed"), "prompt": text}, ensure_ascii=False))
    return 0


def cmd_verify(a):
    p = contract_path(a.film, a.role)
    if not os.path.exists(p):
        print("[cast] 未锁定 %s/%s" % (a.film, a.role))
        return 3
    d = json.load(open(p, encoding="utf-8"))
    ref = os.path.join(ROOT, d["ref"])
    if not os.path.exists(ref):
        print("[cast] 锚图不见了：", ref)
        return 3
    shots = [s for s in a.shots if os.path.exists(s)]
    if not shots:
        print("[cast] 没有可核验的镜头图")
        return 3
    refb = b64(ref)
    ok, bad, err = [], [], []
    for s in shots:
        try:
            ans = ask([refb, b64(s)],
                      "First image is the reference person. Second image is a shot from a film. "
                      "Is the person in the second image the SAME person as the first? "
                      "Answer with one word SAME or DIFFERENT, then a short reason.")
        except Exception as e:
            err.append([os.path.basename(s), str(e)[:100]])
            continue
        up = ans.upper()
        verdict = "SAME" if up.startswith("SAME") else ("DIFFERENT" if "DIFFERENT" in up else "UNKNOWN")
        (ok if verdict == "SAME" else bad).append({"shot": os.path.relpath(s, ROOT),
                                                   "verdict": verdict, "why": ans[:160]})
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "film": a.film, "role": a.role,
           "ref": d["ref"], "checked": len(shots), "same": len(ok), "different": len(bad),
           "errors": err, "outliers": bad[:20],
           "verdict": "PASS" if not bad and ok else ("FAIL" if bad else "UNKNOWN")}
    out = a.out or os.path.join(FILMS, a.film, "cast", "%s-verify-%s.json"
                                % (a.role, time.strftime("%Y%m%d")))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[cast] %s/%s 核验 %d 张：SAME %d / DIFFERENT %d / 错误 %d -> %s"
          % (a.film, a.role, len(shots), len(ok), len(bad), len(err), rec["verdict"]))
    for b in bad[:5]:
        print("   ! ", os.path.basename(b["shot"]), "|", b["why"][:90])
    print("  ->", os.path.relpath(out, ROOT))
    return 0 if rec["verdict"] == "PASS" else (1 if bad else 3)


def upload_ref(server, ref_path, name):
    """把锚图放进 ComfyUI 的 input 目录（幂等覆盖），返回可在 LoadImage 里用的文件名。"""
    import uuid
    b = uuid.uuid4().hex
    parts = []
    for k, v in (("overwrite", "true"), ("type", "input"), ("subfolder", "")):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                      % (b, k, v)).encode())
    data = open(ref_path, "rb").read()
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                  "Content-Type: image/png\r\n\r\n" % (b, name)).encode())
    parts.append(data)
    parts.append(("\r\n--%s--\r\n" % b).encode())
    req = urllib.request.Request(server + "/upload/image", data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=" + b})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    return r.get("name") or name


def graph_img2img(pos, neg, seed, conf, img_name, w, h, denoise):
    """从锚图出发做 img2img：纯文字生成锁不住真人脸（实测 0/2 SAME），必须让模型从锚图出发。"""
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": conf["ckpt"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4", 1]}},
        "10": {"class_type": "LoadImage", "inputs": {"image": img_name}},
        "11": {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["4", 2]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": int(conf.get("steps", 8)), "cfg": float(conf.get("cfg", 2.0)),
            "sampler_name": conf.get("sampler", "euler"), "scheduler": conf.get("scheduler", "normal"),
            "denoise": float(denoise), "model": ["4", 0], "positive": ["6", 0],
            "negative": ["7", 0], "latent_image": ["11", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "castshot"}},
    }


PULID_FILE = "ip-adapter_pulid_sdxl_fp16.safetensors"


def graph_pulid(pos, neg, seed, conf, img_name, w, h, weight=0.9, method="fidelity"):
    """PuLID 出图：身份从锚图注入，姿势/场景由提示词决定（img2img 做不到这一点）。

    2026-11-09 实测：同一锚图三个不同姿势/场景，VLM 判 3/3 SAME；
    而 img2img 在同样三个场景下画面几乎不变。
    """
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": conf["ckpt"]}},
        "2": {"class_type": "PulidModelLoader", "inputs": {"pulid_file": PULID_FILE}},
        "3": {"class_type": "PulidEvaClipLoader", "inputs": {}},
        "4": {"class_type": "PulidInsightFaceLoader", "inputs": {"provider": "CUDA"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": img_name}},
        "6": {"class_type": "ApplyPulid", "inputs": {"model": ["1", 0], "pulid": ["2", 0],
                                                    "eva_clip": ["3", 0], "face_analysis": ["4", 0],
                                                    "image": ["5", 0], "method": method,
                                                    "weight": float(weight), "start_at": 0.0, "end_at": 1.0}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["1", 1]}},
        "8": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
        "9": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "10": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": int(conf.get("steps", 8)),
                                                    "cfg": float(conf.get("cfg", 2.0)),
                                                    "sampler_name": conf.get("sampler", "euler"),
                                                    "scheduler": conf.get("scheduler", "normal"),
                                                    "denoise": 1.0, "model": ["6", 0],
                                                    "positive": ["7", 0], "negative": ["8", 0],
                                                    "latent_image": ["9", 0]}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["1", 2]}},
        "12": {"class_type": "SaveImage", "inputs": {"images": ["11", 0], "filename_prefix": "castshot"}},
    }


def cmd_shot(a):
    """按锁定契约出一张镜头：默认从锚图 img2img（denoise 控制「保留多少原脸」）。"""
    import asset_gen as ag
    import char_gen as cg
    p = contract_path(a.film, a.role)
    if not os.path.exists(p):
        print("[cast] 未锁定 %s/%s" % (a.film, a.role))
        return 3
    d = json.load(open(p, encoding="utf-8"))
    ref = os.path.join(ROOT, d["ref"])
    conf = json.load(open(os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1",
                                       "comfy-bm-c.json"), encoding="utf-8"))
    pos = "%s, %s, cinematic film still, natural skin texture, shallow depth of field, 35mm" % (
        d["appearance"], a.scene)
    neg = a.negative
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    if a.engine == "pulid":
        name = upload_ref(a.server, ref, "cast_%s_%s.png" % (a.film, a.role))
        g = graph_pulid(pos, neg, d["seed"], conf, name, a.width, a.height,
                        weight=a.pulid_weight, method=a.pulid_method)
    elif a.engine == "text":
        g = cg.graph_ckpt(pos, neg, d["seed"], conf, a.width, a.height)
    else:
        name = upload_ref(a.server, ref, "cast_%s_%s.png" % (a.film, a.role))
        g = graph_img2img(pos, neg, d["seed"], conf, name, a.width, a.height, a.denoise)
    ok = ag.submit_and_save(cg, a.server, g, a.out)
    print("[cast] %s %s -> %s (%s)" % (a.role, a.engine,
                                       a.out, "ok" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("add"); p1.add_argument("film"); p1.add_argument("role")
    p1.add_argument("--ref", required=True); p1.set_defaults(fn=cmd_add)
    p2 = sub.add_parser("show"); p2.add_argument("film"); p2.set_defaults(fn=cmd_show)
    p3 = sub.add_parser("prompt"); p3.add_argument("film"); p3.add_argument("role")
    p3.add_argument("--scene", default=""); p3.set_defaults(fn=cmd_prompt)
    p5 = sub.add_parser("shot"); p5.add_argument("film"); p5.add_argument("role")
    p5.add_argument("--scene", required=True); p5.add_argument("--out", required=True)
    p5.add_argument("--denoise", type=float, default=0.45)
    p5.add_argument("--engine", default="pulid", choices=["pulid", "img2img", "text"],
                    help="pulid=身份注入且姿势自由（默认）；img2img=锁构图；text=纯文字")
    p5.add_argument("--pulid-weight", type=float, default=0.9)
    p5.add_argument("--pulid-method", default="fidelity", choices=["fidelity", "style", "neutral"])
    p5.add_argument("--width", type=int, default=1024); p5.add_argument("--height", type=int, default=1536)
    p5.add_argument("--server", default="http://127.0.0.1:8188")
    p5.add_argument("--negative", default=("text, watermark, anime, cartoon, 3d render, oversmooth skin, "
                                           "plastic skin, heavy makeup, celebrity likeness, extra fingers, "
                                           "deformed, two faces, duplicated figure"))
    p5.set_defaults(fn=cmd_shot)
    p4 = sub.add_parser("verify"); p4.add_argument("film"); p4.add_argument("role")
    p4.add_argument("shots", nargs="+"); p4.add_argument("--out", default="")
    p4.set_defaults(fn=cmd_verify)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))