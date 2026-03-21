"""
pawpal_system.py
Core backend logic for PawPal+.
Contains the Owner, Pet, Task, and Scheduler classes.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


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

    def __str__(self) -> str:
        return f"{self.name} ({self.species}{', ' + self.breed if self.breed else ''}, age {self.age})"


class Owner:
    """Represents the pet owner who manages one or more pets."""

    def __init__(self, name: str, email: str = ""):
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

    def __str__(self) -> str:
        return f"Owner: {self.name} | Pets: {len(self.pets)}"


class Scheduler:
    """The brain of PawPal+. Sorts, filters, and validates tasks."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_all_tasks(self) -> List[tuple]:
        """Return all (pet_name, task) pairs from the owner."""
        return self.owner.get_all_tasks()

    def sort_by_time(self) -> List[tuple]:
        """Return all tasks sorted chronologically, then by priority."""
        return sorted(self.get_all_tasks(), key=lambda x: (x[1].time, x[1].priority))

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
        """Return tasks matching a specific priority level."""
        return [(n, t) for n, t in self.get_all_tasks() if t.priority == priority]

    def detect_conflicts(self) -> List[str]:
        """Detect tasks scheduled at the exact same time. Returns warning strings."""
        seen = {}
        warnings = []
        for pet_name, task in self.get_all_tasks():
            if task.time in seen:
                prev_pet, prev_desc = seen[task.time]
                warnings.append(
                    f"⚠️ Conflict at {task.time}: '{prev_desc}' ({prev_pet}) "
                    f"and '{task.description}' ({pet_name})"
                )
            else:
                seen[task.time] = (pet_name, task.description)
        return warnings

    def mark_task_complete(self, pet_name: str, task_description: str) -> str:
        """Mark a task complete. Auto-schedules next occurrence if recurring."""
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

    def generate_daily_plan(self) -> str:
        """Generate a formatted daily schedule with conflict warnings."""
        sorted_tasks = self.sort_by_time()
        conflicts = self.detect_conflicts()
        lines = ["=" * 50, "🐾 PawPal+ Daily Schedule", "=" * 50]
        if not sorted_tasks:
            lines.append("No tasks scheduled.")
        else:
            for pet_name, task in sorted_tasks:
                lines.append(f"  [{pet_name}] {task}")
        if conflicts:
            lines.append("")
            lines.append("⚠️  CONFLICTS DETECTED:")
            for w in conflicts:
                lines.append(f"  {w}")
        lines.append("=" * 50)
        return "\n".join(lines)