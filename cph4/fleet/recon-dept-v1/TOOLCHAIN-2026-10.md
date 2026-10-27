# 逆向工具链调研（2026-10-23）与当前缺口

> 口径：只列**实际可用/可验证**的工具；星数、最后发布日取自 GitHub（2026-10-23 查询）。
> 目的：确定「Unity 加固/加密 + 私有配置格式」的标准解法，避免继续手工试错。

## 一、生态现状（按用途）

| 工具 | 星 | 最新版本/更新 | 用途 | 本项目状态 |
|---|---|---|---|---|
| **Il2CppDumper**（Perfare） | 6k+ | v6.7.46（2024-07 发布，仓库活跃） | 静态还原 dump.cs（类/字段/方法签名） | ✅ 已用，成功出 3,164 表 |
| **Cpp2IL**（SamboyCoding） | 3,055 | 2022.0.7（release 停在 2022，dev 分支持续更新） | 还原 IL/程序集 | ✅ 已用；**对 Unity 2021.3 只出签名、方法体为空** |
| **Il2CppInspector**（djkaty） | 3,059 | 持续更新（2026-10） | 静态，支持更多运行时/混淆，带插件体系 | ⬜ 未试（Cpp2IL 失败时的首选替代） |
| **Zygisk-Il2CppDumper**（Perfare） | 3,346 | 仓库活跃（无 release，自编译/模块） | **运行时** dump，绕过加密 metadata | ⬜ 待 root 真机 |
| **frida-il2cppDumper**（IIIImmmyyy） | 260 | 活跃（2026-10） | 运行时内存 dump，**明确标注支持易盾加固** | ⬜ 待 root 真机 |
| **frida-il2cpp-bridge**（vfsfitvnm） | 1,764 | 活跃 | 运行时枚举类/实例/字段（读已解析对象） | ✅ 已编译待用（卡 root） |
| **objection**（sensepost） | 9,455 | 活跃 | APK 重打包注入 frida-gadget（**免 root** 路线） | ⬜ 备选 |
| **apk.sh**（ax） | 3,851 | 活跃（2026-10） | 拆包/重打包/gadget 注入自动化 | ⬜ 备选 |
| **AssetRipper** | 8,717 | 活跃 | Unity 资源导出（模型/纹理/AB） | ⬜ 未用（本次只读配置） |
| **UnityPy** | 1,505 | 活跃 | Python 读 AB/TextAsset | ✅ 已用（导出配置表） |

## 二、结论：四类目标，四条路线

| 目标类型 | 正确路线 | 依据 |
|---|---|---|
| Cocos 系（三国/向往/消消乐/寻道） | **直接读 `assets/**/*.json`**，不反编译 | 本轮实测：明文 `cc.JsonAsset`；消消乐还带 Lua 源码 |
| Unity 未加固 | Il2CppDumper 静态 → 若配置是私有二进制，仍需运行时 | 本轮实测：结构可出，数值不行 |
| Unity **加固/加密 metadata**（地铁/神庙） | **运行时 dump**：Zygisk-Il2CppDumper（Magisk 模块）或 frida-il2cppDumper | Il2CppDumper 报 Not found or encrypted；静态无解 |
| 无 root 设备 | objection / apk.sh 注入 gadget 重打包 | 免 root；风险=签名校验 |

**核心判断：私有二进制配置（PbWriteBuf）与加固包，静态都走不通，运行时是唯一稳的路。**

## 三、当前资产盘点（本机）

| 项 | 数量/状态 |
|---|---|
| APK 样本 | 9 个 / 5.2 GB |
| 已出真实配置 | 向往的生活 252 表、三国 5,359 表（部分列式）、消消乐 16,683 关 |
| 结构已出、数值未解 | 向僵尸开炮（3,164 表 schema） |
| 待解压/待解析 | 寻道大千（自定义压缩 TextAsset）、保卫萝卜4（cocos2d-x tmx/plist） |
| 受阻 | 地铁跑酷/神庙逃亡2（metadata 加密）、汤姆猫（无 il2cpp） |
| 运行时链路 | frida-server + bridge 代理 + attach 脚本**已就绪**，卡模拟器 root |

## 四、下一步（按优先级）

1. **真机 root 到位后**：装 Zygisk-Il2CppDumper（一次性把 dump.cs 拿到手）→ 再跑 frida-bridge 读 `LevelWaveConfig`/`MonsterCfg` 实例，直接出原表数值。
2. 若真机暂不可用：试 `apk.sh` 注入 gadget（不动手机），验证是否有签名校验。
3. 静态替代：Cpp2IL 失败时换 **Il2CppInspector**（支持更多运行时），可补出方法体。
4. 寻道大千：其 `cc.TextAsset` 是自定义编码（`z#` 前缀），先找同框架解码器；无则按运行时读。
5. 保卫萝卜4：cocos2d-x `.tmx`/`.plist` 直接可读，属可解项。

## 五、工具版本备忘

- Il2CppDumper v6.7.46（本机在用）
- Cpp2IL 2022.0.7（本机在用）
- frida 17.24.3 + frida-il2cpp-bridge（本机已装）
- jadx 51,199★ / Apktool 26,548★（已登记，未装 jar）

## 六、存储约定（CEO 令 2026-10-23）

**所有逆向资产一律放 D 盘**：

```
D:\FluxGroup-Recon\recon\
  ├─ apk\      原始安装包（含解包目录）
  ├─ data\     抽出的配置表/数据
  ├─ tools\    工具与 frida 脚本
  └─ raw\      视频样本
```

- `media\recon` 已改为指向 `D:\FluxGroup-Recon\recon` 的 **Junction**，旧脚本路径无需改动。
- 新增下载/解包/数据默认写 D 盘，不再占用 C 盘。
- 迁移实测：14.36 GB / 9 个 APK，校验一致。