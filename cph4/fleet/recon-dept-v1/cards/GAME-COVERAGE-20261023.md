# 竞品覆盖矩阵（2026-10-23 · 9 款）

> 判定口径：**真数值**=从包内配置直接读出并抽样验证；**结构**=字段/表结构已还原但数值未解；**受阻**=需额外手段（加密/私有格式）。

| # | 游戏 | 品类 | 引擎 | 包体/解压 | 拿到什么 | 状态 |
|---|---|---|---|---|---|---|
| 1 | 向僵尸开炮 | 塔防射击 | Unity IL2CPP | 335MB / 456MB | 3,164 表结构（关卡 29 字段、怪物 42、技能 24）；二进制数值未解 | 结构 ✅ / 数值 ⛔ |
| 2 | 三国：冰河时代 | SLG | Cocos | 888MB / 1.8GB | 5,358 张配置（CfgSoldier/CfgHeroN/CfgDropgroup…）；部分表为列式 | 结构 ✅ / 数值 🟡 |
| 3 | 向往的生活 | 模拟经营 | Cocos | 229MB / 567MB | **243 张表全量真数值**：100 级经验曲线（3/16/36/140…3,749,710）、247 个 IAP 档（¥1–¥648，79 档≥¥60）、掉落 1,842 行 | 数值 ✅ |
| 4 | 保卫萝卜4 | 塔防 | 待判 | 1,927MB / — | 包体已拆 | 包体 ✅ |
| 5 | 寻道大千 | 放置修仙 | Cocos | 582MB / 736MB | 8,095 个 JSON，配置在 `cc.TextAsset`（CloudLevelDB/LanguageWordDB，压缩态） | 待解压 |
| 6 | 开心消消乐 | 消除 | Cocos + Lua | 385MB / 468MB | **16,683 关真实关卡表**（关卡 ID 17942–175374，每关含步数/目标/四档分数阈值）+ **11,871 个 Lua 脚本**（真实逻辑） | 数值 ✅ |
| 7 | 地铁跑酷 | 跑酷 | Unity IL2CPP | 633MB / 1.7GB | metadata 加密（Il2CppDumper 报 Not found or encrypted） | 受阻 |
| 8 | 神庙逃亡2 | 跑酷 | Unity IL2CPP | 157MB / 425MB | 同上 | 受阻 |
| 9 | 汤姆猫跑酷 | 跑酷 | Unity(Mono?) | 210MB / 354MB | 无 il2cpp 元数据，schema 0 表 | 受阻 |

## 已可直接用的真数值（摘）

**向往的生活 · 等级曲线**：1→3、2→16、3→36、**4→140**、10→1,080、100→3,749,710
→ 手法：前三级秒过，第四级立刻上墙。

**向往的生活 · 付费**：247 SKU，¥1–¥648；79 档 ≥¥60；统一 10 钻/元，礼包做差异。

**开心消消乐 · 关卡**：
```
17942: [98, 2, 7, 22, [5000,17000,30000,40000], "v_0", 0, 24]
17943: [87, 2, 7, 30, [2500,5000,10000,50000], "v_0", 1197, 24]
```
→ 四档分数阈值（1-4 星）+ 步数/目标在同一行；1.6 万关靠模板+参数化生成，不是手工摆关。

## 卡点归类（后续处理方式）

| 卡点 | 涉及 | 处理 |
|---|---|---|
| 自定义二进制配置（PbWriteBuf） | 向僵尸开炮 | 需按 `unpack` 逐字段解；已在做，字段顺序已确认 |
| metadata 加密 | 地铁跑酷 / 神庙逃亡2 | 需专用解密或换版本源（非本项目首选） |
| 压缩 TextAsset | 寻道大千 | 判断压缩算法（zlib/deflate）后解压即得 |
| 微信/抖音纯小游戏 | 榜前 10 中 7 款 | 无公开包，红线不解密 |

## 方法论沉淀

- **Cocos 系（三国/向往/消消乐/寻道）**：`assets/**/*.json` 直接可读；消消乐更直接给 Lua 源码。
- **Unity 系**：先看 metadata 是否加密；未加密用 Il2CppDumper + Cpp2IL；配置若是自定义二进制才需要逐族解码。
- **跑酷品类**（地铁/神庙/汤姆猫）当前三款全部受阻于加密，优先换源（如国际版/旧版本 APK）再试。

## 运行时 dump 路线（已搭好，卡在模拟器 root）

专业解法：不碰私有二进制，运行时直接读已解析的配置对象。

已完成：
- BlueStacks 5 Pie64 启动 + ADB 打通（改 `bluestacks.conf` 的 `bst.enable_adb_access`，须停机后改）
- 游戏安装成功（335MB，ARM 转译可运行）
- `frida-server` 17.24.3 推送并运行
- `frida-il2cpp-bridge` 代理已编译（`media/recon/tools/frida-bridge/agent.ts` → `agent.js`），用 `Il2Cpp.gc.choose()` 枚举 `LevelWaveConfig` / `MonsterCfg` 实例按字段读出
- 宿主脚本：`Tools/recon/attach_dump.py`（按 pid 附着）

**卡点**：attach 返回 `PermissionDeniedError`。根因=模拟器未真正 root——`adb root` 后 `id` 仍是 uid=2000(shell)，`su` 拒绝；`bst.feature.rooting=1` 对已建实例不生效。LDPlayer 官网 403、MuMu 下载页无直链，本机无可 root 模拟器。

**换一台可 root 的模拟器/真机后一条命令出数**：
```
adb shell "nohup /data/local/tmp/frida-server -D &"
adb forward tcp:27042 tcp:27042
python Tools/recon/attach_dump.py <pid> media/recon/tools/frida-bridge/agent.js media/recon/data/xjskp_runtime.jsonl 120
```