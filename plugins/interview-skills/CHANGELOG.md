# Changelog

## 0.3.0

- Reworked into five steps: `prep`, `plan`, `implement`, `test`, `commentary`, plus `configure`, `observability` and `narrate`.
- `prep` replaces `clarify`: a background agent writes `best_practices.md` while the candidate builds `prompt.md` with the interviewer, then trims the research.
- `plan` follows both artifacts and adds a plain-language summary, a diagram, a shared contract (including what the system reports about itself and the test scenarios) and a work split with a dashboard unit and a clickable-tests unit.
- `implement` replaces `direct` and `review`: it writes the contract first, dispatches many agents at once, integrates, and runs the candidate's review.
- New `observability` skill: the dispatch phrase and what the dashboard must show, so the system's activity is visible as it happens.
- `test` replaces `verify` and `integration-tests`: a few clickable demonstrations watched on the dashboard, the candidate's own edge cases, and iteration on what breaks.
- New `commentary` skill: a spoken close on what the candidate would do for real, tied to the plan's Not-doing list.
- `implement` treats the review as the main event: the build is short, and the candidate must explain the output in their own words.
- `configure` shares `time` across the steps (15%, 15%, 30%, 30%, 10%) and accepts the new skill names in `skip`.
- Removed skills: `clarify`, `direct`, `review`, `verify`, `integration-tests`.

## 0.2.0

- Renamed from `vellum-gambit` to `interview-skills`.
- New `configure` meta-skill: asks about mode, time, level, stack, AI tool, voice, narration and skipped skills, and writes `interview/config.md`.
- Every other skill now reads `interview/config.md` if it exists. Shared rules live in `skills/configure/references/settings.md`.

## 0.1.0

- First draft: `clarify`, `plan`, `direct`, `review`, `verify`, `integration-tests`, `narrate`.
- `integration-tests` is a meta-skill that instructs Claude to build the tests, an observability dashboard and click-triggered runs.
