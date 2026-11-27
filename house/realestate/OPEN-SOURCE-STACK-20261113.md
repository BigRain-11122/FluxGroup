# 地产 · 装修 · 设计 三条线的开源技术栈选型（2026-11-13）

> 编制：地产子公司 · 研究部　｜　原则：**先找现成轮子，找不到才自研**（CEO 常设令）
> 检索：GitHub 2026-11-13，按 star 排序　｜　许可已标注，未核实的标「待核」

---

## 一、一页结论

| 能力 | 现状 | 结论 |
|---|---|---|
| **CAD 出图（DXF）** | 只有 SVG/PNG，施工方 CAD 打不开 | ✅ **已接 ezdxf（MIT）**，已生成 `plan-A03.dxf`（194 实体 / 11 图层） |
| **工程量（墙长/面积）** | 靠手算 | ✅ **已用同一份几何自动算**：外墙 25.4m、内墙 30.8m、新墙 11.9m、展开面积 183.9㎡ |
| **BIM / IFC 交付** | 无 | 建议接 **IfcOpenShell（LGPL-3.0）**，给施工方/物业的正式交付格式 |
| **户型图自动识别** | 靠人读图 | 有轮子但**许可有雷**（基于 CubiCasa5K 非商用数据），只做内部试点 |
| **3D 可视/漫游** | 无 | 可接 **floorplan-to-3d**（39★）试点，同样受 CubiCasa5K 许可限制 |
| **方案生成 / 板块评分 / 现金流模型** | 自研已有 | **继续自研**——GitHub 上没有适配中国住宅改造的轮子 |
| **算量引擎** | 无 | 不单独找，先用 ezdxf 遍历实体自建（100 行内） |

**一句话：能用的三个轮子（ezdxf、IfcOpenShell、floorplan 识别）已经明确，其中 ezdxf 今天就用上了；方案与财务这两块没有轮子，继续自己写。**

---

## 二、三域能力地图

### 2.1 地产（选址 / 估值 / 现金流）

| 环节 | 我们现在的做法 | GitHub 有没有 | 结论 |
|---|---|---|---|
| 政策与市场数据 | 联网检索 + 人工核 | 无中国本地库（数据源不开放） | 自研，继续用检索 + 网页抓取 |
| 板块评分 | `sector_score.py` 七维模型 | 无可直接用的 | **自研保留** |
| 租金/房价下行数据 | 我爱我家/房天下/贝壳手工取 | 有爬虫但合规风险高 | 只做人工取样，不写爬虫 |
| 现金流/包租测算 | 已内嵌在模型里 | 有 RE 财务模型（多为欧美） | 自研，按国内口径 |
| 产权/规划核验 | 人工调档 | 无 | 人工 |

### 2.2 装修（图纸 / 算量 / 成本）

| 环节 | 现状 | GitHub 轮子 | 结论 |
|---|---|---|---|
| 平面图绘制 | 自研 SVG 生成器（12 张） | `ezdxf` 1,529★ / MIT | **已接，出 DXF** |
| 施工图交付 | SVG/PNG | `ezdxf`、`IfcOpenShell` 2,953★ / LGPL-3.0 | DXF 已用于施工方，IFC 下一阶段 |
| 算量 | 手算 | `cad-ai-agent` 55★（DXF 解析+算量） | 参考其思路，自建 100 行算量 |
| 成本库 | `RENOVATION-PLAYBOOK` 成本卡 | 无中国家装价格库 | 自研，按本地询价校准 |
| BIM 协同 | 无 | `ifc-pipeline` 176★、`massing` 135★ | 需要时再上，现在过重 |
| CAD 编辑器 | 无 | `ingecad` 152★ / GPL-3.0 | 不用（GPL 传染） |

### 2.3 设计（平面 / 3D / 软装）

