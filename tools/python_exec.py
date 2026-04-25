from __future__ import annotations

import contextlib
import io


SAFE_GLOBALS = {
    "__builtins__": {
        "print": print,
        "range": range,
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "float": float,
        "int": int,
        "str": str,
        "list": list,
        "dict": dict,
    }
}


def run_python_snippet(code: str) -> str:
    """Run a short Python snippet in a restricted global scope."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        local_vars = {}
        exec(code, SAFE_GLOBALS, local_vars)
    output = buffer.getvalue().strip()
    return output or "执行完成（无输出）。"
