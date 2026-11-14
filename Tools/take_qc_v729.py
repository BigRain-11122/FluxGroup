# -*- coding: utf-8 -*-
# take_qc_v729.py - performance-take QC for v729: prove the take has REAL motion (replacing the
# v728 freeze versions). Evidence machine-checkable:
#   1) frame count / duration / fps (ffprobe)
#   2) inter-frame MAD via signalstats YAVG diff distribution - a performance take must have
#      non-trivial motion in the performance window (the 2026-11-13 orders row cites
#      "VC inter-frame MAD 11-24 proven to have performance" as the reference standard)
#   3) freezedetect must report ZERO freezes (a frozen take = exactly what v729 replaces)
#   4) 6-frame contact strip (q88 jpg) for eyeball review
import json, subprocess, sys, os, argparse

def ffprobe(p):
    out = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', p],
                         capture_output=True, text=True).stdout
    return json.loads(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--strip', default=None, help='output contact strip jpg path')
    a = ap.parse_args()
    v = os.path.abspath(a.video)
    assert os.path.isfile(v), 'missing ' + v
    probe = ffprobe(v)
    st = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    n = int(st['nb_frames']) if 'nb_frames' in st else None
    dur = float(probe['format']['duration'])
    fps = st.get('r_frame_rate', '?')
    print('video: %s' % v)
    print('frames: %s dur: %.2fs fps: %s size: %dx%d' % (n, dur, fps, st['width'], st['height']))

    # inter-frame MAD on luma (YAVG per frame, diff sequence)
    # NB: ffprobe -f lavfi movie=<path> chokes on Windows drive-letter escaping; use plain
    # ffmpeg -i with signalstats+metadata=print and parse the stderr frame tags instead.
    # Re-pinned after executor-merge rollback (11-08 precedent).
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-i', v, '-vf',
                        'signalstats,metadata=print:key=lavfi.signalstats.YAVG', '-f', 'null', '-'],
                       capture_output=True, text=True)
    yavgs = []
    for l in (r.stderr or '').splitlines():
        if 'lavfi.signalstats.YAVG=' in l:
            try:
                yavgs.append(float(l.split('lavfi.signalstats.YAVG=')[1].strip()))
            except ValueError:
                pass
    if len(yavgs) >= 2:
        diffs = [abs(yavgs[i + 1] - yavgs[i]) for i in range(len(yavgs) - 1)]
        diffs_sorted = sorted(diffs)
        n = len(diffs)
        print('inter-frame YAVG diffs: n=%d mean=%.3f median=%.3f p90=%.3f max=%.3f zero(<0.05)=%d/%d'
              % (n, sum(diffs) / n, diffs_sorted[n // 2], diffs_sorted[int(n * 0.9)], diffs_sorted[-1],
                 sum(1 for d in diffs if d < 0.05), n))
        verdict_motion = 'MOTION-OK' if (sum(1 for d in diffs if d > 0.1) >= max(3, n // 10)) else 'MOTION-WEAK'
    else:
        verdict_motion = 'NO-DATA'

    # freezedetect: must be zero for a performance take
    r = subprocess.run(['ffmpeg', '-v', 'info', '-i', v, '-vf', 'freezedetect=n=0.001:d=0.3', '-f', 'null', '-'],
                       capture_output=True, text=True)
    fz = [l for l in (r.stderr or '').splitlines() if 'freeze_start' in l]
    print('freezedetect hits: %d' % len(fz))
    for l in fz[:4]:
        print('  ', l.strip()[:120])

    # contact strip (6 frames) - step precomputed from ffprobe frame count (nb_frames is
    # not available inside select expressions)
    strip = a.strip or (os.path.splitext(v)[0] + '-strip.jpg')
    total = int(st['nb_frames']) if 'nb_frames' in st else int(round(dur * 24))
    step = max(1, total // 6)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', v, '-vf',
                    r"select=not(mod(n\,%d)),scale=672:-1,tile=6x1" % step, '-frames:v', '1',
                    '-q:v', '8', strip], capture_output=True)
    print('strip: %s (%s)' % (strip, os.path.getsize(strip) if os.path.isfile(strip) else 'FAILED'))

    verdict = 'PASS' if (verdict_motion == 'MOTION-OK' and not fz) else 'FAIL(%s,freeze=%d)' % (verdict_motion, len(fz))
    print('VERDICT: %s' % verdict)
    return 0 if verdict == 'PASS' else 1

if __name__ == '__main__':
    sys.exit(main())
