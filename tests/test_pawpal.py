"""
tests/test_pawpal.py - Automated test suite for PawPal+
Run with: python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


@pytest.fixture
def sample_owner():
    owner = Owner(name="Test Owner")
    dog = Pet(name="Rex", species="Dog")
    cat = Pet(name="Luna", species="Cat")

    dog.add_task(Task(description="Walk", time="09:00", frequency="daily", priority=1))
    dog.add_task(Task(description="Feeding", time="07:00", frequency="daily", priority=1))
    dog.add_task(Task(description="Medication", time="08:00", frequency="weekly", priority=1))

    cat.add_task(Task(description="Feeding", time="07:00", frequency="daily", priority=1))  # conflict
    cat.add_task(Task(description="Playtime", time="15:00", frequency="daily", priority=3))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


@pytest.fixture
def scheduler(sample_owner):
    return Scheduler(sample_owner)


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
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_once_task_no_recurrence(self):
        task = Task(description="Vet Visit", time="14:00", frequency="once")
        assert task.mark_complete() is None


class TestPet:

    def test_add_task_increases_count(self):
        pet = Pet(name="Buddy", species="Dog")
        assert len(pet.tasks) == 0
        pet.add_task(Task(description="Walk", time="09:00", frequency="daily"))
        assert len(pet.tasks) == 1

    def test_remove_task(self):
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(Task(description="Walk", time="09:00", frequency="daily"))
        assert pet.remove_task("Walk") is True
        assert len(pet.tasks) == 0

    def test_remove_nonexistent_task(self):
        pet = Pet(name="Buddy", species="Dog")
        assert pet.remove_task("FlyToMoon") is False

    def test_get_pending_tasks(self):
        pet = Pet(name="Buddy", species="Dog")
        t1 = Task(description="Walk", time="09:00", frequency="daily")
        t2 = Task(description="Feeding", time="07:00", frequency="daily")
        t2.completed = True
        pet.add_task(t1)
        pet.add_task(t2)
        assert len(pet.get_pending_tasks()) == 1


class TestScheduler:

    def test_sort_by_time_is_chronological(self, scheduler):
        times = [t.time for _, t in scheduler.sort_by_time()]
        assert times == sorted(times)

    def test_conflict_detection(self, scheduler):
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) > 0
        assert any("07:00" in c for c in conflicts)

    def test_no_conflict_when_times_differ(self):
        owner = Owner("Solo")
        dog = Pet(name="Max", species="Dog")
        dog.add_task(Task(description="Walk", time="08:00", frequency="daily"))
        dog.add_task(Task(description="Feeding", time="09:00", frequency="daily"))
        owner.add_pet(dog)
        assert Scheduler(owner).detect_conflicts() == []

    def test_filter_by_pet(self, scheduler):
        assert len(scheduler.filter_by_pet("Luna")) == 2

    def test_filter_pending_tasks(self, scheduler):
        pending = scheduler.filter_by_status(completed=False)
        assert all(not t.completed for _, t in pending)

    def test_mark_task_complete_and_recurrence(self, scheduler):
        dog = next(p for p in scheduler.owner.pets if p.name == "Rex")
        initial_count = len(dog.tasks)
        msg = scheduler.mark_task_complete("Rex", "Walk")
        assert "marked complete" in msg
        assert len(dog.tasks) == initial_count + 1

    def test_mark_task_not_found(self, scheduler):
        msg = scheduler.mark_task_complete("Rex", "FlyToMoon")
        assert "❌" in msg

    def test_empty_owner(self):
        s = Scheduler(Owner("Empty"))
        assert s.get_all_tasks() == []
        assert s.detect_conflicts() == []