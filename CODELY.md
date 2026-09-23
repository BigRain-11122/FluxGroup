

## Codely Structured Memories

### User

### Feedback

### Project
- [2026-09-23 14:05:55] FLUX Quant 线实质项目=BigMoney（沪深ETF 3-15天日线波段「量化交易公司系统」·8流派35策略·门禁链G1'/G2+零假设校准），2026-09-23 已从 git@github.com:BigRain-11122/BigMoney.git 克隆至 quant/bigmoney（main分支·remote已更新为改名后地址）；项目自带根级 CODELY.md 记忆体系+fleet 机队协议+10分钟OS自迭代循环设计（Bigmoney-IterationLoop 计划任务本机未安装，装法=Tools/register_loop_task.ps1）；Money02/ 7.7GB 前代资产库 gitignored 不在库内；交接指南=research/HANDOVER.md；当前=维护态（策略线全收线，3交易员在册，2026-10-31首月晋升检查）。
- [2026-09-23 14:13:09] FluxGroup 总控 git 仓已建并接通远程（2026-09-23·main→origin git@github.com:BigRain-11122/FluxGroup.git·初始提交 4ca948e·方案A=独立治理层仓）：.gitignore 隔离 gaming/MiniGame 与 quant/bigmoney 两个子公司仓（各自独立 remote：BigRain-11122/MiniGame.git、BigMoney.git），严禁把这两个目录 add 进总控；根级 CODELY.md 与 .codely-cli/settings.json 随仓提交；总控定名 FluxGroup（原 BigRainGround 为临时叫法，已在 README 更正，未注册于 BRAND.md）。
- [2026-09-23 14:26:51] Bigmoney 机队公网互传机制已立（2026-09-23 用户令·fleet/TRANSFER.md v1.0·commit 7cf0727）：方案A=git分批（≤1.5GB/批·保险丝>12h或>5GB）；方案B2=croc中继直传（零安装·口令经fleet inbox交换·Tools/bin/已gitignore）；方案B1=Tailscale组网（需用户装机授权·未装）；方案C=云中转（R2/OneDrive）；方案D=移动硬盘。交付判据=Tools/transfer_manifest.ps1 双侧manifest一致；控制面走git inbox、数据面走通道；A保险丝触发自动切B2无需用户再裁决。现行任务T-2026-09-23-01（Money02清理+上传）bm-b已于14:55认领。
- [2026-09-23 14:31:34] Bigmoney 机队治理机制完整落地（2026-09-23 用户令·commit e614ad9）：fleet/FLEET-OPS.md v1.0 四件套=①通信SLA（控制面git 10min轮·单跳≤10min·心跳≤20min判在线）②机器生命周期（加入5步不变·剔除=标记retired+任务释放+**用户GitHub撤钥匙=唯一真断权·不撤=没剔除**）③用户令牌台账 fleet/orders/O-<时间>-<发令机>.md（任何机器发号施令·优先级最高·落git即全机队生效·心跳orders_ack回执）④云端备份三级模型（库内=GitHub私库每轮push持续备份·clone+bootstrap即重建；库外大资产=方案C云中转桶即备份位；身份/钥匙刻意不备份）。bm-b已在14:55认领Money02任务，另有640c782提交显示bm-b切换了mandate（AI takeover dev scope restored）。
- [2026-09-23 14:36:25] BigMoney AI 接管系统开发已全面落地（2026-09-23 CEO 令·commit 640c782 由 bm-a 侧会话交付）：①mandate=Tools/iteration_prompt.txt 接管版（开发范围恢复 PLAN P0-P4+§7+任务板；反重复铁律=先读后写/复用禁重建/job_list+fleet/tasks 双板认领/同仓单执行体退避；多机轮账本分文件 fleet§6：bm-a 用 state-bm-a.json、bm-b 沿用 state.json；P1 新方向须 CEO 署名）；②HANDOVER §一/§六 已同步，开发队列=J12 公司小镇（点名高优）→J13 LLM 助理→J10/J18b→Optuna；③本机 bm-a（DASHENG 32核）Bigmoney-IterationLoop 已注册点火（首轮 14:33 实测 spawn headless·prompt=接管版 2462 字符·State=Running）；④拓扑实锤：bm-a=开发机、bm-b=16核回测/Money02 宿主（P1 传输票认领中，TRANSFER.md+FLEET-OPS.md 配套），Money02 传完后 bm-a 侧拉取对账 10444 bars 锚点。
- [2026-09-23 14:45:54] 集团治理规则已立（2026-09-23·commits a7f629e+ec4ac87 已推）：①docs/governance.md v1.0=总控↔子公司契约：三层结构/职责边界（引用不复制·实况优先·跨仓写禁令）/产品登记簿/开线收线五步/CEO 令牌接口（含 /CEO 触发器=RULES §7 接线）/三级记忆各归各仓/互见与共享机纪律（引用 fleet §10 不重复立法）/安全密钥律+编码律集团适用/OS 劳动力各公司自治·集团不建循环；②architecture.md 新增系统三层结构节+机队表（bm-a=DASHENG=BigMoney 开发节点∥Biggame A 机；bm-b=回测/Money02 宿主；B/C=游戏分机）；③gaming/README 与 quant/README 按「实况优先」刷新（团结引擎1.10.3·纯IAA·08号分治 / Python·自研引擎·门禁链G1'/G2·双节点循环）；④两子公司机制同构发现入法：多机认领制/根级活数据冻结位/登记簿仲裁/令牌台账/10分钟OS循环均为同源机制，集团只登记不重立。
- [2026-09-23 14:48:02] 集团拼图补齐（2026-09-23·commit 8238506 已推）：①CPH4 Labs 地址化=cph4/README.md（横切 AI 研究核心·非业务线·零产品代码·能力注册表两公司对照+共享方法论六律+新能力入列规则）；②BRAND.md §8 名称登记簿补档（FluxGroup/Biggame/MiniGame/BigMoney locked，产品内部子名归各公司登记簿引用不复制）；③CEO 宣言入 README 头部+BRAND（「这就是我的 FLUX 集团——创新元宇宙，超体能量」）；④架构图/治理图均接线 cph4/ 横切层。至此集团四层齐备：治理层（docs/）+三线（gaming/quant/media）+CPH4（cph4/）+两产品仓（MiniGame/BigMoney）；唯一空位=Media 线产品（开线须 CEO 点产品名，五步流程就绪）。

### Reference

