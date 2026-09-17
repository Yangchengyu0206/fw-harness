import datetime
import importlib.util
import subprocess
import sys

import pytest

from helpers import ROOT

COPIES = {
    "fw-c-harness": ROOT / "plugins" / "fw-c-harness" / "skills" / "fw-c-debug" / "scripts" / "hitl_loop.py",
    "cdev": ROOT / "plugins" / "cdev" / "skills" / "cdev-debug" / "scripts" / "hitl_loop.py",
}
NOW = datetime.datetime(2026, 9, 17, 10, 30, 0)


def load(path):
    spec = importlib.util.spec_from_file_location("hitl_loop", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def hitl():
    return load(COPIES["fw-c-harness"])


def scripted(*replies):
    queue = list(replies)
    return lambda prompt: queue.pop(0)


def test_both_plugins_ship_the_same_script():
    texts = {name: path.read_text(encoding="utf-8") for name, path in COPIES.items()}
    assert texts["fw-c-harness"] == texts["cdev"]


def test_the_shipped_example_steps_are_valid(hitl):
    assert hitl.validate(hitl.STEPS) == []


def test_answers_are_written_as_key_value(hitl, tmp_path):
    out = tmp_path / "evidence" / "hitl.txt"
    steps = [("do", "Press reset."), ("ask", "BANNER", "Banner? (y/n)"), ("ask", "LAST", "Last line:")]
    shown = []
    code = hitl.main(["--out", str(out)], steps, scripted("", " y ", "boot ok"), shown.append, NOW)
    assert code == 0
    assert out.read_text(encoding="utf-8") == "# captured 2026-09-17T10:30:00\nBANNER=y\nLAST=boot ok\n"
    assert any("Press reset." in line for line in shown)


def test_bad_steps_fail_before_any_prompt(hitl, capsys):
    steps = [("do", "ok"), ("ask", "lower", "q"), ("ask", "DUP", "q"), ("ask", "DUP", "q"), ("wait", "x")]
    asked = []
    code = hitl.main([], steps, lambda prompt: asked.append(prompt) or "", lambda text: None, NOW)
    assert code == 2 and asked == []
    errors = capsys.readouterr().err
    assert "UPPER_SNAKE_CASE" in errors and "used twice" in errors and "'wait'" in errors


def test_interrupted_run_writes_nothing(hitl, tmp_path):
    out = tmp_path / "hitl.txt"

    def interrupt(prompt):
        raise KeyboardInterrupt

    code = hitl.main(["--out", str(out)], [("ask", "A", "q")], interrupt, lambda text: None, NOW)
    assert code == 130 and not out.exists()


def test_script_runs_from_the_command_line(tmp_path):
    out = tmp_path / "hitl.txt"
    result = subprocess.run(
        [sys.executable, str(COPIES["cdev"]), "--out", str(out)],
        input="\n\ny\nhello\n", capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "BANNER=y\nLAST_LINE=hello\n" in out.read_text(encoding="utf-8")
