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

## Session rules (every session, no exceptions)

At the start of a session:

1. Read this file, `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/TASKS.md` and `docs/SESSIONS.md`.
2. Read the latest results file in `docs/` if the task touches strategy or backtests.
3. Know which task you are working on and its file in `docs/tasks/`. If there is none, ask before writing code.
4. Run `git fetch` and start from an up-to-date `main`.

During a session:

5. One session, one task, one branch, one pull request.
6. Update the docs in the same pull request as the change, so they never fall behind the code:
   a decision goes in `docs/DECISIONS.md`, a plan or gate change in `docs/PLAN.md`, a test result in a
   dated results file, and a changed rule in this file.
7. Do not rely on anything said in a chat that is not written in the repo. If it matters, write it down.
8. If the docs and the code disagree, stop and report it. Do not guess which one is right.

At the end of a session:

9. Update the task file in `docs/tasks/` with status, what was done, what was not, and how it was checked.
10. Leave the branch pushed and the pull request open or updated. Never leave finished work only on a local machine.

## Git rules

- Never push to `main` directly.
- Every change goes on a new branch pushed with remote tracking (`git push -u origin <branch>`).
- Open a pull request before anything merges.
- Do not merge pull requests. Sujay reviews and merges, unless he says otherwise for a specific PR.
- Delete the branch after it merges.
- Branch names: `task/T-<number>-<short-name>`.

## Keeping `main` working at all times

- `main` must always be in a working state: tests pass and the docs match the code.
- A pull request is not ready for review until its checks pass. Do not ask for a merge with a failing check.
- Never disable, skip or delete a failing test to get a pull request through. Fix the cause or report it.
- Never rewrite history on a shared branch (no force-push to `main`, no rebasing someone else's branch).
- Never commit secrets (API keys, broker tokens, Telegram tokens). They go in `.env`, which is ignored.
- Never commit data files or model weights. Document where they come from in `docs/DATA.md`.
- Nothing that can place a real order may be merged before plan step 6, and then only behind an explicit switch that defaults to off.
- A change to these rules is itself a pull request that Sujay approves. Sessions do not relax a rule on their own.
- If following a rule is impossible for a task, stop and say so in the task file. Do not work around it.

## Engineering rules

- Tests mirror the source layout under `tests/`. A change without a test needs a stated reason in the PR.
- Heavy computation uses processes or compiled code (NumPy, Numba). Threads and async are for network I/O.

## Open decisions (owner: Sujay)

- Stop-loss and risk rules. Parked; must be decided before step 3 (signal service).
- Hosting. Deferred. Order placement in India will need a static IP registered with the broker.
- Which Indian broker supplies the intraday data feed.
