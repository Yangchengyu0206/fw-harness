import sys

import pytest

from helpers import PY, add_origin, commit_all, fake_config, make_fixture_repo
from steps import StepResult, changed_files, expand_argv, run_command, step_cppcheck, step_format

FAIL_IF_ARGS = [PY, "-c", "import sys; print(' '.join(sys.argv[1:])); sys.exit(1 if len(sys.argv) > 1 else 0)"]


@pytest.fixture
def fw(tmp_path):
    return make_fixture_repo(tmp_path / "fw")


def test_expand_argv_replaces_python_placeholder():
    assert expand_argv(["{python}", "-c", "pass"]) == [sys.executable, "-c", "pass"]


def test_run_command_reports_missing_tool(fw):
    proc, problem = run_command(fw, ["definitely-not-a-real-tool-xyz", "--version"])
    assert proc is None and "definitely-not-a-real-tool-xyz not found on PATH" in problem


def test_changed_files_include_modified_and_untracked_only(fw):
    assert changed_files(fw, [".c", ".h"]) == []
    (fw / "src" / "app" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    (fw / "src" / "app" / "extra.h").write_text("#define EXTRA 1\n", encoding="utf-8")
    (fw / "src" / "app" / "notes.txt").write_text("x\n", encoding="utf-8")
    assert changed_files(fw, [".c", ".h"]) == ["src/app/extra.h", "src/app/main.c"]


def test_changed_files_since_merge_base_with_origin(fw, tmp_path):
    add_origin(fw, tmp_path)
    (fw / "src" / "drivers" / "uart.c").write_text("int uart_init(void) { return 1; }\n", encoding="utf-8")
    commit_all(fw, "FW-0001 change uart")
    assert changed_files(fw, [".c"]) == ["src/drivers/uart.c"]


def test_format_passes_when_nothing_changed(fw):
    result = step_format(fw, fake_config(format={"command": FAIL_IF_ARGS, "extensions": [".c", ".h"]}))
    assert result == StepResult("format", True, "no changed C sources to check")


def test_format_checks_changed_files_but_skips_vendor(fw):
    config = fake_config(format={"command": FAIL_IF_ARGS, "extensions": [".c", ".h"]})
    (fw / "third_party" / "cmsis" / "Include" / "core_cm4.h").write_text("/* vendor update */\n", encoding="utf-8")
    assert step_format(fw, config).passed
    (fw / "src" / "app" / "main.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    result = step_format(fw, config)
    assert not result.passed
    assert "src/app/main.c" in result.output and "core_cm4.h" not in result.output


def test_cppcheck_runs_with_suppressions_list_and_paths(fw):
    echo = [PY, "-c", "import sys; print(' '.join(sys.argv[1:]))"]
    result = step_cppcheck(fw, fake_config(cppcheck={"command": echo, "paths": ["src"]}))
    assert result.passed
    assert "--suppressions-list=harness/cppcheck-suppressions.txt src" in result.output


def test_cppcheck_failure(fw):
    fail = [PY, "-c", "import sys; print('src/app/main.c:3: error: nullPointer'); sys.exit(1)"]
    result = step_cppcheck(fw, fake_config(cppcheck={"command": fail, "paths": ["src"]}))
    assert not result.passed and "nullPointer" in result.output


def test_cppcheck_suppression_ratchet(fw):
    path = fw / "harness" / "cppcheck-suppressions.txt"
    path.write_text(path.read_text(encoding="utf-8") + "nullPointer:src/app/main.c\n", encoding="utf-8")
    result = step_cppcheck(fw, fake_config())
    assert not result.passed
    assert "may only shrink" in result.summary and "nullPointer:src/app/main.c" in result.summary
