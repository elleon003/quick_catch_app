---
name: quick-catch-data-models
description: |
  Defines Quick Catch MVP #1 data schema for brain dumps, extracted tasks, blockers, energy level, and action plans. Use when creating or changing Django models, migrations, API payloads, or serializers for the BrainDump / Priority Engine feature.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Quick Catch Data Models (MVP #1)

Schema for the BrainDump cognitive model dataset. Use when defining Django models, migrations, or API request/response shapes.

## Concepts to Persist

| Concept | Purpose |
|--------|--------|
| Brain dump text | Raw user input |
| Extracted tasks | Full list of tasks from AI |
| Blockers | Detected blockers / self-sabotage / avoidance |
| Energy level | User selection: Low / Medium / High |
| Time of day | When dump was processed (for analytics / matching later) |
| Action plan | Generated 10-Minute Action Plan text (and optionally structured parts) |

## Model Design Options

**Option A – Single record per dump**

One model (e.g. `BrainDump` or `QuickCatchSession`) with fields:

- `user` (FK to user if authenticated)
- `raw_text` (TextField) – brain dump
- `energy_level` (CharField with choices: LOW, MEDIUM, HIGH)
- `extracted_tasks` (JSONField or TextField) – full task list
- `top_3_task_ids` or `top_3_tasks` (JSONField / array) – references or inline
- `blockers` (JSONField or TextField)
- `action_plan_text` (TextField) – the 10-Minute Action Plan
- `created_at` (DateTimeField, auto) – time of day

**Option B – Normalized**

- `BrainDump`: user, raw_text, energy_level, created_at
- `ExtractedTask`: FK to BrainDump, description, rank, is_top_3
- `Blocker`: FK to BrainDump, description
- `ActionPlan`: FK to BrainDump, plan_text (and optionally structured JSON)

Use Option A for MVP speed; Option B if you need to query or display tasks/blockers independently.

## Energy Level

Store as uppercase choices for consistency:

```python
ENERGY_CHOICES = [
    ('LOW', 'Low'),
    ('MEDIUM', 'Medium'),
    ('HIGH', 'High'),
]
```

## API / Serialization

When exposing via Django Ninja or REST:

- **Input**: `raw_text`, `energy_level` (required).
- **Output**: Same as stored: `extracted_tasks`, `top_3_tasks`, `blockers`, `action_plan_text`, plus `id` and `created_at` if persisting.

Match field names to what the AI pipeline returns so parsing is a single mapping step.

## Reference

- Flow and storage intent: `braindump-mvp` skill and `docs/QUICK_CATCH_APP_UX.md`.
- AI output contract: `quick-catch-ai-prompt` skill.
