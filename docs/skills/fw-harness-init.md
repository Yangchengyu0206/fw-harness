# fw-harness-init

User-invoked. Type `/fw-harness-init`.

## What it does

Writes the harness into a firmware repository: the entry documents, the state folders, the gate scripts, the git hooks, and the settings files that point at this marketplace. It then runs the whole generation without stopping, drafting `harness/architecture.json` from the real tree, writing an ARCHITECTURE.md for every module, and running `check` once. You review the finished result in one pass and say what is wrong.

## When to reach for it

Once per repository, on a clean working tree. Every later plugin version is `fw-harness-upgrade`.

## Common questions

**Why was my file not overwritten?** Nothing the harness writes replaces an existing file. The new version lands as `<name>.harness-proposed`, and you decide what to take from it.

**Why does it ask me about the modules?** The approved layering becomes a gate that fails builds. A script can observe what the code includes today; only a person can say what it is allowed to include. It asks once, after generating everything, and you answer in a sentence: usually "looks right", or "src/hal is vendor, the rest is fine". Nothing is committed until you say so, so `git diff` shows you the real files rather than a summary of them.

**What is left for me?** The responsibility line in each ARCHITECTURE.md, the flash and RAM budgets in `harness/config.json`, and the incident table at the end of CLAUDE.md.

## It is working if

`check` runs, the architecture gate passes, and the install plus the generated documents land in one commit that starts with `harness:`.
