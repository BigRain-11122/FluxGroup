# -*- coding: utf-8 -*-
"""drama-001 EP001-003 pilot voicegen (r998) -- multi-speaker batch, ONE model load.

Reuses the proven infer pattern from E:\\Fluxgroup\\.codely-cli\\drama_voicegen.py (v1.1,
runbook R-20261016-drama-sfx-tts-deploy-01.md B.4 route 3: Python API, use_qwen_emo=False
on the 8GB card). Extends it: per-speaker zero-shot ref + 8-dim emotion table, single
IndexTTS2 constructor for all 51 lines (vs 8 reloads = ~4 min saved).

Pilot casting (PILOT-001-PLAN: formal voice lib NOT built -> zero-shot refs):
  narr  旁白        -> examples/voice_05.wav (153Hz male doc-narrator, boot-smoke proven) + calm vec
  长    protagonist -> examples/voice_12.wav (131Hz male, neutral)
  熊/熊伟 villain    -> examples/voice_07.wav (true F0 ~98Hz male, stern; family share timbre)
  满仓  comic       -> examples/voice_05.wav + happy 0.6 (timbre shared w/ narrator, emo-separated)
  红利  reporter F  -> examples/voice_04.wav (262Hz female professional, cases.jsonl ZH case)
  父    father      -> examples/voice_07.wav
  散户群/散户甲     -> examples/voice_05.wav + happy 0.5
  经纪（画外）      -> examples/voice_05.wav mode0
Combined speaker lines resolve to main character (长 > 熊伟/熊 > first listed).

Output: C:\\Fluxgroup\\FluxGroup\\media\\drama-tts-out\\r998_ep001_003\\<EP>\\epXXX_lineNN.wav
        + MANIFEST-r998.json (line->file/speaker/ref/emo/dur) -- mixing-stage input face.
Log:   media\\drama-tools\\voicegen_r998.log  (pythonw: stdout is None, file-log only)
DONE:  media\\drama-tools\\voicegen_r998.DONE.json (status/counts/rtf) -- successor harvest face.
"""
import io, json, os, sys, time, traceback

REPO = r'C:\Fluxgroup\FluxGroup\media\drama-tools\repos\index-tts'
EPS_DIR = r'C:\Fluxgroup\FluxGroup\cph4\fleet\drama-001-stockera\episodes'
OUT_BASE = r'C:\Fluxgroup\FluxGroup\media\drama-tts-out\r998_ep001_003'
LOG = r'C:\Fluxgroup\FluxGroup\media\drama-tools\voicegen_r998.log'
DONE = r'C:\Fluxgroup\FluxGroup\media\drama-tools\voicegen_r998.DONE.json'
EPS = ['EP001', 'EP002', 'EP003']

EX = os.path.join(REPO, 'examples')
CALM = [0, 0, 0, 0, 0, 0, 0, 0.5625]
HAPPY5 = [0.5, 0, 0, 0, 0, 0, 0, 0]
HAPPY6 = [0.6, 0, 0, 0, 0, 0, 0, 0]


def logf(msg):
    try:
        with io.open(LOG, 'a', encoding='utf-8') as f:
            f.write('[%s] %s\n' % (time.strftime('%m-%d %H:%M:%S'), msg))
    except Exception:
        pass


PREFIX_RE = None
QUOTE_CHARS = u"\"\u201c\u201d\u300c\u300d\u300e\u300f'\u2018\u2019"


def clean_sub(text):
    """Strip speaker labels / stage notes / quote marks before synthesis.

    44% of the 1081 dialogue lines carry a '旁白（长虹）：' style prefix in the
    script JSON; feeding it to IndexTTS makes the narrator literally read the
    label aloud and inflates the take well past its shot slot.
    """
    global PREFIX_RE
    if PREFIX_RE is None:
        import re as _re
        PREFIX_RE = _re.compile(u"^[^\\uff1a:\"]{1,14}[\\uff1a:]\\s*")
    t = (text or "").strip()
    t = PREFIX_RE.sub("", t)
    t = "".join(ch for ch in t if ch not in QUOTE_CHARS)
    return t.strip()


def duration_factor_for(text, slot):
    """Pick a speaking-rate factor so the take fits its shot slot.

    Natural pace measured in this pipeline: ~4.5 CJK chars/second. If the line
    would overrun the slot by >10%, compress; never below 0.75 (audible rushing).
    """
    n = len([ch for ch in text if u"\u4e00" <= ch <= u"\u9fff"])
    if n <= 0:
        return 1.0
    pred = n / 4.5
    if pred <= slot * 1.1:
        return 1.0
    return max(0.65, round(slot * 1.1 / pred, 3))


def resolve(spk):
    """speaker string -> (ref_path, emo_vec_or_None, cast_note)"""
    table = [
        ('旁白', 'voice_05.wav', CALM, 'narr calm'),
        ('长', 'voice_12.wav', None, 'protagonist'),
        ('熊伟', 'voice_07.wav', None, 'villain-son'),
        ('熊', 'voice_07.wav', None, 'villain'),
        ('满仓', 'voice_05.wav', HAPPY6, 'comic happy6'),
        ('红利', 'voice_04.wav', None, 'reporter female'),
        ('父', 'voice_07.wav', None, 'father'),
        ('散户', 'voice_05.wav', HAPPY5, 'crowd happy5'),
        ('经纪', 'voice_05.wav', None, 'broker voi'),
        ('门卫', 'voice_12.wav', None, 'gatekeeper'),
    ]
    for key, ref, emo, note in table:
        if key in spk:
            return os.path.join(EX, ref), emo, '%s->%s' % (key, note)
    return os.path.join(EX, 'voice_05.wav'), None, 'fallback->narr mode0'


