import io

p = r'K:\Fluxgroup\MiniGame\.codely-cli\engine-tick\tick-ledger.txt'
anchor = b'2026-10-24 16:41:32 | tick-spawn 20261024-164132 | GATESIT_SPAWN step0-flag | out=none\r\n'
rows = [
    "[2026-10-24 17:05] [Step0 完成] C2191 开工自检=Step0Preflight 全 PASS 唯一 FLAG=WAVE-PENDING（C2190 KN17 768P 在飞·age 0.1h）→本轮定性为收割轮；state 解析 OK·无 redline·无 claims",
    "[2026-10-24 17:05] [Step1-3 完成] 情报/扫描：KN 段仍卡在银河两镜（正式片 v2 等 KN17）；KN18 病灶复核=光块错挂（galaxy_gold 是远景银河带描述，挂 85mm 特写必读成琥珀星云团）；门禁 kn_prompt_hygiene_gate --shots = fail 0 warn 3（3 条为本轮未触的运镜用词旧警）",
    "[2026-10-24 17:05] [Step4-5 完成] 收割 C2190：log 读到 CHAIN DONE（1587s / 2531KB / 260 帧 1344x768）；c2190_kn_harvest.py 三原生帧 + 1:1 天区条 → p99 32/31/32（线 47）= 历来最冷；1:1 无纵条碎片无硬撕边；关键帧 37/18 → 片比帧冷 1 点=模型忠实不添光 → 直升 KN_A-KN17.mp4（2591996B）",
    "[2026-10-24 17:05] [Step4-5 完成] KN18 提示词手术（2e773bcf）：新增特写专用光块 galaxy_dust_cu（零 band 零 thick dust·均匀圆点+干净暗底）+KN18 KF 词面改挂该块·changelog v3.1；--dry-run 解析 seed=40200018 jman=False（手术对烧帧生效）",
    "[2026-10-24 17:05] [Step6-7 完成] 收口：HARVEST-KN-GALAXY-c2190-r5.md + qc-frames-c2190（3 帧+1 条）+ 看板 KN-GALAXY-PROD-c2190.jpg + kn-harvest-c2190.json；片 v2 装配已脱手开火（c2190e_kn_full_assembly_launch.py·pid 44332·41 windows/239.03s·KN-FULL-v1-C2183.mp4）·wave flag 改写指向该编码产物",
    "[2026-10-24 17:05] C2191 TICK_DONE product=KN17 768P 通过质检并进片（p99 32/31/32·几何干净·帧片一致）+KN18 病根落到光块并已修（特写专用 galaxy_dust_cu）+片 v2 全片重装开火 | batch C2191 | next = 收割 KN-FULL-v1-C2183.mp4（时长/帧点抽检/银河段 109-117.46s 读感）→ KN18 关键帧重烧（--only KN18）→ 480P 探针 → 导演席拉片",
    "[2026-10-24 17:05] TICK_DONE C2191",
]

raw = open(p, 'rb').read()
assert raw.count(anchor) == 1, raw.count(anchor)
add = b''.join((r + '\r\n').encode('utf-8') for r in rows)
with open(p, 'wb') as fh:
    fh.write(raw + add)
print('appended', len(add), 'bytes')
print(open(p, 'rb').read()[-200:].decode('utf-8', 'replace'))