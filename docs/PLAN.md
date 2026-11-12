# Plan

Each step has a gate. If the gate fails, fix or drop that piece. Do not build on it.

| Step | What gets built | Gate |
|---|---|---|
| 1. Confirm the edge | Indian daily data that includes delisted stocks; re-run the ranking test | The edge over the index survives |
| 2. Ranking engine | Data pipeline, signal library, monthly ranking, market filter, portfolio limits | Reproduces the step 1 result exactly |
| 3. Signal service | Monthly portfolio list to Telegram and a dashboard; tamper-proof signal log | Log and alerts always agree |
| 4. Paper test | Three months of live signals, no real money | Results within the backtest's expected range, positive after costs |
| 5. Improve the ranking | Dependency web, filings read by a local LLM, more signals | Each addition improves results on unseen data |
| 6. Real money and product | Broker execution, risk rules, registration, verified performance page | Legal sign-off before the first subscriber |
| Later | Commodities, US market; stock-level intraday and price action as research | Same gates |

## Module gate

A strategy module goes live only if, on data it was never tuned on, it shows all of:

- at least 200 trades (or, for a monthly portfolio, at least 8 years of history);
- profit factor above 1.3 after costs, or for a portfolio, a better return per unit of risk than the Nifty 500;
- maximum drawdown under 20% for trade-based modules; for the ranking portfolio, a smaller drawdown than the index;
- results that survive doubled costs and a two-day execution delay.

## Signal filter (per-trade modules)

- Minimum expected move after costs: 1.5% intraday, 4% for 1-3 day trades, 8% for weekly or monthly trades.
- Reward at least twice the risk.
- Rank by return per day of capital tied up; send only the top few.

## Ranking engine (step 2) specification, as tested

- Universe: top 200 stocks by 126-day median traded value, rebuilt monthly, price at least 20, at least 252 days of history.
- Signals: 12-month momentum skipping the last month, 6-month momentum skipping the last month,
  closeness to the 52-week high, low 126-day volatility. Equal-weight average of cross-sectional z-scores.
- Portfolio: top 20, equal weight (5% each), rebalanced every 21 trading days, traded one day after the signal.
- Market filter: hold cash when the equal-weight universe index is below its 200-day average.
- Costs assumed: 0.2% per side.

## Architecture

Five stages per module: signal library -> combination -> risk model -> portfolio construction -> execution
(execution outputs signals only until step 6). Repo layout and dependency rules are in `CLAUDE.md`.

Parallelism: async I/O for feeds and APIs; one process per strategy module; process pools and compiled code
for backtests and features; a message queue between stages; a single writer for the signal log.

Updating: regime switch daily by pre-set rules; parameters re-fitted monthly or quarterly and kept only if
they beat the current version out of sample; logic changes only through the full module gate. A decay monitor
switches a module off when live results fall below its backtest range.

## Product and legal notes

- Selling trading calls in India can require SEBI Research Analyst registration. A provider whose algo logic
  is not disclosed to users needs that registration under the 2026 retail algo framework.
- Order APIs must come from a static IP registered with the broker.
- Performance claims need a verifiable record, which is why the signal log starts in step 3.
- Get a securities lawyer's advice before step 6.
