---
name: braindump-mvp
description: |
  Implements MVP #1 BrainDump to Priority Engine per product spec: flow, UI wireframe, data schema, and cognitive triage behavior.
  Use when building or changing the BrainDump entry screen, action plan display, "Email me this" flow, stored dump/task/blocker/plan data, or the AI pipeline for task extraction and 10-Minute Action Plan.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# BrainDump MVP (Priority Engine)

MVP #1 turns an unfiltered brain dump into a focused "10-Minute Action Plan" for neurodivergent founders. The UI must feel like a **safety space**, not a productivity app.

## Core Flow

1. **Entry**: One large text box + "Dump my brain" (or equivalent) primary action.
2. **Energy**: User selects **Low / Medium / High** (buttons) before or with submit.
3. **Submit**: Run AI pipeline:
   - Extract all actionable tasks
   - Identify top 3 by urgency/impact
   - Detect blockers / self-sabotage phrases
   - Match tasks to current energy level (micro-missions)
   - Generate the "10-Minute Action Plan"
4. **Results**: Show action plan in a card below; optional "Email me this" toggle.
5. **Upsell**: Soft CTA e.g. "Want unlimited dumps? Upgrade."

## UI Wireframe

- White (or very light) page, minimal chrome
- Centered **giant textarea** for the dump
- Under textarea:
  - **Energy Level**: Low / Medium / High (button group)
  - **Process Dump** (primary button)
- Results appear in a **card** below the form

Keep the layout minimal and calm. Avoid busy dashboards or multiple steps before the dump.

## Data to Store (Cognitive Model Dataset)

Persist at least:

| Field / concept   | Purpose |
|-------------------|--------|
| Brain dump text   | Raw input |
| Extracted tasks   | Full list from AI |
| Blockers          | Detected blockers / self-sabotage |
| Energy level      | Low / Medium / High |
| Time of day       | For future matching/analytics |
| Action plan text | Generated 10-Minute Action Plan |

This forms the basis for a cognitive model and for "Email me this" and any history/insights later.

## AI Pipeline Contract

- **Input**: Raw brain dump string + energy level (Low | Medium | High).
- **Output**: Structured result that supports:
  - List of extracted tasks
  - Top 3 tasks (urgency/impact)
  - Blockers / emotional friction / avoidance triggers
  - Energy-adapted micro-missions and the final "10-Minute Action Plan" text

Tone of all AI output: **calm, non-judgmental, shame-free, concise.**

The canonical system prompt for the cognitive triage engine is in the project: see `docs/QUICK_CATCH_APP_UX.md` or the `quick-catch-ai-prompt` skill for the exact prompt text. Use that prompt when implementing or changing the AI pipeline.

## Implementation Notes

- Reuse existing Django app patterns (function-based views, `@login_required` if the feature is authenticated).
- Use project Tailwind/DaisyUI patterns for the textarea, energy buttons, primary button, and results card.
- If adding a new app (e.g. `quick_catch` or `braindump`), register it in `config/settings/base.py` and add URLs in `config/urls.py`.
- "Email me this" can be a simple mail send (action plan + optional link); use project email settings from `config/settings/`.

## Reference

- Full Empire Build Plan and MVP #1 spec: `docs/QUICK_CATCH_APP_UX.md`
- AI system prompt and output shape: use skill `quick-catch-ai-prompt` when implementing or editing the prompt/pipeline.
