#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama_ep_chain.py — 单集端到端链（D3→D4→D7→D8），幂等 + SKIP + 状态落盘。

为什么（2026-11-20）：PRODUCTS.json 的 PROD-DRAMA-EP 九个工序只有 3 条命令，
且都不带集号；一张卡无法表达"给 EP017 出片"。本文件把「一集」作为最小执行单元，
一条命令跑完整链，每一步都可单独重跑（SKIP 判据同各站自己的判据）。

站序：
  plan     剧本 → kf_prompts.json        (drama_kf_plan)
  kf       prompt 表 → kf/*.png          (drama_kf_batch)
  i2v-plan kf → i2v_manifest.json        (drama_i2v_plan)
  i2v      帧 → i2v/*.mp4                (h3_i2v_album + 工作流)
  audio    配音/音效                      (占位：未接线则 SKIP 并写明)
  assembly i2v + audio + 字幕 → ep.mp4    (drama_assemble 需要 manifest，本链先做保守版)
  qc       成片 → qa.json                (drama_quality_gate)

用法：
  python Tools/fleet/drama_ep_chain.py --ep 1 --dry-run
  python Tools/fleet/drama_ep_chain.py --ep 1 --stages plan,kf,i2v-plan
  python Tools/fleet/drama_ep_chain.py --ep 1 --stages all
Exit: 0 全绿/全跳过；1 有站失败；2 参数或前置缺失
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
I2V = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "local-i2v", "h3_i2v_album.py")
WF480 = os.path.join(ROOT, "cph4", "fleet", "mv-album-001-jay", "local-i2v", "wf_h3_i2v_480p_int4.json")
PY = sys.executable
NO_WIN = 0x08000000 if os.name == "nt" else 0


def sh(cmd, dry):
    print("  $ " + " ".join(cmd[1:]), flush=True)
    if dry:
        return 0
    p = subprocess.run(cmd, cwd=ROOT, creationflags=NO_WIN)
    return p.returncode


PIPER = r"K:\Fluxgroup\.tools\tts-venv\Scripts\piper.exe"
PIPER_MODEL = r"K:\Fluxgroup\.tools\piper-voices\zh_CN-huayan-medium.onnx"

# 2026-11-21：多角色配音。piper 本机只有一把女声（zh_CN-huayan），漫剧里「旁白/父/门卫」
# 全同音=硬伤。edge-tts 是**云端**通道（CEO 令：云端只作辅助），所以默认仍走 piper，
# 显式 --tts edge 才启用按 speaker 分音色。音色映射按剧本 speaker 字段匹配。
EDGE_VOICES = {
    "旁白": "zh-CN-YunjianNeural",      # 沉稳男声，叙述感
    "父": "zh-CN-YunxiNeural",          # 中年男声
    "门卫": "zh-CN-YunxiNeural",
    "长": "zh-CN-YunxiNeural",          # 主角（成年）
    "神": "zh-CN-YunjianNeural",
}
EDGE_DEFAULT = "zh-CN-XiaoxiaoNeural"


def _edge_say(text, voice, out):
    """edge-tts 合成一句（云端辅助通道）。失败抛异常由调用方记 failed。"""
    import asyncio
    import edge_tts

    async def _go():
        await edge_tts.Communicate(text, voice).save(out)

    asyncio.run(_go())
    return os.path.getsize(out) > 2000


def _speaker_voice(speaker):
    for k, v in EDGE_VOICES.items():
        if k and k in (speaker or ""):
            return v
    return EDGE_DEFAULT


def voice_all(ep, a, dry=False):
    """逐镜配音：对每个有 sub 的镜出一句 wav（SKIP 已存在 >10KB）。

    单音色（piper zh_CN-huayan）是当前本机能跑的诚实上限；多角色需 IndexTTS/GPT-SoVITS。
    """
    import json as _json
    base = os.path.join(ROOT, "cph4", "fleet", "out", "drama", "EP%03d" % ep)
    plan = os.path.join(base, "kf_prompts.json")
    if not os.path.isfile(plan):
        print("  AUDIO ABORT 缺 kf_prompts.json")
        return 2
    rows = _json.load(open(plan, encoding="utf-8"))
    vo = os.path.join(base, "vo")
    os.makedirs(vo, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    made = skipped = failed = 0
    for r in rows:
        sub = (r.get("sub") or "").strip()
        if not sub:
            continue
        wav = os.path.join(vo, r["id"] + ".wav")
        if os.path.isfile(wav) and os.path.getsize(wav) > 10000:
            skipped += 1
            continue
        if dry:
            print("  DRY voice " + r["id"])
            made += 1
            continue
        txt = os.path.join(vo, r["id"] + ".txt")
        open(txt, "w", encoding="utf-8").write(sub)
        use_edge = (getattr(a, "tts", "piper") == "edge")
        if use_edge:
            voice = _speaker_voice(r.get("speaker"))
            mp3 = os.path.join(vo, r["id"] + ".mp3")
            try:
                ok = _edge_say(sub, voice, mp3)
            except Exception as e:
                ok = False
                print("  VOICE edge ERR %s %s" % (r["id"], type(e).__name__))
            if ok:
                # 统一成 wav（下游 _mixed.wav 走 pydub，格式混杂会拖慢）
                pc = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3,
                                     "-ar", "48000", "-ac", "1", wav],
                                    creationflags=NO_WIN, capture_output=True)
                if pc.returncode == 0 and os.path.getsize(wav) > 1000:
                    made += 1
                    continue
            failed += 1
            print("  VOICE FAIL " + r["id"])
            continue
        p = subprocess.run([PIPER, "--model", PIPER_MODEL, "--output_file", wav, "--input_file", txt],
                           env=env, creationflags=NO_WIN, capture_output=True)
        if p.returncode == 0 and os.path.getsize(wav) > 1000:
            made += 1
        else:
            failed += 1
            print("  VOICE FAIL " + r["id"])
    print("  AUDIO made=%d skipped=%d failed=%d" % (made, skipped, failed))
    return 0 if failed == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", type=int, required=True)
    ap.add_argument("--stages", default="plan,kf,i2v-plan")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--height", type=int, default=864)
    ap.add_argument("--max-s", type=float, default=3.0)
    ap.add_argument("--wf", default=WF480)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tts", choices=["piper", "edge"], default="piper",
                    help="piper=本地单音色（默认·离线）；edge=云端多音色，按剧本 speaker 分角色（辅助通道）")
    a = ap.parse_args(argv)

    ep = a.ep
    base = os.path.join(ROOT, "cph4", "fleet", "out", "drama", "EP%03d" % ep)
    os.makedirs(base, exist_ok=True)
    state_p = os.path.join(base, "chain-state.json")
    state = {"ep": ep, "stages": {}, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if os.path.isfile(state_p):
        try:
            state = json.load(open(state_p, encoding="utf-8"))
        except Exception:
            pass
    state.setdefault("stages", {})

    want = [s.strip() for s in a.stages.split(",") if s.strip()]
    if want == ["all"]:
        # 2026-11-21 修：原 all 漏了 audio —— EP002-009 因此全程无配音，
        # 装配走"无音轨"兜底并连带踩到 ffmpeg 参数错位，9 集全 blocked。
        want = ["plan", "kf", "i2v-plan", "i2v", "audio", "assembly", "qc"]
    fails = 0
    print("CHAIN EP%03d stages=%s dry=%s" % (ep, ",".join(want), a.dry_run))

    for st in want:
        t0 = time.time()
        print("[%s]" % st, flush=True)
        if st == "plan":
            rc = sh([PY, os.path.join(HERE, "drama_kf_plan.py"), "--eps", str(ep)], a.dry_run)
            out = "kf_prompts.json"
        elif st == "kf":
            cmd = [PY, os.path.join(HERE, "drama_kf_batch.py"), "--ep", str(ep)]
            if a.limit:
                cmd += ["--limit", str(a.limit)]
            rc = sh(cmd, a.dry_run)
            out = "kf/"
        elif st == "i2v-plan":
            rc = sh([PY, os.path.join(HERE, "drama_i2v_plan.py"), "--ep", str(ep),
                     "--width", str(a.width), "--height", str(a.height), "--max-s", str(a.max_s)], a.dry_run)
            out = "i2v_manifest.json"
        elif st == "i2v":
            rc = sh([PY, I2V, "--repo", ROOT, "--lane", "bmc",
                     "--manifest", "cph4/fleet/out/drama/EP%03d/i2v_manifest.json" % ep,
                     "--out", "cph4/fleet/out/drama/EP%03d/i2v" % ep,
                     "--wf", os.path.relpath(a.wf, ROOT).replace("\\", "/")], a.dry_run)
            out = "i2v/"
        elif st == "audio":
            # 逐镜配音（piper 单音色）→ 见 tools 侧 _voice_all
            rc = voice_all(ep, a, dry=a.dry_run)
            out = "vo/"
        elif st == "assembly":
            rc = sh([PY, os.path.join(HERE, "drama_av_manifest.py"), "--ep", str(ep), "--mix"], a.dry_run)
            if rc == 0:
                rc = sh([PY, os.path.join(ROOT, "Tools", "fleet", "drama_assemble.py"),
                         "--manifest", "cph4/fleet/out/drama/EP%03d/assemble_manifest.json" % ep,
                         "--out", "cph4/fleet/out/drama/EP%03d/ep%03d.mp4" % (ep, ep),
                         "--qa", "cph4/fleet/out/drama/EP%03d/ep%03d-qa.json" % (ep, ep)], a.dry_run)
            out = "ep%03d.mp4" % ep
        elif st == "qc":
            rc = sh([PY, os.path.join(ROOT, "Tools", "fleet", "drama_quality_gate.py"),
                     "--in", "cph4/fleet/out/drama/EP%03d/ep%03d.mp4" % (ep, ep),
                     "--subs-burned",
                     "--out", "cph4/fleet/out/drama/EP%03d/ep%03d-gate.json" % (ep, ep)], a.dry_run)
            out = "ep%03d-gate.json" % ep
        else:
            rc, out = 2, None
            print("  UNKNOWN STAGE %s" % st)
        state["stages"][st] = {"rc": rc, "sec": round(time.time() - t0, 1),
                               "out": out, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if rc not in (0, 3):
            fails += 1
        if rc == 2:
            break

    state["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    state["fails"] = fails
    if not a.dry_run:
        json.dump(state, open(state_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("CHAIN DONE fails=%d state=%s" % (fails, os.path.relpath(state_p, ROOT)))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
