# R-20261013-mv-typography — MV 歌词字幕与字体设计（词级时间戳→行级 ASS→ffmpeg 烧录）
> 溯源：CEO 调研令 2026-10-13·消费方=mv-album-001-jay 专辑线字幕/装配站·判据预注册=①专业歌词字幕规范？②2000s 华语 MV 字幕质感考据？③词级→行级 ASS+karaoke/烧录/嵌字体？④中文字体商用授权边界？⑤观众体验（不抢戏/双语/副歌）？
> 结论落点：mv-album-001-jay 字幕站任务单（§二 Style 行与烧录命令可直接接线）。

## 一、核心发现
- 【方向1·C 引 A】字幕时长/行帽：单行 ≤42 字符·每 cue ≤2 行；阅读速 160-180 WPM（Netflix 帽 20 CPS）；最长 7s（C 级引文·BBC/Netflix）；白字黑描边；SMPTE 90% title-safe。URL: https://convertaudiototext.com/blog/subtitle-styling-best-practices
- 【方向1·A·防线二直验】Netflix Timing 官方全文直读：cue 最短 20 帧=4/5 秒（24fps·833ms）；相邻 cue 最小 2 帧 gap，3-11 帧空隙须闭合到 2 帧（chaining）；无后续行时出点延后半秒（linger 律）；FN 与画内文字同步时 in/out 设在 fade 中点；「让观众在看片而非读片」。URL: https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines · https://partnerhelp.netflixstudios.com/hc/en-us/articles/219375728-Timed-Text-Style-Guide-Subtitle-Templates
- 【方向1·C】广播级参数：字幕字号=画面高 4.5-5.5%（1080p≈48-59px）；BBC 建议无衬线+字腔开阔（与 2001 衬线质感目标有张力·§二已注记取舍）；全片禁行内覆盖·只用全局 Style。URL: https://www.databrush.com/article.php?id=880
- 【方向2·C】2000s KTV 经典式考据=上下双行（原文+译文）+「纯色覆盖唱过部分」；例：衬线粗体 110px+\bord5 白边。URL: https://michiyamakaren.github.io/2022/09/30/202209-karaoke-subtitle-with-aegisub/
- 【方向2·B】90s-2000s 华语卡拉OK VCD（DAT）实物流档=年代介质一手证据（样式需看片核验）。URL: https://archive.org/details/chinese-90s-karaoke-vcd-dat
- 【方向2·M 待证】推测「2001 官方 MV 版无歌词硬字幕·硬字幕属 KTV/VCD 发行配置」——本次未成源，需看片核验后再采信。
- 【方向3·B】ffmpeg 字体/烧录：`-vf "ass=lyrics.ass:fontsdir=C:/fonts"`（fontsdir 必带·Fontname 须匹配字体内部名）；旧版 Windows 走 FONTCONFIG_FILE。URL: https://salivity.github.io/ffmpeg/article/f-fmpeg-custom-font-path-for-subtitles-and-ass
- 【方向3·C】ASS 语法要点：色序 &HAABBGGRR（BGR）；BorderStyle 1=描边+影/3=底框；Alignment 小键盘 1-9（2=底中）；{\fad(in,out)} 毫秒；{\kf} 平滑填充；「过度样式化损害可读性·克制才专业」；播放器缺字体静默替换→烧录必带 fontsdir。URL: https://www.allsubconverter.com/zh/blog/ass-subtitle-styling-guide/
- 【方向3·A】Aegisub 官方 karaoke 工作流=先整行粗轴→后逐词打 K 轴（印证：行级由词级聚合=标准工艺·行轴取首词起至末词止）。URL: https://aegisub.org/docs/latest/karaoke_timing_tutorial/
- 【方向4·A】思源宋体 LICENSE.txt 原文直验：SIL OFL 1.1=免费商用/可嵌入/可再分发（保留字体名 Source 不得用于修改版）。URL: https://raw.githubusercontent.com/adobe-fonts/source-han-serif/master/LICENSE.txt
- 【方向4·A/C】方正四款免费商用=方正黑体/书宋/仿宋/楷体（商业发布免费·官网走 0 元书面授权流程）；「方正甲骨文」下载页标非商免费勿商用。URL: https://www.foundertype.com · https://zhuanlan.zhihu.com/p/408495311
- 【方向4·B/C】华文家族（STSong/STZhongsong 等 22 款）≠免费：版权=常州华文印刷新技术·商用授权走 VCG 独家平台购买；系统预装≠可商用——本项目禁用。URL: https://sinotype.vcg.com/ · https://aiqicha.baidu.com/details/ugknowledge?id=838d5cc0bc067f54ebfe963645ae39e4
- 【方向5·B】双语字幕眼动研究（JoSTrans 2020·20 名中文母语者·Liao/Kruger/Doherty）：母语字幕注意分配最稳定；双语较单语无更多认知负荷亦无额外认知增益；优于无字幕。URL: https://www.jostrans.org/issue33/art_liao.pdf · https://researchers.mq.edu.au/en/publications/the-impact-of-monolingual-and-bilingual-subtitles-on-visual-atten/
- 【方向5·C】副歌强调惯例=同族字重对比（Bold 副歌/Regular 主歌）制造段落层次，而非换色加特效；按手机尺寸预览判读性。URL: https://www.epitrite.com/blog/best-fonts-for-lyric-videos
- 【方向5·A】淡入出时长锚点：入 200-300ms/出 150-200ms（Material Motion 官方动效时长）。URL: https://m1.material.io/motion/duration-easing.html

