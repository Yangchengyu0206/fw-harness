# cdev: a markdown-first harness for solo C and Python development

- Date: 2026-09-17
- Author: Yang cheng
- Status: draft, under review
- Relation: a lighter sibling of the fw-c-harness plugin (`2026-09-15-fw-c-harness-plugin-design.md`). It keeps the working loop and the domain knowledge, and drops everything that exists to coordinate several people or to enforce rules mechanically.

## 1. Goals

One install gives a single developer:

1. **A context harness written into their repository**: AGENTS.md, CLAUDE.md, an ARCHITECTURE.md for the root and every code folder, a progress log, and a feature list. An agent reads these to know where it is and what to do next.
2. **Skills for the whole loop**: start a session, pick a feature, implement, review, audit test gaps, debug, verify on real hardware when there is any, and wrap up.
3. **Domain depth where it matters**: rules that general coding skills do not carry, for five domains.

Constraints:

- Works with both Claude Code and GitHub Copilot.
- One developer. No identity tracking, no ticket IDs to allocate, no merge conflict avoidance.
- Markdown first. Exactly one script ships: the one that keeps `feature_list.json` valid.
- Languages: C and Python. Nothing else in this version.
- Tests are optional. Many users write algorithms and keep no test suite. When a repository has none, `cdev-init` records `Test: none`, and no skill adds a test framework unless the user asks. The one bar every change still meets is a real run on a real input, with the command and output shown.

### Non-goals

- Verification gates: no `check`, no ratchets, no `arch_check`, no size budget enforcement, no git hooks.
- Multi-person workflow: no per-person handoff, no collision detection, no review-by-someone-else rule. Self-review is allowed.
- Upgrade tracking: no `.harness-version`, no managed versus team-owned files.
- Other languages. The structure leaves room for them (section 7), and none ship now.

## 2. Distribution

`cdev` lives next to `fw-c-harness` on `main`, and the existing marketplace lists both:

```
fw-harness/
├─ .claude-plugin/marketplace.json     lists fw-c-harness and cdev
├─ .github/plugin/marketplace.json     lists fw-c-harness and cdev
└─ plugins/
   ├─ fw-c-harness/                    the team harness, unchanged
   └─ cdev/
      ├─ .claude-plugin/plugin.json
      ├─ plugin.json
      ├─ skills/
      └─ README.md
```

A user picks one:

```
/plugin marketplace add Yangchengyu0206/fw-harness
/plugin install cdev@fw-harness
```

Each plugin stands alone. `cdev` copies nothing from `fw-c-harness` at install time and reads nothing from it at run time, so installing one never requires the other. Where the two carry similar material (the two-axis review, the debugging loop, the firmware rules), `cdev` holds its own copy adapted to one developer; keeping them aligned is a maintenance task, not a runtime dependency.

The two plugins are meant to be installed one at a time. Their skill names do not collide (`fw-` against `cdev-`), so installing both works, but they would generate different harnesses into the same repository.

The marketplace keeps the name `fw-harness`. Renaming it would break the install commands already published and the `extraKnownMarketplaces` entry that `fw-harness-init` writes into firmware repositories.

## 3. Domains

A repository belongs to **a set** of domains, not one. A firmware project with Python test tooling is `{firmware, python}`.

| Domain | Detected from | Reference file |
|---|---|---|
| `c` | `.c` / `.h` files and none of the signals below | `c.md` |
| `firmware` | a linker script (`*.ld`, `*.icf`, `*.sct`), `startup_*.s`, an `arm-none-eabi` toolchain file, vendor HAL folders | `firmware.md` |
| `linux-driver` | `obj-m` in a Makefile, `Kconfig`, `#include <linux/module.h>` | `linux-driver.md` |
| `windows-driver` | `.inf`, `.vcxproj` with a driver target, `#include <wdf.h>` or `<ntddk.h>` | `windows-driver.md` |
| `python` | `pyproject.toml`, `setup.py`, `requirements*.txt`, or `.py` files | `python.md` |

