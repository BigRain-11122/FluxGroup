# PROMPT-GATE-可爱女人-i2v-PACK-A-v1 · L1 机械闸回执（C2167 站 2）

- **gate id**：PROMPT-GATE-可爱女人-i2v-PACK-A-v1-L1 · 2026-10-24 04:5x（Get-Date 实测）
- **上游**：`FRAME-GATE-KN-PACKA-c2166.md` verdict=PASS（条件式）· 放行范围明文「准进站 2（提示词闸）」——30 帧 `media/mv-album-001-jay/frames/KN_KN*.png`（1344×768）全部 F1–F8 过闸
- **审对象**：`可爱女人-i2v-PACK-A-v1.json`（30 单 · `可爱女人-shots-v2.py` v2.8 NEW 表逐镜一单 · 正档 1344×768 int8）
- **执行件**：`.codely-cli/tmp/kn_i2v_pack_c2167.py`（构建 + 双闸 + 出清单，幂等可复跑）

## 一、机械闸（双跑：构建时一次 + 落盘后复跑一次，同一输出）

| 闸 | 工具 | 结果 |
|---|---|---|
| 提示词 lint（video 模式） | `prompt_lexicon.lint(prompt, mode="video")` | **30/30 零命中**（NEG/VAGUE/CONCEPT/[FLAT]/长度 15–200 全过） |
| 烧前 guard | `preflight_gate.guard(shot_id, prompt_text, tokens, kf_verified=True, kf_note="FRAME-GATE-KN-PACKA-c2166", kinds=[])` | **30/30 返回空列表** |

- guard 实现来源：`K:\Fluxgroup\hq-wt-c2310\Tools\preflight_gate.py`（全盘唯一副本；本树 `FluxGroup/Tools/preflight_gate.py` 当前缺失=报机制缺口，按只读引用、不新造第二份防漂移）
- guard 的 token 五键按镜头词面归一到 v1 词表（记录原始运镜名在 `move_raw` 字段，供烧制端核对）：`slide→track`、`tiltup→tilt`、`stead/hand→handheld`、`orbit/whippan→pan`、`crashzoom/dollyzoom→pushin`。`scene` 按光块映射（rooftop/city/cloud），`texture` 按昼夜（film_night/film_day），`grade=tw2001` 全包。
- `kinds=[]`：本曲无刻痕/展柜/唱歌/刻写类镜（预检表那四类正向必备锚不适用）。

## 二、量化面（实测）

- 单数 30 · 总窗长 **196.35s**（30 新镜窗口，逐镜按 SHOTLIST v2.7 表）
- 提示词词数 **75–114**（≤200 上限；含追加的身份锁句）
- 时长带：`5s` 档 9 单 / `8-15s` 档 21 单（`src_s = win_s / speed`，全部 ≤15s，无超长源）
- 首帧：30/30 文件在位、非零字节（字节数与 sha12 见包内 `frame_bytes` / `frame_sha12`）· 零缺帧
- 种子：沿用 runner 的 id-MD5 确定性默认（无单内覆盖）
- 音轨：全包零音频描述（CEO 音轨禁令合规）

## 三、v2.8 词面令（本轮回写分镜正身，不重烧 KF）

1. **身份三口径锁死**（FRAME-GATE §五 观察 1–3，站 2 处理）：
   - 纸机＝素白无格线薄纸（`HER_PLANE` 由「cream paper + 一翼尖染红」改为 plain white unruled + 单一红标在**尾尖**）
   - 红色位置＝尾尖（KN21/28/29/30 词面同步）
   - 水塔＝黑色波纹铁皮圆筒带侧梯（对提到 water tower 的镜统一追加锁句 `TOWER_LOCK`）
   - 追加锁句只加在词面（i2v），不回头重烧首帧
2. **清 lint [FLAT] 平速门**：KN01/KN18 原用 `LX.CAM_MOVE["slide"]`（描述含 `at slow speed`）→ 本曲局部 `CM_SLIDE_EASED`（缓入缓出曲线短语），LX 共享词表零改动（不波及他曲）。

## 四、480P 验证片（效率律：先低清验证再烧 768P 全批）

`local-i2v/run-bmc-kn-verify480.json` 三型代表镜（672×384 int4，落 `clips-verify-480`，永不与正片混）：

| 单 | 镜型 | 选择理由 |
|---|---|---|
| KN_A-KN21 | 特写（红尾纸机停檐·13.66s 最长镜） | 最长时长 + 纸机最近特写（身份/红位漂移最敏感） |
| KN_A-KN04 | 动作（掷出 burst 1.20×） | 最快变速 + 手部离手瞬间（动作崩点） |
| KN_A-KN22b | 大远景（水塔+晾衣绳·黑场 56.4%） | 最暗帧 + 剪影辨识（暗部编码风险） |

## 五、产物清单

- `cph4/fleet/mv-album-001-jay/可爱女人-i2v-PACK-A-v1.json`（30 单 + tokens + 双闸字段 + 身份锁）
- `cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-i2v.json`（正档 30 单）
- `cph4/fleet/mv-album-001-jay/local-i2v/run-bmc-kn-verify480.json`（验证 3 单）
- 分镜正身：`可爱女人-shots-v2.py` 升 **v2.8**

## 六、未签发

本件只做机械面。专家面 verdict 见 `-B1..B4`，合并签发见 `-SIGN`。**未过 SIGN 不得起烧。**