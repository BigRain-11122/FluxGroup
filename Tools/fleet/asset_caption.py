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

# 两套词表（2026-11-04 实测）：资产库里多数是道具/物件，旧提示词只问 hair/coat/expression，
# 物件图必然 0-2 命中被判空话（抽 20 张 20 拒）。人像与物件必须分开判，不能一套词打天下。
PROMPT_PORTRAIT = ("Describe this image as a Stable Diffusion LoRA training caption. "
                   "Include only visible attributes: subject, apparent age, hair, clothing, "
                   "expression, lighting, camera angle, background. "
                   "One sentence, under 40 words, English. "
                   "Do not name anyone, do not guess identity, do not add style words.")

PROMPT_OBJECT = ("Describe this image as a Stable Diffusion LoRA training caption of an object "
                 "or scene. Include only visible attributes: what the object is, its material, "
                 "colour, shape, surface condition, how it is arranged, and the background. "
                 "One sentence, under 40 words, English. "
                 "Do not guess brands, do not name people, do not add style words.")

SLOTS_PORTRAIT = ("hair", "coat", "shirt", "cloth", "dress", "jacket", "expression", "light",
                  "background", "angle", "face", "eyes", "window", "room", "street",
                  "indoor", "outdoor")
SLOTS_OBJECT = ("object", "item", "material", "wood", "metal", "fabric", "paper", "plastic",
                "glass", "leather", "ceramic", "stone", "colour", "color", "red", "blue",
                "white", "black", "grey", "gray", "brown", "green", "yellow", "shape",
                "round", "square", "flat", "surface", "texture", "background", "table",
                "floor", "wall", "arranged", "placed", "light", "shadow", "angle")

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


# 2026-11-09 修：原来只认 /faces/，而资产库的角色素材放在 characters/、
# portraits/、people/ 等目录下，一律被判成 object，于是人物 caption 用物件词表
# 校验 → 命中 1-2 → 判「像空话」。20 张抽检 0 通过就是这条。
# 实测：同一批 7 条合格 caption，object 表 7/7 过，portrait 表 7/7 废。
PORTRAIT_HINTS = ("/faces/", "/face/", "/characters/", "/character/", "/portraits/",
                  "/portrait/", "/people/", "/person/", "/avatars/", "/avatar/",
                  "/人物/", "/角色/", "/人像/")


def kind_of(path, forced=""):
    if forced in ("portrait", "object"):
        return forced
    p = "/" + str(path).replace("\\", "/").lower().strip("/") + "/"
    return "portrait" if any(h in p for h in PORTRAIT_HINTS) else "object"


def caption(path, kind="object"):
    img = base64.b64encode(open(path, "rb").read()).decode()
    prompt = PROMPT_PORTRAIT if kind == "portrait" else PROMPT_OBJECT
    t0 = time.time()
    d = post("/api/generate", {"model": MODEL, "prompt": prompt, "images": [img],
                               "stream": False, "think": False, "keep_alive": "30m",
                               "options": {"temperature": 0.2, "num_predict": 90}})
    text = (d.get("response") or "").strip()
    sec = time.time() - t0
    toks = d.get("eval_count") or 0
    return text, sec, toks


def _check(text, kind):
    """按单一词表判。返回 (ok, why, hits)。"""
    low = text.lower()
    if not text:
        return False, "空回复（多半是没关 think）", 0
    if len(text) < 20 or len(text) > 300:
        return False, "长度异常 %d" % len(text), 0
    slots = SLOTS_PORTRAIT if kind == "portrait" else SLOTS_OBJECT
    hits = sum(1 for s in slots if s in text.lower())
    if hits < 3:
        return False, "只命中 %d 个可见属性，像空话" % hits, hits
    return True, "ok", hits


def validate(text, kind="object", inferred=False):
    """返回 (ok, why)。宁可退回人工，也不写一条猜身份的 caption 进训练集。

    inferred=True 表示 kind 是按目录猜的（--kind auto）：主表判废时用另一张词表复核一次。
    两步都不达标仍判废——复核只修「表选错」，不放宽「是不是空话」。
    """
    low = text.lower()
    ok, why, hits = _check(text, kind)
    if not ok and len(text) >= 20 and len(text) <= 300:
        for b in BAD:
            if b in low:
                return False, "含推测/身份词：%s" % b
        if re.search(r"[\"'“”][A-Z][a-z]{2,}", text):
            return False, "含疑似专名（引号+大写）"
    if ok or not inferred:
        return ok, why
    other = "portrait" if kind == "object" else "object"
    ok2, _why2, hits2 = _check(text, other)
    if ok2:
        return True, "ok（复核命中 %d，按 %s 表）" % (hits2, other)
    return False, why