`cdev-init` detects the set, and the user confirms it in the same single review as everything else (section 5). The confirmed set is written into AGENTS.md, which is how every later skill knows which reference files apply.

## 4. What lands in the repository

```
<repo>/
├─ AGENTS.md            entry point: where to work, guardrails, the loop, active domains
├─ CLAUDE.md            handbook: working rules per domain, what "done" means, decisions and why
├─ ARCHITECTURE.md      map of the repository
├─ <code folder>/ARCHITECTURE.md
├─ PROGRESS.md          top: where I am and the next step; below: dated session log
├─ feature_list.json    the feature list, the single source of truth
├─ tools/feature.py     keeps feature_list.json valid
└─ docs/reviews/        review reports, one per review
```

An existing file is never overwritten. The new version is written as `<name>.cdev-proposed` and the user is told.

### 4.1 feature_list.json

```json
{
  "version": 1,
  "features": [
    {
      "id": "F-003",
      "title": "UART receives with DMA",
      "area": "drivers/uart",
      "status": "active",
      "behavior": "Receives 4 KB at 115200 baud without dropping a byte",
      "verification": ["host test: ring buffer overflow returns an error", "on board: 4 KB loopback, CRC matches"],
      "next_step": "wire the DMA half-transfer callback",
      "notes": "",
      "updated": "2026-09-17"
    }
  ]
}
```

- `status` is one of `backlog`, `next`, `active`, `verifying`, `done`, `blocked`. Transitions are not enforced; one developer does not need a state machine to protect them from themselves.
- `id` is `F-` plus a zero-padded number, allocated as the maximum plus one.

### 4.2 tools/feature.py

Standard library only, Python 3.9+, UTF-8 with LF, written through a temporary file and a rename.

```
py -3 tools/feature.py add --title "..." [--area ...] [--behavior "..."] [--verify "..."]
py -3 tools/feature.py set F-003 [--status active] [--next "..."] [--notes "..."]
py -3 tools/feature.py show [F-003]
py -3 tools/feature.py check
```

`check` validates the schema and exits non-zero with the field and the fix. Every other command runs `check` on the result before writing, so a bad edit never lands.

## 5. cdev-init: generate everything, then one review

1. Confirm the repository root and that the working tree is clean.
2. Detect the domain set and scan the code folders. Default depth is two levels; vendor and generated folders are recognised by name and by generated markers in file headers, and are marked read-only.
3. Write every file in section 4, with no questions in between. ARCHITECTURE.md contents come from reading the code: responsibility, entry points, what the folder includes from elsewhere, and, for firmware and drivers, interrupt and memory notes.
4. Hand over the whole result once: the domain set, a table of folders with their inferred role and dependencies, and every `.cdev-proposed` file. Ask one question: what is wrong? Apply the corrections, then show the difference.
5. Commit after the user says to.

## 6. Skills (11)

| Skill | Invocation | Purpose |
|---|---|---|
| `cdev-init` | user | Section 5 |
| `cdev-session-start` | user | Read AGENTS.md, the top of PROGRESS.md, and `feature_list.json`; propose the feature to work on; confirm it with the user before writing code |
| `cdev-feature` | model | Add, update, and show features through `tools/feature.py` |
| `cdev-architecture-sync` | model | Rewrite ARCHITECTURE.md for folders that changed or appeared |
| `cdev-implement` | model | A failing test first when the repository has tests, otherwise a chosen input and expected output; then implement, build, and run |
| `cdev-review` | model | Two axes, Standards and Spec, each in its own sub-agent; report into `docs/reviews/`. Self-review is allowed |
| `cdev-test-gap` | model | Read-only audit of untested behaviour, P0 to P3 |
| `cdev-debug` | model | Build a loop that shows the defect, shrink it, rank and prove hypotheses, lock the fix down with a test or a kept script, clean up |
| `cdev-target-verify` | user | Verification on real hardware or a real OS: flash or load the driver, capture the log, note it on the feature |
| `cdev-done` | user | Update PROGRESS.md and the feature, draft the commit message |
| `cdev-guide` | user | Router over the other ten |

