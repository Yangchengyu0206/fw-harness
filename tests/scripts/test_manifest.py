import manifest
from helpers import TEMPLATES


def test_every_listed_template_exists():
    for path in list(manifest.MANAGED) + list(manifest.TEAM_OWNED):
        assert (TEMPLATES / path).is_file(), path


def test_managed_files_include_every_script():
    files = manifest.managed_files(TEMPLATES)
    assert "harness/scripts/check.py" in files and "harness/scripts/install.py" not in manifest.MANAGED
    assert files == sorted(set(files))
    assert all(not path.endswith(".pyc") for path in files)


def test_generated_files_are_not_also_managed_or_team_owned():
    listed = set(manifest.MANAGED) | set(manifest.TEAM_OWNED)
    assert not listed & set(manifest.GENERATED)


def test_read_version_and_digest():
    assert manifest.read_version(TEMPLATES).count(".") == 2
    assert manifest.digest(b"abc") == manifest.digest(b"abc") != manifest.digest(b"abd")


def test_executables_are_managed():
    assert set(manifest.EXECUTABLE) <= set(manifest.MANAGED)
