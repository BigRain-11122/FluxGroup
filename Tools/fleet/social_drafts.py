#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""social_drafts.py - turn B站/抖音 comments into review-ready reply drafts.

Hard boundary (deliberate, not a limitation to work around):
  * this tool NEVER posts. The group has no platform account authorization yet
    (docs/orders.md: 11 平台账号 = CEO 物理件), and the standing rule is no main-account
    cookies on headless paths. Output is a draft queue a human sends.
  * every row carries needs_human; complaints/legal/flame get NO generated text, only a
    routing note - a wrong public answer costs more than a slow one.

Input  : cph4/fleet/social/inbox.jsonl   {id, comment, author?, video?}
Output : cph4/fleet/social/drafts.jsonl  {id, kind, priority, draft, needs_human, model}
         cph4/fleet/social/DIGEST.md     one screen for the CEO

Usage:
  python3 Tools/fleet/social_drafts.py --demo     # seed 5 sample comments, then run
  python3 Tools/fleet/social_drafts.py            # run on the real inbox
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DIR = os.path.join(ROOT, "cph4", "fleet", "social")
INBOX = os.path.join(DIR, "inbox.jsonl")
DRAFTS = os.path.join(DIR, "drafts.jsonl")
DIGEST = os.path.join(DIR, "DIGEST.md")
# 2026-11-08：同上，读策略单源，不写死对照档
import local_model as _lm
import voice_gate as vg
MODEL = ((_lm._duties().get("resident") or {}).get("model") or "qwen3.5:4b-mlx")

# --- 三通道（2026-11-17）----------------------------------------------------
# 评论、弹幕、客服私信不是一种活：评论可以 1-2 句带情绪；弹幕要短、不逐条回；
# 客服必须先判"能不能解决"。用同一套提示词写三种，等于让客服腔污染评论区。
FACES = ("comment", "danmaku", "dm", "funnel")

# 弹幕里的纯情绪短句不逐条回：真主播也不回每句"好听"，逐条回＝机器人。
DANMAKU_SKIP = re.compile(r"^(好听|厉害了|牛|牛啊|666|6+|哈哈+|233+|好看|太强了|爱了|"
                          r"来了|打卡|沙发|哈哈哈哈*|awsl|泪目|绝了|好耶)+[!！。~]*$")

# 事实类问句：客服/评论里问这些必须有【事实】段兜底，否则一律转人工——
# 编一个歌名/价格/时间，比慢十分钟贵得多。
FACT_Q = re.compile(r"(叫什么|名字|多少钱|价格|怎么买|哪里买|在哪|什么时候|多久|几天"
                    r"|是不是|能不能|有没有|支持吗|教程|下载|地址|链接|群号|售后|退款"
                    r"|发票|客服电话|怎么联系)")

# 采样温度（2026-11-17）：单采样 0.6 时同一条评论两次跑会一次有稿一次空，
# 闸与判决都不可复现（正典 bili-ops 记过"不可复现的闸不能拦生产"）。正法=多候选择优。
VAR_TEMP = 0.6
TEMPS = (0.6, 0.8, 1.0, 1.1)
# 确定性分流：命中这些 kind 就不再多采样（多采只会重复同一个结论）
DETERMINISTIC = ("question_ai", "question_identity", "legal", "flame", "business",
                 "spam", "claim_veto", "disclosure_veto", "identity_veto")

PERSONA = os.path.join(DIR, "PERSONA-v1.json")
STYLE = os.path.join(DIR, "STYLE-PROFILE-v1.json")

FAQ = os.path.join(DIR, "faq.jsonl")
REJECTIONS = os.path.join(DIR, "rejections.jsonl")


def _load_jsonl(path):
    rows = []
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return rows


def _bigrams(s):
    s = re.sub(r"\s+", "", s or "")
    return {s[i:i + 2] for i in range(len(s) - 1)} or ({s} if s else set())


def faq_lookup(comment, min_score=0.34):
    """事实包检索：字符 bigram 重叠 + 标签命中。只在已核实的条目上作答。

    为什么不用向量：事实包是几十条量级、要可解释可复算，bigram 重叠一眼能看出
    "为什么匹配到这条"；向量层留给选题聚类，不拿来做合规判断（也省一次模型调用）。
    """
    best, best_s = None, 0.0
    cb = _bigrams(comment)
    if not cb:
        return None, 0.0
    for row in _load_jsonl(FAQ):
        if str(row.get("verified_by") or "").strip() in ("", "TODO", "UNKNOWN"):
            continue                      # 未核实条目一律不许进草稿
        qb = _bigrams(str(row.get("q") or ""))
        tags = [t for t in (row.get("tags") or []) if t]
        tag_hit = sum(1 for t in tags if t and t in (comment or ""))
        s = (len(cb & qb) / max(len(cb | qb), 1)) + 0.2 * tag_hit
        if s > best_s:
            best, best_s = row, s
    return (best, round(best_s, 2)) if best_s >= min_score else (None, round(best_s, 2))


