# T-003: Re-run the ranking test on survivor-bias-free data

- **Status:** Ready (blocked until T-002 is Done)
- **Plan step:** 1
- **Branch:** task/T-003-rerun-ranking-test
- **Pull request:**
- **Depends on:** T-002

## Goal

A yes or no answer to the step 1 gate: does the ranking engine's edge over the index survive
when delisted stocks are included?

## Acceptance criteria

- [ ] Same rules as `docs/PLAN.md` "Ranking engine specification, as tested", with no parameter changes
- [ ] Results for 2005-2016 and 2017 onward, with and without the market filter
- [ ] Stress runs: doubled costs, two-day delay, 100 most liquid only
- [ ] Comparison table against the first simulation, showing how much survivor bias contributed
- [ ] Dated results file in `docs/` with a clear pass or fail on the gate
- [ ] `docs/DECISIONS.md` updated with the outcome

## Out of scope

- Tuning parameters to rescue a failed result. If it fails, report the failure.
