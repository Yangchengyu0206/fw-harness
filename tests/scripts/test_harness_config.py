import json

import pytest

from harness_config import ConfigError, load_config, validate_config
from helpers import TEMPLATES, fake_config


def test_template_config_is_valid():
    config = json.loads((TEMPLATES / "harness" / "config.json").read_text(encoding="utf-8"))
    assert validate_config(config) == []


def test_fake_config_is_valid():
    assert validate_config(fake_config()) == []


@pytest.mark.parametrize("mutate, fragment", [
    (lambda c: c.update(language="fr"), "language"),
    (lambda c: c.update(required_tools="cmake"), "required_tools"),
    (lambda c: c["check"].pop("build"), "check.build"),
    (lambda c: c["check"]["format"].update(command=[]), "check.format.command"),
    (lambda c: c["check"]["format"].update(extensions=["c"]), "check.format.extensions"),
    (lambda c: c["check"]["cppcheck"].update(paths=[]), "check.cppcheck.paths"),
    (lambda c: c["check"]["test"].update(commands=[["ctest"], []]), "check.test.commands"),
    (lambda c: c["check"]["size"].update(flash_budget=0), "check.size.flash_budget"),
])
def test_invalid_configs(mutate, fragment):
    config = fake_config()
    mutate(config)
    errors = validate_config(config)
    assert any(fragment in e for e in errors), errors


def test_load_config_missing(repo):
    with pytest.raises(ConfigError, match="fw-harness-init"):
        load_config(repo)


def test_load_config_lists_every_problem(repo):
    config = fake_config()
    config["language"] = "fr"
    config["check"]["size"]["ram_budget"] = -1
    (repo / "harness" / "config.json").write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ConfigError) as exc:
        load_config(repo)
    assert "language" in str(exc.value) and "ram_budget" in str(exc.value)


def test_load_config_broken_json(repo):
    (repo / "harness" / "config.json").write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid JSON"):
        load_config(repo)


def test_architecture_section_is_optional_and_validated():
    config = fake_config()
    assert validate_config(config) == []
    config["architecture"] = {"max_depth": 2, "vendor_patterns": []}
    assert validate_config(config) == []
    config["architecture"] = {"max_depth": 0, "vendor_patterns": "third_party"}
    errors = validate_config(config)
    assert any("architecture.max_depth" in error for error in errors)
    assert any("architecture.vendor_patterns" in error for error in errors)
