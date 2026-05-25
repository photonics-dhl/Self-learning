---
name: handoff_discipline
description: HANDOFF.md must be filled before every /clear or session end — iron rule for cross-session continuity
metadata:
  type: feedback
---

# HANDOFF.md Discipline

**Rule:** Before `/clear` or session end, always fill HANDOFF.md with current task state, key decisions, blockers, next steps, and relevant files.

**Why:** SessionEnd hook auto-checks HANDOFF.md and warns if empty. SessionStart hook prints HANDOFF.md content. Without this discipline, every /clear loses all task context — the prior session's work becomes invisible to the next session.

**How to apply:** After any non-trivial work, write to HANDOFF.md. Before `/clear`, verify all 4 sections are filled. The hook will warn if fewer than 3 sections have content.
