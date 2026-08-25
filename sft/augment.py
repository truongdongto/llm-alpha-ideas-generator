# Augmentation pipeline for sft/worldquant_alphas.py.
#
# Two things this does:
#   1. Parametric perturbation: walk each expression's AST, generate variants
#      by scaling window sizes / numeric kwargs and swapping equivalent
#      fields. Every variant is re-validated through the REAL dsl.evaluator
#      before being kept -- nothing invalid ever reaches the dataset.
#   2. Rationale paraphrasing: attach 2-3 alternate phrasings per expression
#      (templated, deterministic -- not LLM-based) so SFT sees a many-to-one
#      prompt->expression mapping instead of memorizing one exact sentence.
#
# Output schema change: each alpha entry now has "rationales" (list) instead
# of "rationale" (single string), plus a "source" tag ("original"/"augmented").

from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dsl.parser import parse_expression, AlphaExpressionSyntaxError, Number, Boolean, Field, FuncCall, BinOp, UnaryNeg
from dsl.operators import REGISTRY
from dsl.evaluator import Evaluator, evaluate_expression, AlphaEvaluationError
from data_layer import generate_synthetic_data

# conservative: only swap fields that are genuinely interchangeable in role
FIELD_SWAP_GROUPS = {"close": ["vwap"], "vwap": ["close"]}
WINDOW_SCALE_FACTORS = [0.5, 2.0]      # shrink / grow window args
KWARG_SCALE_FACTORS = [0.75, 1.5]      # milder perturbation for kwargs (std, rate, etc.)
MIN_WINDOW = 2


# ---------------------------------------------------------------------------
# AST unparse (node -> expression string). Always parenthesizes non-atomic
# children -- verbose but guarantees correctness without precedence logic.
# ---------------------------------------------------------------------------

def _fmt_num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def unparse(node) -> str:
    if isinstance(node, Number):
        return _fmt_num(node.value)
    if isinstance(node, Boolean):
        return "true" if node.value else "false"
    if isinstance(node, Field):
        return node.name
    if isinstance(node, UnaryNeg):
        return f"-({unparse(node.operand)})"
    if isinstance(node, BinOp):
        return f"({unparse(node.left)} {node.op} {unparse(node.right)})"
    if isinstance(node, FuncCall):
        parts = [unparse(a) for a in node.pos_args]
        parts += [f"{k}={unparse(v)}" for k, v in node.kwargs.items()]
        return f"{node.name}({', '.join(parts)})"
    raise TypeError(f"Cannot unparse node type {type(node)}")


# ---------------------------------------------------------------------------
# AST replace-by-identity: rebuilds the tree with exactly one target node
# (matched by id(), not value) swapped for a new node.
# ---------------------------------------------------------------------------

def _replace(node, target_id: int, new_node):
    if id(node) == target_id:
        return new_node
    if isinstance(node, FuncCall):
        new_pos = tuple(_replace(a, target_id, new_node) for a in node.pos_args)
        new_kwargs = {k: _replace(v, target_id, new_node) for k, v in node.kwargs.items()}
        return FuncCall(node.name, new_pos, new_kwargs)
    if isinstance(node, BinOp):
        return BinOp(node.op, _replace(node.left, target_id, new_node), _replace(node.right, target_id, new_node))
    if isinstance(node, UnaryNeg):
        return UnaryNeg(_replace(node.operand, target_id, new_node))
    return node  # Number / Field / Boolean leaves: unchanged unless they were the target


# ---------------------------------------------------------------------------
# Collect perturbable targets: (node, kind) pairs, kind in {'window','kwarg','field'}
# ---------------------------------------------------------------------------

def _collect_targets(node, targets: list) -> None:
    if isinstance(node, FuncCall):
        spec = REGISTRY.get(node.name)
        if spec is not None and spec.arg_types is not None:
            for typ, arg in zip(spec.arg_types, node.pos_args):
                if typ == "int" and isinstance(arg, Number):
                    targets.append((arg, "window"))
                else:
                    _collect_targets(arg, targets)
        else:  # variadic or unknown -- treat all positional args as data
            for arg in node.pos_args:
                _collect_targets(arg, targets)
        for v in node.kwargs.values():
            if isinstance(v, Number):
                targets.append((v, "kwarg"))
    elif isinstance(node, Field):
        if node.name in FIELD_SWAP_GROUPS:
            targets.append((node, "field"))
    elif isinstance(node, BinOp):
        _collect_targets(node.left, targets)
        _collect_targets(node.right, targets)
    elif isinstance(node, UnaryNeg):
        _collect_targets(node.operand, targets)
    # Number / Boolean leaves not reachable via FuncCall args: nothing to do


