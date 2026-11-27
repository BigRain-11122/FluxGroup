# 资产库体检（2026-11-19，只读审计）

## 一、资产在哪（真实路径，非推测）

- 盘上实主根：`/Users/junsheng.sun/FluxAssets`（ASSET-STORE.json `roots[0]`，role=primary），269MB，`store/` 下 643 个文件、`incoming/` 下 37 个文件。
- **正身两处打架**：`ASSET-VAULT.json` 写 `vault.path=null / status=EMPTY / files=0`；而 `ASSET-STORE.json` 的 primary 根上真实存在 643 个文件。工具因 `vault.root()` 回落到 ASSET-STORE 才没坏，但凡读 ASSET-VAULT.json 的人都会认为库是空的。
- `/Volumes/移动硬盘` **未挂载**（当前只有 Macintosh HD、Recovery）；台账里 8 行账面在此，原件已于 2026-11-11 按 CEO 令清空，**不可恢复**。
- `python3 Tools/fleet/vault.py verify` → `台账 651 条 · 可达 643（根 /Users/junsheng.sun/FluxAssets）· 可从 origin 重建 0 · 历史快照 8 · 真缺失 0`（rc=0）。

## 二、类别表（数量=盘上实见，全部来自命令输出）

| 类别 | 数量 | 最近更新 | 缺口 / 冗余（证据） |
|---|---|---|---|
| characters 角色包 | **0 张图**（8 个目录各 1 个 PROMPTS.json） | 2026-11-18（只改 json） | 缺 8。8 个空壳目录 = 纯冗余壳（`media/asset/characters/CH01..CH08/PROMPTS.json`；`SUPPLY-P0.json` totals usable=0/128） |
| scenes 场景 | 0 | 无 | 缺 12（`media/asset/scenes/` 空） |
| props 道具 | 9 png（+9 txt+1 json） | 2026-11-09 | 缺 11；`ASSET-MANIFEST.json` 11-03 就记 count=9/20，16 天零进度 |
| motions 动作 | 0 | 无 | 缺 15。store 里 66 个 mp4 无类别归属，数不进这一类 |
| transitions 转场 | 0 | 无 | 缺 10 |
| styles 风格 | 0 | 无 | 缺 3 |
| voices 音色 | 6 wav（1 个 batch） | 2026-11-16 | 缺 5；另 24 条 mp3 停在 `incoming/voices/` 未入库 |
| audio-sfx 音效 | 0 | 无 | 缺 40，P0 最大单块缺口 |
| audio-bgm 配乐 | **0 入库** | 2026-11-07（在 incoming） | 账面 OK 是**假绿**：10 条全在 incoming，被算作"待入"抵掉了缺口（`state/asset-gap.json`） |
| typography 字体 | 0 | 无 | 缺 4 |
| 台账/存储 vault | 651 行 / 643 可达 / 269MB | 2026-11-03（此后 0 新增） | **冗余**：651 条 origin 全在仓内，643 条与 origin 逐字节同 sha → 整库是仓库文件的一份副本，净新增资产 0；`license=unknown` 651/651；`gate_status=pending` 651/651；kind 错标 359/651；8 行原件在已清空移动盘 |

`asset_gap_audit.py` → `P0 达标 1/10`（唯一"达标"的 audio-bgm 见上，实为 0）；`asset_incoming_verify.py` → `核验通过 34，不一致 0，未登记 0`（voices 24、audio-bgm 10）。

## 三、最该先做的三件

**① 让"入库了"能被数到（度量先修，否则后面全是假账）**
- 症状：`vault.py add` 入的是 `store/<sha前2>/<sha><ext>`，而 `asset_gap_audit.count_cls` 数的是 `VAULT/store/<类别>/`；盘上 store 下类别目录 **0 个** → 真入库的素材在这张表里永远显示 0。
- 根因：两套目录约定不一致（内容寻址 vs 类别分层），且 gap 用 `gap = p0 - have - pending` 把 incoming 当抵扣。
- 最小改法：台账行加 `class` 字段（`vault.py add --class`），`count_cls` 改为"读台账、按 class 计数、要求 `resolve()` 成功"，删掉 pending 抵扣；顺手把 `ASSET-VAULT.json` 的 `vault.path` 指向 `~/FluxAssets`、status 改 ACTIVE。
- 验收：给 10 条 bgm 标 `class=audio-bgm` 后，gap_audit 报"已入 10 / 缺 0"；未标 class 的行不落进任何类别；ASSET-VAULT.json 与 ASSET-STORE.json 指向同一根。

