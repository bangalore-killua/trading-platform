# trading-platform

A fresh-start trading platform for Indian stocks first, then commodities and US stocks.

This repo currently holds the project structure, the working rules and the automated checks.
There is no product code yet, and coding does not start until a build plan is approved.

Start with `CLAUDE.md` (project rules and current state), then `docs/DECISIONS.md`.

## Repository structure

This is the projected layout. The folders exist and are empty.

```
trading-platform/
├── CLAUDE.md                    # project rules and current state; Claude Code reads it automatically
├── README.md
├── pyproject.toml               # test and lint settings
│
├── common/                      # logic shared by every market and strategy; no market facts
│   ├── data/                    # loaders, corporate-action adjustment, quality checks
│   ├── universe/                # which instruments are eligible to trade
│   ├── signals/                 # signal library
│   ├── priceaction/             # candles, swing structure, multi-timeframe tools
│   ├── portfolio/               # ranking, position sizing, stock and sector limits
│   ├── risk/                    # market filter, stops, kill switch
│   ├── backtest/                # engine, cost models, reports
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
│   │   ├── positional/          # trades held for weeks
│   │   ├── swing/               # trades held for 1-3 days
│   │   ├── intraday/            # trades opened and closed the same day
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
│
├── tests/                       # mirrors the source layout
│   └── tools/                   # tests for the rule checker
│
├── tools/
│   └── check_rules.py           # the rule checks CI runs on every pull request
│
├── docs/
│   ├── DECISIONS.md             # dated decision log and open decisions
│   ├── SESSIONS.md              # how manager and worker sessions coordinate
│   ├── TASKS.md                 # task board (edited only by the manager session)
│   └── tasks/                   # one file per task, plus TEMPLATE.md
│
└── .github/
    ├── workflows/checks.yml     # required checks: repo-rules and tests
    └── pull_request_template.md
```

`docs/PLAN.md` will be added once a build plan is approved.

## How the pieces depend on each other

- `common/` depends on nothing else in the repo.
- Each `markets/<market>/<module>` depends only on `common/` and its own market's `adapters/` and `config/`.
- A strategy module (`positional`, `swing`, `intraday`) never imports another strategy module.
- `services/` wires modules together and may import `common/` and `markets/`.
- Nothing imports `research/`.

CI enforces these import boundaries on every pull request.

## Working in this repo

- Never push to `main`. Work on a branch named `task/T-<number>-<short-name>` and open a pull request.
- Run `python tools/check_rules.py` and `pytest -q` before pushing.
- Update the docs in the same pull request as the change.

The full rules are in `CLAUDE.md`.
