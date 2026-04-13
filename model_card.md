# Model Card -- PawPal+ Applied AI System

## Base project

PawPal+ from AI110 Module 2. The original system was a Python OOP scheduling app for pet care management built around four classes: Owner, Pet, Task, and Scheduler. It implemented sorting by time and priority, conflict detection, recurring task management, filtering, and a next-available-slot feature. All logic was verified through a CLI demo and a pytest suite.

This version extends that system with an agentic AI advisor that uses Groq (llama-3.1-8b-instant) to analyze the schedule and produce specific recommendations.

---

## New AI feature: agentic advisor

The advisor runs as a three-step pipeline with observable intermediate state at each step.

Step 1 (Plan) inspects the owner's current schedule state -- number of pets, total tasks, conflict count, high-priority items -- and decides what to focus the analysis on. No model call happens here.

Step 2 (Retrieve) pulls all task data from the Scheduler into a structured JSON context object. This includes the sorted schedule, pet details, conflict warnings, pending task count, and the next available time slot. Still no model call.

Step 3 (Advise) sends the structured context to Groq with a focused prompt and returns numbered recommendations. This is the only step that calls the model.

The three-step structure means you can inspect exactly what the model received and trace any recommendation back to specific data in the schedule.

---

## Model

Groq API, llama-3.1-8b-instant. Chosen for its generous free tier (14,400 requests/day) and fast inference. The model is called once per advisor run with a structured JSON context and a direct prompt. No fine-tuning or few-shot examples are used.

---

## Limitations

The advisor output is not deterministic. The same schedule can produce slightly different recommendations on repeated runs.

The model has no memory between sessions. Each run is independent.

The prompt does not include veterinary expertise. Recommendations about pet health are general suggestions, not medical advice.

Conflict detection in the underlying scheduler only catches exact HH:MM matches, not overlapping durations. The advisor inherits this limitation.

---

## Guardrails and reliability

Missing API key raises a ValueError with clear instructions rather than an unhandled exception.

All Groq calls are wrapped in try/except. Errors surface as readable messages in both the CLI and Streamlit UI without crashing the rest of the app.

The scheduling features work fully without an API key. The advisor is additive.

Input to the model is structured JSON built from validated Python objects, not raw user text, which reduces prompt injection risk.

The eval_harness.py script runs three predefined scenarios and prints a pass/fail score for each structural check, giving a confidence score without requiring human review of every run.

---

## AI collaboration during development

Helpful suggestion I kept: the sorted() lambda key using a tuple for composite sorting. Clean and correct.

Flawed suggestion I rejected: raising ValueError on conflict detection. Changed to returning a list of warning strings.

Flawed suggestion I rejected: recursive implementation of next_available_slot(). Replaced with a flat double loop.

Flawed suggestion I rejected: wrapping Owner in a custom class to fix Streamlit session state. The actual fix was simpler.

---

## Testing

17 automated unit tests covering core scheduling logic. All pass.

eval_harness.py runs 3 scenario tests with 14 structural checks against the advisor pipeline. Checks include step count, step names, context shape, and presence of key terms in advice output.

Known gaps: no tests for invalid time formats, duration-aware overlap detection, or advisor content assertions beyond keyword presence.

---

## Potential misuse

The system is a scheduling assistant, not a medical advisor. Output should not be treated as veterinary guidance.

No authentication. data.json is readable by anyone with filesystem access to the machine running the app.