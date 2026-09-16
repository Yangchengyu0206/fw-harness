# Repository architecture

Sample firmware tree used by the fw-harness tests.

<!-- fw-harness:architecture:begin -->
<!-- Generated from harness/architecture.json. Run fw-architecture-sync after changing it. -->

| Module | Kind | Approved dependencies |
|---|---|---|
| src/app | owned | src/drivers |
| src/drivers | owned | src/hal |
| src/hal | owned | third_party/cmsis |
| test | test | none |
| third_party/cmsis | vendor | none |

Grandfathered dependencies (the list may only shrink):
- src/hal -> src/app

<!-- fw-harness:architecture:end -->
