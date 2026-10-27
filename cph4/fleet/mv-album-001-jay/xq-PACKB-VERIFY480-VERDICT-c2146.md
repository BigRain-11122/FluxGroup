# 星晴 KF-PACK-B 480P 验证判定（C2146）

- 日期：2026-10-20
- 判定席：bm-c 引擎 tick C2146
- 输入波：`packB-verify480`（lane=bmcverify · 672×384 · int4 · 3 镜 · pythonw hidden 发射 14:42）
- 产物目录：`media/mv-album-001-jay/clips-verify-480/`
- 判读法：ffprobe 技术面 + 逐片多模态运动/身份判读（低清验证律：先 480P 确认运动与漂移，再 768P 正片）

## 一、技术面（ffprobe 实测）

| 镜位 | 文件 | 字节 | 分辨率 | fps | 帧数 | 时长 |
|---|---|---|---|---|---|---|
| XQ_VERIFY-S3-17 | XQ_VERIFY-S3-17.mp4 | 1,044,286 | 672×384 | 24 | 175 | 7.292s |
| XQ_VERIFY-S5-31 | XQ_VERIFY-S5-31.mp4 | 460,603 | 672×384 | 24 | 277 | 11.542s |
| XQ_VERIFY-S2-10 | XQ_VERIFY-S2-10.mp4 | 746,570 | 672×384 | 24 | 192 | 8.000s |

波终态：`ALBUM LANE DONE lane=bmcverify ok=3 fail=0`。三片时长与 manifest src_s 对齐（无截断、无空帧）。

## 二、逐片判定

| 镜位 | 判 | 依据 |
|---|---|---|
| S3-17 脚+白线（特写） | **GO** | 双脚交替步频自然，落脚有接触不滑不飘；机位全程锁死零漂移；鞋/小腿结构完整无融化、无多趾、纹理不爬 |
| S5-31 双人牵手（双人） | **GO** | 两张脸全程同一对人（无换脸/无漂移/发型服装稳定）；牵手在第一秒即落且指部不粘连不多指；动作幅度克制无橡皮肢；机位稳 |
| S2-10 金黄草坡（空景） | **GO** | 草浪方向一致成一阵风带（非沸腾噪声）；白线路径与地平线稳定不呼吸不抖动；机位微漂平滑（非 Ken Burns 推拉）；无闪烁/无色彩泵动 |

## 三、结论

**三镜全 GO，768P 正片波放行。** 运动维度在 480P 已证成：步频接触正确、牵手落点正确、草浪成阵；身份维度在双人镜证成不漂移。480P 未暴露的只剩高分辨率下的皮肤/织物细节，属 768P 收割轮的帧级判定面。

## 四、证据清单

- 验证 manifest：`cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-packB-verify480.json`
- 生产 manifest（已放行）：`.../run-bmc-packB-i2v.json`（6 镜 · 37.16s 屏时）
- 构建器：`cph4/fleet/idle-guard-kit/kfpb_i2v_manifest_c2146.py`
- 执行日志：`media/MV/mv0001/logs/kfpb_verify480_c2146.out.txt`（err 0B）
- 进度台账：`media/mv-album-001-jay/clips-verify-480/progress-bmcverify.jsonl`
- 执行回执：`cph4/fleet/mv-album-001-jay/xq-PACKB-VERIFY480-RECEIPT-c2146.json`

## 五、下一步

1. 768P 六镜正片波已点火（14:52 · lane=bmc · 1344×768 int8 · log `logs/kfpb_packB_768p_c2146.out.txt`），本草判据=ok=6 且每片 ≥900KB。
2. 收割后帧级判定（原生尺寸读）：手/脚解剖、皮肤是否蜡、夜戏肤色、年代服装、无字无 logo。
3. 通过 → A+B 合装（A 196.14s + B 37.16s 屏时，装配站按 SHOTLIST 时间码插入 B-EX 两镜）。