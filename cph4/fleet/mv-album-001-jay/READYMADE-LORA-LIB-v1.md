# 现成 LoRA 库 v1（READYMADE-LORA-LIB-v1 · 开源社区捞货）

> 令源：CEO 2026-11-12「github 或者开源社区有现成的女主也可以下载下来建库，但不要常见的烂大街的」。
> 口径：私有非商用（同 LORA-FACE-LIB-PLAN-v1 §〇）。产线正片仍走 CASTING-LAW 原创脸。
> 选品器：`Tools/lora_scout.py`　库目录：`media/lora/readymade/`（gitignored，不入仓库）

## 一、为什么不能按「Most Downloaded」挑

热门榜是**反向指标**：所有人都在用同一批脸 → 片子必然撞脸，而且那批模型正是「一眼 AI 网红脸」的源头。
所以选品用四个反向调整：**热度取中段、看点赞率、要具体性、避开通用美女词**。

## 二、准入五关（缺一不入库）

| 关 | 判据 | 判法 |
|---|---|---|
| 1 非通用脸 | 名称/标签命中通用词（asian beauty / korean beauty / perfect face / realistic girl / 美女 等）→ 直接剔 | `lora_scout.py` 内置黑名单 |
| 2 热度中段 | 下载 200–20000；>2 万视为烂大街，<200 视为未验证 | 同上，log 距离打分 |
| 3 质量佐证 | 赞/下载 ≥0.5%，且赞 ≥50 | 防"刷下载" |
| 4 具体性 | 名称/标签含年代/媒介/风格词（1990s/film/kodak/editorial…）或像人设名 | 加分项 |
| 5 可得与许可 | 有公开直链、`.safetensors`、许可字段留档 | 下载时校验文件头 |

综合分 0–100，`--min-score 55` 起。

## 三、落库规则

- 文件放 `media/lora/readymade/`（gitignored，单件动辄 200MB+，绝不进 git）
- 台账放 `cph4/fleet/mv-album-001-jay/readymade-lora-lib.json`（进 git，只记元数据+哈希）
- 一个文件必须能回答三问：**它治什么（角色/质感）· 触发词是什么 · 从哪来（模型页 URL）**

## 四、用法

```bash
# 选品（多关键词合并、自动去重与打分）
python Tools/lora_scout.py search --queries "film portrait,1990s portrait,35mm woman" \
    --base "Flux.1 D" --top 20 --out cph4/fleet/mv-album-001-jay/lora-candidates-flux.json

# 按标签扫真实角色类
python Tools/lora_scout.py search --tag character --base "Flux.1 D" --top 18 --out cand.json

# 下载（受限模型需 CIVITAI_TOKEN；无 token 会明确报错而不是写出坏件）
python Tools/lora_scout.py fetch --version-id 1949248 --out media/lora/readymade
```

## 五、2026-11-12 首轮实测

- 抓取 597 条（两轮 6 组关键词），通用脸剔除 28 条，过线 40 条
- **质感类命中一批**：analog / Kodak Vision3 / Gold 200 / Ektar / ECHROME / 35mm / Polaroid / 2000s Flash —— 这批正好打 AI 感 L2（光学）与 L3（噪声谱），可组合使用
- **人物类现状**：社区里"东亚年轻女性脸"的 LoRA 大量是通用美女款（已全部被黑名单剔掉）；剩下的要么是真人明星，要么是二次元/风格向。**结论：脸层自训，质感层外购**
- 下载：`2000s Flash Portrait`（219MB，触发词 `harsh flash photography`）成功入库；`Analog Photo Style`、`Portrait Artifacts` 直链返回登录页（Civitai 已收紧），需 token

## 六、kill criteria（出现即下架）

1. 用了它之后「盲评判 AI」比例上升 → 立刻停用（说明它加的是塑料而不是质感）
2. 触发词污染：不写触发词也出它的味道 → 底模被带偏，弃用
3. 许可字段与商用冲突且我们要商用 → 出库（私有实验不受此限，但台账要标）
4. 每次上新都必须过 `Tools/deai_metrics.py` 前后对比，说不出改善数值的不入库
