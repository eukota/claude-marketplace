# Meldwerkes — Design Feedback

Open observations from using the plugin, collected for future design changes.
Not a bug tracker — these are judgment calls about how the plugin should
behave, surfaced through actual use.

## Calibration

- **Highlight the domain/brain being calibrated per question.** During a
  calibration run, questions were presented to the user as a flat list
  (bare IDs like "V4") without their domain/brain visible. Dev-shaped
  decisions (tooling) and doc-shaped decisions (writing) draw on different
  instincts for this user, and losing the domain label made some questions
  harder to answer well — the user had to infer context the underlying data
  already carried (`calibrate.py`'s question schema already has a `domain`
  field per question; it just wasn't surfaced in how the questions were
  presented). The `meldwerkes-calibrate` skill should require/format
  questions with their domain or brain name shown alongside the question
  text, not left to the presenting agent's discretion.
  — surfaced 2026-08-15, kinetic-photo-booth bootstrap session.
