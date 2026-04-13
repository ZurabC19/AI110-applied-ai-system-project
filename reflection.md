# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I went with four classes: Task, Pet, Owner, and Scheduler.

Task holds everything about a single care activity - the description, what time it's scheduled, how often it repeats, priority level, how long it takes, the date, and whether it's done. It also handles creating the next instance of itself when you mark it complete, which felt like the right place for that logic since the task already knows its own frequency.

Pet stores the basic info about the animal and keeps a list of its tasks. It has methods to add tasks, remove them, and filter for just the ones that aren't done yet.

Owner holds the owner's name and email and keeps track of all their pets. It has a method that flattens everything into one list of (pet name, task) pairs so the Scheduler can work with it.

Scheduler is where all the actual logic lives - sorting, filtering, conflict detection, marking things complete, and the stretch features.

For the applied AI extension, I added PawPalAdvisor as a fifth component. It sits on top of the existing system and uses the Scheduler's outputs as input to a Groq API call.

**b. Design changes**

The main thing I changed in the original system was storing due_date as a date object instead of a string. I started with strings and immediately ran into problems when I tried to add days to them for recurrence. Switching to datetime.date with timedelta fixed that cleanly.

I also moved recurrence logic into Task.mark_complete() instead of the Scheduler. The task itself knows its own frequency so it made more sense there.

For the advisor, the original design had the model call in a single function. I split it into three steps after realizing the grader needed to see observable intermediate state. The split also made the code easier to test since steps 1 and 2 are pure Python with no API dependency.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

Tasks are sorted by time first, then priority as a tiebreaker if two tasks share the same slot. I also added a weighted score that factors in duration, so longer high-priority tasks rank ahead of shorter ones within the same priority tier.

Time is the primary sort key because a pet owner's day is time-structured - you need to know what's happening at 8am before you can think about relative priority.

**b. Tradeoffs**

Conflict detection only catches exact time matches. Two tasks at the same HH:MM get flagged, but a 60-minute task at 9:00 and another at 9:30 won't trigger anything even though they obviously overlap. I kept it simple because duration-aware detection would have required significantly more complexity for a feature that already does its job for the common case.

The advisor uses a single model call per run rather than a chain. A more sophisticated agent would call the model at each step and let each step's output influence the next. I chose the simpler approach because the schedule data is structured enough that the retrieval step doesn't need AI to decide what to collect.

---

## 3. AI Collaboration

**a. How I used AI**

I used Copilot for scaffolding the original class skeletons, filling in method bodies, drafting the initial test file, and debugging session state issues in the Streamlit UI. For the advisor, I used it to draft the initial three-step structure and the Groq API call syntax.

**b. What I accepted and what I changed**

Helpful suggestion I kept: the sorted() lambda key using a tuple for composite sorting. Clean and correct, adopted as-is.

Flawed suggestion I rejected: for conflict detection, the AI suggested raising ValueError when it found a conflict. A conflict is a notification, not a crash condition. Changed to collecting warnings in a list.

Flawed suggestion I rejected: for next_available_slot(), the AI suggested a recursive function. Replaced with a flat double loop over hours and half-hours. Simpler, no stack concerns for a 28-slot window.

Flawed suggestion I rejected: for the Streamlit session state bug where Add Task wasn't persisting, the AI suggested wrapping the Owner in a custom class. The actual fix was simpler - use st.session_state.owner directly for all writes instead of a local variable copy.

**c. Limitations and future improvements**

The advisor output is non-deterministic. The same schedule can produce slightly different recommendations on repeated runs. This makes it impossible to assert on specific wording in automated tests, so the eval harness checks structural properties instead.

The conflict detection gap (duration-aware overlap) is the most significant known limitation. A 60-minute task at 09:00 and a task at 09:30 don't conflict in the current system.

If I had more time I would add duration-aware conflict detection, a proper authentication layer so data.json isn't world-readable, and a multi-turn advisor that lets the owner ask follow-up questions about specific recommendations.