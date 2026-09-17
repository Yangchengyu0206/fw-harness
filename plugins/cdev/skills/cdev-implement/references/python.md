# Python

Applies to Python in this repository, which is most often the tooling around a C project: test scripts, host tools, hardware and serial scripts, and build helpers.

## Rules

### Text and paths

- Pass `encoding="utf-8"` to every `open` and every text-mode `subprocess` call. The default encoding on Windows follows the console code page (cp950, cp1252, and others), so code that works on one machine raises `UnicodeDecodeError` on the next.
- A command line tool calls `sys.stdout.reconfigure(encoding="utf-8")` before printing, so non-ASCII output does not crash a Windows console.
- Use `pathlib.Path` for paths. Joining strings with `/` or `\\` breaks on the other platform.

### Processes and errors

- `subprocess.run([...])` with an argument list, and check `returncode` or pass `check=True`. A list needs no quoting and cannot be injected into.
- Catch the exception you expect. A bare `except:` also catches `KeyboardInterrupt` and hides the real failure.
- Raise with a message that says what failed and how to fix it.

### Structure

- Type hints on every public function.
- No mutable default arguments: `def f(items=None)`, then `items = items or []`.
- Context managers (`with`) for files, sockets, and serial ports, so they close on the error path too.

### Talking to hardware and C

- `pyserial`: set `timeout` on every port. A read with no timeout hangs for ever when the board stops answering.
- `ctypes`: declare `argtypes` and `restype` for every foreign function. Without them, pointers and 64-bit integers are truncated silently.
- Keep hardware access behind one small module, so tests can replace it.

## Review checklist

### Critical

- `shell=True` with any value that came from outside the program
- `eval`, `exec`, or `pickle.load` on data that is not trusted
- a secret, token, or password in the source
- a bare `except` that swallows a failure
- text I/O without an explicit encoding in code that runs on Windows

### Important

- new logic with no test
- a file, socket, or port left open on an error path
- I/O that can block with no timeout
- a `ctypes` call with no `argtypes` or `restype`

### Suggestion

- missing type hints on a public function
- naming, or a function doing several jobs
- `print` used for diagnostics in a tool that should log

## Debugging anchors

- **Stop at the failure**: `pytest -x --pdb`.
- **Hidden warnings and resource leaks**: `python -X dev`.
- **A crash inside a C extension or a `ctypes` call**: `python -X faulthandler`, which prints the Python stack even when the process dies in native code.
- **A hang**: `py-spy dump --pid <pid>` shows every thread's stack without stopping the process.
- **Works here, fails there**: compare `sys.version`, the encoding (`locale.getpreferredencoding()`), and the installed package versions before reading code.

## Build and test

Use the commands in AGENTS.md when the repository records them. Otherwise:

- Environment: `py -3 -m venv .venv` (Windows) or `python3 -m venv .venv`, then activate it
- Install: `pip install -e .` for a package, `pip install -r requirements.txt` otherwise
- Tests: `pytest`
- Linters: `ruff` and `mypy` only when the repository already uses them
