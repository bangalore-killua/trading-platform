# Task board

Edited only by the manager session. Details live in `docs/tasks/`.

| Task | Title | Plan step | Status | Branch | PR | Depends on |
|---|---|---|---|---|---|---|
| T-001 | Project skeleton, rules and handoff docs | 0 | In review | setup/skeleton-and-handoff | not opened | none |
| T-002 | Find Indian daily data that includes delisted stocks | 1 | Ready | task/T-002-survivor-free-data | | T-001 |
| T-003 | Re-run the ranking test on survivor-bias-free data | 1 | Ready (waits on T-002) | task/T-003-rerun-ranking-test | | T-002 |

## Waiting on Sujay

- Give Claude write access to the repo, or push the T-001 branch himself.
- Turn on branch protection for `main` (require a pull request and passing checks).
- Stop-loss and risk rules (needed before plan step 3).
- Broker for the intraday data feed.
- Hosting.
