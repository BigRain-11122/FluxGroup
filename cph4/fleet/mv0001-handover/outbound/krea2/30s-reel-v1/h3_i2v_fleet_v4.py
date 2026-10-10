# -*- coding: utf-8 -*-
# h3_i2v_fleet_v4.py - 机队机器用·mv0001 30秒重制 v4 本地 MiniMax-H3 i2v 客户端（自包含·2026-10-10 派单）
# 用法: python h3_i2v_fleet_v4.py --repo <FluxGroup仓库根> [--server http://127.0.0.1:8188] [--out <产物目录>] [--only S1,S2]
# 输入: <repo>/cph4/fleet/mv0001-handover/outbound/krea2/30s-reel-v1/{frames/, local_h3_i2va_v4.json, h3_i2v_local_768p_v4.json}
# 硬律: 纯画面无音轨(工作流已剥audio链)·FIFO共服(不动他窗队列项)·逐镜自检分<7.5记种子重摇
import argparse, json, os, shutil, sys, time, urllib.request, uuid


def http_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def upload_image(server, path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----i2v" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(server + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)


def run_shot(server, wf_path, out_dir, comfy_out_hint, tag, frame_path, prompt, seed, length, width, height):
    img = upload_image(server, frame_path)
    wf = json.load(open(wf_path, "r", encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = prompt
    n6["length"] = length
    n6["width"] = width
    n6["height"] = height
    wf["10"]["inputs"]["noise_seed"] = seed
    pid = http_json(server + "/prompt", {"prompt": wf, "client_id": "fleet-mv30s-v4"})["prompt_id"]
    print("[%s] SUBMITTED frame=%s seed=%d" % (tag, img, seed), flush=True)
    t0 = time.time()
    while time.time() - t0 < 3000:
        time.sleep(10)
        try:
            hist = http_json(server + "/history/" + pid, timeout=15)
        except Exception:
            continue
        e = hist.get(pid)
        if e is None:
            print("[%s] %4ds running..." % (tag, time.time() - t0), flush=True)
            continue
        if e.get("status", {}).get("status_str") == "error":
            print("[%s] ERROR %s" % (tag, json.dumps(e["status"].get("messages", []))[:400]), flush=True)
            return False
        for nid, out in e["outputs"].items():
            vids = out.get("gifs", []) or out.get("videos", []) or out.get("images", [])
            for vid in vids:
                url = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                    server, vid["filename"], vid.get("subfolder", ""), vid.get("type", "output"))
                data = urllib.request.urlopen(url, timeout=300).read()
                dst = os.path.join(out_dir, tag + ".mp4")
                open(dst, "wb").write(data)
                print("[%s] SAVED %s (%.0fs, %dKB)" % (tag, dst, time.time() - t0, len(data) // 1024), flush=True)
                return True
        print("[%s] finished but no video output found" % tag, flush=True)
        return False
    print("[%s] TIMEOUT" % tag, flush=True)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="FluxGroup 仓库根（绝对路径）")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--out", default=None, help="产物目录（默认 <repo>/.../30s-reel-v1/fleet-shots/<主机名>）")
    ap.add_argument("--only", default="", help="逗号分隔的 tag 子集（调试用）")
    args = ap.parse_args()

    base = os.path.join(args.repo, "cph4", "fleet", "mv0001-handover", "outbound", "krea2", "30s-reel-v1")
    manifest = json.load(open(os.path.join(base, "local_h3_i2va_v4.json"), "r", encoding="utf-8"))
    wf_path = os.path.join(base, "h3_i2v_local_768p_v4.json")

    host = os.environ.get("COMPUTERNAME", "fleet-node")
    out_dir = args.out or os.path.join(base, "fleet-shots", host)
    os.makedirs(out_dir, exist_ok=True)

    only = set(x.strip() for x in args.only.split(",") if x.strip())
    ok, fail = 0, []
    for shot in manifest:
        if only and shot["tag"] not in only:
            continue
        frame = os.path.join(base, shot["frame"])
        if not os.path.isfile(frame):
            print("MISSING FRAME", frame, flush=True)
            fail.append(shot["tag"])
            continue
        r = run_shot(args.server, wf_path, out_dir, None, shot["tag"], frame,
                     shot["prompt"], shot["seed"], shot["length"], shot["width"], shot["height"])
        ok += 1 if r else 0
        if not r:
            fail.append(shot["tag"])
    print("FLEET BATCH DONE ok=%d fail=%s out=%s" % (ok, ",".join(fail) or "none", out_dir), flush=True)


if __name__ == "__main__":
    main()
