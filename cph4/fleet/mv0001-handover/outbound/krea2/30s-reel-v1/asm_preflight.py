# -*- coding: utf-8 -*-
# asm_preflight.py — V3 装配预检+全本地过闸探针
# 收编：O-20261014-1045 导演席严格律（原 tmp 清扫区孤本收编正典）
# 判据机械化：O-20261013-2200 CEO 全本地令「过闸判据=装配前 asm_preflight 云引用计数=0」
# 云族口径（从严）：CLOUD(cloudv2 归档) + D_OLD(cloud-v4 旧云波) 均计云引用——
#   成品=机队自产能力干净验证件，凡云产源一律入重产清单。
# 退出码：0=过闸（零云引用·零缺源）· 1=未过（云引用或缺源非零）
# 用法：python asm_preflight.py   （波2 待产清单=本探针 CLOUD-ONLY 段输出）
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ASM = os.path.join(HERE, "build_full_mv_v2.py")

spec = importlib.util.spec_from_file_location("bfm", ASM)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def resolve(fname):
    """按装配器同序解析（CLOUD→DL→D_OLD→FLUX）——如实反映 find_src 现行为"""
    for tag, d in (("CLOUD", m.CLOUD), ("DL", m.DL), ("D_OLD", m.D_OLD), ("FLUX", m.FLUX)):
        if os.path.isfile(os.path.join(d, fname)):
            return tag
    return None

def local_only(fname):
    """去掉云族（CLOUD+D_OLD）后能否解析——DL(bm-c 本地新产)+FLUX(本地 INT8 史)为本地族"""
    for tag, d in (("DL", m.DL), ("FLUX", m.FLUX)):
        if os.path.isfile(os.path.join(d, fname)):
            return tag
    return None

rows = m.build_rows()
resolved, missing, cloud_now, cloud_only = [], [], [], []
for r in rows:
    tag = resolve(r[4])
    if tag is None:
        missing.append(r[0])
        continue
    resolved.append((r[0], tag))
    if tag in ("CLOUD", "D_OLD"):
        cloud_now.append((r[0], tag))
        if local_only(r[4]) is None:
            cloud_only.append((r[0], tag))

print("TOTAL-ROWS %d (window sum %.2fs target %.2f)" % (
    len(rows), sum(r[2] - r[1] for r in rows), m.FILM_END))
print("RESOLVED %d  CLOUD=%d DL=%d D_OLD(cloud-v4)=%d FLUX=%d" % (
    len(resolved),
    sum(1 for _, t in resolved if t == "CLOUD"),
    sum(1 for _, t in resolved if t == "DL"),
    sum(1 for _, t in resolved if t == "D_OLD"),
    sum(1 for _, t in resolved if t == "FLUX")))
print("MISSING %d: %s" % (len(missing), " ".join(missing)))
print("CLOUD-FAMILY %d (当前解析在云族): %s" % (
    len(cloud_now), " ".join("%s(%s)" % (s, t) for s, t in cloud_now)))
print("CLOUD-ONLY %d (波2必产清单·去云族即缺源): %s" % (
    len(cloud_only), " ".join(s for s, _ in cloud_only)))
gate = (len(missing) == 0 and len(cloud_now) == 0)
print("GATE %s (missing=%d cloud-refs=%d)" % (
    "PASS" if gate else "FAIL", len(missing), len(cloud_now)))
sys.exit(0 if gate else 1)
