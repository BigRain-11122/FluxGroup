# -*- coding: utf-8 -*-
# kf_d03b_take_v729.py - v729: D03b direct-gaze PERFORMANCE take from the machine-best candidate frame.
# Slot: D03b_direct_gaze 150.54-152.00s (1.46s) -> render 39 frames (1.625s @24fps grid 17k+5, k=2), trim on assembly.
# KF choice: NOT waiting for CEO pick per 2026-10-25 CEO order ("don't wait - wrong beats empty"):
#   r3-lora c4 (seed 30972904, machine review 85/100, jaw-bone 9/10, zero disqualifiers) is the working pick;
#   all four candidates + LOOKBOARD remain on file for CEO final review (D03b-JMAN-CANDIDATES-REVIEW-20261113.md).
# Performance spec: v723 B5 intent "to say it without saying it" COMPLIANT with the 2026-11-08 literal-performance
#   ban (no breath-on-face literalization): torch flame breathes FIRST (environment carries the breath), then his
#   eyes lift into a direct gaze - eyes leading a half-beat before the head; lips relax closed. One thing only.
# Audio chain stripped (CEO audio ban). Locked-off shot (C2 inverse rule: strong beat -> still camera).
import argparse, json, os, sys, time, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WF = os.path.join(ROOT, 'cph4', 'fleet', 'mv0001-handover', 'outbound', 'krea2', '30s-reel-v1', 'h3_i2v_local_768p_v4.json')
KF = os.path.join(ROOT, 'media', 'mv-album-001-jay', 'v729-candidates', 'r3-lora', 'D03b_jman_c4_seed30972904.png')
OUT_DIR = os.path.join(ROOT, 'media', 'mv-album-001-jay', 'v729-clips')
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, 'D03b_direct_gaze_v729.mp4')

PROMPT = ("A dark basalt temple wall with carved cuneiform wedges and seated god reliefs, one continuous take. "
          "The young stone carver in a rough undyed linen tunic faces the camera in a near close-up, "
          "lit by a hard amber torch flame from the upper right. "
          "The torch flame breathes once, and after the flame settles his heavy-lidded eyes lift into a direct "
          "gaze at the lens, the eyes leading a half-beat before the head, "
          "as the flame steadies. [locked-off static shot]. "
          # take-3 root-cause fix (two-burn law, CHARTER sec.6): the KF frame itself is
          # SLIGHTLY-OPEN at the lips (measured). Any "closed lips" instruction turns that
          # static rest position into an ACTION (open->close) = extra movement = fail.
          # Take-1 (lips relax closed) and take-2 (lips staying closed) both produced exactly
          # that lip transition. Fix = ZERO lip/jaw wording: the mouth keeps the KF rest
          # position unchanged (not an action); only eyes + flame are described.
          "Warm amber monochrome grade, deep crushed shadows, shot on 35mm film with visible grain "
          "and halation on the flame, cinematic film still from a 2001 Taiwanese music video.")


def http_json(url, payload=None, timeout=60):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def upload_image(server, path):
    fn = os.path.basename(path)
    data = open(path, 'rb').read()
    boundary = '----d03bv729' + uuid.uuid4().hex
    body = (('--%s\r\nContent-Disposition: form-data; name="image"; filename="%s"\r\n'
             'Content-Type: image/png\r\n\r\n') % (boundary, fn)).encode() + data + ('\r\n--%s--\r\n' % boundary).encode()
    req = urllib.request.Request(server + '/upload/image?overwrite=true', data=body,
                                 headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=180).read()).get('name', fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--server', default='http://127.0.0.1:8188')
    ap.add_argument('--seed', type=int, default=30972952)
    a = ap.parse_args()

    if not os.path.isfile(KF):
        print('KF MISSING:', KF)
        return 2
    if os.path.isfile(OUT) and os.path.getsize(OUT) > 100000:
        print('SKIP: exists ->', OUT)
        return 0

    http_json(a.server + '/system_stats')
    img = upload_image(a.server, KF)
    print('uploaded KF as', img)
    wf = json.load(open(WF, 'r', encoding='utf-8'))
    wf['16']['inputs']['image'] = img
    n6 = wf['6']['inputs']
    n6['prompt'] = PROMPT
    n6['length'] = 39
    n6['width'] = 1344
    n6['height'] = 768
    wf['10']['inputs']['noise_seed'] = a.seed

    pid = http_json(a.server + '/prompt', {'prompt': wf, 'client_id': str(uuid.uuid4())})['prompt_id']
    print('prompt_id', pid, 'seed', a.seed)
    t0 = time.time()
    while time.time() - t0 < 1800:
        time.sleep(8)
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
    print('TIMEOUT after 1800s')
    return 1


if __name__ == '__main__':
    sys.exit(main())
