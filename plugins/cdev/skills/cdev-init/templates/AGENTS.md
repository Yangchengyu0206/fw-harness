# {{PROJECT}}

Entry point for any agent working in this repository. Read this file first, then [CLAUDE.md](CLAUDE.md).

## Domains

Domains: {{DOMAINS}}

The cdev skills read the matching domain reference for each domain listed here before they write, review, or debug code. Change this line when the repository gains or loses a domain.

## Where to work

Editable:

{{EDITABLE}}

Read-only (vendor or generated; upgrade from the source instead of editing here):

{{READ_ONLY}}

Every code folder has an ARCHITECTURE.md. Read the one next to the code before changing that code.

## Guardrails

Ask before any of these:

- `git clean`, `git push`, force pushes, and rewriting history
- deleting a file the current task did not create
- editing a read-only folder
- changing compiler flags, linker scripts, or build configuration the task did not ask about

## The loop

1. Read `## Now` in PROGRESS.md and run `py -3 tools/feature.py show`.
2. Work on one feature at a time.
3. Write a failing test first.
4. Build: `{{BUILD}}`
5. Test: `{{TEST}}`
6. Update the feature with `py -3 tools/feature.py set F-NNN --status verifying --next "..."`, and add an entry to PROGRESS.md.

## Windows notes

- Run Python as `py -3`. A bare `python` can be the Microsoft Store stub, which exits without running anything.
- Every file in this repository is UTF-8. Pass `encoding="utf-8"` when a script reads or writes text.
