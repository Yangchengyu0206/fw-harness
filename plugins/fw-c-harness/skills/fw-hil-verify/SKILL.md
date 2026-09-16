---
name: fw-hil-verify
description: Pay off the board verification a ticket still owes: flash it, capture the serial log, and record the evidence.
disable-model-invocation: true
---

# fw-hil-verify

A human flashes the board and watches it. This skill supplies the commands, collects the log, and records the evidence, so the ticket carries proof rather than a claim.

## Process

### 1. Read what the ticket owes

```bash
py -3 harness/scripts/ticket.py dod FW-NNNN
```

Read `verification_steps` and `dod_pending`, and pick the board step you are about to run.

**Done when:** you can state in one sentence what the board must show for this step to pass.

### 2. Give the user the commands

Take the flash and serial commands from `harness/config.json` when the team has recorded them there, and otherwise ask the user for the ones they use. Present the exact commands, the expected output, and where the log will be written:

```
harness/evidence/FW-NNNN/<step>-<date>.log
```

**Done when:** the user has the commands and has confirmed which board and which build they are running.

### 3. Capture the log

Ask the user to save the serial capture to that path, or save the output they paste. Keep the whole capture, including the timestamps and any failing lines.

**Done when:** the log file exists, and you can quote the lines in it that show the expected behaviour.

### 4. Record the evidence

```bash
py -3 harness/scripts/ticket.py evidence FW-NNNN hil --ref harness/evidence/FW-NNNN/<step>-<date>.log
```

Then remove the step you just paid off from `dod_pending`.

**Done when:** `ticket.py show FW-NNNN` lists the hil evidence, `dod_pending` no longer names this step, and you have told the user what the ticket still owes.