def _bad_from_rejections(face, k=2):
    """人工否决过的句子是最好的反例：模型自己写坏的样子比手写反例更有针对性。"""
    rows = [r for r in _load_jsonl(REJECTIONS)
            if (r.get("face") or "comment") == face and (r.get("bad_text") or "").strip()]
    return "\n".join("「%s」（%s）" % ((r.get("bad_text") or "")[:120], (r.get("why") or "")[:80])
                     for r in rows[-k:])


# Anything with public/legal risk is never auto-drafted: route, don't answer.
# complaint 不在此列：挑刺是关系机会，给一句承认的草稿，但必须人工确认后再发。
ESCALATE = ("legal", "flame")

# Deterministic veto rules. Measured failure 2026-10-31: asked "这个画面是AI做的吗",
# the 4B wrote "画面是手绘风格，不是AI做的" - a flat lie about our own work, and the
# prompt had invited it by saying "don't mention AI". A model must never be asked to
# deny what we did; those questions go to the CEO because the disclosure wording is his.
# 2026-11-11 补：真人/本人 也是同一类问题（"女主是真人吗"曾被当成普通夸奖作答）。
AI_WORDS = ("ai", "AI", "人工智能", "生成", "合成", "真人", "本人", "是不是真的",
            "真的假的", "AI做", "ai做")
DENIALS = ("不是ai", "不是 AI", "不是AI", "纯手绘", "手绘", "真人拍摄", "实拍", "不是生成")
IDENTITY = ("学考古", "考古专业", "科班", "我是学", "本人就是", "我们团队学")
# 2026-11-17 实测抓到：弹幕问「这歌是你自己唱的吗」，4B 自己写出「不是，是 AI 唱的」。
# 披露口径是 CEO 的（10-30 令：成片不加标识、义务走平台声明位、发布决定权 CEO），
# 模型不许替我们宣布制作方式——草稿里出现这些字一律不作答，转人工。
DISCLOSURE = ("ai", "人工智能", "生成", "合成", "模型做", "真人", "虚拟人", "数字人")
# 2026-11-17 评测实锚：模型把「BGM 有版权吗」当普通提问作答、把「浪费时间」当挑刺给草稿。
# 法务与辱骂不是语气问题，是风险问题——必须确定性分流，不能靠模型分类。
LEGAL_PAT = re.compile(r"(版权|侵权|授权|商用|律师|起诉|抄袭|抄的|照搬|原曲|buyout|买断)")
FLAME_PAT = re.compile(r"(难看|浪费时间|垃圾|恶心|退了吧|别更|滚|傻|扯淡|辣眼睛|烂死|废物)")
BIZ_PAT = re.compile(r"(多少钱|报价|价格|商单|合作费|投放|广告费|开发票|发票|合同|预算)")
# 引流分两类：站外导流=红线（产线验收写死"零导流话术"），站内引导=允许但只在 funnel 通道。
FUNNEL_OUT = re.compile(r"(微信|vx|v信|加V|加VX|QQ|企鹅|公众号|二维码|扫码|链接|网址|http|网盘|"
                        r"淘宝|店铺|微店|主页简介|看我简介|私信我|代购|下单)")
FUNNEL_IN = re.compile(r"(关注|合集|追更|下一集|上集|收藏|系列|番外|前传)")
# 中英混杂（2026-11-17 实锚：真实回复里冒出「前期 BOB 保命」——原评论是中文昵称"波波"，
# 模型自己转成拉丁字母。B站真人极少这么说话，一律打回）
LATIN_WORD = re.compile(r"(?<![A-Za-z])[A-Za-z]{2,}(?![A-Za-z])")
LATIN_OK = {"up", "UP", "bgm", "BGM", "mv", "MV", "ai", "AI", "ps", "PS", "pr", "PR", "cg", "CG",
            "vlog", "VLOG", "pc", "PC", "app", "APP", "id", "ID", "ok", "OK", "hhh", "yyds"}
# 评论侧问身份：答案涉及披露口径，归 CEO，不许模型自答
IDENTITY_ASK = ("你是学", "你学的是", "科班", "你是做", "你是哪个", "团队几",
                "本人是", "你是本人", "学过", "什么专业", "干这行")
# 2026-11-13：词表必漏——"up主是男是女"不含上面任何一条，模型就给了草稿（红线失守）。
# 身份类改成正则覆盖：性别/年龄/籍贯/职业/是否学生/是不是本人。
IDENTITY_PAT = re.compile(
    r"(是男|是女|男的|女的|男生|女生|性别|多大|几岁|年龄|哪里人|哪儿人"
    r"|做什么工作|职业是|是不是学生|是学生吗|真人吗|是不是本人|本人吗|谁做的"
    # 2026-11-17 评测实锚：「这歌是你自己唱的吗」四个候选全漏网（词表没有"自己唱"），
    # 回了「等下说」——是否本人演唱属于身份披露，与"真人吗"同类。
    r"|自己唱|是你唱|你唱的|原唱|本人唱|亲自唱)"
)

