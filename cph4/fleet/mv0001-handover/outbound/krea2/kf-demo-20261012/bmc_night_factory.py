# -*- coding: utf-8 -*-
# bmc_night_factory.py -- O-20261012-2305 CEO 明朝成片死线令 @bm-c i2v 夜产线
# Phase A: wait for wave A chain (v1.2 whitelist) to complete, upload clips -> CDN
# Phase B: 44-frame archive batch (mv_full_shots.NEW, t0 canonical order, INT8 768P)
#          each finished mp4 -> immediate CDN upload -> I2V-URL-INDEX.md row
# Phase C: whitelist re-scan for v1.3 additions (INT2/4/5 from bm-a), burn new entries
# Laws: 纯画面无音轨 (workflow audio chain stripped) · FIFO 共服不动他窗队列项 ·
#       resume-safe skip-if-exists · CEO 让路令=@bm-c 今晚唯一优先=i2v 产线.
import io, json, os, re, subprocess, sys, time, urllib.request, uuid

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
BMC = os.path.join(HERE, "bmc")
FRAMES = os.path.join(BMC, "i2v_frames")
I2V_OUT = os.path.join(BMC, "i2v")
ARCH_OUT = os.path.join(BMC, "archive_i2v")
INDEX = os.path.join(BMC, "I2V-URL-INDEX.md")
SERVER = "http://127.0.0.1:8188"
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
WF_768P = os.path.join(REPO_ROOT, "cph4", "fleet", "mv0001-handover", "outbound",
                       "krea2", "30s-reel-v1", "h3_i2v_local_768p_v4.json")
ARCH_FRAMES = r"K:\Fluxgroup\archive\mv0001-kf-frames-bmc-r840\frames_full"
SHOTS_MOD_DIR = os.path.join(REPO_ROOT, "cph4", "fleet", "mv0001-handover", "outbound",
                             "krea2", "30s-reel-v1")
MCP_DIR = os.path.join(REPO_ROOT, "quant", "bigmoney", ".codely-cli", "scratch", "meme_v1")
WAVE_CHAIN_PID_FILE = os.path.join(BMC, "wave_chain.pid")
for d in (BMC, I2V_OUT, ARCH_OUT):
    os.makedirs(d, exist_ok=True)

