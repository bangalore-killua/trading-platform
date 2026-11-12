# trading-platform

Fresh-start trading platform (India first, then commodities and US). It replaces the older
`trading-system` repo. Only lessons carry over from that repo; none of its code or algorithms.

**Read `docs/PLAN.md`, `docs/DECISIONS.md` and `docs/RESULTS-2026-11-first-simulation.md` before
proposing or changing anything.** They are the source of truth. Update them in the same PR whenever
a decision, gate result or plan step changes.

## Current state

- Step 1 of the plan is next: re-run the ranking test on data that includes delisted stocks.
- Nothing in `common/` or `markets/` is implemented yet. The folders are a skeleton.
- The only working code is the research simulation in `research/2026-11-first-simulation/`.

## Rules for this codebase

- Code makes every trading decision. An LLM only supplies inputs (structured facts from filings)
  and explanations. It never decides or overrides a trade.
- `common/` holds logic shared by every market. It contains no market facts.
- Market facts (hours, costs, taxes, lot sizes, data formats, brokers) live in `markets/<market>/adapters/`.
- Strategy modules (`positional`, `swing`, `intraday`) are thin: they select from `common/` and set parameters.
- Modules never import each other. Each depends only on `common/`. Nothing in one market imports another market.
- `common/utils/` is plumbing only (config, logging, calendars, parallel helpers).
- No hardcoded symbol lists. Universes are built by rules (liquidity), point in time.
- Every signal uses only data known on that day. No lookahead. Signals at close of day t trade no earlier than t+1.
- Every strategy or signal must pass its gate on data it was not tuned on before it goes live (see `docs/PLAN.md`).
- A simple baseline stays as the fallback. A learned model replaces it only if it wins out of sample.
- Nothing in `research/` runs live.
- Do not build scrapers that bypass bot protection. Use exchange filings, official APIs and licensed feeds.

## Workflow

- Feature branch -> pull request -> merge to `main` -> delete the branch. Never commit to `main` directly.
- Tests mirror the source layout under `tests/`.
- Heavy computation uses processes or compiled code (NumPy, Numba). Threads and async are for network I/O.

## Open decisions (owner: Sujay)

- Stop-loss and risk rules. Parked; must be decided before step 3 (signal service).
- Hosting. Deferred. Order placement in India will need a static IP registered with the broker.
- Which Indian broker supplies the intraday data feed.
