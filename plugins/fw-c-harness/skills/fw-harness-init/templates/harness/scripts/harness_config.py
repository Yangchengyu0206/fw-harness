"""Load and validate harness/config.json (spec section 4.2)."""
import json
from pathlib import Path

from jsonio import read_json

CONFIG_PATH = "harness/config.json"
LANGUAGES = ("en", "zh-TW")


class ConfigError(ValueError):
    pass


def _is_argv(value):
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _is_str_list(value, allow_empty=False):
    return (isinstance(value, list) and (allow_empty or bool(value))
            and all(isinstance(item, str) and item for item in value))


def _is_positive(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_config(config):
    if not isinstance(config, dict):
        return ["config must be a JSON object"]
    errors = []
    if config.get("language") not in LANGUAGES:
        errors.append(f"language must be one of {', '.join(LANGUAGES)}")
    if not _is_str_list(config.get("required_tools"), allow_empty=True):
        errors.append("required_tools must be an array of command names")
    check = config.get("check")
    if not isinstance(check, dict):
        return errors + ["check must be an object with format, cppcheck, build, test, and size"]
    for name in ("format", "cppcheck", "build", "test", "size"):
        if not isinstance(check.get(name), dict):
            errors.append(f"check.{name} must be an object")

    fmt = check.get("format")
    if isinstance(fmt, dict):
        if not _is_argv(fmt.get("command")):
            errors.append("check.format.command must be a non-empty argv array")
        extensions = fmt.get("extensions")
        if not (_is_str_list(extensions) and all(ext.startswith(".") for ext in extensions)):
            errors.append('check.format.extensions must be an array like [".c", ".h"]')

    cppcheck = check.get("cppcheck")
    if isinstance(cppcheck, dict):
        if not _is_argv(cppcheck.get("command")):
            errors.append("check.cppcheck.command must be a non-empty argv array")
        if not _is_str_list(cppcheck.get("paths")):
            errors.append("check.cppcheck.paths must be a non-empty array of paths")

    for name in ("build", "test"):
        step = check.get(name)
        if isinstance(step, dict):
            commands = step.get("commands")
            if not (isinstance(commands, list) and commands and all(_is_argv(c) for c in commands)):
                errors.append(f"check.{name}.commands must be a non-empty array of argv arrays")

    size = check.get("size")
    if isinstance(size, dict):
        if not _is_argv(size.get("command")):
            errors.append("check.size.command must be a non-empty argv array")
        for key in ("flash_budget", "ram_budget"):
            if not _is_positive(size.get(key)):
                errors.append(f"check.size.{key} must be a positive integer (bytes)")

    architecture = config.get("architecture")
    if architecture is not None:
        if not isinstance(architecture, dict):
            errors.append("architecture must be an object")
        else:
            for key in ("max_depth", "deep_file_threshold"):
                if key in architecture and not _is_positive(architecture[key]):
                    errors.append(f"architecture.{key} must be a positive integer")
            for key in ("vendor_patterns", "test_patterns"):
                if key in architecture and not _is_str_list(architecture[key], allow_empty=True):
                    errors.append(f"architecture.{key} must be an array of folder patterns")
    return errors


def load_config(repo):
    path = Path(repo) / CONFIG_PATH
    if not path.is_file():
        raise ConfigError(f"{CONFIG_PATH} not found. Fix: run fw-harness-init to create it")
    try:
        config = read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError(f"{CONFIG_PATH} is not valid JSON ({exc}). Fix: repair it or restore it from git") from exc
    errors = validate_config(config)
    if errors:
        raise ConfigError(f"{CONFIG_PATH} is invalid:\n- " + "\n- ".join(errors))
    return config
