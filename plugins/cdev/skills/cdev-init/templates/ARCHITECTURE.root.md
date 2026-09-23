# Architecture

## Map

{{MODULES}}

## How to read this

Each folder in the map has its own ARCHITECTURE.md next to its code: its responsibility, a line per file, the flows that run through it, its entry points, what it depends on, and the notes that matter for its domain. Use them to find the code, then read the code.

When a folder appears, disappears, or starts depending on something new, run cdev-architecture-sync so this map and the folder's document stay true. `py -3 tools/doc_check.py` reports where they have already drifted.

## Decisions and why

Record a decision when the next reader would otherwise undo it.

| Date | Decision | Reason |
|---|---|---|
| | | |

## Terms

A term belongs here once it has been misread: a word this project uses differently from the datasheet, an abbreviation with two meanings in the tree, or a name whose scope is narrower than it sounds. A term anyone would read correctly does not.

| Term | What it means here |
|---|---|
| | |
