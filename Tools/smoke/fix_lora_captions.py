# -*- coding: utf-8 -*-
"""把资产库人脸集的 caption 重写成「触发词 + 设定档真身描述 + 视角」，供 krea2 LoRA 训练使用。

病灶（2026-11-15 实测）：`media/asset/faces/CH0x/*.txt` 是 VLM 自由描述，12 条里 9 条带
background/blurred/outdoors 这类**场景词**——LoRA 会把环境学进角色里，换场景就跟着脏；
而且首词各不相同（"Young Asian woman…" / "A young woman…"），没有可调用的触发词。

正法：真身描述一律取自正典设定表 `cph4/fleet/asset-lib-v1/CHARACTERS-EN-v1.json`
（region/role/face/hair/outfit 都是设计事实，不是模型猜的），视角词由文件名映射，
首词统一成 `<字符小写>face`（例：ch01face）。原 caption 备份到 `_caption-bak/`。

用法：
  python fix_lora_captions.py            # 全量重写 8 个角色
  python fix_lora_captions.py --chars CH01,CH02
  python fix_lora_captions.py --dry-run
"""
import argparse, json, os, shutil, sys

SPEC = r'K:\Fluxgroup\FluxGroup\cph4\fleet\asset-lib-v1\CHARACTERS-EN-v1.json'
ROOT = r'K:\Fluxgroup\FluxGroup\media\asset\faces'

VIEWS = {
    'front': 'front view',
    'profile_left': 'full left profile',
    'profile_right': 'full right profile',
    'three_quarter_left': 'three-quarter view turned to the left',
    'three_quarter_right': 'three-quarter view turned to the right',
    'back': 'back view with the face turned away',
    'high_angle': 'viewed from a high angle',
    'low_angle': 'viewed from a low angle',
    'mid_shot': 'medium shot, waist up',
    'expression_smile': 'front view with a slight smile',
    'expression_soft': 'front view with a calm soft expression',
    'expression_tense': 'front view with a tense tightened expression',
}


def caption(spec, view):
    return '%s, %s, %s, %s, %s, %s.' % (
        view['token'], spec.get('role', 'person').strip().rstrip('.'),
        spec.get('face', '').strip().rstrip('.'), spec.get('hair', '').strip().rstrip('.'),
        spec.get('outfit', '').strip().rstrip('.'), view['phrase'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', default=SPEC)
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--chars', default='')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    spec = json.load(open(a.spec, encoding='utf-8'))['characters']
    only = set(x.strip().upper() for x in a.chars.split(',') if x.strip())
    total = 0
    for ch in sorted(spec):
        if only and ch.upper() not in only:
            continue
        d = os.path.join(a.root, ch)
        if not os.path.isdir(d):
            print('SKIP %s (no dir)' % ch)
            continue
        token = ch.lower() + 'face'
        bak = os.path.join(d, '_caption-bak')
        if not a.dry_run:
            os.makedirs(bak, exist_ok=True)
        n = 0
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.png'):
                continue
            view = fn[:-4]
            phrase = VIEWS.get(view)
            if not phrase:
                print('  WARN %s/%s 视角未登记，保持原 caption' % (ch, fn))
                continue
            cap = caption(spec[ch], dict(token=token, phrase=phrase))
            txt = os.path.join(d, view + '.txt')
            if a.dry_run:
                print('[%s] %s' % (view, cap))
            else:
                if os.path.isfile(txt) and not os.path.isfile(os.path.join(bak, view + '.txt')):
                    shutil.copy2(txt, os.path.join(bak, view + '.txt'))
                with open(txt, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(cap + '\n')
            n += 1
        total += n
        print('%-5s token=%-10s captions=%d%s' % (ch, token, n, ' (dry-run)' if a.dry_run else ''))
    print('SUMMARY captions=%d' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main())
