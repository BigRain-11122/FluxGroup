# -*- coding: utf-8 -*-
"""给软著提审缺图标的产品生成 16-bit 像素风 app 图标（AI 设计稿，不是应用截图）。

为什么只做图标不做截图：图标是设计产物，提审本来就要设计；截图必须是应用内真实画面，
拿生成图冒充截图就是假证据，一律不做。

用法：
  python Tools/fleet/game_icon_gen.py --limit 4
  python Tools/fleet/game_icon_gen.py --only TimeRepairShop
Exit: 0 有产出；3 无可做项；1 全失败
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
MATS = os.path.join(ROOT, "软著申请材料")
RECEIPTS = os.path.join(ROOT, "cph4", "fleet", "queue-receipts")
ICON_HINTS = ("icon", "logo", "appicon", "图标")

# 16-bit 像素风：与项目既有图标（g16_icon_1024.png）保持同一风格锚
STYLE = ("16-bit pixel art game app icon, {subject}, limited palette, crisp hard pixels, "
         "thick dark outline, strong silhouette, centered composition, plain background, no text")
HOST = os.environ.get("OLLAMA_HOST") or "http://100.75.133.10:11434"
LLM = os.environ.get("SUBJECT_MODEL") or "qwen3.5:4b-mlx"


def slug(name):
    m = re.match(r"^([A-Za-z]*\d+)", name)
    if m:
        return m.group(1).lower()
    head = re.split(r"[_\s]", name)[0]
    return re.sub(r"[^a-z0-9]", "", head.lower()) or "game"


def has_icon(d):
    for root, _dirs, files in os.walk(d):
        for f in files:
            low = f.lower()
            if low.endswith(".png") and any(k in low for k in ICON_HINTS):
                return True
    return False


def subject_of(name):
    """把产品名换成一句英文视觉描述；中文名交给主控上的小模型翻译，避免硬编码。"""
    clean = re.sub(r"_(CCPC提交格式|提交格式)$", "", name)
    clean = re.sub(r"^[A-Za-z]{0,3}\d{2,4}[_\-]", "", clean)   # G02_TimeRepairShop -> TimeRepairShop
    clean = clean.replace("_", " ").strip()
    if re.search(r"[\u4e00-\u9fff]", clean):
        try:
            body = {"model": LLM, "stream": False, "think": False,
                    "prompt": ("Turn this Chinese game title into one short English visual subject "
                               "for a game icon, 6-10 words, describing the main object or scene. "
                               "Output only the English phrase, no quotes.\n\n" + clean),
                    "options": {"temperature": 0.3, "num_predict": 60}}
            req = urllib.request.Request(HOST + "/api/generate", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=60))
            text = " ".join((r.get("response") or "").split())
            if text:
                return text
        except Exception:
            pass
        return "a stylized game scene"
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", clean).lower()
    half = spaced.split()
    if len(half) % 2 == 0 and half[:len(half) // 2] == half[len(half) // 2:]:
        spaced = " ".join(half[:len(half) // 2])      # FluxVerse_FluxVerse -> flux verse
    spaced = " ".join(spaced.split())
    return "a %s game scene" % spaced


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--receipt", default=os.path.join(RECEIPTS, "game-icons-%s.json"
                                                      % time.strftime("%Y%m%d")))
    a = ap.parse_args(argv)
    if not os.path.isdir(MATS):
        print("[icons] 缺目录 %s" % MATS)
        return 3

    import asset_gen as ag
    import char_gen as cg

    try:
        conf = json.load(open(os.path.join(ROOT, "cph4", "fleet", "asset-lib-v1",
                                           "comfy-bm-c.json"), encoding="utf-8"))
    except Exception as e:
        print("[icons] 读不到 ComfyUI 配置：%s" % e)
        return 3

    todo = []
    for name in sorted(os.listdir(MATS)):
        d = os.path.join(MATS, name)
        if not os.path.isdir(d) or name.startswith(("_", ".")):
            continue
        if a.only and name != a.only:
            continue
        if os.path.isdir(os.path.join(d, "__pycache__")):
            continue
        if has_icon(d):
            continue
        todo.append((name, d))
    if not todo:
        print("[icons] 没有缺图标的产品（rc=3）")
        return 3

    made, failed = [], []
    for name, d in todo[:a.limit]:
        subj = subject_of(name)
        prompt = STYLE.format(subject=subj)
        neg = ("text, words, letters, signage, sign board, banner, label, typography, "
               "chinese characters, watermark, photo, 3d render, blurry, lowres, frame, border")
        out_dir = os.path.join(d, "提交材料")
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, "%s_icon_1024.png" % slug(name))
        g = cg.graph_ckpt(prompt, neg, 20261108, conf, 1024, 1024)
        try:
            ok = ag.submit_and_save(cg, a.server, g, target)
        except Exception as e:
            failed.append([name, str(e)[:120]])
            continue
        if not ok:
            failed.append([name, "无图返回"])
            continue
        print("[icons] %s <- %s" % (name, subj), flush=True)
        made.append({"product": name, "file": os.path.relpath(target, ROOT),
                     "subject": subj, "style": "16-bit pixel art"})

    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "game-icon",
           "made": made, "failed": failed, "pending": len(todo),
           "verdict": "PASS" if made else "FAIL",
           "note": ("AI 生成的设计稿图标（16-bit 像素风），用于软著提审的图标位；"
                    "**不是应用截图**——应用截图必须在应用内真实截取，本工具不生成。")}
    os.makedirs(os.path.dirname(a.receipt), exist_ok=True)
    json.dump(rec, open(a.receipt, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[icons] 出 %d / 待 %d，失败 %d → %s"
          % (len(made), len(todo), len(failed), os.path.relpath(a.receipt, ROOT)))
    for f in failed[:3]:
        print("  ! ", f[0], f[1])
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))