# Qwen-Image-2.1 LICENSE 判决书（POOL-0021 leg-1 · bm-c GPU 道 · C2101）

- **判定时间**：2026-10-20 00:25（C2101·24h 收据窗 ≤22:00 10-20 内）
- **取证通道**：本机 hf-mirror API 元数据 + raw LICENSE 直读（web_fetch 对 huggingface.co/hf-mirror.com 页面双掐断改走本机通道——本机 hf-mirror 实测活=下载在流同源）；取证脚本=MiniGame/.codely-cli/tmp/c2101_license_probe.py
- **判定席**：bm-c M1（C2101）· 消费方=v040 stage 腿/smoke 腿/商用切换决策

## 一、一手取证
1. **Qwen/Qwen-Image-2.1（官方仓）cardData**：`license=other · license_name=qwen-research · license_link=LICENSE`；README L154-156「This model is licensed under the Qwen Research License Agreement」。
2. **LICENSE 全文**（Qwen RESEARCH LICENSE AGREEMENT · Release Date: September 20, 2026 · Hangzhou Tongyi Laboratory Technology Co., Ltd.）关键条款：
   - §2a/§2b：**仅限非商用**（"FOR NON-COMMERCIAL PURPOSES ONLY"）；商用须另行取得商用授权（model-business@notice.qwencloud.com）。
   - §4b：用模型或其输出**创建/训练/微调/改进对外分发的 AI 模型**时须显著标注「Built with Qwen」/「Improved using Qwen」。
   - §4c：衍生作品/产品禁以「Qwen」作主名（合理描述性使用除外）。
   - §3：再分发须附本协议副本+修改声明+版权告示。
3. **Comfy-Org/Qwen-Image-2.1**（本链实际下载的 turbo int8 DiT/w4a8 TE/VAE/LoRA 重打包仓）：cardData 同为 `license_name=qwen-research`·license_link 指回 Qwen 官方 LICENSE——**重打包不改变许可面**。

## 二、判定
1. **bm-b 8G 栈记录交叉印证成立**（bm-b-model-stack-20261016「许可=qwen-research 非 Apache 商用前必读」）——本件=一手证据定谳。
2. **当前阶段（预商业化）**：按合规阶段门控令（CEO 令 2026-10-16 23:46「合规不要这么严格，只有我开始商业化的时候再严格介入」·commit 8631822）——合规席=轻量顾问模式不拦产线——**qwen21 权重链继续用于内部 KF 试验/smoke/对照（vs Krea2 三账）合规**，风险留痕=本件。
3. **商业化触发锚**（商业化/上线/变现/提审/接广告/带货任一宣布时）：**严格全检硬门激活**——商用前必须二选一：①向 model-business@notice.qwencloud.com 取得商用授权；②切换 Apache-2.0 系替代底座（如 Qwen-Image 初代=apache-2.0）。未决前 qwen21 产物**禁入商业化交付链**。
4. §4b 标注义务仅当「输出用于训练/改进对外分发的 AI 模型」时触发——常规内容生成（MV KF/i2v）不触发标注义务，但商用授权要求**不受豁免**。

## 三、下载链现态（判定副产·2026-10-20 00:2x 实测）
- **TE qwen3vl_8b_w4a8.safetensors 已完成**（6,312,105,364B 全量@00:20:35·2/4 件）——VAE .part 起流@00:21:12、DiT .part 2,623,721,472B 保全（FAIL 态候 guard 自愈 relaunch）、runner pid 42588+curl 双活。链健康·收割归 guard 自愈腿。

## 四、下游接线
- v040 便携版预挂银行单照常推进（预商业化内部试验·files_at_least 门控权重落位）；
- 商用切换决策挂 POOL-0021 收口链（委员会/导演席消费本件）；
- 本件=cph4/fleet/bmc/qwen21_weights_c2094/LICENSE-VERDICT-20261020-c2101.md
