# -*- coding: utf-8 -*-
"""C2168 closeout: sync 768P manifest to KN04 prompt v3.0, write the 480P verify
verdict, close the bank job and pre-stow the 768P wave job."""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PACK = os.path.join(HERE, "可爱女人-i2v-PACK-A-v1.json")
MAN768 = os.path.join(HERE, "local-i2v", "run-bmc-kn-i2v.json")
BANK = os.path.join(REPO, "cph4", "fleet", "work-bank", "bm-c-gpu-bank.json")
VERDICT = os.path.join(HERE, "KN-I2V-VERIFY480-VERDICT-20261024.md")

pack = json.load(io.open(PACK, encoding="utf-8"))
pu = [u for u in pack["units"] if u["id"] == "KN_A-KN04"][0]

# 1) 768P production manifest carries the same prompt the 480P slice verified
man = json.load(io.open(MAN768, encoding="utf-8"))
tgt = [u for u in man["units"] if u["id"] == "KN_A-KN04"]
assert len(tgt) == 1, "768 manifest KN04 count=%d" % len(tgt)
tgt[0]["i2v_prompt"] = pu["i2v_prompt"]
tgt[0]["prompt_words"] = pu["prompt_words"]
tgt[0]["prompt_rev"] = pu["prompt_rev"]
io.open(MAN768, "w", encoding="utf-8").write(json.dumps(man, ensure_ascii=False, indent=1))
print("768 manifest KN04 synced (rev %s, %d words)" % (pu["prompt_rev"], pu["prompt_words"]))

# 2) verdict document
md = u"""# KN i2v 480P 验证片闸 · 逐单判决（C2168 · 2026-10-24）

> 上游=C2167 站2 提示词闸签件（PROMPT-GATE-可爱女人-i2v-PACK-A-v1-SIGN.md，SIGN=条件 GO：先烧 480P 切片再放 768P 全量）。
> 本件=480P 切片实测判决书：通路=bmcverify 道（672x384 int4，出口 `media/mv-album-001-jay/clips-verify-480`，永不进正片）。
> 机械证据：三单 ffprobe 解码计帧全对；framemd5 逐帧哈希 175/362/209 帧全独占（dup=0，无定格无复读）；判读先原生 672x384 帧，多模态只作辅助。

## 一、第一轮（C2167 契约三单）

| 单 | 窗口 | 帧数 | 种子 | 判决 | 依据（原生帧） |
|---|---|---|---|---|---|
| KN21（近景·窗边停机） | 13.66s | 362 | 808997 | **GO** | 折纸形状稳定、红尾标记单点不增不减、窗光呼吸式微弱明灭、机位近静（首尾构图一致）；零复制帧 |
| KN22b（大远景·城碗） | 8.14s | 209 | 976266 | **GO** | 水塔钢腿/立面刚性不塌、晾衣绳不融天、城灯保持点状不涂抹；天空零人形幻影；运动只在灯光与空气 |
| KN04（掷出·动作） | 8.14s | 175 | 764880 | **FIX** | 0.3s 干净；3.9s 起天空被金色飘带/碎片群占满（模型幻觉装饰），纸机折边在中段塌成鸟形塌陷；素材保全 `_archive-c2167-verify/KN_A-KN04-FAIL-ribboncollapse.mp4` |

**KN04 归因**：动作句 "a white paper plane flashing up …" 的「快闪」暗示 + 长横向跟拍，在 int4 480P 上被模型翻译成「爆发粒子/飘带」+ 折叠变形。修法=正面重写（单只纸机·折边锐利·一条干净弧线·干净开阔黄昏天空），零否定词（过闸③）。

## 二、第二轮（v2.9 词面）

原生帧复核（0.3 / 1.5 / 2.8 / 4.2 / 5.5 / 6.9s）：金色飘带群**清零**，纸机折边锐利、红尾位对；但 4.2s 起背景水塔**复制成两座**——横向跟拍让模型凭空续出第二座塔。素材保全 `_archive-c2167-verify/KN_A-KN04-R2-twintower.mp4`。

**归因**：运镜块 "travels alongside the subject at the subject's own pace, easing with each step" 属「跟随步行」口径，横向位移大 → 背景重绘风险；且水塔未点名唯一性。

## 三、第三轮（v3.0 词面 = 定稿）

修法两条：①运镜改「起飞即托起·随它上升缓落」（无横向步行位移）；②水塔点名 `the one black corrugated-tin water tower standing on its steel legs below`（正面单数）。
原生帧复核（同六点）：**单塔全程唯一**、飘带零残留、折边稳定、手部随镜上升自然出画；175 帧全独占零复制。素材=`clips-verify-480/KN_A-KN04.mp4`（165s 烧成，280KB）。

## 四、判决

**GO — 768P 全量《可爱女人》PACK-A 30 单放行。**
- 已落到正身：`可爱女人-shots-v2.py` v3.0（KN04 动作句+运镜）；`可爱女人-i2v-PACK-A-v1.json` KN_A-KN04 `prompt_rev=v3.0-C2168b-480P-round2`；`local-i2v/run-bmc-kn-i2v.json` 同词同步（烧的就是验过的词）。
- 机械闸：lint(video) 零命中 + `preflight_gate.guard(kf_verified=True)` 空列表（三闸全绿）。
- 后续：768P 波（`--manifest run-bmc-kn-i2v.json`，lane bmc int8 1344x768）由银行任务 `kn-packA-i2v-768p-wave-c2168` 承载；烧完接帧级/剪辑闸。

**教训入库（本曲长期）**：i2v 词面里「快闪/爆发」类动词与「步行节奏跟随」运镜，放大模型幻觉的两种形态=装饰粒子群 / 背景复制；正面写法应为「一条干净弧线」+「点名唯一背景物」。
"""
io.open(VERDICT, "w", encoding="utf-8").write(md)
print("verdict written:", VERDICT)

