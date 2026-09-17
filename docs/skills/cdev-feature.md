# cdev-feature

The agent reaches this one on its own.

## What it does

Adds, updates, and lists the features in `feature_list.json` through `tools/feature.py`, and keeps each feature's behaviour, verification steps, and next step written so they can be acted on.

## When to reach for it

Whenever what is being built changes: a new feature, a status change, a blocker, a verification step that turned out to be needed.

## Common questions

**Why does a script guard a JSON file?** An agent editing JSON by hand eventually leaves a trailing comma or a half-written entry, and then every other skill fails to read the list. The script validates before every write, so a bad edit never lands.

**Why are status changes not restricted?** One developer does not need a state machine to protect them from themselves. The list records where things stand.

**Must every feature list verification steps?** No. `verification` is optional and usually empty for algorithm work, where running the code is the proof. Add an entry for a check that will not happen on its own, such as one on real hardware.

**What makes a good `behavior`?** Something you could observe: "receives 4 KB at 115200 baud without dropping a byte", not "add DMA support".

## It is working if

`py -3 tools/feature.py check` passes, and every active feature has a next step you could start on without rereading the conversation.
