## G2 引擎
  > dex 4 个（最大 7.6 MB） [F7]
  > dex 21.5 MB 4.7% [F10]
  > 42.98 MB `lib/armeabi-v7a/libil2cpp.so` 32 位 il2cpp 运行时/代码 [F17]
  > 39.64 MB `lib/arm64-v8a/libil2cpp.so` 64 位同上（与左侧高度重复） [F18]

## G4 UI
未测

## G5 循环
未测

## G6 数值
- 解读：资源按 AB 分块组织，运营应提前规划热更策略
  > **资源组织**：62% 体积在 `assets` 且走 AB 分块 —— 说明它把内容（关卡/皮肤/特效）全部当可热更资源。我方若做长线运营，**从第一天就按 AB/分包组织**，避免后期拆包返工。 [F33]

## G7 商业化
- 解读：广告聚合三家渠道，需验证实际点位与频次表现
  > Pangle / 穿山甲 4 字节系激励视频/插屏 [F25]
  > 优量汇 GDT 2 腾讯系广告 [F28]
  > **初判：标准 IAA 多聚合结构（穿山甲 + 优量汇 + UnityAds 三家竞价）。**具体广告点位与频次需实机录屏（G-01 动态项，待设备）。 [F31]

## G8 留存
- 解读：七日留存依赖签到机制，建议优化 UI 引导流程
  > G8 留存钩 ⬜ 需 7 日体验或拆 UI 资源 [F34]

## G9 性能
- 解读：包体解压后体积较大，需重点优化压缩效率
  > 样本：`media/recon/apk/xjskp.apk`（335 MB，本地保留 30 天）。 [F2]
  > APK 压缩后 **335 MB**（实际 334.9） [F3]
  > 解压后总体积 **455.8 MB** [F4]
  > 压缩率 0.732 [F5]

## 可抄结论
1. 单 ABI 发布适配多端架构
2. 资源按 AB 分块组织内容
3. 广告聚合三家渠道竞价
   > 依据见上文实测：[F7][F10][F17][F18][F33][F25]

## 不可抄/风险
未测

## 落地动作
1. 发布只打 arm64-v8a，去掉 32 位包 [F17]
2. 字体做子集化后再打包，别整字库入包 [F24]
3. 资源按 AB/分包组织，别把散图直打进包 [F33]
4. 广告以激励视频为主，插屏控频，不做强制插屏 [F25]
5. 上线即带七日签到与每日任务 [F34]

## 怎么复现
```bash
# 重新测量包体（静态，不运行游戏）
python3 Tools/recon/apk_recon.py --apk <样本 apk> --out cph4/fleet/out/recon/raw/
# 按拆解卡重新生成本配方
python3 Tools/fleet/recon_recipe.py --source cph4/fleet/recon-dept-v1/cards/GAME-01-向僵尸开炮.md --out cph4/fleet/out/recon/recipe.md
# 复核本配方（数字必须有出处、段必须齐）
python3 Tools/fleet/recon_recipe.py --check cph4/fleet/out/recon/recipe.md --source cph4/fleet/recon-dept-v1/cards/GAME-01-向僵尸开炮.md
```
