# OH-20261008-biglife — 开源收获轮·BigLife E1 域切片（语言/声纹/年轮产线 OSS 工具族）

- **窗**：O-20261008-0650 九司切片窗（10-10 12:00·D-20261008-07③ E1 面）；本切片=2026-10-10 20:0x（BigLife-OSLoop R784·T-20261010-02 兑现）。**过窗如实记**：BigLife 10-10 17:52 CEO 解冻令+18:0x 双任务复启（C-20261010-03⑤），窗内三轮预算耗于复工收口+冻结锁冲突事件（R778~R782），三腿证据 18:42/18:56/19:41 三轮接力补齐后组装——补件通道活（D-20261008-07「补件即销」面）。
- **实搜面（三腿实证据·全活面零死面·每主张带探针指针）**：
  - **腿① GitHub API 直采**（R779·`state/oss-probe-R779.json`）：SYSTRAN/faster-whisper **25792★ MIT**·pushed 2026-10-10（探针日活推）·issues 30·活跃；rhasspy/piper **11298★ MIT**·**archived=true**（2025-08-26 末推=上游封存）；hexgrad/Kokoro-82M **404**（仓迁移）。
  - **腿② 搜索定位**（R780·`state/oss-probe-R780.json`·GitHub search API）：Kokoro 迁移=**hexgrad/kokoro**（9236★ Apache-2.0 活跃·desc 指向 HF 权重 hf.co/hexgrad/Kokoro-82M=血统不断）；piper 继任=**OHF-Voice/piper1-gpl**（5813★·pushed 2026-10-06 活跃）。
  - **腿③ 本地探针**（R783·`state/oss-probe-R783.json`+样音 wav 双件·本机 4070S 纯 CPU）：**piper-tts 1.8.0**（piper1 继任线 PyPI 包）zh_CN-huayan-medium 双样音（问候台词+年轮句域各一）——冷载 1.25s·0.14-0.25s 出 6.8-6.9s 音=**27-48× 实时**；**faster-whisper 1.2.1**（uv venv py3.12 隔离）tiny int8——冷载 0.41s+6.9s 音转写 0.39s=**17.7× 实时**（**tiny 中文质量=弱档实锚**：转写样本错字率高→产线档=small+）；**装机四坑实锚**（成本门注记面）：①hf_hub 1.x 下载栈本机双病（xet cache WinError5+open(metadata_errors) TypeError→curl 直拉模型件绕开）②av 19.0.1 签名变更撞 faster-whisper 文件路径解码（av<15 无 py3.12 轮→numpy 数组入口绕开）③piper1 synth_wav/CLI channels 病（AudioChunk 手写 WAV 绕开）④系统 py3.14 ctranslate2 asyncio TypeError（uv venv py3.12 净）。
  - 许可复核（R784 今日 API 直验）：OHF-Voice/piper1-gpl=**GPL-3.0**；hexgrad/kokoro=**Apache-2.0**；PyPI piper-tts 1.8.0/faster-whisper 1.2.1 license_expression 字段=空值如实记（包级许可以上游仓为准=MIT 直验）。