| 环节 | 现状 | GitHub 轮子 | 结论 |
|---|---|---|---|
| 户型识别（图片→矢量化） | 人读图 | `floorplan-to-3d` 39★（CubiCasa5K UNet）、`rtdetr-floorplan-detector` 6★、`RoomSegmentation` 2★（中文+OCR） | **内部试点**，许可待核 |
| 平面方案生成 | 自研（一改二/三居） | `SCUT-AutoALP` 15★（数据集）、`SkipNet` 5★ | 参考数据集，生成仍自研 |
| 3D 建模/漫游 | 无 | `floorplan-to-3d`（挤出墙体）、Blender | 试点阶段 |
| 软装/效果图 | 文字描述 + D-02 材料板 | 生成式模型（非仓库） | 用现成图像生成，不自研 |
| 家具布置算法 | 自研（按净尺寸规则） | 无成熟轮子 | 自研 |

---

## 三、GitHub 轮子清单（已核 star / 许可）

| # | 仓库 | ★ | 许可 | 能力 | 结论 |
|---|---|---|---|---|---|
| 1 | **mozman/ezdxf** | **1,529** | MIT | Python 读写 DXF；绘图插件可回渲 PNG | ✅ **已接** |
| 2 | **IfcOpenShell/IfcOpenShell** | **2,953** | LGPL-3.0 | IFC/BIM 几何引擎，Python 绑定 | ⏭ 下一阶段 |
| 3 | AECgeeks/ifc-pipeline | 176 | 待核 | IfcOpenShell + Flask 的 BIM 可视化队列 | 参考 |
| 4 | ibuilder/massing | 135 | 待核 | IFC 原生 AEC 平台：算量、proforma、rent roll | 过重，参考其字段设计 |
| 5 | ingelibre/ingecad | 152 | GPL-3.0 | 完整 2D CAD（DWG/DXF） | ❌ GPL 传染，不用 |
| 6 | jeremylongshore/cad-ai-agent | 55 | 待核 | DXF/PDF 图纸分析、算量、LLM 辅助 | 参考算量实现 |
| 7 | **Yytsi/floorplan-to-3d** | 39 | 待核 | CubiCasa5K UNet 分割 → 挤出 3D 墙体，浏览器可转 | ⚠️ 试点（数据许可风险） |
| 8 | jakob-beetz/ifcopenshell-notebooks | 116 | 待核 | IFC 教学 notebook | 学习用 |
| 9 | designfuturelab702/SCUT-AutoALP | 15 | 待核 | 户型/城市布局数据集 | 数据集参考 |
| 10 | OldDeLorean/rtdetr-floorplan-detector | 6 | 待核 | 墙/门/窗/栏杆检测（CubiCasa5K 训练） | 备选 |
| 11 | tonkane/RoomSegmentation | 2 | 待核 | 中文户型图识别 + PaddleOCR | 备选（最贴近国内图） |

> 「待核」= 本次检索未拉到 LICENSE 文件，接入前必须逐仓核实。**star 少于 10 的仓库先用只读方式试跑，不进产线。**

---

## 四、许可红线（比功能更重要）

1. **CubiCasa5K 数据集是 CC BY-NC（非商用）**，基于它训练的权重（#7/#10）**不能直接用于商业交付**。要做，只能：①内部试点验证准确率；②换商用许可数据重训；③只用其网络结构，不用其权重。
2. **GPL-3.0（#5 ingecad）**：链接或分发会传染，商用产品一律不碰。
3. **LGPL-3.0（#2 IfcOpenShell）**：可商用，动态链接、保留声明即可。
4. **MIT（#1 ezdxf）**：随便用，保留版权声明。
5. 任何"待核"的仓库，**接入前先读 LICENSE**，不要凭 README 假设。

---

## 五、今天已经落地的（不是提案，是跑通的）

### 5.1 DXF 出图

