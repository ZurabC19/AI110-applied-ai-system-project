"""
main.py - CLI demo to verify backend logic works end-to-end.
Run with: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def separator(title: str = "") -> None:
    line = "─" * 55
    if title:
        print(f"\n{line}")
        print(f"  {title}")
        print(line)
    else:
        print(line)


def main():
    print("\n🐾  Welcome to PawPal+ CLI Demo\n")

    # ── Create Owner ───────────────────────────────────────
    owner = Owner(name="Alex Johnson", email="alex@example.com")

    # ── Create Pets ────────────────────────────────────────
    buddy = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
    whiskers = Pet(name="Whiskers", species="Cat", breed="Siamese", age=5)
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # ── Add Tasks (intentionally out of order to prove sorting) ───────────
    buddy.add_task(Task(description="Evening Walk",        time="18:00", frequency="daily",  priority=1, duration_minutes=45))
    buddy.add_task(Task(description="Morning Feeding",     time="07:30", frequency="daily",  priority=1, duration_minutes=10))
    buddy.add_task(Task(description="Heartworm Medication",time="08:00", frequency="weekly", priority=1, duration_minutes=5))
    buddy.add_task(Task(description="Grooming Appointment",time="14:00", frequency="once",   priority=2, duration_minutes=60))

    whiskers.add_task(Task(description="Morning Feeding",  time="07:30", frequency="daily",  priority=1, duration_minutes=10))  # conflict!
    whiskers.add_task(Task(description="Playtime",         time="11:00", frequency="daily",  priority=3, duration_minutes=20))
    whiskers.add_task(Task(description="Vet Checkup",      time="10:00", frequency="once",   priority=1, duration_minutes=60))

    # ── Scheduler ──────────────────────────────────────────
    scheduler = Scheduler(owner)

    # 1. Daily plan (sorted + conflict detection)
    print(scheduler.generate_daily_plan())

    # 2. Mark a recurring task complete
    separator("Marking 'Evening Walk' complete for Buddy")
    print(scheduler.mark_task_complete("Buddy", "Evening Walk"))

    # 3. Pending tasks after completion
    separator("Pending tasks after completion")
    for pet_name, task in scheduler.filter_by_status(completed=False):
        print(f"  [{pet_name}] {task}")

    # 4. Filter by pet
    separator("Whiskers' tasks only")
    for task in scheduler.filter_by_pet("Whiskers"):
        print(f"  {task}")

    # 5. Priority-first sort
    separator("Sort by priority (most urgent first)")
    for pet_name, task in scheduler.sort_by_priority():
        print(f"  [{pet_name}] {task}")

    # 6. Weighted priority sort (stretch feature)
    separator("Weighted priority sort (urgency score)")
    for pet_name, task in scheduler.sort_by_weighted_priority():
        score = scheduler.weighted_priority_score(task)
        print(f"  score={score:5.1f}  [{pet_name}] {task.description} @ {task.time}")

    # 7. Next available slot (stretch feature)
    separator("Next available 30-min slot")
    slot = scheduler.next_available_slot()
    print(f"  First free slot: {slot if slot else 'None found'}")

    # 8. Data persistence (stretch feature)
    separator("Saving data to data.json")
    owner.save_to_json("data.json")
    print("  Saved ✅")
    loaded = Owner.load_from_json("data.json")
    print(f"  Loaded back: {loaded} ({sum(len(p.tasks) for p in loaded.pets)} tasks)")

    print("\n✅  Demo complete.\n")


if __name__ == "__main__":
    main()