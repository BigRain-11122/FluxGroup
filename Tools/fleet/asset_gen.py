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
import re
import subprocess
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
EN_CACHE = os.path.join(CONF, "PROMPTS-EN-v1.json")
RMBG_SCRIPT = os.path.join(HERE, "rmbg_matte.py")
# 项目 python 没有 torch，抠图交给 ComfyUI 自带的解释器；可在 conf 里用 matte_python 覆盖。
DEFAULT_RMBG_PYTHON = r"D:\ComfyUI\python_embeded\python.exe"

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


def _feather(alpha):
    import cv2
    import numpy as np
    return cv2.GaussianBlur(alpha, (3, 3), 0)


def matte_white(data):
    """白底转透明：从四边泛洪只吃掉与边缘连通的背景，物体内部白色高光得以保留。

    返回 (bytes, applied)。applied=False 表示没抠掉任何东西（多半不是白底）。
    """
    import numpy as np
    import cv2
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if arr is None:
        return data, False
    h, w = arr.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
             (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    flags = cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
    for seed in seeds:
        cv2.floodFill(arr, mask, seed, (0, 0, 0), (20, 20, 20), (20, 20, 20), flags)
    inner = mask[1:-1, 1:-1]
    if inner.max() != 0 and int((inner == 255).sum()) >= 0.05 * inner.size:
        alpha = np.where(inner == 255, 0, 255).astype(np.uint8)
        rgba = cv2.cvtColor(arr, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = _feather(alpha)
        ok, buf = cv2.imencode(".png", rgba)
        if ok:
            return buf.tobytes(), True
    return data, False


def matte_grabcut(data):
    """白底抠不动时用 grabCut：假定主体居中、四周是背景。慢（数秒）但通用。"""
    import numpy as np
    import cv2
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if arr is None:
        return data, False
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    m = max(8, int(min(h, w) * 0.04))
    try:
        cv2.grabCut(arr, mask, (m, m, w - 2 * m, h - 2 * m),
                    np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64),
                    5, cv2.GC_INIT_WITH_RECT)
    except Exception:
        return data, False
    fg = (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)
    if fg.sum() < 0.01 * fg.size or fg.sum() > 0.98 * fg.size:
        return data, False
    alpha = np.where(fg, 255, 0).astype(np.uint8)
    rgba = cv2.cvtColor(arr, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = _feather(alpha)
    ok, buf = cv2.imencode(".png", rgba)
    return (buf.tobytes(), True) if ok else (data, False)


def _is_white_bg(arr):
    """四角都是亮且均匀的近白色，才算白底；否则泛洪会顺着亮部漏进物体内部。"""
    import numpy as np
    h, w = arr.shape[:2]
    k = max(8, min(h, w) // 40)
    for y, x in ((0, 0), (0, w - k), (h - k, 0), (h - k, w - k)):
        blk = arr[y:y + k, x:x + k].astype(np.float32)
        if blk.mean() < 232 or blk.std() > 14:
            return False
    return True


def render_size(w, h):
    """SDXL 在 9:16 这类极端比例上会把一个主体画成两个（实测怀表出成上下两块）。

    先按模型友好的 832x1472 出图，落盘后再放大到规格尺寸。
    """
    if max(w, h) / float(min(w, h)) > 1.6 and max(w, h) > 1440:
        return (832, 1472) if h > w else (1472, 832)
    return w, h


def upscale_to(target, w, h):
    from PIL import Image
    im = Image.open(target)
    if im.size == (w, h):
        return
    im.resize((w, h), Image.LANCZOS).save(target)


def matte_rmbg(target):
    """用本机 BRIA RMBG 权重抠图（质量远好于 grabCut）。成功则原地替换 target。"""
    py = os.environ.get("RMBG_PYTHON") or DEFAULT_RMBG_PYTHON
    if not py or not os.path.exists(py) or not os.path.exists(RMBG_SCRIPT):
        return False
    out_dir = os.path.dirname(os.path.abspath(target))
    stem = os.path.splitext(os.path.basename(target))[0]
    cand = os.path.join(out_dir, stem + "-alpha.png")
    try:
        r = subprocess.run([py, RMBG_SCRIPT, os.path.abspath(target), "--out-dir", out_dir,
                            "--suffix", "-alpha", "--force"],
                           capture_output=True, text=True, timeout=600)
    except Exception:
        return False
    if r.returncode != 0 or not os.path.exists(cand):
        return False
    os.replace(cand, target)
    return True


def matte_auto(data):
    """白底优先（快且干净），不是白底就上 grabCut。"""
    import numpy as np
    import cv2
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if arr is not None and _is_white_bg(arr):
        out, ok = matte_white(data)
        if ok:
            return out, True
    return matte_grabcut(data)


def submit_and_save(cg, server, graph, target, matte=False):
    """提交工作流→等 history→按 /view 取回像素。char_gen 只落 ComfyUI 输出目录，
    本执行器要求产物直接落在 media/asset 下（主控侧要能立刻核验）。"""
    payload = {"prompt": graph, "client_id": str(uuid.uuid4())}
    r = cg.http_json(server + "/prompt", payload, timeout=60)
    pid = r.get("prompt_id")
    if not pid:
        return False
    h = {}
    for i in range(180):
        time.sleep(2)
        h = cg.http_json(server + "/history/" + str(pid), timeout=15) or {}
        if pid in h:
            break
        # stdout 就是执行器的进度信号：静默等待会被 closer 判 30min STALL 并杀线
        if i and i % 15 == 0:
            print("WAIT pid=%s elapsed=%ds" % (pid, (i + 1) * 2), flush=True)
    if pid not in h:
        print("TIMEOUT pid=%s after 360s (comfy history empty)" % pid, flush=True)
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
                if not matte:
                    return 1
                if matte_rmbg(target):
                    return 1
                data, applied = matte_auto(data)
                with open(target, "wb") as f:
                    f.write(data)
                # 2 = 已落盘但没抠出透明底（不是出图失败）
                return 2 if not applied else 1
    return 0


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
    # 中文提示在 SDXL 上会跑题，优先用 prompt_en.py 生成的英文标签。
    en = {}
    if os.path.exists(EN_CACHE):
        try:
            en = json.load(open(EN_CACHE, encoding="utf-8")).get("items") or {}
        except Exception:
            en = {}
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
        m = re.match(r"^\s*(\d+)\s*[xX*]\s*(\d+)\s*$", str(v.get("size") or ""))
        if m:
            w, h = int(m.group(1)), int(m.group(2))
        alpha = v.get("alpha") is True or str(v.get("alpha")).lower() == "true"
        neg = v.get("negative", "lowres, bad anatomy, text, watermark, signature, extra fingers")
        pos = (en.get(key) or {}).get("en") or \
            "%s, %s, %s" % (v.get("subject", ""), v.get("composition", ""), v.get("style", ""))
        if alpha:
            pos += ", single isolated object, plain solid white studio background, even flat lighting, " \
                   "no background shadows, no bokeh, centered, whole object inside frame"
            neg += ", bokeh, depth of field, gradient background, background scenery, city, street, crowd, " \
                   "reflection on background"
        seed = 20261103 + abs(hash(key)) % 10000
        rw, rh = render_size(w, h)
        g = cg.graph_ckpt(pos, neg, seed, conf, rw, rh) if conf["route"] == "ckpt" \
            else cg.graph(pos, neg, seed, conf, rw, rh)
        try:
            ok = submit_and_save(cg, a.server, g, target, matte=alpha)
        except Exception as e:
            failed.append([key, str(e)[:120]])
            continue
        if not ok:
            failed.append([key, "无返回图"])
            continue
        if (rw, rh) != (w, h):
            upscale_to(target, w, h)
        made.append({"key": key, "file": os.path.relpath(target, ROOT),
                     "alpha_missing": ok == 2, "alpha": alpha, "size": [w, h]})

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "class": a.cls, "node": a.node,
           "made": made, "skipped": skipped, "failed": failed,
           "verdict": "PASS" if (made or skipped) and not failed else "FAIL",
           "no_new_work": (not made and bool(skipped) and not failed),
           "note": "alpha_missing=true 表示规格要求透明底但本机只出白底图，需主控抠图补齐"}
    os.makedirs(os.path.dirname(rec_path), exist_ok=True)
    json.dump(rec, open(rec_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[asset_gen] %s 出 %d 件，跳过 %d，失败 %d → %s"
          % (a.cls, len(made), skipped, len(failed), os.path.relpath(rec_path, ROOT)))
    for f in failed[:3]:
        print("   ! ", f[0], f[1])
    # 2026-11-12 R41: 目标全部已在盘 = 无新活 = 成功，不是失败。
    # 旧实参 `return 0 if made else 1` 让 made=[]/skipped=20/failed=[] 也返回 1，
    # 卡被判 FAILED 后由 master 每 30 秒重派重跑（实测 05:19-05:23 连跑 6 次，每轮一笔噪声提交）。
    # 语义对齐 char_gen.py：有失败=1（要重试）；有产出或有跳过且无失败=0；规格为空=1（可疑）。
    return 0 if (made or skipped) and not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))