# meme-daily-v1 —— 热点梗短视频机队日产线（CEO 令 O-20261010-1240）

定位一句话：**热搜上什么，AI 就把什么演成 15 秒小剧场**。全流程 AI（AI 关键帧→AI 图生视频→AI 配音→AI 配乐→自动剪辑装配），机队自治日产 3 条，bm-a 零 GPU 占用。

## 目录
- `SPEC-ACCOUNT.md` 账号定位 + 爆款公式 + 合规红线 + 日更选题 SOP
- `topics/v1-zunjie-brake.md` 样片① 尊界V800 刹车断裂（17.8s·今日主呈）
- `topics/v2-sucheng-car.md` 样片② 速成车/一年三款（18.5s·草样）
- `topics/v3-zhiji-overtime.md` 样片③ 智己加班图鉴（排队·V1 定向后终剪）
- `topics/v{1,2,3}-shots.json` 装配机读参数（镜头/字幕/音轨全量）
- `tools/assemble_meme.py` 确定性装配器（拼片+大字幕ASS+混音+AIGC水印）
- `outbound/` 交付区（每片一夹：成片+素材表+回执；RECEIPTS.md=机队回执台账）

## 机队执行手册（每片七步）
0. **前置自检**：TJGenerators MCP 可用（generate_image 一次轻调用即知）；ffmpeg（`ffmpeg -version`，缺则 `python -m pip install imageio-ffmpeg` 用其内置 bin）；python ≥3.10（ComfyUI 便携 python 可用）。
1. **读规格**：`topics/vN-*.md`（事实底稿+旁白+镜头意图）+ `topics/vN-shots.json`（机读参数）。
2. **关键帧**：TJGenerators `generate_image`，逐镜 1 张，尺寸 `{"width":768,"height":1344}`（服务器拒则改 portrait 预设）；提示词照抄 JSON 内 `kf_prompt`（已按正词法写好，禁加否定墙）。单波 ≤10 单（配额纪律：TJGenerators 100 任务/日机队共享，单片 ≈12 单）。
3. **图生视频**：本地关键帧先 `file_upload` 拿 CDN URL，再 `generate_video`：provider=`minimax_h3`，mode=`first_frame`，image_urls=该镜 CDN URL，duration=5，resolution=`768P`，prompt=JSON 内 `i2v_prompt`（运镜三维写足）。**H3 输出自带原生 AAC 音轨——下载后必 `ffmpeg -i in -c:v copy -an out` 剥离（CEO 音轨禁令·O-20261009-1901）**。逐镜多模态自检 <7.5 分：换 seedance2（mode first_frame，ratio 9:16，720p）重摇并记录。
4. **配音**：`generate_tts`，prompt=JSON `narration` 全文逐字，voice_query=JSON `tts_voice_query`，speed=JSON `tts_speed`；返回 voice_selection_required 则按服务器候选挑一条快嘴男声并复用其 ID。
5. **配乐**：`generate_music`，prompt=JSON `bgm_prompt`，duration_seconds=20，output_format=wav。
6. **装配**：媒体文件按 `media_layout` 落位（S1.mp4…、narration.mp3、bgm.wav）后跑
   `python tools/assemble_meme.py --topic v1 --media <该片 media 夹> --out <该片夹>`
   （读同目录上级 topics/v1-shots.json；旁白实测时长偏离计划 >8% 时加 `--time-scale <实测/计划>`）。
7. **QC 门**（多模态过片 `analyze_multimedia` 五检点，<9 分整改重摇）：①大字幕无错字无遮挡人脸 ②画面无油腻 AI 感/崩坏帧 ③旁白与字幕同拍 ④成片 12-19s ⑤AIGC 水印在左下。
8. **交付+回执**：成片 mp4（单件 ≤50MB，超则 `-crf 23` 降码率；>95MB 硬红线禁入 git）+ 素材表（各镜耗时/自检分/引擎/TTS 音色 ID）+ 发布文案落 `outbound/vN-<slug>/`，commit+push，`outbound/RECEIPTS.md` 加一行回执（机器/时间/成片路径/门检分）。

## 排产与让路
- 每日 3 条 = 1 条车圈连载（连续剧粘性）+ 2 条全网热榜扫描（微博/抖音/百度热榜，按 SPEC-ACCOUNT 选题评分取 2）。
- 错峰：上午 1 片 / 午后 1 片 / 晚间 1 片；与 MV 线/MiniGame 线共享 TJGenerators 配额，超限如实报不硬塞。
- 本线云端生成为主、本地仅 ffmpeg 装配（CPU）=与在飞 GPU 批零冲突；若走本地 ComfyUI 兜底（bm-c int8 H3 768P / Krea2 关键帧），GPU 腾挪按 CEO 直令优先（O-20261008-1755 先例，完事按序恢复）。
- SLA：接单回执 ≤30min（orders 行注 executing+预计完片时刻）·单片 ≤3h。
- 账号未开号前（CEO 物理件：抖音号/视频号注册实名），成片一律入 `outbound/` 待发库，零发布零浪费。
