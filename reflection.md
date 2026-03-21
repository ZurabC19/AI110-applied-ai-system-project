# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I designed four classes: `Task`, `Pet`, `Owner`, and `Scheduler`.

- `Task` holds all details about a single care activity: description, scheduled time (HH:MM), frequency (once/daily/weekly), priority, duration, due date, and completion status. It also handles creating the next recurring instance when marked complete.
- `Pet` stores a pet's identity (name, species, breed, age) and owns a list of Task objects. It has methods to add, remove, and filter tasks.
- `Owner` holds the owner's name and email, and maintains a list of Pet objects. It exposes a get_all_tasks() method that returns a flat list of (pet_name, task) tuples for the Scheduler to use.
- `Scheduler` is the central class that handles all the logic: sorting tasks by time, filtering, detecting conflicts, marking tasks complete, and generating the daily plan.

Relationships: Owner has many Pets, Pet has many Tasks, Scheduler references an Owner.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

One change was storing the due date as a datetime.date object instead of a string. This made recurrence logic using timedelta cleaner and less error-prone. I also moved recurrence logic into Task.mark_complete() rather than the Scheduler, since the task itself knows its own frequency.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: time, priority, and completion status. Tasks are sorted chronologically first, then by priority as a tiebreaker when two tasks share the same time. Completion status is used for filtering so the owner only sees what still needs to be done.

Time was chosen as the primary sort key because a pet owner's day is time-structured -- they need to know when to act.

**b. Tradeoffs**

Conflict detection only flags exact time matches -- two tasks scheduled at the same HH:MM. It does not catch overlapping durations (for example, a 60-minute task at 09:00 overlapping a task at 09:30). This is a reasonable tradeoff for a basic daily planner because it keeps the logic simple and avoids false positives on tasks that are technically close but still manageable back-to-back.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used in several phases: brainstorming the class architecture, scaffolding implementations from skeleton stubs, drafting tests, and tracing bugs. The most useful prompts were specific ones that referenced the actual file being worked on, rather than general questions.

**b. Judgment and verification**

When generating conflict detection logic, the AI suggested raising an exception when a conflict was found. I rejected this because a scheduling conflict is a warning, not a fatal error. Raising an exception would crash the app for something the user just needs to be notified about. I changed it to collect warnings into a list and return them so the UI can display them without breaking anything.

---

## 4. Testing and Verification

**a. What you tested**

- Task completion: mark_complete() sets completed to True
- Recurrence: daily tasks create a next task for today + 1 day, weekly for +7 days, one-time tasks return None
- Pet task management: adding and removing tasks changes the count correctly
- Sorting: tasks are returned in chronological order
- Conflict detection: flags duplicate times, returns empty list when all times are unique
- Filtering: by pet name, completion status, and priority
- Edge cases: empty owner with no pets, completing a task that does not exist

These tests matter because the scheduler is the core of the app. A bug in sorting or recurrence would give wrong information without any visible error.

**b. Confidence**

4 out of 5. The core logic is well covered. Given more time I would test invalid time formats, large task lists, and overlapping duration conflicts.

---

## 5. Reflection

**a. What went well**

Keeping the logic in pawpal_system.py separate from the UI in app.py worked well. Because all the behavior lived in plain Python classes, the Streamlit code stayed simple and debugging was easier. I could run main.py in the terminal to test logic without the UI getting in the way.

**b. What you would improve**

I would add duration-aware conflict detection and some form of data persistence so the schedule is not lost when the browser refreshes.

**c. Key takeaway**

AI speeds things up but does not make design decisions for you. You still need to understand the problem well enough to evaluate what the AI produces and push back when it is wrong for the use case.