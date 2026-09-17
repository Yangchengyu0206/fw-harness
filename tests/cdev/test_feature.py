import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "plugins" / "cdev" / "skills" / "cdev-init" / "templates" / "tools"
sys.path.insert(0, str(TOOLS))

import feature  # noqa: E402

TODAY = "2026-09-17"


@pytest.fixture
def path(tmp_path):
    return tmp_path / "feature_list.json"


def run(path, *argv):
    return feature.main(["--file", str(path), *argv], today=TODAY)


def test_template_is_valid():
    data = json.loads((TOOLS.parent / "feature_list.json").read_text(encoding="utf-8"))
    assert feature.validate(data) == [] and data["features"] == []


def test_default_file_sits_at_the_repository_root():
    assert feature.DEFAULT_FILE == TOOLS.parent / "feature_list.json"


def test_add_creates_the_file_and_allocates_from_the_maximum(path, capsys):
    assert run(path, "add", "--title", "UART DMA receive", "--area", "drivers/uart",
               "--verify", "host test", "--verify", "board loopback") == 0
    assert run(path, "add", "--title", "SPI flash driver") == 0
    data = feature.load(path)
    data["features"] = [item for item in data["features"] if item["id"] != "F-001"]
    feature.save(path, data)
    assert run(path, "add", "--title", "Bootloader") == 0
    ids = [item["id"] for item in feature.load(path)["features"]]
    assert ids == ["F-002", "F-003"]
    assert "added F-003: Bootloader" in capsys.readouterr().out


def test_set_updates_fields_and_the_date(path):
    run(path, "add", "--title", "UART DMA receive")
    assert run(path, "set", "F-001", "--status", "active", "--next", "wire the callback",
               "--verify", "board loopback") == 0
    item = feature.find(feature.load(path), "F-001")
    assert item["status"] == "active" and item["next_step"] == "wire the callback"
    assert item["verification"] == ["board loopback"] and item["updated"] == TODAY


def test_set_requires_a_change(path, capsys):
    run(path, "add", "--title", "UART DMA receive")
    assert run(path, "set", "F-001") == 1
    assert "give at least one" in capsys.readouterr().err


def test_set_on_an_unknown_id_names_the_known_ones(path, capsys):
    run(path, "add", "--title", "UART DMA receive")
    assert run(path, "set", "F-009", "--status", "done") == 1
    assert "F-009 not found. Known ids: F-001" in capsys.readouterr().err


def test_validate_names_every_broken_field():
    data = {"version": 1, "features": [
        {"id": "F-1", "title": "", "area": "", "status": "doing", "behavior": "",
         "verification": "host", "next_step": "", "notes": "", "updated": "yesterday"},
        {"id": "F-002", "title": "a", "area": "", "status": "next", "behavior": "",
         "verification": [], "next_step": "", "notes": "", "updated": TODAY},
        {"id": "F-002", "title": "b", "area": "", "status": "next", "behavior": "",
         "verification": [], "next_step": "", "notes": "", "updated": TODAY},
    ]}
    errors = "\n".join(feature.validate(data))
    for fragment in ("id must look like F-001", "title must not be empty", "status must be one of",
                     "verification must be an array", "updated must be a date", "used more than once"):
        assert fragment in errors, fragment


def test_save_refuses_invalid_data_and_leaves_the_file_alone(path):
    run(path, "add", "--title", "UART DMA receive")
    before = path.read_bytes()
    data = feature.load(path)
    data["features"][0]["status"] = "doing"
    with pytest.raises(feature.FeatureError, match="refusing to write"):
        feature.save(path, data)
    assert path.read_bytes() == before


def test_check_exit_codes(path, capsys):
    run(path, "add", "--title", "UART DMA receive")
    assert run(path, "check") == 0
    assert "1 features, valid" in capsys.readouterr().out
    path.write_text("{", encoding="utf-8")
    assert run(path, "check") == 1
    assert "not valid JSON" in capsys.readouterr().err


def test_check_on_a_missing_file_says_how_to_fix_it(path, capsys):
    assert run(path, "check") == 1
    assert "cdev-init" in capsys.readouterr().err


def test_show_lists_and_filters(path, capsys):
    run(path, "add", "--title", "UART DMA receive", "--status", "active")
    run(path, "add", "--title", "SPI flash driver")
    capsys.readouterr()
    assert run(path, "show", "--status", "active") == 0
    out = capsys.readouterr().out
    assert "F-001" in out and "F-002" not in out
    assert run(path, "show", "F-002") == 0
    assert '"title": "SPI flash driver"' in capsys.readouterr().out


def test_writes_utf8_with_lf(path):
    title = "Temperature " + chr(0xB1) + " 0.5 " + chr(0xB0) + "C, 10 " + chr(0xB5) + "A"
    run(path, "add", "--title", title)
    raw = path.read_bytes()
    assert b"\r\n" not in raw
    assert chr(0xB1) in raw.decode("utf-8")
