# GAME-01 向僵尸开炮 — 包体结构卡（v1，2026-10-23）

> 来源：应用宝官方 APK（`com.xjskp.gztv1.hnsc` v1.10），下载时间 2026-10-23。
> 方法：`Tools/recon/apk_recon.py`（纯静态，未反编译、未运行）。
> 样本：`media/recon/apk/xjskp.apk`（335 MB，本地保留 30 天）。

## 一、包体（G1）实测

| 项 | 数值 |
|---|---|
| APK 压缩后 | **335 MB**（实际 334.9） |
| 解压后总体积 | **455.8 MB** |
| 压缩率 | 0.732 |
| 文件数 | 6,046 |
| dex | 4 个（最大 7.6 MB） |

### 体积归因

| 目录 | 解压体积 | 占比 |
|---|---|---|
| assets | 284.2 MB | **62.3%** |
| lib | 142.4 MB | **31.2%** |
| dex | 21.5 MB | 4.7% |
| res | 4.8 MB | 1.1% |
| META-INF | 1.5 MB | 0.3% |
| 其他 | 1.5 MB | 0.3% |

### ABI（关键浪费点）

| ABI | 体积 |
|---|---|
| arm64-v8a | 74.8 MB |
| armeabi-v7a | 67.6 MB |

**结论：双 ABI 同时打包，光 armeabi-v7a 就 67.6 MB（占 APK 体积 20%）。**

### 最大文件 Top 6

| 体积 | 文件 | 说明 |
|---|---|---|
| 42.98 MB | `lib/armeabi-v7a/libil2cpp.so` | 32 位 il2cpp 运行时/代码 |
| 39.64 MB | `lib/arm64-v8a/libil2cpp.so` | 64 位同上（与左侧高度重复） |
| 24.46 MB | `lib/arm64-v8a/libunity.so` | Unity 运行时 |
| 17.11 MB | `lib/armeabi-v7a/libunity.so` | 同上 32 位 |
| 11.96 MB | `assets/ab/assets_resources_font_chinesetraditional.ttf.ab` | **繁体中文整字体资源包** |
| 8.53 MB | `assets/bin/Data/Managed/Metadata/global-metadata.dat` | il2cpp 元数据 |

## 二、引擎（G2）

- **Unity + IL2CPP**（`libil2cpp.so`、`global-metadata.dat`、`assets/bin/Data` 三证齐）。
- 资源走 **AssetBundle**（`assets/ab/*.ab`），非直接 Resources 散图 → 具备热更与分包能力。
- 未发现 Addressables catalog 命名痕迹（可能自研加载器或旧 AB 体系）。

## 三、资源（G3）

- 资源几乎全部集中在 `assets`（62.3%），其中单个 `.ab` 最大 7.62 MB（特效序列帧）。
- 字体单独打成 11.96 MB 的繁体字体 AB —— **繁体字库整包是显著可优化项**（可按需子集化）。
- 纹理格式未在本次静态统计中展开（`.ab` 内部需 AssetRipper 才能看），待深拆。

## 四、商业化痕迹（G7 初判）

dex 字符串命中（非行为证据）：

| SDK | 命中 dex 数 | 用途推断 |
|---|---|---|
| Pangle / 穿山甲 | 4 | 字节系激励视频/插屏 |
| 抖音 SDK | 3 | 抖音侧登录/分享/小游戏入口 |
| 微信 SDK | 2 | 微信登录/分享 |
| 优量汇 GDT | 2 | 腾讯系广告 |
| UnityAds | 1 | 海外/补充填充 |
| 腾讯 Bugly | 1 | 崩溃上报 |

**初判：标准 IAA 多聚合结构（穿山甲 + 优量汇 + UnityAds 三家竞价）。**具体广告点位与频次需实机录屏（G-01 动态项，待设备）。

## 五、可抄结论（3 条）

1. **包体控制**：单款 335 MB 属于休闲小游戏里的"重包"。我方同类应**只发 arm64**（省 ~67 MB），并把字体子集化（省 ~10 MB 量级），首包可压到 250 MB 以内。
2. **资源组织**：62% 体积在 `assets` 且走 AB 分块 —— 说明它把内容（关卡/皮肤/特效）全部当可热更资源。我方若做长线运营，**从第一天就按 AB/分包组织**，避免后期拆包返工。
3. **变现结构**：穿山甲+优量汇+UnityAds 三家并行是成熟 IAA 做法；我方接入时应至少双聚合，避免单一填充率。

## 六、不可抄 / 风险（1 条）

- `libil2cpp.so` 与 `global-metadata.dat` 属受版权保护的编译产物，**不得提取代码或资源复用**；本卡只记录体积与结构。若后续需要看逻辑，只允许读类名/方法名做理解，不得搬运。

## 七、待补面

| 面 | 状态 | 缺什么 |
|---|---|---|
| G4 UI 规格 | ⬜ | 需实机截图（adb/模拟器） |
| G5 核心循环 | ⬜ | 需试玩录屏 |
| G6 数值 | ⬜ | 需试玩记录 |
| G8 留存钩 | ⬜ | 需 7 日体验或拆 UI 资源 |
| G9 性能 | ⬜ | 需 adb 实测冷启动/内存 |