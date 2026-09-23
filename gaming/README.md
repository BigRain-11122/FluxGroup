# FLUX Gaming / 超体游戏

Line of FLUX Group.
Read `/README.md`, `/BRAND.md`, `/docs/philosophy.md`, `/RULES.md`, `/docs/governance.md` first.

## Position

The content universe — the company that ships playable worlds.
An **AI game company**: the company itself is the engine — self-evolving, AI-empowered,
automated development (U168). Products are games; the engine is the company.
Not a dopamine machine. We build games players carry for years.
Lucy side: a universe with soul.
WALL-E side: experiences that respect the player, not their wallet.

## Operating company

本线的运营主体 = **MiniGame 组合（Biggame）**——一家 **AI 游戏公司**（AI-native·公司制宪 U139+U168：
公司本体＝AI 驱动的自动开发机器·**主打进化迭代 / AI 赋能 / 自动化开发**）：
8 款软著 IP（P01-P08）+ G 系全球线 + 09 独立项目 · 团结引擎 1.10.3 · A 机总控 + B/C 军团分治（08号）· 零预算纯 IAA · 零服务器。

- 仓库地图与落位规则：`MiniGame/README.md`（子公司唯一导航件·五区分区图）
- 公司组织与治理（组织架构 / 门禁链全图 / 汇报节律 / 流程命名）：`MiniGame/_共享与总控/16_公司组织与治理.md`（16号 · U167）
- 子公司边界：内部文档体系 / 命名 / 规则 / OS 自动化机队归产品仓自治（`/docs/governance.md` §1）——更严不更松 · 实况优先 · 令落产品台账

## Stack

- Engine: Tuanjie (团结引擎) 1.10.3 — weixinminigame / windows-il2cpp / android modules
- Language: C# (games) + PowerShell / C# tooling (automation) + Python (artifacts pipeline)
- Target platform: WeChat & Douyin mini-games first; overseas App batch data-driven after W52

## Run commands

- Open the company dashboard (pixel town): double-click `MiniGame/像素小镇看板.bat`
- Latest state (rewritten by the engine every 10 min): `MiniGame/自动化快照.md`

## Red lines for this line

- No pay-to-win loops designed around addiction.
- No dark patterns, no loot-box psychology targeting minors.
- Content must pass the origin test: does it add meaning, or only retention?
- Product-level red lines (12 engineering constraints incl. zero-server, 10-second hook,
  vertical-only) live in the subsidiary's own constitution:
  `MiniGame/_共享与总控/MASTER总控与开发协议.md` — stricter, never looser.

## Structure

```
gaming/
├── README.md          <- this file (line entry)
├── CODELY.md          <- line memory (Codely)
└── MiniGame/          <- the operating company repo (independent git + remote,
                          isolated from this group repo by .gitignore)
    ├── README.md            <- repo map & placement rules (five zones)
    ├── _共享与总控/          <- 16 numbered charters + strategy reports
    ├── projects/            <- P01-P08 Unity projects (+ G-line)
    ├── packages/            <- shared UPM packages (com.sy.*)
    └── ...                  <- full five-zone map in MiniGame/README.md
```
