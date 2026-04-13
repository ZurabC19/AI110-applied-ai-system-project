"""
pawpal_system.py
Core backend logic for PawPal+.
Contains the Owner, Pet, Task, and Scheduler classes.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional
import json
import os


@dataclass
class Task:
    """Represents a single pet care task (e.g., feeding, walk, medication)."""

    description: str
    time: str                        # "HH:MM" format, e.g. "08:00"
    frequency: str                   # "once", "daily", or "weekly"
    priority: int = 2                # 1 = high, 2 = medium, 3 = low
    duration_minutes: int = 30
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete. Returns next occurrence if recurring."""
        self.completed = True
        if self.frequency == "daily":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                priority=self.priority,
                duration_minutes=self.duration_minutes,
                due_date=self.due_date + timedelta(days=1),
                completed=False,
            )
        elif self.frequency == "weekly":
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                priority=self.priority,
                duration_minutes=self.duration_minutes,
                due_date=self.due_date + timedelta(weeks=1),
                completed=False,
            )
        return None

    def to_dict(self) -> dict:
        """Serialize task to a JSON-compatible dictionary."""
        return {
            "description": self.description,
            "time": self.time,
            "frequency": self.frequency,
            "priority": self.priority,
            "duration_minutes": self.duration_minutes,
            "due_date": self.due_date.isoformat(),
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Deserialize a Task from a dictionary."""
        return cls(
            description=data["description"],
            time=data["time"],
            frequency=data["frequency"],
            priority=data.get("priority", 2),
            duration_minutes=data.get("duration_minutes", 30),
            due_date=date.fromisoformat(data["due_date"]),
            completed=data.get("completed", False),
        )

    def __str__(self) -> str:
        status = "✅" if self.completed else "⏳"
        priority_label = {1: "High", 2: "Medium", 3: "Low"}.get(self.priority, "Medium")
        return (
            f"{status} [{self.time}] {self.description} "
            f"({self.duration_minutes} min | {priority_label} priority | {self.frequency})"
        )


@dataclass
class Pet:
    """Represents a pet belonging to an owner."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove a task by description. Returns True if removed."""
        for task in self.tasks:
            if task.description.lower() == description.lower():
                self.tasks.remove(task)
                return True
        return False

    def get_pending_tasks(self) -> List[Task]:
        """Return only incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def to_dict(self) -> dict:
        """Serialize pet to a JSON-compatible dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Deserialize a Pet from a dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            breed=data.get("breed", ""),
            age=data.get("age", 0),
        )
        pet.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return pet

    def __str__(self) -> str:
        return f"{self.name} ({self.species}{', ' + self.breed if self.breed else ''}, age {self.age})"


class Owner:
    """Represents the pet owner who manages one or more pets."""

    def __init__(self, name: str, email: str = ""):
        """Initialize an Owner with a name and optional email."""
        self.name = name
        self.email = email
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's profile."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name. Returns True if removed."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                self.pets.remove(pet)
                return True
        return False

    def get_all_tasks(self) -> List[tuple]:
        """Return all (pet_name, task) tuples across all pets."""
        result = []
        for pet in self.pets:
            for task in pet.tasks:
                result.append((pet.name, task))
        return result

    def to_dict(self) -> dict:
        """Serialize owner to a JSON-compatible dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Deserialize an Owner from a dictionary."""
        owner = cls(name=data["name"], email=data.get("email", ""))
        owner.pets = [Pet.from_dict(p) for p in data.get("pets", [])]
        return owner

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Persist the owner's full data (pets + tasks) to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> Optional["Owner"]:
        """Load an Owner from a JSON file. Returns None if file not found."""
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r") as f:
            return cls.from_dict(json.load(f))

    def __str__(self) -> str:
        return f"Owner: {self.name} | Pets: {len(self.pets)}"


