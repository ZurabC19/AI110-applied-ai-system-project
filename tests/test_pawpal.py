"""
tests/test_pawpal.py - Automated test suite for PawPal+
Run with: python -m pytest
"""

import pytest
import json
import os
import tempfile
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def sample_owner():
    owner = Owner(name="Test Owner", email="test@example.com")
    dog = Pet(name="Rex", species="Dog", breed="Husky", age=4)
    cat = Pet(name="Luna", species="Cat", breed="Persian", age=2)

    dog.add_task(Task(description="Walk",       time="09:00", frequency="daily",  priority=1, duration_minutes=30))
    dog.add_task(Task(description="Feeding",    time="07:00", frequency="daily",  priority=1, duration_minutes=10))
    dog.add_task(Task(description="Medication", time="08:00", frequency="weekly", priority=1, duration_minutes=5))

    cat.add_task(Task(description="Feeding",    time="07:00", frequency="daily",  priority=1, duration_minutes=10))  # conflict
    cat.add_task(Task(description="Playtime",   time="15:00", frequency="daily",  priority=3, duration_minutes=20))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


@pytest.fixture
def scheduler(sample_owner):
    return Scheduler(sample_owner)


# ── Task Tests ─────────────────────────────────────────────────────────────

class TestTask:

    def test_mark_complete_changes_status(self):
        task = Task(description="Walk", time="09:00", frequency="once")
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_daily_task_recurrence(self):
        today = date.today()
        task = Task(description="Feeding", time="08:00", frequency="daily", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False

    def test_weekly_task_recurrence(self):
        today = date.today()
        task = Task(description="Bath", time="10:00", frequency="weekly", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_once_task_no_recurrence(self):
        task = Task(description="Vet Visit", time="14:00", frequency="once")
        assert task.mark_complete() is None

    def test_recurrence_preserves_attributes(self):
        task = Task(description="Walk", time="09:00", frequency="daily", priority=1, duration_minutes=45)
        next_task = task.mark_complete()
        assert next_task.priority == 1
        assert next_task.duration_minutes == 45
        assert next_task.time == "09:00"

    def test_serialization_round_trip(self):
        today = date.today()
        task = Task(description="Walk", time="09:00", frequency="daily", priority=1,
                    duration_minutes=30, due_date=today, completed=False)
        restored = Task.from_dict(task.to_dict())
        assert restored.description == task.description
        assert restored.due_date == task.due_date
        assert restored.priority == task.priority


# ── Pet Tests ──────────────────────────────────────────────────────────────

class TestPet:

    def test_add_task_increases_count(self):
        pet = Pet(name="Buddy", species="Dog")
        assert len(pet.tasks) == 0
        pet.add_task(Task(description="Walk", time="09:00", frequency="daily"))
        assert len(pet.tasks) == 1

    def test_remove_task_decreases_count(self):
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(Task(description="Walk", time="09:00", frequency="daily"))
        assert pet.remove_task("Walk") is True
        assert len(pet.tasks) == 0

    def test_remove_nonexistent_task_returns_false(self):
        pet = Pet(name="Buddy", species="Dog")
        assert pet.remove_task("FlyToMoon") is False

    def test_get_pending_tasks_excludes_completed(self):
        pet = Pet(name="Buddy", species="Dog")
        t1 = Task(description="Walk",    time="09:00", frequency="daily")
        t2 = Task(description="Feeding", time="07:00", frequency="daily")
        t2.completed = True
        pet.add_task(t1)
        pet.add_task(t2)
        assert len(pet.get_pending_tasks()) == 1

    def test_pet_serialization_round_trip(self):
        pet = Pet(name="Max", species="Dog", breed="Poodle", age=3)
        pet.add_task(Task(description="Walk", time="09:00", frequency="daily"))
        restored = Pet.from_dict(pet.to_dict())
        assert restored.name == "Max"
        assert len(restored.tasks) == 1


# ── Scheduler Tests ────────────────────────────────────────────────────────

class TestScheduler:

    def test_sort_by_time_is_chronological(self, scheduler):
        times = [t.time for _, t in scheduler.sort_by_time()]
        assert times == sorted(times)

    def test_conflict_detection_flags_duplicate_times(self, scheduler):
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) > 0
        assert any("07:00" in c for c in conflicts)

    def test_no_conflict_when_times_differ(self):
        owner = Owner("Solo")
        dog = Pet(name="Max", species="Dog")
        dog.add_task(Task(description="Walk",    time="08:00", frequency="daily"))
        dog.add_task(Task(description="Feeding", time="09:00", frequency="daily"))
        owner.add_pet(dog)
        assert Scheduler(owner).detect_conflicts() == []

    def test_filter_by_pet_returns_correct_tasks(self, scheduler):
        luna_tasks = scheduler.filter_by_pet("Luna")
        assert len(luna_tasks) == 2
        assert all(isinstance(t, Task) for t in luna_tasks)

    def test_filter_pending_excludes_completed(self, scheduler):
        pending = scheduler.filter_by_status(completed=False)
        assert all(not t.completed for _, t in pending)

    def test_mark_task_complete_adds_recurrence(self, scheduler):
        dog = next(p for p in scheduler.owner.pets if p.name == "Rex")
        initial_count = len(dog.tasks)
        msg = scheduler.mark_task_complete("Rex", "Walk")
        assert "marked complete" in msg
        assert len(dog.tasks) == initial_count + 1

    def test_mark_task_not_found_returns_error(self, scheduler):
        msg = scheduler.mark_task_complete("Rex", "FlyToMoon")
        assert "❌" in msg

    def test_empty_owner_returns_no_tasks(self):
        s = Scheduler(Owner("Empty"))
        assert s.get_all_tasks() == []
        assert s.detect_conflicts() == []

    def test_filter_by_priority(self, scheduler):
        high = scheduler.filter_by_priority(1)
        assert all(t.priority == 1 for _, t in high)

    def test_sort_by_priority_ordering(self, scheduler):
        priorities = [t.priority for _, t in scheduler.sort_by_priority()]
        assert priorities == sorted(priorities)

    def test_next_available_slot_not_in_occupied(self, scheduler):
        occupied = {task.time for _, task in scheduler.get_all_tasks()}
        slot = scheduler.next_available_slot()
        assert slot is not None
        assert slot not in occupied

    def test_weighted_priority_score(self):
        owner = Owner("W")
        s = Scheduler(owner)
        t_high = Task(description="Med",  time="08:00", frequency="daily", priority=1, duration_minutes=5)
        t_low  = Task(description="Play", time="15:00", frequency="daily", priority=3, duration_minutes=5)
        assert s.weighted_priority_score(t_high) < s.weighted_priority_score(t_low)


# ── Persistence Tests ──────────────────────────────────────────────────────

class TestPersistence:

    def test_save_and_load_json(self, sample_owner):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            sample_owner.save_to_json(path)
            loaded = Owner.load_from_json(path)
            assert loaded.name == sample_owner.name
            assert len(loaded.pets) == len(sample_owner.pets)
            original_tasks = sum(len(p.tasks) for p in sample_owner.pets)
            loaded_tasks   = sum(len(p.tasks) for p in loaded.pets)
            assert loaded_tasks == original_tasks
        finally:
            os.unlink(path)

    def test_load_nonexistent_file_returns_none(self):
        result = Owner.load_from_json("/tmp/does_not_exist_pawpal.json")
        assert result is None