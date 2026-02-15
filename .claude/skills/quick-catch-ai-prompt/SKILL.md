---
name: quick-catch-ai-prompt
description: |
  Defines the cognitive triage system prompt and output contract for the BrainDump AI pipeline (task extraction, top 3, blockers, energy-matched micro-missions, 10-Minute Action Plan).
  Use when implementing or changing the AI pipeline, prompt engineering, or response parsing for Quick Catch / BrainDump.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Quick Catch AI Prompt (Cognitive Triage Engine)

Use this when implementing or modifying the BrainDump AI pipeline. The engine consumes an unfiltered brain dump and the user's energy level, then returns structured data for the 10-Minute Action Plan.

## System Prompt (Canonical)

Use this as the system prompt for the cognitive triage model:

```
You are a cognitive triage engine for neurodivergent founders.
Input is an unfiltered brain dump. 
Your job:
1. Extract all actionable tasks.
2. Identify the 3 most important tasks (based on urgency, consequences, and cognitive load).
3. Detect hidden blockers, emotional friction, or avoidance triggers.
4. Reshape tasks into "micro-missions" based on user energy:
   - LOW energy → tiny, non-intimidating wins
   - MEDIUM energy → steady progress tasks
   - HIGH energy → leverage high-focus tasks
5. Produce a "10-Minute Action Plan" that removes overwhelm.

Tone: calm, non-judgmental, shame-free, concise.
```

## Inputs

- **Brain dump**: Raw text from the user (unfiltered).
- **Energy level**: One of `LOW` | `MEDIUM` | `HIGH`. Pass this into the prompt or as a structured parameter so the model can adapt micro-missions.

## Output Contract

The pipeline must produce (or parse from the model response) at least:

| Output | Description |
|--------|-------------|
| Extracted tasks | Full list of actionable tasks from the dump |
| Top 3 tasks | The three most important by urgency, consequences, cognitive load |
| Blockers | Detected blockers, emotional friction, avoidance triggers |
| Micro-missions | Energy-adapted small steps |
| 10-Minute Action Plan | Single coherent plan text (or structured bullets) for display and "Email me this" |

Prefer a **structured** response (e.g. JSON) from the model so the app can store and display each part without re-parsing prose. If the model returns markdown or prose, define a parsing contract (sections, headings) and document it where the pipeline is implemented.

## Tone Rules

All model output must stay **calm, non-judgmental, shame-free, and concise**. When editing the system prompt or adding few-shot examples, preserve this tone. Avoid productivity jargon that can feel punishing (e.g. "you should", "you must", guilt-inducing framing).

## Reference

- Product and data spec: `braindump-mvp` skill and `docs/QUICK_CATCH_APP_UX.md`.
