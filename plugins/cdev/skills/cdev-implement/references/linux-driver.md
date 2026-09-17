# Linux driver

Applies to Linux kernel modules and in-tree drivers. The general C rules in `c.md` about bounds and undefined behaviour apply; where the kernel's conventions differ (error codes, allocation, style), this file wins.

## Rules

### Context: what may sleep

Kernel code runs in one of two kinds of context, and the difference decides which calls are legal.

- **Process context** may sleep: system call handlers, `probe` and `remove`, work queue items, threaded interrupt handlers.
- **Atomic context** may not sleep: hard interrupt handlers, softirqs and tasklets, timer callbacks, any code holding a spinlock, and an RCU read-side critical section.

In atomic context there is no `mutex_lock`, no `GFP_KERNEL` allocation, no `copy_from_user` or `copy_to_user`, no `msleep`, and no call that might do any of these. Allocate with `GFP_ATOMIC` there and `GFP_KERNEL` everywhere else, and prefer moving the work to a work queue over allocating atomically.

### Locking and lifetime

- Data shared with an interrupt handler is protected by a spinlock taken with `spin_lock_irqsave`, so the handler cannot run on the same CPU while the lock is held.
- Data touched only where sleeping is allowed is protected by a mutex.
- One lock order for the whole driver, written in a comment where the locks are declared. Two paths that take the same two locks in opposite orders will deadlock.
- An object reachable from more than one path carries a reference count (`kref` or `refcount_t`), and the last `put` frees it.
- `remove` undoes `probe` in reverse order. Interrupts are freed, and timers and work items cancelled with the `_sync` variants, before the memory they touch is released.
- `devm_*` managed resources where they fit, so the unwind happens by construction.

### User memory

- Never dereference a pointer that came from user space.
- `copy_from_user` and `copy_to_user` return the number of bytes not copied. Anything other than zero becomes `-EFAULT`.
- Every length that came from user space is checked against the destination before it is used, including in the size passed to an allocation.
- Zero a structure (`memset` or `= {}`) before copying it to user space. Padding bytes otherwise carry leftover kernel memory out of the kernel.

### Style and portability

- Return negative `errno` values (`-EINVAL`, `-ENOMEM`), and propagate the ones you receive.
- Unwind errors with `goto` labels in reverse order of acquisition.
- Kernel coding style: tabs, the 80-column guideline, and `scripts/checkpatch.pl` clean.
- No floating point.
- Kernel stacks are small, so no large local arrays or structures.
- Register access through the `__iomem` accessors (`ioread32`, `iowrite32`, `readl`, `writel`), and explicit byte order with `le32_to_cpu`, `cpu_to_be16`, and their relatives.

## Review checklist

### Critical

- a sleeping call in atomic context
- a user pointer dereferenced directly, or a `copy_*_user` result ignored
- shared data accessed without its lock
- use after free on `remove`, or on a path racing with it
- an unchecked return value
- a user-supplied length used without validation
- kernel memory copied to user space without being cleared

### Important

- two paths taking the same locks in different orders
- an error path that does not unwind everything acquired before it
- a resource not released on `remove`
- logic with no test where KUnit could reach it

### Suggestion

- `checkpatch.pl` warnings
- naming that does not follow the subsystem's conventions
- a comment that restates the code

## Debugging anchors

- **Read the log first**: `dmesg -w` while reproducing. Add `pr_debug` and enable it at run time with dynamic debug (`echo 'module <name> +p' > /sys/kernel/debug/dynamic_debug/control`).
- **"BUG: sleeping function called from invalid context"**: build with `CONFIG_DEBUG_ATOMIC_SLEEP`. The trace names the sleeping call and the context.
- **Deadlocks and lock order**: `CONFIG_PROVE_LOCKING` (lockdep) reports an inversion the first time both orders happen, before the deadlock does.
- **Memory corruption**: `CONFIG_KASAN` reports out-of-bounds access and use after free at the faulting line.
- **An oops**: run it through `scripts/decode_stacktrace.sh vmlinux . <module path> < oops.txt` to get file and line.
- **Timing**: `ftrace` (`trace-cmd record -p function_graph`) for what ran and how long it took.

## Build and test

Use the commands in AGENTS.md when the repository records them. Otherwise:

- Out-of-tree build: `make -C /lib/modules/$(uname -r)/build M=$PWD modules`
- Load and unload: `sudo insmod <name>.ko`, `sudo rmmod <name>`, then check `dmesg`
- Style: `scripts/checkpatch.pl --strict -f <file>`
- Static checks: `make C=1` for sparse
- Unit tests: KUnit for logic that runs without hardware
- Test on a virtual machine or a board you can reboot, never on your workstation's running kernel
