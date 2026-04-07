import os
import subprocess
import tempfile
import threading
import time


EXEC_TIMEOUT = 15    # seconds before killing process
MAX_OUTPUT   = 2000  # max chars returned


def run_python(code: str, timeout: int = EXEC_TIMEOUT) -> str:
    """
    Execute Python code in a subprocess sandbox.
    Returns combined stdout + stderr, truncated to MAX_OUTPUT chars.
    """
    tmp_path = None
    try:
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".py", mode="w", encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(tmp_path)
        )

        output = ""
        if result.stdout.strip():
            output += result.stdout.strip()
        if result.stderr.strip():
            output += ("\n[stderr] " + result.stderr.strip()) if output else result.stderr.strip()

        if not output:
            output = "(no output)"

        # Truncate
        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + f"\n… (truncated, {len(output)} chars total)"

        return output

    except subprocess.TimeoutExpired:
        return f"[Timeout] Code ran for over {timeout}s and was terminated."
    except FileNotFoundError:
        return "[Error] Python interpreter not found."
    except Exception as e:
        return f"[Error] {e}"
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def run_python_async(code: str, callback=None, timeout: int = EXEC_TIMEOUT):
    """
    Run Python code in background thread.
    Calls callback(result_string) when done.
    """
    def _worker():
        result = run_python(code, timeout)
        if callback:
            callback(result)
        else:
            print(f"[code_executer] Result:\n{result}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def run_shell(command: str, timeout: int = 10) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        out = result.stdout.strip() or result.stderr.strip() or "(no output)"
        return out[:MAX_OUTPUT]
    except subprocess.TimeoutExpired:
        return f"[Timeout] Command timed out after {timeout}s"
    except Exception as e:
        return f"[Error] {e}"
