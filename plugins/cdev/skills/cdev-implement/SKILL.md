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

Run the build command from AGENTS.md, the test command when there is one, and the change itself on the step 2 input. Fix what they report. Send long output to a file and read the errors and the tail.

When AGENTS.md says the build or the run happens outside this editor, write the checklist for the user under `Waiting on the user` in `## Now` of PROGRESS.md instead: what to build, what to flash or load, what to do, what output shows success, and what shows failure. Fix what the user reports back. A new dependency between folders that ARCHITECTURE.md does not describe is a design question, so take it to the user rather than working around it.

Any scratch script you wrote to run the change goes in a folder git ignores. When it finishes, ask the user whether to keep it in the repository as an example, or delete it.

**Done when:** the build succeeds with no new warnings, every test passes where there are tests, and you have shown the command and the output of the run; or the checklist is written and the user has it.

### 5. Update the documents and the feature

Update the ARCHITECTURE.md of every folder whose files, flows, or dependencies the change altered, and run `py -3 tools/doc_check.py`.

```bash
py -3 tools/feature.py set F-NNN --status verifying --next "<the step>" --notes "checked on <input>: <result>"
```

When the behaviour has been observed and no `verification` step is still owed, show the user the evidence and propose closing the feature with cdev-done. The feature becomes `done` on the user's confirmation.

**Done when:** `doc_check` reports no drift, the feature's status says what is left, and the user knows what is owed or has the proposal to close it.
