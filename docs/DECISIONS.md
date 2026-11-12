# Decision log

Newest first. Add an entry whenever something is decided or reversed.

## 2026-11-12

- **Git rules.** No direct pushes to `main`; every change on a remote-tracking branch; pull request before merge; Sujay merges.
- **Session rules.** Every session reads the docs first and updates them in the same pull request as the change.
- **Manager and worker sessions.** One manager session tracks tasks and reviews; worker sessions do one task each. Coordination is through `docs/TASKS.md`, `docs/tasks/` and pull requests. See `docs/SESSIONS.md`.
- **Start fresh.** New repo. Only ideas and lessons come from `trading-system`; no code or algorithms.
- **Build the monthly ranking engine first.** It was the only method that passed the first simulation.
  Intraday index strategies and candlestick/price-action entry rules failed and are research-only.
- **Two-step commitment.** Step 1 re-tests the ranking on data with delisted stocks. If the edge disappears, stop.
- **Markets:** India first (free daily data), then commodities and US.
- **Code decides, LLM informs.** No fully agentic trading. A local open-weights LLM (Qwen class) reads filings
  for the slower modules, added only after rule-based strategies pass. Fine-tune only for a measured gap.
- **Separate module per market and trading style, shared `common/`.** Layout in `CLAUDE.md`.
- **Outputs:** Telegram and a dashboard, both fed from one signal log.
- **No bot-protection bypass.** News inputs are exchange filings, GDELT, RSS headlines; licensed feed later if it helps.
- **Open-source terminals (OpenBB, Fincept)** are research conveniences only, not product dependencies. Check licences.
- **Dependency web** of related stocks (suppliers, customers, competitors, input commodities, group companies,
  lead-lag) is a planned input in step 5. It was not in `trading-system`.
- **Account:** the Indian demat account is linked to a resident savings account. Owner to confirm with the bank or
  a chartered accountant whether it must be converted, since that changes which segments can be traded.

## Lessons carried over from trading-system

- Universe by liquidity rules, not index membership.
- Point-in-time data discipline.
- Test each signal alone before combining.
- Keep a simple baseline as the fallback.
- Blow-up filter (bankruptcy, fraud, dilution) before ranking.
- Regime awareness (now the market filter).
- Benchmark honestly: beat the index after costs.
- Three months of paper trading before real money.
- No hardcoded symbols; kill switch; Telegram alerts.

## Still open

- Stop-loss and risk rules (before step 3).
- Hosting.
- Broker for the intraday data feed.
- Capital size (sizes are expressed as a percentage of capital until then).