# ---------------------------------------------------------------------------
# Variant generation
# ---------------------------------------------------------------------------

def generate_variant_strings(expr_str: str) -> list[str]:
    """One perturbation per candidate variant (change exactly one leaf)."""
    root = parse_expression(expr_str)
    targets = []
    _collect_targets(root, targets)

    variants = set()
    for node, kind in targets:
        if kind == "window":
            for factor in WINDOW_SCALE_FACTORS:
                new_val = max(MIN_WINDOW, round(node.value * factor))
                if new_val == node.value:
                    continue
                new_root = _replace(root, id(node), Number(float(new_val)))
                variants.add(unparse(new_root))
        elif kind == "kwarg":
            for factor in KWARG_SCALE_FACTORS:
                new_val = round(node.value * factor, 4)
                if new_val == node.value or new_val <= 0:
                    continue
                new_root = _replace(root, id(node), Number(new_val))
                variants.add(unparse(new_root))
        elif kind == "field":
            for swap_name in FIELD_SWAP_GROUPS[node.name]:
                new_root = _replace(root, id(node), Field(swap_name))
                variants.add(unparse(new_root))

    variants.discard(expr_str)
    return sorted(variants)


def validate_expression(expr_str: str, panel) -> bool:
    try:
        result = Evaluator(panel).eval(parse_expression(expr_str))
        return result.shape == panel["close"].shape
    except (AlphaEvaluationError, ValueError, ZeroDivisionError):
        return False
    except Exception:
        return False  # defensive: never let one bad variant crash the whole pipeline


# ---------------------------------------------------------------------------
# Rationale paraphrasing -- templated, deterministic, no LLM call needed.
# Matches common sentence shapes in the curated rationales; falls back to
# generic wrapper phrasings for anything that doesn't match.
# ---------------------------------------------------------------------------

_REPHRASE_RULES = [
    (re.compile(r"^(.*), ranked cross-sectionally$", re.I),
     lambda m: f"Cross-sectional rank of {m.group(1)[0].lower()}{m.group(1)[1:]}"),
    (re.compile(r"^prefer (lower|higher) (.*)$", re.I),
     lambda m: f"Favors stocks with {m.group(1)} {m.group(2)}"),
    (re.compile(r"^fade (.*)$", re.I),
     lambda m: f"Mean-reversion signal that fades {m.group(1)}"),
    (re.compile(r"^(\d+)-day (.*)$"),
     lambda m: f"Uses a {m.group(1)}-day window to capture {m.group(2)}"),
]
_GENERIC_WRAPPERS = ["Alpha idea: {r}", "Signal based on {r_lower}"]


def paraphrase_rationale(base: str, n: int = 2) -> list[str]:
    """Returns [base] + up to n alternate phrasings, deduplicated."""
    variants = [base]
    for pattern, template in _REPHRASE_RULES:
        m = pattern.match(base)
        if m:
            variants.append(template(m))
            break
    for wrapper in _GENERIC_WRAPPERS:
        candidate = wrapper.format(r=base, r_lower=base[0].lower() + base[1:] if base else base)
        variants.append(candidate)
    # dedupe while preserving order, cap at 1 (base) + n alternates
    seen, out = set(), []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out[: n + 1]


# ---------------------------------------------------------------------------
# Full pipeline: original alphas -> perturbed + validated + paraphrased pool
# ---------------------------------------------------------------------------

