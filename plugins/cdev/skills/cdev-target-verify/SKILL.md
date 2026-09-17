---
name: cdev-target-verify
description: "Verify a feature on real hardware or a real operating system: flash the board or load the driver, capture the log, and record the result."
disable-model-invocation: true
---

# cdev-target-verify

Host tests prove logic. Some behaviour only shows on the target: a board, a loaded kernel driver, an installed Windows driver. You run the target; this skill supplies the commands, keeps the log, and records what it showed.

## Process

### 1. Pick the step

```bash
py -3 tools/feature.py show F-NNN
```

Pick the `verification` step you are about to run.

**Done when:** you can state in one sentence what the target must show for this step to pass.

### 2. Give the commands

Use the commands in AGENTS.md when the repository records them. Otherwise take them from the Build and test section of the domain's reference, which for each target looks like this:

- **Firmware**: flash with the project's probe tool, then capture the serial console at the project's baud rate. See [firmware.md](../cdev-implement/references/firmware.md).
- **Linux driver**: `sudo insmod <name>.ko`, exercise the device, capture `dmesg`, then `sudo rmmod <name>` and capture `dmesg` again. See [linux-driver.md](../cdev-implement/references/linux-driver.md).
- **Windows driver**: on a test machine, `pnputil /add-driver <name>.inf /install` with Driver Verifier enabled for the driver, exercise the device, and capture the trace or debugger output. See [windows-driver.md](../cdev-implement/references/windows-driver.md).

Give the exact commands, what the output should show, and where the log goes:

```
docs/evidence/F-NNN/<step>-<YYYY-MM-DD>.log
```

**Done when:** the user has the commands and has confirmed which target and which build they are running.

### 3. Capture the log

Save the whole capture to that path, including timestamps and any failing lines, or save the output the user pastes.

**Done when:** the log file exists, and you can quote the lines in it that show the expected behaviour, or the lines that show it failing.

### 4. Record the result

```bash
py -3 tools/feature.py set F-NNN --notes "on board: 4 KB loopback passed, docs/evidence/F-NNN/loopback-2026-09-17.log"
```

When every `verification` step has now run, move the feature to `done`; otherwise set `--next` to the step still owed. Add the result to today's entry in PROGRESS.md.

**Done when:** the feature's notes point at the log, its status says what is left, and you have quoted the evidence lines to the user.
