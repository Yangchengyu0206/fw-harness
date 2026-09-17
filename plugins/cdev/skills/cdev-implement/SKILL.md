---
name: cdev-implement
description: Implement a feature in C or Python, test first, inside the structure the architecture documents describe. Use when the user asks to implement a feature, write or change a driver or module, add behaviour to C or Python code, or fix code so a test passes.
---

# cdev-implement

Write the test before the code, keep each folder inside the dependencies its ARCHITECTURE.md describes, and finish with a build and a test run rather than a claim.

## Before you write

Read the `Domains:` line in AGENTS.md, then read the reference for every domain it lists. Each holds the rules to write by, and the review checklist the code will be held to:

- [c.md](references/c.md): C that runs as an ordinary process
- [firmware.md](references/firmware.md): bare-metal and RTOS code on a microcontroller
- [linux-driver.md](references/linux-driver.md): Linux kernel modules and drivers
- [windows-driver.md](references/windows-driver.md): Windows kernel-mode drivers
- [python.md](references/python.md): Python, most often the tooling around a C project

## Process

### 1. Read the feature and the folders

Read the feature with `py -3 tools/feature.py show F-NNN`, and the ARCHITECTURE.md of every folder you are about to touch.

**Done when:** you can state the feature's `behavior` in one sentence, list its `verification` steps, and name which folder owns the change and what it depends on.

### 2. Write the failing test

Add a test that fails for the reason the feature exists, and run the test command from AGENTS.md. A test that passes before the code is written proves nothing, so read the failure and confirm it is the one you intended.

When the behaviour can only be observed on real hardware or a real operating system, say so, write the host-side test for the logic you can reach, and leave the rest to `cdev-target-verify`.

**Done when:** the test run fails, and the failure names the behaviour the feature asked for.

### 3. Implement

Write the smallest change that makes the test pass, following the rules in the domain references. Add every new source file to the build as well as to disk.

**Done when:** the new test passes and no existing test changed its expectations to accommodate the new code.

### 4. Build and test

Run the build and test commands from AGENTS.md and fix what they report. A new dependency between folders that ARCHITECTURE.md does not describe is a design question, so take it to the user rather than working around it.

**Done when:** the build succeeds with no new warnings and every test passes.

### 5. Update the feature

```bash
py -3 tools/feature.py set F-NNN --status verifying --next "run the on-board loopback"
```

**Done when:** the feature's status and next step say what is left, and you have told the user which `verification` steps still need real hardware or a real operating system.