sys.path.insert(0, MCP_DIR)
import tj_mcp


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def http_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def upload_frame_image(path):
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    boundary = "----i2v" + uuid.uuid4().hex
    body = (("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
             "Content-Type: image/png\r\n\r\n") % (boundary, fn)).encode() + data + \
           ("\r\n--%s--\r\n" % boundary).encode()
    req = urllib.request.Request(SERVER + "/upload/image?overwrite=true", data=body,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get("name", fn)


def run_i2v(frame_path, prompt, seed, out_mp4, tag, poll_timeout=3000):
    if os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 500000:
        log("[%s] SKIP (exists)" % tag)
        return True
    img = upload_frame_image(frame_path)
    wf = json.load(open(WF_768P, encoding="utf-8"))
    wf["16"]["inputs"]["image"] = img
    n6 = wf["6"]["inputs"]
    n6["prompt"] = prompt
    n6["length"] = 124
    n6["width"] = 1344
    n6["height"] = 768
    wf["10"]["inputs"]["noise_seed"] = seed
    pid = http_json(SERVER + "/prompt", {"prompt": wf, "client_id": "bmc-night-factory"})["prompt_id"]
    log("[%s] SUBMITTED frame=%s seed=%d" % (tag, img, seed))
    t0 = time.time()
    while time.time() - t0 < poll_timeout:
        time.sleep(15)
        try:
            hist = http_json(SERVER + "/history/" + pid, timeout=20)
        except Exception:
            continue
        e = hist.get(pid)
        if e is None:
            log("[%s] %4ds running..." % (tag, time.time() - t0))
            continue
        if e.get("status", {}).get("status_str") == "error":
            log("[%s] ERROR %s" % (tag, json.dumps(e["status"].get("messages", []))[:300]))
            return False
        for nid, out in e["outputs"].items():
            vids = out.get("gifs", []) or out.get("videos", []) or out.get("images", [])
            for vid in vids:
                u = "%s/view?filename=%s&subfolder=%s&type=%s" % (
                    SERVER, vid["filename"], vid.get("subfolder", ""), vid.get("type", "output"))
                data = urllib.request.urlopen(u, timeout=300).read()
                open(out_mp4, "wb").write(data)
                log("[%s] SAVED %s (%.1fs)" % (tag, os.path.basename(out_mp4), time.time() - t0))
                return True
        return False
    log("[%s] TIMEOUT" % tag)
    return False


def index_tags():
    if not os.path.isfile(INDEX):
        return set()
    t = io.open(INDEX, encoding="utf-8").read()
    return set(re.findall(r"\| (\S+) \|", t))


def cdn_upload(path, tag):
    """file_upload -> PUT bytes -> verify 200 -> append index row. Returns file_url or None."""
    if tag in index_tags():
        log("[%s] INDEX SKIP (already)" % tag)
        return None
    if not getattr(tj_mcp, "session_id", None):
        tj_mcp.initialize()
    for attempt in (1, 2):
        try:
            res = tj_mcp.call_tool("file_upload", {"file_path": path}, timeout=120)
        except Exception as ex:
            log("[%s] file_upload FAIL attempt%d: %r" % (tag, attempt, ex))
            if "session" in str(ex).lower():
                tj_mcp.session_id = None
                try:
                    tj_mcp.initialize()
                except Exception:
                    pass
            time.sleep(3)
            continue
        rec = None
        for c in res.get("content", []):
            if c.get("type") == "resource":
                try:
                    rec = json.loads(c["resource"]["text"])
                except Exception:
                    rec = None
        if not rec or not rec.get("upload_url"):
            log("[%s] file_upload no upload_url (attempt%d): %s" % (tag, attempt, json.dumps(res)[:200]))
            time.sleep(3)
            continue
        if rec.get("already_uploaded") and rec.get("file_url"):
            furl = rec["file_url"]
        else:
            req = urllib.request.Request(rec["upload_url"], data=open(path, "rb").read(),
                                         headers={"Content-Type": "application/octet-stream"}, method="PUT")
            with urllib.request.urlopen(req, timeout=300) as r:
                code = r.status
            if code != 200:
                log("[%s] PUT attempt%d code=%d -- retry ticket" % (tag, attempt, code))
                time.sleep(2)
                continue
            furl = rec["file_url"]
        with open(INDEX, "a", encoding="utf-8") as f:
            f.write("| %s | %.1fMB | %s |\n" % (tag, os.path.getsize(path) / 1048576.0, furl))
        log("[%s] CDN UPLOADED %s" % (tag, furl))
        return furl
    log("[%s] CDN UPLOAD FAILED after retries" % tag)
    return None


def parse_whitelist():
    t = io.open(os.path.join(HERE, "FRAME-GATE-WHITELIST-v1.md"), encoding="utf-8").read()
    pm, urls = {}, {}
    for m in re.finditer(r"^(\d)\. \*\*([A-Za-z0-9_v]+)\*\*：(.+)$", t, re.M):
        pm[m.group(1)] = m.group(3).strip()
    for m in re.finditer(r"^(\d)\. (\S+) → (\S+\.png)$", t, re.M):
        urls[m.group(1)] = (m.group(2), m.group(3))
    return pm, urls


def phase_wait_wave_a(chain_pid):
    log("PHASE A: waiting for wave A chain PID %d" % chain_pid)
    while True:
        alive = subprocess.run(["tasklist", "/FI", "PID eq %d" % chain_pid],
                               capture_output=True, text=True).stdout
        if str(chain_pid) not in alive:
            log("PHASE A: chain exited")
            break
        # opportunistic: upload any already-finished wave A clips
        for fn in sorted(os.listdir(I2V_OUT)):
            if fn.endswith(".mp4"):
                cdn_upload(os.path.join(I2V_OUT, fn), os.path.splitext(fn)[0])
        time.sleep(60)
    for fn in sorted(os.listdir(I2V_OUT)):
        if fn.endswith(".mp4"):
            cdn_upload(os.path.join(I2V_OUT, fn), os.path.splitext(fn)[0])
    log("PHASE A DONE (wave A uploads flushed)")


# O-20261012-2330 CLOUDWAVE-1 OK skip order (23:5x): whitelist 8 + museum INT1-5
# (书房线替代) + C01 archive (cloud KF3v3) + wave-2 D/B/E/Z 17 all cloud-produced
# or replaced -> bm-c local 正身 = N01-N07 + C02-C09 + R01-R06 (21 shots) only.
MANDATED = set(
    "N01_war_relief N02_crowd_her N03_goddess_pass N04_river_marks N05_dead_language "
    "N06_poem_light N07_fire_breath C02_sand_bury C03_dig_reveal C04_words_alive "
    "C05_flame_gap C06_forever_cut C07_stele_sink C08_strike_burst C09_oath_weather "
    "R01_war_later R02_she_turns R03_goddess_dim R04_river_dry R05_gold_threads "
    "R06_museum_verse".split())


def phase_b_archive():
    sys.path.insert(0, SHOTS_MOD_DIR)
    import mv_full_shots as mfs
    shots = [s for s in mfs.NEW if s[0] in MANDATED]
    log("PHASE B: mandated subset %d/%d shots (skip museum INT1-5/C01/wave2-17 per O-2330 CLOUDWAVE-1)"
        % (len(shots), len(mfs.NEW)))
    missing = []
    for idx, s in enumerate(shots):
        sid, t0, t1, speed = s[0], s[1], s[2], s[3]
        prompt = s[5]
        frame = os.path.join(ARCH_FRAMES, sid + ".png")
        if not os.path.isfile(frame):
            missing.append(sid)
            log("[%s] FRAME MISSING -- skipped (disclosed)" % sid)
            continue
        out = os.path.join(ARCH_OUT, sid + ".mp4")
        ok = run_i2v(frame, prompt, 9100 + idx, out, sid)
        if ok:
            cdn_upload(out, sid)
    log("PHASE B DONE (missing frames: %s)" % (missing or "none"))


def phase_c_whitelist_watch(until_h=5, until_m=30):
    log("PHASE C: whitelist v1.3 watch until %02d:%02d" % (until_h, until_m))
    last_seen = set()
    while True:
        now = time.localtime()
        if (now.tm_hour, now.tm_min) >= (until_h, until_m):
            log("PHASE C: watch window closed")
            break
        try:
            pm, urls = parse_whitelist()
        except Exception as ex:
            log("PHASE C: whitelist parse FAIL %r" % ex)
            time.sleep(120)
            continue
        for i in sorted(urls):
            tag, url = urls[i]
            if tag in last_seen:
                continue
            out = os.path.join(I2V_OUT, tag + ".mp4")
            if os.path.isfile(out) and os.path.getsize(out) > 500000:
                cdn_upload(out, tag)
                last_seen.add(tag)
                continue
            frame = os.path.join(FRAMES, tag + ".png")
            if not (os.path.isfile(frame) and os.path.getsize(frame) > 100000):
                log("[%s] downloading frame..." % tag)
                try:
                    data = urllib.request.urlopen(url, timeout=120).read()
                    open(frame, "wb").write(data)
                except Exception as ex:
                    log("[%s] frame download FAIL %r" % (tag, ex))
                    continue
            ok = run_i2v(frame, pm[i], 9021 + int(i), out, tag)
            if ok:
                cdn_upload(out, tag)
                last_seen.add(tag)
        time.sleep(120)


if __name__ == "__main__":
    chain_pid = 0
    if os.path.isfile(WAVE_CHAIN_PID_FILE):
        chain_pid = int(io.open(WAVE_CHAIN_PID_FILE).read().strip())
    if chain_pid:
        phase_wait_wave_a(chain_pid)
    phase_b_archive()
    phase_c_whitelist_watch()
    log("NIGHT FACTORY COMPLETE -- all phases done")
