---
name: quant-backtest-gate
description: Design, run and judge A-share and ETF backtests for the BigMoney line with correct return accounting and honest significance, and decide whether a strategy is real money-ready. Use when asked to backtest a factor or strategy, verify a claimed annualized return or Sharpe, compare against a benchmark, or judge whether a research result is a real finding or an artefact.
---

# Quant backtest gate (BigMoney)

Only results that could become money count. Ledgers, calibration runs and extra documentation are not results.

## Accounting rules (violating these silently inflates returns)

- Annualize per调仓期: advances day by day and only turns over on rebalance dates. Annualizing a sparse series (one observation per R days) as daily produced a fake Sharpe of 2.25.
- `last^(1/yrs)-1` over a sub-window whose start value is not 1 inflates results; compute growth from the sub-window's first value.
- Execution: decide at close, fill at the **next open**. Same-close fills are fantasy.
- Costs: model per-side cost explicitly (5/10/20 bp) and report the version used.
- Repair quote flips: single-day |r| > 35% on an ETF is a data flip, not a return. Rebuild the series from the first price rather than accepting it.

## Judging a result

- Compare against the right baseline: same-pool equal weight and the index — not against zero.
- Require a permutation / null test before calling a factor real; report the p-value.
- A negative result is a result: report it plainly (e.g. cross-sectional stock composite underperformed the same-pool equal weight).
- Survivorship: a pool of currently-listed ETFs is biased; say so whenever quoting decade-long numbers.

## Current production candidate (as of 2026-11-02)

Debt-free book plus an 8% volatility target: ~11.5% annualized, Sharpe ~1.13, max drawdown ~-10.6%. Bonds provide defence by *holding* them, not by selecting them — equity factors applied to bonds were negative. Re-check before quoting; numbers age.

## Pre-quote checklist (any single unchecked item = do not quote the number)

1. Series density: print the observation interval; never annualize a sparse (per-R-day) series as daily.
2. Sub-window growth computed from the sub-window's first value, not `last^(1/yrs)-1`.
3. Fill timing stated: decide at close, fill at next open.
4. Cost written on the page: bp per side **and** the turnover version used.
5. Quote flips repaired first (single-day |r| > 35% → rebuild from first price).
6. Baseline named: same-pool equal weight **and** the index, in the same table.
7. Significance reported: permutation / null p-value, with the number of shuffles.
8. Survivorship stated explicitly whenever the window exceeds ~2 years.
9. Costs and window fingerprints printed, so the run can be reproduced byte-for-byte.

## Delivery

Report money first (annualized / Sharpe / max drawdown / yearly distribution), then the evidence chain. Never let tooling or documentation stand in for a result. Live trading with real money is the CEO's decision alone.