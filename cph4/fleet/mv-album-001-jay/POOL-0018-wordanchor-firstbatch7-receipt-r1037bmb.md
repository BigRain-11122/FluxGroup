# POOL-0018 词锚首批回执 — @bm-b r1037（O-20261019-1935 满负荷令 @bm-b 立领·POOL-0018/0019）

**card**: POOL-0018 词锚批（whisperx small/int8 CPU·word+line 双面·lyric_calibration 消费格式）
**回执窗**: 首批 7 曲 <=2026-10-20 20:2x（本件=6/7 到货面回执·第 7 曲待 Taildrop）

## 1. 首批词锚产物（本批新增 4 曲·r1036 点火 r1037 收成）
| 曲 | words | lines | 时间跨度 (s) | 产物 |
|---|---|---|---|---|
| 安静 | 447 | 11 | 284.62 | `anchors/安静-words.json` (33663B) |
| 开不了口 | 311 | 7 | 215.22 | `anchors/开不了口-words.json` (23352B) |
| 晴天 | 372 | 8 | 234.80 | `anchors/晴天-words.json` (27914B) |
| 简单爱 | 301 | 5 | 187.51 | `anchors/简单爱-words.json` (22542B) |

另有 2 曲 already_done（可爱女人/星晴·先前批在册）。生成器状态面 `words_gen_done ok=4 fail=0`（21:31:37）。音源=`mv-audio-bmb/` 320k mp3（Taildrop 到货 19:53-21:13 六件）。

## 2. 运行诚实披露
- 首跑 21:25:28 处理《安静》报 `'str' object has no attribute 'get'` 瞬态崩（对齐面内部），自愈重启后同曲同码成功（113.9s）——瞬态非病理性，全部 4 曲 ok=4 fail=0 收官。
- 第 7 曲 mp3 未到货（Downloads/Taildrop 扫描 21:3x 无新件）——首批回执按 6/7 面发出，第 7 曲到货后生成器幂等补齐（staging 目录轮询自动纳入）。

## 3. 消费验证（lyric_calibration.py 端到端·PASS）
- `CALIBRATED 安静 mode=whisper exact=9 approx=39 none=3 total=51`（21:36:00）——新 -words.json 格式（words+lines 双面）被校准器 DP 全链消费成功，`anchors/安静-calibrated.{json,txt}` 再生（5155B）。
- 工具面接线：`lyric_calibration.py` SONGS 注册表补 `晴天→晴天-words` 新条目；`安静` 映射由 legacy 拼音面（anjing）翻到新词锚面。
- **遗留映射**：`开不了口→kaibuliaokou`、`简单爱→jiandanan` 仍指 10-15 旧拼音面——是否统一切到新 -words 面 = 下一次校准批派单决策（翻面即再生，幂等零风险）。

## 4. 缺口面（下一批决策件）
- **《晴天》官方词面缺位**（`lyrics/` 无 晴天.txt·校准消费被 MISS 卡住）——需词面供给线补官方 lyrics 后 `python lyric_calibration.py 晴天` 即通（映射已接好）。
- 第 7 曲 mp3 待 bm-c Taildrop 到货。

— via bm-b r1037（2026-10-19 21:3x·词锚批 ok=4 fail=0 + 消费验证 PASS + SDK 解堵链已点火 r1038 收成）

## 5. 第 7 曲核验收口（r1042·首批 7/7 齐平）
- 第 7 曲《龙卷风》mp3 于 10-19 21:34:18 落 Downloads；r1042 拷入 staging 跑幂等核验——`龙卷风-words.json` **早已在册**（10-17 18:16 批产物·30,970B·已被 lyric_calibration 成功消费再生 `龙卷风-calibrated.json` 同窗在案），生成器幂等跳过（`words_gen_all_done`·staged=7 todo=0）。
- 至此 **POOL-0018 首批 7 曲词锚 7/7 齐平**（本批新增 4 + 先前批在册 3：可爱女人/星晴/龙卷风）——§2「第 7 曲待 Taildrop」缺口面结清。

— via bm-b r1042（2026-10-20 00:3x·words 7/7 幂等核验 + POOL-0018/0019 双首批收口同窗）
