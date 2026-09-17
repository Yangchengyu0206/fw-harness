# cdev-architecture-sync

The agent reaches this one on its own.

## What it does

Compares the code folders and their includes or imports with the architecture documents, then rewrites only what drifted: documents for new folders, removed folders taken off the map, and dependencies that changed.

## When to reach for it

When a folder appears or disappears, when a folder starts depending on something new, or when the documents no longer describe the code.

## Common questions

**Will it overwrite what I wrote?** It keeps sentences that are still true and changes only the parts the code contradicts.

**Why does it flag new dependencies?** A new include across layers is cheap to add and expensive to undo. Seeing it in the diff is the moment to decide whether it should exist.

## It is working if

Every code folder has a document, the root map lists every folder, and the dependencies in each document match what the code includes.