- **候选（五门评估）**：

  **A. piper zh 神经 TTS（台词池/声纹线升级路健康定谳·T-20260925-13① 在册线）**
  - 契合门 **PASS**：本司声纹线现役（VOICES 53 声纹角色映射+入城 10 席 piper huayan 候选通道在册）——zh_CN-huayan-medium 样音=问候台词+年轮句双域实测 27-48× 实时**纯 CPU**（GPU 让路窗可用性实证=年轮产线零争用）；居民台词→音频管线直配。
  - 反重复门 **PASS**：cph4/README.md 注册表 rg piper/kokoro/whisper=**零 OSS 采用行**（唯一命中=token-economy 栈「whisper 随消费线」模型行·非注册采用）；本司 piper 使用=T-20260925-13① 既有在册升级路——本切片=血统健康定谳+继任定位，非重建非双购。
  - 许可门 **过（带注记）**：上游 rhasspy/piper=MIT（腿① 直验）；继任仓 piper1-gpl=**GPL-3.0**（今日直验）——**产线依赖面=PyPI piper-tts 1.8.0 包（MIT 血统 core）·GPL 仓=完整分发线不采**（只依赖 PyPI 包、不 clone GPL 仓=不触 GPL 义务面）；对外发布面（居民配音入对外视频等）**许可复核一行注记**在案。
  - 健康门 **PASS（血统链定谳）**：上游 archived（2025-08-26 封存）→继任 OHF-Voice/piper1-gpl 活跃（pushed 2026-10-06）+PyPI 1.8.0 已发布且本机实装可用=**升级路不死**；维护方=OHF-Voice org。
  - 成本/安全门 **PASS**：63MB onnx 单模型本地推理·零网络零外发·纯 CPU·四坑全有绕开实录。
  - **判定：采用（维持+定谳）**——piper zh=声纹产线主 TTS 档；GPL 仓避用条款+发布面复核注记入任务单。盲测判据 5/5（T-20260925-13①）留声纹线首个换轨需求触发。

  **B. faster-whisper（台词池 QC 校验候选·advisory 形）**
  - 契合门 **弱过（advisory 实测定谳·ruff 判例同型）**：本司消费面=声纹线产物 QC（TTS 输出→转写回比对=「只提所喂事实」的音频域镜像）+机审门语音域候选；17.7× 实时=QC 档可用·tiny 中文弱档=**产线需 small+ 档**。
  - 反重复门 **PASS**：集团域 openai-whisper=BigStream MV 歌词锚点通道（他司在册·不同消费面不同栈）——faster-whisper=本司 QC 候选·uv venv 隔离·非同域双建；注册表零行。
  - 许可门 **PASS**：SYSTRAN/faster-whisper=MIT（腿① 直验）。
  - 健康门 **PASS**：pushed 2026-10-10（探针日活推）·issues 30·CTranslate2 生态标准件。
  - 成本/安全门 **PASS（带坑注记）**：uv venv py3.12 隔离净装（系统 3.14 ctranslate2 坑绕开）·hf_hub 下载栈双病→curl 直拉绕开·零 GPU。
  - **判定：parked→advisory 候选**——不立即接线；声纹线首个 QC 需求触发时 small+ 档实弹验收；装机四坑链=成本注记存档。

  **C. kokoro TTS**
  - 契合门 **parked**：zh 声部覆盖有限（主强 en）·本司域=中文台词池主战场→piper zh 已在产覆盖；Apache-2.0+9236★ 活跃（pushed 2025-08-06）。
  - **判定：parked**（英文声部需求触发再评）。
- **采用→落点**：①T-20260925-13① 装机实证维度部分兑现（zh huayan 装机+样音在盘·盲测 5/5 留触发）+GPL 仓避用条款+发布面许可复核注记；②T-20261010-02 关结（本件即交付）；③cph4/README.md 注册表**不加行**（piper=既有在册线定谳非新采用·B/C=parked 留档本件即可·防注册表膨胀）。
- **下窗指针**：声纹线 QC 首需求=faster-whisper small+ 实弹验收（uv venv 通道已备）；kokoro 英文声部需求触发再评；装机四坑链=本机装机知识复用面（新机/新环境部署成本直查本件）。

## 切片结论应用表（research-protocol 强制·无表=未交付·BigLife OH 序列续 13-16）

| # | 发现 | 判定 | 落点（工作流变更） | 后续 |
|---|------|------|------|------|
| 13 | piper 血统链：上游 rhasspy/piper MIT archived（2025-08-26 封存）→继任 OHF-Voice/piper1-gpl GPL-3.0 活跃+PyPI piper-tts 1.8.0 本机实装 zh 样音 27-48× 实时纯 CPU | 五门过（许可门带 GPL 仓避用注记）→**采用（维持+定谳）** | T-20260925-13① 定谳注记（装机实证部分兑现+盲测留触发）；声纹产线主 TTS 档 | 对外配音发布前许可复核一行；盲测 5/5 随首个换轨需求 |
| 14 | faster-whisper MIT 活跃（探针日活推）·tiny int8 17.7× 实时·tiny 中文弱档 | 弱过→**parked→advisory 候选**（QC 档·需 small+） | 无立即变更（需求触发实弹验收） | 声纹线首个 QC 需求触发 |
| 15 | kokoro Apache-2.0 活跃·zh 声部覆盖有限 | **parked** | 无变更 | 英文声部需求触发再评 |
| 16 | 三腿实搜面（API 直采/搜索定位/本地探针+装机四坑链） | 搜索面实录·零死面 | —（实录面行） | 四坑链=新机部署成本直查件 |

- 三律自检（本切片）：①业务契合=三候选逐门实测定谳（A 定谳采用/B advisory 弱过/C parked 带理由）②不重复造轮子=注册表 rg 零行+他司在册（openai-whisper 他司域）双查③科学使用=parked 带理由禁悬空·全主张带探针指针（R779/R780/R783 三 json+样音 wav）。
- 送达：本件=R784 落账（BigLife 仓 commit 含 T-20261010-02 关结行；cph4/oss-harvest/ 本件落位）；三腿证据=BigLife 仓 `state/oss-probe-R779/R780/R783.json`+样音 wav（gitignored state/·文件内数据即指针实体）；本实体单文件制+集团仓终接件零接触（跨仓写入遵 CEO 令法源·oss-harvest §六）。
