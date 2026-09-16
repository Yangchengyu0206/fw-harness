# Embedded C rules

Adapted from `agents/expert-embedded-c-engineer.agent.md` in [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT), trimmed to the rules this harness checks or a reviewer applies.

## Types and scope

- Use fixed-width integer types (`uint8_t`, `int16_t`, `uint32_t`) wherever a value's width matters, which in firmware is nearly everywhere.
- Give every function and variable the narrowest scope that works: `static` at file scope for anything the module does not export.
- Use `const` on pointers to read-only data, on parameters the function does not modify, and on file-scope constants.
- Prefer an `enum` over a group of related `#define` constants, because a debugger can show an enum's name.

## Functions and errors

- C has no exceptions, so every function that can fail returns a status the caller can act on, or writes it to an output parameter. Say which one in the header.
- Check every return value you receive. An ignored error code is a critical review finding.
- Validate inputs at the module boundary, meaning the functions the header exports. Inside the module, trust what the boundary already checked rather than paying for the check twice.
- Keep one job per function, and name the function after that job.

## Macros

- Wrap every macro parameter in parentheses, and wrap a multi-statement macro in `do { ... } while (0)`.
- Reach for a `static inline` function before a macro when the compiler allows it: the function keeps its types and gives a debugger something to step into.

## What to leave alone

- Generated code, vendor code, linker scripts, startup files, and compiler flags. Their ARCHITECTURE.md says where they come from and how they are upgraded.
- The naming convention of the module you are editing. Match it.

## MISRA

`harness/review-policy.json` holds the mode. In `advisory` a MISRA finding is a suggestion and never blocks a merge. In `required`, breaking a required rule needs a deviation record, which the `fw-misra-deviation` skill writes. Cite a rule as `Rule X.Y (required)` or `Rule X.Y (advisory)`, so the classification travels with the citation.
