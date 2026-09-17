# Windows driver

Applies to Windows kernel-mode drivers: KMDF first, WDM where the driver requires it. The general C rules in `c.md` about bounds and undefined behaviour apply; where the kernel's conventions differ, this file wins.

## Rules

### IRQL: what each level permits

Every routine runs at an interrupt request level, and the level decides what it may touch.

- **`PASSIVE_LEVEL`**: may touch paged memory, wait, and call almost anything. Dispatch routines for most I/O start here.
- **`APC_LEVEL`**: may touch paged memory; some waits are restricted.
- **`DISPATCH_LEVEL`** and above: DPCs, timer callbacks, and code holding a spinlock. No paged code or paged data, no wait with a non-zero timeout, and no call documented as `PASSIVE_LEVEL` only.

Mark every pageable routine with `PAGED_CODE()` at its top, so a checked build asserts when it is called too high. Annotate routines with SAL, for example `_IRQL_requires_max_(PASSIVE_LEVEL)`, so the static analysers check callers.

### Memory

- `ExAllocatePool2(POOL_FLAG_NON_PAGED, size, tag)` for anything touched at `DISPATCH_LEVEL` or above; `POOL_FLAG_PAGED` otherwise.
- A distinct four-character pool tag per allocation site, so a leak in `!pool` points at the line that made it.
- Check every allocation. `ExAllocatePool2` zeroes the memory; older allocators do not.

### KMDF objects and requests

- Parenting decides lifetime: an object is deleted with its parent. Choose the parent on purpose, and do not keep a pointer to an object past its parent's life.
- Per-device and per-request state lives in context space (`WDF_DECLARE_CONTEXT_TYPE`), not in globals.
- Every request is completed exactly once. A path that completes it twice crashes; a path that never completes it hangs the caller and blocks unload.
- A request that waits is cancelable, and its cancel routine and completion path cannot both complete it.
- Choose the queue dispatch type (sequential, parallel, manual) on purpose, and write the reason beside it.
- `WdfSpinLock` for state touched at `DISPATCH_LEVEL`, `WdfWaitLock` for state touched only at `PASSIVE_LEVEL`.

### IOCTL buffers

- Check the input and output buffer lengths of every IOCTL before reading or writing either buffer.
- Prefer `METHOD_BUFFERED`, or `METHOD_DIRECT` for large transfers.
- A `METHOD_NEITHER` user pointer is probed with `ProbeForRead` or `ProbeForWrite` and accessed only inside `__try` / `__except`, in the context of the requesting process.
- Check every `NTSTATUS` with `NT_SUCCESS`, and propagate failures.
- No floating point unless the extended processor state is saved with `KeSaveExtendedProcessorState` and restored.

## Review checklist

### Critical

- paged code or paged memory touched at `DISPATCH_LEVEL` or above
- a request completed twice, or a path that never completes it
- an IOCTL buffer length not validated before use
- a `METHOD_NEITHER` pointer used without probing inside `__try`
- an object used after it, or its parent, was deleted
- an `NTSTATUS` ignored
- state shared with an ISR or DPC without synchronisation

### Important

- an allocation without a distinct pool tag
- a waiting request that cannot be cancelled
- a pageable routine without `PAGED_CODE()`
- a change that has not run under Driver Verifier

### Suggestion

- missing SAL annotations on a routine's IRQL and buffers
- naming, or a comment that restates the code
- diagnostics through `DbgPrint` where WPP tracing is set up

## Debugging anchors

- **Run under Driver Verifier while testing**: `verifier /standard /driver <name>.sys`, then reboot. It turns silent corruption into an immediate, attributable bugcheck.
- **Start every crash with** `!analyze -v` in WinDbg. Then `!irql` for the level at the crash, `!pool <address>` for the allocation, and `!wdfkd.wdflogdump <name>` for the KMDF log.
- **`IRQL_NOT_LESS_OR_EQUAL` (0xA) or `DRIVER_IRQL_NOT_LESS_OR_EQUAL` (0xD1)**: almost always paged memory touched at `DISPATCH_LEVEL`, or a freed pointer. Check the address against the pool and the routine's IRQL.
- **A hang on unload**: a request that was never completed, or a reference that was never released.
- **Tracing**: WPP messages collected with TraceView or `tracelog`, readable after the fact without a debugger attached.

## Build and test

Use the commands in AGENTS.md when the repository records them. Otherwise:

- Build: `msbuild <driver>.vcxproj /p:Configuration=Debug /p:Platform=x64`, with the Windows Driver Kit installed
- Test machine only: enable test signing with `bcdedit /set testsigning on` and reboot; never on a workstation you depend on
- Install: `pnputil /add-driver <name>.inf /install`
- Verifier: enabled for the driver during every test run
- Before release: Static Driver Verifier or CodeQL, and the checks the Windows Hardware Lab Kit requires for the driver's class
