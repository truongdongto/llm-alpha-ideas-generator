"""
llm_gen/reward.py
==================
Converts a backtested alpha into a single scalar reward.

This ONE function is used in two places:
  1. The in-context generate-backtest-feedback loop (orchestrate.py) --
     to rank the leaderboard and decide what to show the LLM as "good".
  2. The PPO reward signal (ppo_finetune.py) -- the exact same function,
     so the model is fine-tuned to optimize the thing we actually
     display and screen alphas by. Keeping these identical is
     deliberate: a common RLHF pitfall is training against a reward
     that doesn't match the metric you evaluate on.

Reward components:
    + |mean_ic|, capped and normalized to [0, 1]
        Sign doesn't matter -- an alpha with IC = -0.05 is exactly as
        tradeable as one with IC = +0.05 (just trade it inverted), so we
        reward magnitude, not direction.
    - turnover penalty
        Only kicks in above `turnover_cap`; alphas that trade too much
        eat their edge in transaction costs.
    - diversity penalty
        Only kicks in when `diversity_max_corr` (the alpha's max |correlation|
        against the current accepted pool) exceeds `corr_threshold` --
        discourages sign-flip / trivial-rescaling duplicates of alphas
        already found.
    - flat invalid penalty
        Applied instead of everything else when the expression didn't
        parse or evaluate at all. This is the signal that teaches the
        policy (in PPO) to stay within the DSL grammar.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class RewardWeights:
    ic_cap: float = 0.15           # |mean_ic| at or above this maps to full IC reward of 1.0
    turnover_cap: float = 0.5      # turnover above this starts being penalized
    turnover_penalty: float = 0.5  # penalty weight per unit of turnover over the cap
    corr_threshold: float = 0.5    # |correlation to pool| above this starts being penalized
    corr_penalty: float = 1.0      # penalty weight per unit of correlation over the threshold
    invalid_penalty: float = -1.0  # flat reward for syntax/semantic errors


DEFAULT_WEIGHTS = RewardWeights()

def compute_reward(
    mean_ic: float | None,
    turnover: float | None,
    diversity_max_corr: float,
    valid: bool,
    weights: RewardWeights = DEFAULT_WEIGHTS,
) -> float:
    if not valid or mean_ic is None or not np.isfinite(mean_ic):
        return weights.invalid_penalty

    ic_component = min(abs(mean_ic), weights.ic_cap) / weights.ic_cap

    turnover_component = 0.0
    if turnover is not None and np.isfinite(turnover):
        turnover_component = weights.turnover_penalty * max(0.0, turnover - weights.turnover_cap)

    corr_component = weights.corr_penalty * max(0.0, diversity_max_corr - weights.corr_threshold)

    return ic_component - turnover_component - corr_component


if __name__ == "__main__":
    cases = [
        dict(mean_ic=0.20, turnover=0.3, diversity_max_corr=0.1, valid=True),   # strong, cheap, diverse -> near max reward
        dict(mean_ic=0.03, turnover=0.3, diversity_max_corr=0.1, valid=True),   # weak IC -> low reward
        dict(mean_ic=0.20, turnover=1.5, diversity_max_corr=0.1, valid=True),   # strong but expensive to trade
        dict(mean_ic=0.20, turnover=0.3, diversity_max_corr=0.95, valid=True),  # strong but redundant vs pool
        dict(mean_ic=None, turnover=None, diversity_max_corr=0.0, valid=False), # invalid expression
    ]
    for c in cases:
        r = compute_reward(**c)
        print(f"{c} -> reward={r:.3f}")