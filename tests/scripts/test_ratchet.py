from helpers import add_origin, commit_all
from ratchet import BASE_REF, baseline_ref, baseline_text, new_entries, parse_entries


def test_parse_entries_skips_blank_lines_and_comments():
    text = "# header\n\nuninitvar:src/a.c\n  nullPointer:src/b.c  \n"
    assert parse_entries(text) == {"uninitvar:src/a.c", "nullPointer:src/b.c"}


def test_new_entries():
    assert new_entries({"a", "b"}, {"a"}) == ["b"]
    assert new_entries({"a"}, {"a", "b"}) == []
    assert new_entries({"a"}, None) == []


def test_baseline_falls_back_to_head_with_warning(repo):
    ref, warning = baseline_ref(repo)
    assert ref == "HEAD" and f"{BASE_REF} not found" in warning


def test_baseline_uses_origin_main(repo, tmp_path):
    add_origin(repo, tmp_path)
    assert baseline_ref(repo) == (BASE_REF, None)


def test_baseline_text(repo):
    (repo / "harness" / "list.txt").write_text("a\n", encoding="utf-8")
    commit_all(repo, "harness: list")
    assert baseline_text(repo, "HEAD", "harness/list.txt") == "a"
    assert baseline_text(repo, "HEAD", "harness/missing.txt") is None
