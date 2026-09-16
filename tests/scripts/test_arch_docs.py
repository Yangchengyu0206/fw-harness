from arch_docs import (BEGIN, END, apply_block, block_of, new_document, new_root_document,
                       render_block, render_root, summary_for)
from jsonio import write_text_atomic

ARCH = {
    "version": 1,
    "include_dirs": ["src/app"],
    "modules": {
        "src/app": {"kind": "owned", "allowed_deps": ["src/hal"]},
        "src/hal": {"kind": "owned", "allowed_deps": []},
        "third_party/cmsis": {"kind": "vendor", "allowed_deps": []},
    },
    "grandfathered": ["src/hal -> src/app"],
}


def test_render_block_lists_kind_and_approved_dependencies():
    block = render_block("src/app", ARCH)
    assert block.startswith(BEGIN) and block.endswith(END)
    assert "- Kind: owned" in block
    assert "- Approved dependencies: src/hal" in block
    assert "Grandfathered" not in block


def test_render_block_marks_vendor_read_only_and_names_grandfathered_edges():
    assert "Read-only" in render_block("third_party/cmsis", ARCH)
    assert "- Approved dependencies: none" in render_block("src/hal", ARCH)
    assert "Grandfathered dependencies (remove them, do not add more): src/app" in render_block("src/hal", ARCH)


def test_render_root_tabulates_every_module():
    root = render_root(ARCH)
    assert "| src/app | owned | src/hal |" in root
    assert "- src/hal -> src/app" in root


def test_block_of_and_apply_block_round_trip():
    block = render_block("src/app", ARCH)
    document = new_document("src/app", "Holds 1 .c and 1 .h files.", block)
    assert block_of(document) == block
    changed = render_block("src/hal", ARCH)
    updated = apply_block(document, changed)
    assert block_of(updated) == changed
    assert "# src/app" in updated


def test_apply_block_appends_when_the_document_has_no_block():
    assert apply_block("# src/app\n\nHand written notes.\n", "BLOCK") == "# src/app\n\nHand written notes.\n\nBLOCK\n"
    assert block_of("# src/app\n") is None


def test_summary_for_counts_files_and_names_headers():
    summary = summary_for("src/app", ["src/app/main.c", "src/app/app_config.h"])
    assert summary == "Holds 1 .c and 1 .h files. Public headers: app_config.h."


def test_new_root_document_contains_the_block_and_human_sections():
    document = new_root_document(render_root(ARCH))
    assert document.startswith("# Repository architecture")
    assert "## How to read this map" in document and END in document


def test_write_text_atomic_uses_lf(tmp_path):
    target = tmp_path / "notes.md"
    write_text_atomic(target, "a\nb\n")
    assert target.read_bytes() == b"a\nb\n"
