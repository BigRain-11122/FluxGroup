# 星晴 PACK-A 回炉重烧 R1 · 执行进度回执（X2670 §五 progress 面）— bm-c 执行席

> 回执 id=xq-PACKA-REDO-R1-PROGRESS-20261019 · 2026-10-19 17:2x-17:3x · bm-c 执行席（C2083 轮窗）
> 承令=xq-PACKA-REDO-ORDER-20261019.md（X2670·bm-a 导演席 05:23 签发）·执行序=XQ 先行（CEO 11:21 自带令）
> 层判定法=§三1 KF 处置树：原生分辨率像素复核该单 KF 源帧——判读板 media/mv-album-001-jay/qc-split/xq-KF-RECHECK1-REDO-r1019-c2083.jpg（S2-14/S3-19/S3-20/S4-20 四帧 2×2·1000px 格）+ xq-KF-RECHECK2-REDO-r1019-c2083.jpg（F5-33a/S4-24+两备份帧）+ F5-33a 单帧原生 1344×768 直读

## 一 层判定表 6/6（KF 病 / i2v 病）

| # | 镜 | KF 源帧 | 层判定 | 原生证据 |
|---|---|---|---|---|
| 1 | F5-33a | s20234（备 s20233） | **KF 重摇层** | KF 无清晰伪词/零镜像字（原生直读：盘贴空白·deck 面磨损无字）·但左卷盘磁带包边缘带微弱乱痕=伪写种子（clip 三帧清晰伪词串=i2v 放大产物）；验收闸零伪词要求+裁决单 KF 重摇优先令 → 从根治层执行（锚词入 KF） |
| 2 | S4-24 | s21037（t1r1hd） | **KF 重摇层** | KF 本体已带清晰乱码：伪手写 "STUK STORS TOO ILNL" + 橙带伪印刷 "…ils Vnghor crgto slnnph" + 伪厂标 "TD"（TDK 退化版）——裁决稿 A 的标签软化锚必须入 KF 重摇 |
| 3 | S2-14 | s20105（备 s20108） | **i2v 病·直烧** | KF 原生复核恰 2 人零第三人（红橙上衣少女零在场·两备份帧同判）——第三人系 i2v 生成增生 → B 稿双人锚直烧 |
| 4 | S3-19 | s20143 | **KF 重摇层** | KF 本体退化：全帧竖向涂抹+暖耀斑·天空/地平线不可辨（仅抬臂剪影一元素幸存）——dusk sky 不成立于 KF 层 → KF 重摇（八块模板+黄昏天空锚）后 i2v 词面零改动 |
| 5 | S3-20 | s20146 | **i2v 病·直烧** | KF 原生复核双剪影连贯·剪影轮廓/裙摆/地平线全清晰·零纸屑零瓦片缝——三彩纸屑冻结场=i2v 生成面 → 词面零改动+种子换新直烧 |
| 6 | S4-22 | s20158 | **i2v 病·直烧** | KF 原生复核侧影连贯（吉他弦/音孔/弦桥全清晰·背光 bloom=自然镜头行为）——静持+机位重构跳=i2v 生成面 → C 稿指弹动作锚+同框保持锚直烧 |

**层分布=3 KF 重摇（F5-33a/S4-24/S3-19）+3 直烧（S2-14/S3-20/S4-22）**。判读坑律执法：低清板（1000px 格）仅初筛·F5-33a 标签面与 S4-24 乱码面均补原生直读定谳。

## 二 直烧腿已武装（本窗 GPU 即烧·预挂银行 p14）

- **银行单**=xq-redo-i2v-direct3（bm-c-gpu-bank.json priority 14·pending·守卫 ≤10min 自领·PASS 闸=ALBUM LANE DONE ok=3 fail=0+3 mp4≥100KB+progress jsonl ok×3）
- **车道**=bmcpackAredo（assignment-album-v1.json 新道·out=media/mv-album-001-jay/clips-packA-redo-r1·与原 FAIL 片分仓）
- **manifest**=cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-redo-r1-direct3.json（3 单·词面=X2670 B/C 稿逐字+S3-20 零改动·lint 复验 72/75/77 词全带内·零否定·保留句官方口径全在）
- **种子换新律执法**：新 id 族 -redo-r1（id-MD5 派生）→ S2-14=80322 · S3-20=374590 · S4-22=653655（同单同种子禁复用·三单全换新）
- **帧**：三单 KF 原帧不动（层判定=KF 干净）
- **GPU 态**：点火时窗 VRAM 14.3GB free·batchmode 0·ComfyUI :8188 在役——直烧腿当窗点火=化解日窗空窗张力（R2.24 披露面·XQ 先行序不变）

## 三 KF 重摇腿（下一切片·C2084 authoring）

- 单=F5-33a/S4-24/S3-19 三帧 KF 重摇（§三1 试构图律 672×384→1344×768·种子换新·锚词=§二正身：F5-33a「the cassette's paper label blank and age-worn」+对齐 F5-33b 已过件；S4-24 标签软化锚（A 稿锚位）；S3-19 八块模板黄昏天空重建）→ 新 KF 过帧审三件套 → 入 i2v（词面按 §二：F5-33a 零改动/S4-24 A 稿/S3-19 零改动）
- 调度=直烧腿 GPU 在烧期间 authoring（CPU 并行·先做前缀制）·烧毕即挂 KF 重摇银行单
- S3-19/S3-20 解码完整性闸+全部验收闸（§四）=烧后帧检注册表逐项+原生复核·随烧毕回执呈数表

## 四 本窗连带收官件

- POOL-0016 夜系收尾证据板落袋：latentsync-qcboard 输入路径修（trial 消费 repo demo asset 未留拷贝→IN_VIDEO 回退路径·银行 cmd 零改动）+当轮复燃 PASS（板 554460B·6 IN vs 6 OUT 帧）→ R-stack dossier 人眼面就绪·银行 14 单全 done
- 帧检判读正身（31/31=25P/6F·C2060+C2061）已在链·本回执=其回炉执行面首件

—— bm-c 执行席（C2083）· 2026-10-19 17:3x · 验收数表与抽帧随烧毕回执（§五全量面）
