# 硅基城市 · 共用技术底座 v1（BigLife × FluxVerse/CityWeb 联合）

> CEO 令 2026-11-26：「要联合城市等一起打造技术底座，不要各干各的，拉起集团的负责这一块的牵头做。」
> 本件=该令的执行件。**不新开实验室**（承 `cph4/city-lab.md` 三不条款），只给已存在的
> 联合实验室补上两样缺的东西：①一份两边都必须遵守的接口契约 ②一个说了算的牵头席。
> 牵头席=`cph4/skills/city-foundation-lead`（下称"底座席"）。

## 一、问题是什么（先把病说清）

现状是**两个仓各自演进、靠一个 JSON 偶然对齐**：

| 症状 | 实锚 |
|---|---|
| 语义在 BigLife、几何在 CityWeb，中间没有契约 | 我在 BigLife 新加 `place/act`，CityWeb 侧只有在有人手工改 `types.ts` 时才认识 |
| 同一个事实两处实现 | 街区地点表只存在于 `Tools/city_agents.py`；城市侧要自己猜坐标 |
| 没有版本号，改字段靠"我记得也改了那边" | `city-bridge.json` 协议号 `biglife-city-bridge/0.1` 自 11-26 起没动过 |
| 没有跨仓验收 | BigLife 侧 `--check` 只验自己；CityWeb 侧只有 file:// 截图冒烟 |

## 二、单一写入者矩阵（谁写谁读，不许双写）

| 事实 | 唯一写入者 | 读者 | 载体 |
|---|---|---|---|
| 居民身份/人设/年轮 | BigLife `evolve_citizen` | 桥、城市 | `census/registry/*.md` |
| 居民**位置/动作/相遇** | BigLife `Tools/city_agents.py` | 桥、城市 | `state/agents/agent-loop-<day>.json` |
| 挂牌席名册 + 年轮摘要 + 外观 | BigLife `Tools/city_bridge_export.py` | 城市 | `FluxVerse/world-public/city-bridge.json` |
| **地点名字表**（语义键） | 底座席（本件 `places.json`） | BigLife 行动层、城市几何层 | `cph4/city-foundation/places.json` |
| 地点→3D 坐标 | FluxVerse CityWeb | 城市 | `CityWeb/src/city/*` |
| 城市数据投影 | FluxVerse `export-city-data` | 页面 | `FluxVerse/world-public/city-data.js` |
| 世界事件/探针 | FluxVerse `world-events.jsonl` | BigLife 感知 | `world-public/` |

**铁律**：一个字段只能有一个写入者；读的一方**不许**重新计算写入者已经算好的东西
（判据同源律）。要改语义 = 改写入者 + 升协议版本 + 通知读方，不许在读方打补丁。

## 三、契约 v1

三个载体，各有版本号，破坏性变更必须升号：

```
biglife-agent-loop-v1   居民行动闭环（BigLife 写）
{
  "protocol": "biglife-agent-loop-v1", "day": "YYYY-MM-DD", "turns": 8,
  "agents": { "C-02503": {"name": "...", "district": "QT", "prof": "..."} },
  "timeline": [ {"turn":0, "agents": {"C-02503": {"place":"巡边站","act":"work","label":"巡边","with":""}}} ],
  "events": [ {"turn":0,"type":"MEET","a":"C-..","b":"C-..","place":"茶铺","mates":true},
              {"turn":0,"type":"ACT","id":"C-..","place":"..","act":"..","label":".."} ]
}

biglife-city-bridge/0.1  挂牌席与城市面（BigLife 写）
  slots[].{id,name,district,profession,ring,goal,place,act,act_label,with,
           gender,age,hair_part,eye_part,skin_c,hair_c,cloth_c,pant_c,badge_c,eye_c,faction}
  echoes[].{owner,by,owner_d,by_d,day,frag}

places.json（底座席写）
  {"protocol":"silicon-city-places-v1",
   "districts":{"GM":["自家摊","料市","街口","茶铺"], ...},
   "plaza":["广场"]}
```

约束：
- `place` 只能是 `places.json` 里声明过的名字（跨区重名允许，但必须在表内）；
- `act` 只能取 `work|move|seek|rest|wait`（行为种类，城市侧按此选动画）；
- `MEET` 一条记录代表一对（a<b 规范化），**两个人的 `with` 必须互指**；
- 缺文件 = 读方关闭该层（零漂移），不许用占位数据冒充。

## 四、节拍与延迟预算

| 环节 | 频率 | 归属 | 预算 |
|---|---|---|---|
| 行动闭环（位置/相遇） | 随泵每批（≥10min 一次） | BigLife | ≤3s（93 席 ×8 拍实测 <1s） |
| 桥导出 | 泵收尾 | BigLife | ≤5s |
| 城市数据投影 | FluxVerseTick 5min | FluxVerse | ≤10s |
| 页面重载 | 10min | CityWeb | — |

端到端：**正常 5-6 分钟，最坏 15 分钟**。任何一环超预算要落日志，不许静默变慢。

## 五、跨仓闸（"不要各干各的"的执行机关）

`Tools/city_contract_check.py`（集团根，跨仓只读）：

1. 生产件 schema：agent-loop 协议号 / 每拍每人有 place / place ∈ places.json / act ∈ 词表；
2. 桥一致性：`slots[].id ⊆ agent-loop.agents`，且 `place/act` 字段在；
3. **消费侧声明**：`CityWeb/src/city/types.ts` 必须声明 `place`/`act_label`/`with`，
   否则判 `consumer-not-wired`（这就是"各干各的"的报警器）；
4. 相遇对称：MEET 两人 `with` 互指、同地点。

返回码非 0 = 底座不合，**该轮不许把城市数据当作"已接通"上报**。
建议挂到每日首个泵窗（与 preflight 同拍），失败只留痕不拦产线。

## 六、牵头席（底座席）职权与边界

- **职权**：接口变更签字权（字段增删/协议升号必须过它）；跨仓闸的判据维护；每日闸跑通与否的问责。
- **不越界**：不写居民文案、不改城市美术、不动渲染色法（那是 `lowpoly-city-3d` 四专家族）；
  不新开循环、不新增台账（承 city-lab 三不条款）；法权仍走 governance T0-T3。
- **席位正身**：`cph4/skills/city-foundation-lead/SKILL.md`。

## 七、现存缺口（写清，不遮）

1. **CityWeb 侧尚未接** `place/act_label/with`：`types.ts` 没声明、`residents.ts` 还按
   hash 随机站在外环带。⇒ 行为层目前"有数据、没表现"，本轮只做到桥。
2. `places.json` 只有 7 个子区 ×4 + 广场，城市侧还没有 place→坐标映射。
3. 桥里 32 席有 1 席未在 agent-loop 中（该卡缺名字），闸会以 warning 形式列出。

## 八、下一步（按依赖顺序）

1. FluxVerse 侧接字段：`types.ts` 声明 + `export-city-data` 直传 + `residents.ts` 按 place 落位并 lerp。
2. `places.json` 扩到真实 POI（与城市 layout 的楼块对齐），并把坐标写进 CityWeb 的 place→anchor 表。
3. 跨仓闸挂进每日 preflight，进入"红了不许报接通"的状态。