# 3) bank: close the verify job, pre-stow the 768P wave
bank = json.load(io.open(BANK, encoding="utf-8"))
by_id = {j.get("id"): j for j in bank["jobs"]}
vj = by_id["kn-packA-i2v-480p-verify-c2167"]
vj["status"] = "done"
vj["done_ts"] = "2026-10-24T06:35:00"
vj["result"] = ("3/3 adjudicated by native frames + framemd5 (dup=0): KN21 GO, KN22b GO, "
                "KN04 FIX (golden ribbon swarm + fold collapse) -> prompt v2.9 (ribbons gone, water "
                "tower duplicated) -> prompt v3.0 (single tower, clean arc) re-burn PASS. "
                "Verdict = GO for the 768P 30-unit wave. Doc cph4/fleet/mv-album-001-jay/"
                "KN-I2V-VERIFY480-VERDICT-20261024.md")
if "kn-packA-i2v-768p-wave-c2168" not in by_id:
    bank["jobs"].append({
        "id": "kn-packA-i2v-768p-wave-c2168",
        "status": "pending",
        "priority": 65,
        "auth": "KN i2v 480P verify verdict GO (KN-I2V-VERIFY480-VERDICT-20261024) — the 768P wave is "
                "the station-3 deliverable of O-20261023-2325 for the 可爱女人 pack.",
        "require": {"files_at_least": []},
        "cmd": ["D:\\ComfyUI\\python_embeded\\python.exe",
                "K:\\Fluxgroup\\FluxGroup\\cph4\\fleet\\mv-album-001-jay\\local-i2v\\h3_i2v_album.py",
                "--repo", "K:\\Fluxgroup\\FluxGroup",
                "--lane", "bmc",
                "--manifest", "cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-i2v.json"],
        "log_out": "media/mv-album-001-jay/logs/kn_i2v_768p_wave.out.log",
        "log_err": "media/mv-album-001-jay/logs/kn_i2v_768p_wave.err.log",
        "note": ("KN 30-unit 768P production wave (1344x768 int8, first_frame = the C2166 signed KN frames, "
                 "prompt rev v3.0 for KN04 / v2.8-v2.9 for the rest). PASS gate = ALBUM LANE DONE ok=30 "
                 "fail=0 in the log tail. Long burn (~3h) => run via the self-healing loop; SKIP is "
                 "idempotent so a restart resumes. No native audio (CEO audio ban)."),
    })
io.open(BANK, "w", encoding="utf-8", newline="").write(
    json.dumps(bank, ensure_ascii=False, indent=1).replace("\n", "\r\n"))
print("bank updated: verify=done, 768p wave armed; jobs=%d" % len(bank["jobs"]))
print("CLOSEOUT OK")