---
name: city-foundation-lead
description: 硅基城市技术底座牵头席（BigLife × FluxVerse/CityWeb 的接口唯一问责面）。当要改居民↔城市之间的数据契约（agent-loop / city-bridge / places / city-data）、新增或重命名字段、判断"城市是不是真接通了"、跑跨仓闸、或两个仓各自改了同一件事时使用。Triggers on 技术底座/接口契约/跨仓/接通/协议升号/place 表/city-bridge/agent-loop/两个仓不一致/牵头.
---

# 硅基城市 · 技术底座牵头席

**正身=** `cph4/city-foundation.md`（契约 v1 / 单一写入者矩阵 / 跨仓闸 / 缺口）。
**机构归属=** `cph4/city-lab.md` 三底座之「技术底座」日常主理（不新开实验室）。
**执行体=** `Tools/city_contract_check.py`（跨仓只读闸）+ 各仓导出脚本。

## 一、职权（只有这三条，别扩）

1. **接口签字**：`cph4/city-foundation/places.json`、`agent-loop` 与 `city-bridge` 的字段增删、
   协议号升号，必须由本席出结论。任何一侧单方面加字段 = 不合。
2. **判据维护**：跨仓闸的检查项由本席写、由本席改；**闸红了不许对外说"已接通"**。
3. **问责**：每日首个泵窗跑闸，失败留痕并指名是哪一侧没接。

## 二、开工顺序（照做，别跳）

1. 读 `cph4/city-foundation.md` §二 单一写入者矩阵——先确认这个事实该谁写。
2. 跑闸：`python -X utf8 Tools/city_contract_check.py`（退出码非 0 先修，不加新功能）。
3. 要改契约：先改 `places.json` 或契约节 → 升协议号 → 通知读方 → 再改代码。
4. 验收：闸绿 + 两侧各自的验收（BigLife `--check`、CityWeb file:// 冒烟）都过，才算接通。

## 三、边界（越界=返工）

- 不写居民文案/年轮（BigLife 产线面）；
- 不改城市美术、灯光、地形、装配（渲染面=FluxVerse/CityWeb；旧 Unity 五席已于 2026-11-26 隔离）；
- 不动渲染性能参数（`aesthetic-visual` / `aesthetic-ui-icon` 口径）；
- 不新开循环、不新增台账（city-lab 三不条款）；法权仍走 governance T0-T3。

## 四、当前未接（每次开工先看这里，别假设已通）

1. CityWeb `types.ts` 未声明 `place/act_label/with`，`residents.ts` 仍按 hash 站位 →
   **行为层有数据没表现**。
2. `places.json` 尚未有 place→坐标映射（城市侧缺一半）。
3. 闸尚未挂进每日 preflight。
