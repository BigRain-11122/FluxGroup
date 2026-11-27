# 资产储备施工图 v1（角色 LoRA + 音色库，2026-11-03）

CEO 令：「机队小钢炮和传家宝，先不做短剧和漫剧，先储备资产，比如说去烧各种角色的 lora 和音色库，
你去分配…我很讨厌和别的 ai 一样的 ai 脸和声音，去烧各种有自己特色的，流程自己研究」。

短剧（bigstream-duanju）与漫剧（bigstream-drama）已 PARKED，理由写进 `LINE-REGISTRY.json`。
本文件只讲一件事：**怎么在现有两台机上有特色地攒资产**。

## 一、分配（按显存与角色定，不是按心情）

| 机器 | 显存 | 干什么 | 不干什么 |
|---|---|---|---|
| 传家宝 bm-c | 16GB | **角色 LoRA 主力**（SDXL 1024）+ 音色语料分片 2/4 + 音色微调 | — |
| 小钢炮 bm-b | 8GB | **音色微调主力**（GPT-SoVITS bs=1）+ 语料分片 1/4 | 不做 SDXL 训练（8GB 要开 fused backward，慢且易爆） |
| 公司生产力 bm-a | 8GB | 语料分片 0/4（纯 CPU）+ 夜间可做 ASR 打标 | 不做训练主力 |
| MacBook Pro bm-m | 32GB | 语料分片 3/4（**仅夜间**，白天让给主控脉）+ 闸、编目、抽检 | 不做训练（无 CUDA，MPS 慢一个量级） |

**音色库的分工要点（CEO 2026-11-03「CPU 的算力很强，所有机队都可以去烧音色库」）**：
烧音色库八成工作量是"把脏音频变成训练语料"——转码、静音切分、削波检查、出清单，**纯 CPU、
可断点续跑、可按分片拆到多台机**。所以四台机同时跑 `voice_corpus_prep.py` 的不同分片，
只有最后 SoVITS/GPT 微调那一步吃 GPU（在 bm-b 8GB 上 bs=1 即可）。

依据（实测与社区共识一致）：SDXL LoRA 需要 12GB 起、16GB 舒服；8GB 必须用
`--fused_backward_pass` + Adafactor 才勉强能跑。Flux LoRA 传统要 24GB，kohya v0.9+ 的融合反向传播
能压到 16GB。GPT-SoVITS 的 SoVITS 训练在 10s 切片下：8GB→bs=1、16GB→bs=8；**DPO 训练 12GB 以下做不了**。

## 二、三步走（每步都有机器判据）

### 第 1 步：环境自检（先回答"这台机能不能烧"）

```bash
python Tools/fleet/asset_env_check.py --out cph4/fleet/queue-receipts/asset-env-$(date +%F).json
```
判据：`verdict=PASS` 且 `routes_ok` 非空。缺什么就装什么，装完重跑；**别在 FAIL 的机器上派训练卡**。

### 第 2 步：数据集过闸（这一步决定后面会不会白烧几小时）

```bash
python Tools/fleet/asset_dataset_audit.py --mode face  --dir media/asset/faces  --out cph4/fleet/queue-receipts/asset-face-$(date +%F).json
python Tools/fleet/asset_dataset_audit.py --mode voice --dir media/asset/voices --out cph4/fleet/queue-receipts/asset-voice-$(date +%F).json
```
闸只排除"明显不合格"（网红脸/磨皮脸/播音腔/样本太少），**并且必须先过来源合规门**（目录里的 RIGHTS.json：license 不在白名单、或 real_person=true 无 consent，一律 FAIL）。**PASS 不等于有特色**，见第五节。来源清单见 `SOURCES-V1.md`。

### 第 3 步：训练（在 PASS 的机器上，用下面这套参数起步）

