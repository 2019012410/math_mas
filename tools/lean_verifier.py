from __future__ import annotations

import os
import subprocess
import tempfile


def verify_lean(lean_code: str, timeout: int = 30) -> str:
    """Verify Lean code by compiling a temporary file with Mathlib import."""
    lean_bin = os.getenv("LEAN_BIN", "lean")
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "Test.lean")
        with open(filepath, "w", encoding="utf-8") as handle:
            handle.write("import Mathlib\n\n")
            handle.write(lean_code)

        try:
            completed = subprocess.run(
                [lean_bin, filepath],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = completed.stdout.strip() or "Lean 验证通过"
            return output
        except subprocess.CalledProcessError as err:
            return f"Lean 编译错误:\n{err.stderr.strip()}"
        except FileNotFoundError:
            return "未找到 Lean 可执行文件。请安装 Lean 或设置 LEAN_BIN。"
        except subprocess.TimeoutExpired:
            return f"Lean 验证超时（>{timeout}s）。"
