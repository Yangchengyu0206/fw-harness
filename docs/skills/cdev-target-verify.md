# cdev-target-verify

User-invoked. Type `/cdev-target-verify`.

## What it does

Walks one verification step that needs real hardware or a real operating system: gives the commands for flashing a board, loading a Linux driver, or installing a Windows driver, keeps the capture under `docs/evidence/`, and records the result on the feature.

## When to reach for it

When a feature's verification list has a step only the target can prove.

## Common questions

**Who runs the target?** You do. The skill supplies commands and keeps the evidence; it never claims a result it did not see in the log.

**Where does the log go?** `docs/evidence/F-NNN/<step>-<date>.log`, committed with the code, so the proof is still there months later.

**Why test Windows drivers on a separate machine?** Test signing and a driver under development can leave a machine unbootable. Use one you can afford to lose.

## It is working if

The feature's notes point at a log you can open, and the log contains the lines that show the behaviour.