**② 34 条已核验素材真入库 + 8 条死行退场（0 成本，当天见效）**
- 症状：incoming 的 24 条音色 + 10 条 BGM 从 11-07 躺到现在，`asset_incoming_verify` 34/34 全 PASS 却一条没进库；同时 8 行台账原件在已清空盘上，永久不可达，仍占"历史快照"名分。
- 根因：没有"核验通过 → 入库"的动作；8 行是 origin 漂移后留下的快照，盘清空后却没有退场机制。
- 最小改法：`vault.py add ~/FluxAssets/incoming/audio-bgm ~/FluxAssets/incoming/voices --kind audio --class ...`；8 行标 retired（或删行，`storage/deleted-assets-manifest-20261111.jsonl` 已有清单可引）。
- 验收：`vault.py verify` 的历史快照由 8 变 0；`vault.py list --kind audio` ≥34 行；incoming 媒体文件剩 0；gap_audit 的 audio-bgm 由"待入 10"变"已入 10"。

**③ 补 P0 里"零件齐、只差执行"的一类：characters 8 个空壳出图**
- 症状：CH01–CH08 八个目录各只有 1 个 PROMPTS.json，0 张图；`SUPPLY-P0.json` 从 11-03 就记 usable=0，四份状态文件（LIBRARY-TARGETS/ASSET-MANIFEST/SUPPLY-P0/asset-gap）各说一套。
- 根因：角色包只做到"写提示词"，缺 出图 → 入库 → 计数 的闭环；gap 判据要求每目录 ≥6 张 ≥1024 边，提示词再好也不计数。
- 最小改法：用现成 PROMPTS.json 各出 6 张 1024 长边，落 `media/asset/characters/CHxx/`，再 add 入库（characters P0=8）。
- 验收：gap_audit `characters 已入 8 / 缺 0`；8 个目录各 ≥6 张图；`RIGHTS.json` 覆盖全部 8 个角色。

## 四、我验证了什么 / 我没验证什么

验证过的（有命令输出）：①`vault.py verify` 651/643/0 缺失/8 快照；②`asset_gap_audit.py` 1/10 与逐类数字；③`asset_incoming_verify.py` 34 通过 0 不一致；④全量 sha256 比对 651 行——643 条与仓内 origin 逐字节相同、8 条 origin 已漂移、origin 全部位于 FluxGroup 仓内；⑤盘上清点：store 643 文件（369 jpg/160 png/66 mp4/33 md/9 json/2 mp3/2 txt/1 log/1 jsonl）、md5 重复 0 组、`store/` 下类别目录 0 个、`-newermt 2026-11-08` 命中 0；⑥台账字段统计：license/gate_status 全 unknown/pending，kind=report 413 行里 359 行其实是 jpg/png/mp4。`Tools/asset_index.py list` 跑通但**空输出**——它的索引路径硬编码为 `C:\Users\sjs20\...\ASSET-INDEX.jsonl`，macOS 上不存在，与本资产库无关（孤儿工具）。

**没验证**：`/Volumes/移动硬盘` 未挂载，那 8 行只能读台账里的旧记录，无法核对原件；66 个 mp4 与 529 张图的分辨率/时长/画面/授权内容**未抽检**（只数了文件，没看内容）；`media/` 库外 43 个 mp4/wav/mp3（review-720p 21、drama-out 8、asset 8、drama-sample-v2 6）只按 origin 字段确认台账 0 条引用，**未做内容去重**；props 9 张 png 的 alpha 通道与 1024 边长未验；未执行任何生成、采集或入库动作（本次纯只读）。