Authoring conventions carry over unchanged from the fw-c-harness spec, section 3.4: deliberate invocation choice, short SKILL.md with disclosed reference, a completion criterion on every step, positive phrasing, a single source of truth, no em-dashes.

## 7. Domain references

Reference files live once, inside the plugin at `skills/cdev-implement/references/<domain>.md`. `cdev-implement`, `cdev-review`, and `cdev-debug` read only the files for the repository's active domains.

Each file holds the same four sections, so adding a language later means adding one file and one detection rule:

1. **Rules**: what to write.
2. **Review checklist**: critical, important, and suggestion items for this domain, used by `cdev-review`.
3. **Debugging anchors**: the failure modes worth ruling out first.
4. **Build and test**: the usual commands, for when the project has not written its own into AGENTS.md.

What each carries:

- `c.md`: ownership of every allocation, bounds on every buffer and string operation, error returns checked, undefined behaviour to avoid, sanitizers for debugging.
- `firmware.md`: `volatile` and shared state with interrupts, critical sections, static allocation and stack bounds, flash and RAM budget, HardFault decoding, MISRA C:2012 as an advisory reference, and how to record a deviation.
- `linux-driver.md`: atomic versus process context and what may sleep, `GFP_KERNEL` versus `GFP_ATOMIC`, `copy_from_user` and `copy_to_user`, spinlock versus mutex, reference counting and teardown order, kernel coding style, `dmesg`, KASAN and lockdep.
- `windows-driver.md`: IRQL and what each level permits, paged versus non-paged pool, KMDF object lifetime and parenting, request completion rules, Driver Verifier, WinDbg and `!analyze`.
- `python.md`: UTF-8 handling on Windows consoles, `pathlib`, `subprocess` with argument lists, no bare `except`, type hints, pytest, virtual environments, and C interop through `ctypes` and `pyserial` for hardware tooling.

## 8. Testing the plugin

- `tools/feature.py` is tested with pytest: allocation, every command, schema errors, atomic write, UTF-8.
- The plugin tests carry over from fw-c-harness and are re-pointed at the `cdev-` skills: frontmatter, invocation, relative links, no em-dashes, both manifests, one page per skill, and every documented `feature.py` command parsed by the real CLI parser.
- A manual checklist runs init once per domain on a scratch repository, in both tools.

## 9. Open questions

1. **The name when Python stands alone.** `cdev` assumes Python here is tooling around C projects. If standalone Python projects are in scope, the prefix should change before anything is published.
2. **Translation.** The Traditional Chinese version of this spec is written after the English content is approved, so it is translated once.

## 10. Revision: GitHub Copilot first (2026-09-17)

Field use on a firmware repository showed three gaps: answers about architecture and flows still meant reading the code from scratch, long conversations lost what they had found when the context was summarised, and build and flashing happen in a vendor IDE the agent cannot drive. GitHub Copilot in VS Code is now the primary target; Claude Code stays supported through a CLAUDE.md that only imports AGENTS.md.

Changes:

