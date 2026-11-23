#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_client.py - 机队调本地大模型的唯一客户端（令牌/端点/退避都在这里）。

为什么要有它（2026-11-08 实测）：
  · 网关 8792 今天被打了 835 次，**成功 6 次、被拒 817 次**，原因几乎全是
    `bad or missing X-Flux-Token`；而全仓 `token_env: FLUX_LLM_TOKEN` 只有 4 处
    **声明**、零个读取者 —— 配置是装饰品，所以"机队能调本地大模型"一直没通电。
  · 更糟的是没有钥匙时它仍然每 40 秒重试一次，一晚上空打 800 次：
    既刷不出结果，又把网关日志变成噪音，还让人误判"网关坏了"。

三条纪律（与 llm_selftest 同一口径）：
  1) 没令牌=缺料(rc=3)，不是故障；**先本地判、不发请求**，绝不空打；
  2) 端点解析顺序：参数 → FLUX_LLM_BASE → 策略/节点声明 → 本机回环；
     非回环一律走网关（裸 11434 无认证无白名单，会把常驻主力顶掉）；
  3) 同一个进程里失败过一次就退避 300s（熔断），避免把网关刷成日志洪水。

用法：
  from llm_client import generate
  r = generate("写一句理由", cls="resident")     # r = {"ok":bool,"text":..,"why":..,"rc":..}
命令行自检：
  python3 Tools/fleet/llm_client.py --probe
