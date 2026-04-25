from __future__ import annotations

from typing import Dict


def run_sympy_check(expression: str, symbol: str = "x") -> str:
    """Evaluate a symbolic expression and return key diagnostics."""
    try:
        import sympy as sp
    except ImportError as exc:
        raise RuntimeError("Package 'sympy' is required. Install dependencies first.") from exc

    x = sp.symbols(symbol)
    expr = sp.sympify(expression)

    diagnostics: Dict[str, str] = {
        "expr": str(expr),
        "simplified": str(sp.simplify(expr)),
        "derivative": str(sp.diff(expr, x)),
    }
    return "\n".join(f"{k}: {v}" for k, v in diagnostics.items())
