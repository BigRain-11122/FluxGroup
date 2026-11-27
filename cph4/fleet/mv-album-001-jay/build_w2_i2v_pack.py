# -*- coding: utf-8 -*-
"""build_w2_i2v_pack.py — W2《可爱女人》i2v 提示词包 B（2026-10-20·H3 新语法）

读取 `可爱女人-shots-v2.py`（只读，不改），逐镜把旧 i2v 文本重写成 H3 语法：
  景别 + 方括号相机命令（最多两段：先动后静）+ 内容（含 PERF 微动作）+ 光（LIGHT7）+ 焦点（FOCUS）
术语与禁词走 `mv_prompt_upgrade.py` 的 lint_density，不另立词表。

产物：W2-I2V-PACK-B-20261020.md / .json
铁律：不改编剧、不改 KF 包、不编造镜头内容——每镜内容都能回溯到原脚本的 note/i2v 文本。
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, HERE)
import mv_prompt_upgrade as UP  # noqa: E402

SHOTS_PY = os.path.join(HERE, "可爱女人-shots-v2.py")
OUT_MD = os.path.join(HERE, "W2-I2V-PACK-B-20261020.md")
OUT_JSON = os.path.join(HERE, "W2-I2V-PACK-B-20261020.json")
PACK_DATE = "2026-10-20"

PREFIX = "Single continuous take at 24fps, 16:9. "

# 旧 i2v 的 motion 槽 → H3 方括号命令（单镜最多两段：先动后静）
CAM_MAP = {
    "static": ["static"],
    "slide": ["truck_l", "static"],
    "pushin": ["push", "static"],
    "pullout": ["pull", "static"],
    "track": ["track", "static"],
    "tiltup": ["tilt_u", "static"],
    "panr": ["pan_r", "static"],
    "hand": ["static"],          # 手持微晃=静机位的一种，不挂运动命令
    "cranedn": ["ped_d", "static"],
}

LIGHT_KEYS = ["roof_dusk", "roof_night", "city_bowl", "city_moon",
              "cloud_moon", "galaxy_gold", "warm_window", "streak"]

# ---------------------------------------------------------------------------
# 逐镜改写表（内容一律由原脚本 note/i2v 改写，不新增剧情）
#   kind: face=有脸/有人 | empty=空镜（纸机/城/银河/窗） | action=手部动作
#   perf: PERF 键（至少 1 个；按表演法减法治 ≤2 个微手势，KN09 沿用 PATCH 实样 3 拍）
#   focus: "shallow" 或 ("deep", near, far) —— deep 按 PATCH §三 KN02 先例换成镜内实词
# ---------------------------------------------------------------------------
SPEC = {
    "KN01": dict(kind="action", light_note="黄昏天台·手的顶部光",
                 base="His hands fold the white paper plane flat on the rooftop ledge, each crease pressed down in turn; the paper catches the last of the dusk light",
                 perf=["settle_back"], focus="shallow"),
    "KN02": dict(kind="face", light_note="黄昏天台·天的 180° 面光",
                 base="He stands among the strung clotheslines and the black tin water tower, his fringe lying flat over his eyebrows; the city bowl dim and warm below the parapet",
                 perf=["shoulders_settle", "settle_back"], focus="shallow"),
    "KN03": dict(kind="face", light_note="黄昏天台·边缘持机",
                 base="He holds the plane back by its tail at the parapet edge; the rising wind moves his fringe",
                 perf=["eyes_first"], focus="shallow"),
    "KN04": dict(kind="action", light_note="掷出·天台蓝调",
                 base="He releases the plane off the ledge, the water tower sliding past below as it climbs",
                 perf=["fingers_open"], focus="shallow",
                 size="A close-up at eye level on the hand and the plane"),
    "KN05": dict(kind="empty", light_note="银蓝月晕·探照光柱",
                 base="The white paper plane climbs through the silver-blue night over the city bowl, crossing between two pale searchlight pillars that hold thin and steady; the pillar light lays a soft edge along its wings",
                 perf=["settle_back"], focus=("deep", "paper plane", "searchlight pillars")),
    "KN06": dict(kind="empty", light_note="掠过屋顶升空",
                 base="The paper plane climbs past the last dark rooftops into deepening blue air, the street lights sinking below the frame as the camera rises with it",
                 perf=["settle_back"], focus=("deep", "climbing plane", "sinking street lights")),
    "KN07": dict(kind="empty", light_note="城碗全景·她的一窗暖",
                 base="The paper plane hangs small and high above the whole night city bowl; far below, one single rooftop window burns warm among the scatter of sodium lights",
                 perf=["settle_back"], focus=("deep", "paper plane", "single warm window")),
    "KN08": dict(kind="face", light_note="她的灯窗·唯一光源 40cm 纸罩灯泡",
                 base="She pauses inside the warm window light, the beaded bracelet at her wrist, the red-tipped paper plane resting on the ledge outside; the window light breathing softly as she stands still",
                 perf=["eyes_first"], focus="shallow"),
    "KN09": dict(kind="face", light_note="夜天台·城市上升反光",
                 base="He keeps his face tipped up to the first stars",
                 perf=["eyes_first", "mid_expression", "settle_back"], focus="shallow",
                 post="Only the city glow moves on his skin.",
                 size="A head-and-shoulders framing at eye level, gentle handheld sway"),
    "KN10": dict(kind="empty", light_note="城碗·宽弧回旋",
                 base="The paper plane carves a wide slow arc above the night city lights, its white wings flashing once as they cross a streetlamp flare; the skyline wheeling past behind",
                 perf=["settle_back"], focus=("deep", "white wings", "wheeling skyline")),
    "KN11": dict(kind="empty", light_note="城碗·迎面直飞（源文本自带散景）",
                 base="The paper plane flies nose-on toward the camera, its wings flexing once as it climbs; the night city reduced to soft circles of light behind it",
                 perf=["settle_back"], focus="shallow",
                 focus_note="源 i2v 明写「soft circles of light behind」＝散景，故用浅景深而非 deep"),
    "KN12": dict(kind="empty", light_note="城碗·两楼灯阵",
                 base="The paper plane threads between two lit apartment towers, warm windows sliding past both wingtips close to the paper; the gap opening again beyond",
                 perf=["settle_back"], focus=("deep", "tower windows on the left", "gap beyond")),
    "KN13": dict(kind="empty", light_note="城碗·全城上的一个点",
                 base="The paper plane holds as a single pale point high over the whole lit bowl of the city; the streets a slow warm drift far below",
                 perf=["settle_back"], focus=("deep", "pale point of the plane", "warm drift of the streets")),
    "KN14": dict(kind="empty", light_note="暖微光尾迹",
                 base="The paper plane holds a steady line through the night, trailing a faint warm shimmer; its white edge taking light softly from the city below",
                 perf=["settle_back"], focus=("deep", "lit paper edge", "tail of the shimmer")),
    "KN15": dict(kind="empty", light_note="云海月晕·穿云",
                 base="The paper plane punches up through a moving cloud layer, thin mist streaming off its wings; the grey breaking into blue as it breaks through",
                 perf=["settle_back"], focus=("deep", "mist off the wings", "blue break above")),
    "KN16": dict(kind="empty", light_note="云海月晕·极缓长镜",
                 base="The paper plane holds small above an endless moonlit cloud deck; the camera easing back until the halo of the moon fills the sky",
                 perf=["settle_back"], focus=("deep", "small plane", "haloed moon")),
    "KN17": dict(kind="empty", light_note="银河金带全景",
                 base="The whole arc of the warm gold star band arches across the ink-blue night, the star dust wheeling almost imperceptibly; the cloud deck a dark rim below the frame",
                 perf=["settle_back"], focus=("deep", "star dust", "dark cloud rim")),
    "KN18": dict(kind="empty", light_note="银河近景·星尘本体",
                 base="The star dust of the galaxy band fills the frame in close detail, fine warm points and pale currents drifting through deep blue-black; everything moving at the slowest breath",
                 perf=["settle_back"], focus=("deep", "nearest grain of dust", "pale current behind")),
    "KN19": dict(kind="empty", light_note="纸机漂进星流",
                 base="The paper plane drifts up into the stream of warm gold stars, its white paper warming to gold at the edges; the star field thickening around it",
                 perf=["settle_back"], focus=("deep", "warming paper edge", "thickening star field")),
    "KN20": dict(kind="empty", light_note="融化在银河（XF_T2 叠化源帧）",
                 base="The paper plane dissolves softly into the stream of warm gold stars, its silhouette thinning into light until only the fold lines remain as threads of star dust",
                 perf=["settle_back"], focus=("deep", "thinning silhouette", "star dust behind")),
    "KN20b": dict(kind="empty", light_note="星尘逆引力折拢成机",
                  content="The star dust draws back inward against its own drift and folds into the small sharp shape of a paper plane; then easing back to stillness at the top of its arc; the shape leans into a slow dive toward the city far below.",
                  perf=["settle_back"], focus=("deep", "folding dust", "city lights below")),
    "KN21": dict(kind="empty", light_note="红尾机停檐·窗灯",
                 base="The cream paper plane rests on the rooftop ledge beside the warm window, its red wing tip turned toward the light; the red tip taking the light as the window breathes",
                 perf=["settle_back"], focus=("deep", "red wing tip", "lit window pane")),
    "KN22a": dict(kind="empty", light_note="两天台隔城·她端",
                  base="A single far rooftop stands alone on one side of the night city bowl, one small warm light burning on its ledge; the streets a soft warm drift running away toward the far side of the city",
                  perf=["settle_back"], focus=("deep", "street edge", "lone rooftop light")),
    "KN22b": dict(kind="empty", light_note="两天台隔城·他端",
                  base="The rooftop sits on the near side of the night city bowl, the black corrugated-tin water tower and the strung clotheslines dark against the sky glow; the whole bowl of lights spread below the parapet",
                  perf=["settle_back"], focus=("deep", "tin water tower", "bowl of lights")),
    "KN23": dict(kind="face", light_note="他俯望·城碗低角光",
                 base="He sits on the rooftop edge with his elbows on his knees, looking across the whole night city; the bowl of lights below him",
                 perf=["shoulders_settle", "settle_back"], focus="shallow"),
    "KN24": dict(kind="face", light_note="她灯窗内初见·唯一露脸",
                 base="She stands inside the warm window light holding the red-tipped plane to her chest; the window light breathing",
                 perf=["eyes_first"], focus="shallow"),
    "KN25": dict(kind="empty", light_note="两灯之间的城",
                 base="The night city holds between the two rooftops, her one small warm window light lined up across the frame with the sodium glow of the city; the streets a slow warm drift far below",
                 perf=["settle_back"], focus=("deep", "rooftop window light", "sodium glow of the bowl")),
    "KN28": dict(kind="empty", light_note="她的红尾机升空",
                 base="The cream paper plane with its red wing tip lifts off from the warm rooftop window; the square of light falling away below it as it climbs into the night",
                 perf=["settle_back"], focus=("deep", "red wing tip", "falling square of window light")),
    "KN29": dict(kind="empty", light_note="双机航线交错",
                 base="The two small hand-folded planes, one white and one red-tipped, cross paths high above the night city, their thin notebook-paper wings catching the city light; both holding their line as they pass",
                 perf=["settle_back"], focus=("deep", "white wing", "red wing tip")),
    "KN30": dict(kind="empty", light_note="双机并排定格收",
                 base="The red-tipped plane settles onto the ledge beside the white one; the two planes come to rest side by side in the warm window light",
                 perf=["settle_back"], focus=("deep", "paper wings", "dim city glow")),
}

TAIL = ("Every motion eases in and settles out, in the quiet camera language of a 2000 Taiwanese music video. "
        "2000 Taiwanese telecine grade; black point lifted to 10-14 code with shadow detail kept, never crushed; visible 35mm film grain; skin lit only by the listed source, no fill light. "
        "Preserve the original color palette.")


def load_shots_module():
    spec = importlib.util.spec_from_file_location("kn_shots_v2", SHOTS_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_old_i2v(text, cm, old_tail):
    """把旧 i2v 还原成 (size_angle, motion_key, content)。只读，不改原串。"""
    if not text.startswith(PREFIX):
        raise ValueError("unexpected i2v prefix: %r" % text[:60])
    rest = text[len(PREFIX):]
    i = rest.rfind(old_tail)
    if i < 0:
        raise ValueError("tail not found")
    core = rest[:i].rstrip()
    size_angle, remainder = core.split("; ", 1)
    for key, mv in sorted(cm.items(), key=lambda kv: len(kv[1]), reverse=True):
        if remainder.startswith(mv):
            content = remainder[len(mv):].lstrip(". ").rstrip()
            return size_angle, key, content
    raise ValueError("motion slot not matched: %r" % remainder[:60])


def light_of(kf_text, LX):
    """从原 kf 文本反查光锚名——不靠人工猜测。"""
    hits = [k for k in LIGHT_KEYS if LX.LIGHT[k].capitalize() in kf_text]
    if len(hits) != 1:
        raise ValueError("light anchor resolve failed: %r" % hits)
    return hits[0]


def focus_clause(spec):
    f = spec["focus"]
    if f == "shallow":
        return UP.FOCUS["shallow"]
    _, near, far = f
    return "deep focus, both the near %s and the far %s resolved" % (near, far)


def build_content(spec):
    if "content" in spec:
        content = spec["content"]
    else:
        clauses = [spec["base"]] + [UP.PERF[k] for k in spec["perf"]]
        content = "; ".join(clauses) + "."
    post = spec.get("post")
    if post:
        content = content + " " + post
    return content


def build_prompt(shot, spec, light_key, mod):
    sid, t0, t1, speed, note, kf_p, old_i2v = shot
    size_angle, motion_key, old_content = parse_old_i2v(old_i2v, mod.CM, mod.I2V_TAIL)

    size_angle = spec.get("size", size_angle)
    cam = CAM_MAP[motion_key]
    content = build_content(spec)
    keep = UP.LIGHT7[light_key] + ". " + focus_clause(spec) + "."

    prompt = UP.h3_i2v(size_angle, cam, content, keep, tail=TAIL)
    return dict(shot_id=sid, t0=t0, t1=t1, speed=speed, note=note,
                kind=spec["kind"], light=light_key,
                old_content=old_content, prompt=prompt)


def main():
    mod = load_shots_module()
    if len(mod.NEW) != 30:
        raise SystemExit("expected 30 shots, got %d" % len(mod.NEW))

    rows = []
    for shot in mod.NEW:
        sid = shot[0]
        if sid not in SPEC:
            raise SystemExit("shot %s missing from SPEC" % sid)
        spec = SPEC[sid]
        light_key = light_of(shot[5], mod.LX)
        built = build_prompt(shot, spec, light_key, mod)
        lint = UP.lint_density(built["prompt"], spec["kind"])
        # 自证：PERF 微动作至少 1 个真的落在词面里
        perf_vals = [UP.PERF[k] for k in spec["perf"]]
        perf_in = [v for v in perf_vals if v.lower() in built["prompt"].lower()]
        problems = list(lint["problems"])
        if not perf_in:
            problems.append("perf_missing")
        built.update(terms=lint["terms"], hits=lint["hits"], banned=lint["banned"],
                     perf_in=len(perf_in), problems=problems, ok=not problems)
        rows.append(built)

    passed = [r for r in rows if r["ok"]]
    failed = [r for r in rows if not r["ok"]]
    avg_terms = sum(r["terms"] for r in rows) / float(len(rows))

    # ---------------- JSON ----------------
    payload = {
        "pack": "W2-I2V-PACK-B",
        "date": PACK_DATE,
        "track": "可爱女人 / mv-jay-02",
        "source": "可爱女人-shots-v2.py",
        "grammar": "h3_i2v(): size_angle + [bracket cam, max 2 segments: move-then-static] + content(PERF) + LIGHT7 + FOCUS",
        "gate": "mv_prompt_upgrade.lint_density (terms>=3, banned=0) + PERF landed>=1",
        "summary": {"total": len(rows), "pass": len(passed), "fail": len(failed),
                    "avg_terms": round(avg_terms, 2),
                    "failed_ids": [r["shot_id"] for r in failed]},
        "shots": [{"shot_id": r["shot_id"], "t0": r["t0"], "t1": r["t1"], "kind": r["kind"],
                   "prompt": r["prompt"], "terms": r["terms"], "pass": r["ok"]} for r in rows],
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # ---------------- MD ----------------
    L = []
    L.append("# 《可爱女人》W2 i2v 提示词包 B（%s·H3 新语法·可直接烧制）" % PACK_DATE)
    L.append("")
    L.append("> 来源：`可爱女人-shots-v2.py` 30 镜（只读，未改动）；语法件=`mv_prompt_upgrade.py`（h3_i2v / LIGHT7 / FOCUS / PERF / lint_density）。")
    L.append("> 结构：景别 ＋ 方括号相机命令（单镜最多两段：先动后静）＋ 内容（含 PERF 微动作）＋ 光（LIGHT7 七槽）＋ 焦点（FOCUS）。")
    L.append("> 闸：`lint_density` 术语数 ≥3、禁词 0；另加自证「PERF 微动作必须真的落在词面」。")
    L.append("> 铁律：不改剧本、不改 KF 包、不编造镜头内容——每镜内容均可回溯原脚本 note/i2v。")
    L.append("")
    L.append("## 总览")
    L.append("")
    L.append("| 项 | 数 |")
    L.append("|---|---|")
    L.append("| 镜数 | %d |" % len(rows))
    L.append("| 过闸 | %d |" % len(passed))
    L.append("| 未过 | %d |" % len(failed))
    L.append("| 平均术语数 | %.2f |" % avg_terms)
    L.append("| 最低术语数 | %d（%s） |" % (min(r["terms"] for r in rows),
                                          min(rows, key=lambda r: r["terms"])["shot_id"]))
    L.append("")
    L.append("镜型口径：`face`=有脸/有人（加 FOCUS shallow）｜`empty`=空镜（纸机/城/银河/窗，用 deep）｜`action`=手部动作（浅景深，同 PATCH §三 KN04 先例）。")
    L.append("")
    L.append("## 逐镜提示词")
    L.append("")
    for r in rows:
        flag = "PASS" if r["ok"] else "FAIL"
        L.append("### %s ｜%.2f-%.2fs｜速 %.2f｜%s｜术语 %d｜%s" %
                 (r["shot_id"], r["t0"], r["t1"], r["speed"], r["kind"], r["terms"], flag))
        L.append("")
        L.append("- 内容锚（原脚本 note）：%s" % r["note"])
        L.append("- 光锚：`%s`｜PERF 落地 %d 条｜命中术语：%s" %
                 (r["light"], r["perf_in"], ", ".join(r["hits"])))
        if r["problems"]:
            L.append("- **问题**：%s" % "; ".join(r["problems"]))
        L.append("")
        L.append("```")
        L.append(r["prompt"])
        L.append("```")
        L.append("")

    L.append("## 未过镜清单")
    L.append("")
    if failed:
        L.append("| 镜 | 术语数 | 原因 |")
        L.append("|---|---|---|")
        for r in failed:
            L.append("| %s | %d | %s |" % (r["shot_id"], r["terms"], "; ".join(r["problems"])))
    else:
        L.append("无。30 镜全部过闸（术语数 ≥3、禁词 0、PERF 落地 ≥1）。")
    L.append("")

    L.append("## 附录：四处口径说明（不改规则，只解释）")
    L.append("")
    L.append("1. **空镜的 PERF**：`mv_prompt_upgrade.PERF` 12 条全部是人形微动作，空镜里没有演员。为避免编造剧情，空镜统一取 `PERF[\"settle_back\"]`（收势静止）作为唯一克制微动作——它与 `h3_i2v` 自带尾句「Every motion eases in and settles out」同义，不新增戏；若某镜需要连续出画，导演可删该分句，其余不动。")
    L.append("2. **KN11 的焦点**：源 i2v 明写「soft circles of light behind it」，即散景。此处用 `FOCUS[\"shallow\"]` 而非空镜默认的 deep，属对源文本的服从；JSON 里 kind 仍记 `empty`。")
    L.append("3. **deep focus 的写法**：沿用 PATCH §三 KN02 先例，把 `FOCUS[\"deep\"]` 的空位换成该镜实词（near X / far Y），不写通用占位；术语统计里的 `deep` 只是 `deep focus` 的子串，不是第二个术语。")
    L.append("4. **词库原句里的域词**：LIGHT7 是逐字引用的，`roof_dusk` 句内写有「his face」、`warm_window` 句内写有「two metres from her」，落到空镜时会指到不在画的人。按铁律不改词库、不改规则，此处在包内如实标注：空镜烧制时导演可只删该分句，光锚其余参数不动。")
    L.append("")
    L.append("*构建脚本 `build_w2_i2v_pack.py` 为唯一生成源；本 md/json 为脚本产物，重跑可复现。*")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print("PACK B built | shots=%d pass=%d fail=%d | avg_terms=%.2f" %
          (len(rows), len(passed), len(failed), avg_terms))
    for r in rows:
        print("  %-6s %-6s terms=%d %s%s" % (r["shot_id"], r["kind"], r["terms"],
                                             "PASS" if r["ok"] else "FAIL",
                                             "" if r["ok"] else " -> " + "; ".join(r["problems"])))
    print("md  ->", OUT_MD)
    print("json->", OUT_JSON)
    if failed:
        print("FAILED IDS:", ",".join(r["shot_id"] for r in failed))


if __name__ == "__main__":
    main()