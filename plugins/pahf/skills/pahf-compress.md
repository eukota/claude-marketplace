---
name: pahf-compress
description: Run the compression loop to extract principles from accumulated decisions and corrections. Promotes patterns from raw observations up the memory hierarchy.
---

# PAHF Compression Loop

Periodically compress accumulated decisions into principles, and principles into meta-principles.

## When to Run

- Manually triggered by the user ("compress memory", "extract principles")
- After a session with 5+ decisions
- When the user asks what principles have been learned

## Steps

1. **Run compression**:
   ```bash
   python3 ~/Development/small-brain-alpha/scripts/compress.py \
     --domain <domain> \
     --num-recent 20
   ```
2. **Review extracted principles** — show them to the user.
3. **Ask for corrections** — are any principles wrong? Weighted incorrectly?
4. **Run meta-principle extraction** if 2+ principles exist:
   ```bash
   python3 ~/Development/small-brain-alpha/scripts/compress.py \
     --domain <domain> \
     --meta-only
   ```
5. **Show the updated memory state** — how many principles, any conflicts surfaced.

## Format

```
Compression run for domain: [domain]
Decisions analyzed: [N]
Principles extracted:
  - [principle 1] (confidence: X%)
  - [principle 2] (confidence: X%)
Meta-principles:
  - [when A conflicts with B, A wins in context C]
Corrections to these? [wait for user response]
```

## What This Catches

Compression is what prevents sycophancy from accumulating. Without it, the brain drifts toward whatever worked recently. With it, corrections become durable principles that override future sycophantic tendencies.
