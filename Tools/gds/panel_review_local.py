#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""立项评审的独立席通道：本地 9b 顺序跑两个席位，产出落盘供人工比对。

用途：给 S1（市场）和 S7（独立审计）各一个不同模型的独立意见，避免单人自审自签。
不是判据本身：模型输出只作旁证，分数仍须挂在可核验的文件/数字上。
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G2 = ROOT / "cph4" / "fleet" / "game-v2"
PROJ = G2 / "projects" / "fold-001"
OUT = PROJ / "local"
URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3.5:9b"

FACTS = """\
项目：FOLD-001《折一折：衣柜》，Steam 买断 $14.99，无广告无服务器，单槽生产。
契约：session 75 秒/局，12 分钟/会话，最强一秒在第 8 秒，content_hours=3，6 周周期。
内容包：25 房间 × 4 格 = 100 格；每格 4-6 件；一格 60-90 秒；声称首通 127 分钟、总 3.5 小时。
另一份文档（机会卡）写：100 件 × 25 秒 ≈ 首通 42 分钟。
市场：折/纸类扫到 14 款，全部 0-20,000 拥有，最高 Paper Trail 496 条评论、0.54 评/天；2025-2026 新发 3 款 0 评论。
母类：Unpacking 75 万拥有、ALTTL 35 万；母类是「整理/归位」，不是「折」。
数据只拉了 2026-11-20 一天，没有 7 天连续样本。
题材变更：从折纸 PIVOT 到折衣；契约 scene 字段仍写「折纸/折布」，未改。
代审记录：G-A 给折衣 25/30（市场验证 4/5），但市场扫描扫的是折，不是折衣。
工程：团结 batchmode 编译 0 error；折叠几何重放 20 次哈希一致；IoU 判定 1.0（负控 unfolded 0.5、错半边 0.0）。
未测：层遮挡、1080p 帧率、手势、单件计时、5 人盲看。
8 闸回执：G1-G8 全部 NOT_RUN 或 FAIL（无编译日志/无包/无素材）。
财务：复算后每份净 ¥32.52（税 20%、退款 15%、区域 0.75），月净 3 万需 923 份/月。
"""

JOBS = [
    {
        "id": "S1-market",
        "out": "panel-S1-market-9b.md",
        "system": ("你是独立市场评审。只依据下面的证据判断，禁止引入证据以外的记忆或数字。"
                   "输出三段，简体中文，总长不超过 450 字：\n"
                   "①市场验证应给几分（0-5，可给小数）与一句理由；\n"
                   "②列出你认为最可能站不住的三条判断；\n"
                   "③每条写明：需要什么证据才能证实或证伪。"),
        "prompt": FACTS + "\n请评审。",
    },
    {
        "id": "S7-audit",
        "out": "panel-S7-audit-9b.md",
        "system": ("你是独立审计。只依据下面的事实，用三句话回答三个问题，不要复述事实、不要总结。"
                   "①哪一条结论用错了证据对象？②哪两个数字互相矛盾？③哪个「通过」其实没有测？"),
        "prompt": FACTS + "\n请按①②③回答。",
    },
]


def stop(model: str):
    subprocess.run(["ollama", "stop", model], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=30)


def call(job: dict, model: str = MODEL) -> dict:
    payload = {
        "model": model, "system": job["system"], "prompt": job["prompt"],
        "stream": False, "keep_alive": "10m",
        # qwen3.5 默认把整段输出放进 thinking，response 为空；评审要的是可落盘的正文。
        "think": False,
        "options": {"num_ctx": 8192, "temperature": 0.1, "num_gpu": 99, "num_thread": 8,
                    "num_predict": 500},
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=900) as r:
        out = json.loads(r.read().decode("utf-8"))
    text = (out.get("response") or "").strip()
    path = OUT / job["out"]
    path.write_text(text + "\n", encoding="utf-8")
    return {
        "id": job["id"], "model": model, "chars": len(text),
        "tok_s": round(out.get("eval_count", 0) / max(out.get("eval_duration", 1) / 1e9, 1e-9), 1),
        "elapsed_s": round(time.time() - t0, 1),
        "out": str(path.relative_to(ROOT)),
    }


def main() -> int:
    import sys

    only = ""
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    model = MODEL
    if "--model" in sys.argv:
        model = sys.argv[sys.argv.index("--model") + 1]

    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for job in JOBS:
        if only and job["id"] != only:
            continue
        try:
            r = call(job, model)
        except Exception as exc:  # noqa: BLE001
            r = {"id": job["id"], "error": str(exc)[:200]}
        finally:
            stop(model)
            time.sleep(2)
        results.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
    (OUT / "panel-local-report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if all("error" not in r for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