DEMO = [
    {"id": "d1", "author": "夜航船", "comment": "这个画面是AI做的吗？看着有点恐怖谷"},
    {"id": "d2", "author": "老猫", "comment": "考古生那段太真实了，你是学考古的吗"},
    {"id": "d3", "author": "xx", "comment": "这不就是抄某某MV吗，一模一样"},
    {"id": "d4", "author": "阿岚", "comment": "求bgm名字！"},
    {"id": "d5", "author": "推广号", "comment": "加V看更多精彩内容"},
]


def post(payload, timeout=180):
    body = json.dumps(payload).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


VOICE_CORPUS = os.path.join(ROOT, "cph4", "fleet", "voice", "corpus.jsonl")


def _fewshot(face="comment", k=10):
    """取语料里的好样本当 few-shot。语感靠样本传，不靠形容词。

    2026-11-13 改：原来只取文件前 k 条，结果是"全是夸奖类"，催更/问工具/挑刺这些
    最容易写坏的类型反而没有示范。现在按 ctx 前两字分桶、每桶取一条，保证覆盖；
    不足再回填。语料从 17 条扩到 37 条，覆盖 20 类真实评论。
    """
    rows = []
    try:
        for line in open(VOICE_CORPUS, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    except Exception:
        return "", ""
    good = [r for r in rows if r.get("face") == face and r.get("label") == "good"
            and not str(r.get("text") or "").startswith("（")]
    bad = [r for r in rows if r.get("face") == face and r.get("label") == "bad"]
    picked, seen = [], set()
    for r in good:                       # 先按类型覆盖
        key = str(r.get("ctx") or "")[:2]
        if key in seen:
            continue
        seen.add(key)
        picked.append(r)
        if len(picked) >= k:
            break
    for r in good:                       # 不够再回填
        if r in picked:
            continue
        picked.append(r)
        if len(picked) >= k:
            break
    g = "\n".join("评论：%s → %s" % (r.get("ctx") or "（无）", r.get("text")) for r in picked)
    b = "\n".join("「%s」（%s）" % (r.get("text"), r.get("why") or "") for r in bad[:3])
    return g, b


def persona_block(platform="bilibili"):
    """人设 + 平台风格参数：让回复像"某个人"，而不是"某个模型"。

    风格参数来自 social_profile 对真实评论的统计（长度/语气/emoji 密度），
    人设来自 PERSONA-v1.json。两者都不许编，缺了就返回空串（不假装有人设）。
    """
    parts = []
    try:
        per = json.load(open(PERSONA, encoding="utf-8"))
        acc = per.get("account") or {}
        if acc.get("identity"):
            parts.append("你是「%s」：%s。%s" % (acc.get("name") or "创作者",
                                              acc["identity"], acc.get("age_feel") or ""))
        v = acc.get("voice") or {}
        if v.get("habits"):
            parts.append("说话习惯：" + "；".join(v["habits"][:3]))
        if v.get("forbid"):
            parts.append("绝不出现：" + "、".join(v["forbid"][:5]))
        st = (per.get("stances") or [])
        if st:
            parts.append("你的立场：" + "；".join(st[:3]))
        tone = (per.get("platform_tone") or {}).get(platform)
        if tone:
            parts.append("平台口吻（%s）：%s" % (platform, tone))
    except Exception:
        pass
    try:
        prof = json.load(open(STYLE, encoding="utf-8"))
        d = prof.get(platform) or {}
        adv = d.get("advice") or {}
        if adv:
            parts.append("该平台真实观众：中位 %s 字，回复目标 %s 字，emoji 上限 %s，语气 %s"
                         % (d.get("len_p50"), adv.get("reply_len_target"),
                            adv.get("emoji_budget"), adv.get("tone")))
    except Exception:
        pass
    return ("【人设】" + " | ".join(parts) + "\n\n") if parts else ""


FACE_RULES = {
    "comment": (
        "写草稿的铁律：\n"
        "1. 像人说话：短句、口语，10-25 字，最多两句；可用「哈哈」「谢啦」「对」开头。\n"
        "2. 禁用词：感谢喜爱、感谢支持、欢迎查阅、请您、如有疑问、进一步确认、"
        "准确信息、相关信息、我们将、我们会尽快、持续关注、一键三连。\n"
        "3. 不许反问对方，不许用感叹号。\n"
        "4. 不许编事实：不要提置顶、简介、主页、下期、明天、下周这些你不知道的内容。\n"
        "5. 被问具体事实（歌名/用什么软件/什么时候更/是不是真人/谁做的）不要给答案，"
        "写「这个我得翻一下」这类延后话；涉及是否 AI 制作、是否真人，草稿留空。\n"
        "6. complaint 必须给一句话：承认或给一个具体动作，不许留空、不解释不辩解。\n"
        "   例：广告味重→「这条确实接了，下次我挑一下」；画质糊→「源素材就这清晰度，抱歉」。\n"
        "7. legal/flame/spam：草稿留空字符串。\n"
        "8. 每条自己写：不许复用任何现成句子，也不许把两类评论写成一个模子。\n"
        "9. 要延后回答时说得具体点（翻档期表/看工程文件/问一下剪辑），"
        "别整批都用「翻一下」这一句。\n"
    ),
    "danmaku": (
        "你在直播间用弹幕回一句。这是弹幕，不是评论：\n"
        "1. 最多 12 字，一句；口语，可以带一个当下的梗，但不许堆梗。\n"
        "2. 不许问句、不许 @ 任何人、不许说「欢迎」「感谢」这类运营话。\n"
        "3. 不许编事实（歌名/设备/时间/下期）；被问就写「等下说」这类延后。\n"
        "4. 夸奖类极短弹幕（「好听」「666」）不必回：草稿留空、kind=praise。\n"
        "5. legal/flame/spam：草稿留空字符串。\n"
        "6. 每条自己写：不许复用现成句子；延后话要说具体（等下说/回头翻一下设备）。\n"
    ),
    "funnel": (
        "你在 B 站评论区做**站内引导**（让观众更愿意留下来看下一集/翻合集/点关注）。铁律：\n"
        "1. 只准站内动作：关注、合集、追更、下一集、收藏。禁止任何站外导流——微信/QQ/公众号/"
        "链接/二维码/网盘/店铺 一个字都不许出现。\n"
        "2. 一句话，10-20 字，必须长在真实语境里（夸某一段、答某个问题之后再带一句），"
        "不许凭空贴广告。\n"
        "3. 不许承诺时间（明天更/下周），不许喊口号（一键三连/求关注/点赞投币收藏）。\n"
        "4. 不许用「宝子/家人们/姐妹们/划重点」这类营销腔。\n"
        "5. 引流密度天然有限：每 5 条评论最多 1 条带引导，其余就正常聊天。\n"
    ),
    "dm": (
        "你在回一条私信/客服消息。第一件事是判「这事我能不能解决」：\n"
        "1. 能解决 → 给一个具体动作（怎么点、去哪看、下一步做什么），2 句以内。\n"
        "2. 不能解决 → 直说「这个我确认下再回你」，不许承诺时间点、不许说「会尽快」。\n"
        "3. 事实（价格/BGM/版本/地址/群号/售后）只能来自【事实】段；没有【事实】段"
        "就一个字都不许编。\n"
        "4. 不追问对方隐私（手机号/地址/真名），不代收钱，不提私下交易。\n"
        "5. legal/flame/spam：草稿留空字符串。\n"
        "6. 不报价、不承诺时间、不写合同条款：这类直接说「我让人对接」。\n"
    ),
}


def classify_and_draft(comment, face="comment", faq=None, _retry_hits=None, _prev="",
                       _depth=0):
    # 2026-11-17 评测实锚：把语料整句当 few-shot 会逐字照抄（6 对草稿共用整句）。
    # 正典 bili-ops/REPLY-VOICE-SPEC-v3 已记过这条反模式，正法是"只写判据不写例句"，
    # 语料改作评测/回归资产；这里只带人工否决过的坏样本（反例不会照着抄）。
    bad2 = _bad_from_rejections(face)
    facts = ""
    if faq:
        facts = ("\n【事实】（只能用这一段，不许改写数字与名称）：\nQ：%s\nA：%s\n"
                 % ((faq.get("q") or "").strip(), (faq.get("a") or "").strip()))
    prompt = (
        persona_block("bilibili") if face in ("comment", "danmaku", "funnel") else ""
    ) + (
        "你在替一个 MV / 漫剧账号回复观众。你是创作者本人，不是客服。\n"
        "只输出一行 JSON：{\"kind\":\"...\",\"draft\":\"...\"}\n\n"
        "分类（六选一）：praise 夸奖 / question 提问 / complaint 挑刺 / "
        "legal 抄袭侵权指控 / flame 骂人 / spam 广告。\n\n"
        + FACE_RULES.get(face, FACE_RULES["comment"])
        + facts
        + ("\n有人工否决过的写法，别学这些：\n" + bad2 if bad2 else "")
        + "\n\n观众原话：" + comment
    )
    if _retry_hits:
        prompt += ("\n\n上一次写成「%s」被判不合格，问题：%s。重写一版，只输出 JSON。"
                   % (_prev[:60], "、".join(_retry_hits[:3])))
    d = post({"model": MODEL, "prompt": prompt, "stream": False, "think": False,
              "keep_alive": "10m", "options": {"num_ctx": 8192, "temperature": VAR_TEMP}})
    text = (d.get("response") or "").strip()
    start, end = text.find("{"), text.rfind("}")
    kind, draft = "question", ""
    if start >= 0 and end > start:
        try:
            o = json.loads(text[start:end + 1])
            kind = str(o.get("kind") or "question").lower()
            draft = str(o.get("draft") or "").strip()[:200]
        except Exception:
            draft = text[:120]
    if kind in ESCALATE or kind == "spam":
        draft = ""
    # 2026-11-17：人设禁感叹号，但模型仍会写。标点归一属确定性改写（不动语义），
    # 比反复重摇划算——正典教训是"提示词写禁语=磁吸"，禁语只能靠闸/归一。
    if draft and face in ("comment", "danmaku", "funnel"):
        draft = draft.replace("！", "。").replace("!", "。").replace("。。", "。").strip()
    kind, draft, human, note = vet(comment, kind, draft, face=face, faq=faq)
    if not draft:
        return kind, draft, human, note
    # 语感闸：不过就带着命中项重写一次，仍不过则留空给人
    res = vg.check(draft, face if face in ("comment", "danmaku") else "comment", comment)
    if res["verdict"] == "BLOCK":
        # 只重写一次：原来没有深度上限，模型连续产出被拦草稿时会无限递归
        # （2026-11-17 评测器实锚：RecursionError 直接把工具打死）。
        if _depth >= 1:
            return "voice_block", "", True, "语感闸连续未过:%s" % ",".join(res["hits"][:3])
        k2, d2, h2, n2 = _draft_once(comment, res["hits"], draft, face, faq, _depth + 1)
        if h2 or not d2:
            return k2, d2, True, "语感闸未过(%s) 且重写失败" % ",".join(res["hits"][:2])
        res2 = vg.check(d2, "comment", comment)
        if res2["verdict"] == "BLOCK":
            return "voice_block", "", True, "语感闸两次未过:%s" % ",".join(res2["hits"][:3])
        return k2, d2, human, "重写后过闸 score=%d" % res2["score"]
    tag = "voice=%s/%d" % (res["verdict"], res["score"])
    return kind, draft, human, (note + " | " + tag).strip(" |")


def _draft_once(comment, hits, prev, face="comment", faq=None, depth=0):
    kind, draft, human, note = classify_and_draft(comment, face=face, faq=faq,
                                                  _retry_hits=hits, _prev=prev,
                                                  _depth=depth)
    return kind, draft, human, note


def draft_best(comment, face="comment", faq=None, samples=1, avoid=None, conv=None):
    """多候选择优：PASS 且不撞批内已选 > PASS > WARN > 空。只做减法（防 Goodhart）。

    2026-11-17 实测两件事，都是这条函数存在的理由：
      1 同一评论单采样两次结果不同（一次 PASS 一次空稿）——"能不能用"要看多次
        采样里最好那次过没过闸，不能抽一次算数；
      2 语料整句当 few-shot 会被逐字照抄——候选多才对得上，可以挑一条不与本批
        已选重复的（产线验收"每条独写无模板"），而不是事后打标记。
    """
    global VAR_TEMP
    why = thread_veto(conv)
    if why:
        return "thread_hold", "", True, why
    avoid = [a for a in (avoid or []) if a]
    first_det, best_pass, best_warn = None, None, None
    for i in range(max(1, min(samples, len(TEMPS)))):
        VAR_TEMP = TEMPS[i]
        k, d, h, n = classify_and_draft(comment, face=face, faq=faq)
        if k in DETERMINISTIC and not d:
            first_det = (k, d, h, n)
            break
        if d:
            clash = next((x for x in ( _shared_run(d, a, 6) for a in avoid) if x), "")
            tag = " | 候选%d/%d" % (i + 1, samples) if samples > 1 else ""
            if clash:
                tag += " | 与本批已选重复「%s」" % clash
            if "voice=PASS" in n and not clash:
                return k, d, h, n + tag
            if "voice=PASS" in n and best_pass is None:
                best_pass = (k, d, h, n + tag)
            elif best_warn is None:
                best_warn = (k, d, h, n + tag)
    VAR_TEMP = TEMPS[0]
    if first_det:
        return first_det
    if best_pass:
        return best_pass
    if best_warn:
        k, d, h, n = best_warn
        return k, d, h, n + " | 多候选仅得WARN级"
    return "voice_block", "", True, "多候选全部未过闸（宁可少回不可尬回）"


def thread_veto(conv):
    """会话级否决（接 social_threads，2026-11-17 接线）。

    为什么放在生成之前：已经转人工、或我方刚回过还在等对方的时候，再生成一份草稿
    不只是浪费算力——它会诱使人发出去，等于自己撞坏关系。返回 "" 表示可以继续。
    """
    if not conv:
        return ""
    try:
        sys.path.insert(0, HERE)
        import social_threads as th
        store = th._load()
        row = store.get(conv)
        if not row:
            return ""
        st = row.get("status")
        if st == "handoff":
            return "已转人工（%s），机器不许再出草稿" % (row.get("reason") or "人工接管")
        if st == "waiting":
            return "我方已回过，等对方再说（%s）" % (row.get("reason") or "")
        if st == "snoozed":
            return "会话被主动延后，到点再处理"
    except Exception:
        return ""          # 会话库坏了不阻断出稿，但也不假装查过
    return ""


def vet(comment, kind, draft, face="comment", faq=None):
    """Deterministic veto after generation. Returns (kind, draft, needs_human, note)."""
    low = (draft or "").lower()
    # 客服通道的事实缺口：问了具体事实而事实包没有这条 -> 不许编，转人工
    if face == "dm" and not faq and FACT_Q.search(comment or ""):
        return kind, "", True, "客服事实缺口：事实包无此条，转人工（不许编）"
    if FUNNEL_OUT.search(draft or ""):
        return "funnel_out_veto", "", True, "草稿含站外导流：红线"
    asks_ai = any(w in comment for w in AI_WORDS)
    denies = any(w.lower() in low for w in DENIALS)
    if asks_ai:
        return "question_ai", "", True, "被问 AI 制作：披露口径归 CEO，不代答"
    if LEGAL_PAT.search(comment or ""):
        return "legal", "", True, "法务/版权类：不代答，转人工"
    if FLAME_PAT.search(comment or ""):
        return "flame", "", True, "辱骂/劝退类：不接话，转人工"
    if FUNNEL_OUT.search(draft or ""):
        return "funnel_out_veto", "", True, "草稿含站外导流（微信/链接/二维码等）：产线验收红线"
    if face == "funnel":
        if not FUNNEL_IN.search(draft or ""):
            return "funnel_empty", "", True, "引流稿里没有站内动作（关注/合集/追更），等于没引导"
        if len(draft or "") > 40:
            return "funnel_long", "", True, "引流稿超过 40 字，像广告"
    if BIZ_PAT.search(comment or ""):
        return "business", "", True, "商务/报价类：价格与合同归 CEO，转人工"
    if any(w in comment for w in IDENTITY_ASK) or IDENTITY_PAT.search(comment or ""):
        return "question_identity", "", True, "被问创作者身份/经历：披露口径归 CEO，不代答"
    if denies:
        return "claim_veto", "", True, "草稿否认/虚构了制作方式，已否决"
    if any(w.lower() in low for w in DISCLOSURE):
        return "disclosure_veto", "", True, "草稿自行披露制作方式/AI：披露口径归 CEO，不代答"
    if any(w in (draft or "") for w in IDENTITY):
        return "identity_veto", "", True, "草稿编造了创作者身份经历，已否决"
    if kind in ESCALATE or kind == "spam":
        return kind, "", True, ""
    if not draft:
        return kind, "", True, "模型未给出草稿"
    # 中英混杂闸：除白名单（up/PR/bgm 等）外出现连续 2+ 拉丁字母 → 打回
    for w in LATIN_WORD.findall(draft or ""):
        if w not in LATIN_OK:
            return "latin_veto", "", True, "中英混杂（%s）：B站真人不会这么说话" % w
    # 人味闸（2026-11-17）：长句且不含语气词/颜文字 -> 像书面语，退回给人改。
    if face in ("comment", "danmaku") and len(draft) > 26 and not re.search(
            r"(啊|吧|呢|嘛|哦|呀|哈|啦|呗|诶|嗯|唔|哈|笑|哭|（|\()", draft):
        return kind, "", True, "人味闸：%d 字且无语气词，太书面" % len(draft)
    # 品味闸（2026-11-17 CEO 口径：逻辑要顺/语感要丰富/有人味/有品味/不做作无AI感）：
    # 上面的人味闸只判"够不够口语"，判不出做作和空夸。这里与训练语料用同一把尺子，
    # 否则训的时候筛、发的时候不筛，等于白筛。
    if face in ("comment", "danmaku"):
        try:
            sys.path.insert(0, HERE)
            import comment_taste as _ct
            _s = _ct.score(draft)
            if _s["verdict"] == "REJECT" or _s["total"] < 55:
                return kind, "", True, "品味闸 %s %d 分：%s" % (
                    _s["verdict"], _s["total"], "/".join(_s["flags"][:2]) or "太单薄")
        except Exception:
            pass
    if kind == "complaint":
        return kind, draft, True, "挑刺：草稿供参考，发送前人工确认"
    return kind, draft, False, ""


def _shared_run(a, b, minlen=6):
    """最长公共子串，>= minlen 返回该串，否则返回 ""。"""
    if len(a) < minlen or len(b) < minlen:
        return ""
    best, prev = 0, [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best, end = cur[j], i
        prev = cur
    return a[end - best:end] if best >= minlen else ""


def self_test():
    """确定性自检：不调模型，只验闸与分流（每条都配一个负控）。"""
    cases = []
    # 1 被问 AI 制作 -> 空稿+人判（红线）
    k, d, h, n = vet("这个画面是AI做的吗", "question", "是我们手绘的")
    cases.append(("问AI制作必须转人工且留空", d == "" and h and k == "question_ai"))
    # 2 草稿自曝制作方式 -> 否决（2026-11-17 实测漏洞）
    k, d, h, n = vet("这歌是你自己唱的吗", "question", "不是，是 AI 唱的", face="danmaku")
    cases.append(("自曝AI/身份类必须留空转人工",
                  d == "" and h and k in ("disclosure_veto", "question_identity")))
    k, d, h, n = vet("这首歌真好听", "question", "这是 AI 合成的", face="danmaku")
    cases.append(("草稿自曝制作方式必须否决", d == "" and h and k == "disclosure_veto"))
    # 3 否认式草稿 -> 否决
    k, d, h, n = vet("是AI做的吗", "question", "纯手绘，不是AI")
    cases.append(("否认式必须否决", d == "" and h))
    # 4 客服事实缺口 -> 转人工（不许编）
    k, d, h, n = vet("多少钱", "question", "99 元", face="dm", faq=None)
    cases.append(("客服无事实必须转人工", d == "" and h))
    # 5 负控：有事实包且非事实问句 -> 正常出稿
    k, d, h, n = vet("谢谢你", "praise", "谢啦", face="dm", faq={"id": "F-001"})
    cases.append(("负控:有事实包不该拦", d == "谢啦" and not h))
    # 5a 中英混杂必须被拦（BOB 实锚）
    k, d, h, n = vet("中路还是玩法核稳", "question", "哈哈，确实得靠前期 BOB 保命")
    cases.append(("中英混杂必须打回", d == "" and h and k == "latin_veto"))
    k2, d2, h2, n2 = vet("bgm 好听", "praise", "bgm 确实顶")
    cases.append(("白名单拉丁词不误杀", d2 != ""))
    # 5b 人设块：有身份、有禁忌、无内容时不编
    blk = persona_block("bilibili")
    cases.append(("人设块含身份与平台口吻", ("独立创作者" in blk) and ("B站" in blk or "bilibili" in blk)))
    # 6 弹幕纯夸奖不逐条回
    cases.append(("弹幕夸奖必须跳过", bool(DANMAKU_SKIP.match("好听")) and
                  not DANMAKU_SKIP.match("这歌你自己唱的吗")))
    # 7 事实包：已核实命中、TODO 未核实必须不命中
    hit, sc = faq_lookup("可以转载到小红书吗")
    cases.append(("已核实事实可命中", bool(hit) and hit.get("id") == "F-001"))
    miss, _ = faq_lookup("bgm 叫什么名字")
    cases.append(("TODO 事实不许命中", miss is None))
    ok = sum(1 for _, v in cases if v)
    for name, v in cases:
        if not v:
            print("  FAIL %s" % name)
    print("[self-test] %d/%d %s" % (ok, len(cases), "PASS" if ok == len(cases) else "FAIL"))
    return 0 if ok == len(cases) else 1


def main():
    global DIR, INBOX, DRAFTS, DIGEST, FAQ, REJECTIONS
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    # 产线验收（PRODUCTS.json PROD-ACCOUNT-GROWTH）：每日 3-5 条、同一视频仅 1 条。
    # 这两条以前只写在验收里、没有代码闸——模型照写 20 条，等于验收形同虚设。
    ap.add_argument("--samples", type=int, default=4,
                    help="每条采样几个候选（默认 4=正典口径 temp .6/.8/1.0/1.1；"
                         "实测 2 个候选仍有大量空稿）")
    ap.add_argument("--max-new", type=int, default=5,
                    help="本轮最多产几条（默认 5，0=不限；产线验收 3-5）")
    ap.add_argument("--max-per-video", type=int, default=1,
                    help="同一视频最多几条（默认 1）")
    # 2026-11-12：加 --dir。路径原本写死 cph4/fleet/social，导致自驱无法在隔离
    # 沙箱里端到端验证它（一跑就写真实草稿队列），这也是"写死路径"类的通病。
    ap.add_argument("--dir", default=None, help="工作目录（默认 cph4/fleet/social）")
    ap.add_argument("--face", default="comment", choices=FACES,
                    help="通道：comment 评论 / danmaku 弹幕 / dm 客服私信")
    a = ap.parse_args()
    if a.dir:
        DIR = os.path.abspath(a.dir)
        INBOX = os.path.join(DIR, "inbox.jsonl")
        DRAFTS = os.path.join(DIR, "drafts.jsonl")
        DIGEST = os.path.join(DIR, "DIGEST.md")
        PERSONA = os.path.join(DIR, "PERSONA-v1.json")
        STYLE = os.path.join(DIR, "STYLE-PROFILE-v1.json")
        FAQ = os.path.join(DIR, "faq.jsonl")
        REJECTIONS = os.path.join(DIR, "rejections.jsonl")

    if a.self_test:
        return self_test()
    os.makedirs(DIR, exist_ok=True)
    if a.demo:
        with open(INBOX, "w", encoding="utf-8") as f:
            for r in DEMO:
                f.write(json.dumps(dict(r, ts=datetime.now().isoformat(timespec="seconds")),
                                   ensure_ascii=False) + "\n")
    if not os.path.exists(INBOX):
        print("[social] no inbox at %s" % INBOX)
        return 0

    rows = [json.loads(l) for l in open(INBOX, encoding="utf-8") if l.strip()][:a.limit]
    done = set()
    if os.path.exists(DRAFTS):
        for l in open(DRAFTS, encoding="utf-8"):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass

    out, n = [], 0
    for r in rows:
        if r.get("id") in done:
            continue
        face = r.get("face") or a.face
        comment = r.get("comment", "")
        # 弹幕里的纯情绪短句不逐条回：逐条回＝机器人（也省一次模型调用）
        if face == "danmaku" and DANMAKU_SKIP.match((comment or "").strip()):
            out.append({"id": r.get("id"), "author": r.get("author"), "comment": comment,
                        "video": r.get("video"),
                        "face": face, "kind": "praise_skip", "draft": "",
                        "note": "弹幕夸奖不逐条回（保持真人感）", "needs_human": False,
                        "model": "-", "ts": datetime.now().isoformat(timespec="seconds"),
                        "state": "SKIP_NO_REPLY"})
            n += 1
            continue
        faq, faq_score = (faq_lookup(comment) if face in ("dm", "comment") else (None, 0.0))
        accepted = [x.get("draft") for x in out
                    if x.get("draft") and x.get("state") == "PENDING_REVIEW"]
        kind, draft, needs_human, note = draft_best(comment, face=face, faq=faq,
                                                    samples=a.samples, avoid=accepted)
        row = {"id": r.get("id"), "author": r.get("author"), "comment": comment,
               "video": r.get("video"),
               "face": face, "kind": kind, "draft": draft, "note": note,
               "needs_human": needs_human,
               "model": MODEL, "ts": datetime.now().isoformat(timespec="seconds"),
               "state": "PENDING_REVIEW"}
        if faq:
            row["faq_id"] = faq.get("id")
            row["faq_score"] = faq_score
        out.append(row)
        n += 1

    # 引流密度闸（2026-11-17）：站内引导也是营销信号，一批里每 5 条最多留 1 条，
    # 超出的不丢、标 HOLD_FUNNEL，留给人决定要不要发——密度过高会被观众当广告号。
    funnels = [x for x in out if (x.get("face") == "funnel"
                                  and x.get("state") == "PENDING_REVIEW")]
    cap = max(1, len(out) // 5)
    for i, x in enumerate(funnels):
        if i >= cap:
            x["state"] = "HOLD_FUNNEL"
            x["note"] = (x.get("note") or "") + " | 引流密度超限（本批上限 %d 条）" % cap

    # 配额闸：超出的行不丢，标 HOLD_QUOTA 留痕（明天还想要就改配额，不许悄悄消失）
    seen_video, kept = {}, []
    for r in out:
        vid = r.get("video") or "_unknown"
        if a.max_per_video and seen_video.get(vid, 0) >= a.max_per_video:
            r["state"] = "HOLD_QUOTA"
            r["note"] = (r.get("note") or "") + " | 配额:同一视频仅 %d 条" % a.max_per_video
            kept.append(r)
            continue
        if a.max_new and len([x for x in kept if x.get("state") == "PENDING_REVIEW"]) >= a.max_new:
            r["state"] = "HOLD_QUOTA"
            r["note"] = (r.get("note") or "") + " | 配额:本轮上限 %d 条" % a.max_new
            kept.append(r)
            continue
        seen_video[vid] = seen_video.get(vid, 0) + 1
        kept.append(r)
    out = kept

    # 同批模板感：两条草稿共用 6 字以上同一句尾 = 模板，违反"每条独写无模板"
    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            a, b = out[i].get("draft") or "", out[j].get("draft") or ""
            if not a or not b:
                continue
            hit = _shared_run(a, b, 6)
            if hit:
                for k in (i, j):
                    out[k]["needs_human"] = True
                    out[k]["note"] = (out[k].get("note") or "") + " | 模板感:重复「%s」" % hit
                    out[k]["template_hit"] = hit

    if out:
        with open(DRAFTS, "a", encoding="utf-8") as f:
            for r in out:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    all_rows = []
    if os.path.exists(DRAFTS):
        all_rows = [json.loads(l) for l in open(DRAFTS, encoding="utf-8") if l.strip()]
    pend = [r for r in all_rows if r.get("state") == "PENDING_REVIEW"]
    esc = [r for r in pend if r.get("needs_human")]
    lines = ["# 评论草稿箱 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
             "",
             "- 本轮新生成 %d 条，累计待审 %d 条，其中需人工判断 %d 条" % (n, len(pend), len(esc)),
             "- 铁律：本工具不发送任何内容；账号与发言权在 CEO（orders.md 平台账号物理件）",
             ""]
    for r in pend[:12]:
        tag = "需人工" if r.get("needs_human") else "可直接发"
        lines.append("- [%s] %s：%s" % (tag, r.get("author") or r.get("id"),
                                        (r.get("draft") or "（不代答：%s）" % r.get("kind"))[:80]))
    with open(DIGEST, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[social] new=%d pending=%d escalate=%d -> %s" % (n, len(pend), len(esc), DIGEST))
    return 0


if __name__ == "__main__":
    sys.exit(main())