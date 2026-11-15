# Changelog

## 0.3.0

- Reworked into four steps: `prep`, `plan`, `implement`, `test`, plus `configure` and `narrate`.
- `prep` replaces `clarify`: a background agent writes `best_practices.md` while the candidate builds `prompt.md` with the interviewer, then trims the research.
- `plan` now follows both artifacts and adds a plain-language summary, a diagram, a shared contract and a work split for parallel agents.
- `implement` replaces `direct` and `review`: it writes the contract first, dispatches agents in parallel, integrates, and runs the candidate's review.
- `test` replaces `verify` and `integration-tests`: quick checks plus integration tests that always come with an observability dashboard and click-triggered runs.
- `configure` shares `time` across the steps (15%, 15%, 40%, 30%) and accepts the new skill names in `skip`.
- Removed skills: `clarify`, `direct`, `review`, `verify`, `integration-tests`.

## 0.2.0

- Renamed from `vellum-gambit` to `interview-skills`.
- New `configure` meta-skill: asks about mode, time, level, stack, AI tool, voice, narration and skipped skills, and writes `interview/config.md`.
- Every other skill now reads `interview/config.md` if it exists. Shared rules live in `skills/configure/references/settings.md`.

## 0.1.0

- First draft: `clarify`, `plan`, `direct`, `review`, `verify`, `integration-tests`, `narrate`.
- `integration-tests` is a meta-skill that instructs Claude to build the tests, an observability dashboard and click-triggered runs.
