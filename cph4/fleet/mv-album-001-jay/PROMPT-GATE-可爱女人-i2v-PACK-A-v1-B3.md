# PROMPT-GATE-可爱女人-i2v-PACK-A-v1-B3（第 3 块 KN16-KN23 · 独立评审席）

- **审**=独立评审席（非作者席、非导演席；只报发现不签发）· 2026-10-24 04:5x
- **审对象**：shots KN16–KN23（磁盘现版）＋逐张首帧原生对读；首帧与词面/尾句三方互核

| unit | verdict | 命中 | 理由（最小改法） | 落位 |
|---|---|---|---|---|
| KN16 | FIX | A/B | 首帧纸机肉眼看得到蓝灰横格线且占画面主体，词面 unruled＋small 两处与帧冲突；改「the paper plane holding still above the white sea」，删 unruled 断言 | v2.8 已落（尾挂身份句全撤） |
| KN17 | PASS | — | 纯星空延伸、无新增主体，pushin 缓入缓出齐备；记 warm gold 与帧冷蓝的推色风险 | — |
| KN18 | FIX | E | 词面 slide 缓入缓出，但 tokens.move=static、move_raw 空，机械面与词面互斥；改 move=track | v2.8 已落（token 归一路径补「slides laterally→track」） |
| KN19 | PASS | — | 纸机漂入星流、染金为同体渐变非新主体，track 缓动成立 | — |
| KN20 | PASS | — | 溶解至折痕丝化=设计内延伸（XF_T2 源帧），static 锁机相配 | — |
| KN20b | FIX | A/F | 首帧金机已成型，词面「star dust drawing together」反向要求凝形，会诱发先拆后合；改「The gold paper plane of the frame easing into a slow dive…」 | v2.8 已落 |
| KN21 | FIX | B | 正文 cream/red wing tip ≠ 尾句 plain white unruled/红在尾 ≠ 帧（米色+红在尾）；正文统一「cream paper plane, its single red mark on the tail tip」 | v2.8 已落 |
| KN22a | PASS | — | 单暖窗＋街道延伸，与帧一致、无新增主体；8.2s 静止单见跨块静帧拖时长检点 | — |
| KN22b | FIX | B | 首帧水塔=带锥顶的木质圆筒钢架（非铁皮、无侧梯），尾挂铁皮句会把木桶改成铁皮筒；删尾句，正文改「the dark wooden water tank on its steel legs」 | v2.8 已落 |
| KN23 | PASS | — | 俯望城＋缓降运镜与功能一致，男主钝感骨相未被写成韩系精修；move_raw=cranedn→tokens.tilt 归一差仅记档 | — |

**小计：PASS 5 / FIX 5 / REJECT 0**

## 本块跨镜注意

1. **纸机身份尾句是系统性缺陷不是单点**：全批 9 单挂同一尾句，其中 KN16/KN19/KN29（左机）/KN30（右机）首帧纸面看得见蓝灰横格线，KN21/KN24/KN28/KN30 为米色纸——烧后必检格线是否被抹平、纸色是否被洗白。
2. **HER_PLANE 三口径三方不一致**是 B4 五单全 FIX 的共同根因；v2.8 已统一到「cream + 红在尾尖」，并删掉与之矛盾的全批尾挂句。
3. **KN25 最易翻车**（全片最暗 mean 15.7 + 原词把冷白路灯写成 warm）——已改词，烧后核路灯色温仍冷、左右分居成立。
4. **长窗静止单**（KN22a 8.2s / KN25 5.4s / KN29 7.1s）：源片运动矢量≈0，烧后检「静帧拖时长」与 768P 微抖；必要时补极微呼吸。
5. **KN20b 倒放感**：烧后重点看是否先散后聚、机首是否仍朝下（下坠语义不得回弹为平飞）。
6. **元数据已修**：KN18 move=track；KN15 texture=film_day（跟帧）；KN21/22a/22b 词锚已按 anchors 时间窗重算。