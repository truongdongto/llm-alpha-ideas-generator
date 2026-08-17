"""
test_orchestration_loop.py
============================
Validates orchestrate.AlphaResearchLoop end to end using deterministic
mock generators (llm_gen.mock_generator) instead of a real LLM, so we
can assert EXACTLY what should happen:

  1. A genuinely predictive expression ("factor", built into a synthetic
     dataset with a known predictive relationship, same technique as
     Module 4's oracle test) should rank at/near the top of the
     leaderboard by reward.
  2. Syntactically invalid expressions get reward == invalid_penalty
     (-1.0) and never crash the loop.
  3. A sign-flip duplicate of an already-accepted good alpha ("-factor"
     proposed AFTER "factor" is already in the pool) gets its reward
     reduced by the diversity penalty, even though its raw |IC| is just
     as strong.
  4. The feedback_context passed to the generator on round 2 actually
     contains a reference to the best alpha found in round 1 -- proving
     context threading works, not just that rewards get computed.
  5. EchoFeedbackGenerator (which reacts to feedback) successfully
     avoids repeating an expression it was told was invalid.
"""

import numpy as np
import pandas as pd

from orchestrate import AlphaResearchLoop
from llm_gen.base import AlphaIdea
from llm_gen.mock_generator import FixedPoolGenerator, EchoFeedbackGenerator

failures = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    if not condition:
        failures.append(label)
    print(f"[{status}] {label}")


# ---------------------------------------------------------------------------
# Build a synthetic panel with a KNOWN predictive relationship (same
# technique as Module 4's oracle test), so we know in advance which
# alpha SHOULD win.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(99)
n_days, n_tickers = 200, 20
dates = pd.bdate_range("2022-01-03", periods=n_days)
tick = [f"S{i:02d}" for i in range(n_tickers)]

factor = pd.DataFrame(rng.standard_normal((n_days, n_tickers)), index=dates, columns=tick)
factor_z = factor.sub(factor.mean(axis=1), axis=0).div(factor.std(axis=1), axis=0)
noise = pd.DataFrame(rng.standard_normal((n_days, n_tickers)), index=dates, columns=tick)
daily_log_ret = 0.03 * factor_z.shift(1).fillna(0.0) + 0.01 * noise
close = 100 * np.exp(daily_log_ret.cumsum())
unrelated = pd.DataFrame(rng.standard_normal((n_days, n_tickers)), index=dates, columns=tick)
volume = pd.DataFrame(rng.integers(1_000_000, 5_000_000, size=(n_days, n_tickers)).astype(float),
                       index=dates, columns=tick)

panel = {
    "close": close, "open": close, "high": close, "low": close,
    "volume": volume, "returns": close.pct_change(), "vwap": close,
    "adv20": volume.rolling(20, min_periods=1).mean(),
    "factor": factor_z,           # the genuinely predictive field
    "unrelated_field": unrelated,  # a decoy with no real predictive power
}

# ---------------------------------------------------------------------------
# Part 1-3: single loop, one round, mixed batch of good / bad / invalid ideas
# ---------------------------------------------------------------------------
round1_batch = [
    AlphaIdea("factor", "the genuinely predictive field"),
    AlphaIdea("unrelated_field", "a decoy with no real signal"),
    AlphaIdea("unknown_function_xyz(close, 5)", "deliberately invalid: unknown function"),
    AlphaIdea("ts_delta(close", "deliberately invalid: malformed syntax"),
]
round2_batch = [
    AlphaIdea("-factor", "sign-flip duplicate of the winning alpha from round 1"),
]

gen = FixedPoolGenerator(batches=[round1_batch, round2_batch])
loop = AlphaResearchLoop(
    generator=gen, panel=panel, n_rounds=2, ideas_per_round=4,
    pool_accept_reward=0.3,
)
leaderboard = loop.run(verbose=True)

# --- correctness checks ---
factor_row = leaderboard[leaderboard["expression"] == "factor"].iloc[0]
unrelated_row = leaderboard[leaderboard["expression"] == "unrelated_field"].iloc[0]
invalid_rows = leaderboard[~leaderboard["valid"]]

check(
    f"'factor' (real signal) has much higher reward than 'unrelated_field' "
    f"({factor_row['reward']:.3f} vs {unrelated_row['reward']:.3f})",
    factor_row["reward"] > unrelated_row["reward"] + 0.3,
)
check(
    "'factor' ranks #1 overall on the leaderboard",
    leaderboard.iloc[0]["expression"] == "factor",
)
check(
    f"both invalid expressions got reward == invalid_penalty (-1.0), got {invalid_rows['reward'].tolist()}",
    (invalid_rows["reward"] == -1.0).all(),
)
check(
    "invalid expressions are marked valid=False with a captured error message",
    (~invalid_rows["valid"]).all() and (invalid_rows["error"].str.len() > 0).all(),
)

# --- diversity penalty check ---
neg_factor_row = leaderboard[leaderboard["expression"] == "-factor"].iloc[0]
check(
    f"'-factor' (sign-flip duplicate) has high diversity_max_corr against the pool "
    f"(got {neg_factor_row['diversity_max_corr']:.3f})",
    neg_factor_row["diversity_max_corr"] > 0.9,
)
check(
    f"'-factor' reward is penalized for redundancy despite strong raw |IC| "
    f"(reward={neg_factor_row['reward']:.3f} vs factor's {factor_row['reward']:.3f})",
    neg_factor_row["reward"] < factor_row["reward"] - 0.2,
)
check(
    "-factor's raw |mean_ic| is still just as strong as factor's (proves the "
    "penalty came from diversity, not from the IC itself being weaker)",
    np.isclose(abs(neg_factor_row["mean_ic"]), abs(factor_row["mean_ic"]), atol=1e-8),
)

# --- feedback context threading check ---
check(
    "round 1 was called with empty/no-history feedback context",
    "No alphas have been tried yet" in gen.received_contexts[0],
)
check(
    "round 2's feedback context references the winning 'factor' expression from round 1",
    '"factor"' in gen.received_contexts[1],
)
check(
    "round 2's feedback context includes the mean_ic of the winning alpha",
    f"{factor_row['mean_ic']:.4f}" in gen.received_contexts[1],
)

# ---------------------------------------------------------------------------
# Part 4: EchoFeedbackGenerator actually avoids a previously-invalid expression
# ---------------------------------------------------------------------------
candidates = [
    AlphaIdea("ts_delta(close", "malformed, should get flagged as invalid in round 1"),
    AlphaIdea("factor", "valid backup idea"),
]
echo_gen = EchoFeedbackGenerator(candidate_pool=candidates)
echo_loop = AlphaResearchLoop(generator=echo_gen, panel=panel, n_rounds=2, ideas_per_round=2)
echo_leaderboard = echo_loop.run(verbose=False)

round2_expressions = echo_leaderboard[echo_leaderboard["round"] == 2]["expression"].tolist()
check(
    f"EchoFeedbackGenerator stops proposing the invalid expression once it's in "
    f"feedback history (round 2 proposed: {round2_expressions})",
    "ts_delta(close" not in round2_expressions,
)

# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")