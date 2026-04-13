# PawPal+ Applied AI System

**Base project:** PawPal+ (AI110 Module 2)

The original PawPal+ was a Python OOP scheduling app for pet care management. It modeled Owner, Pet, Task, and Scheduler classes and implemented algorithmic features including time-based sorting, conflict detection, recurring task management, and filtering. This project extends that system with an agentic AI advisor powered by Groq (llama-3.1-8b-instant).

---

## What's new in this version

The main addition is `pawpal_advisor.py` — a three-step agentic pipeline that analyzes the owner's current schedule and returns specific, actionable recommendations. The agent's intermediate steps are fully observable in both the CLI output and the Streamlit UI.

The agent does not just pass the schedule to the model and print the output. It runs three distinct steps with logged intermediate state:

**Step 1 - Plan:** inspects the owner's pets, total task count, conflict count, and high-priority items to decide what to focus the analysis on. No model call happens here.

**Step 2 - Retrieve:** pulls all task data from the Scheduler into a structured JSON context object including pet details, the full sorted schedule, conflict warnings, and the next available time slot. Still no model call.

**Step 3 - Advise:** sends the structured context to Groq with a focused prompt and returns numbered recommendations grounded in the actual schedule data from steps 1 and 2.

---

## System Architecture

```
User (CLI or Streamlit UI)
        |
        v
PawPalAdvisor (pawpal_advisor.py)
   Step 1: Plan     -- inspect owner/scheduler state (no model call)
   Step 2: Retrieve -- build structured JSON context from Scheduler
   Step 3: Advise   -- send context to Groq, return recommendations
        |
        v
Scheduler (pawpal_system.py)
   sort_by_time, sort_by_priority, detect_conflicts,
   filter_by_*, next_available_slot, weighted_priority_score
        |
        v
Owner -> Pet(s) -> Task(s)
        |
        v
data.json (persistence layer)
```

See `assets/uml_diagram.png` for the full class diagram.

Data flows from the user's schedule up through the Scheduler, gets packaged into a context dict by the advisor, sent to Groq, and recommendations come back into the UI. The Scheduler never talks to Groq directly — the advisor is the bridge layer.

---

## Files

```
pawpal-plus/
    pawpal_system.py      core OOP classes (Owner, Pet, Task, Scheduler)
    pawpal_advisor.py     agentic AI advisor (3-step Groq pipeline)
    eval_harness.py       evaluation script with pass/fail scoring
    app.py                Streamlit UI with AI Advisor tab
    main.py               CLI demo including advisor run
    requirements.txt
    README.md
    reflection.md
    model_card.md
    .env                  your GROQ_API_KEY goes here (not committed)
    assets/
        uml_diagram.png   system class diagram
    tests/
        test_pawpal.py    17 automated tests
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=gsk_your-key-here
```

Get a free Groq API key at console.groq.com.

**Run the CLI demo:**
```bash
python main.py
```

**Run the Streamlit app:**
```bash
streamlit run app.py
```

**Run the automated tests:**
```bash
python -m pytest
```

**Run the evaluation harness:**
```bash
python eval_harness.py
```

---

## Sample interactions

### Example 1: Conflict detection + AI advice

Input: Buddy and Whiskers both have "Morning Feeding" scheduled at 07:30.

Scheduler conflict output:
```
Conflict at 07:30: 'Morning Feeding' (Buddy), 'Morning Feeding' (Whiskers)
```

AI Advisor agent steps:
```
Step 1 - Plan: Analyzing schedule for Buddy, Whiskers. Focus: 1 conflict; 7 tasks across 2 pets; 4 high-priority tasks.
Step 2 - Retrieve: Collected 7 tasks, 1 conflict, next free slot: 07:00
Step 3 - Advise: Sending schedule context to Groq (llama-3.1-8b-instant) for analysis
```

AI recommendation:
```
1. Alex, you have a conflict at 07:30 where both Buddy and Whiskers have Morning
   Feeding scheduled at the same time. Consider feeding one at 07:15 and the other
   at 07:45 so you can give each pet proper attention.
```

### Example 2: Recurring task completion

Input: Mark "Evening Walk" (daily frequency) complete for Buddy.

Output:
```
'Evening Walk' marked complete. Next occurrence added for 2026-04-14.
```

### Example 3: Evaluation harness output

```
Test: Conflict Schedule
  [PASS] 3 agent steps recorded
  [PASS] Step 1 is Plan
  [PASS] Step 2 is Retrieve
  [PASS] Step 3 is Advise
  [PASS] Conflict mentioned in advice
  [PASS] Owner name in advice
  [PASS] Context has conflicts

Result: 13/14 checks passed
Confidence score: 0.93
```

---

## Reliability and guardrails

Missing API key raises a `ValueError` with clear instructions rather than crashing. All Groq calls are wrapped in try/except — errors display as readable messages in both CLI and UI without affecting the scheduling features.

The core scheduling logic works fully without an API key. The advisor is additive.

Input to the model is structured JSON built from validated Python objects, not raw user text, which reduces prompt injection risk.

17 automated pytest tests cover the scheduling logic independently of the AI feature.

The `eval_harness.py` script runs the advisor against three predefined schedules and prints a pass/fail score for each structural check.

---

## Testing

```bash
python -m pytest        # 17 unit tests
python eval_harness.py  # 3 scenario evaluation with scoring
```

17 unit tests all pass. Eval harness runs 3 scenarios with 14 checks total.

Confidence: 4 out of 5. Core scheduling logic is well covered. AI advisor output is non-deterministic so it is evaluated structurally (step count, context shape) rather than by content assertion.

---

## Design decisions and tradeoffs

The three-step pipeline separates data collection from model interaction deliberately. Steps 1 and 2 are pure Python — fast, testable, deterministic. Only Step 3 calls the model. This means if the API is down the rest of the app still works, and it means the eval harness can check steps 1 and 2 without a live API call if needed.

Conflict detection only flags exact HH:MM matches. Duration-aware overlap detection was considered but would have added significant complexity for marginal benefit in a basic daily planner. Documented as a known gap.

Groq was chosen over other providers for its generous free tier (14,400 requests/day vs Gemini's per-project daily cap that exhausts quickly during development).