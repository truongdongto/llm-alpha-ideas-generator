"""
orchestrate.py
===============
The generate -> validate -> backtest -> feedback loop described in the
project roadmap. This is the piece that turns a raw idea generator (mock
or real LLM) into an actual research process: run N rounds, each round
ask the generator for ideas, test every idea, keep a running leaderboard,
and feed a summary of what worked / didn't back into the next round's
prompt.

This module is generator-agnostic -- it only depends on the
AlphaIdeaGenerator interface (llm_gen.base), so swapping
FixedPoolGenerator for QwenAlphaGenerator requires changing exactly one
line in the caller.
"""

from __future__ import annotations
import pandas as pd

from dsl.evaluator import evaluate_expression, AlphaEvaluationError
from dsl.parser import AlphaExpressionSyntaxError
from backtest.engine import backtest_alpha, alpha_correlation
from llm_gen.base import AlphaIdeaGenerator, AlphaIdea
from llm_gen.prompt_builder import build_user_prompt
from llm_gen.reward import compute_reward, RewardWeights, DEFAULT_WEIGHTS


LEADERBOARD_COLUMNS = [
    "round", "expression", "rationale", "valid", "error",
    "mean_ic", "ic_ir", "turnover", "long_short_tstat",
    "diversity_max_corr", "reward",
]


class AlphaResearchLoop:
    def __init__(
        self,
        generator: AlphaIdeaGenerator,
        panel: dict[str, pd.DataFrame],
        n_rounds: int = 3,
        ideas_per_round: int = 5,
        top_k_context: int = 5,
        pool_accept_reward: float = 0.3,
        pool_max_size: int = 20,
        backtest_horizons: tuple[int, ...] = (1, 5, 10),
        n_quantiles: int = 5,
        weights: RewardWeights = DEFAULT_WEIGHTS,
    ):
        self.generator = generator
        self.panel = panel
        self.n_rounds = n_rounds
        self.ideas_per_round = ideas_per_round
        self.top_k_context = top_k_context
        self.pool_accept_reward = pool_accept_reward
        self.pool_max_size = pool_max_size
        self.backtest_horizons = backtest_horizons
        self.n_quantiles = n_quantiles
        self.weights = weights

        self.leaderboard = pd.DataFrame(columns=LEADERBOARD_COLUMNS)
        # accepted_pool holds {expression: signal_dataframe} for alphas
        # good enough to matter for future diversity checks -- NOT every
        # attempted alpha, only ones that cleared pool_accept_reward
        self.accepted_pool: dict[str, pd.DataFrame] = {}

    # -----------------------------------------------------------------
    def _diversity_max_corr(self, signal: pd.DataFrame) -> float:
        """Max |correlation| of this signal against every signal currently in the pool."""
        if not self.accepted_pool:
            return 0.0
        corrs = [abs(alpha_correlation(signal, other)) for other in self.accepted_pool.values()]
        return max(corrs) if corrs else 0.0

    def _maybe_add_to_pool(self, expression: str, signal: pd.DataFrame, reward: float) -> None:
        if reward < self.pool_accept_reward:
            return
        self.accepted_pool[expression] = signal
        if len(self.accepted_pool) > self.pool_max_size:
            # drop the weakest-reward member to keep the pool bounded;
            # look it up from the leaderboard since that's where rewards live
            valid_rows = self.leaderboard[self.leaderboard["expression"].isin(self.accepted_pool)]
            weakest = valid_rows.sort_values("reward").iloc[0]["expression"]
            self.accepted_pool.pop(weakest, None)

    # -----------------------------------------------------------------
    def _evaluate_one_idea(self, idea: AlphaIdea, round_num: int) -> dict:
        row = {
            "round": round_num, "expression": idea.expression, "rationale": idea.rationale,
            "valid": False, "error": "", "mean_ic": float("nan"), "ic_ir": float("nan"),
            "turnover": float("nan"), "long_short_tstat": float("nan"),
            "diversity_max_corr": float("nan"), "reward": float("nan"),
        }
        try:
            signal = evaluate_expression(idea.expression, self.panel)
        except (AlphaExpressionSyntaxError, AlphaEvaluationError) as e:
            row["error"] = str(e)
            row["reward"] = compute_reward(None, None, 0.0, valid=False, weights=self.weights)
            return row
        except Exception as e:  # noqa: BLE001 -- defensively catch anything else
            # a malformed expression could in principle trip an unexpected
            # numpy/pandas error (e.g. divide by a literal 0 window); treat
            # it the same as any other invalid expression rather than
            # crashing the whole research loop over one bad LLM output
            row["error"] = f"unexpected evaluation error: {e}"
            row["reward"] = compute_reward(None, None, 0.0, valid=False, weights=self.weights)
            return row

        result = backtest_alpha(
            signal, self.panel["close"],
            horizons=self.backtest_horizons, n_quantiles=self.n_quantiles,
        )
        mean_ic = result["primary_horizon_ic"]["mean_ic"]
        diversity = self._diversity_max_corr(signal)
        reward = compute_reward(
            mean_ic=mean_ic, turnover=result["turnover"],
            diversity_max_corr=diversity, valid=True, weights=self.weights,
        )

        row.update({
            "valid": True,
            "mean_ic": mean_ic,
            "ic_ir": result["primary_horizon_ic"]["ic_ir"],
            "turnover": result["turnover"],
            "long_short_tstat": result["quantile_summary"]["long_short_tstat"],
            "diversity_max_corr": diversity,
            "reward": reward,
        })
        self._maybe_add_to_pool(idea.expression, signal, reward)
        return row

    # -----------------------------------------------------------------
    def run(self, verbose: bool = True) -> pd.DataFrame:
        for round_num in range(1, self.n_rounds + 1):
            context = build_user_prompt(self.ideas_per_round, self.leaderboard, top_k=self.top_k_context)
            ideas = self.generator.generate(self.ideas_per_round, context)

            if verbose:
                print(f"\n=== Round {round_num}: generator proposed {len(ideas)} idea(s) ===")

            round_rows = [self._evaluate_one_idea(idea, round_num) for idea in ideas]
            self.leaderboard = pd.concat(
                [self.leaderboard, pd.DataFrame(round_rows)], ignore_index=True
            )
            # pd.concat can leave "valid" as object dtype (e.g. when the
            # leaderboard started life as an empty frame); force it back
            # to bool so downstream boolean masks (~leaderboard["valid"])
            # behave correctly instead of silently bitwise-negating ints.
            self.leaderboard["valid"] = self.leaderboard["valid"].astype(bool)

            if verbose:
                for r in round_rows:
                    status = f"reward={r['reward']:.3f}" if r["valid"] else f"INVALID ({r['error'][:60]})"
                    print(f"  {r['expression']:45s} -> {status}")

        return self.leaderboard.sort_values("reward", ascending=False).reset_index(drop=True)