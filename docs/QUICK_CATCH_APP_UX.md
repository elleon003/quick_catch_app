**Excellent.**
Here is your **full Empire Build Plan** — product specs, UI flows, prompts, data schema, and a 3-day build schedule for each MVP. This is the kind of internal blueprint founders would normally guard with NDAs.

I’m giving you the whole war map.

---

# 🏛️ **EMPIRE BUILD PLAN (All 3 MVPs)**

Built for 1–3 day execution, AI-heavy, low code, maximum impact.

---

# =========================================

# ⚡️ **MVP #1 — BrainDump → Priority Engine**

# =========================================

## 🎯 Purpose

Create instant clarity from chaos. Get users addicted to the “dump → action plan” loop.

## 🧠 Core Flow (Keep extremely minimal)

1. **Entry screen**: one large text box + “Dump my brain” button.
2. On submit, run AI pipeline:

   * extract tasks
   * identify top 3 by urgency/impact
   * detect blockers/self-sabotage phrases
   * match to current energy level
   * generate the “10-Minute Action Plan”
3. Display action plan + optional “Email me this” toggle.
4. Soft upsell: “Want unlimited dumps? Upgrade.”

---

## 🖼️ UI Wireframe (simple)

* White page
* Centered giant textarea
* Under it:
  “Energy Level: Low / Medium / High (buttons)”
  “Process Dump” (primary button)
* Results appear in a card below

This UI must feel like a **safety space**, not a productivity app.

---

## 🧬 Data Storage

Store:

* brain dump text
* extracted tasks
* blockers
* energy level
* time of day
* action plan generated

This forms your **cognitive model dataset**.

---

## 🧩 AI Prompt (Core Engine)

Use this as your system prompt:

```
You are a cognitive triage engine for neurodivergent founders.
Input is an unfiltered brain dump. 
Your job:
1. Extract all actionable tasks.
2. Identify the 3 most important tasks (based on urgency, consequences, and cognitive load).
3. Detect hidden blockers, emotional friction, or avoidance triggers.
4. Reshape tasks into “micro-missions” based on user energy:
   - LOW energy → tiny, non-intimidating wins
   - MEDIUM energy → steady progress tasks
   - HIGH energy → leverage high-focus tasks
5. Produce a “10-Minute Action Plan” that removes overwhelm.

Tone: calm, non-judgmental, shame-free, concise.
```
