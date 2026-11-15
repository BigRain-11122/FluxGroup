# -*- coding: utf-8 -*-
"""Krea2 角色 LoRA 三步驱动：缓存 latent → 缓存文本编码 → 训练（16GB 卡口径）。

为什么要有这个脚本而不是手敲三条命令：
  1. PYTHONPATH / 解释器 / 日志重定向每次手敲都会漏（musubi 装在 .tools/lora-venv，
     源码在 .tools/vendor/musubi-tuner-main/src，用别的解释器一跑就 ImportError）；
  2. 三步的显存/内存口径不同（缓存要 VAE 或 TE 单独占卡，训练要 fp8 + block swap），
     一次跑完中间失败也方便重来（缓存步都支持 --skip_existing）；
  3. 长跑必须脱离会话（会话一断 GPU 批就死），所以默认写日志到文件、可后台。

用法：
  python run_krea2_lora.py --step all                 # 三步连跑
  python run_krea2_lora.py --step cache|te|train      # 单步
  可选：--dataset <toml> --dit <bf16 raw> --vae <vae> --te <qwen3vl bf16> --out <dir>
        --max-epochs 10 --blocks-swap 26 --dim 32

显存口径（bm-c RTX 3070 16GB）：--fp8_base --fp8_scaled 让 28 个主 block 权重按 fp8 常驻，
配合 --blocks_to_swap 把多余 block 放 CPU（fp8 下每块约 0.45GB），再开 gradient_checkpointing。
没有 --fp8_scaled 单独用 --fp8_base 会被训练器直接拒绝（会把 norm 也转 fp8 把模型搞坏）。
"""
import argparse, os, subprocess, sys, time

PY = r'K:\Fluxgroup\.tools\lora-venv\Scripts\python.exe'
SRC = r'K:\Fluxgroup\.tools\vendor\musubi-tuner-main\src'
MODELS = r'K:\Fluxgroup\.tools\models\krea2'


def run(mod, args, log):
    cmd = [PY, '-m', 'musubi_tuner.' + mod] + args
    env = dict(os.environ, PYTHONPATH=SRC, PYTHONUNBUFFERED='1')
    print('>> %s %s' % (mod, ' '.join(args)), flush=True)
    t0 = time.time()
    with open(log, 'a', encoding='utf-8') as lf:
        lf.write('\n===== %s @ %s =====\n%s\n' % (mod, time.strftime('%Y-%m-%d %H:%M:%S'),
                                                 ' '.join(cmd)))
        lf.flush()
        p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             cwd=os.path.dirname(SRC.rstrip('\\')).rstrip('\\') or None)
        for raw in p.stdout:
            line = raw.decode('utf-8', 'replace')
            lf.write(line)
            lf.flush()
            s = line.rstrip()
            if s and any(k in s for k in ('steps:', 'epoch', 'Error', 'error', 'Traceback',
                                          'saving', 'model saved', 'caching', 'loaded')):
                print('   ' + s[-180:], flush=True)
        rc = p.wait()
    print('<< %s rc=%d (%.0fs)' % (mod, rc, time.time() - t0), flush=True)
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--step', default='all', choices=['all', 'cache', 'te', 'train'])
    ap.add_argument('--dataset', default=r'K:\Fluxgroup\FluxGroup\cph4\fleet\mv0001-handover\plan\cast-lora-dataset.toml')
    ap.add_argument('--dit', default=os.path.join(MODELS, 'krea2_raw_bf16.safetensors'))
    ap.add_argument('--vae', default=r'D:\ComfyUI\ComfyUI\models\vae\qwen_image_vae.safetensors')
    ap.add_argument('--te', default=os.path.join(MODELS, 'qwen3vl_4b_bf16.safetensors'))
    ap.add_argument('--out', default=r'K:\Fluxgroup\FluxGroup\media\mv0001-handover\lora-out')
    ap.add_argument('--name', default='xq_cast_v1')
    ap.add_argument('--log', default=r'K:\Fluxgroup\FluxGroup\media\mv0001-handover\lora-out\run.log')
    ap.add_argument('--dim', type=int, default=32)
    ap.add_argument('--alpha', type=int, default=32)
    ap.add_argument('--lr', default='1e-4')
    ap.add_argument('--max-epochs', type=int, default=10)
    ap.add_argument('--blocks-swap', type=int, default=26)
    ap.add_argument('--save-every', type=int, default=2)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    os.makedirs(os.path.dirname(a.log), exist_ok=True)
    for p, what in ((a.dataset, 'dataset toml'), (a.dit, 'DiT bf16'), (a.vae, 'VAE'), (a.te, 'text encoder')):
        if not os.path.isfile(p):
            print('MISSING %s: %s' % (what, p))
            return 2

    if a.step in ('all', 'cache'):
        rc = run('krea2_cache_latents',
                 ['--dataset_config', a.dataset, '--vae', a.vae,
                  '--batch_size', '1', '--skip_existing'], a.log)
        if rc:
            return rc
    if a.step in ('all', 'te'):
        rc = run('krea2_cache_text_encoder_outputs',
                 ['--dataset_config', a.dataset, '--text_encoder', a.te,
                  '--batch_size', '1', '--skip_existing'], a.log)
        if rc:
            return rc
    if a.step in ('all', 'train'):
        args = ['--dit', a.dit, '--vae', a.vae, '--dataset_config', a.dataset,
                '--sdpa', '--mixed_precision', 'bf16',
                '--timestep_sampling', 'krea2_shift', '--weighting_scheme', 'none',
                '--optimizer_type', 'AdamW', '--learning_rate', a.lr,
                '--gradient_checkpointing',
                '--max_data_loader_n_workers', '2', '--persistent_data_loader_workers',
                '--network_module', 'networks.lora_krea2',
                '--network_dim', str(a.dim), '--network_alpha', str(a.alpha),
                '--max_train_epochs', str(a.max_epochs),
                '--save_every_n_epochs', str(a.save_every),
                '--seed', '42', '--output_dir', a.out, '--output_name', a.name,
                '--fp8_base', '--fp8_scaled']
        if a.blocks_swap > 0:
            args += ['--blocks_to_swap', str(a.blocks_swap)]
        rc = run('krea2_train_network', args, a.log)
        if rc:
            return rc
    print('DONE -> %s' % a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
