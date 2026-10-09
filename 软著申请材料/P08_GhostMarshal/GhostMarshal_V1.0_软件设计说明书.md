# 奈何桥游戏软件 V1.0 软件设计说明书

## 1. 软件概述

奈何桥是一款2D文字冒险解谜游戏，运行于Unity引擎，面向Android与iOS小游戏平台。玩家扮演奈何桥上的新任判官，通过TouchAdventure触控探索场景，收集证物，审问亡魂，依据VerdictSystem做出审判，最终决定亡魂的去向。

游戏核心循环为：探索场景 → 收集线索 → 审问亡魂 → 做出判决 → 解锁下一章。StoryEngine驱动剧情推进，ChapterConfig定义章节解锁条件，FinalLauncher根据玩家选择触发不同结局。

命名空间为Sy.P08，运行时代码共37个.cs文件，有效代码行6600行。

## 2. 运行环境

| 项目 | 配置 |
|---|---|
| 开发硬件 | Intel i7处理器，16GB内存，512GB SSD |
| 运行硬件 | ARM四核处理器，2GB内存，占用空间100-150MB，触控屏 |
| 开发操作系统 | Windows 10 |
| 开发工具 | Unity 2022，Visual Studio 2022 |
| 运行平台 | Android 8.0+，iOS 12.0+，微信小游戏平台 |
| 支撑环境 | Unity Runtime |
| 编程语言 | C# |
| 源程序量 | 约6600行 |

## 3. 系统架构

启动流程由BootRunner驱动BootSequence，注入BootServices注册的核心服务。冒险模块由ExploreLauncher调度：SceneConfig定义场景布局，TouchAdventure处理触控交互，StoryEngine推进剧情对话，CaseSim模拟案件推理。

```
BootRunner → BootSequence → BootServices
ChapterUnlockGate → ChapterConfig → Chapter1Controller
ExploreLauncher → ExploreView → SceneConfig → TouchAdventure
              → StoryEngine → StoryConfig → VerticalTextLayout
              → CaseSim → CaseView → VerdictSystem → VerdictConfig
              → HintSystem → PuzzleConfig
FinalLauncher → FinalView → ArchiveBook → ArchiveView
```

## 4. 核心模块设计

### 4.1 章节系统

ChapterConfig定义了5个章节，每个章节包含1个独立案件。ChapterUnlockGate校验章节解锁条件：

| 章节 | 案件 | 解锁条件 | 场景 |
|---|---|---|---|
| 第一章 | 断桥遗梦 | 默认解锁 | 奈何桥 |
| 第二章 | 忘川谜案 | 第一章判决完成 | 忘川畔 |
| 第三章 | 孟婆庄疑云 | 第二章判决完成 | 孟婆庄 |
| 第四章 | 幽冥府探秘 | 第三章判决完成 | 幽冥府 |
| 第五章 | 轮回终局 | 第四章判决完成 | 轮回台 |

Chapter1Controller驱动第一章的具体流程。

### 4.2 场景探索系统

ExploreView渲染当前场景，SceneConfig定义场景中的可交互热点。TouchAdventure处理触控输入：

- 点击热点 → 触发证物收集或对话
- 滑动屏幕 → 切换视角/场景
- 长按证物 → 查看详情

每个场景有3-5个可交互点，HintSystem在玩家卡住时高亮提示。PuzzleConfig定义了场景中的谜题类型：找不同、拼图、密码解锁。

### 4.3 案件推理系统

CaseSim模拟案件推理流程。玩家收集到的证物存入ArchiveBook，CaseView展示证物列表。审问亡魂时，玩家可选择已收集的证物质问亡魂，VerdictConfig定义了每个案件的正确判决逻辑。

| 判决选项 | 结果 | 条件 |
|---|---|---|
| 转世投胎 | 善终 | 证物齐全且判决正确 |
| 滞留桥畔 | 悬而未决 | 证物不足 |
| 堕入幽冥 | 冤判 | 判决错误 |

VerdictSystem根据玩家的选择与证物收集度计算最终评价。

### 4.4 剧情对话系统

StoryEngine驱动剧情对话，StoryConfig定义了角色台词与分支选项。VerticalTextLayout实现竖排文字渲染，适配中式古风排版。

对话流程：
1. 角色立绘淡入
2. 竖排文字逐字显示
3. 玩家点击继续或选择分支
4. 分支选择影响后续对话与判决

PuppetMicroMotion实现角色立绘的微动效果（眨眼、呼吸），提升沉浸感。

### 4.5 结局系统

FinalLauncher根据玩家在5个章节中的判决选择与证物收集度，触发不同结局：

| 结局 | 触发条件 |
|---|---|
| 圆满轮回 | 全部判决正确，证物收集率100% |
| 桥畔徘徊 | 判决正确率60%-99% |
| 幽冥沉冤 | 判决正确率低于60% |
| 隐藏结局 | 收集全部隐藏证物 |

FinalView展示结局动画与文字总结。

### 4.6 档案系统

ArchiveBook记录已收集的证物、已解锁的对话分支、已达成的结局。ArchiveView以图鉴形式展示收集进度。每解锁一个新条目弹出收集动画。

## 5. 数据持久化

存档包含章节进度、证物收集、判决记录、结局达成：

```json
{
  "currentChapter": 2,
  "collected_evidence": ["lantern", "letter_01", "coin"],
  "verdicts": {"chapter1": "reincarnate"},
  "endings": [],
  "hints_used": 3
}
```

存档在每次章节结束与退出时自动写入。NewbieConfig配置新手引导流程，NewbieTuning调整第一章的提示频率。

## 6. 交互设计

游戏全程触控操作，无虚拟摇杆。MainUI设计简洁：右上角菜单、左下角档案入口、右下角提示按钮。UIDemoView在首次进入时演示基本操作。

TutorialFlow驱动首次引导，通过高亮交互区域配合UiText完成教学。

## 7. 技术特点

- 竖排中文排版，中式古风沉浸感
- 5章节独立案件，多分支多结局
- 证物收集驱动推理深度
- 角色立绘微动效，低成本高表现
- 代码基于Unity引擎C#编写，命名空间Sy.P08统一管理
