---
name: cdev-implement
description: "Implement a feature in C or Python inside the structure the architecture documents describe, test first when the repository has tests, and run the change before calling it done. Use when the user asks to implement a feature, write or change a driver, module, or algorithm, add behaviour to C or Python code, or fix code so a test passes."
---

# cdev-implement

Keep each folder inside the dependencies its ARCHITECTURE.md describes, and finish with a run rather than a claim. Whether that run is a test suite or the code on a real input depends on the repository: the `Test:` line in AGENTS.md says which.

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

**Done when:** you can state the feature's `behavior` in one sentence, name which folder owns the change and what it depends on, and list its `verification` steps if it has any.

### 2. Decide how you will know it works

**When AGENTS.md has a test command**, add a test that fails for the reason the feature exists, and run it. A test that passes before the code is written proves nothing, so read the failure and confirm it is the one you intended. When the behaviour can only be observed on real hardware or a real operating system, write the host-side test for the logic you can reach, and leave the rest to `cdev-target-verify`.

**When AGENTS.md says `Test: none`**, add no test framework and no test files unless the user asks. Write down instead the input you will run the change on and the output you expect: from the feature's `behavior`, from a reference result the user has (a spreadsheet, a MATLAB or NumPy output, a worked example), or from the user when neither says. For floating point, write the tolerance too. Run the current code on that input once, so you know the starting point.

**Done when:** either a test fails and its failure names the behaviour the feature asked for, or you have shown the user the input, the expected output, and what the code prints today.

### 3. Implement

Write the smallest change that delivers the behaviour, following the rules in the domain references. Add every new source file to the build as well as to disk.

**Done when:** the new test passes, or the run on the chosen input prints the expected output, and no existing test changed its expectations to accommodate the new code.

### 4. Build, test, and run

Run the build command from AGENTS.md, the test command when there is one, and the change itself on the step 2 input. Fix what they report. A new dependency between folders that ARCHITECTURE.md does not describe is a design question, so take it to the user rather than working around it.

Any scratch script you wrote to run the change goes in a folder git ignores. When it finishes, ask the user whether to keep it in the repository as an example, or delete it.

**Done when:** the build succeeds with no new warnings, every test passes where there are tests, and you have shown the command and the output of the run.

### 5. Update the feature

```bash
py -3 tools/feature.py set F-NNN --status done --notes "checked on <input>: <result>"
```

Use `done` when the behaviour was observed and the feature has no `verification` step still owed. When a step is still owed, such as one that needs real hardware, use `--status verifying --next "<the step>"` instead.

**Done when:** the feature's status says what is left, and you have told the user about any `verification` step still owed.
