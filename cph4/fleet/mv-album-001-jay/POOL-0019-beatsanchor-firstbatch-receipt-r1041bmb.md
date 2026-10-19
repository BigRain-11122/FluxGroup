# POOL-0019 节拍锚首批回执 — @bm-b r1041（O-20261019-1935 满负荷令·O-20261015-1741 POOL 承接）

**card**: POOL-0019 节拍锚批（madmom-0.16.1 RNNDownBeat+DBN·fps100·beats_per_bar [3,4]·CPU 车道）
**回执窗**: 首批 7 曲 <=2026-10-20 20:2x（本件=**6/6 可产面全胜收口**·第 7 曲 mp3 待 Taildrop 到货后幂等补齐）

## 1. 首批节拍锚产物（6/6 全 OK·r1041 修复后点火 00:20:10→00:25:09 全批 5 分钟）
| 曲 | beats | downbeats | 时长 (s) | 中位 BPM | 产物 |
|---|---|---|---|---|---|
| 可爱女人 | 533 | 133 | 239.03 | ~133 | `anchors/可爱女人-beats.json` (16,778B) |
| 安静 | 389 | 98 | 334.23 | ~70 | `anchors/安静-beats.json` (12,390B) |
| 开不了口 | 320 | 80 | 284.97 | ~67 | `anchors/开不了口-beats.json` (10,201B) |
| 星晴 | 378 | 95 | 259.40 | ~87 | `anchors/星晴-beats.json` (11,982B) |
| 晴天 | 304 | 76 | 269.75 | ~68 | `anchors/晴天-beats.json` (9,680B) |
| 简单爱 | 425 | 107 | 270.99 | ~96.8 | `anchors/简单爱-beats.json` (13,464B) |

格式契约：`{song, source, model, n_beats, n_downbeats, duration_sec, beats:[[t,beat_pos]...], downbeats:[t...]}`——卡点剪辑（CHK-E4 卡点 ≤0.1s 面）/节拍对齐下游可直接消费。

## 2. 修复链诚实披露（r1040 首点火 0/6 → r1041 6/6 的两处根因）
1. **r1040 批 23:27 无声死**：`RNNDownBeatProcessor/DBNDownBeatTrackingProcessor` 构造在 try 块外，构造崩溃无 traceback（pythonw detached stderr 未落）——根因=madmom Cython 编译产物（ml/hmm.pyx→.pyd）内残留 `np.int` 族调用（r1038 文本补丁只及 .py 面 19 件，编译面不可文本修）；修法=**运行时 numpy legacy 别名恢复**（int/float/bool/object/complex/str/long/uint）+构造挪进 try 带日志（`anchor_beats_gen.py` r1041 面）。
2. **r1041 首复跑 0/6 全 FAIL**：`madmom/features/downbeats.py` L287 `np.argmax(np.asarray(results)[:, 1])`——results 为 ragged (path,log_prob) list，numpy 2.x `np.asarray` 抛 inhomogeneous ValueError；修法=**venv 内文本补丁**（`int(np.asarray([r[1] for r in results]).argmax())`，语义恒等只抽标量列）+30s 短样复现验证（ACT OK (3000,2) → DBN OK (67,2)）。
- 点火载体=S4U 单发任务 `bm-b-BeatsGen-r1041`（pythonw 零窗·CLI 会话死亡连坐免疫）。

## 3. 消费验证（结构契约探针·PASS 6/6）
`POOL-0019-beats-consumption-verify-r1041bmb.json`：逐曲断言 pos∈[1,4]/时间戳严格单调/downbeats⊆beat_pos=1 帧/首拍 <5s 尾拍距终 <15s/计数自洽——6/6 全绿 fails=0。探针正身=`_r1041_beats_consume_verify.py`（read-only）。
- 注：`lyric_calibration.py` 现版本消费词锚面（POOL-0018 域）；beats 消费线=生成器头注预告位（节拍级校准接入=下一批派单决策件）。

## 4. 缺口面（下一批决策件）
- **第 7 曲 mp3 未到货**（Downloads/Taildrop 扫描 00:1x 无新件）——到货后 `bm-b-BeatsGen` 幂等补齐（staging 目录轮询自动纳入），7/7 收口随到随补。
- venv 补丁面维护性：numpy 别名补丁焊在生成器入口（跟随脚本走）；downbeats.py 补丁在 venv 内（venv 重建需重打——已在本件 §2 留档配方）。

— via bm-b r1041（2026-10-20 00:2x·beats 批 ok=6 fail=0 + 消费验证 PASS 6/6 + 回执窗提前兑现 20h）
