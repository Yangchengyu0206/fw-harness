# fw-architecture-sync

The agent reaches this one on its own.

## What it does

Scans the tree for folders of C sources, classifies each as owned, vendor, generated, or test, reads the includes to find the dependencies between them, and drafts `harness/architecture.json`. It then rewrites the generated block in every ARCHITECTURE.md from that file, leaving the human-written sections alone.

## When to reach for it

When `arch_check` fails, when a new folder of C sources appears, or when a generated block and the json have drifted apart.

## Common questions

**Why does a person still have to approve?** The scan sees what the code does today, including the dependencies nobody wanted. The json is what the code is allowed to do, which is a decision.

**Why can the grandfather list only shrink?** It is a record of debt. Growing it quietly turns a gate into a formality, so the gate compares the list against `origin/main` and fails on a new entry.

**Will it overwrite my architecture file?** Not when it already holds approved rules. The draft goes to `harness/architecture.json.harness-proposed` and you carry over what you want.

## It is working if

`arch_check` passes, and every rule in the json is one a person agreed to.
