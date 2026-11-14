# -*- coding: utf-8 -*-
# kf_e04_take_v729.py - v729 second nail: E04 replay-faces PERFORMANCE take (replaces v728 freeze version).
# Spec sources:
#   - docs/orders.md 2026-11-13 21:55 row: "E04 performance take ... replace v728 freeze version"
#   - ARTISTIC-UPGRADE-PLAN-v723 B10: memory-replay face montage, each face does ONE thing only,
#     no double expressions; performance beats (eye-lid single action fits), no literal sigh/breath on face
#     (2026-11-08 CEO literal-performance ban - breath only allowed on environment: torch flame breathes).
#   - KF: canon/kf-reburn-v723/E04_kf_blonde.png (v727 blonde priestess redesign: centre part + gold fillet
#     + kohl + snake armband, CEO 11-09 review fix)
#   - Camera: C2 inverse rule - strong performance -> locked-off static (no fake motion per CHARTER ban)
# Audio chain stripped in workflow (CEO audio-track ban). Timeline slot: E04_replay_faces 212.66-219.84s
# (7.18s) -> render 174 frames (7.25s @ 24fps, safe overshoot for trim).
import argparse, json, os, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WF = os.path.join(ROOT, 'cph4', 'fleet', 'mv0001-handover', 'outbound', 'krea2', '30s-reel-v1', 'h3_i2v_local_768p_v4.json')
KF = os.path.join(ROOT, 'cph4', 'fleet', 'mv0001-handover', 'canon', 'kf-reburn-v723', 'E04_kf_blonde.png')
OUT_DIR = os.path.join(ROOT, 'media', 'mv-album-001-jay', 'v729-clips')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'E04_replay_faces_v729.mp4')

PROMPT = ("A dark stone shrine interior lit by a single torch flame, one continuous take. "
          "The Babylonian high priestess in a white linen robe with a gold fillet, dark kohl-rimmed eyes "
          "and a snake armband faces the camera with a faint restrained smile. "
          "Her gaze holds the lens as her eyelids close in one slow deliberate blink, then lift again; "
          "after the blink her faint smile softens almost imperceptibly, "
          "while the torch flame breathes in a slow steady rhythm beside her. [locked-off static shot]. "
          "Warm amber monochrome grade, deep crushed shadows, shot on 35mm film with visible grain "
          "and halation on the flame, cinematic film still from a 2001 Taiwanese music video.")


def http_json(url, payload=None, timeout=60):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def upload_image(server, path):
    fn = os.path.basename(path)
    data = open(path, 'rb').read()
    boundary = '----e04v729' + uuid.uuid4().hex
    body = (('--%s\r\nContent-Disposition: form-data; name="image"; filename="%s"\r\n'
             'Content-Type: image/png\r\n\r\n') % (boundary, fn)).encode() + data + ('\r\n--%s--\r\n' % boundary).encode()
    req = urllib.request.Request(server + '/upload/image?overwrite=true', data=body,
                                 headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get('name', fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--server', default='http://127.0.0.1:8188')
    ap.add_argument('--seed', type=int, default=30972951, help='v729 seed segment for reproducibility')
    a = ap.parse_args()

    if os.path.isfile(OUT) and os.path.getsize(OUT) > 100000:
        print('SKIP: exists ->', OUT)
        return 0

    http_json(a.server + '/system_stats')  # alive check
    img = upload_image(a.server, KF)
    print('uploaded KF as', img)
    wf = json.load(open(WF, 'r', encoding='utf-8'))
    wf['16']['inputs']['image'] = img
    n6 = wf['6']['inputs']
    n6['prompt'] = PROMPT
    n6['length'] = 174
    n6['width'] = 1344
    n6['height'] = 768
    wf['10']['inputs']['noise_seed'] = a.seed

    pid = http_json(a.server + '/prompt', {'prompt': wf, 'client_id': str(uuid.uuid4())})['prompt_id']
    print('prompt_id', pid, 'seed', a.seed)
    t0 = time.time()
    while time.time() - t0 < 2400:
        time.sleep(10)
        try:
            h = http_json(a.server + '/history/' + pid, timeout=30)
        except Exception:
            continue
        if pid in h:
            if h[pid].get('status', {}).get('status_str') == 'error':
                print('ERROR:', json.dumps(h[pid]['status'].get('messages', []))[:500])
                return 1
            for nid, out in h[pid]['outputs'].items():
                for v in out.get('gifs', []) or out.get('videos', []) or out.get('images', []):
                    url = '%s/view?filename=%s&subfolder=%s&type=%s' % (
                        a.server, v['filename'], v.get('subfolder', ''), v.get('type', 'output'))
                    data = urllib.request.urlopen(url, timeout=300).read()
                    open(OUT, 'wb').write(data)
                    print('SAVED %s (%.0fs, %d bytes)' % (OUT, time.time() - t0, len(data)))
                    return 0
    print('TIMEOUT after 2400s')
    return 1


if __name__ == '__main__':
    sys.exit(main())
