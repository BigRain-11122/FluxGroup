# CT-20261105-bmb-voice-pipeline-status.md

type: judgment
audience: all（音色线相关席位 + 主控排线参考）
urgency: P1

## 管线现况（2026-11-05 深夜）

- 16 槽语料（8 zh AISHELL-3 / 8 en LibriTTS）**全部切片完成**（voices/<slot>/sliced 86-414 片）；
- e01 微调试点 R6 **在飞**（切片窗根修版）；z01 试点申报行 READY 待车道空闲自动接；
- **批量门=双试点 PASS 后才派 14 槽**（批前抽检律，申报行锚点 VCORP-TRAIN-BATCH-14）。

## 关键判例（en 语料的坑）

- **vb_build 默认 3-10s 切片窗对 LibriTTS 连续朗读整段丢弃**（无 -35dB 静音间隙+长句 →
  "+0 clips"×66 → 试点诚实 BLOCK）→ 修法=vb_train_card `--max-clip` 直通，en 语音一律
  25s（zh 的 AISHELL-3 指令式短句保持默认 10s 即可）；
- 重跑前必清 `VB_ROOT/<voice>/` 与 `_m4a/<voice>/` 整目录（多跑残留会引发 SEG-DROP 级联
  把可用语音压到 17 秒的假象）；
- 训练闸=原始语音时长（过滤静音后 ≥ 一定分钟数），部分槽薄数据会诚实 BLOCK——那是真
  缺口不是 bug，候换肥或补料。

## 工装位置（全在 git：Tools/voicebank/）

切片=voice_corpus_prep.py；微调驱动=vb_train_card.py（--max-clip 新参·GPU 卫生内置）；
构建=vb_build.py（44.1k 全保真+身份闸+SoVITS s2）；参考音三闸=vb_pickref.py。