---
name: cdev-feature
description: "Add, update, and list the features in feature_list.json. Use when the user asks for a new feature, asks to update, block, or finish one, asks what is left to do, mentions an F-NNN id, or when finished work changes a feature's status."
---

# cdev-feature

`feature_list.json` is the single source of truth for what is being built. `tools/feature.py` validates the file before every write, so every change goes through it and the file is never left half edited.

## Commands

```bash
py -3 tools/feature.py add --title "Median filter on the sensor stream" --area src/filter --behavior "A single-sample spike in a 5-sample window does not appear in the output"
py -3 tools/feature.py add --title "UART receives with DMA" --area drivers/uart --behavior "Receives 4 KB at 115200 baud without dropping a byte" --verify "host test: ring buffer overflow returns an error" --verify "on board: 4 KB loopback, CRC matches"
py -3 tools/feature.py set F-NNN --status active
py -3 tools/feature.py set F-NNN --status verifying --next "run the on-board loopback"
py -3 tools/feature.py set F-NNN --status blocked --notes "waiting for the new board revision"
py -3 tools/feature.py set F-NNN --verify "on board: survives 1000 resets"
py -3 tools/feature.py show
py -3 tools/feature.py show --status active
py -3 tools/feature.py show F-NNN
py -3 tools/feature.py check
```

Statuses: `backlog`, `next`, `active`, `verifying`, `done`, `blocked`. Any status can move to any other; the list records the state rather than policing it.

## How to write a feature

- **`behavior`** names what the product does differently when the feature is finished, in terms someone could observe: "Receives 4 KB at 115200 baud without dropping a byte", not "add DMA support".
- **`verification`** is optional. Leave it empty when running the code on a real input is proof enough, which is the usual case for algorithm work. Add an entry only for a check that will not happen on its own: one that needs real hardware or a real operating system, or one the user names.
- **`next_step`** is the single next action, specific enough to start without rereading the conversation.

## Moving a feature to done

Move a feature to `done` when its behaviour has been observed in a run, every entry in `verification` (if any) has been run, and the result is recorded in PROGRESS.md. When the code works but a verification entry is still owed, the feature stays `verifying` with that entry as its `next_step`.

**Done when:** the command exits zero and you have read the feature's new state back to the user.
