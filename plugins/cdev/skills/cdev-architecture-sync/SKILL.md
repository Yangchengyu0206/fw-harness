---
name: cdev-architecture-sync
description: "Bring ARCHITECTURE.md back in line with the code, and write the document for a folder that has none yet. Use when doc_check reports drift or a folder not documented yet, when work or a question first reaches such a folder, when a code folder appears or is removed, when a folder's files, flows, responsibility, or dependencies change, or when the user asks to update the architecture documents."
---

# cdev-architecture-sync

The architecture documents are written from reading the code, so they drift when the code moves. This skill rereads what changed and rewrites only what is out of date, leaving what a person wrote alone where it still holds.

`cdev-init` documents the folders the work starts in and leaves the rest as stubs, so a large repository finishes its setup in one pass. Filling one of those stubs is this skill's other job, and the cheaper way in: when the user names a folder, or work or a question first reaches one, do only step 2 for that folder and then step 3.

The templates are [ARCHITECTURE.folder.md](../cdev-init/templates/ARCHITECTURE.folder.md) and [ARCHITECTURE.stub.md](../cdev-init/templates/ARCHITECTURE.stub.md).

## Process

### 1. Find the drift

```bash
py -3 tools/doc_check.py
```

It lists files missing from or added to each `## Files`, and folder documents the root map does not link. Then list the code folders two levels deep and compare them with the map in the root ARCHITECTURE.md. For folders that exist in both, compare each folder's `## Depends on` with what its code now includes or imports, and each step of `## Flows` with the functions it names.

**Done when:** you have a list of folders that are new, removed, or whose files, flows, or dependencies changed, each with the file, include, or function that shows it.

### 2. Rewrite what drifted

- **A new folder, or one whose document says it is not documented yet**: read its code and write its ARCHITECTURE.md from the folder template. Read the whole of the files it names in `## Files` and the functions each flow passes through; leave the folders around it for when the work reaches them.
- **A removed folder**: remove it from the root map.
- **A changed folder**: update `## Files`, `## Flows`, and `## Depends on`, and `## Responsibility` or `## Entry points` only where the code no longer matches them. Read the functions a flow passes through before rewriting it. Keep sentences a person wrote when they are still true.

**Done when:** every folder on your list has been handled, `doc_check` reports no drift, and every `## Responsibility` you wrote describes what the folder does rather than how many files it has.

### 3. Update the root map

Rewrite the table in the root ARCHITECTURE.md so every code folder appears once, with its role and what it depends on.

**Done when:** every code folder two levels deep has a document, and the root map lists each one.

### 4. Show the difference

Show the user `git diff -- '*ARCHITECTURE.md'`, and point out any new dependency that looks like a layer being crossed.

**Done when:** the user has seen the difference, including every new dependency you flagged.
