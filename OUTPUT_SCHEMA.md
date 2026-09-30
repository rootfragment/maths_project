# risk_model_output.json 
## Top-level shape

```
{
  "weights":          { <factor>: float },   // final blended weights, sum to 1.0
  "weights_pca":      { <factor>: float },   // PCA-only weights, for comparison/debug
  "stocks":           { <TICKER>: StockEntry },
  "model_info":       ModelInfo
}
```

## `<factor>` keys
`volatility`, `liquidity`, `correlation`, `leverage`, `track_record`

## StockEntry

| field                       | type  | range   | meaning                                                |
|------------------------------|-------|---------|---------------------------------------------------------|
| `scores.<factor>`             | float | 0-100   | normalized risk score per factor, higher = riskier      |
| `current_score`               | float | 0-100   | weighted sum of `scores` using `weights`                |
| `predicted_score`             | float | 0-100   | same, but with `volatility` swapped for the prediction  |
| `predicted_volatility_score`  | float | 0-100   | model's forecast of next-period volatility, normalized  |

Risk bands (fixed, used consistently across script + dashboard):
`0–33 = Low`, `34–66 = Moderate`, `67–100 = High`.

## ModelInfo

| field                          | type   | meaning                                            |
|----------------------------------|--------|-----------------------------------------------------|
| `volatility_prediction_mae`      | float  | test-set MAE of the volatility forecast (annualized) |
| `tickers_used`                   | list   | tickers that had enough data to be included          |
| `weight_method`                  | string | human-readable description of how weights were derived |
| `weights_regression`             | object | regression-only weights, for comparison/debug         |
| `weights_pca`                    | object | duplicate of top-level `weights_pca`, kept for convenience |


- All 5 factor keys are always present for every stock.
- All scores are already clamped to [0, 100].
- `weights` always sums to 1.0 (rounded to 3 decimals, so it may be 0.999–1.001).
- If a data field was missing at collection time (e.g. no debt/equity for an ETF), it was
  defaulted to a neutral score of `50.0`.

## Known limitations 

- `track_record` is a max-drawdown proxy, not a credit rating — avoid implying it's official.
- `predicted_score` reflects a change in forecast *volatility only* — leverage, correlation,
  liquidity and track_record stay fixed between current/predicted.
- The model predicts a risk **score direction**, never a price direction 