角色 LoRA（bm-c，SDXL）：
```bash
# 数据：media/asset/faces/<角色名>/  12–30 张，1024 分辨率
# 配置要点（sd-scripts/train_network.py + accelerate）
--network_module=networks.lora --network_dim=32 --network_alpha=16
--learning_rate=1e-4 --text_encoder_lr=5e-5 --unet_lr=1e-4
--optimizer_type=AdamW8bit --fused_backward_pass      # 8GB 机器必须；16GB 也建议开
--resolution=1024,1024 --train_batch_size=1 --max_train_epochs=10
--save_every_n_epochs=1 --mixed_precision=bf16
```

音色微调（bm-b，GPT-SoVITS）：
```bash
# 参考音频 1 分钟起，切成 2–12s（越界会爆显存/学不到韵律）
# WebUI：1-GPT-SoVITS → 切片 → 可选降噪 → ASR 打标（必须人工校对，错标会学错字）
# SoVITS: bs=1（8GB），epochs 8–15；GPT: bs=1，epochs 10（不要超过 20）
# DPO：8GB 不做（显存不够 2 倍开销）
```

## 三、反「AI 脸」的可执行规则（数据层，不是提示词层）

只靠提示词写"真实感"没用，数据集本身必须有脏东西：

1. **年龄与体型必须有分布**：不许全是 25 岁瘦脸。每个角色批次里至少含 30+ 与 40+ 脸型各一。
2. **五官必须不对称**：单眼皮/大小眼、鼻梁微歪、嘴角一边高、眉形不一样——AI 脸最典型的特征就是"过度对称"。
3. **皮肤必须有纹理**：毛孔、晒斑、法令纹、痣、痘印至少占两项；闸里的"细节能量中位数"就是这个的机器代理。
4. **必须跨光位**：正面平光、侧逆光、室内暖光、低照度各至少 2 张；只有一种光的批次训出来只会摆一个姿势。
5. **禁止**：磨皮、美颜、高饱和网红调色、纯白背景证件照风。
6. **同一角色 12–30 张，同一张图换背景不算多样性**（闸用近似重复率卡这条）。

## 四、反「播音腔」的可执行规则（同样在数据层）

1. **不要朗读腔**：要对话、要带情绪的短句（抱怨、催促、撒娇、冷笑），不要念文章。
2. **允许并鼓励口音与瑕疵**：轻微方言、吞音、气声、鼻音——这些正是"人味"。
3. **录音条件多样**：手机近场、房间混响、稍远的麦克风都要有；全是棚录干声反而假。
4. **动态要够**：闸用"停顿密度 ≥6 次/分"和"LRA ≥5 LU"两条卡播音腔（播音腔的特征就是把起伏压平）。
5. **禁止**：默认 TTS 音色直接当训练集（那等于克隆 AI 自己）。

## 五、怎么验收"有特色"（机器判不了，必须人看人听）

- **人脸**：用 5 条**训练集里从未出现**的提示词出图（日常疲惫、侧光、低照度、大笑、背影转侧脸），
  只留一张看不出"这就是 AI"的，其余退回重训；同一角色跨 5 图必须是同一个人。
- **音色**：盲听 5 条不同文本，问一句"这是配音员还是一段合成音"；答不出来的才算过。
- 每批资产入库必须带：数据集合格回执 + 5 图/5 条的抽检记录 + license 字段（见 `vault.py`）。

## 六、失效条件（到了就停，不硬撑）

1. 环境自检连续 2 次 FAIL 且原因相同 → 停派训练卡，先修环境（别拿失败当"模型不行"）。
2. 同一角色重训 3 次仍"一眼 AI" → 停这个角色，换设计，不加步数。
3. 音色盲听连续 2 批被听出"合成味" → 停用该数据集，回去补口语化语料。
4. 单批训练真实工时超过 8 小时 → 先查是不是数据集太大/分辨率过高，别加卡。

## 七、指针

- 工序表：`cph4/fleet/ri/content/lines/asset.json`（internal=true，无市场门）
- 闸：`Tools/fleet/asset_env_check.py`、`Tools/fleet/asset_dataset_audit.py`
- 资产库：`Tools/fleet/vault.py` + `cph4/fleet/vault/index.jsonl`
- 目录约定：`media/asset/{faces,voices,loras,voice-models}/`（media 不入 git，台账入 git）