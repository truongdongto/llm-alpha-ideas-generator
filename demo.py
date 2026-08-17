"""
integration_demo.py
====================
End-to-end smoke test of the full pipeline built so far:

    data_layer.fetch_real_data()
        -> dsl.evaluator.evaluate_expression()
        -> backtest.engine.backtest_alpha()

This isn't a correctness test (synthetic random-walk prices have no real
predictive structure, so don't read meaning into the actual IC numbers
here) -- it's a WIRING test: proving all three modules built so far
compose correctly end to end on a handful of handwritten expressions,
the same way Module 5's generate-test loop will call them later.
"""

import pandas as pd

from data_layer import fetch_real_data
from dsl.evaluator import evaluate_expression
from backtest.engine import backtest_alpha

pd.set_option("display.width", 120)

tickers = ["AAPL", "MSFT", "^GSPC", "BTC-USD"]
panel = fetch_real_data(tickers, "2020-01-01")

handwritten_alphas = [
    "rank(ts_delta(close, 5))",
    "-rank(ts_delta(close, 1))",             # short-term reversal
    "rank(ts_mean(returns, 10))",             # momentum
    "zscore(volume) - zscore(adv20)",         # volume surprise
    "rank(ts_corr(volume, close, 10))",
    "decay_linear(returns, 5)",
]

rows = []
for expr in handwritten_alphas:
    signal = evaluate_expression(expr, panel)
    result = backtest_alpha(signal, panel["close"], horizons=(1, 5, 10), n_quantiles=5)
    rows.append({
        "expression": expr,
        "mean_ic_1d": result["primary_horizon_ic"]["mean_ic"],
        "ic_ir_1d": result["primary_horizon_ic"]["ic_ir"],
        "long_short_1d": result["quantile_summary"]["long_short_mean"],
        "ls_tstat": result["quantile_summary"]["long_short_tstat"],
        "turnover": result["turnover"],
    })

summary = pd.DataFrame(rows).set_index("expression")
summary = summary.sort_values("mean_ic_1d", key=abs, ascending=False)

print("Alpha screening summary:")
print(summary.round(4))

print("\nPipeline wiring OK: data_layer -> dsl.evaluator -> backtest.engine all composed successfully.")