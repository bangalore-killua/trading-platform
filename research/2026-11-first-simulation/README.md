# First simulation (research only)

Throwaway research code behind `docs/RESULTS-2026-11-first-simulation.md`. Not production code.

Run order, with `OUT` an empty output folder:

1. `python load.py <path to nse_eod_data clone> OUT` builds price panels.
2. `python adjust.py OUT` repairs unadjusted splits and bonuses.
3. `python daily.py OUT 0.002 base` runs benchmarks and the ranking tests (second argument is cost per side).
4. `python swing.py OUT 0.002 base` runs the multi-timeframe price-action swing tests.
5. `python intra.py <path to nifty50-historical-data clone> OUT 0.0004 base` runs the intraday index tests.
6. `python diag.py OUT` prints trade diagnostics for the swing test.

Needs pandas, numpy, pyarrow.
