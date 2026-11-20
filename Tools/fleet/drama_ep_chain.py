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
        want = ["plan", "kf", "i2v-plan", "i2v", "assembly", "qc"]
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
        elif st in ("audio", "assembly", "qc"):
            rc, out = 0, None
            print("  SKIP %s：未接线（drama_assemble 需要 clip+voice+subs 三件齐）" % st)
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
