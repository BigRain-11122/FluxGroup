#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_caption.py - 用常驻 vision 模型给资产库图片打训练用 caption。

为什么（2026-11-03）：资产库现在的缺口不是图，是 caption——kohya 训练要
"<触发词>, 画面描述" 的 .txt，没有它就得一张张手写，30 张就是半小时人工。
本机常驻档 qwen3.5:4b-mlx 带 vision，实测能把关键帧描述准
（短发米色风衣女主/蓝西装男/办公室/仰拍/自然光），所以让它出草稿、人只做校对。

两条硬约束（都是实测/合规要求）：
  1. **think=false**：qwen3 系思考模型不关思考，response 会是空字符串（实测 120 token 全进 thinking）
  2. **不写人名、不猜身份**：caption 只描述可见属性；出现 \u4e0d确定/名字/明星一律判废，退回人工
  3. 每张 72 秒量级（M1 Pro 图像预填开销），所以默认单张串行、夜间跑，不做白天实时

用法：
  python3 asset_caption.py --dir media/asset/faces/<角色> --trigger mychar [--limit 5]
Exit: 0 已产出 caption；3 没有待打标图片（都有 .txt 了）；1 模型不可用；2 目录不存在。
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request

IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
HOST = os.environ.get("OLLAMA_HOST") or "127.0.0.1:11434"
HOST = HOST if "://" in HOST else "http://" + HOST
MODEL = os.environ.get("CAPTION_MODEL") or "qwen3.5:4b-mlx"

PROMPT = ("Describe this image as a Stable Diffusion LoRA training caption. "
          "Include only visible attributes: subject, apparent age, hair, clothing, expression, "
          "lighting, camera angle, background. One sentence, under 40 words, English. "
          "Do not name anyone, do not guess identity, do not add style words.")

# caption 必须覆盖到的可见属性（至少命中 3 个），否则判废——防模型输出空话
SLOTS = ("hair", "coat", "shirt", "cloth", "dress", "jacket", "expression", "light",
         "background", "angle", "face", "eyes", "window", "room", "street", "indoor", "outdoor")
BAD = ("i think", "possibly", "maybe", "probably", "appears to be", "looks like",
       "celebrity", "famous", "actor", "actress", "idol")


def post(path, body, timeout=300):
    req = urllib.request.Request(HOST + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def caption(path):
    img = base64.b64encode(open(path, "rb").read()).decode()
    t0 = time.time()
    d = post("/api/generate", {"model": MODEL, "prompt": PROMPT, "images": [img],
                               "stream": False, "think": False, "keep_alive": "30m",
                               "options": {"temperature": 0.2, "num_predict": 90}})
    text = (d.get("response") or "").strip()
    sec = time.time() - t0
    toks = d.get("eval_count") or 0
    return text, sec, toks


def validate(text):
    """返回 (ok, why)。宁可退回人工，也不写一条猜身份的 caption 进训练集。"""
    low = text.lower()
    if not text:
        return False, "空回复（多半是没关 think）"
    if len(text) < 20 or len(text) > 300:
        return False, "长度异常 %d" % len(text)
    hits = sum(1 for s in SLOTS if s in low)
    if hits < 3:
        return False, "只命中 %d 个可见属性，像空话" % hits
    for b in BAD:
        if b in low:
            return False, "含推测/身份词：%s" % b
    # 中文人名式「某某」或引号内大写专名一律退回（宁可错杀）
    if re.search(r"[\"'“”][A-Z][a-z]{2,}", text):
        return False, "含疑似专名（引号+大写）"
    return True, "ok"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--trigger", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        print("目录不存在：%s（rc=2）" % a.dir)
        return 2
    todo = []
    for n in sorted(os.listdir(a.dir)):
        p = os.path.join(a.dir, n)
        if os.path.isfile(p) and n.lower().endswith(IMG):
            txt = os.path.splitext(p)[0] + ".txt"
            if not os.path.exists(txt):
                todo.append((p, txt))
    if a.limit:
        todo = todo[:a.limit]
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "dir": a.dir, "model": MODEL,
           "trigger": a.trigger, "pending": len(todo), "written": 0, "rejected": [],
           "seconds": 0.0}
    if not todo:
        rec.update({"verdict": "BLOCKED", "status": "BLOCKED",
                    "gaps": ["没有待打标图片（目录里都有 .txt 了）"]})
        emit(rec, a.out)
        print("[caption] 没有待打标图片（rc=3）")
        return 3
    t0 = time.time()
    for p, txt in todo:
        try:
            text, sec, toks = caption(p)
        except Exception as e:
            rec["rejected"].append([os.path.basename(p), "请求失败 %s" % str(e)[:80]])
            continue
        ok, why = validate(text)
        if not ok:
            rec["rejected"].append([os.path.basename(p), why, text[:120]])
            continue
        body = ("%s, %s" % (a.trigger, text)) if a.trigger else text
        with open(txt, "w", encoding="utf-8") as f:
            f.write(body.strip() + "\n")
        rec["written"] += 1
    rec["seconds"] = round(time.time() - t0, 1)
    rec["per_image_s"] = round(rec["seconds"] / max(1, len(todo)), 1)
    rec.update({"verdict": "PASS" if rec["written"] else "FAIL", "gaps": []})
    if not rec["written"]:
        rec["gaps"] = ["一条都没写成功，看 rejected 的原因"]
    rec["status"] = rec["verdict"]
    emit(rec, a.out)
    print("[caption] 写 %d / 待 %d（%.1fs/张）%s"
          % (rec["written"], len(todo), rec["per_image_s"],
             "" if rec["written"] else "，全部被拒，看 rejected"))
    for r in rec["rejected"][:5]:
        print("  ! %s：%s" % (r[0], r[1]))
    return 0 if rec["written"] else 1


def emit(rec, path):
    if not path:
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    json.dump(rec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))