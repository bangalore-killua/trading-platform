# trading-platform

Fresh-start trading platform (India first, then commodities and US). It replaces the older
`trading-system` repo. Only lessons carry over from that repo; none of its code or algorithms.

## Current state

- This repo holds the project structure, the working rules and the automated checks. Nothing else.
- There is no product code and no approved build plan. Strategy research and the draft plan are still
  being reviewed outside `main`.
- **Do not write product or strategy code until Sujay approves a plan and it is merged as `docs/PLAN.md`.**

## Rules for this codebase

These apply once coding starts.

- Code makes every trading decision. An LLM only supplies inputs (structured facts from filings)
  and explanations. It never decides or overrides a trade.
- `common/` holds logic shared by every market. It contains no market facts.
- Market facts (hours, costs, taxes, lot sizes, data formats, brokers) live in `markets/<market>/adapters/`.
- Strategy modules (`positional`, `swing`, `intraday`) are thin: they select from `common/` and set parameters.
- Modules never import each other. Each depends only on `common/`. Nothing in one market imports another market.
- `common/utils/` is plumbing only (config, logging, calendars, parallel helpers).
- No hardcoded symbol lists.
- Every signal uses only data known on that day. No lookahead.
- Nothing in `research/` runs live.
- Do not build scrapers that bypass bot protection. Use exchange filings, official APIs and licensed feeds.

## Session rules (every session, no exceptions)

At the start of a session:

1. Read this file, `docs/DECISIONS.md`, `docs/TASKS.md` and `docs/SESSIONS.md`, and `docs/PLAN.md` once it exists.
2. Know which task you are working on and its file in `docs/tasks/`. If there is none, ask before writing anything.
3. Run `git fetch` and start from an up-to-date `main`.

During a session:

4. One session, one task, one branch, one pull request.
5. Update the docs in the same pull request as the change, so they never fall behind the code:
   a decision goes in `docs/DECISIONS.md`, a plan change in `docs/PLAN.md`, and a changed rule in this file.
6. Do not rely on anything said in a chat that is not written in the repo. If it matters, write it down.
7. If the docs and the code disagree, stop and report it. Do not guess which one is right.

At the end of a session:

8. Update the task file in `docs/tasks/` with status, what was done, what was not, and how it was checked.
9. Leave the branch pushed and the pull request open or updated. Never leave finished work only on a local machine.

## Git rules

- Never push to `main` directly.
- Every change goes on a new branch pushed with remote tracking (`git push -u origin <branch>`).
- Open a pull request before anything merges.
- Do not merge pull requests. Sujay reviews and merges, unless he says otherwise for a specific PR.
- Delete the branch after it merges.
- Branch names: `task/T-<number>-<short-name>`.

## Keeping `main` working at all times

- `main` must always be in a working state: checks pass and the docs match the contents.
- A pull request is not ready for review until its checks pass. Do not ask for a merge with a failing check.
- Never disable, skip or delete a failing test to get a pull request through. Fix the cause or report it.
- Never rewrite history on a shared branch (no force-push to `main`, no rebasing someone else's branch).
- Never commit secrets (API keys, broker tokens, Telegram tokens). They go in `.env`, which is ignored.
- Never commit data files or model weights.
- Nothing that can place a real order may be merged unless an approved plan calls for it, and then only
  behind an explicit switch that defaults to off.
- A change to these rules is itself a pull request that Sujay approves. Sessions do not relax a rule on their own.
- If following a rule is impossible for a task, stop and say so in the task file. Do not work around it.

## What the automated checks enforce

Two required checks run on every pull request: `repo-rules` (`tools/check_rules.py`) and `tests`.
Run `python tools/check_rules.py` and `pytest -q` locally before pushing.

| Rule | Enforced by |
|---|---|
| Branch is named `task/T-<number>-<short-name>` | `repo-rules` |
| The task's own file in `docs/tasks/` is updated; no other task's file is modified | `repo-rules` |
| Code change under `common/`, `markets/`, `services/` comes with a doc change | `repo-rules` |
| Code change comes with a test, or a `No-test-reason:` line in the PR description | `repo-rules` |
| PR description has `Task: T-<number>` and `Checked: <how>` lines | `repo-rules` |
| Changes to `CLAUDE.md`, `.github/` or `tools/check_rules.py` have a title starting `[rules]` | `repo-rules` |
| Required docs exist | `repo-rules` |
| No data files, model weights, `.env` files, files over 1 MB, or secrets in file contents | `repo-rules` |
| Import boundaries: `common/` never imports `markets/` or `services/`; a market never imports another market; a strategy module never imports another strategy module; nothing imports `research/` | `repo-rules` |
| Code compiles, lint passes, no skipped tests, all tests pass | `tests` |
| No direct push to `main`, PR required, checks must pass | GitHub branch rules |

Not machine-checkable, so sessions and reviewers must hold these themselves: reading the docs at the start,
not coding before a plan is approved, no lookahead in signals, code (not an LLM) making trading decisions,
only the manager editing `docs/TASKS.md`, and not merging without Sujay.

## Engineering rules

- Tests mirror the source layout under `tests/`. A change without a test needs a stated reason in the PR.

## Open decisions (owner: Sujay)

- The build plan: what gets built first, and the tests each step must pass.
- Stop-loss and risk rules.
- Hosting.
- Which Indian broker supplies the data feed.
