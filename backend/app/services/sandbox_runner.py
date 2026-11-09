"""Child process that runs untrusted code against test cases (stdlib only).

Started by ``code_execution`` as ``python -I -S -B sandbox_runner.py`` with a JSON payload on
stdin. It must not import anything from the ``app`` package.

Layers of protection (best effort, not a hardened jail):
  1. runs in a separate process with an empty environment and a temp working directory
  2. CPU/file-size/(Linux) memory rlimits
  3. user code gets restricted builtins and an import allow-list
  4. an audit hook blocks file, network, process and similar events even if (3) is bypassed
The parent also enforces a wall-clock timeout and kills the process on expiry.
"""

import builtins
import importlib
import io
import json
import math
import os
import resource
import sys

MARKER = "@@SANDBOX_RESULT@@"
ALLOWED_MODULES = (
    "abc", "bisect", "collections", "copy", "dataclasses", "datetime", "decimal", "enum",
    "fractions", "functools", "heapq", "itertools", "math", "operator", "random", "re",
    "statistics", "string", "textwrap", "typing", "unicodedata",
)  # fmt: skip
REMOVED_BUILTINS = (
    "open", "exec", "eval", "compile", "input", "breakpoint", "exit", "quit", "help",
    "license", "credits", "copyright",
)  # fmt: skip
BLOCKED_EVENT_PREFIXES = (
    "open", "socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn",
    "os.fork", "os.forkpty", "os.kill", "os.killpg", "os.remove", "os.rename", "os.mkdir",
    "os.rmdir", "os.chmod", "os.chown", "os.link", "os.symlink", "os.truncate", "os.putenv",
    "os.listdir", "os.scandir", "os.chdir", "shutil.", "ctypes.", "pty.", "glob.", "urllib.",
    "http.", "ftplib.", "smtplib.", "webbrowser.", "tempfile.", "sqlite3.", "mmap.",
    "resource.", "sys.settrace", "sys.setprofile", "code.",
)  # fmt: skip
MAX_TEXT = 200
_real_import = builtins.__import__


class _Discard(io.TextIOBase):
    """Swallows anything the submission prints."""

    def write(self, text: str) -> int:
        return len(text)


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level != 0 or name.split(".")[0] not in ALLOWED_MODULES:
        raise ImportError(f"Importing '{name}' is not allowed in this exercise")
    return _real_import(name, globals, locals, fromlist, level)


def _audit(event: str, args: tuple) -> None:
    if event.startswith(BLOCKED_EVENT_PREFIXES):
        raise PermissionError(f"'{event}' is not allowed in this exercise")


def _apply_limits(timeout: float) -> None:
    cpu = math.ceil(timeout) + 1
    for limit, value in ((resource.RLIMIT_CPU, cpu), (resource.RLIMIT_FSIZE, 0)):
        try:
            resource.setrlimit(limit, (value, value))
        except ValueError, OSError:
            pass
    if sys.platform.startswith("linux"):
        try:
            resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
        except ValueError, OSError:
            pass


def _safe_builtins() -> dict:
    safe = {k: v for k, v in vars(builtins).items() if k not in REMOVED_BUILTINS}
    safe["__import__"] = _guarded_import
    return safe


def _short(text: str) -> str:
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + "…"


def _describe(exc: BaseException) -> str:
    return _short(f"{type(exc).__name__}: {exc}")


def _canon(value) -> str:
    return json.dumps(value, sort_keys=True)


def _run_tests(func, test_cases: list) -> list:
    outcomes = []
    for index, case in enumerate(test_cases, start=1):
        outcome = {"index": index, "passed": False, "actual": None, "error": None}
        try:
            actual = _canon(func(*case["input"]))
            outcome["actual"] = _short(actual)
            outcome["passed"] = actual == _canon(case["expected"])
        except BaseException as exc:  # noqa: BLE001  (user code can raise anything)
            outcome["error"] = _describe(exc)
        outcomes.append(outcome)
    return outcomes


def _load_submission(code: str, entry_point: str):
    """Compile and execute the submission; returns (function, error message)."""
    try:
        code_object = compile(code, "<your code>", "exec")
    except SyntaxError as exc:
        return None, f"SyntaxError: {exc.msg} (line {exc.lineno})"
    namespace = {"__builtins__": _safe_builtins(), "__name__": "__submission__"}
    sys.addaudithook(_audit)
    try:
        exec(code_object, namespace)  # noqa: S102
    except BaseException as exc:  # noqa: BLE001
        return None, f"Error while running your code: {_describe(exc)}"
    func = namespace.get(entry_point)
    if not callable(func):
        return None, f"Function '{entry_point}' was not found. Keep the given function name."
    return func, None


def main() -> None:
    """Read the payload, run the tests, and print one marked JSON line."""
    payload = json.loads(sys.stdin.read())
    out_fd = os.dup(1)
    for name in ALLOWED_MODULES:
        importlib.import_module(name)
    _apply_limits(float(payload["timeout"]))
    sys.stdout = sys.stderr = _Discard()
    func, error = _load_submission(payload["code"], payload["entry_point"])
    tests = [] if error else _run_tests(func, payload["test_cases"])
    line = MARKER + json.dumps({"error": error, "tests": tests}) + "\n"
    os.write(out_fd, line.encode())


if __name__ == "__main__":
    main()