- 脚本：`Tools/house/plan_dxf.py`（**ezdxf 1.4.5**）
- 产物：`house/rental-conversion/drawings/plan-A03.dxf`
- 规格：**194 个实体 / 11 个图层**（A-WALL-EXT / A-WALL-INT / A-WALL-NEW / A-WIN / A-DOOR / A-FURN / A-TEXT / A-PLUMB / A-TITLE）
- 做法：双线墙（沿中线偏移 120）、窗洞处断墙、门弧用 16 段折线（避免角度换算错）、中文用 simhei 文字样式
- 坐标：`Y = 8900 - y`，**北在上**，符合 CAD 习惯

### 5.2 回渲自检

- 脚本：`Tools/house/dxf_preview.py`（ezdxf 自带 drawing 插件 + matplotlib）
- 产物：`plan-A03-preview.png`
- 目检结果：墙线闭合、窗（蓝）在洞口、新建墙（红）位置正确、门弧与洁具无错位

### 5.3 工程量（装修报价的基础）

| 项 | 数量 |
|---|---|
| 外墙 | **25.40 m**（240 厚，已扣窗洞） |
| 原内墙 | **30.80 m**（120 厚） |
| 新建轻钢龙骨墙 | **11.90 m**（100 厚） |
| 拆墙 | **0.00 m** |
| 墙体展开面积 | **≈183.9 ㎡**（净高 2.7m，未扣门窗） |

> 这五个数直接进报价：拆改 0、砌墙按米、乳胶漆按展开面积。

---

## 六、7 天落地计划

| 天 | 事 | 产出 |
|---|---|---|
| D1 | 把 12 张图全部导出 DXF（现在只做了 A-03） | `drawings/dxf/*.dxf` |
| D2 | 写算量器：遍历 DXF 实体统计墙长/洞口/地面面积，出 CSV | `quantities.csv` |
| D3 | 用算量结果反算改造报价，与成本卡对账（误差 >15% 要查） | 对账表 |
| D4 | 试跑 `floorplan-to-3d`（只读、内部），拿 3 张真实户型图测识别率 | 识别率报告 |
| D5 | 核实 #7/#10/#11 的 LICENSE，判定能否商用 | 许可结论 |
| D6 | 评估 IfcOpenShell：能否把我们的平面直接升成 IFC 墙体 | 可行性结论 |
| D7 | 汇总：确定「自研 + 开源」的最终技术栈 v1 | 一页栈图 |

---

## 七、与现有产线的接线

```
                 ┌─ gen_drawings.py ─→ 12 张 SVG/PNG（给人看）
同一份几何 ──────┤
   (mm)          └─ plan_dxf.py ────→ DXF（给施工方/CAD）
                          │
                          └─ 算量器 ─→ 工程量 CSV ─→ 成本卡对账
                                    │
                                    └─→（下一阶段）IfcOpenShell → IFC/BIM
```

**关键：几何只维护一份（`gen_drawings.py` 与 `plan_dxf.py` 共用同一套坐标），改一处，图、DXF、算量全部同步。**

---

## 八、不做什么（同样重要）

1. **不写爬虫**抓贝壳/房天下：合规风险、封号风险，收益不如人工取样。
2. **不用 GPL 的 CAD 应用**（ingecad）做底座。
3. **不自研 DXF 解析器**——ezdxf 已经做了 8 年、1,529 星。
4. **不上 BIM 平台**（massing/ifc-pipeline）——现在是 1-5 套房的规模，过重；等有 10 套以上再上。
5. **不把 CubiCasa5K 系模型用于商业交付**，除非换权重或换数据。

---

## 九、来源

1. GitHub 检索 2026-11-13（`search_repositories`，按 star 排序）：ezdxf 1,529★、IfcOpenShell 2,953★、ifc-pipeline 176★、massing 135★、ingecad 152★、cad-ai-agent 55★、floorplan-to-3d 39★、ifcopenshell-notebooks 116★、SCUT-AutoALP 15★、rtdetr-floorplan-detector 6★、RoomSegmentation 2★
2. ezdxf 1.4.5 实测：DXF 生成 194 实体、回渲 PNG 通过
3. 许可：ezdxf MIT、IfcOpenShell LGPL-3.0、ingecad GPL-3.0 为仓库明示；其余标「待核」
