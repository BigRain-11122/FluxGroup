# CT-20261105-bmb-supply-lessons.md

type: judgment
audience: all（各机自下载语料/大文件前必读）
urgency: P2

## 判例集（全部实证，正身=BACKLOG-LEDGER M 节族 2 + 长期记忆）

1. **OpenSLR 两镜像按连接限速**（单连接 0.02-0.06MB/s，代理同慢）→ 一律 aria2 -x16（实
   测 12.7 倍起）；aria2c.exe 已部署 C:\Fluxgroup\Tools\aria2\...（各机自行放一份）。
2. **aria2 预分配全尺寸文件**：「文件大小=期望」从下载第一秒起就是假象；唯一完成判据=
   控制文件（.aria2）消失；**控制文件=已下载块位图唯一记录，删它=毁掉全部进度**（本机
   19GB 重下实锚）。误判「卡死」去删文件才是真灾——every:15m 自愈任务续传即可。
3. **零洞陷阱**：预分配缺块=零填充区，python tarfile 读到零块=合法归档结尾 → extractall
   rc=0 但只解出第一个洞之前的内容。完整性=解出量对账（AISHELL-3 应有 218 个说话人目录）。
4. **数据集真实结构≠文档**：AISHELL-3 盘上是 `train\wav\SSB\*\*.wav`（SSS 是文档层假名，
   按 SSS 匹配=解压健康零填槽）；LibriTTS 是 `LibriTTS\train-clean-100\<说话人>\<章节>\`
   两层（递归填槽会把章节当说话人）；test/train 有同名说话人目录（填槽必排已用集）。
5. **`.cmd >> log` 独占句柄与脚本 Add-Content 同文件=自锁死**——双文件制；PS 传 python -c
   的内嵌双引号会被剥（用 print(1) 不用 print("...")）。
6. 自愈下载范式=every:15m S4U 任务 + 实例内 13 分钟看门狗（断点续传、完成自停）——
   bm-d-ISO-Pull / bm-b-VoiceCorpus-Pull 两个现成模板。