# 方案规格：资产库：六类缺口体检并出补齐优先级

- 线：asset-lib｜类型：asset｜生成：2026-11-05T17:46:29
- 产出目录：`cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级`

## 一、目标（一句话，可判）
资产库：六类缺口体检并出补齐优先级

## 二、验收判据（机器可判，不靠感觉）
1. 每一步都有交付物路径且在本仓内；
2. 每一步 ≤10 分钟（超了就再拆，不许出现"一周的卡"）；
3. 第一步产物在转化当分钟就存在且非空；
4. 卡序列全部进备队列，主控 45 秒内可接走。

## 三、步骤（颗粒度：每步一件可验物）
| # | 阶段 | 做什么 | 交付物 | 分钟 |
|---|---|---|---|---|
| 1 | 01-取证 | 确认输入在盘、算出基线（多少件、指纹、缺口） | `cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级/step1-取证.json` | 3 |
| 2 | 02-加工 | 对输入做本方案的核心加工；有 --tool 就真调，没有就先落可执行骨架与输入输出契约 | `cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级/step2-加工.json` | 8 |
| 3 | 03-验收 | 跑机器可判的判据并出 PASS/FAIL 清单（含本仓验收腿的真实回执） | `cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级/step3-验收.json` | 4 |
| 4 | 04-交付 | 出交付清单草稿：谁签、缺什么、可发物定义是否满足 | `cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级/step4-交付.json` | 4 |

## 四、命令
1. **01-取证**（≤3 分钟）
   ```
   python3 Tools/fleet/plan_convert.py --probe cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级 cph4/fleet/asset-lib-v1
   ```
2. **02-加工**（≤8 分钟）
   ```
   python3 Tools/fleet/plan_convert.py --step 2 --conv cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级 --tool python3 Tools/fleet/asset_library_check.py
   ```
3. **03-验收**（≤4 分钟）
   ```
   python3 Tools/fleet/plan_convert.py --step 3 --conv cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级
   ```
4. **04-交付**（≤4 分钟）
   ```
   python3 Tools/fleet/plan_convert.py --step 4 --conv cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级
   ```

## 五、风险与前置
- 输入在盘检查：cph4/fleet/asset-lib-v1（缺料则第 1 步以 BLOCKED 落盘并具名缺什么，不造假产物）
- 加工工具未指定时，第 2 步先产出"可执行骨架 + 输入/输出契约"，不许空跑
- 本规格不改变任何既有阈值；阈值仍只认 AUTONOMY-CONFIG.json

## 六、下一分钟能看到什么
`cph4/fleet/conversions/20261105/资产库-六类缺口体检并出补齐优先级/step1-取证.json`：输入在不在盘、各多少件、指纹。
