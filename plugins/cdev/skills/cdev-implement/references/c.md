# C in user space

Applies to C that runs as an ordinary process: applications, libraries, and command line tools. Firmware and kernel drivers have their own references, and their rules win where the two disagree.

## Rules

### Ownership and allocation

- Every allocation has exactly one owner, and the owner is named in the comment on the function that hands it out: "caller frees", or "valid until the next call".
- Check every allocation. A `malloc` that returns `NULL` and is used anyway turns an out-of-memory condition into a crash somewhere else.
- Before allocating `count * size`, check that the product cannot overflow. `calloc` does the check for you; a hand-written multiplication does not.
- Sizes and indices are `size_t`. Mixing signed and unsigned in a comparison silently converts the signed side.
- Free on every exit path. A function with several early returns releases what it took with one cleanup label, not with a copy of the cleanup before each return.

### Buffers and strings

- Every write into a buffer carries its length. `snprintf` over `sprintf`, `memcpy` with an explicit bound over a loop that trusts a terminator.
- `strncpy` does not terminate the destination when the source fills it. Terminate it yourself, or use `snprintf(dst, size, "%s", src)`.
- A length that came from outside the program (a file, a socket, an argument) is checked against the buffer before it is used.
- A format string is always a literal. `printf(user_text)` hands the caller a way to read and write memory.

### Undefined behaviour

The compiler assumes none of these happen and optimises accordingly, so the result is not a wrong value but arbitrary behaviour:

- signed integer overflow
- shifting by a negative amount, or by the width of the type or more
- reading memory that was never initialised
- pointer arithmetic outside an object, other than one past its end
- accessing an object through a pointer of an unrelated type (strict aliasing)
- modifying a string literal

### Structure

- `static` for every function and file-scope variable the module does not export.
- `const` on every pointer to data the function does not modify.
- One error convention per module: a status return with output parameters, or a negative error code. Say which in the header, and check every return you receive.

## Review checklist

### Critical

- a buffer or string written past its end, or an external length used without a bound
- use after free, or a double free
- an allocation or a return code that is not checked
- an integer overflow in a size or index calculation
- a format string built from input
- undefined behaviour from the list in Rules

### Important

- memory or a file handle leaked on an error path
- new logic with no test
- a resource released on the success path only
- a magic number standing in for a size or a limit

### Suggestion

- naming that does not match the module it lives in
- a comment that restates the code instead of giving the reason
- deep nesting, or a function doing several jobs

## Debugging anchors

- **AddressSanitizer and UndefinedBehaviorSanitizer** catch out-of-bounds access, use after free, leaks, and undefined behaviour at the line where they happen. Build with `-fsanitize=address,undefined -g -O1` and run the reproduction.
- **Valgrind** (`valgrind --leak-check=full ./program`) where sanitizers are unavailable. Slower, and needs no rebuild.
- **A core dump in gdb**: `gdb ./program core`, then `bt full` for the stack with locals. On Linux, `ulimit -c unlimited` before reproducing.
- **A crash that moves when you add a print** is memory corruption until proven otherwise. Reach for the sanitizers before reading code.
- **It appeared recently**: `git bisect run` with the shrunken reproduction as the test.

## Build and test

Use the commands in AGENTS.md when the repository records them. Otherwise, the usual shapes are:

- CMake: `cmake -B build -S .`, `cmake --build build`, `ctest --test-dir build --output-on-failure`
- Make: `make`, `make test`
- Tests: Unity or cmocka for C, each test file built as its own executable
- Warnings: `-Wall -Wextra -Werror` on new code, and fix the warning rather than silence it
