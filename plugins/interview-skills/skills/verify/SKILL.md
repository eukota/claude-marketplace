---
name: verify
description: Use when the candidate in an AI-assisted interview needs to show that the code works, with quick unit checks and edge cases, before or alongside integration tests.
---

# Verify

"It works" needs evidence on screen. For the system as a whole, use `integration-tests`; this skill covers fast checks of the parts.

## Do

1. Ask for tests of the **core flows first**, then happy path only for speed. Name the kinds wanted (unit, integration, regression) so the intent is visible.
2. Get tests into real files and **run them**. Show the output.
3. **Review the test inputs, not just the results.** AI-written tests often cover only easy inputs. Check for: empty, very long, special characters, wrong types, duplicates, and bad requests.
4. The candidate adds **two or more edge cases from their own domain knowledge**, then directs the AI to expand coverage.
5. If a test fails, decide with the candidate whether the code or the test is wrong before changing either.
6. Save a short list to `interview/05-verify.md`: what ran, what passed, what was added, what is deliberately not covered.

## Done when

Tests ran with visible output, at least two candidate-chosen edge cases were added, and the gaps are stated aloud.

Then move on to `integration-tests`.
