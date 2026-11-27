# KN 出生站 C2178：KN15 整条落成布景（装置化）＋ 镜头句洁净闸

## 一句话

KN15 的 768P 成片不是"纸飞机飞过云海"，而是**纸飞机架在一个台子上、隔着机舱舷窗和窗帘看云**——
布景化、离世界。它的关键帧是对的，运镜闸（1.00x PASS）、字幕闸（PASS）、覆盖闸（声明主体=纸飞机，在）**三道机械闸全放行**。
根因在提示词层：镜头句里写着 `the camera holds a locked-off tripod frame`——"tripod"（三脚架）是一个实物名词，
模型把它和内容句的 "the blue opening ahead"（前方那道蓝色开口）一起落成了实景：三脚架＋舷窗框＋窗帘。

## 证据

| 项 | 值 |
|---|---|
| 单元 | KN_A-KN15（11.54s，277 帧，1344×768） |
| 关键帧 | `frames/KN_KN15.png` = 白色纸飞机在云海上方，正确 |
| 落片 | 纸飞机立在深色机座上，背后是舷窗框＋左右大片窗帘，窗外云海 |
| 运镜闸 | locked，实测 1.00x → **PASS**（它是静帧，锁定反而合规） |
| 字幕闸 | PASS（无烧字） |
| 覆盖闸 | 声明主体=纸飞机 → 在位，PASS |
| 同句对照 | KN13、KN20、KN20b、KN02、KN07 用的是同一句 `locked-off tripod frame`，**都渲染干净**（纸飞机挂夜城、溶进星流） |

所以：这句话不是"必然出事"，是**可避免的风险面**——6 个落片里坏 1 个。这正好是 lint 该管的事：在烧之前把可避免的那一半拿掉，
而不是让眼睛板事后去抓。

## 本轮做了什么

1. **`kn_prompt_hygiene_gate.py`（入仓可重跑·零 GPU）**
   - `--shots`：审作者层镜头宏（未来一切 manifest 的来源），必须干净；
   - `--manifest`：审已构建的 manifest，已发射的单元标 LEGACY，保留"作者层改了 / 盘上已按旧词烧了"的差额可见；
   - 判定：镜头句只许描述视角运动，**机材/人员名词 = FAIL**（tripod / floor dolly / steadicam / operator / jib arm / gimbal / rail / boom pole / cameraman），
     机材派生动词（cranes / dollies）= WARN（作动词读是运动，作名词读才是道具）。
2. **作者层修好**：本片 shots 文件在既有 album-local 覆盖位（`LX.CAM_MOVE["slide"]` 之后、`CM = LX.CAM_MOVE` 之前）追加 6 条覆盖——
   static / pushin / pullout / stead / hand / pushthru 去掉三脚架、地面轨道车、斯坦尼康、操作员，改成纯运动描述；运动语义一字未改。
   **只改本片进程内词表，不动共享正典 `prompt_lexicon.py`**（mv0001 也从那份词表出稿）。
3. **闸门自证**：改前 `--shots` = FAIL 6 / WARN 3；改后 = **FAIL 0 / WARN 3**（exit 0）。改后 shots 文件仍可导入（NEW 30 / REUSE 11 不变）。
4. **在飞 manifest 的差额登账**：`run-bmc-kn-i2v.json` = 30 单元中 **18 FAIL / 1 WARN**（LEGACY）。
   其中 10 个已落片（KN02/03/07/08/11/13/16/17/20/20b）用的是旧词、9 个渲染干净，KN15 坏。
   **还在烧的 8 个（KN21/22a/22b/24/25/29/30 + KN23 WARN）跑的是已读进内存的旧 manifest**——runner 在启动时一次性 json.load，
   中途改盘无效。本轮决定**不杀**：kill 掉要重发 manifest、丢在飞单元，而风险面约 1/6、落片后闸门＋眼睛站仍能拦，
   坏件进重烧队列即可。这条决定记在这里，不靠记忆。
5. **眼睛站成件**：`kn_unit_board_c2178.py` + `KN-768P-EYE-BOARD-1-c2178.jpg`
   （KN15 / KN13 对照 / KN20 对照 / KN17 各三帧原生 1344×768，行上带 framing/hygiene 判决与眼睛判决，板与闸不会各说各话）。

## 顺带定谳的两件

- **KN17 不是"主体丢了"**：它作者层就是星辰带空镜（未声明实体主体）。C2177 记"声明主体不在画"的说法要收窄：
  没有主体的是**作者层**，不是渲染层。真正的问题形态是"无锚空镜占 10.5s"，属于分镜预算层，不是这张闸能判的。
- **KN15 这类件不能靠"纹理/细节量"的廉价统计去抓**：本轮实测 21 个落片，
  细细节率、粗结构对比、细/粗比三面都**不能**把 KN15 从干净件里分出来（KN15 的窗帘细纹反而让它"细节最多"）。
  任何宣称"统计面能判主体/布景漂移"的闸都是假闸。真闸只有两条路：**作者层洁净（本轮已落）** 或 **视觉模型/检测器**（未落，记待办）。

## 产物

- `cph4/fleet/mv-album-001-jay/kn_prompt_hygiene_gate.py`（入仓可重跑）
- `cph4/fleet/mv-album-001-jay/kn_unit_board_c2178.py`
- `cph4/fleet/mv-album-001-jay/KN-768P-EYE-BOARD-1-c2178.jpg`
- `cph4/fleet/mv-album-001-jay/可爱女人-shots-v2.py`（v3.1：镜头句去机材/人员，album-local 覆盖）
- `media/mv-album-001-jay/evidence-c2178/{hygiene-shots-before,hygiene-shots-after,hygiene-manifest-legacy,unit-notes,eye-board}.json`（media 不入 git）

## 待办

- (红) KN15 整条布景化 → 重烧，480P 先验（用的是改后镜头句）
- (黄) KN21-KN30（8 单）在飞用旧词 → 落片后逐单过 hygiene＋眼睛站，坏件进重烧队列
- (黄) 主体/布景漂移的机械判定仍是空位：需要视觉检测器，或继续靠"作者层洁净＋眼睛站"两条腿（本轮已把第一条腿装上）
- (黄) KN11 push 渲染成静止、KN17 空镜占 10.5s → 已在重烧/分镜候选（承 C2177）