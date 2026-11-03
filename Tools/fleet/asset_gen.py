#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_gen.py - 通用资产出图执行器（吃 ASSET-PROMPTS 规格，在**本机** ComfyUI 出图）。

为什么（2026-11-03 CEO「自己去派活」）：
  规格件 `asset-lib-v1/ASSET-PROMPTS-v1.json` 已有 128 件七字段规格（P0 全量），
  但只有 char_gen 能出角色。没有通用执行器，道具/场景的规格就永远只是纸——
  机器醒来也接不到活。

设计要点：
  1. 只在 127.0.0.1:8188 跑（ComfyUI 不外绑），所以卡片必须钉在有 ComfyUI 的机器上。
  2. 不知道模型就不猜：走 char_gen.probe()，配置缺失即 BLOCKED（rc=3）。
  3. 幂等：目标图已存在则跳过；落 media/asset/<class>/<KEY>.png。
  4. 透明底规格（alpha=true）在 ComfyUI 侧做不到时**不假装做到**：先出白底图，
     回执里标 alpha_missing=true，由主控侧抠图（或换服务）补齐。

用法（在目标机上）：
  python Tools/fleet/asset_gen.py --node bm-c --class props --limit 4
  python Tools/fleet/asset_gen.py --class scenes --only scenes-03
Exit: 0 有产出；1 全部失败；3 输入/服务未到位（BLOCKED）
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1", "ASSET-PROMPTS-v1.json")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
CONF = os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1")

SIZE = {"props": (1024, 1024), "scenes": (832, 1472), "motions": (832, 1472),
        "transitions": (832, 1472), "styles": (1024, 1024), "typography": (1080, 1920)}


def blocked(why, gaps, out):
    rec = {"rc": 3, "verdict": "BLOCKED", "status": "BLOCKED", "error_class": "E-BLOCKED-INPUT",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "why": why, "gaps": gaps, "tool": "asset_gen"}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    p = os.path.splitext(out)[0] + "-blocked.json"
    json.dump(rec, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[asset_gen] BLOCKED:", why)
    for g in gaps:
        print("   -", g)
    print("[asset_gen] 回执:", p)
    return 3


def submit_and_save(cg, server, graph, target):
    """提交工作流→等 history→按 /view 取回像素。char_gen 只落 ComfyUI 输出目录，
    本执行器要求产物直接落在 media/asset 下（主控侧要能立刻核验）。"""
    payload = {"prompt": graph, "client_id": str(uuid.uuid4())}
    r = cg.http_json(server + "/prompt", payload, timeout=60)
    pid = r.get("prompt_id")
    if not pid:
        return False
    h = {}
    for _ in range(180):
        time.sleep(2)
        h = cg.http_json(server + "/history/" + str(pid), timeout=15) or {}
        if pid in h:
            break
    node_out = (h.get(pid) or {}).get("outputs") or {}
    for v in node_out.values():
        for im in v.get("images") or []:
            q = urllib.parse.urlencode({"filename": im.get("filename", ""),
                                        "subfolder": im.get("subfolder", ""),
                                        "type": im.get("type", "output")})
            with urllib.request.urlopen(server + "/view?" + q, timeout=60) as resp:
                data = resp.read()
            if len(data) > 1024:
                with open(target, "wb") as f:
                    f.write(data)
                return True
    return False


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default="bm-c")
    ap.add_argument("--class", dest="cls", default="props")
    ap.add_argument("--only", default="", help="如 props-03")
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--receipt", default="")
    a = ap.parse_args(argv)
    out_dir = os.path.join(ROOT, "media", "asset", a.cls)
    rec_path = a.receipt or os.path.join(RECEIPTS, "asset-gen-%s-%s-%s.json"
                                         % (a.cls, a.node, time.strftime("%Y%m%d")))
    if not os.path.exists(SPEC):
        return blocked("规格件不存在：%s" % os.path.relpath(SPEC, ROOT),
                       ["先跑 Tools/fleet/asset_prompts.py"], rec_path)
    spec = json.load(open(SPEC, encoding="utf-8"))
    items = [(k, v) for k, v in (spec.get("items") or {}).items()
             if v.get("cls") == a.cls and v.get("status") == "OK"]
    if a.only:
        items = [(k, v) for k, v in items if k == a.only]
    if not items:
        return blocked("规格里没有 %s 类的合格条目" % a.cls,
                       ["先补 ASSET-PROMPTS 的 %s 类" % a.cls], rec_path)

    import char_gen as cg  # 复用探测与图结构，不另写一套
    try:
        conf = json.load(open(os.path.join(CONF, "comfy-%s.json" % a.node), encoding="utf-8"))
    except Exception:
        try:
            conf = cg.probe(a.server)
        except Exception as e:
            return blocked("ComfyUI 不可达：%s（%s）" % (a.server, e),
                           ["在 %s 上启动 ComfyUI 并确认 8188 可连" % a.node], rec_path)
        json.dump(conf, open(os.path.join(CONF, "comfy-%s.json" % a.node), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    if not conf.get("route"):
        return blocked("本机 ComfyUI 没有可用模型（ckpt/unet 都是 0）",
                       ["在 %s 装一个 SDXL 级底模" % a.node], rec_path)

    os.makedirs(out_dir, exist_ok=True)
    made, skipped, failed = [], 0, []
    for key, v in items:
        if len(made) >= max(0, a.limit):
            break
        target = os.path.join(out_dir, key + ".png")
        if os.path.exists(target) and os.path.getsize(target) > 1024:
            skipped += 1
            continue
        w, h = SIZE.get(a.cls, (1024, 1024))
        pos = "%s, %s, %s" % (v.get("subject", ""), v.get("composition", ""), v.get("style", ""))
        neg = v.get("negative", "lowres, bad anatomy, text, watermark, signature, extra fingers")
        seed = 20261103 + abs(hash(key)) % 10000
        g = cg.graph_ckpt(pos, neg, seed, conf, w, h) if conf["route"] == "ckpt" \
            else cg.graph(pos, neg, seed, conf, w, h)
        try:
            ok = submit_and_save(cg, a.server, g, target)
        except Exception as e:
            failed.append([key, str(e)[:120]])
            continue
        if not ok:
            failed.append([key, "无返回图"])
            continue
        made.append({"key": key, "file": os.path.relpath(target, ROOT),
                     "alpha_missing": bool(v.get("alpha") is True or v.get("alpha") == "true"),
                     "size": [w, h]})

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "class": a.cls, "node": a.node,
           "made": made, "skipped": skipped, "failed": failed,
           "verdict": "PASS" if made else ("FAIL" if failed else "PASS"),
           "note": "alpha_missing=true 表示规格要求透明底但本机只出白底图，需主控抠图补齐"}
    os.makedirs(os.path.dirname(rec_path), exist_ok=True)
    json.dump(rec, open(rec_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[asset_gen] %s 出 %d 件，跳过 %d，失败 %d → %s"
          % (a.cls, len(made), skipped, len(failed), os.path.relpath(rec_path, ROOT)))
    for f in failed[:3]:
        print("   ! ", f[0], f[1])
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))