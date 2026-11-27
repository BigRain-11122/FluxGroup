# 夜间交接 2026-11-09（CEO 休息期间的机队状态）

> 本件手写，不被脉覆盖。自动一屏见 `HANDOFF.md`（每轮重写）。

## 一、今晚已修（都有提交在 origin/main）

1. **传家宝=bm-c 钉死**：CEO 2026-11-03 14:00 令原文即 bm-c(16G)=传家宝；`comms_check.py`／
   `lib_consolidate.py`／`ARCHITECTURE-v2` 三处曾把 bm-b/bm-c 绰号整套写反，已改。
   绰号唯一来源标注在 `Tools/fleet/fleet_lane.py`。
2. **归集与验收目标收敛**：新增 `cph4/fleet/AGGREGATE-TARGET.json`（target_node=bm-c、
   accept_on=bm-c、通道=git origin/main）。`lib_consolidate.py` 从它读目标，读不到即停。
3. **第 18 类堵点 NODE-REPO-DIVERGED 已立**：节点仓库一旦分叉，`/poke` 只做 ff-only
   就永远"假受理"——新卡与归集产出都到不了，界面上却只显示车道空闲。原 17 类全都看不见。
   判据用 git 祖先关系（rc=128=节点自己的新提交，也必须判不可达，否则整片漏报）。
   解法故意用 classify_only：远程三条通道都没有执行能力，假装自愈=假绿。
   负控实测：bm-b 仅落后（rc=0）不被误报。

## 二、当前阻塞（物理件，只有人能解）

4. **四台机里只有 bm-b 能收到新活**。实测：
   - bm-a：能应答，但 head 不是 origin/main 祖先 → ff-only 拉不到卡
   - bm-c：能应答，head 每分钟还在变（本地不停提交）→ 同样拉不到
   - bm-d：`PENDING-TAILNET`，名册里没有真 IP
   - bm-b：只落后 13 个提交，ff-only 可合，**唯一可执行**

5. **所以"所有产出归集到 bm-c"目前只能到 origin 为止**。产出进 origin/main 是安全的
   （已核 blob 在远端树），但 bm-c 拉不下来，验收做不了。

6. **解只有一条**：在 bm-a 和 bm-c 上各跑一次收口命令（安全：先开救生分支
   `salvage-auto-<ts>`，再 `reset --mixed origin/main`，只把 `Tools` 换成 origin 版，
   不 `--hard`、不 rebase、不 push）。命令由
   `python3 Tools/fleet/remote_closeout_card.py --nodes bm-c --print-cmd` 生成
   （bm-c root=`K:/Fluxgroup/FluxGroup`，已在候选根内）。

## 三、今晚机队不会满负荷（不是没派，是没地方派）

7. origin 上 3 张 OPEN 卡全部挂在不可达节点：`OPS-I2V-CAP-BMA`（nodes=bm-a）、
   `R-NEXT-BIGSTREAMD-TTS-QC`（nodes=bm-c）、`VCORP-GEN...`（gpu + day_ok=false）。
   唯一能跑的 bm-b 手上没有真活；而图标这类活必须在 GPU 机做，主控按职责不得自己出图。
   → 结论：供给不是问题，**可执行节点是问题**。

## 四、明天开盘按这个顺序

8. ① bm-c 收口 → 归集与验收立刻通，我提的图标与配置会自动落到它盘上；
   ② bm-a 收口 → 它的 CPU 面回来；
   ③ 再谈图标批量与截图（截图 CEO 2026-11-08 已口头放行，限本地静默跑图、不联网不发布，
     但 `fleet_lane` 里 `game_launch_ok` 仍是 False，要改配置才生效）。

## 五、我没做/没验的（不许当已完成）

9. 归集器首跑报「225 张 DONE 卡交付物不在盘」。这个数**不作结论**：跑它的是 Mac 克隆，
   跨机产物和外置盘都会被判"不存在"，bm-c 自己修过同类误报（227→41）。要按
   "远端待查/未挂载"口径重算才算数。
10. bm-c 上的验收器还不存在（判据已写进配置，执行器没写）。
11. 本机（bm-m）克隆也是分叉的（领先 203/落后 1238），我这轮的修复是**直接落到工作树**
    才让脉立即生效，代码另推了 origin；本机克隆本身没有收口。