class Scheduler:
    """The brain of PawPal+. Sorts, filters, and validates tasks."""

    def __init__(self, owner: Owner):
        """Initialize the Scheduler with an Owner instance."""
        self.owner = owner

    def get_all_tasks(self) -> List[tuple]:
        """Return all (pet_name, task) pairs from the owner."""
        return self.owner.get_all_tasks()

    # ── Sorting ────────────────────────────────────────────────────────────

    def sort_by_time(self) -> List[tuple]:
        """Return all tasks sorted chronologically, then by priority for ties."""
        return sorted(self.get_all_tasks(), key=lambda x: (x[1].time, x[1].priority))

    def sort_by_priority(self) -> List[tuple]:
        """Return all tasks sorted by priority first, then by time."""
        return sorted(self.get_all_tasks(), key=lambda x: (x[1].priority, x[1].time))

    # ── Filtering ──────────────────────────────────────────────────────────

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return all tasks for a specific pet."""
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                return pet.tasks
        return []

    def filter_by_status(self, completed: bool) -> List[tuple]:
        """Filter tasks by completion status."""
        return [(n, t) for n, t in self.get_all_tasks() if t.completed == completed]

    def filter_by_priority(self, priority: int) -> List[tuple]:
        """Return tasks matching a specific priority level (1=High, 2=Med, 3=Low)."""
        return [(n, t) for n, t in self.get_all_tasks() if t.priority == priority]

    # ── Conflict Detection ─────────────────────────────────────────────────

    def detect_conflicts(self) -> List[str]:
        """
        Detect tasks scheduled at the exact same time.
        Returns one warning per conflicting time slot (not one per duplicate pair).
        Tradeoff: only checks exact HH:MM matches, not overlapping durations.
        """
        from collections import defaultdict
        slots: dict = defaultdict(list)
        for pet_name, task in self.get_all_tasks():
            slots[task.time].append((pet_name, task.description))

        warnings: List[str] = []
        for time_slot, entries in sorted(slots.items()):
            if len(entries) > 1:
                names = ", ".join(f"'{desc}' ({pet})" for pet, desc in entries)
                warnings.append(f"⚠️ Conflict at {time_slot}: {names}")
        return warnings

    # ── Task Completion + Recurrence ───────────────────────────────────────

    def mark_task_complete(self, pet_name: str, task_description: str) -> str:
        """
        Mark a task complete. Auto-schedules next occurrence if recurring.
        Returns a status message string.
        """
        for pet in self.owner.pets:
            if pet.name.lower() == pet_name.lower():
                for task in pet.tasks:
                    if task.description.lower() == task_description.lower() and not task.completed:
                        next_task = task.mark_complete()
                        if next_task:
                            pet.add_task(next_task)
                            return (
                                f"✅ '{task.description}' marked complete. "
                                f"Next occurrence added for {next_task.due_date}."
                            )
                        return f"✅ '{task.description}' marked complete (one-time task)."
        return f"❌ Task not found for {pet_name}."

    # ── Next Available Slot (Stretch Feature) ──────────────────────────────

    def next_available_slot(self, duration_minutes: int = 30) -> Optional[str]:
        """
        Find the next time slot (on the hour or half-hour, 07:00-21:00)
        that has no existing task. Returns HH:MM string or None.
        """
        occupied = {task.time for _, task in self.get_all_tasks()}
        for hour in range(7, 22):
            for minute in (0, 30):
                slot = f"{hour:02d}:{minute:02d}"
                if slot not in occupied:
                    return slot
        return None

    # ── Weighted Priority Score (Stretch Feature) ──────────────────────────

    def weighted_priority_score(self, task: "Task") -> float:
        """
        Compute a composite urgency score. Lower = more urgent.
        Formula: priority * 10 - duration_minutes * 0.1
        """
        return task.priority * 10 - task.duration_minutes * 0.1

    def sort_by_weighted_priority(self) -> List[tuple]:
        """Return tasks sorted by weighted priority score (most urgent first)."""
        return sorted(
            self.get_all_tasks(),
            key=lambda x: (self.weighted_priority_score(x[1]), x[1].time),
        )

    # ── Daily Plan ─────────────────────────────────────────────────────────

    def generate_daily_plan(self) -> str:
        """Generate a formatted daily schedule with conflict warnings."""
        sorted_tasks = self.sort_by_time()
        conflicts = self.detect_conflicts()
        lines = ["=" * 55, "🐾  PawPal+ Daily Schedule", "=" * 55]
        if not sorted_tasks:
            lines.append("  No tasks scheduled.")
        else:
            for pet_name, task in sorted_tasks:
                lines.append(f"  [{pet_name}] {task}")
        if conflicts:
            lines.append("")
            lines.append("⚠️  CONFLICTS DETECTED:")
            for w in conflicts:
                lines.append(f"  {w}")
        lines.append("=" * 55)
        return "\n".join(lines)