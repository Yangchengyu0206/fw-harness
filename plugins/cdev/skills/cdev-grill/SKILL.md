---
name: "cdev-grill"
description: "Interview the user about a plan, a port, or a decision until the assumptions behind it are on the table, then record what was decided and why."
disable-model-invocation: true
---

# cdev-grill

The design-tree interview is adapted from `skills/productivity/grilling` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), pointed at the decisions that go wrong in C and firmware work.

The expensive mistakes here are decided before any code is written: a timing copied from the previous chip, a module switched off with nobody left to remember, a sequence taken from an application note written for a different part. None of them look wrong in the diff. They show up on the board, days later.

You ask. The user decides. Write no code during this skill.

## Process

### 1. Map the decision tree

Take what the user brought and split it into the decisions it rests on. Every decision branches into the ones that hang off it.

The **frontier** is every decision whose prerequisites are already settled: the ones you can ask about now without guessing at answers you have not heard.

**Done when:** you can name the decisions on the frontier and, for each, what it depends on.

### 2. Find the facts yourself

Facts are your job, never the user's. Before a round, gather what the frontier needs:

- the repository: the architecture documents, then the code
- a question that means reading several files: the `cdev-explorer` agent, so this conversation keeps room
- another branch, a datasheet, an application note: the tools this session holds, following `## When this repository cannot answer` in AGENTS.md
- what the project already decided: `## Decisions and why` in the root ARCHITECTURE.md, and `## Log` in PROGRESS.md

A search still running is an unsettled prerequisite: ask the rest of the frontier now, and keep the questions that depend on it for a later round.

**Done when:** every frontier question is about a decision the user has to make, rather than a fact you could have looked up.

### 3. Ask a round

Ask the whole frontier in one message. Number each question, and give your own recommended answer so the user has something to push against:

```
❓ **Q1** - **<question title>**: <the question, with the options when there are some>

➡️ <your recommended answer, and what it rests on>

---

❓ **Q2** - **<question title>**: <the question>

➡️ <your recommended answer, and what it rests on>
```

Then wait. These are the questions worth asking in this domain:

- **Where did this come from?** A datasheet for this part, an application note for this part, the previous chip, or someone's memory. Name the source, and its revision when it has one.
- **What makes the two parts the same here?** A value carried over from another chip needs the sentence that says it still holds: same clock tree, same flash controller, same pin multiplexing.
- **What breaks if this is wrong, and how would you see it?** A wrong value that reads as a slightly slow response is expensive. Name the symptom, and where it would show.
- **What is the cheapest check before the full change?** One register read, one scope capture, one build with a smaller step. A check that costs an hour beats a rework that costs a week.
- **What is being deferred, and who remembers?** A module switched off, a limit hardcoded, a case not handled: each becomes a feature in the list or a line in the decisions table, or it is forgotten.
- **What happens on the real board?** Interrupts, resets, power states, and the recovery path when an update is cut off.
- **What would have to be true for the opposite choice to win?** When the user cannot answer this, the choice is a habit rather than a decision.

**Done when:** the user has answered the round, or has said which questions do not matter here.

### 4. Recompute and repeat

Their answers settle decisions and push the frontier outward. Ask the next round. A question whose answer depends on another still open belongs to a later round.

**Done when:** the frontier is empty: every branch visited, nothing left silently assumed.

### 5. Record what was decided

For each decision the user made, add a row to `## Decisions and why` in the root ARCHITECTURE.md: the date, the decision, and the reason, written so the next reader does not undo it by accident. An assumption that is still unverified goes in as an assumption, with the check that would settle it.

Work that came out of the interview becomes features:

```bash
py -3 tools/feature.py add --title "..." --behavior "..."
```

**Done when:** every decision is in the table with its reason, every deferred item is a feature or a row, and the user has seen the list.
