WORLDQUANT_INSPIRED_ALPHAS = [
    {
        "theme": "volatility",
        "expression": "(rank(ts_argmax(signedpower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)",
        "rationales": [
            "Measures volatility dynamics by analyzing historical returns, rolling volatility, cross-sectional ranking, timing of maximum historical values and standardizing the resulting signal across assets to isolate extreme price fluctuations",
            "Captures volatility regimes and tail risk using close, returns, aiming to exploit asset price dispersion and risk premiums during market stress",
            "Formulates a cross-sectionally ranked trading indicator based on historical returns, rolling volatility, cross-sectional ranking, timing of maximum historical values, tracking historical variance patterns and price differences"
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, price differences, cross-sectional ranking and transaction flow",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, close, volume and trading volume",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets"
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * correlation(rank(open), rank(volume), 10))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, cross-sectional ranking and transaction flow",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, volume and trading volume",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets"
        ]
    },
    {
        "theme": "momentum",
        "expression": "(-1 * ts_rank(rank(low), 9))",
        "rationales": [
            "A trend-following signal that measures price momentum using historical time-series rank, cross-sectional ranking to identify sustained directional movements",
            "Capitalizes on price persistence by tracking momentum indicators built from low, positioning for continuation of historical trends",
            "Constructs a cross-sectional rank of historical time-series rank, cross-sectional ranking to prioritize assets showing the strongest relative historical performance"
        ]
    },
    {
        "theme": "trend",
        "expression": "(rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))",
        "rationales": [
            "An alpha model that extracts persistent directional trends by filtering noise in open, close, vwap through VWAP imbalances, cross-sectional ranking",
            "Seeks to capture medium-to-long-term trend transitions by analyzing relative price moves of open, close, vwap and moving averages",
            "Develops a multi-period trend indicator using VWAP imbalances, cross-sectional ranking to establish stable directional exposure"
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * correlation(open, volume, 10))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations and transaction flow",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, volume and trading volume",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations to capture changes in trading intensity and capital flow across assets"
        ]
    },
    {
        "theme": "volume",
        "expression": "((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, historical time-series rank, price differences, cross-sectional ranking and transaction flow",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume",
            "A volume-based predictive signal utilizing volume metrics, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets"
        ]
    },
    {
        "theme": "momentum",
        "expression": "(-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10))))",
        "rationales": [
            "A trend-following signal that measures price momentum using historical returns, lagged indicators, cross-sectional ranking to identify sustained directional movements",
            "Capitalizes on price persistence by tracking momentum indicators built from open, returns, positioning for continuation of historical trends",
            "Constructs a cross-sectional rank of historical returns, lagged indicators, cross-sectional ranking to prioritize assets showing the strongest relative historical performance"
        ]
    },
    {
        "theme": "momentum",
        "expression": "((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))",
        "rationales": [
            "A trend-following signal that measures price momentum using price differences, rolling minimums, rolling maximums to identify sustained directional movements",
            "Capitalizes on price persistence by tracking momentum indicators built from close, positioning for continuation of historical trends",
            "Constructs a cross-sectional rank of price differences, rolling minimums, rolling maximums to prioritize assets showing the strongest relative historical performance"
        ]
    },
    {
        "theme": "momentum",
        "expression": "rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(close, 1) : (-1 * delta(close, 1)))))",
        "rationales": [
            "A trend-following signal that measures price momentum using price differences, cross-sectional ranking, rolling minimums, rolling maximums to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of price differences, cross-sectional ranking, rolling minimums, rolling maximums to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(ts_max((vwap - close), 3)) + rank(ts_min((vwap - close), 3))) * rank(delta(volume, 3)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, price differences, cross-sectional ranking, rolling minimums, rolling maximums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, price differences, cross-sectional ranking, rolling minimums, rolling maximums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(sign(delta(volume, 1)) * (-1 * delta(close, 1)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, price differences and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, price differences to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * rank(covariance(rank(close), rank(volume), 5)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, rolling covariances, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, rolling covariances, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((-1 * rank(delta(returns, 3))) * correlation(open, volume, 10))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, historical returns, cross-asset correlations, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, volume, returns and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, historical returns, cross-asset correlations, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * rank(covariance(rank(high), rank(volume), 5)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, rolling covariances, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, rolling covariances, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1))) * rank(ts_rank((volume / adv20), 5)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volatility",
        "expression": "(-1 * rank(((stddev(abs((close - open)), 5) + (close - open)) + correlation(close, open, 10))))",
        "rationales": [
            "Measures volatility dynamics by analyzing rolling volatility, cross-asset correlations, cross-sectional ranking and standardizing the resulting signal across assets to isolate extreme price fluctuations.",
            "Captures volatility regimes and tail risk using open, close, aiming to exploit asset price dispersion and risk premiums during market stress.",
            "Formulates a cross-sectionally ranked trading indicator based on rolling volatility, cross-asset correlations, cross-sectional ranking, tracking historical variance patterns and price differences."
        ]
    },
    {
        "theme": "momentum",
        "expression": "((-1 * sign(((close - delay(close, 7)) + delta(close, 7)))) * (1 + rank((1 + sum(returns, 250)))))",
        "rationales": [
            "A trend-following signal that measures price momentum using historical returns, price differences, lagged indicators, cross-sectional ranking to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, returns, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of historical returns, price differences, lagged indicators, cross-sectional ranking to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "trend",
        "expression": "(((-1 * rank((open - delay(high, 1)))) * rank((open - delay(close, 1)))) * rank((open - delay(low, 1))))",
        "rationales": [
            "An alpha model that extracts persistent directional trends by filtering noise in open, high, low, close through lagged indicators, cross-sectional ranking.",
            "Seeks to capture medium-to-long-term trend transitions by analyzing relative price moves of open, high, low, close and moving averages.",
            "Develops a multi-period trend indicator using lagged indicators, cross-sectional ranking to establish stable directional exposure."
        ]
    },
    {
        "theme": "volume",
        "expression": "((((sum(close, 8) / 8) + stddev(close, 8)) < (sum(close, 2) / 2)) ? (-1 * 1) : (((sum(close, 2) / 2) < ((sum(close, 8) / 8) - stddev(close, 8))) ? 1 : (((1 < (volume / adv20)) || ((volume / adv20) == 1)) ? 1 : (-1 * 1))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, rolling volatility and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, rolling volatility to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * (delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, rolling volatility, cross-asset correlations, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, rolling volatility, cross-asset correlations, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0)",
        "rationales": [
            "A trend-following signal that measures price momentum using price differences to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from high, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of price differences to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "momentum",
        "expression": "((((delta((sum(close, 100) / 100), 100) / delay(close, 100)) < 0.05) || ((delta((sum(close, 100) / 100), 100) / delay(close, 100)) == 0.05)) ? (-1 * (close - ts_min(close, 100))) : (-1 * delta(close, 3)))",
        "rationales": [
            "A trend-following signal that measures price momentum using price differences, lagged indicators, rolling minimums to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of price differences, lagged indicators, rolling minimums to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "rank(((((-1 * returns) * adv20) * vwap) * (high - close)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, historical returns, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, close, vwap, returns and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, historical returns, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * ts_max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, historical time-series rank, cross-sectional ranking, rolling maximums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, historical time-series rank, cross-sectional ranking, rolling maximums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((0.5 < rank((sum(correlation(rank(volume), rank(vwap), 6), 2) / 2.0))) ? (-1 * 1) : 1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "scale(((correlation(adv20, low, 5) + ((high + low) / 2)) - close))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, rescaled inputs and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, rescaled inputs to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(min(product(rank(rank(scale(log(sum(ts_min(rank(rank((-1 * rank(delta((close - 1), 5))))), 2), 1))))), 1), 5) + ts_rank(delay((-1 * returns), 6), 5))",
        "rationales": [
            "A trend-following signal that measures price momentum using historical returns, historical time-series rank, price differences, lagged indicators, rescaled inputs, cross-sectional ranking, rolling minimums to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, returns, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of historical returns, historical time-series rank, price differences, lagged indicators, rescaled inputs, cross-sectional ranking, rolling minimums to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "(((1.0 - rank(((sign((close - delay(close, 1))) + sign((delay(close, 1) - delay(close, 2)))) + sign((delay(close, 2) - delay(close, 3)))))) * sum(volume, 5)) / sum(volume, 20))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, lagged indicators, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, lagged indicators, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3)))) + sign(scale(correlation(adv20, low, 12))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, linearly decaying weights, price differences, rescaled inputs, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, close and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, linearly decaying weights, price differences, rescaled inputs, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "mean_reversion",
        "expression": "(scale(((sum(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230))))",
        "rationales": [
            "Measures short-term price overextension using VWAP imbalances, cross-asset correlations, lagged indicators, rescaled inputs to identify potential mean-reversion pivot points.",
            "Exploits market overreaction and liquidity imbalances by taking contrarian positions when close, vwap deviate from historical averages.",
            "Computes an inverse or normalized signal based on VWAP imbalances, cross-asset correlations, lagged indicators, rescaled inputs, targeting mean-reversion tendencies across the asset universe."
        ]
    },
    {
        "theme": "trend",
        "expression": "rank((-1 * ((1 - (open / close))^1)))",
        "rationales": [
            "An alpha model that extracts persistent directional trends by filtering noise in open, close through cross-sectional ranking.",
            "Seeks to capture medium-to-long-term trend transitions by analyzing relative price moves of open, close and moving averages.",
            "Develops a multi-period trend indicator using cross-sectional ranking to establish stable directional exposure."
        ]
    },
    {
        "theme": "volatility",
        "expression": "rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))",
        "rationales": [
            "Measures volatility dynamics by analyzing historical returns, rolling volatility, price differences, cross-sectional ranking and standardizing the resulting signal across assets to isolate extreme price fluctuations.",
            "Captures volatility regimes and tail risk using close, returns, aiming to exploit asset price dispersion and risk premiums during market stress.",
            "Formulates a cross-sectionally ranked trading indicator based on historical returns, rolling volatility, price differences, cross-sectional ranking, tracking historical variance patterns and price differences."
        ]
    },
    {
        "theme": "volume",
        "expression": "((ts_rank(volume, 32) * (1 - ts_rank(((close + high) - low), 16))) * (1 - ts_rank(returns, 32)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, historical returns, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close, volume, returns and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, historical returns, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) + (0.73 * rank(ts_rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap, adv20, 6)))) + (0.6 * rank((((sum(close, 200) / 200) - open) * (close - open)))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, historical returns, cross-asset correlations, historical time-series rank, lagged indicators, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, close, volume, vwap, returns and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, historical returns, cross-asset correlations, historical time-series rank, lagged indicators, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "mean_reversion",
        "expression": "(rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))",
        "rationales": [
            "Measures short-term price overextension using cross-asset correlations, lagged indicators, cross-sectional ranking to identify potential mean-reversion pivot points.",
            "Exploits market overreaction and liquidity imbalances by taking contrarian positions when open, close deviate from historical averages.",
            "Computes an inverse or normalized signal based on cross-asset correlations, lagged indicators, cross-sectional ranking, targeting mean-reversion tendencies across the asset universe."
        ]
    },
    {
        "theme": "trend",
        "expression": "((-1 * rank(ts_rank(close, 10))) * rank((close / open)))",
        "rationales": [
            "An alpha model that extracts persistent directional trends by filtering noise in open, close through historical time-series rank, cross-sectional ranking.",
            "Seeks to capture medium-to-long-term trend transitions by analyzing relative price moves of open, close and moving averages.",
            "Develops a multi-period trend indicator using historical time-series rank, cross-sectional ranking to establish stable directional exposure."
        ]
    },
    {
        "theme": "volume",
        "expression": "((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sum(returns, 250))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, historical returns, linearly decaying weights, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume, returns and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, historical returns, linearly decaying weights, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, rolling volatility, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, rolling volatility, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(((high * low)^0.5) - vwap)",
        "rationales": [
            "A trend-following signal that measures price momentum using VWAP imbalances to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from high, low, vwap, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of VWAP imbalances to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(rank((vwap - close)) / rank((vwap + close)))",
        "rationales": [
            "A trend-following signal that measures price momentum using VWAP imbalances, cross-sectional ranking to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, vwap, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of VWAP imbalances, cross-sectional ranking to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "(ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * correlation(high, rank(volume), 5))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * ((rank((sum(delay(close, 5), 20) / 20)) * correlation(close, volume, 2)) * rank(correlation(sum(close, 5), sum(close, 20), 2))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, lagged indicators, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, lagged indicators, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "((0.25 < (((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10))) ? (-1 * 1) : (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < 0) ? 1 : ((-1 * 1) * (close - delay(close, 1)))))",
        "rationales": [
            "A trend-following signal that measures price momentum using lagged indicators to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of lagged indicators to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "((((rank((1 / close)) * volume) / adv20) * ((high * rank((high - close))) / (sum(high, 5) / 5))) - rank((vwap - delay(vwap, 5))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, lagged indicators, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, close, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, lagged indicators, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "mean_reversion",
        "expression": "(indneutralize(((correlation(delta(close, 1), delta(delay(close, 1), 1), 250) * delta(close, 1)) / close), indclass.subindustry) / sum(((delta(close, 1) / delay(close, 1))^2), 250))",
        "rationales": [
            "Measures short-term price overextension using cross-asset correlations, industry neutralization, price differences, lagged indicators to identify potential mean-reversion pivot points.",
            "Exploits market overreaction and liquidity imbalances by taking contrarian positions when close deviate from historical averages.",
            "Computes an inverse or normalized signal based on cross-asset correlations, industry neutralization, price differences, lagged indicators, targeting mean-reversion tendencies across the asset universe."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.1)) ? 1 : ((-1 * 1) * (close - delay(close, 1))))",
        "rationales": [
            "A trend-following signal that measures price momentum using lagged indicators to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of lagged indicators to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking, rolling maximums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking, rolling maximums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.05)) ? 1 : ((-1 * 1) * (close - delay(close, 1))))",
        "rationales": [
            "A trend-following signal that measures price momentum using lagged indicators to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of lagged indicators to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "((((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) * rank(((sum(returns, 240) - sum(returns, 20)) / 220))) * ts_rank(volume, 5))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, historical returns, historical time-series rank, lagged indicators, cross-sectional ranking, rolling minimums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, volume, returns and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, historical returns, historical time-series rank, lagged indicators, cross-sectional ranking, rolling minimums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(-1 * delta((((close - low) - (high - close)) / (close - low)), 9))",
        "rationales": [
            "A trend-following signal that measures price momentum using price differences to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from high, low, close, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of price differences to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "trend",
        "expression": "((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))",
        "rationales": [
            "An alpha model that extracts persistent directional trends by filtering noise in open, high, low, close through historical trading features.",
            "Seeks to capture medium-to-long-term trend transitions by analyzing relative price moves of open, high, low, close and moving averages.",
            "Develops a multi-period trend indicator using historical trading features to establish stable directional exposure."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, cross-sectional ranking, rolling minimums, rolling maximums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, cross-sectional ranking, rolling minimums, rolling maximums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(0 - (1 * (rank((sum(returns, 10) / sum(sum(returns, 2), 3))) * rank((returns * cap)))))",
        "rationales": [
            "A trend-following signal that measures price momentum using historical returns, cross-sectional ranking to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from returns, cap, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of historical returns, cross-sectional ranking to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))",
        "rationales": [
            "A trend-following signal that measures price momentum using VWAP imbalances, linearly decaying weights, cross-sectional ranking, timing of maximum historical values to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, vwap, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of VWAP imbalances, linearly decaying weights, cross-sectional ranking, timing of maximum historical values to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * ts_rank(decay_linear(correlation(indneutralize(vwap, indclass.sector), volume, 3.92795), 7.89291), 5.50322))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(-1 * ts_rank(decay_linear(correlation(indneutralize(((vwap * 0.728317) + (vwap * (1 - 0.728317))), indclass.industry), volume, 4.25197), 16.2289), 8.19648))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(rank(ts_argmax(close, 10))))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, rescaled inputs, cross-sectional ranking, timing of maximum historical values and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, rescaled inputs, cross-sectional ranking, timing of maximum historical values to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank((vwap - ts_min(vwap, 16.1219))) < rank(correlation(vwap, adv180, 17.9282)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, cross-sectional ranking, rolling minimums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, cross-sectional ranking, rolling minimums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(correlation(vwap, sum(adv20, 22.4101), 9.91009)) < rank(((rank(open) + rank(open)) < (rank(((high + low) / 2)) + rank(high))))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, high, low, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(decay_linear(delta(indneutralize(close, indclass.industry), 2.25164), 8.22237)) - rank(decay_linear(correlation(((vwap * 0.318108) + (open * (1 - 0.318108))), sum(adv180, 37.2467), 13.557), 12.2883))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), sum(adv120, 12.7054), 16.6208)) < rank(delta(((((high + low) / 2) * 0.178404) + (vwap * (1 - 0.178404))), 3.69741))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, high, low, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374)) < rank((open - ts_min(open, 13.635)))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, cross-sectional ranking, rolling minimums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, cross-sectional ranking, rolling minimums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "((rank(decay_linear(delta(vwap, 3.51013), 7.23052)) + ts_rank(decay_linear(((((low * 0.96633) + (low * (1 - 0.96633))) - vwap) / (open - ((high + low) / 2))), 11.4157), 6.72611)) * -1)",
        "rationales": [
            "A trend-following signal that measures price momentum using VWAP imbalances, linearly decaying weights, historical time-series rank, price differences, cross-sectional ranking to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from open, high, low, vwap, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of VWAP imbalances, linearly decaying weights, historical time-series rank, price differences, cross-sectional ranking to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank((high - ts_min(high, 2.14593)))^rank(correlation(indneutralize(vwap, indclass.sector), indneutralize(adv20, indclass.subindustry), 6.02936))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, industry neutralization, cross-sectional ranking, rolling minimums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, industry neutralization, cross-sectional ranking, rolling minimums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((ts_rank(correlation(rank(high), rank(adv15), 8.91644), 13.9333) < rank(delta(((close * 0.518371) + (low * (1 - 0.518371))), 1.06157))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(ts_max(delta(indneutralize(vwap, indclass.industry), 2.72412), 4.79344))^ts_rank(correlation(((close * 0.490655) + (vwap * (1 - 0.490655))), adv20, 4.92416), 9.0615)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking, rolling maximums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking, rolling maximums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(delta(vwap, 1.29456))^ts_rank(correlation(indneutralize(close, indclass.industry), adv50, 17.8256), 17.9171)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "max(ts_rank(decay_linear(correlation(ts_rank(close, 3.43976), ts_rank(adv180, 12.0647), 18.0175), 4.20501), 15.6948), ts_rank(decay_linear((rank(((low + open) - (vwap + vwap)))^2), 16.4662), 4.4388))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, low, close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank(decay_linear(correlation(((high + low) / 2), adv40, 8.93345), 10.1519)) / rank(decay_linear(correlation(ts_rank(vwap, 3.72469), ts_rank(volume, 18.5188), 6.86671), 2.95011)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "(max(rank(decay_linear(delta(vwap, 4.72775), 2.91864)), ts_rank(decay_linear(((delta(((open * 0.147155) + (low * (1 - 0.147155))), 2.03608) / ((open * 0.147155) + (low * (1 - 0.147155)))) * -1), 3.33829), 16.7411)) * -1)",
        "rationales": [
            "A trend-following signal that measures price momentum using VWAP imbalances, linearly decaying weights, historical time-series rank, price differences, cross-sectional ranking to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from open, low, vwap, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of VWAP imbalances, linearly decaying weights, historical time-series rank, price differences, cross-sectional ranking to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(correlation(close, sum(adv30, 37.4843), 15.1365)) < rank(correlation(rank(((high * 0.0261661) + (vwap * (1 - 0.0261661)))), rank(volume), 11.4791))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, close, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank(correlation(vwap, volume, 4.24304)) < rank(correlation(rank(low), rank(adv50), 12.4413)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(max(rank(decay_linear(delta(vwap, 1.24383), 11.8259)), ts_rank(decay_linear(ts_rank(correlation(indneutralize(low, indclass.sector), adv81, 8.14941), 19.569), 17.1543), 19.383)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "min(rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20.0451)), rank(decay_linear(correlation(((high + low) / 2), adv40, 3.1614), 5.64125)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank(correlation(sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 19.7428), sum(adv40, 19.7428), 6.83313))^rank(correlation(rank(vwap), rank(volume), 5.77492)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank(delta(indneutralize(((close * 0.60733) + (open * (1 - 0.60733))), indclass.sector), 1.23438)) < rank(correlation(ts_rank(vwap, 3.60973), ts_rank(adv150, 9.18637), 14.6644)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(sign(delta(indneutralize(((open * 0.868128) + (high * (1 - 0.868128))), indclass.industry), 4.04545)))^ts_rank(correlation(high, adv10, 5.11456), 5.53756)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, high and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(Log(product(rank((rank(correlation(vwap, sum(adv10, 49.6054), 8.47743))^4)), 14.9655))) < rank(correlation(rank(vwap), rank(volume), 5.07914))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(min(rank(decay_linear(delta(open, 1.46063), 14.8717)), ts_rank(decay_linear(correlation(indneutralize(volume, indclass.sector), ((open * 0.634196) + (open * (1 - 0.634196))), 17.4842), 6.92131), 13.4283)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(delay(((high - low) / (sum(close, 5) / 5)), 2)) * rank(rank(volume))) / (((high - low) / (sum(close, 5) / 5)) / (vwap - close)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, lagged indicators, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, lagged indicators, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "momentum",
        "expression": "signedpower(ts_rank((vwap - ts_max(vwap, 15.3217)), 20.7127), delta(close, 4.96796))",
        "rationales": [
            "A trend-following signal that measures price momentum using VWAP imbalances, historical time-series rank, price differences, cross-sectional ranking, rolling maximums to identify sustained directional movements.",
            "Capitalizes on price persistence by tracking momentum indicators built from close, vwap, positioning for continuation of historical trends.",
            "Constructs a cross-sectional rank of VWAP imbalances, historical time-series rank, price differences, cross-sectional ranking, rolling maximums to prioritize assets showing the strongest relative historical performance."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank(correlation(((high * 0.876703) + (close * (1 - 0.876703))), adv30, 9.61331))^rank(correlation(ts_rank(((high + low) / 2), 3.70596), ts_rank(volume, 10.1595), 7.11408)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((ts_rank(correlation(close, sum(adv20, 14.7444), 6.00049), 20.4195) < rank(((open + close) - (vwap + open)))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(max(rank(decay_linear(delta(((close * 0.369701) + (vwap * (1 - 0.369701))), 1.91233), 2.65461)), ts_rank(decay_linear(abs(correlation(indneutralize(adv81, indclass.industry), close, 13.4132)), 4.89768), 14.4535)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8.06882)), ts_rank(decay_linear(correlation(ts_rank(close, 8.44728), ts_rank(adv60, 20.6966), 8.01266), 6.65053), 2.61957))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, high, low, close and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(ts_rank(decay_linear(correlation(((low * 0.967285) + (low * (1 - 0.967285))), adv10, 6.94279), 5.51607), 3.79744) - ts_rank(decay_linear(delta(indneutralize(vwap, indclass.industry), 3.48158), 10.1466), 15.3012))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank((close - ts_max(close, 4.66719)))^ts_rank(correlation(indneutralize(adv40, indclass.subindustry), low, 5.38375), 3.21856)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, industry neutralization, historical time-series rank, cross-sectional ranking, rolling maximums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, close and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, industry neutralization, historical time-series rank, cross-sectional ranking, rolling maximums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((ts_rank(decay_linear(decay_linear(correlation(indneutralize(close, indclass.industry), volume, 9.74928), 16.398), 3.83219), 4.8667) - rank(decay_linear(correlation(vwap, adv30, 4.01303), 2.6809))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "min(ts_rank(decay_linear(((((high + low) / 2) + close) < (low + open)), 14.7221), 18.8683), ts_rank(decay_linear(correlation(rank(low), rank(adv30), 7.58555), 6.94024), 6.80584))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, high, low, close and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(ts_rank(decay_linear(correlation(indneutralize(vwap, indclass.industry), adv81, 17.4193), 19.848), 7.54455) / rank(decay_linear(delta(((close * 0.524434) + (vwap * (1 - 0.524434))), 2.77377), 16.2664)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank((vwap - ts_min(vwap, 11.5783)))^ts_rank(correlation(ts_rank(vwap, 19.6462), ts_rank(adv60, 4.02992), 18.0926), 2.70756)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, historical time-series rank, cross-sectional ranking, rolling minimums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, historical time-series rank, cross-sectional ranking, rolling minimums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank((open - ts_min(open, 12.4105))) < ts_rank((rank(correlation(sum(((high + low) / 2), 19.1351), sum(adv40, 19.1351), 12.8742))^5), 11.7584))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between cross-asset correlations, historical time-series rank, cross-sectional ranking, rolling minimums and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, high, low and trading volume.",
            "A volume-based predictive signal utilizing cross-asset correlations, historical time-series rank, cross-sectional ranking, rolling minimums to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(max(ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 3.83878), 4.16783), 8.38151), ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close, 7.45404), ts_rank(adv60, 4.13242), 3.65459), 12.6556), 14.0365), 13.4143)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking, timing of maximum historical values and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between close, volume, vwap and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking, timing of maximum historical values to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(decay_linear(delta(indneutralize(((low * 0.721001) + (vwap * (1 - 0.721001))), indclass.industry), 3.3705), 20.4523)) - ts_rank(decay_linear(ts_rank(correlation(ts_rank(low, 7.87871), ts_rank(adv60, 17.255), 4.97547), 18.5925), 15.7152), 6.71659)) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between low, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, industry neutralization, historical time-series rank, price differences, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(rank(decay_linear(correlation(vwap, sum(adv5, 26.4719), 4.58418), 7.18088)) - rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open), rank(adv15), 20.8187), 8.62571), 6.95668), 8.07206)))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking, timing of minimum historical values and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between open, vwap and trading volume.",
            "A volume-based predictive signal utilizing VWAP imbalances, cross-asset correlations, linearly decaying weights, historical time-series rank, cross-sectional ranking, timing of minimum historical values to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "((rank(correlation(sum(((high + low) / 2), 19.8975), sum(adv60, 19.8975), 8.8136)) < rank(correlation(low, volume, 6.28259))) * -1)",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, cross-sectional ranking and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, cross-sectional ranking to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "volume",
        "expression": "(0 - (1 * (((1.5 * scale(indneutralize(indneutralize(rank(((((close - low) - (high - close)) / (high - low)) * volume)), indclass.subindustry), indclass.subindustry))) - scale(indneutralize((correlation(close, rank(adv20), 5) - rank(ts_argmin(close, 30))), indclass.subindustry))) * (volume / adv20))))",
        "rationales": [
            "Evaluates liquidity-driven market dynamics by calculating the relationship between volume metrics, cross-asset correlations, industry neutralization, rescaled inputs, cross-sectional ranking, timing of minimum historical values and transaction flow.",
            "Designed to detect institutional buying or selling pressure by analyzing the interaction between high, low, close, volume and trading volume.",
            "A volume-based predictive signal utilizing volume metrics, cross-asset correlations, industry neutralization, rescaled inputs, cross-sectional ranking, timing of minimum historical values to capture changes in trading intensity and capital flow across assets."
        ]
    },
    {
        "theme": "trend",
        "expression": "((close - open) / ((high - low) + .001))",
        "rationales": [
            "An alpha model that extracts persistent directional trends by filtering noise in open, high, low, close through historical trading features.",
            "Seeks to capture medium-to-long-term trend transitions by analyzing relative price moves of open, high, low, close and moving averages.",
            "Develops a multi-period trend indicator using historical trading features to establish stable directional exposure."
        ]
    },
    {
        "theme": 'rsi',
        "expression": '(-1 * rank(((100 - (100 / (1 + (sum((delta(close, 1) * (delta(close, 1) > 0)), 14) / sum((-delta(close, 1) * (delta(close, 1) < 0)), 14)))))) - 50))',
        "rationales": [
            'Fades overbought and oversold conditions by ranking a simple-moving-average approximation of RSI built from close price gains and losses, shorting stocks with elevated readings and favoring depressed ones',
            'A mean-reversion signal derived from relative strength (gains versus losses over a 14-day window), cross-sectionally ranked and inverted to bet against momentum extremes',
            'Constructs a contrarian ranking using an RSI-style gain/loss ratio computed purely from close price changes, exploiting short-term overreaction in price'
        ]
    },
    {
        "theme": 'rsi',
        "expression": 'rank(delta(((100 - (100 / (1 + (sum((delta(close, 1) * (delta(close, 1) > 0)), 14) / sum((-delta(close, 1) * (delta(close, 1) < 0)), 14)))))), 3))',
        "rationales": [
            'Tracks whether relative strength is accelerating or decelerating by ranking the 3-day change in an RSI-style gain/loss ratio built from close',
            'Captures shifts in momentum quality by measuring how quickly the balance of up-moves versus down-moves in close price is changing',
            'A second-derivative momentum signal: ranks the recent trend in a relative-strength proxy rather than its raw level'
        ]
    },
    {
        "theme": 'macd',
        "expression": 'rank(((decay_linear(close, 12) - decay_linear(close, 26)) - decay_linear((decay_linear(close, 12) - decay_linear(close, 26)), 9)))',
        "rationales": [
            'Ranks the gap between a fast and slow linearly-decayed moving average of close and its own smoothed trend, capturing accelerating bullish or bearish momentum',
            'A trend-acceleration signal built from two decay-weighted moving averages of close, isolating divergence between short- and long-term price averages',
            'Constructs a MACD-style histogram from linearly decaying weighted averages of close and ranks it cross-sectionally to find stocks with strengthening momentum'
        ]
    },
    {
        "theme": 'macd',
        "expression": 'rank(sign(((decay_linear(close, 12) - decay_linear(close, 26))) - (decay_linear((decay_linear(close, 12) - decay_linear(close, 26)), 9))))',
        "rationales": [
            'Classic moving-average crossover signal: ranks the sign of a fast-minus-slow decayed average of close relative to its own smoothed signal line',
            'Detects bullish/bearish crossovers in a MACD-style construction built entirely from close price, using linear decay as an EMA approximation',
            'A directional trend-following indicator that flags whether short-term price momentum (via decayed averages) has just turned positive or negative'
        ]
    },
    {
        "theme": 'bollinger',
        "expression": '(-1 * rank((close - ((sum(close, 20) / 20))) / ((((sum(close, 20) / 20) + (2 * stddev(close, 20)))) - ((sum(close, 20) / 20)))))',
        "rationales": [
            'Fades stocks trading near the upper edge of their 20-day price and volatility band, betting on reversion toward the mean',
            'A band-based mean-reversion signal that ranks how far close price has stretched toward its rolling mean plus two standard deviations, then inverts it',
            'Measures relative position within a volatility-adjusted price channel built from a 20-day moving average and standard deviation of close, shorting extended stocks'
        ]
    },
    {
        "theme": 'bollinger',
        "expression": '(-1 * rank(((4 * stddev(close, 20)) / (sum(close, 20) / 20))))',
        "rationales": [
            'Prefers stocks currently in a low-volatility regime, ranked by the width of their rolling standard-deviation-based price band relative to its mean',
            'A volatility-contraction signal: ranks the normalized spread between upper and lower price bands built from a 20-day mean and standard deviation of close',
            'Favors calmer names by inverting the rank of relative band width, a proxy for how compressed or stretched recent price dispersion has been'
        ]
    },
    {
        "theme": 'bollinger',
        "expression": 'rank((close < (((sum(close, 20) / 20) - (2 * stddev(close, 20))))) ? 1 : 0)',
        "rationales": [
            'Flags stocks currently trading below their lower 20-day volatility band as short-term reversion candidates',
            'A binary breakout-below-band indicator built from a 20-day moving average and standard deviation of close',
            'Identifies oversold conditions relative to a rolling mean-and-volatility price channel'
        ]
    },
    {
        "theme": 'volatility_indicators',
        "expression": '(-1 * rank(((sum((((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) > abs(low - delay(close, 1)) ? ((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) : abs(low - delay(close, 1))), 14) / 14)) / close))',
        "rationales": [
            'Prefers stocks with lower normalized daily trading-range volatility, using a simple-moving-average approximation of average true range scaled by price',
            'A low-volatility tilt built from the average of the largest intraday and overnight price swings over the past 14 days, normalized by current price',
            'Ranks and inverts a true-range-based volatility measure combining high, low and close, favoring names with calmer recent price action'
        ]
    },
    {
        "theme": 'volatility_indicators',
        "expression": 'rank(delta(((sum((((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) > abs(low - delay(close, 1)) ? ((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) : abs(low - delay(close, 1))), 14) / 14)), 5))',
        "rationales": [
            'Flags expanding volatility regimes by ranking the 5-day change in a true-range-based volatility proxy built from high, low and close',
            'Captures the early stages of a volatility breakout by tracking the trend in average trading range over the past two weeks',
            'A regime-shift signal that ranks stocks whose recent price-range volatility is rising fastest relative to two weeks prior'
        ]
    },
    {
        "theme": 'stochastic',
        "expression": '(-1 * rank(((100 * (close - ts_min(low, 14)) / (ts_max(high, 14) - ts_min(low, 14)))) - 50))',
        "rationales": [
            'Fades stochastic-oscillator extremes by ranking how far current close sits within its 14-day high-low range, then inverting the signal',
            "A range-based mean-reversion indicator measuring close's position relative to its recent trading range, shorting names near the top of their range",
            'Constructs a %K-style oscillator from high, low and close and bets against readings far from the midpoint'
        ]
    },
    {
        "theme": 'stochastic',
        "expression": 'rank(sign(((100 * (close - ts_min(low, 14)) / (ts_max(high, 14) - ts_min(low, 14)))) - ((sum((100 * (close - ts_min(low, 14)) / (ts_max(high, 14) - ts_min(low, 14))), 3) / 3))))',
        "rationales": [
            'Detects stochastic %K crossing above or below its own 3-day smoothed average, a classic short-term reversal/continuation trigger',
            'Ranks the sign of the gap between a fast range-position oscillator and its smoothed version, built from high, low and close',
            'A crossover-based timing signal derived from where close sits in its recent range versus a smoothed version of that same measure'
        ]
    },
    {
        "theme": 'stochastic',
        "expression": 'rank((-100 * (ts_max(high, 14) - close) / (ts_max(high, 14) - ts_min(low, 14))))',
        "rationales": [
            'Ranks a Williams %R-style measure of how far current close sits below its 14-day high, capturing short-term relative strength',
            'A range-position momentum signal built from high, low and close, closely related to the stochastic oscillator but inverted in scale',
            'Measures proximity to recent highs versus lows over a two-week window, ranked cross-sectionally as a momentum proxy'
        ]
    },
    {
        "theme": 'cci_obv',
        "expression": '(-1 * rank(((((high + low + close) / 3) - (sum(((high + low + close) / 3), 20) / 20)) / (0.015 * (sum(abs(((high + low + close) / 3) - (sum(((high + low + close) / 3), 20) / 20)), 20) / 20)))))',
        "rationales": [
            'Fades extreme deviations of the typical price (average of high, low, close) from its own 20-day moving average, scaled by mean absolute deviation',
            'A Commodity-Channel-Index-style mean-reversion signal built from high, low and close, betting against stocks far from their recent average price level',
            'Ranks and inverts a normalized price-deviation measure to capture short-term overextension in either direction'
        ]
    },
    {
        "theme": 'cci_obv',
        "expression": 'rank(delta(((sum(sign(delta(close, 1)) * volume, 100))), 10))',
        "rationales": [
            'Tracks the 10-day change in a windowed on-balance-volume proxy (signed volume accumulated over the past 100 days), capturing shifts in accumulation or distribution',
            'A volume-flow momentum signal built from the direction of daily price change multiplied by volume, summed over a trailing window',
            'Ranks stocks by how quickly their cumulative signed-volume flow is changing, a proxy for building buying or selling pressure'
        ]
    },
    {
        "theme": 'cci_obv',
        "expression": 'rank(correlation(((sum(sign(delta(close, 1)) * volume, 100))), close, 20))',
        "rationales": [
            'Confirms price trends with volume flow by ranking the 20-day correlation between a windowed on-balance-volume proxy and close price',
            'A trend-confirmation signal: high correlation between signed cumulative volume and price suggests a move is backed by genuine participation',
            'Combines volume-flow and price-trend information into a single cross-sectional ranking based on their recent co-movement'
        ]
    },
    {
        "theme": 'trend_strength',
        "expression": 'rank((sum((100 * abs((100 * sum((delta(high, 1) * (delta(high, 1) > (-delta(low, 1))) * (delta(high, 1) > 0)), 14) / sum((((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) > abs(low - delay(close, 1)) ? ((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) : abs(low - delay(close, 1))), 14)) - (100 * sum(((-delta(low, 1)) * ((-delta(low, 1)) > delta(high, 1)) * ((-delta(low, 1)) > 0)), 14) / sum((((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) > abs(low - delay(close, 1)) ? ((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) : abs(low - delay(close, 1))), 14))) / ((100 * sum((delta(high, 1) * (delta(high, 1) > (-delta(low, 1))) * (delta(high, 1) > 0)), 14) / sum((((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) > abs(low - delay(close, 1)) ? ((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) : abs(low - delay(close, 1))), 14)) + (100 * sum(((-delta(low, 1)) * ((-delta(low, 1)) > delta(high, 1)) * ((-delta(low, 1)) > 0)), 14) / sum((((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) > abs(low - delay(close, 1)) ? ((high - low) > abs(high - delay(close, 1)) ? (high - low) : abs(high - delay(close, 1))) : abs(low - delay(close, 1))), 14)))), 14) / 14))',
        "rationales": [
            'Prefers stocks currently in a strong directional trend, using a simplified average-directional-index built from high, low and close',
            'A trend-strength filter combining smoothed directional movement (up-moves versus down-moves, weighted by true range) into a single ranked measure',
            'Ranks names by the intensity of their recent directional price movement, regardless of whether the trend is up or down'
        ]
    },
    {
        "theme": 'ichimoku',
        "expression": 'rank(close - (((ts_max(high, 26) + ts_min(low, 26)) / 2)))',
        "rationales": [
            'Ranks the distance of close price above or below its Ichimoku base line, the midpoint of the 26-day high-low range',
            'A trend-positioning signal measuring how far price has moved from its longer-term high-low equilibrium level built from high and low',
            'Captures deviation from a slower-moving price anchor derived from the average of 26-day extremes'
        ]
    },
    {
        "theme": 'ichimoku',
        "expression": 'rank(sign((((ts_max(high, 9) + ts_min(low, 9)) / 2)) - (((ts_max(high, 26) + ts_min(low, 26)) / 2))))',
        "rationales": [
            'Implements the Ichimoku TK-cross: ranks the sign of the gap between a fast 9-day and slow 26-day high-low midpoint, a classic bullish/bearish trigger',
            'A dual-timeframe trend-crossover signal built entirely from rolling high/low extremes at two different lookback windows',
            'Flags recent shifts in short-versus-long-term price equilibrium using the Ichimoku conversion and base line construction'
        ]
    },
    {
        "theme": 'trend',
        "expression": 'rank(close - ((sum(close, 20) / 20)))',
        "rationales": [
            'Ranks the distance of close price from its own 20-day simple moving average, a basic trend-following momentum measure',
            'Captures whether a stock is trading above or below its recent average price level, a foundational trend-strength proxy',
            'A straightforward price-versus-moving-average signal, ranked cross-sectionally to compare relative trend positioning across names'
        ]
    },
    {
        "theme": 'trend',
        "expression": 'rank(close - (decay_linear(close, 20)))',
        "rationales": [
            'Ranks price relative to a recency-weighted moving average of close (approximated via linear decay), emphasizing more recent price action than a simple average',
            'A trend signal similar to price-vs-SMA but weighting recent days more heavily, built using a linearly decaying moving average',
            'Measures deviation from a smoothed, recency-tilted price trend, useful for detecting faster-reacting momentum shifts'
        ]
    }
]
THEMES = sorted(set(item['theme'] for item in WORLDQUANT_INSPIRED_ALPHAS))

if __name__ == "__main__":
    cnt = {}
    for item in WORLDQUANT_INSPIRED_ALPHAS:
        if item['theme'] not in cnt:
            cnt[item['theme']] = 1
        else:
            cnt[item['theme']] += 1

    print(sorted(cnt.items(), key=lambda item: item[1]))
    # [('trend_strength', 1), ('rsi', 2), ('macd', 2), ('volatility_indicators', 2), ('ichimoku', 2), ('volatility', 3), ('mean_reversion', 3), ('bollinger', 3), ('stochastic', 3), ('cci_obv', 3), ('trend', 8), ('momentum', 19), ('volume', 70)]
