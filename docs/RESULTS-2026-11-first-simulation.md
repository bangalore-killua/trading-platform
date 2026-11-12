# First simulation, 12 November 2026

Code: `research/2026-11-first-simulation/`. Raw output: `results/*.json` in that folder.

## Data

- Stocks: about 2,250 NSE stocks, daily OHLCV, January 2003 to 11 November 2024, from
  https://github.com/ipsycodex/nse_eod_data. 923 unadjusted splits and bonuses were repaired
  (overnight gaps below 0.72x or above 1.4x treated as corporate actions).
- Index intraday: Nifty 50 one-minute bars, April 2017 to 11 November 2026, from
  https://github.com/technovusin/nifty50-historical-data. Checked against an independent daily file:
  median close difference 0.05%.
- Rules were fixed in advance. "Earlier" is 2005-2016, "later" is 2017-2024 (stocks) or 2017-21 and 2022-26 (intraday).

## Results (annual return after costs)

| Method | Earlier | Later | Worst drawdown | Verdict |
|---|---|---|---|---|
| Nifty 500, price only | n/a | 16.4% | -38% | Benchmark |
| Equal-weight top-200 liquid universe | 10.0% | 15.5% | -73% | Fair comparison |
| Ranking, top 20, monthly | 22.7% | 20.5% | -68% | Passes, deep drawdowns |
| Ranking + market filter | 21.1% | 21.2% | -41% | Best |
| Ranking + filter, doubled costs (0.4%/side) | 19.5% | 19.4% | -41% | Holds |
| Ranking + filter, signals two days late | 20.1% | 21.7% | -44% | Holds |
| Ranking + filter, 100 most liquid stocks only | 11.2% | 15.0% | -42% | No edge over the index |
| Multi-timeframe price-action swing, best of 4 exits | 0.7% | 6.3% | -55% | Fails |
| Same, tight stop and 2R target | -10.1% | -7.7% | -89% | Fails |
| Intraday Nifty, 15-min opening-range breakout | -5.5% | -4.6% | -30% | Fails |
| Intraday Nifty, daily bias + 15m trend + 5m pullback | -5.2% | -4.7% | -24% | Fails |
| Intraday Nifty, first-30-minute momentum | -9.9% | -9.4% | -38% | Fails |
| Intraday Nifty, gap fade in the first hour | 3.3% | 0.0% | -13% | Fails later period |

Costs: 0.2% per side for stocks; 0.04% round trip for index trades (futures-level).

## Other findings

- Single signals, later period, top-minus-bottom quintile 21-day return: 12-month momentum 1.41%,
  6-month momentum 1.17%, 52-week-high closeness 0.85%. Low volatility, 5-day reversal and delivery
  accumulation showed no spread.
- Candles alone are a coin flip: 5 days after a bullish engulfing candle the stock was up 47-48.5% of the time,
  against 48-50% for any day.
- A weekly-trend filter improved the swing entries in most variants, but none beat random entries consistently
  and none came near buy-and-hold. At zero cost the best swing variant made 7% a year.
- Tight per-trade stops were the largest drag: 40-50% of swing trades were stopped out.
- The market filter was the largest risk reduction. Time in cash: 34%.
- Ranking + filter beat the Nifty 500 in 5 of 8 later years. 2022: -16.7% against +3.0%. Worst month: -23.6%.
- The Nifty's overnight gain is mostly an artefact of the 09:15 index print and is not tradable after costs since 2022.

## Known weaknesses

- **Survivor bias.** The stock data contains only companies still listed in 2024. This flatters every stock result,
  most in early years and most in mid-sized stocks, which is where all the ranking edge sits.
- Dividends and taxes are not included. Monthly turnover means short-term capital gains tax.
- Stock-level intraday, short selling, options and commodities were not tested (no data).
- Intraday tests used the index itself, not futures prices.
- Large genuine overnight crashes (worse than -28%) are treated as corporate actions and removed.

## Conclusion

Build the ranking engine, after step 1 confirms the edge on data that includes delisted stocks.
