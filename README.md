# trading-platform

A fresh-start trading platform for Indian stocks first, then commodities and US stocks.

Start with `CLAUDE.md` (project rules and current state), then `docs/PLAN.md` and `docs/DECISIONS.md`.

## Repository structure

This is the projected layout. The folders exist; most are empty until the plan reaches them
(see "Build order" below).

```
trading-platform/
├── CLAUDE.md                    # project rules and current state; Claude Code reads it automatically
├── README.md
├── pyproject.toml               # pytest and lint settings
│
├── common/                      # logic shared by every market and strategy; no market facts
│   ├── data/                    # loaders, corporate-action adjustment, quality checks
│   ├── universe/                # liquidity filters, blow-up filter
│   ├── signals/                 # signal library (momentum, trend, volatility, ...)
│   ├── priceaction/             # candles, swing structure, multi-timeframe tools
│   ├── portfolio/               # ranking, position sizing, stock and sector limits
│   ├── risk/                    # market filter, stops, kill switch
│   ├── backtest/                # engine, cost models, walk-forward, reports
│   ├── execution/               # broker interface (one contract, many brokers)
│   ├── signal_log/              # tamper-proof record of every signal
│   ├── alerts/                  # Telegram, dashboard feed
│   ├── graph/                   # dependency web of related stocks
│   ├── llm/                     # filings reader, local model client
│   └── utils/                   # plumbing only: config, logging, calendars, parallel helpers
│
├── markets/                     # one folder per market; markets never import each other
│   ├── india/
│   │   ├── adapters/            # NSE data, broker API, Indian costs and taxes, holidays
│   │   ├── positional/          # monthly ranking engine (built first)
│   │   ├── swing/               # 1-3 day trades, price-action based (research until it passes its gate)
│   │   ├── intraday/            # minute-bar strategies (research until it passes its gate)
│   │   └── config/              # universe rules, parameters, limits
│   ├── us/
│   │   ├── adapters/            # US data feed, broker, costs, calendar
│   │   ├── positional/
│   │   ├── swing/
│   │   ├── intraday/
│   │   └── config/
│   └── commodities/
│       ├── adapters/            # MCX data, contract rollover, margins
│       ├── positional/
│       ├── swing/
│       ├── intraday/
│       └── config/
│
├── services/                    # long-running processes: ingest, signal, alert, dashboard
│
├── research/                    # experiments; nothing here runs live or is imported
│   └── 2026-11-first-simulation/   # code and raw results behind the first results doc
│
├── tests/                       # mirrors the source layout
│   └── tools/                   # tests for the rule checker
│
├── tools/
│   └── check_rules.py           # the rule checks CI runs on every pull request
│
├── docs/
│   ├── PLAN.md                  # steps, gates, ranking engine specification
│   ├── DECISIONS.md             # dated decision log and open decisions
│   ├── SESSIONS.md              # how manager and worker sessions coordinate
│   ├── TASKS.md                 # task board (edited only by the manager session)
│   ├── tasks/                   # one file per task, plus TEMPLATE.md
│   ├── RESULTS-2026-11-first-simulation.md
│   └── DATA.md                  # data sources and licences (written in task T-002)
│
└── .github/
    ├── workflows/checks.yml     # required checks: repo-rules and tests
    └── pull_request_template.md
```

## How the pieces depend on each other

- `common/` depends on nothing else in the repo.
- Each `markets/<market>/<module>` depends only on `common/` and its own market's `adapters/` and `config/`.
- A strategy module (`positional`, `swing`, `intraday`) never imports another strategy module.
- `services/` wires modules together and may import `common/` and `markets/`.
- Nothing imports `research/`.

CI enforces these import boundaries on every pull request.

## Build order

| Plan step | Folders filled in |
|---|---|
| 1. Confirm the edge | `research/`, `docs/DATA.md` |
| 2. Ranking engine | `common/data`, `universe`, `signals`, `portfolio`, `risk`, `backtest`; `markets/india/adapters`, `positional`, `config` |
| 3. Signal service | `common/signal_log`, `alerts`; `services/` |
| 4. Paper test | No new folders; live signals are logged for three months |
| 5. Improve the ranking | `common/graph`, `llm` |
| 6. Real money and product | `common/execution` |
| Later | `markets/commodities`, `markets/us`; `common/priceaction` with the `swing` and `intraday` modules as research |

## Working in this repo

- Never push to `main`. Work on a branch named `task/T-<number>-<short-name>` and open a pull request.
- Run `python tools/check_rules.py` and `pytest -q` before pushing.
- Update the docs in the same pull request as the change.

The full rules are in `CLAUDE.md`.
