import io

P = r'K:\Fluxgroup\MiniGame\Design\configs\GLOBAL\档案\机队协作看板.md'

row = (
 "| C | 2026-10-24 | **C2191 KN17 768P 过线进片 + KN18 病根落到光块并修 + 整片 v2 重装出片**（17:00-17:05 tick·批次 C2191）"
 "｜**正在干**=KN18 关键帧重烧排队（光块已改 `galaxy_dust_cu`，待烧帧）"
 "｜**最近交付**=`media/mv-album-001-jay/assembly-packA-KN/KN-FULL-v1-C2183.mp4`（17:04 出·1344×768·239.0417s·5737 帧·含音轨·88.7MB）"
 "+ 收割档 `cph4/fleet/mv-album-001-jay/HARVEST-KN-GALAXY-c2190-r5.md`（KN17 p99 32/31/32 线 47·1:1 无竖条无硬撕边·帧 37/18 片比帧冷 1 点=模型忠实）"
 "+ 对照板 `qc-boards/KN-GALAXY-PROD-c2190.jpg`"
 "｜**下一步**=KN18 关键帧重烧（`kn_reroll_c2166.py --only KN18 --seed-offset 1`）→ 读 p99 对 KN17 锚 37/18 → 480P 探针（线 82）→ 进片重装 → 导演席拉片（窗 ≤48h） |"
)

raw = io.open(P, encoding='utf-8', newline='').read()
assert 'C2191 KN17 768P' not in raw, 'row already present'
lines = raw.split('\n')
# find last line that starts with '| C | 2026-10-24' and insert right after it
idx = None
for i, l in enumerate(lines):
    if l.startswith('| C | 2026-10-24 |'):
        idx = i
assert idx is not None
lines.insert(idx + 1, row)
out = '\n'.join(lines)
io.open(P, 'w', encoding='utf-8', newline='').write(out)
print('inserted after line', idx + 1, '| total lines', len(lines))