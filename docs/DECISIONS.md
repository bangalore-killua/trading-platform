# Decision log

Newest first. Add an entry whenever something is decided or reversed.

## 2026-11-12

- **Initial pull request holds structure and rules only.** No product code, strategy code, research code or
  build plan is in it. Coding starts only after the plan is understood and approved.
- **Start fresh.** New repo. Only ideas and lessons come from `trading-system`; no code or algorithms.
- **Markets:** India first, then commodities and US.
- **Separate module per market and trading style, shared `common/`.** Layout in `README.md`.
- **Code decides, LLM informs.** No fully agentic trading.
- **No bot-protection bypass** for collecting news or data.
- **Git rules.** No direct pushes to `main`; every change on a remote-tracking branch; pull request before merge; Sujay merges.
- **Rules enforced by CI.** `repo-rules` and `tests` are required checks on every pull request; the table in
  `CLAUDE.md` lists what each enforces and what cannot be machine-checked.
- **Session rules.** Every session reads the docs first and updates them in the same pull request as the change.
- **Manager and worker sessions.** One manager session tracks tasks and reviews; worker sessions do one task each.
  Coordination is through `docs/TASKS.md`, `docs/tasks/` and pull requests. See `docs/SESSIONS.md`.

## Still open

- The build plan and the strategy it is based on. A first simulation and a draft plan exist on the branch
  `draft/plan-and-first-simulation`. A review on 2026-11-12 found the draft's headline result overstated,
  so it needs correcting before it is proposed for `main`.
- Stop-loss and risk rules.
- Hosting.
- Broker for the data feed.
- Capital size.
