# T-001: Project skeleton, rules and handoff docs

- **Status:** In review
- **Plan step:** 0 (setup)
- **Branch:** task/T-001-skeleton-and-docs
- **Pull request:** not opened yet (branch not pushed; Claude had no write access on 2026-11-12)
- **Depends on:** none

## Goal

The repo has the folder layout, the session and git rules, the plan, the decision log, the first simulation's
results and code, and the task system.

## Acceptance criteria

- [x] `common/` and `markets/` skeleton matches the layout agreed on 2026-11-12
- [x] `CLAUDE.md` holds the session, git, engineering and codebase rules
- [x] `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/RESULTS-2026-11-first-simulation.md` written
- [x] `docs/SESSIONS.md`, `docs/TASKS.md`, task template written
- [x] Research code and raw results from the first simulation included
- [x] Rules enforced as required checks: `tools/check_rules.py` with tests, `.github/workflows/checks.yml`, PR template
- [ ] Branch pushed and pull request opened
- [ ] `repo-rules` and `tests` set as required status checks in the branch rules for `main` (Sujay)
- [ ] Sujay has reviewed the docs for anything missing or wrong

## Worker notes

Written in the chat session of 2026-11-12. No production code. Simulation scripts are research quality.
Checked: `pytest -q` (8 tests for the rule checker pass), `ruff check` clean, `python tools/check_rules.py`
run locally against `origin/main` with this PR's title and description (all checks pass).
Not checked: the workflow has not run on GitHub yet, because the branch has not been pushed.