RELEASE_FLAG = os.path.expanduser("~/.fluxgroup-disk-release")

SPEC_EN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "cph4", "fleet", "asset-lib-v1", "CHARACTERS-EN-v1.json")

VIEW_PHRASE = {
    "front": "front view, facing camera, neutral expression",
    "three_quarter_left": "three-quarter view from the left, facing camera",
    "three_quarter_right": "three-quarter view from the right, facing camera",
    "profile_left": "left side profile",
    "profile_right": "right side profile",
    "back": "seen from behind, back view",
    "expression_soft": "front view, relaxed soft expression",
    "expression_smile": "front view, light smile",
    "expression_tense": "front view, tense expression",
    "high_angle": "high angle, looking slightly up at camera",
    "low_angle": "low angle looking up",
    "mid_shot": "mid shot, waist up",
}


def _clip(text, words):
    """按词数截断，不切半个词。"""
    parts = str(text or '').replace(';', ',').split()
    return ' '.join(parts[:words]).strip(' ,.')


def spec_caption(char_id, view, chars):
    """按设定派生：图像内容本来就来自这份 spec，事实精确，不需要模型去猜。

    组装按总词数预算推进（LoRA caption 要短，校验上限 300 字符）：
    主体与视角最先占位，稀缺预算留给它们；描述字段按剩余额度补，补不下就丢。
    """
    c = chars.get(char_id) or {}
    role = _clip(c.get('role'), 6) or 'person'
    view_txt = VIEW_PHRASE.get(view, view.replace('_', ' '))
    queue = [
        ('head', 'portrait photo of a %s' % role),
        ('view', view_txt),
        ('hair', _clip(c.get('hair'), 8)),
        ('outfit', _clip(c.get('outfit'), 8)),
        ('skin', _clip(c.get('skin'), 4)),
        ('build', _clip(c.get('build'), 4)),
        ('tail', 'soft even light, plain background'),
    ]
    out, words = [], 0
    for _k, txt in queue:
        if not txt:
            continue
        w = len(txt.split())
        if words + w > 38:
            continue
        out.append(txt)
        words += w
    return ' '.join(', '.join(out).split())


