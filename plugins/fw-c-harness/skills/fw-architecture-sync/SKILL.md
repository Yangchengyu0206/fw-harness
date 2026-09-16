---
name: fw-architecture-sync
description: Refresh harness/architecture.json and the generated block in every ARCHITECTURE.md from the real directory tree. Use when arch_check fails, when a new folder of C sources appears, when a generated architecture block disagrees with the json, or when the user asks to update the architecture documents.
---

# fw-architecture-sync

`harness/architecture.json` is the single source of approved rules. Each ARCHITECTURE.md renders that json inside a marked block, and the human-written sections around the block stay untouched. This skill regenerates the block and drafts entries for what the tree has grown.

Approved rules are a human decision. This skill drafts, and a human approves.

## Process

### 1. Read the failure

Run `py -3 harness/scripts/arch_check.py` and read what it says. It names one of four situations: a folder with C sources belongs to no module, an include breaks an approved rule, a block disagrees with the json, or the grandfather list grew.

**Done when:** you can state which of the four the repository is in, quoting the line that says so.

### 2. Handle it

- **A folder belongs to no module**: run `py -3 harness/scripts/arch_sync.py scan`. In a repository whose json already holds approved rules, the draft lands at `harness/architecture.json.harness-proposed`. Compare it with the current file and carry over only the new module, with the kind and dependencies the user confirms.
- **An include breaks an approved rule**: removing the include is the fix. Propose the change that lets the module keep its layer, and reach for the grandfather list only when the user says the dependency stays.
- **A block disagrees with the json**: run `py -3 harness/scripts/arch_sync.py docs`.
- **The grandfather list grew**: the list may only shrink, so restore the removed entries or remove the new dependency. Show the user `git diff harness/architecture.json` and let them choose.

**Done when:** the situation you named in step 1 is addressed, with a human answer for every approved rule you changed.

### 3. Fill in what a script cannot

A newly created ARCHITECTURE.md carries a responsibility line written from the file listing. Replace it with the one sentence a new colleague needs, and fill in the entry points and the ISR and memory notes from the code you can read.

**Done when:** every document you created in this run has a responsibility line naming what the module does, not how many files it holds.

### 4. Verify

```bash
py -3 harness/scripts/arch_check.py
```

**Done when:** `arch_check` passes, or its remaining failure is one the user has decided to answer another way.
