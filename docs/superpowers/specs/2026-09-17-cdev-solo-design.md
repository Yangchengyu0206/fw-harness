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
