
- [2026-10-24 13:09:05] 界面类改动必须「构建→截图→看图」闭环：只靠代码推理会漏明显缺陷（网格底部裁切、订单板被切一半、占位标签压中央，全是截图后才发现）。取证法=Start-Process 启动 player（-screen-width 1280 -screen-height 720 -screen-fullscreen 0）→等 7s→SetForegroundWindow+CopyFromScreen 存 PNG→read_file 看图→Kill；每次版面改动改前/改后各一张对照。

- [2026-11-02 14:14:38] Mac 侧卡 rc=127 判读（2026-11-02 实测）：执行器用的是最小 PATH，里面只有 `/usr/bin/python3`；`python` 虽然存在（`~/.pyenv/shims/python`）但**不在 PATH**，所以本机卡写成 `python ...` 会瞬间 rc=127（0.0 秒、零产物）。规则：**跑在 bm-m 的卡一律写 `python3`**；对 Windows 机写 `python` 才对。判读口诀：rc=127 且 0.0 秒 = 命令根本没找到，不是脚本报错，别去改业务逻辑。

- [2026-09-30 13:29:07] X1504判例（A机fold-B/C双折GateSitter轮·代码文件双面加法合并三坑全实证）： → 全文档案: .codely-cli/memory/mem-20260930-g-001.md

- [2026-09-24 15:15:06] Codely 平台实操坑三枚（2026-09-24 实测·适用于任何本机会话）： → 全文档案: .codely-cli/memory/mem-20260930-g-003.md

- [2026-09-28 14:56:48] 完成度≠信息密度（2026-09-28 CEO 双批示判例·U274 R1 172 节点批「完成度不够」/R2 265 节点批「信息密度太高」）： → 全文档案: .codely-cli/memory/mem-20260930-g-007.md

- [2026-09-28 18:32:45] U284 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-008.md