"""
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOKEN_FILE = os.path.expanduser("~/.fluxgroup-llm-token")
# 2026-11-18 D-20261117-03：8792 已不是网关（现为 BigCompute resident_qa_server 的
# qwen3.6-35b QA 服务），默认停指该端口，改本地优先；找不到网关时如实报 GATEWAY-ABSENT。
GATEWAY_DEFAULT = "http://127.0.0.1:11434"
LOOPBACK = ("127.0.0.1", "localhost", "::1")
_COOLDOWN = {}          # base -> 解冻时刻
TRAIN_SENTINEL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), ".codely-cli", "state", "TRAIN-EXCLUSIVE")
COOLDOWN_S = 300


def _is_tailnet(url):
    """2026-11-10 CEO 选 B：Tailscale 内网免令牌。100.64.0.0/10 视为可信邻居。"""
    try:
        import ipaddress
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        return ipaddress.ip_address(host) in ipaddress.ip_network("100.64.0.0/10")
    except Exception:
        return False


def token():
    """令牌来源：环境变量优先（便于一次性注入），其次令牌文件（权限 600、不入 git）。"""
    v = (os.environ.get("FLUX_LLM_TOKEN") or "").strip()
    if v:
        return v
    try:
        return open(os.path.expanduser(os.environ.get("FLUX_LLM_TOKEN_FILE") or TOKEN_FILE)).read().strip()
    except Exception:
        return ""


def base_for(endpoint=None):
    """端点解析：显式参数 > 环境变量 > 本机回环。非回环一律视为网关。"""
    if endpoint:
        return endpoint.rstrip("/")
    env = (os.environ.get("FLUX_LLM_BASE") or "").strip()
    if env:
        return env.rstrip("/")
    return "http://127.0.0.1:11434"


# 网关端口：走网关就必须带 X-Flux-Token（2026-11-08 实锚：一天被拒 830 次）。
# 2026-11-18：8792 已降级为他司 QA 服务，从网关端口表移除——「端口活着」不等于
# 「网关活着」，是否为网关一律由 probe_service() 自证身份判定。
GATEWAY_PORTS = set()


def _port_of(url):
    try:
        from urllib.parse import urlparse
        return urlparse(url).port
    except Exception:
        return None


def _needs_token(url):
    """需要令牌的判定：非回环，且（不是 tailnet 或 是网关端口）。"""
    if _is_loopback(url):
        return False
    if _is_tailnet(url) and _port_of(url) not in GATEWAY_PORTS:
        return False
    return True


def _is_loopback(url):
    return any(h in url for h in LOOPBACK)


def probe_service(url=None, timeout=5):
    """探活须自证身份（D-20261117-03）：/health 必须自报网关标识才算 available。

    返回 {"verdict": "GATEWAY-OK"|"NOT-GATEWAY"|"GATEWAY-ABSENT"|"UNAVAILABLE", ...}
    只看端口是否活着会把「他司 QA 服务」当成网关，故非 gateway 标识一律不计可用。
    """
    url = (url or base_for()).rstrip("/")
    try:
        with urllib.request.urlopen(url + "/health", timeout=timeout) as r:
            raw = r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 端口在答话但没有 /health 身份面：服务活着≠网关活着。
            return {"verdict": "NOT-GATEWAY", "url": url, "identity": "no /health (404)",
                    "why": "端口活着但不是网关，不计入 available"}
        return {"verdict": "UNAVAILABLE", "url": url, "why": "http %d" % e.code}
    except Exception as e:
        return {"verdict": "GATEWAY-ABSENT", "url": url,
                "why": "%s: %s" % (type(e).__name__, str(e)[:60])}
    marker = ""
    try:
        d = json.loads(raw or "{}")
        marker = " ".join(str(d.get(k) or "") for k in ("service", "name", "role", "gateway"))
    except Exception:
        marker = raw[:200]
    low = marker.lower()
    if "gateway" in low or "llm_gateway" in low:
        return {"verdict": "GATEWAY-OK", "url": url, "identity": marker[:80]}
    return {"verdict": "NOT-GATEWAY", "url": url, "identity": (marker or raw[:80])[:80],
            "why": "端口活着但不是网关，不计入 available"}


def generate(prompt, model=None, endpoint=None, timeout=120, cls=None, think=False,
             num_predict=None, max_age_s=60, keep_alive=None):
    """返回 {"ok","text","why","rc"}。rc: 0 成功 / 3 缺令牌(缺料) / 1 真故障 / 4 熔断中。

    cls 用来选座位（与 LOCAL-MODEL-POLICY.duties 对齐），未知 cls 走主力档，
    **绝不默认拉大的**（35B 一驻留就 swap）。
    """
    # 缺料判定必须排在训练独占之前（2026-11-20 RG-33 实锚）：没有令牌是配置缺料，
    # 跟训练在不在跑无关；先判训练独占会把"缺料"报成 5，调用方以为稍后能重试，
    # 实际永远拿不到模型。顺序=先算缺料，再算资源占用。
    url = base_for(endpoint)
    tok = token()
    if not tok and _needs_token(url):
        # 缺料就地判死：不发请求、不进熔断、不计故障
        return {"ok": False, "rc": 3, "text": "",
                "why": "本机没有令牌（%s 或 FLUX_LLM_TOKEN），不走网关" % TOKEN_FILE}
    # FLUX_ALLOW_DURING_TRAIN=1 是"显式声明：我用的模型在 TRAIN-LANE-OK 白名单里"。
    # 2026-11-18 实锚：不加这条，清扫器放行车道但客户端照样拒绝，并行出稿 10 条全 0 可用。
    _allow = os.environ.get("FLUX_IGNORE_TRAIN_LOCK") or os.environ.get("FLUX_ALLOW_DURING_TRAIN")
    if os.path.exists(TRAIN_SENTINEL) and not _allow:
        return {"ok": False, "rc": 5, "text": "",
                "why": "训练独占中（%s），本轮不装载模型" % os.path.basename(TRAIN_SENTINEL)}
    if not model:
        model = _model_for(cls)
        if any(h in url for h in LOOPBACK):
            model = _resolve_local(model)
    if not think:
        pass
    now = time.time()
    if _COOLDOWN.get(url, 0) > now:
        return {"ok": False, "rc": 4, "text": "",
                "why": "熔断中：%ds 后再试（避免空打网关）" % int(_COOLDOWN[url] - now)}


    body = {"model": model, "prompt": prompt, "stream": False, "think": bool(think)}
    if keep_alive:                      # 不传就吃服务端 10m，档位"常驻"会静默失效
        body["keep_alive"] = keep_alive
    if num_predict:
        body["options"] = {"num_predict": int(num_predict)}
    req = urllib.request.Request(url + "/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    if tok:
        req.add_header("X-Flux-Token", tok)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode() or "{}")
        text = (d.get("response") or "").strip()
        if not text:
            _COOLDOWN[url] = now + COOLDOWN_S
            return {"ok": False, "rc": 1, "text": "", "why": "空回复（模型未产出）"}
        return {"ok": True, "rc": 0, "text": text, "why": ""}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read().decode() or "{}").get("error", "")
        except Exception:
            pass
        if e.code == 401:
            return {"ok": False, "rc": 3, "text": "",
                    "why": "网关拒绝令牌（本机串与主控不一致）"}
        if e.code == 403:
            return {"ok": False, "rc": 1, "text": "",
                    "why": "档位不在白名单：%s（改座位，不要改网关）" % detail[:60]}
        _COOLDOWN[url] = now + COOLDOWN_S
        return {"ok": False, "rc": 1, "text": "", "why": "http %d %s" % (e.code, detail[:60])}
    except Exception as e:
        _COOLDOWN[url] = now + COOLDOWN_S
        return {"ok": False, "rc": 1, "text": "",
                "why": "%s: %s" % (type(e).__name__, str(e)[:80])}


LORA_BASE = "http://127.0.0.1:8788"


def _lora_model(timeout=8):
    """8788 上已加载模型的 id。

    mlx_lm.server 会把 `model` 字段当仓库名去 HF 拉——传错就是 401/404，
    所以模型名不能写死，一律读 /v1/models 拿真实 id（= 本地基座绝对路径）。
    """
    with urllib.request.urlopen(LORA_BASE + "/v1/models", timeout=timeout) as r:
        d = json.loads(r.read().decode() or "{}")
    data = d.get("data") or []
    return data[0]["id"] if data else ""


def probe_lora(timeout=5):
    """8788 是否可用。活着且能报出模型 id 才算可用（端口在答话不等于模型在）。"""
    try:
        mid = _lora_model(timeout)
        if not mid:
            return {"verdict": "LORA-EMPTY", "url": LORA_BASE, "why": "/v1/models 无模型"}
        return {"verdict": "LORA-OK", "url": LORA_BASE, "identity": mid}
    except Exception as e:
        return {"verdict": "LORA-ABSENT", "url": LORA_BASE,
                "why": "%s: %s" % (type(e).__name__, str(e)[:60])}


def generate_lora(prompt, timeout=120, max_tokens=60, temperature=0.8, endpoint=None):
    """走 8788 的养号 LoRA 车道（OpenAI /v1/chat/completions）。

    与 generate() 是**两条独立车道**：ollama 走 /api/generate，这里走 OpenAI 协议。
    思考默认关（Qwen3.5 开着会把 60 token 全花在 thinking 里，content 返回 null）——
    这是评测口径踩过的同一个坑，服上默认关一次，调用方就不必各自记得。
    """
    url = (endpoint or LORA_BASE).rstrip("/")
    try:
        mid = _lora_model()
    except Exception as e:
        return {"ok": False, "rc": 2, "text": "",
                "why": "8788 不可用（%s）——launchctl kickstart -k gui/$(id -u)/com.fluxgroup.mlxlora"
                       % type(e).__name__}
    body = {
        "model": mid,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(url + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode() or "{}")
        ch = (d.get("choices") or [{}])[0]
        text = ((ch.get("message") or {}).get("content") or "").strip()
        if not text:
            return {"ok": False, "rc": 1, "text": "",
                    "why": "空回复（finish=%s）" % ch.get("finish_reason")}
        return {"ok": True, "rc": 0, "text": text, "why": ""}
    except Exception as e:
        return {"ok": False, "rc": 1, "text": "",
                "why": "%s: %s" % (type(e).__name__, str(e)[:80])}


HUMAN_PERSONA = os.path.join(ROOT, "cph4", "fleet", "social", "HUMAN-PERSONA-v1.json")

# 8 条候选各自换一个"从哪儿说"，避免候选之间只是换词。
_ANGLE = [
    "\n指着这条片子里一个具体的东西说（某个镜头/某句话/某个声音）。",
    "\n只说你自己看完的感受，别描述画面。",
    "\n挑一个不完美的地方，口气放轻。",
    "\n短一点，像随手一评，别写完整句。",
    "\n说说你想起的另一件事。",
    "\n只提一个小细节，别的都不说。",
    "\n像跟人接话，口语一点。",
    "\n就着片子里某个具体点问一句（怎么做的/是哪一版）。",
    # 真实评论 38% 是短评（≤10 字），但角度池里只有 1 条短句任务 → 生成侧短评只占 12%。
    # 补两条纯短句角度，让短评比例靠近真实分布（不是每条都写整句）。
    "\n只写几个字，像看完顺手丢一句。",
    "\n只留一个词或一个短句，不要成句。",
]
# 表情要"跟着情绪走"：CEO 2026-11-21「不要为了表情而表情」。
# 原来有一条角度直接要求"结尾带一个表情"，等于给每条候选发一个强制配额，
# 模型于是把 [笑哭] 贴在毫无情绪的陈述句后面。现在改成条件句，并明说不许硬加。
_EMOJI_RULE = ("\n表情只在句子本身有情绪（好笑/无奈/惊讶/想笑）时才带一个，"
               "平铺直述就别加；不许为了带表情而带。")


def human_persona_block(acct=None):
    """把**本人亲笔**的评论样句拼进提示词（只有有亲笔语料的号才加）。

    2026-11-20 CEO「学习老号真人评论人设」：光写"带一两个语气词"教不出来——
    4B 会把语气词硬塞在词中间（实测「结尾那声鸣叫哈挺带感的」）。样本比形容词管用：
    直接给他自己的 6 句原话，并明说"不要更整齐、不要更夸张、不要抄原句"。
    """
    acct = acct if acct is not None else (os.environ.get("FLUX_ACCOUNT") or "")
    if acct not in ("acct1",):
        return ""
    try:
        d = json.load(open(HUMAN_PERSONA, encoding="utf-8"))
    except Exception:
        return ""
    few = [s for s in (d.get("fewshot") or []) if s][:6]
    if not few:
        return ""
    # 样句不加引号：2026-11-20 实测加了「」以后模型把引号一起抄出来
    # （「突然「我」发现这段配乐…」），看着就像模板。
    return ("\n我平时在评论区就是这么写的（每条一行）：\n" +
            "\n".join("- %s" % s for s in few) +
            "\n照这个口气写：不要更整齐、更完整、更夸张，不要加引号，也不要照抄这几句。")


def human_len_target(i=0):
    """按**本人实测分布**取一个目标字数，而不是所有评论都写 10-20 字。

    2026-11-21 实锚：老号亲笔 23 条真实长度是 2–63 字（中位 10、p25 7、p75 21），
    而生产带子是 10-20 —— 每条都被逼进同一区间，这本身就是模板特征；
    真人一句话长短是随口定的。做法：从实测分位数里按 i 轮换取目标。
    没有亲笔语料的号（新号）返回 None，调用方继续用原带子。
    """
    acct = os.environ.get("FLUX_ACCOUNT") or ""
    if acct not in ("acct1",):
        return None
    try:
        d = json.load(open(HUMAN_PERSONA, encoding="utf-8"))
    except Exception:
        return None
    L = d.get("len") or {}
    base = [L.get(k) for k in ("min", "p25", "median", "p75", "max")]
    base = [int(x) for x in base if isinstance(x, (int, float)) and x]
    if not base:
        return None
    # 权重偏短：多数 7-14 字、偶尔一句长，跟他实际形态一致（不是均匀分布）
    order = [2, 1, 2, 3, 1, 2, 0, 4]
    return base[order[i % len(order)] % len(base)]


PLATFORM_VOICE = os.path.join(ROOT, "cph4", "fleet", "social", "PLATFORM-VOICE-v1.json")


def platform_block(seg=None):
    """把这个平台上"这一类人怎么说话"拼进提示词（表情码/口癖/字数）。

    2026-11-21 CEO「要有平台相关用户的人味」+ 实测：真实 B 站评论 20% 带表情码
    （memer 段 72%、shallow 25%、music_seeker 9%），我们生成 **0%**。
    提示词里只写了"像随口说话"，从没写过"像这个平台的人"——所以模型写的是通用中文。

    只用统计出来的三条：表情码候选、口癖候选、字长区间；例句不给（给了就照抄）。
    """
    try:
        d = json.load(open(PLATFORM_VOICE, encoding="utf-8"))
    except Exception:
        return ""
    v = (d.get("segments") or {}).get(seg) or d.get("global") or {}
    if not v:
        return ""
    em = [e for e, _ in (v.get("emoji_top") or [])[:4]]
    mt = [g for g, _ in (v.get("meme_top") or [])[:4]]
    rate = float(v.get("emoji_rate") or 0)
    p25, p75 = v.get("len_p25") or 0, v.get("len_p75") or 0
    bits = []
    if em:
        # 只给比例、不给"必须带"：写完 0%→46.7%，真实是 25.4%，说清"多数不带"才收得住
        # 实测写"约 25% 会带"仍输出 40%：模型对比例不敏感，对"几句里几句"敏感。
        # 换成硬约束数量（四句最多一句），再补一句"宁可没有"。
        bits.append("表情码就用 %s 这种写法、紧贴不空格；这批人只有约 %.0f%% 会带，"
                    "也就是四句话里最多一句带表情，宁可没有"
                    % ("/".join(em), rate * 100))
    if mt:
        bits.append("这类人嘴上常挂 %s 这种词，但别硬塞" % "、".join(mt[:3]))
    if p25 and p75:
        bits.append("他们一般写 %d-%d 字" % (p25, p75))
    return ("\n这是 B 站评论区，要像这个平台的人说话：" + "；".join(bits) + "。") if bits else ""


def lora_comment_prompt(title, desc="", i=0, seg=None, brief=""):
    """按**训练时用的同一批指令模板**拼提示词。

    踩过的坑：自己另写一句"写一条B站评论"喂给 LoRA，它会退回助手腔——
    「这里有一条既符合B站用户调性的评论，供你选择：**选项一**…」。
    原因是训练样本的 user 轮全是 train_build.INSTRUCTIONS 那三句，
    提示词不对版等于没触发微调。口径单源，不在生产侧另发明模板。

    唯一在推理侧追加的是**本次说话的角度**：不改训练口径，只让 8 条候选别长一个样。
    2026-11-20 实测：不加这句，18 条里 19 条以"镜头/配乐"开头（占满，等于模板）。
    """
    import train_build as tb
    hint = ("（简介：%s）" % (desc or "")[:50]) if desc else ""
    ins = tb.INSTRUCTIONS[i % len(tb.INSTRUCTIONS)].format(title=(title or "")[:40], hint=hint)
    if seg:
        try:
            import segments as _sg
            ins += " " + _sg.style_block(seg)
        except Exception:
            pass
    if brief:
        ins += brief
    ins += human_persona_block()
    ins += platform_block(seg)
    # 分区常识（在聊什么/别碰什么）——CEO 2026-11-21「好好理解 b 站」「目前不做引流」
    try:
        import bili_norms as _bn
        ins += _bn.block(seg or "")
    except Exception:
        pass
    # 明确写出"别用这些词"：光靠闸拒稿会把八条候选打成一条都过不去
    # （2026-11-22 实测：不写这句时 8 条候选里 5 条带"绝了"，全被烂梗闸拒）。
    ins += ("\n这些词最多偶尔带一个（八条里最多一条带，别每条都带）：绝了、氛围感、质感、干货、"
            "拉满、封神、爱了、绝美、高级感。表情符号同理：偶尔一个可以，别堆。"
            "别用\"首先/然后/之后\"这类连接词。")
    ins += _EMOJI_RULE
    # 真实样本（few-shot）：小模型的腔调靠样本改，不靠形容词。样本取自 6 万条真实评论里
    # PASS 的部分，按 B 站自己的分类（提问/夸奖/挑刺/玩梗/共鸣/打卡）分组，按候选序号轮换，
    # 这样 8 条候选不会长成同一个样（2026-11-22 CEO「策略可以多元化…不要这么讲话」）。
    ins += voice_block(i=i, title=title)
    # 角度随机：固定 i%8 会让"第 1 条永远说画面、第 8 条永远带表情"，
    # 换条视频还是同序，等于半个模板。用 (标题+序号) 做种子，不同视频取到不同角度。
    import random as _rnd
    _seed = (title or "") + str(i)
    ins += _ANGLE[_rnd.Random(_seed).randrange(len(_ANGLE))]
    return ins


_VOICE = {"spec": None, "ts": 0.0}


def _voice_spec():
    """进程内缓存 10 分钟：每个候选都读盘会把生成时间拉长。"""
    import json as _json
    import time as _t
    if _VOICE["spec"] is not None and _t.time() - _VOICE["ts"] < 600:
        return _VOICE["spec"]
    p = os.path.join(ROOT, "cph4", "fleet", "social", "corpus", "hot", "VOICE-SPEC-v1.json")
    try:
        _VOICE["spec"] = _json.load(open(p, encoding="utf-8")) or {}
    except Exception:
        _VOICE["spec"] = {}
    _VOICE["ts"] = _t.time()
    return _VOICE["spec"]


_ARCH = {"use": None, "ts": 0.0, "picked": {}}


def _arch_state():
    """当天各原型的已用次数（跨进程共享）：轮换要按"今天谁用得多"来定，
    否则同一天 8 条候选可能全是夸奖型，多样性为零（2026-11-22 实测）。"""
    import json as _json
    import time as _t
    from datetime import datetime as _dt
    p = os.path.join(ROOT, ".codely-cli", "state", "VOICE-USAGE.json")
    today = _dt.now().strftime("%Y-%m-%d")
    if _ARCH["use"] is not None and _ARCH["ts"] and _dt.now().strftime("%Y-%m-%d") == _ARCH.get("day"):
        return _ARCH["use"]
    try:
        d = _json.load(open(p, encoding="utf-8")) or {}
    except Exception:
        d = {}
    cur = d.get(today) or {}
    _ARCH["use"] = cur
    _ARCH["day"] = today
    _ARCH["path"] = p
    _ARCH["all"] = d
    _ARCH["ts"] = _t.time()
    return cur


def _arch_save():
    import json as _json
    try:
        d = _ARCH.get("all") or {}
        d[_ARCH.get("day")] = _ARCH.get("use") or {}
        # 只留最近 14 天，文件不涨
        keep = sorted(d.keys())[-14:]
        d = {k: d[k] for k in keep}
        _json.dump(d, open(_ARCH["path"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass


_ARCH_PERF = {"v": None, "ts": 0.0}


def _arch_perf():
    """原型效果台账（arch_perf.py 产出，10 分钟缓存）。样本不足时 best=None。"""
    import json as _json
    import time as _t
    if _ARCH_PERF["v"] is not None and _t.time() - _ARCH_PERF["ts"] < 600:
        return _ARCH_PERF["v"]
    p = os.path.join(ROOT, ".codely-cli", "state", "ARCH-PERF.json")
    try:
        _ARCH_PERF["v"] = _json.load(open(p, encoding="utf-8")) or {}
    except Exception:
        _ARCH_PERF["v"] = {}
    _ARCH_PERF["ts"] = _t.time()
    return _ARCH_PERF["v"]


def _pick_arch(i, title=""):
    """选原型：优先"今天用得最少"的那类，同次数时用 (标题+序号) 做种子定序。"""
    spec = _voice_spec()
    names = list((spec.get("archetypes") or {}).keys())
    if not names:
        return None
    key = "%s|%d" % ((title or "")[:24], i)
    hit = _ARCH["picked"].get(key)
    if hit:
        return hit
    use = _arch_state()
    import random as _rnd
    seed = _rnd.Random((title or "") + "arch" + str(i))
    order = sorted(names, key=lambda n: (int(use.get(n) or 0), seed.random()))
    name = order[0]
    # 探索-利用：80% 走"今天用得最少"（保多样性），20% 投给"被赞率最高"的原型
    # （前提是该类样本≥5 条，见 arch_perf.MIN_N）。没有数据时自动退化为纯均匀轮换。
    _best = (_arch_perf() or {}).get("best")
    if _best in names and seed.random() < 0.2:
        name = _best
    use[name] = int(use.get(name) or 0) + 1
    _ARCH["picked"][key] = name
    _arch_save()
    return name


def fix_emoji(text):
    """把模型写坏的 B 站表情码修好："[打 call]" → "[打call]"。

    2026-11-22 实测：模型经常在方括号里加空格，露馅闸判"表情码破损"整条拒掉，
    一天能白扔好几条好稿。这是纯粹的写法瑕疵，修词不修意。
    """
    import re as _re
    if not text:
        return text
    return _re.sub(r"\[\s*([^\[\]]{1,16}?)\s*\]",
                   lambda m: "[" + m.group(1).replace(" ", "") + "]", text)


def voice_band(i=0, title=""):
    """与 voice_block 同一套选原型逻辑，返回它的字数带；没有样本时返回 None。"""
    spec = _voice_spec()
    arch = (spec.get("archetypes") or {})
    if not arch:
        return None
    name = _pick_arch(i, title)
    band = (arch.get(name) or {}).get("band")
    if not band:
        return None
    return int(band[0]), int(band[1])


def voice_block(i=0, title=""):
    """按候选序号轮换一个说话原型，给 3 条真实样本 + 字数带。"""
    spec = _voice_spec()
    arch = (spec.get("archetypes") or {})
    if not arch:
        return ""
    name = _pick_arch(i, title)
    a = arch.get(name) or {}
    samples = list(a.get("samples") or [])[:3]
    if not samples:
        return ""
    band = a.get("band") or [8, 30]
    return ("\n下面是这条视频下真实用户的评论，只借用说话方式，不要照抄内容：\n"
            + "\n".join("- " + s for s in samples)
            + "\n这次按这个语气写一句，%d–%d 字。" % (int(band[0]), int(band[1])))


def angle_for(title, k):
    """取第 k 条候选的说话角度（与 lora_comment_prompt 内同一套种子规则）。

    2026-11-22「搞到最优」：提示词里凡是**随候选变化**的部分都必须放在最末尾，
    否则 8788 的提示词缓存在每条候选上都失效——实测首枪 5.1s、命中缓存 0.6s，
    3 条候选就要 15s。把模板与视频上下文固定成前缀，只让角度/字数变化，
    第 2 条起都在缓存里跑。
    """
    import random as _rnd
    return _ANGLE[_rnd.Random((title or "") + str(k)).randrange(len(_ANGLE))]


def _model_for(cls):
    """座位 → 模型，读 LOCAL-MODEL-POLICY 单一源；取不到就用主力档，不猜大的。"""
    try:
        d = json.load(open(os.path.join(ROOT, "cph4", "fleet", "LOCAL-MODEL-POLICY.json"),
                           encoding="utf-8"))
        duties = d.get("duties") or {}
        seat = cls if isinstance(cls, str) and cls in duties else "resident"
        m = (duties.get(seat) or {}).get("model")
        if m:
            return m
        return (duties.get("resident") or {}).get("model") or "qwen3.5:4b"
    except Exception:
        return "qwen3.5:4b"


_LOCAL_MODELS = {}


def _local_models():
    """本机 ollama 模型名集合（进程内缓存一次）。查不到=None，不参与判定，避免误伤远端网关。"""
    if "v" in _LOCAL_MODELS:
        return _LOCAL_MODELS["v"]
    try:
        import subprocess
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        names = {ln.split()[0] for ln in (out.stdout or "").splitlines()[1:] if ln.split()}
        _LOCAL_MODELS["v"] = names or None
    except Exception:
        _LOCAL_MODELS["v"] = None
    return _LOCAL_MODELS["v"]


def _resolve_local(model):
    """座位模型名一致性闸（2026-11-18 迭代项）：名字不在本机 ollama list 就换同族可用档，
    并印 MODEL-SUBSTITUTED——禁止静默用不存在的模型空打（此前 qwen3.5:4b-mlx 即此病）。"""
    names = _local_models()
    if not names or model in names:
        return model
    for cand in ("qwen3.5:4b", "qwen3.5:9b", "qwen3.5:2b"):
        if cand in names:
            print("[llm-client] MODEL-SUBSTITUTED %s -> %s" % (model, cand))
            return cand
    print("[llm-client] MODEL-SUBSTITUTED %s -> (本机无可替代档)" % model)
    return model


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--prompt", default="只回答两个字：收到")
    ap.add_argument("--endpoint", default="")
    ap.add_argument("--cls", default="resident")
    a = ap.parse_args()
    if not a.probe:
        r = generate(a.prompt, endpoint=a.endpoint, cls=a.cls)
        print(json.dumps(r, ensure_ascii=False))
        return r["rc"]
    t = token()
    print("[llm-client] base=%s token=%s model=%s"
          % (base_for(a.endpoint), ("present len=%d" % len(t)) if t else "MISSING",
             _model_for(a.cls)))
    print("[llm-client] identity=%s" % json.dumps(probe_service(a.endpoint), ensure_ascii=False))
    r = generate(a.prompt, endpoint=a.endpoint, cls=a.cls)
    print("[llm-client] rc=%d ok=%s %s" % (r["rc"], r["ok"], r["text"] or r["why"]))
    return r["rc"]


if __name__ == "__main__":
    raise SystemExit(main())