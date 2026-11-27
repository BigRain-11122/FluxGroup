# -*- coding: utf-8 -*-
"""T0 云道停用令落地：给执行面正典加统一抬头注记（幂等）。

CEO 令 2026-10-20「集团业务全部停止走云端，全部走本地」。
只改执行面文档抬头，不改写任何历史调用记录与判例正文。
"""
import io
import os

BANNER = (
    "> ⛔ **T0·云道停用（CEO 令 2026-10-20）**：本文件凡以云端 API（视频/图像/TTS/云端 LLM/云存储）"
    "为生产路径的条款**停止执行**，改走本地机队（bm-a/bm-b/bm-c）；本地做不了=排队+报障，"
    "不得自动回落云端；例外仅 CEO 亲批+留痕。权威口径=`cph4/fleet/CLOUD-OFF-LOCAL-ONLY-v1.md`。"
    "历史调用记录与判例保持原样，不作改写。"
)

FILES = [
    "cph4/fleet/dispatcher/DISPATCHER-CHARTER.md",
    "cph4/fleet/dispatcher/CEO-PROXY/ROUND.md",
    "cph4/fleet/FLEET-COMPUTE-ARCHITECTURE.md",
    "cph4/fleet/mv-album-001-jay/MV-PIPELINE-PLAYBOOK-v1.md",
    "cph4/fleet/mv-album-001-jay/MV-PRODUCTION-PIPELINE-v1.md",
    "cph4/fleet/mv-album-001-jay/PRODUCTION-SYSTEM-v2.md",
    "cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/PROMPT-EXPERT-GATE-v1.md",
    "cph4/fleet/mv0001-handover/outbound/krea2/prompt-writing-spec-v1/PROMPT-SPEC-v2-I2V.md",
    "cph4/fleet/drama-dept-v1/DRAMA-PRODUCTION-SYSTEM-v1.md",
    "cph4/fleet/shortvideo-dept/PIPELINE.md",
    "cph4/fleet/meme-daily-v1/README-RUNBOOK.md",
    "cph4/fleet/mv-album-001-jay/AUTO-POLISH-LOOP-v1.md",
    "cph4/fleet/mv-album-001-jay/MV-PREPRO-MASTER-v1.md",
    "cph4/fleet/mv-album-001-jay/QC-MASTER-CHECKLIST-v1.md",
    "cph4/fleet/mv-album-001-jay/PRODUCTION-PLAN.md",
    "cph4/fleet/mv-album-001-jay/MV-0001-RETRO-ACCEL-v1.md",
    "cph4/fleet/mv0001-handover/outbound/H3-工作流升级清单-v1.md",
]


def patch(path: str) -> str:
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    if "T0·云道停用" in text:
        return "skip (already noted)"
    nl = "\r\n" if "\r\n" in text[:2000] else "\n"
    lines = text.split(nl)
    if not lines or not lines[0].startswith("#"):
        return "skip (no H1 head)"
    out = [lines[0], "", BANNER, ""] + lines[1:]
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(out))
    return "noted"


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for rel in FILES:
        print("%-78s %s" % (rel, patch(rel)))