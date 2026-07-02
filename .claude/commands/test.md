---
description: Lightweight test runner — run Playwright tests and fix any failures. Use this mid-work to stay green. For a deep end-of-session audit (type errors, logic, spec compliance), use /debugloop instead.
argument-hint: [optional test file or pattern]
allowed-tools: Bash(npx playwright test:*), Read, Edit, Write
---

Run the test suite now:

```bash
npx playwright test $ARGUMENTS --reporter=line
```

## If all tests pass
Report the result and stop.

## If any tests fail
For each failure:

1. **Read the failure message carefully.** Understand what the test expected vs. what actually happened.

2. **Find the root cause in the implementation** — not in the test. Do not modify test assertions to make them pass unless the test itself has a genuine bug (wrong selector, wrong URL, etc.). If you believe a test needs changing, say so explicitly and explain why before touching it.

3. **Fix the implementation.**

4. **Re-run the tests** to confirm green.

5. **Do not introduce graceful fallbacks to silence a failure.** If the test is failing because something is broken, fix what is broken. Do not add `try/catch` to hide the error.

Report what you found, what you changed, and the final test result.