## 二、字体+ASS 样式建议（1080p·PlayResX/Y=1920/1080）
- 字体：主=思源宋体 SemiBold（OFL 免费商用·Fontname 以 fc-list/字体册实测内部名为准，如"Source Han Serif SC SemiBold"）；备=方正书宋（0 元授权流程后）。衬线=2001 报刊字幕质感正源；BBC 无衬线建议以信息优先场景为限，本片年代美学优先（张力注记）。华文宋体禁用（需 VCG 购权）。
- Style 行：`Style: Lyric,Source Han Serif SC SemiBold,54,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2.5,1,2,240,240,110,1`（白字/黑描边 2.5px/影 1px/底中/MarginV 110 避开 108px 底安全区/MarginL/R 240 留 90% 横向安全区）。
- 字号：主歌 54px（画面高 5%·4.5-5.5% 带内）；副歌 58px 或同字号换 Bold 字重（字重对比律）；单行 ≤14-16 汉字（16×54px=864px<1728px 安全区宽·推算非源引）。
- 淡入出：`{\fad(250,180)}`——24fps≈6.0/4.3 帧·25fps≈6.3/4.5 帧·29.97fps≈7.5/5.4 帧（入 250ms/出 180ms·Material 200-300/150-200ms 带内）。
- 词级→行级规则：行 start=首词 start·行 end=末词 end；无后续行时 end 延后半秒（linger 律）；<20 帧（4/5s·24fps）短行并邻行或延显；>7s 行拆两行；相邻 cue 留 2 帧 gap（3-11 帧空隙闭合到 2 帧）；501 词级时间戳保留为数据资产（副歌强调备用），不弃。
- karaoke 判定：主轨不用 {\k}/{\kf} 填充——纯色填充=KTV 质感而非官方 MV 质感（克制律+方向2 考据）；如需强调，仅末段副歌可加低对比 \kf 试验版，默认关。
- 烧录命令：`ffmpeg -i mv.mp4 -vf "ass=lyrics.ass:fontsdir=C:/Fonts/SrcHan" -c:v libx264 -crf 18 -pix_fmt yuv420p out.mp4`；烧录后抽帧+多播放器核验（缺字体=静默替换）。
- 双语：默认仅中文单轨（母语注意稳定律）；如需英文另立 SubEn 样式（Montserrat Light 38px·灰 &H00CCCCCC·位次下移）不叠双行——双语无认知增益。

## 三、验证声明
- 实读=fetch×20（成源 13 页·403/404/JS 拦截 5 次均重试改道）·检索=search×12 轮（≥4 达标）·成源 18 条分级：A=6（思源 LICENSE.txt·Netflix×2·Aegisub·Material·方正官网）B=5（JoSTrans/Macquarie·archive.org·salivity·华文 VCG）C=6（convertaudiototext·databrush·allsubconverter·michiyamakaren·epitrite·方正知乎）M=1（2001 官方 MV 无字幕·待证）。
- 承重主张双源：时长/行帽（Netflix 官方全文直读+convertaudiototext 引 BBC）；字号 4.5-5.5%（databrush+convertaudiototext）；思源免费商用（LICENSE.txt A 级直验）。
- 防线二独立抽验（本报告收口前）：①Netflix Timing 官方页全文直读成功——纠二手源两处记法（5/6s→官方 20 帧=4/5 秒；1 帧 gap→官方最小 2 帧+3-11 帧闭合律），并新得 linger 半秒律；②思源 LICENSE.txt 原文直验 SIL OFL 1.1 ✓。两根承重主张均 A 级直源核验通过。
- 失败面：trac.ffmpeg.org Anubis 拦截→salivity 替代；BBC 官方页 404→二手引文（已标注）；Springer JS 挑战→Macquarie 出版页；思源 LICENSE 无扩展名 ×2 404→LICENSE.txt 成功；中文检索前 3 次空返回→换措辞恢复。
- 未验残留：①2001 官方 MV 无硬字幕=M 待证（看片/查母带后升格）；②KTV 经典式仅 C 级博客考据（看 archive.org VCD 实物可升 A/B）；③14-16 汉字/行为几何推算非源引。

- 更新记录：T0 骨架→T1 方向1/3→T2 方向2/4/5→T3 定稿→T4 防线二抽验+就地纠（终态 node 实测 40 行·<60 帽达标）。下次核验触发器：看片验 2001 MV 字幕惯例（M 项升格）。
