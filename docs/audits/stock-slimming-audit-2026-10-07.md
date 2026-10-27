# Stock-Slimming & Fleet-Isomorphism Audit — 2026-10-07（C-20261007-04 案证据件）

> CEO 令 2026-10-07 晚：「决策委员会牵头梳理所有规则，任务，命令，AI记忆，文案等存量，开始精简，确保我去机队每台机器都能看到同样的文件夹结构，同样的规则，同样的维度等，你们科学决策，我授权」。
> 机读全量盘点=K:\Fluxgroup\.codely-cli\stock_audit_20261007.json（脚本 c1688_stock_audit.py·只读零改）。

## 一、存量全景（2026-10-07 22:0x 实测）

| 域 | 量 | 病灶定谳 |
|---|---|---|
| AI 记忆 | CODELY.md 家族 21 件 467KB | 根正本 95.2KB 超 80KB 线；Biggame 域 97.4KB（junction 单份）超线；**死层 1 件=bigmoney/results/_r399bmc_ring_aside/CODELY.md 50KB（残单目录记忆挂 git）** |
| 命令/令 | HQ orders.md 212KB/263 行；fleet O 令 173 件 476KB | orders 九天 212KB 无轮转；O 令两周无归档（9 月 124 件全 ack 收尾） |
| 规则 | cph4 243 件 2883KB；GLOBAL 三区 58 件；HQ docs 1038KB；audits 889KB | 承 U254 法熵预算线治理域（未超新线·归 §三.10 三分律管辖） |
| 台账 | 登记簿 527.7KB/377 行（行均 1.4KB）；decisions 161.9KB；resource-chain 77.6KB（五件合册成果） | 登记簿超长行族=C-20261007-03 R1/R2 字节律域 |
| 文案 | README 家族 185 件 3077KB | 合并卷待司域自查（转办面） |
| **同构缺口** | 三机 heartbeat JSON 键名三套（RAM: ram_free_gb/free_ram_gb 混用；VRAM: gpu0_free_vram_gb/gpu_free_vram_mb/gpu_free_vram_mib）+**三机全缺 root_path**+bm-b 缺 gpu_model/prod_lanes+bm-c prod_lanes 陈旧 | 「同样的维度」字面靶点=§二.10 维度清单 v1 处置 |

## 二、同窗执法记录（产出计分制·实改面）

1. **HQ orders.md 九月卷切出**：212KB→63.8KB（-70%）·9 月 101 行全文保全至 `docs/orders-archive-2026-09.md`（149.1KB·零删除）·正本头部立月卷轮转注。
2. **fleet O 令九月卷归位**：124 件 git mv→`fleet/orders/archive-202609/`（R100 纯改名·历史保全·BigMoney 远端 main 已收 39874bee5）。
3. **AI 记忆死层清出**：`results/_r399bmc_ring_aside/CODELY.md`（50KB 残单目录记忆）git rm（同 commit 39874bee5·git 历史保全承诺不受损=工作树清除≠历史销毁）。
4. **立法两节并入**：resource-chain §二.10（同构三层+维度清单 v1）+§三.10（存量三分律）——零新规则文件。
5. **转办**：O-20261007-2255-bm-c 派 bm-a/bm-b（维度字段补写+根骨架 9/9 对账·回执 ≤10-09 12:00）；司域 CODELY.md 预算 ≤80KB 点名（Biggame 域首名·bigmoney 次名自查）。
6. **根 CODELY.md 冷层归档波四**：95.2KB 超线→热层指针化（快照先行+memory-archive 收全文）。

## 三、本批坑录（四条·全实证）

1. **共享树半程搭载+丢行 bug（两窗联合事故）**：orders 切分脚本收集 oct_rows 未组装回正本（本地丢行版）→并行 v4 窗 bbf81df 搭载半程态上链→远端一度仅存 2 数据行。修法=git 对象提取（809e8b2）重组+**同键多行保全去重**（同粗时间戳不同令行禁并·10-06 20:3x/20:5x 两行实证）。正法预存=U357 窗「pathspec 定向提交+add 前重核暂存面」。
2. **gh api 树 API 删除条目需完整 mode/type**（HTTP 422「Must supply a valid tree.mode」实证）——现成配方=engine-tick api_backfill 族。
3. **Out-Null 吞 gh api 错误=假绿三连**（twin 脚本 PATCHED 假输出·幸被 GitHub 全拒零污染）——fail-loud 律：API 链每步必须显式验 sha。
4. **同工作树并行窗在飞时 Git Data API 孪生=错误工具**（孪生法为 detached/他机场景立）——同树正法=让路等吸收（本窗实证=Bigmoney r703 班 pull --rebase 吸收我 commit 39874bee5→claw 拦删除披露→审批逃逸→上链·机制健康）。

## 四、判据回访 10-14（治理日）
①HQ orders.md ≤120KB（月卷在役）②fleet/orders 在飞区 ≤40 件 ③三机 heartbeat 维度清单九字段全齐+root_path ④根 CODELY.md ≤80KB ⑤巡检「同构合规」首判 3/3（字段+根骨架 9/9）。
