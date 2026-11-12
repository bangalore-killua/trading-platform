# T-001: Project structure, rules and checks

- **Status:** In review
- **Branch:** task/T-001-skeleton-and-docs
- **Pull request:** https://github.com/bangalore-killua/trading-platform/pull/1
- **Depends on:** none

## Goal

The repo has the folder layout, the session and git rules, the task system, and automated checks that enforce
the rules on every pull request. It contains no product code, strategy code, research code or build plan.

## Acceptance criteria

- [x] `common/` and `markets/` folder skeleton matches the layout agreed on 2026-11-12
- [x] `CLAUDE.md` holds the session, git and codebase rules
- [x] `README.md` shows the projected repository structure and dependency rules
- [x] `docs/DECISIONS.md`, `docs/SESSIONS.md`, `docs/TASKS.md` and the task template written
- [x] Rules enforced as required checks: `tools/check_rules.py` with tests, `.github/workflows/checks.yml`, PR template
- [x] No simulation code, results or build plan in this pull request
- [x] Branch pushed and pull request opened
- [ ] `repo-rules` and `tests` set as required status checks in the branch rules for `main` (Sujay)
- [ ] Sujay has reviewed the docs for anything missing or wrong

## Worker notes

Written in the chat session of 2026-11-12.

The first version of this pull request also carried a draft build plan, the first simulation's results and its
research code. Sujay asked for those to be removed so this stays an initial, structure-only pull request.
They are kept, unchanged, on the branch `draft/plan-and-first-simulation` and are not proposed for `main`.

The only code here is the rule checker (`tools/check_rules.py`) and its tests, which exist to enforce the rules.

Checked: `pytest -q` (8 tests for the rule checker pass), `ruff check` clean, `python tools/check_rules.py`
run locally against `origin/main` with this pull request's title and description (all checks pass), and the
two checks on GitHub after pushing.