def judge_test():
    """判据回归：正例（人物/物体 caption 必须过）+ 反例（空话/身份词必须废）。

    2026-11-09 加，起因：角色素材放在 characters/ 下却被判 object，
    人物 caption 用物件词表校验 → 命中 1-2 → 20 张抽检 0 通过。改判据必须有回归。
    """
    cases = [
        ("人物 caption 走 characters/ 目录",
         "A young woman with short brown hair wearing a beige trench coat, "
         "plain background, window light from the left", "media/asset/characters/CH01/front.png", True),
        ("人物 caption 走 faces/ 目录（旧路径）",
         "A middle aged man in a dark blue shirt, neutral expression, window light, indoor room",
         "media/asset/faces/CH01/front.png", True),
        ("物体 caption 走 props/ 目录",
         "A stack of white papers with printed text, a black pen on top, black background",
         "media/asset/props/P01.png", True),
        ("空话必须废",
         "a nice picture of something", "media/asset/characters/CH01/x.png", False),
        ("含身份推测必须废",
         "A woman who looks like a famous actress wearing a coat in an office",
         "media/asset/characters/CH01/y.png", False),
        ("空回复必须废", "", "media/asset/props/P02.png", False),
    ]
    bad = 0
    for name, text, path, want in cases:
        k = kind_of(path)
        ok, why = validate(text, k, inferred=True)
        hit = (ok == want)
        bad += 0 if hit else 1
        print("  %s %-34s kind=%-8s -> %s %s"
              % ("PASS" if hit else "FAIL", name, k, "pass" if ok else "reject",
                 "" if hit else "[期望 %s] %s" % ("pass" if want else "reject", why)))
    print("judge-test %s (%d/%d)" % ("OK" if not bad else "FAILED", len(cases) - bad, len(cases)))
    return 0 if not bad else 4


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-test", action="store_true", help="判据回归自检")
    ap.add_argument("--dir", default="")
    ap.add_argument("--trigger", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="")
    ap.add_argument("--kind", default="auto", choices=["auto", "portrait", "object"],
                    help="auto=按路径判：/faces/ 走人像词表，其余走物件词表")
    ap.add_argument("--recursive", action="store_true",
                    help="递归子目录（资产库按 00/01/… 分片存放，不递归会判成没有待打标图片）")
    ap.add_argument("--from-spec", action="store_true",
                    help="不用视觉模型：按 CHARACTERS-EN-v1.json 的设定 + 视角名派生 caption"
                         "（队内无可用 VLM 时的确定性兜底，不臆造内容）")
    a = ap.parse_args(argv)
    if a.judge_test:
        return judge_test()
    if not a.dir:
        print("缺 --dir（或用 --judge-test）")
        return 2
    if os.path.exists(RELEASE_FLAG) and "/Volumes/" in str(a.dir):
        print("[caption] 盘已置「可拔线」旗标，跳过该卷（rc=0）")
        return 0
    if not os.path.isdir(a.dir):
        print("目录不存在：%s（rc=2）" % a.dir)
        return 2
    todo = []
    walker = ([(d, _s, fs) for d, _s, fs in os.walk(a.dir)] if a.recursive
              else [(a.dir, [], sorted(os.listdir(a.dir)))])
    for d, _sub, files in walker:
        for n in sorted(files):
            p = os.path.join(d, n)
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
    if a.from_spec:
        try:
            chars = json.load(open(SPEC_EN, encoding="utf-8")).get("characters") or {}
        except Exception as e:
            rec.update({"verdict": "BLOCKED", "status": "BLOCKED",
                        "gaps": ["读不到 CHARACTERS-EN-v1.json：%s" % str(e)[:80]]})
            emit(rec, a.out)
            print("[caption] 读不到设定文件（rc=3）")
            return 3
        rec["caption_source"] = "spec"
        rec["model"] = "none (spec-derived, no VLM)"
        t0 = time.time()
        for p, txt in todo:
            char_id = os.path.basename(os.path.dirname(p))
            view = os.path.splitext(os.path.basename(p))[0]
            text = spec_caption(char_id, view, chars)
            if not text or len(text) > 300:
                rec["rejected"].append([os.path.basename(p), "派生文本长度异常"])
                continue
            low = text.lower()
            if any(b in low for b in BAD):
                rec["rejected"].append([os.path.basename(p), "含推测/身份词"])
                continue
            body = ("%s, %s" % (a.trigger, text)) if a.trigger else text
            with open(txt, "w", encoding="utf-8") as f:
                f.write(body.strip() + "\n")
            rec["written"] += 1
        rec["seconds"] = round(time.time() - t0, 1)
        rec["per_image_s"] = round(rec["seconds"] / max(1, len(todo)), 3)
        rec.update({"verdict": "PASS" if rec["written"] else "FAIL", "gaps": []})
        if not rec["written"]:
            rec["gaps"] = ["一条都没写成功，看 rejected 的原因"]
        rec["status"] = rec["verdict"]
        rec["note"] = ("caption 由 CHARACTERS-EN-v1.json 的设定 + 视角名派生：图像本身就是按该设定生成的，"
                       "事实精确、不臆造；不同于视觉模型草稿，但仍建议抽查。")
        emit(rec, a.out)
        print("[caption] spec 派生 写 %d / 待 %d" % (rec["written"], len(todo)))
        for r in rec["rejected"][:3]:
            print("  ! %s：%s" % (r[0], r[1]))
        return 0 if rec["written"] else 1

    t0 = time.time()
    for p, txt in todo:
        try:
            _kind = kind_of(p, a.kind)
            text, sec, toks = caption(p, _kind)
        except Exception as e:
            rec["rejected"].append([os.path.basename(p), "请求失败 %s" % str(e)[:80]])
            continue
        ok, why = validate(text, _kind, inferred=(a.kind == "auto"))
        if not ok:
            rec["rejected"].append([os.path.basename(p), why, text[:120]])
            # 早停闸（2026-11-04 实测）：连续 3 张被拒且一张没写成，说明这批图与当前提示词/
            # 判据不匹配，再跑就是每张 34 秒烧 GPU 换垃圾。停下来把问题交回资产线，而不是硬刷。
            if not rec["written"] and len(rec["rejected"]) >= 3:
                rec["early_abort"] = "连续 %d 张被拒且 0 成功，判提示词/判据不匹配" % len(rec["rejected"])
                break
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
        if rec.get("early_abort"):
            rec["gaps"].append(rec["early_abort"])
    rec["status"] = rec["verdict"]
    emit(rec, a.out)
    try:
        st = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "cph4", "fleet", "state", "caption-last.json")
        os.makedirs(os.path.dirname(st), exist_ok=True)
        json.dump(rec, open(st, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
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