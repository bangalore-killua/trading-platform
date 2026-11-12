# trading-platform

A fresh-start trading platform for Indian stocks first, then commodities and US stocks.

- `CLAUDE.md`: project rules and current state (read automatically by Claude Code).
- `docs/PLAN.md`: the step-by-step plan and gates.
- `docs/DECISIONS.md`: decision log.
- `docs/SESSIONS.md`: how manager and worker sessions coordinate.
- `docs/TASKS.md` and `docs/tasks/`: the task board and one file per task.
- `docs/RESULTS-2026-11-first-simulation.md`: the first backtest results.
- `common/`: logic shared by every market.
- `markets/<market>/`: adapters and strategy modules per market (`positional`, `swing`, `intraday`).
- `research/`: experiments. Nothing here runs live.
- `services/`: long-running processes.
- `tests/`: mirrors the source layout.
