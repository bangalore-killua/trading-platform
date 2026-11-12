# T-002: Find Indian daily data that includes delisted stocks

- **Status:** Ready
- **Plan step:** 1
- **Branch:** task/T-002-survivor-free-data
- **Pull request:**
- **Depends on:** T-001 merged

## Goal

A documented, legally usable source of NSE daily prices from 2005 or earlier that includes companies
later delisted, suspended or merged, with corporate actions handled.

## Acceptance criteria

- [ ] At least two candidate sources compared in `docs/DATA.md`: coverage, cost, licence, adjustment quality
- [ ] For the chosen source, a count of stocks per year showing delisted names are present
- [ ] A loader in `research/` that produces the same panel format as the first simulation
- [ ] Spot check of 10 known delisted or failed companies present in the data
- [ ] Docs updated in the same pull request

## Out of scope

- Any change to strategy rules
- Production data pipeline (`common/data`), which is step 2
