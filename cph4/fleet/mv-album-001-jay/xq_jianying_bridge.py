# -*- coding: utf-8 -*-
# xq_jianying_bridge.py - 星晴 shotlist → 剪映草稿粗剪桥（GitHub 收获落地件·pyJianYingDraft·CEO 令 10-11 23:1x「尽快落地」）
# 用法: python xq_jianying_bridge.py [--repo <FluxGroup根>] [--pylibs K:\Fluxgroup\.tools\pylibs]
# 语义: 窗口/变速/重演游标从 shots py 直读（零手抄）·缺片跳过=partial 模式·全片就位后重跑即全量
# v0 粗剪注记: 定格延窗位=重复摆放（导漘认领后剪映内改定格式）·叠化=XF_T1 唯一
import argparse, importlib.util, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=r"K:\Fluxgroup\FluxGroup")
ap.add_argument("--pylibs", default=r"K:\Fluxgroup\.tools\pylibs")
ap.add_argument("--ref", default=r"K:\Fluxgroup\.tools\pyJianYingDraft-ref", help="克隆源库根（main 版 API·与 demo 同源）")
args = ap.parse_args()
sys.path.insert(0, args.pylibs)      # pip --target 依赖垫（pymediainfo/pillow 等）
sys.path.insert(0, args.ref)        # 包本体=克隆 main 源（pip 0.3.0 API 旧）

import pyJianYingDraft as draft
from pyJianYingDraft import trange_seconds, TransitionType

REPO = os.path.abspath(args.repo)
HERE = os.path.join(REPO, "cph4", "fleet", "mv-album-001-jay")
sys.path.insert(0, HERE)

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

XQ = _load("xq_shots", os.path.join(HERE, "星晴-shots-v2.py"))
CLIPS = os.path.join(REPO, "media", "mv-album-001-jay", "clips-local-768")
SONG = os.path.join(HERE, "audio", "周杰伦 - 星晴.mp3")
OUT_ROOT = os.path.join(REPO, "media", "mv-album-001-jay", "jianying-drafts")
os.makedirs(OUT_ROOT, exist_ok=True)

ALIAS = {"XQ17a": "XQ17", "XQ17b": "XQ17", "XQ17c": "XQ17", "XQ17d": "XQ17"}

def clip_of(sid):
    return os.path.join(CLIPS, "XQ_%s.mp4" % ALIAS.get(sid, sid))

rows = [(s[0], s[1], s[2], s[3]) for s in XQ.NEW] + [(r[0], r[1], r[2], r[3]) for r in XQ.REUSE]

placed, missing, cursor = [], [], {}
for sid, t0, t1, speed in rows:
    fp = clip_of(sid)
    if not (os.path.isfile(fp) and os.path.getsize(fp) > 100000):
        missing.append(sid)
        continue
    win = t1 - t0
    src_len = win / speed
    off = cursor.get(sid, 0.0)
    cursor[sid] = off + src_len
    seg = draft.VideoSegment(fp, trange_seconds(t0, duration=win),
                             source_timerange=trange_seconds(off, duration=src_len), speed=speed)
    if sid == "XQ18a":  # XF_T1 唯一叠化挂前段
        for tname in ("叠化", "溶解", "叠影"):
            t = getattr(TransitionType, tname, None)
            if t is not None:
                seg.add_transition(t, duration="1.5s")
                break
    placed.append((seg, sid, t0))

df = draft.DraftFolder(OUT_ROOT)
script = df.create_draft("星晴-粗剪-v23", 1344, 768, allow_replace=True)
script.append_tracks([
    draft.TrackSpec(draft.TrackType.audio, "原曲"),
    draft.TrackSpec(draft.TrackType.video, "主片"),
])
for seg, sid, t0 in placed:
    script.add_segment(seg, "主片")
song = draft.AudioSegment(SONG, trange_seconds(0, duration=XQ.FILM_END), volume=1.0)
script.add_segment(song, "原曲")
script.save()
print("DRAFT OK: placed=%d missing=%d(%s)" % (
    len(placed), len(set(missing)), ",".join(sorted(set(missing))) or "none"), flush=True)
print("DRAFT DIR: %s" % os.path.join(OUT_ROOT, "星晴-粗剪-v23"), flush=True)
print("NOTE: 导入法=把整个草稿文件夹复制进剪映 draft 目录（剪映 5.9/6.x 客户端）·缺片位空缺待 i2v 全落后重跑本桥补满", flush=True)
