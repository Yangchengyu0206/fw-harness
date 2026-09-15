import pytest

from helpers import PY, fake_config, make_fixture_repo
from size_check import evaluate, parse_berkeley
from steps import STEPS, step_arch, step_build, step_size, step_test, step_tickets

BERKELEY = ("   text\t   data\t    bss\t    dec\t    hex\tfilename\n"
            "  12000\t    400\t   2000\t  14400\t   3840\tbuild/target/firmware.elf\n")


@pytest.fixture
def fw(tmp_path):
    return make_fixture_repo(tmp_path / "fw")


def test_parse_berkeley():
    assert parse_berkeley(BERKELEY) == (12000, 400, 2000)
    with pytest.raises(ValueError, match="text/data/bss"):
        parse_berkeley("size: build/target/firmware.elf: No such file")


def test_evaluate_budget():
    problems, summary = evaluate(12000, 400, 2000, flash_budget=16384, ram_budget=4096)
    assert problems == [] and summary == "flash 12400/16384 B (75%), RAM 2400/4096 B (58%)"
    problems, _ = evaluate(12000, 400, 2000, flash_budget=12000, ram_budget=2000)
    assert problems == ["flash 12400 B exceeds the 12000 B budget", "RAM 2400 B exceeds the 2000 B budget"]


def test_steps_run_in_spec_order():
    assert [name for name, _ in STEPS] == ["format", "cppcheck", "arch", "tickets", "build", "test", "size"]


def test_commands_run_in_order_and_stop_at_failure(fw):
    marker = fw / "ran.txt"
    append = [PY, "-c", f"open(r'{marker}', 'a').write('x')"]
    fail = [PY, "-c", "import sys; print('undefined reference to main'); sys.exit(2)"]
    ok = step_build(fw, fake_config(build={"commands": [append, append]}))
    assert ok.passed and marker.read_text() == "xx"
    bad = step_test(fw, fake_config(test={"commands": [fail, append]}))
    assert not bad.passed and "exit 2" in bad.summary
    assert "undefined reference" in bad.output and marker.read_text() == "xx"


def test_size_step(fw):
    printer = [PY, "-c", f"print({BERKELEY!r})"]
    ok = step_size(fw, fake_config(size={"command": printer, "flash_budget": 16384, "ram_budget": 4096}))
    assert ok.passed and ok.summary.startswith("flash 12400/16384 B")
    over = step_size(fw, fake_config(size={"command": printer, "flash_budget": 1000, "ram_budget": 4096}))
    assert not over.passed and "exceeds" in over.summary
    garbage = step_size(fw, fake_config(size={"command": [PY, "-c", "print('nothing')"], "flash_budget": 1, "ram_budget": 1}))
    assert not garbage.passed and "text/data/bss" in garbage.summary


def test_arch_and_tickets_steps(fw):
    assert step_arch(fw, fake_config()).passed
    assert step_tickets(fw, fake_config()).passed
    (fw / "harness" / "tickets" / "FW-0001.json").write_text("{", encoding="utf-8")
    result = step_tickets(fw, fake_config())
    assert not result.passed and "FW-0001.json" in result.output
    (fw / "harness" / "architecture.json").write_text("{", encoding="utf-8")
    assert not step_arch(fw, fake_config()).passed