def main():
    t_start = time.time()
    info = {'status': 'FAIL', 'lines_total': 0, 'lines_ok': 0, 'eps': {}, 'cast_note': __doc__.split('Pilot casting')[1][:600] if 'Pilot casting' in __doc__ else ''}
    logf('RUNNER start r998 EP001-003 pilot voicegen (multi-speaker, single load)')
    try:
        os.chdir(REPO)
        sys.path.insert(0, REPO)
        model_dir = os.path.join(REPO, 'checkpoints')
        cfg_path = os.path.join(model_dir, 'config.yaml')
        from indextts.utils.model_download import ensure_config_available, ensure_models_available
        if not os.path.isfile(cfg_path):
            ensure_config_available(model_dir, version='2.5')
        ensure_models_available(model_dir)
        import torch
        from indextts.infer_v2_5 import IndexTTS2
        t0 = time.time()
        tts = IndexTTS2(cfg_path=cfg_path, model_dir=model_dir,
                        use_bf16=True, use_qwen_emo=False, use_cuda_kernel=False)
        load_s = time.time() - t0
        logf('MODEL loaded %.1fs bf16=%s low_vram=%s' % (load_s, tts.use_bf16, tts.low_vram))
        info['load_s'] = round(load_s, 1)

        try:
            import soundfile as sf
        except ImportError:
            sf = None

        manifest = []
        for ep in EPS:
            ep_path = os.path.join(EPS_DIR, ep + '.json')
            d = json.load(io.open(ep_path, encoding='utf-8'))
            ep_out = os.path.join(OUT_BASE, ep)
            os.makedirs(ep_out, exist_ok=True)
            ep_ok = 0
            for s in d['shots']:
                spk, sub = s.get('speaker') or '', s.get('sub') or ''
                if not spk or not sub:
                    continue
                info['lines_total'] += 1
                ref, emo, note = resolve(spk)
                sub = clean_sub(sub)
                name = 'ep%s_line%02d' % (ep[-3:], s['n'])
                out_path = os.path.join(ep_out, name + '.wav')
                tg = time.time()
                factor = duration_factor_for(sub, float(s.get('dur') or 3.0))
                try:
                    tts.infer(ref, sub, out_path, 'zhen',
                              emo_vector=emo, use_random=False, verbose=False,
                              duration_factor=factor)
                except Exception as e:
                    logf('LINE_FAIL %s %s: %r' % (name, spk, e))
                    manifest.append({'ep': ep, 'n': s['n'], 'name': name, 'speaker': spk,
                                     'text': sub, 'file': out_path, 'ok': False, 'err': repr(e)[:300],
                                     'ref': os.path.basename(ref), 'cast': note})
                    continue
                gen_s = time.time() - tg
                audio_s = 0.0
                if os.path.isfile(out_path):
                    if sf is not None:
                        audio_s = sf.info(out_path).duration
                    else:
                        import wave
                        with wave.open(out_path) as w:
                            audio_s = w.getnframes() / float(w.getframerate())
                ok = os.path.isfile(out_path) and os.path.getsize(out_path) > 8000
                if ok:
                    ep_ok += 1
                    info['lines_ok'] += 1
                logf('VOICEGEN_OK %s spk=%s cast=%s audio_s=%.2f gen_s=%.2f rtf=%.3f ok=%s'
                     % (name, spk, note, audio_s, gen_s, (gen_s / audio_s if audio_s > 0 else -1), ok))
                manifest.append({'ep': ep, 'n': s['n'], 'name': name, 'speaker': spk,
                                 'text': sub, 'file': out_path, 'ok': ok,
                                 'audio_s': round(audio_s, 2), 'gen_s': round(gen_s, 2),
                                 'shot_dur': s.get('dur'), 'fx': s.get('fx'),
                                 'ref': os.path.basename(ref), 'cast': note})
            info['eps'][ep] = {'title': d.get('title'), 'ok': ep_ok}
            logf('EP_DONE %s ok=%d' % (ep, ep_ok))

        with io.open(os.path.join(OUT_BASE, 'MANIFEST-r998.json'), 'w', encoding='utf-8') as f:
            json.dump({'generated': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
                       'eps': EPS, 'lines': manifest}, f, ensure_ascii=False, indent=1)
        info['status'] = 'OK' if info['lines_ok'] == info['lines_total'] else 'PARTIAL'
        info['elapsed_s'] = round(time.time() - t_start, 1)
        logf('RUNNER done status=%s ok=%d/%d elapsed=%.0fs'
             % (info['status'], info['lines_ok'], info['lines_total'], info['elapsed_s']))
    except SystemExit:
        raise
    except Exception:
        info['fatal'] = traceback.format_exc()[-2500:]
        logf('RUNNER FATAL: ' + info['fatal'].replace('\n', ' | '))
    finally:
        try:
            with io.open(DONE, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=True, indent=1)
        except Exception:
            pass


if __name__ == '__main__':
    main()
