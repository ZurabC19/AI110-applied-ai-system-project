"""
main.py - CLI demo to verify backend logic works.
Run with: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    print("\n🐾 Welcome to PawPal+ CLI Demo\n")

    # Create Owner
    owner = Owner(name="Alex Johnson", email="alex@example.com")

    # Create Pets
    buddy = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
    whiskers = Pet(name="Whiskers", species="Cat", breed="Siamese", age=5)
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # Add Tasks (intentionally out of order to test sorting)
    buddy.add_task(Task(description="Evening Walk", time="18:00", frequency="daily", priority=1, duration_minutes=45))
    buddy.add_task(Task(description="Morning Feeding", time="07:30", frequency="daily", priority=1, duration_minutes=10))
    buddy.add_task(Task(description="Heartworm Medication", time="08:00", frequency="weekly", priority=1, duration_minutes=5))
    buddy.add_task(Task(description="Grooming Appointment", time="14:00", frequency="once", priority=2, duration_minutes=60))

    whiskers.add_task(Task(description="Morning Feeding", time="07:30", frequency="daily", priority=1, duration_minutes=10))  # conflict!
    whiskers.add_task(Task(description="Playtime", time="11:00", frequency="daily", priority=3, duration_minutes=20))
    whiskers.add_task(Task(description="Vet Checkup", time="10:00", frequency="once", priority=1, duration_minutes=60))

    # Create Scheduler
    scheduler = Scheduler(owner)

    # Print daily plan
    print(scheduler.generate_daily_plan())

    # Mark a task complete
    print("\n📋 Marking 'Evening Walk' complete for Buddy...\n")
    print(scheduler.mark_task_complete("Buddy", "Evening Walk"))

    # Show pending tasks
    print("\n📋 Pending tasks after completion:")
    for pet_name, task in scheduler.filter_by_status(completed=False):
        print(f"  [{pet_name}] {task}")


if __name__ == "__main__":
    main()