def build_augmented_pool(original_alphas: list[dict], seed: int = 0, n_tickers: int = 20, n_days: int = 120) -> list[dict]:
    panel = generate_synthetic_data([f"T{i:02d}" for i in range(n_tickers)], n_days=n_days, seed=seed)

    # Pass 1: validate every ORIGINAL first. Don't let one bad formula (typo,
    # unsupported operator, paper notation we don't handle) crash the whole
    # pipeline -- report it and keep going so you get a full picture of what
    # needs manual fixing across all 101 formulas in one run.
    valid_originals, rejected = [], []
    for a in original_alphas:
        base_rationale = a["rationale"] if "rationale" in a else a["rationales"][0]
        try:
            parse_expression(a["expression"])
            evaluate_expression(a["expression"], panel)
            valid_originals.append(a)
        except (AlphaExpressionSyntaxError, AlphaEvaluationError) as e:
            rejected.append((a["expression"], str(e)))
        except Exception as e:  # noqa: BLE001 -- never let one formula kill the whole run
            rejected.append((a["expression"], f"unexpected error: {e}"))

    print(f"Original formulas: {len(original_alphas)} total, "
          f"{len(valid_originals)} valid, {len(rejected)} rejected")
    if rejected:
        print("\nRejected originals (fix these manually, then re-run):")
        for expr, err in rejected:
            print(f"  - {expr!r}\n      -> {err}")

    existing_exprs = {a["expression"] for a in valid_originals}
    pool = []
    for a in valid_originals:
        base_rationale = a["rationale"] if "rationale" in a else a["rationales"][0]
        pool.append({
            "theme": a["theme"], "expression": a["expression"],
            "rationales": paraphrase_rationale(base_rationale),
            "source": "original",
        })

    # Pass 2: generate + validate perturbation variants, same defensive handling
    n_generated, n_valid = 0, 0
    for a in valid_originals:
        base_rationale = a["rationale"] if "rationale" in a else a["rationales"][0]
        try:
            candidate_variants = generate_variant_strings(a["expression"])
        except Exception as e:  # noqa: BLE001
            print(f"  - variant generation failed for {a['expression']!r}: {e}")
            continue
        for variant_expr in candidate_variants:
            n_generated += 1
            if variant_expr in existing_exprs:
                continue
            if not validate_expression(variant_expr, panel):
                continue
            n_valid += 1
            existing_exprs.add(variant_expr)
            pool.append({
                "theme": a["theme"], "expression": variant_expr,
                "rationales": paraphrase_rationale(f"{base_rationale} (parameter variant)"),
                "source": "augmented",
            })

    print(f"\nPerturbation candidates generated: {n_generated}")
    print(f"Passed DSL validation: {n_valid}")
    print(f"Final pool size: {len(pool)} (from {len(valid_originals)}/{len(original_alphas)} usable originals)")
    return pool


# ---------------------------------------------------------------------------
# Write back to sft/worldquant_alphas.py, with a safety check: write to a
# temp path, re-validate every entry by re-importing it, only then overwrite
# the real file.
# ---------------------------------------------------------------------------

def _format_entry(a: dict) -> str:
    rationales_str = ",\n".join(f"        {r!r}" for r in a["rationales"])
    return (
        "    {\n"
        f'        "theme": {a["theme"]!r},\n'
        f'        "expression": {a["expression"]!r},\n'
        '        "rationales": [\n'
        f"{rationales_str}\n"
        "        ],\n"
        f'        "source": {a["source"]!r},\n'
        "    }"
    )


def write_worldquant_alphas(pool: list[dict], path: str) -> None:
    header = (
        '"""\n'
        "Alpha expressions for SFT. Originals are hand-curated (WorldQuant-inspired);\n"
        '"augmented" entries were generated by sft/augment.py via parametric\n'
        "perturbation and validated against the real DSL evaluator -- every\n"
        "expression here is guaranteed to parse and run without error.\n"
        '"""\n\n'
    )
    body = ",\n".join(_format_entry(a) for a in pool)
    content = f"{header}WORLDQUANT_INSPIRED_ALPHAS = [\n{body},\n]\n\nTHEMES = sorted(set(a['theme'] for a in WORLDQUANT_INSPIRED_ALPHAS))\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    import importlib
    import sft.worldquant_alphas as wq_module

    original = wq_module.WORLDQUANT_INSPIRED_ALPHAS
    pool = build_augmented_pool(original, seed=0)

    tmp_path = "/tmp/worldquant_alphas_new.py"
    write_worldquant_alphas(pool, tmp_path)

    # safety re-check: import the freshly written file from a temp module and
    # re-validate every single expression before touching the real file
    import importlib.util
    spec = importlib.util.spec_from_file_location("wq_candidate", tmp_path)
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)

    panel = generate_synthetic_data([f"T{i:02d}" for i in range(20)], n_days=120, seed=0)
    all_ok = True
    for a in candidate.WORLDQUANT_INSPIRED_ALPHAS:
        if not validate_expression(a["expression"], panel):
            print(f"POST-WRITE VALIDATION FAILED for: {a['expression']}")
            all_ok = False

    if all_ok:
        real_path = "sft/worldquant_alphas.py"
        write_worldquant_alphas(pool, real_path)
        print(f"\nWrote {len(pool)} validated entries to {real_path}")
    else:
        print("\nABORTED: not overwriting sft/worldquant_alphas.py due to validation failures above.")