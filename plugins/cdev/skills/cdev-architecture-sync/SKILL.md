---
name: cdev-architecture-sync
description: "Bring ARCHITECTURE.md back in line with the code. Use when doc_check reports drift, a new code folder appears, a folder is removed, a folder's files, flows, responsibility, or dependencies change, or the user asks to update the architecture documents."
---

# cdev-architecture-sync

The architecture documents are written from reading the code, so they drift when the code moves. This skill rereads what changed and rewrites only what is out of date, leaving what a person wrote alone where it still holds.

The folder template is [ARCHITECTURE.folder.md](../cdev-init/templates/ARCHITECTURE.folder.md).

## Process

### 1. Find the drift

```bash
py -3 tools/doc_check.py
```

It lists files missing from or added to each `## Files`, and folder documents the root map does not link. Then list the code folders two levels deep and compare them with the map in the root ARCHITECTURE.md. For folders that exist in both, compare each folder's `## Depends on` with what its code now includes or imports, and each step of `## Flows` with the functions it names.

**Done when:** you have a list of folders that are new, removed, or whose files, flows, or dependencies changed, each with the file, include, or function that shows it.

### 2. Rewrite what drifted

- **A new folder**: read its code and write its ARCHITECTURE.md from the folder template.
- **A removed folder**: remove it from the root map.
- **A changed folder**: update `## Files`, `## Flows`, and `## Depends on`, and `## Responsibility` or `## Entry points` only where the code no longer matches them. Read the functions a flow passes through before rewriting it. Keep sentences a person wrote when they are still true.

**Done when:** every folder on your list has been handled, `doc_check` reports no drift, and every `## Responsibility` you wrote describes what the folder does rather than how many files it has.

### 3. Update the root map

Rewrite the table in the root ARCHITECTURE.md so every code folder appears once, with its role and what it depends on.

**Done when:** every code folder two levels deep has a document, and the root map lists each one.

### 4. Show the difference

Show the user `git diff -- '*ARCHITECTURE.md'`, and point out any new dependency that looks like a layer being crossed.

**Done when:** the user has seen the difference, including every new dependency you flagged.
