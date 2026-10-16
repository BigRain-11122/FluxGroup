# JAY-REDO-RESHAKE6-VERDICT-r1033 — 导演席复检定选（6 槽 4选1）

- 签发: bm-a 装配站·导演席 · 2026-10-16 11:4x（O-20261016-1120 直连同步指挥律执法窗）
- 对象: JAY-REDO-RESHAKE6-BOARD-r1032.jpg（bm-c r1032 · 24 KF 海选板 · O-1725 海选制）
- 结论: **6/6 槽定选全过 · 零回炉 · 全部进 i2v**

## 定选表（胜者帧 → i2v 输出）

| 槽 | 胜者 | 帧文件（kf_r1032/） | i2v 输出名 | seed |
|---|---|---|---|---|
| E01c_first_line | s0 | rs_E01c_first_line_s9600.png | E01c_first_line.mp4 | 9800 |
| SIL2_ots_crowd_v4_s9018 | s0 | rs_SIL2_ots_crowd_v4_s9018_s9604.png | SIL2_ots_crowd_v4_s9018.mp4 | 9801 |
| SING1_torch_song_v2_s9013 | s0 | rs_SING1_torch_song_v2_s9013_s9608.png | SING1_torch_song_v2_s9013.mp4 | 9802 |
| C01_carver_face | s0 | rs_C01_carver_face_s9612.png | C01_carver_face.mp4 | 9803 |
| B01_weary | s2 | rs_B01_weary_s9618.png | B01_weary.mp4 | 9804 |
| D01_carver_words | s3 | rs_D01_carver_words_s9623.png | D01_carver_words.mp4 | 9805 |

弃格记录: SIL2 s2/s3=展柜内蜡像人影（处方违例）· SING1 s2=右缘人形剪影 · SING1 s3=正面英气站姿（处方=半瘫）· C01 s1=颊部高光微塑料（AI-tell）
导演风险提示: E01c/D01=手-工具接触面在运动中最易熔接——i2v 出熔接即判负重烧（四闸帧级 QC 把关）

## 补烧规格（@bm-c r1034 执行 · P0）

1. 工作流 = h3_i2v_local_768p_v4.json 同 r1032 Phase D（INT8 768P 5s · 24fps · 1344×768 · 音轨禁令 · skip-if-exists）
2. i2v 提示词 = JAY-REDO-PACK-v1.py SHOTS 各槽 iv verbatim，**唯 SIL2 处方覆盖（导演令）**:
   原包 iv「one blurred visitor wipes across the near frame and clears」**废弃** →
   `"Single continuous take at 24fps, 16:9. A medium shot over his shoulder; the camera holds a locked-off tripod frame while his gaze holds the stone through one slow blink, the empty aisle still in the amber dark. " + I2V_TAIL`
   （清场处方一致性：KF=空馆，i2v 禁再引入访客）
3. 帧缺失兜底: kf_r1032/ 帧若被清，按 receipt json 同 seed 同 prompt 重烧 KF（确定性复现）再进 i2v
4. 6 件烧毕 → **17 件拼 jayredo_qc_sheet**（bmc/i2v/jayredo/ 全量）→ 原子链 push（clips+sheet+orders 回执行）→ poke bm-a 装配站
5. 时限: P0 · 2h 超时哨在役（O-20261016-1120 §4）· 烧毕即推禁攒批
6. 11 放行件已在 bm-a **确认收讫**（bmc/i2v/jayredo/ 11 件 10-15 20:38 落盘）——无需重烧

## 装配站备货（bm-a · 并行进行）

- 17 件齐 → V4 装配（find_src 同名收片 · 窗口表=pack SHOTS 窗注 · V3 时间线 v3_blockA/B 已在位）→ 四闸 → CERTIFIED → 呈 CEO
