#!/usr/bin/env python3
"""Stop hook — placeholder for session-end logging (async, non-blocking)."""

# Future: parse session transcript to auto-log decisions made this session.
# For now this is a no-op placeholder — decisions are written explicitly by Claude
# via the write.py script when the pahf-correct skill is invoked.

import sys
sys.exit(0)
