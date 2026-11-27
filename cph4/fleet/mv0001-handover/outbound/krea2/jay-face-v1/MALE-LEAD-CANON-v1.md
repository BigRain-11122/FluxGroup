# 男主角正典·定脸档案（MALE-LEAD-CANON-v1）

- **CEO 定谳**: 男主=范特西(2001)/八度空间(2002)/叶惠美(2003)三时期合成的年轻周杰伦·图生图路线（2026-10-09）
- **标准脸**: BN2_seed9046.png（门检 9.0/10·七项体检全中：睡不醒眯眼+宽颧钝颊+平圆鼻头+厚下唇+长刘海+原生皮肤颗粒+钝感·韩度≈0）
- **正典锁定包**（后续一切男主生成只准在此之上·禁止重抽换脸）:
  - 种子: **9046 固定**
  - 三参照: ref_main_9.jpg（范特西海报·主）+ ref_close_1.jpg（专辑特写裁字）+ ref_mv_91.jpg（MV 91s 帧）
  - 管线: Krea 2 INT8 ConvRot + krea2_style_reference LoRA(1.0) + TextEncodeQwenImageEditPlus 三图同喂 + FluxKontextMultiReferenceLatentMethod(index_timestep_zero)
  - 提示词=骨相锚全开版（krea2_jay_bone.py PROMPT·反韩锚+骨相锚全固化）
- **变体裁则**: 换机位/换光源/换服装只微调场景描述句·身份描述块+种子 9046 一字不动
- **备胎**: BN3_seed9047（8.5·下颌略尖）
- **门检双判据**: ①韩国脸否决（韩度 ≤1 星）②三时期 Jay 气质七项体检（≥9 过线）
- **迭代实录**: 文字路线 7.5 顶 →弱参照 7.0（CEO 判「韩国人」）→反韩锚 MR2 7.5 →骨相锚 BN2 9.0 过线
- ⚠️ 肖像权注: 成片若公开商用需本人授权（已在 ID-REPORT 备案·CEO 风险自裁）
- 生成脚本: krea2_jay_bone.py（随夹）
