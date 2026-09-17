"""Human-in-the-loop reproduction loop.

Use it when reproducing a defect needs a person: pressing reset, moving a cable,
watching an LED. Copy this file somewhere git ignores, edit STEPS, and ask the
user to run it in their own terminal:

    py -3 hitl_loop.py --out <evidence-folder>/hitl-<YYYY-MM-DD>.txt

Each step is one of:

    ("do", "<instruction>")             the user does it and presses Enter
    ("ask", "<KEY>", "<question>")      the user's one-line answer is kept under KEY

The answers are printed as KEY=VALUE and written to --out for the agent to read.
Ask for observations only. Anything secret the user has to type belongs in a
"do" step, never in an "ask".
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

# --- edit below ---------------------------------------------------------------

STEPS = [
    ("do", "Flash the build, or load the driver, and open the serial terminal or log viewer."),
    ("do", "Press the reset button once, or run the trigger command."),
    ("ask", "BANNER", "Did the startup banner appear? (y/n)"),
    ("ask", "LAST_LINE", "Paste the last line the log printed:"),
]

# --- edit above ---------------------------------------------------------------

KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def validate(steps):
    """Return every problem with the steps, so a typo fails before the first prompt."""
    problems = []
    keys = set()
    for index, step in enumerate(steps, 1):
        if not isinstance(step, tuple) or not step:
            problems.append(f"step {index}: must be a non-empty tuple")
        elif step[0] == "do":
            if len(step) != 2 or not str(step[1]).strip():
                problems.append(f'step {index}: write ("do", "<instruction>")')
        elif step[0] == "ask":
            if len(step) != 3 or not str(step[2]).strip():
                problems.append(f'step {index}: write ("ask", "<KEY>", "<question>")')
            elif not KEY_RE.match(step[1]):
                problems.append(f"step {index}: key {step[1]!r} must be UPPER_SNAKE_CASE")
            elif step[1] in keys:
                problems.append(f"step {index}: key {step[1]} is used twice")
            else:
                keys.add(step[1])
        else:
            problems.append(f"step {index}: kind must be 'do' or 'ask', not {step[0]!r}")
    return problems


def run(steps, read=input, write=print):
    answers = {}
    for index, step in enumerate(steps, 1):
        if step[0] == "do":
            write(f"\n>>> {index}. {step[1]}")
            read("    [Enter when done] ")
        else:
            write(f"\n>>> {index}. {step[2]}")
            answers[step[1]] = read("    > ").strip()
    return answers


def render(answers, when):
    lines = [f"# captured {when}"]
    lines += [f"{key}={value}" for key, value in answers.items()]
    return "\n".join(lines) + "\n"


def main(argv=None, steps=None, read=input, write=print, now=None):
    parser = argparse.ArgumentParser(description="Walk a person through reproduction steps and record what they saw.")
    parser.add_argument("--out", type=Path, help="file the captured answers are written to")
    args = parser.parse_args(argv)
    steps = STEPS if steps is None else steps

    problems = validate(steps)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 2

    try:
        answers = run(steps, read, write)
    except (KeyboardInterrupt, EOFError):
        print("\nstopped before the last step; nothing was written", file=sys.stderr)
        return 130

    when = (now or datetime.datetime.now()).isoformat(timespec="seconds")
    text = render(answers, when)
    write("\n--- Captured ---\n" + text.rstrip("\n"))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        write(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