1. **One rules file.** Copilot loads AGENTS.md on its own and not CLAUDE.md, so every rule moves into AGENTS.md. CLAUDE.md is `@AGENTS.md`. The decisions table moves to the root ARCHITECTURE.md.
2. **Opening without a skill.** AGENTS.md tells the agent to read `## Now`, run `feature.py show` and `doc_check.py`, report, and ask which feature to take. `cdev-session-start` stays as the full, optional pass.
3. **Answering questions.** The architecture documents are a map; claims about behaviour are verified in the code, whole functions are read, vendor code is left out of broad searches and read directly when the question turns on it, and each claim is marked verified or taken from a document.
4. **Documents that say how, not only where.** The folder template gains `## Files` (one line per file, globs allowed) and `## Flows` (numbered steps naming functions and files).
5. **A second script, `tools/doc_check.py`.** It compares each `## Files` with the folder and the root map with the folder documents, using `git ls-files` so ignored build output is skipped. It reports and exits 1 on drift; nothing runs it as a gate. This relaxes the one-script constraint in section 1.
6. **State that survives summarisation.** `## Now` gains `Confirmed facts` and `Waiting on the user`, is rewritten after every step, and receives confirmed facts as they are found. A new user-invoked skill, `cdev-checkpoint`, writes the whole conversation state there on demand. The agent does not suggest starting a new conversation; that stays the user's call.
7. **Verification outside the editor.** When AGENTS.md says the build or the run happens in a vendor IDE, the feature stops at `verifying` with a checklist for the user under `Waiting on the user`.
8. **`done` needs the user.** `cdev-implement` and `cdev-target-verify` propose closing a feature; it becomes `done` on the user's confirmation, and only when the touched folders' documents match the code.
9. **Editor guards, not gates.** `cdev-init` writes `.vscode/settings.json` (`files.readonlyInclude` for read-only folders, `chat.tools.terminal.autoApprove` entries that keep destructive git and delete commands waiting for approval) and `.github/instructions/architecture.instructions.md`, whose `applyTo` covers the code folders so the document rules reach Copilot whenever it edits documented code. Git hooks remain a non-goal.

Not done, pending a check of the Copilot version in use: subagents for reading code, and nested AGENTS.md files per folder.

### 10.1 Verification levels (2026-09-18)

Bringing up a new chip spends weeks before anything runs on a board, and asking for hardware evidence in that phase is friction with nothing behind it. The alternative considered was a second plugin with the verification stage removed; it was rejected because the two would differ in one stage and share the other ninety percent, and `fw-c-harness` and `cdev` already show what parallel copies cost.

`AGENTS.md` carries `Verification: off | light | full`. `cdev-init` writes `off` for every repository and offers the other two inside its single review question. `cdev-implement`, `cdev-done`, `cdev-target-verify`, and `cdev-feature` read the line; `cdev-target-verify` belongs to `full`.

What no level removes: `done` needs the user's confirmation, and `## Log` records how the feature was checked, including what was left unchecked on hardware.

### 10.2 Upgrades, large repositories, and the remaining skills (2026-09-18)

Four gaps left by 10.1, closed together.

1. **`cdev-upgrade`.** `cdev-init` never overwrites, so a repository set up by an older plugin keeps the older shape, and every template change would otherwise cost a manual merge of `.cdev-proposed` files. The skill checks what the repository holds rather than a version number, which keeps section 1's markdown-first constraint and the non-goal on version tracking: it replaces the two plugin-owned scripts, adds missing sections from the templates, and leaves every sentence the user wrote. Running it twice changes nothing the second time.
2. **Documents written where the work is.** Reading every folder of a repository with a vendor SDK to write `## Files` and `## Flows` can fill a context before `cdev-init` finishes. Init now writes full documents for the folders the user works in, up to about five, and `ARCHITECTURE.stub.md` elsewhere. `doc_check` reports a stub as waiting rather than as drift, AGENTS.md has the agent fill a stub before working in or answering about that folder, and `cdev-architecture-sync` gained that single-folder mode.
3. **The reading rules reach the remaining skills.** `cdev-review`, `cdev-test-gap`, and `cdev-debug` now point at the reading rules in AGENTS.md. `cdev-debug` also writes each phase's confirmed facts into `## Now`, since it reads the most code and produces the most output of any loop here.
4. **A Traditional Chinese `cdev` README**, paired with the English one and checked by a test, so the plugin reads in the language its first users work in.
