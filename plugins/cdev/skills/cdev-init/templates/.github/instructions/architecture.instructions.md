---
applyTo: "{{CODE_GLOBS}}"
---

# Keep the architecture documents true

You are working on code that an ARCHITECTURE.md describes.

- When this change adds, removes, or renames a file, update `## Files` in that folder's ARCHITECTURE.md.
- When it changes what the folder includes or calls, update `## Depends on`.
- When it changes a sequence `## Flows` describes (an init order, an interrupt path, an update procedure), update that flow.
- Write any fact you confirmed while working (an address, a timing, a call order) into `## Now` in PROGRESS.md.
- `py -3 tools/doc_check.py` lists the files the documents no longer match.
