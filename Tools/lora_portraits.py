# -*- coding: utf-8 -*-
"""lora_portraits.py - 角色定妆组图生成（给 LoRA 训练备素材）。

为什么单独一个脚本：LoRA 的素材不能从成片里抽（v721 全片 234 帧只有 1 帧女主脸宽达标），
必须先用 krea2 按正典 ID 块生成 20-30 张多光位多姿态的同一个人，才能训。
本脚本不吃 mv_kf_batch 的 preflight 闸——那道闸管的是"片镜准入"，训练素材是另一回事。

用法：
  python Tools/lora_portraits.py --name her_mv0001 --trigger h01 \
      --base "a young taiwanese woman around twenty, ..." --count 24
输出：D:\\FluxGroup-Offload\\15-training\\dataset\\<name>\\<name>_NNN.png + 同名 .txt
"""
import argparse, json, os, random, sys, time, urllib.request

TRAIN_HOME = os.environ.get("LORA_HOME", r"D:\FluxGroup-Offload\15-training")
# 变化维度：光位 × 景别 × 姿态。同一张脸必须覆盖这些，LoRA 才不会只在一种光下像。
LIGHTS = ["warm tungsten practicals, single soft key from the left",
          "flat overcast daylight through a window",
          "cool fluorescent museum light from above",
          "backlit by a rainy street lamp, face half in shadow"]
SHOTS = ["medium close-up, chest up", "close-up, head and shoulders", "waist-up, slight three-quarter turn"]
POSES = ["looking away from camera, lips slightly parted",
         "one hand lifting hair behind the ear, eyes down",
         "walking past, body angled to camera, head turned back over shoulder",
         "sitting, leaning forward on elbows, gaze to the side",
         "standing, adjusting the bag strap, chin lowered",
         "hands holding a paperback, eyes on the page"]
TAIL = "natural clear skin with visible pores, fine film grain, no airbrush, 2001 taiwanese film look"


def graph(prompt, seed, w, h):
    return {
        "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
              "model": ["10", 0], "positive": ["6", 0], "negative": ["6", 0],
              "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "29": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "lora_pf"}},
    }


def post(server, path, payload):
    req = urllib.request.Request(server + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def get(server, path):
    return json.loads(urllib.request.urlopen(server + path, timeout=60).read())


def _size_ok(data, w, h):
    """PNG/JPEG 里直接读宽高，不依赖 Pillow。"""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(data[16:20], "big") == w and int.from_bytes(data[20:24], "big") == h
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            m = data[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                return (int.from_bytes(data[i + 7:i + 9], "big") == w and
                        int.from_bytes(data[i + 5:i + 7], "big") == h)
            if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                i += 2
                continue
            i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    except Exception:
        return False
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--name", required=True)
    ap.add_argument("--trigger", required=True)
    ap.add_argument("--base", required=True, help="正典 ID 块（年代脸结构+服装锚），逐字复用")
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    a = ap.parse_args()

    try:
        get(a.server, "/system_stats")
    except Exception as e:
        print("BLOCKED: ComfyUI 未就绪 %s (%s)" % (a.server, e))
        return 3

    # 队列占用守卫：ComfyUI 被别的长任务（MV 批）占着时提交只会排队超时，
    # 2026-11-03 实测一条 job 排队 4 分钟未完成 —— 等着，别硬塞 24 条。
    for _ in range(60):
        try:
            q = get(a.server, "/queue")
            busy = len(q.get("queue_running", [])) + len(q.get("queue_pending", []))
        except Exception:
            busy = 0
        if busy == 0:
            break
        print("… ComfyUI 忙（%d 条在队），等 30s" % busy, flush=True)
        time.sleep(30)

    out = os.path.join(TRAIN_HOME, "dataset", a.name)
    os.makedirs(out, exist_ok=True)
    combos = [(l, s, p) for l in LIGHTS for s in SHOTS for p in POSES]
    random.Random(a.seed).shuffle(combos)
    combos = combos[:a.count]

    # 续编号：队列会分两批调（16:9 一批、9:16 一批），都从 001 起会互相覆盖，
    # 结果每型恒定只有第一批那么多张（2026-11-04 实锚：每型 12 张，永远凑不够 15）。
    start = 0
    for f in os.listdir(out):
        stem = os.path.splitext(f)[0]
        head = "%s_" % a.name
        if f.endswith(".png") and stem.startswith(head):
            try:
                start = max(start, int(stem[len(head):]))
            except ValueError:
                pass

    done = 0
    streak_fail = 0
    for j, (light, shot, pose) in enumerate(combos, 1):
        i = start + j
        if streak_fail >= 3:
            print("ABORT: 连失败 3 条，ComfyUI 不可用，停手（不硬烧）")
            break
        dst = os.path.join(out, "%s_%03d.png" % (a.name, i))
        if os.path.exists(dst):
            done += 1
            continue
        prompt = "%s, exactly one figure in the frame, %s, %s, %s, %s" % (a.base, shot, pose, light, TAIL)
        prefix = "lora_pf_%s_%03d" % (a.name, i)
        g = graph(prompt, a.seed + i * 7, a.width, a.height)
        g["29"]["inputs"]["filename_prefix"] = prefix
        try:
            pid = post(a.server, "/prompt", {"prompt": g, "client_id": "lora-portraits"})["prompt_id"]
        except Exception as e:
            print("[%d/%d] FAIL submit %s" % (i, len(combos), e))
            continue
        for _ in range(180):
            time.sleep(2)
            h = get(a.server, "/history/" + pid)
            if pid in h:
                break
        else:
            print("[%d/%d] TIMEOUT %s" % (i, len(combos), pid))
            streak_fail += 1
            continue
        imgs = h[pid]["outputs"].get("29", {}).get("images", [])
        if not imgs:
            print("[%d/%d] NO IMAGE %s" % (i, len(combos), pid))
            continue
        src = os.path.join(os.environ.get("COMFY_OUT", r"D:\AI\comfyui-krea\ComfyUI_windows_portable\ComfyUI\output"),
                           imgs[0].get("subfolder", ""), imgs[0]["filename"])
        try:
            with open(src, "rb") as f:
                data = f.read()
        except Exception as e:
            print("[%d/%d] MOVE FAIL %s" % (i, len(combos), e))
            continue
        # 尺寸自证：ComfyUI 忙碌时 history 可能拿到别的产物（2026-11-03 实测混进过一张 1920x1096 成片帧），
        # 尺寸对不上就丢掉，宁缺毋滥——错图进数据集等于给角色训一张别人的脸。
        if not _size_ok(data, a.width, a.height):
            print("[%d/%d] REJECT 尺寸不符 %s" % (i, len(combos), src))
            continue
        with open(dst, "wb") as f:
            f.write(data)
        with open(os.path.splitext(dst)[0] + ".txt", "w", encoding="utf-8") as f:
            f.write("%s, %s, %s, %s\n" % (a.trigger, shot, pose, light))
        done += 1
        streak_fail = 0
        print("[%d/%d] ok %s" % (i, len(combos), os.path.basename(dst)), flush=True)

    print(json.dumps({"dataset": out, "images": done, "requested": len(combos)}, ensure_ascii=False))
    return 0 if done >= 15 else 3


if __name__ == "__main__":
    sys.exit(main())