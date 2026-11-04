# R-20261104-voice-datasets-01 音色数据集寻源报告（bm-c）

CEO 令 2026-11-04：「角色或者音色 要多找数据集 优质的 不要偷懒」。
执行：bm-c 交互窗 2026-11-04 23:0x。原则=只走干净通道（B站素人抓取已被权利闸判死），带证投料不冒充。

## 一、已投料（本批落地）

### AISHELL-3（SLR93）——首选「优质无杂音」源，168 句已投料
- 规格：85h / 218 说话人 / 录音棚高保真 44.1kHz mono / 88035 句 / 标注准确率 98%
- 官方渠道：https://www.openslr.org/93 （HF 镜像 hf-mirror.com 直连可用，本机 168/168 零失败）
- 选角：12 说话人（4 青年女 + 4 青年男 + 2 中年女 + 2 中年男），每人 14 句
- 投料位置：media/asset/inbox/voices-aishell3/<SSBxxx>/（每目录 RIGHTS.json + index.json 就位）
- license：**academic-noncommercial（学术免费，商用需向希尔贝壳购买授权）**
- 状态：voice_dataset 准入闸正确拦截（白名单 {own, public-domain, cc0, cc-by, licensed} 不含此项）
- **待决策：合规席/主控一句话——白名单增补 academic-noncommercial（或标 licensed-pending-contact）即放行 168 句进训练**；若未来商用再购正式授权

## 二、候补通道（未落地，按优先级）

1. **CommonVoice zh-CN（CC0，最干净免决策）**：CV17 HF repo 空（新版数据走官方站点）；S3 直连本机被墙（WinError 10060）。两条出路：a) 开代理拉 S3 桶；b) 官网下载流程（同意条款+邮箱）——邮箱注册类=CEO 物理件域。
2. **VCTK（CC-BY 4.0，白名单内）**：英语 110 说话人 × 48kHz 录音棚——外国人角色音色（mv0001 巴比伦女主系）的对口源；官方全量包 11GB，需挑说话人下载方案，候选下批。
3. **LJSpeech（public-domain，白名单内）**：单说话人女声金标（24kHz 英语），openslr SLR83 直链 2.6GB——单音色优质但只有一人，适合做质量基准样板。
4. **Emilia（101k 小时中文+多语种）**：CC BY-NC + in-the-wild 网络爬取源——授权与源合规均有争议，**不推荐**。

## 三、角色线（同令另一半，本窗已收口）

- char_plan 已由主控扩至 12 视角；本机重生成 PROMPTS.json 并烧图 96 张（旧 48 SKIP + 新 48 烧，零失败，GPU 97% 满载）
- char_dataset 重跑：**passed=8/8，verdict=PASS**（此前 BLOCKED 0/8，6<12 缺口根治）

## 四、下一步建议

1. license 白名单一句话决策后，voice_dataset 装配即可 passed>0，音色库从 0 音频破零
2. VCTK 挑 8-10 说话人投料（外国人角色线）
3. 音色训练环境唯一安装点=bm-b（GPT-SoVITS），装配通过后训练卡将派 bm-b
