# FLUX Quant / FLUX 量化

Line of FLUX Group.
Read `/README.md`, `/BRAND.md`, `/docs/philosophy.md`, `/RULES.md` first.

## Position

Signal across time. Anti-entropy cognition on the capital flow.
Lucy side: time is the only measure; we look through the noise.
WALL-E side: capital serves people's real futures, not the casino.

## Stack（实况 2026-09-23）

- Language: Python 3.10+（3.11 实测）
- Data: 新浪源沪深 ETF 日线 48 只核心池 · 交易日 15:30 自动增量
- Engine: 自研日线回测引擎（T+1 · 成本恒开 · 持仓铁律）+ 门禁链 G1'/G2 + 零假设校准 + 试验账本 N
- Automation: Bigmoney-IterationLoop 10 分钟 AI 自迭代（bm-a 开发节点 + bm-b 回测节点）
- 运行细节以产品仓为准：`quant/bigmoney/`（契约=PLAN.md，交接=research/HANDOVER.md）

## Run commands

- 自举：`python bootstrap.py`（在 quant/bigmoney/）
- 总控面板：`start bigmoney.html`

## Red lines for this line

- No curve-fitted strategies sold as edge.
- No leverage beyond what the owner can actually survive.
- Every backtest must state universe, period, costs, and a walk-forward check.
- Past performance is not a prediction; never present it as one.

## Structure

```
quant/
├── README.md          <- line identity (this file)
└── bigmoney/          <- BigMoney 产品仓（独立 git，.gitignore 隔离）
```
