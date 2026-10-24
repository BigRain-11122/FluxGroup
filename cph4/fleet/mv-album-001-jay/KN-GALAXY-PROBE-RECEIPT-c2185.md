# 回执 · KN 银河段词面重写 + 480P 探针（C2185）

- **片**：《可爱女人》KN PACK-A 整片 v1（C2183，239.04s）
- **上游**：`DIRECTOR-REVIEW-KN-FULL-v1-c2183.md` verdict=REVISE，唯一内容不通过项=银河段（KN17/KN18）
- **本批**：词面重写 + 480P 验证切片发射（GPU 车道 bmcverify 672×384 int4）

## 诊断（先证伪再动刀）

导演档判「120.0s 实读为金色线状/环状缠绕（枝条感/网状/近虫形）」。本批先查两张关键帧原图：

| 件 | 判 | 说明 |
|---|---|---|
| `frames/KN_KN17.png` | 干净 | 真实银河带 + 无数离散暗点，无成环/成线 |
| `frames/KN_KN18.png` | 干净 | 同上，近景仍为离散星点 |
| 成片 120.0s 抽帧（assembly `chk-120.png`） | **病灶确认** | 金色网状/环状缠绕 + 圆形光斑，正是导演档所判 |

结论：**关键帧无罪，漂移由运动提示词产生**——旧句里的连续体名词给了模型可编织的对象：

- KN17：`the whole arc of a warm gold star band arched across` / `the star dust wheeling` / `the dust cloudlike`
- KN18：`the star dust of the galaxy band` / `pale currents drifting` / `the dust cloudlike`

因此本批不重烧关键帧（省一次 GFG/风格闸），只改运动层词面。

## 改动

1. **作者层词面重写**（`可爱女人-shots-v2.py`，精确 count==1 断言落刀，两处）：
   - KN17 → `The night sky full of countless separate round points of warm gold light, each point small, round and distinct, spread evenly through an ink-blue sky, the points drifting apart at the slowest breath, the cloud deck a dark rim below the frame`
   - KN18 → `The night sky in close detail, countless separate round points of warm gold light scattered evenly through deep blue-black, every point small and round and distinct, the points drifting apart at the slowest breath, the darkness between them clean`
   - 删去：arc / band / arched / wheeling / currents / cloudlike / stream 系连续体表述；改为「可数的圆点 + 最慢呼吸的离散漂移」。镜位与运镜子句未动。
2. **验证清单生成器**：`c2185_kn_galaxy_wordface.py`（从作者层现文重派生，杜绝旧文案进波；内嵌 hygiene 闸，rig 名词 FAIL 即拒发）
3. **探针清单**：`local-i2v/run-bmc-kn-galaxy480-c2185.json`（2 单，KN_G1-KN17 win 8.46s / KN_G1-KN18 win 9.06s）
4. **无人值守发射器**：`c2185_kn_galaxy_probe_launch.py`（server 探测→按需起→跑波，全 hidden 无窗）

## 门禁

| 闸 | 结果 |
|---|---|
| `kn_prompt_hygiene_gate`（2 单） | PASS（rig 名词 0） |
| 关键帧在位 | PASS（两帧已在盘，未重烧） |
| 词面预算 | 99 / 96 词（政策带内） |
| 480P 探针 | **在飞**（见下） |

## 在飞与下一步

- 探针日志：`media/mv-album-001-jay/logs/kn-galaxy480-c2185.log`；产物落 `clips-verify-480/`
- 收割轮任务：①看两片是否仍是网状/环状（人眼抽 3 帧）②过 `kn_framing_drift_gate`（本批为建立镜，需真推）③绿→两单 768P 重烧 ④装配站一条命令重跑（`kn_full_assembly_c2183.py`）→ 新 v2 整片 → 导演席复判
- 导演档另两项未在本批：编辑层「本曲零叠化」需导演席认可后写进正身脚本头注记；调色 v2（halation 位 + 逐锚 3 帧实测 + 两曲并排盲评）留独立批

## 纪律

- 无 `tier=placeholder` 冒充成品；本批产物为**验证切片**，不入正典、不计成品。
- GPU 单道长批为常驻 pythonw，会话死批不死。