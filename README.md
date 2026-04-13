# PawPal+

A pet care scheduling app built with Python and Streamlit for the AI110 Module 2 project. It lets a pet owner track daily care tasks across multiple pets, with sorting, conflict detection, and recurring task support.

---

## What it does

You set up an owner profile and add your pets, then schedule tasks for each one - walks, feedings, medications, vet appointments. The scheduler sorts everything by time, warns you if two tasks are booked at the same slot, and automatically creates the next occurrence when you mark a recurring task done. Data saves to a JSON file so it persists between sessions.

---

## Classes

**Task** - holds all the details for one care activity: description, time (HH:MM), frequency (once/daily/weekly), priority (1-3), duration, due date, and completion status. Calling mark_complete() on a daily or weekly task returns a new Task for the next occurrence.

**Pet** - stores the pet's name, species, breed, and age, and keeps a list of its tasks. Has methods to add tasks, remove them, and get just the pending ones.

**Owner** - stores the owner's info and a list of pets. The get_all_tasks() method returns a flat list of (pet name, task) pairs for the Scheduler to use. Also handles saving and loading from JSON.

**Scheduler** - where all the logic lives. Sorting, filtering, conflict detection, marking tasks complete, finding the next open time slot, and the weighted priority ranking.

---

## Algorithmic features

Sorting by time - tasks are sorted chronologically using a tuple key (time, priority) so priority breaks ties within the same time slot.

Conflict detection - single pass through all tasks, storing each time in a dict. Any duplicate triggers a warning string instead of an exception, so the app keeps running.

Recurring tasks - mark_complete() uses timedelta to calculate the next due date. Daily adds 1 day, weekly adds 7 days, once returns None.

Filtering - by pet name, completion status, or priority level.

Next available slot - loops through every hour and half-hour from 7am to 9pm and returns the first one not already taken.

Weighted priority score - formula is priority x 10 minus duration x 0.1, so longer high-priority tasks rank ahead of shorter ones at the same priority level.

---

## File structure

```
pawpal-plus/
    pawpal_system.py     backend logic
    app.py               Streamlit UI
    main.py              CLI demo
    requirements.txt
    README.md
    reflection.md
    model_card.md
    tests/
        test_pawpal.py
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the CLI demo:
```bash
python main.py
```

Run the app:
```bash
streamlit run app.py
```

Run tests:
```bash
python -m pytest
```

---

## Sample output

```
PawPal+ Daily Schedule
=======================================================
  [Buddy] [07:30] Morning Feeding (10 min | High priority | daily)
  [Whiskers] [07:30] Morning Feeding (10 min | High priority | daily)
  [Buddy] [08:00] Heartworm Medication (5 min | High priority | weekly)
  [Whiskers] [10:00] Vet Checkup (60 min | High priority | once)
  [Buddy] [14:00] Grooming Appointment (60 min | Medium priority | once)
  [Buddy] [18:00] Evening Walk (45 min | High priority | daily)

CONFLICTS DETECTED:
  Conflict at 07:30: 'Morning Feeding' (Buddy) and 'Morning Feeding' (Whiskers)
=======================================================

Marking 'Evening Walk' complete for Buddy...
'Evening Walk' marked complete. Next occurrence added for 2026-04-14.
```

---

## Testing

17 tests covering task completion, recurrence logic, sorting, conflict detection, filtering, edge cases, and JSON persistence. All pass.

Confidence level: 4 out of 5. Core logic is solid. Known gap is that conflict detection only catches exact time matches, not overlapping durations.

---

## Smarter scheduling

The Scheduler class handles all the algorithmic work. Tasks come in with times added out of order in the demo - the sort produces correct chronological output. Conflicts surface as warning strings so the UI can display them without crashing. Recurring tasks get their next occurrence added automatically on completion. The next available slot feature scans the 7am-9pm window in 30-minute increments and returns the first free slot.