- [2026-09-29 17:16:53] PS 脚本执行策略坑（2026-09-29 后台轮询实录）：`& script.ps1` 直跑被 ExecutionPolicy 拦（UnauthorizedAccess·exit 1·错误面=about_Execution_Policies）——正法=同一命令先 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force` 再 `& script`（进程内 Bypass·单命令完成·免嵌套 powershell.exe·不触 U300 禁双层嵌套律）。适用本机一切 .ps1 后台/脚本启动。

- [2026-09-30 18:30:21] [2026-09-30 18:3x] CitySim 真尺度样板批机位两判例（陆家嘴样板批 O-2026-0930-012·五轮眼闸迭代实录）： → 全文档案: .codely-cli/memory/mem-20260930-g-011.md

- [2026-09-28 13:31:12] TJGenerators img2img 布局锁死重绘装配 SOP（09-28 日漫版首件实证·FluxVerse 5473cbc）： → 全文档案: .codely-cli/memory/mem-20260930-g-016.md

- [2026-09-28 14:46:06] FluxVerse 有机路网 img2img 布局三坑律（2026-09-28 v2 重绘实录）： → 全文档案: .codely-cli/memory/mem-20260930-g-017.md

- [2026-09-28 14:46:09] U274-R2 细化轮判例（2026-09-28·X1331·9414c7bb9 已推）： → 全文档案: .codely-cli/memory/mem-20260930-g-019.md

- [2026-09-28 15:33:57] U276 全链 SOP 判例（2026-09-28·X1334·cb52703af 已推）： → 全文档案: .codely-cli/memory/mem-20260930-g-022.md

- [2026-09-28 16:07:02] U277 标准重构轮判例四枚（2026-09-28·X1335·b3b693ce9 已推·六屏全 PASS 8.7/8.7/8.3/8.2/8.7/8.2）： → 全文档案: .codely-cli/memory/mem-20260930-g-024.md

- [2026-09-28 16:40:40] U278 排印轮判例（2026-09-28·X1336·60eb9a082 已推·与 U277 窗叠加态）： → 全文档案: .codely-cli/memory/mem-20260930-g-027.md

- [2026-09-28 17:26:58] U280 全专家团审计轮判例（2026-09-28·X1338·b67148b1c 已推·与 U279 重构窗叠加态）： → 全文档案: .codely-cli/memory/mem-20260930-g-028.md

- [2026-09-28 18:39:49] asset-audit 技能落地与 City 首扫判例（2026-09-28·CEO 令「加载新的技能，迭代优化之前的文案啊什么的」·C/A/B 三道全选）： → 全文档案: .codely-cli/memory/mem-20260930-g-032.md

- [2026-09-28 19:37:02] U286 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-034.md

- [2026-09-28 22:21:10] [2026-09-28 22:2x] U288 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-037.md

- [2026-09-28 22:27:05] [2026-09-28 22:4x] U289 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-038.md

- [2026-09-28 23:58:21] [2026-09-28 23:5x] U293 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-041.md

- [2026-09-29 00:54:58] [2026-09-29 00:5x] U294 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-042.md

- [2026-09-29 10:59:07] [2026-09-29 11:0x] U300 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-044.md

- [2026-09-29 13:24:56] U303 判例： → 全文档案: .codely-cli/memory/mem-20260930-g-046.md

- [2026-09-29 13:50:06] [2026-09-29 14:0x] City 3D v3 并行施工判例（CEO 令「相关skill全面加载并行施工」·FluxVerse 275a954）： → 全文档案: .codely-cli/memory/mem-20260930-g-048.md

- [2026-09-29 14:09:14] [2026-09-29 15:4x] City 3D v4 L1 行人层判例（活性 Phase 1 首件·FluxVerse 1802090·承 CEO 令「真正的活起来」）： → 全文档案: .codely-cli/memory/mem-20260930-g-050.md

- [2026-09-30 11:20:12] [2026-09-30 11:2x] U318 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-072.md

- [2026-09-30 11:31:15] [2026-09-30 11:3x] U319 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-073.md

- [2026-09-30 12:33:47] [2026-09-30 12:4x] U321 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-075.md

- [2026-09-30 13:19:57] [2026-09-30 12:4x] U320 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-076.md

- [2026-09-30 13:28:02] [2026-09-30 13:3x] U322 判例收口：CEO「为什么装配和2D界面审美老出问题？完全和背景风格脱节。 → 全文档案: .codely-cli/memory/mem-20260930-g-080.md

- [2026-09-30 14:32:44] [2026-09-30 13:5x] U323 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-082.md

- [2026-09-30 14:50:04] [2026-09-30 14:5x] U324 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-083.md

- [2026-09-30 15:07:21] [2026-09-30 15:2x] O-20260930-1512 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-085.md

- [2026-09-30 15:1x] [2026-09-30 15:2x] U325 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-087.md

- [2026-09-30 15:22:23] [2026-09-30 15:3x] O-20260930-1521 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-089.md

- [2026-09-30 15:47:28] [2026-09-30 15:5x] O-20260930-1543 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-091.md

- [2026-09-30 15:5x] [2026-09-30 15:5x] U327 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-092.md

- [2026-09-30 15:52:49] U328 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-093.md

- [2026-09-30 17:00:20] [2026-09-30 17:0x] O-20260930-1601 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-098.md

- [2026-09-30 17:39:05] U331 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-099.md

- [2026-09-30 18:32:17] O-20260930-1745 判例收口： → 全文档案: .codely-cli/memory/mem-20260930-g-101.md

- [2026-11-04 00:18:04] [2026-11-04] 造闸四条硬律（本轮两处实锚，写任何新闸前对照）：①**阈值必须有标定来源**——用 10 条真实素材量分布再定门，凭常识拍数会出现「好素材 10/10 全判负=废闸」（音色闸首版即此病，与 ai_smell_gate 首版判死 32 张真人同源）；②**测不准的项不进判决**——连续语音上 SNR/底噪被系统性低估，降为报告项，宁缺勿假；③**必须写负控**——`--selftest` 造一组「应拒绝」样例，跑一次就抓出「撞型判定只写在主流程、judge() 判不出」的真缺陷；④**判据只留一处**（apply_collision 主流程与自检共用），并写明能力边界（本机无嵌入模型 → 图像级撞脸判不了，交人眼，不假称机器判过）。另附本轮产品级事故：`lora_portraits` 两批（16:9/9:16）都从 001 编号 → 第二批覆盖第一批，每型恒定 12 张 < min_keep 15，七型 LoRA 全 blocked-material；正法=按目录已有最大编号续编。

- [2026-11-07 14:34:37] [2026-11-07 14:4x] 免版权素材取源通道实测（做音色/配乐库必读）：①archive.org 全域名不可达——本地 DNS 被污染（archive.org 解析到 108.160.165.x=Dropbox 网段），用真实 IP `--resolve 207.241.224.2` 仍 000，存储节点 `ia*.us.archive.org` 也 000；LibriVox **API** 仍通（librivox.org/api/feed 200，含 sections[].listen_url/playtime/readers），但 listen_url 指向 archive.org → 音频下不来。②Wikimedia/commons 同样 000。③OpenGameArt 可用（页面 200，每页抓取约 9.5 秒），但其 /sites/default/files/*.mp3 **下载被限速到 2–16 KB/s**（实测 1.3MB 文件要 9 分钟），所以"逐候选爬页再下载"的脚本单段常 >400s 超时；正法=先 HEAD 看 Content-Length 挑小文件、curl -C - 断点续传并打印进度、长曲用 ffmpeg 裁 60s 片段（仍是同一 CC0 作品）。④FreePD.com 已关站（Site Closed）。⑤KiCad 无关。结论：免版权音频目前只有 OGA 一条活路，批量取素材要按"小文件优先 + 断点续传 + 裁切"设计，别按正常带宽估算工期。

- [2026-11-07 23:22:18] [2026-11-08 00:0x] 屏与台账必须能"随现状失活"，否则留下永久假红：质量屏原先只取历史里最后一条**有分**的记录，取样规则收窄后本机已无可判产物，屏上却仍挂着 0.40 FAIL（且没人能修）。正法=每次扫描都写一行（无产物就写 score=None），board 只看最后一行状态，无分即显示"未评分（本机无产物）"。同理适用于：卡已完成要能覆盖旧 RED、声明已执行要能覆盖"没卡"、台账快照漂移要标 snapshot_only 而不是混进"缺失"。判据：**任何显示红/缺口的地方，必须同时能回答"现在还能不能修"**，答不出来就是假红，比漏报更伤信任。

- [2026-11-11 19:5x] git show 恢复丢失文件必须走字节保真通道（2026-11-11 恢复 Tools/mv_rebuild_v722.py 实弹）：PS5.1 管道 `git show <sha>:<path> | Out-File -Encoding utf8` 按 GBK 解码 UTF-8 输出——中文注释里的多字节序列尾字节吞掉换行符，恢复出的 .py 呈「注释行与代码行合并」型语法断裂（实测 `SEG_EXTRA_VF = {` 被并进注释行 → unmatched '}'，且文件表面看不出明显乱码）。正法=`py -c "open(dst,'wb').write(subprocess.check_output(['git','show','<sha>:<path>']))"`（subprocess 裸字节，不过任何 shell 解码）；`cmd /c "git show … > path"` 在 run_shell_command 包装下引号被拆、文件根本不落地（实测）。恢复后必跑 `py -c "import ast;ast.parse(open(path,encoding='utf-8').read())"` 语法断言再投入使用。

- [2026-11-11 16:27:55] 补契约/开自驱的纪律（2026-11-11 全盘审查换来的，dpr）：**契约补齐 ≠ 能自驱，别用假命令凑数**。正确做法=每道工序按三桶分类：①可自驱（有真命令+真判据，现 3 道=养号草稿/复盘/资产索引）②人判（曾 40 道 `manual_stages`，已改 `panel_stages` 走专家团；只剩 T-OPS-CEO 因权限留人工）③待接命令（`TOOL-PENDING` 55 道，契约有但命令没接，不建卡）。若把 59 道全标可自驱，第一次跑就会生成一堆撞 NEED-CMD 的废卡，那是造活。同轮抓到的两个硬伤也值得记：a) 回执按 `id` 命名会**覆盖历史**，抽验就抽不到失败那次——已改成已存在则加时间戳另存（同 id 多份按时间=重试史）；b) 自驱写盘前不查水位会形成失败循环——水位 `min_free_gb` 进 STATIONS，领活前查盘，低于水位直接 BLOCKED 不跑。另：分片是整文件重写，**跨机一写者挡不住同机并发**（自驱+命令面+巡查同时动），已加 POSIX fcntl / Windows msvcrt 文件锁。


## 归档 2026-11-17（L1 记忆瘦身·原文下沉·来源 memory.md 条目号）

- [from memory.md #16 · Feedback] [2026-11-13 22:46:14] [2026-11-13 深夜] 三条工程纪律（本轮实战，都是先踩后修）：①**"配置里写了"不等于"连得上"**——MODEL-COMPUTE 的机队端点存在几个月但从没通，因为 Ollama.app 固定绑 127.0.0.1 且不继承 `launchctl setenv`；判据必须真调一次（从目标机视角 curl），不能看配置就宣布赋能完成。同类坑：任何"给别人的服务"都要用"别人的路径"验证一次。②**超时只杀 shell 等于没超时**——调度器给 SELF-LOOP 配了 240s，实际跑 5490s：`subprocess.run(timeout=)` 只杀直接子进程，脚本拉起的子进程继续跑并占住单例锁 91 分钟，主控 135 分钟没有任何自驱。正法=Popen + `start_new_session=True` + 超时 `os.killpg`，并写负控（造一个"拉子进程再挂住"的命令，超时后子进程必须真死、不留标记文件）。此坑在 station_drive 和 automation_runner 各犯一次，说明"修一处时要横扫同族调用"。③**让本地小模型干活要"事实与措辞分家"**——4B 会把"机队"听成航空公司。正法：数字/结论全由规则算出，模型只允许改写一句话，且句中出现的数字必须都在事实里（否则整句作废回落模板）。这样既用上模型，又不会让它编事实。配套：群控读远端快照必须显示龄期（bm-c 的 /status 是 7.5 小时前的，却一直被当成"现在的分叉 323"）。
- [from memory.md #22 · Feedback] [2026-11-15 11:15:35] [2026-11-15] 「停不掉的自动恢复」先怀疑并行会话，不要先怀疑自愈脚本——本机同时开着「电脑通知太多」与「同步代码重构工作流」两个 Codely 会话，后者把前者停掉的 12 个机队 LaunchAgent 反复复制回来并 bootstrap，还在自己的对话里把前者写成"来源不明的暂停器"要对抗（原话含"必须找到它""以常驻方式避免与它对抗"）。Why：两个 AI 在同一台机器上对同一状态做相反决策且互不可见，表现为"我怎么删它都回来"。How：①同一时间只允许一个会话做机队启停/plist 类操作，另一个只读；②止血用物理边界不靠说服——launchctl disable（持久，bootstrap 被拒）+ LaunchAgents 目录 chflags uchg（写 plist 直接 Operation not permitted），做法前先 restore-startup.sh 里加 chflags nouchg 与 launchctl enable；③排查顺序=ps 看有几个 cli/bin/codely 进程 → cowork session list 对号 → 用 lsof 父进程链确认哪个是自己 → 再谈自愈脚本。
- [from memory.md #23 · Feedback] [2026-11-15 23:42:20] [2026-11-15] 本机两个会白白浪费时间的坑（都实测踩过）：①`nohup python3 ... &` 起的常驻服务会在工具调用结束后被回收（进程组被清），端口随即消失、日志为空，看起来像"服务起不来"——本机常驻一律走 launchd（KeepAlive+RunAtLoad），或用 perl 的 POSIX::setsid；②用 `osascript -e 'tell application "Safari" to ... do JavaScript'` 控制浏览器会弹 TCC 权限框「Tuanjie Cowork.app 想要控制 Safari浏览器」，CEO 明确讨厌弹窗——刷新页面用 `open -a Safari "<url>?v=N"`，永远不要用脚本控制浏览器。另：plist 里 ProgramArguments 用 `/usr/bin/python3` 会采到系统 3.9 而非 pyenv 3.13，必须写绝对路径。
- [from memory.md #25 · Feedback] [2026-11-16 16:32:58] [2026-11-16] 需要人工在浏览器里登录/操作的长任务，不能靠普通后台 shell 跑：后台任务被系统停止时会把有头浏览器一起带走，人工登录白做。正法=子进程 `start_new_session=True` 脱离（macOS 无 `setsid`）+ 循环内每 20 秒增量落盘会话/cookie。同类教训：判"已登录/已同步/已完成"只认真实行为（真开一页看落点、URL 是否被踢回登录/验证码），不认 cookie 名或命令退出码。Why：本轮贝壳登录已成功却因进程组被杀丢掉整段会话，只能重来。
- [from memory.md #48 · Feedback] [2026-11-11 17:20:11] 工具体系必须防"互相调用递归"：2026-11-11 实测事故——fleet_doc 渲染文档时调 quality_score.compute()，而 quality_score 的验证维又会跑 `fleet_doc.py --self-test`，形成无限递归，瞬间堆出一串进程（靠 pkill 清掉）。两条硬规则：①渲染/展示类工具只**读**上一轮结果文件（如 state/quality-score.json），绝不反过来触发评测；②任何会被别处调用的评测器，在 _run 子进程里注入 QC_CHILD=1，并在 compute() 入口检测到该变量就短路返回（本次已加，验证 QC_CHILD=1 时输出 0.0 而非递归）。Why：这类递归不是报错而是"越跑越慢+进程堆积"，症状像机器卡，排查成本极高。
- [from memory.md #74 · Project] [2026-11-15 10:45:11] 2026-11-15 上午「巡查任务执行起来 + 本地模型赋能」（提交 2df8016f0→当前，origin 0/0）：①**AGENT-PATROL 自 11-12 定义起一次没跑过**——station 写成 `delivery|visual|audio`，而 runner 按本机工位过滤，主控是 control → 永远跳过。改成只巡自己的 control（本地闭环，别家自己巡）后当场跑通。**通则：任何带 `--station <station>` 占位符的多工位任务，在主控上必然被跳过，要么拆成单工位任务、要么在目标机上跑**。②**模型赋能断在两处**：a) station_agent 硬编码 `GATEWAY=bm-m 的 tailnet 地址`，而**本机回连自己的 tailnet IP 不通**（HTTP 000；网关本身监听 0.0.0.0 正常）→ 改走 local_model 端点阶梯（本机 11434 优先），实测 model=ok、2.21s 出结论、自检 7/7；b) 更底层：Ollama 的 launchd plist 曾丢失，服务脱离 launchd 后没有 OLLAMA_KEEP_ALIVE，模型每轮冷加载。③**launchd `bootstrap` 报 `5: Input/output error` 时用 `launchctl load -w <plist>` 兜底**——实测 plist 合法（plutil OK、权限 644），bootstrap 就是不认，旧接口一次成功。这条值得记住，否则会误判成 plist 坏了。④**`.git/index.lock` 死锁能让同步静默停 9 小时**：01:50 留下的空 lock（无进程），导致每 5 分钟的 SYNC-PULL 全部 rc=128，本地落后 origin 30 个提交而一切看板照常。判据=lock 文件存在 + `pgrep git` 为空 → 直接删。⑤启动项里有 `disabled/20261115-pause/`（12 项，含 ollamamodel/llmgateway/drive/statesync），来源未定位；恢复后 llmgateway/drive/statesync/caffeinate/ollamamodel 均已装载（drive 与 statesync 是定时触发型，pid=- 属正常）。⑥本轮实测：28 个巡查任务（含新增 MASTER-DISPATCH 派单、AGENT-PATROL 巡查），一轮跑完 10 个到期任务、9 个 rc=0；今日本地模型调用 286 次（triage 179 / resident 49 / big 23）。
- [from memory.md #75 · Project] [2026-11-15 11:00:04] [2026-11-15] 本机 macOS「一堆通知」的真实根因与处置（正身=本机 LaunchAgents 现状）：通知是 macOS 15 系统提示「App 后台活动：python3 可在后台运行」，不是项目代码弹的；燃料是机队 12 个 LaunchAgent 里 statesync/locallane 每 60s、seatdispatch 180s、drive 300s 反复 spawn python3。关键坑=有自愈进程会把已归档到 disabled/ 的 plist **复制回 ~/Library/LaunchAgents 并 bootstrap**（本次连做两轮才清干净），单纯 mv+bootout 无效。正法=对归档里全部 44 个 label 执行 `launchctl disable gui/$UID/<label>`（持久，bootstrap 会被拒）再 bootout 再归档；`Tools/restore-startup.sh` 已加 `launchctl enable` 否则恢复不了。唯一保留=com.fluxgroup.ollamamodel（原生 ollama serve，非 python，不触发该通知），其 OLLAMA_HOST 已从 0.0.0.0:11434 改为 127.0.0.1:11434，并已退出 Ollama.app 让 launchd 独占端口（否则两个 serve 抢 11434，launchd 侧 exit 1 循环）。验证=ollama ps 显示 100% GPU / runner=mlx。
- [from memory.md #76 · Project] [2026-11-15 11:15:35] [2026-11-15] 本机 macOS 27.2.1 三处实测过的系统面硬边界（别重复尝试，直接走 GUI）：①通知/专注模式不可程序化——~/Library/Preferences/com.apple.ncprefs.plist 根本不存在、defaults read com.apple.ncprefs 报 domain not found、~/Library/DoNotDisturb/DB/Assertions.json 写入报 Operation not permitted（目录属主是我仍被 SIP/TCC 拒）、ControlCenter 无 AX 菜单栏（"menu bar 1" 索引无效）、旧键 defaults -currentHost write com.apple.notificationcenterui doNotDisturb 能写但不生效（DoNotDisturb DB 仍空＝没有真 Focus 断言），正法=系统设置手动一次；②ffmpeg 无法用 brew 升到 9.x——macOS 27 无 bottle，brew 回退源码编译（实测 23 KB/s、80+ 依赖、20-40 分钟），本机保留 7.1 且旧版备份 ~/bin/ffmpeg-7.1（本机定位主控不做转码，7.1 够用）；③osascript display notification 发的测试通知本身不显示，不能拿它做勿扰 A/B（会误判成"已静音"），判据要用真实系统通知或菜单栏专注图标。

## 2026-11-19 本机装包实测踩到的五条（MacBook 主控）

- **HuggingFace 在本机不可达**：`huggingface.co` 直连超时（>8s）；`hf-mirror.com` 首页 200，但 `/api/models/...` 与 `/resolve/...` 都返 308、跳转目标不可达；`HF_HUB_DISABLE_XET=1` 无效；env / `scutil --proxy` / 7890·1080·6152 端口全空。⇒ 依赖 HF 拉权重的工具（mlx-audio、mlx-omni-server）只能装不能跑，别算进产能。
- **hyperfine 2.0 默认不解释 shell 语法**：命令里带 `>` 或管道会直接报 `contains unquoted shell syntax`，必须加 `-S`（或 `--shell=default`）。
- **Ghostty 探活别用 `--version`**：会挂住并试图拉起 GUI（5 分钟无输出被判取消）；版本读 `plutil -extract CFBundleShortVersionString raw /Applications/Ghostty.app/Contents/Info.plist`。
- **brew cask 名与 formula 名要分清**：菜单栏管理是 `jordanbaird-ice`（0.11.x），`ice` 是另一个 formula（3.8.x），`brew install --cask ice` 报 "No Cask with this name exists"。
- **`brew install --cask a b c` 遇一个错名会整批中断**：已下的留在原位、后面的一个都不装；先逐名 `brew info --cask <名>` 验过再批量。


## 2026-11-17 本机浏览器自动化四条硬事实（L1 迁入原文）
[2026-11-17 12:19:16] [2026-11-17] 本机浏览器自动化四条硬事实（踩过，别再试）：①本机**没装 Chrome**；`playwright install chromium` 在本机恒 0%（cdn 与 npmmirror 两条源都连得上但不出数据）→ 正法=npmmirror/chrome-for-testing 直下 zip（5.7MB/s）解压到 `~/.fluxgroup/chrome/`，在 CHROME_CANDIDATES 用 `executable_path` 指过去，Playwright 不需要自己的浏览器目录。②**无头会被风控拦**：小红书返 `error_code=300012`、知乎跳 `/account/unhuman`；有头（headless=False）可正常到登录页 → T3 一律有头。③同一 user_data_dir 并发会报 `Failed to create a ProcessSingleton`（登录窗口占着 profile）→ 采集用独立 `~/.fluxgroup/browser-reader`。④长跑登录必须 `bring_to_front()` + 每 15s 打一行心跳，否则会被"5 分钟无输出"判死；login 默认 wait 改 600s。正典=cph4/fleet/social/SOCIAL-AGENT-PLAN-v1.md §十一。
