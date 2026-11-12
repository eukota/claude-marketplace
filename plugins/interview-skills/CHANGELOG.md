# Changelog

## 0.2.0

- Renamed from `vellum-gambit` to `interview-skills`.
- New `configure` meta-skill: asks about mode, time, level, stack, AI tool, voice, narration and skipped skills, and writes `interview/config.md`.
- Every other skill now reads `interview/config.md` if it exists. Shared rules live in `skills/configure/references/settings.md`.

## 0.1.0

- First draft: `clarify`, `plan`, `direct`, `review`, `verify`, `integration-tests`, `narrate`.
- `integration-tests` is a meta-skill that instructs Claude to build the tests, an observability dashboard and click-triggered runs.
