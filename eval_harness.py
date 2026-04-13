"""
eval_harness.py - Test harness for PawPal+ AI Advisor
Runs the advisor against predefined schedules and prints a pass/fail summary.
Run with: python eval_harness.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler
from pawpal_advisor import PawPalAdvisor

PASS = "PASS"
FAIL = "FAIL"
results = []


def run_test(name: str, owner: Owner, checks: list[tuple[str, callable]]) -> None:
    """Run advisor on owner and evaluate each check function against the output."""
    print(f"\n{'─'*55}")
    print(f"  Test: {name}")
    print(f"{'─'*55}")
    try:
        advisor = PawPalAdvisor(owner, verbose=False)
        result = advisor.run()
        advice = result["advice"].lower()
        steps = result["steps"]

        for check_name, check_fn in checks:
            try:
                passed = check_fn(advice, steps, result["context"])
                status = PASS if passed else FAIL
            except Exception as e:
                status = FAIL
                check_name += f" (error: {e})"
            results.append((name, check_name, status))
            print(f"  [{status}] {check_name}")

    except Exception as e:
        results.append((name, "advisor_run", FAIL))
        print(f"  [FAIL] Advisor failed to run: {e}")


# ── Test 1: Conflict detection advice ─────────────────────────────────────
def make_conflict_owner():
    owner = Owner("Alex")
    dog = Pet("Buddy", "Dog", age=3)
    cat = Pet("Whiskers", "Cat", age=5)
    dog.add_task(Task("Morning Feeding", "07:30", "daily", priority=1, duration_minutes=10))
    cat.add_task(Task("Morning Feeding", "07:30", "daily", priority=1, duration_minutes=10))
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner

run_test(
    "Conflict Schedule",
    make_conflict_owner(),
    [
        ("3 agent steps recorded",      lambda a, s, c: len(s) == 3),
        ("Step 1 is Plan",              lambda a, s, c: "Plan" in s[0]["step"]),
        ("Step 2 is Retrieve",          lambda a, s, c: "Retrieve" in s[1]["step"]),
        ("Step 3 is Advise",            lambda a, s, c: "Advise" in s[2]["step"]),
        ("Conflict mentioned in advice", lambda a, s, c: "conflict" in a or "07:30" in a),
        ("Owner name in advice",        lambda a, s, c: "alex" in a),
        ("Context has conflicts",       lambda a, s, c: len(c["conflicts"]) > 0),
    ]
)

# ── Test 2: Empty schedule ─────────────────────────────────────────────────
def make_empty_owner():
    owner = Owner("Sam")
    owner.add_pet(Pet("Max", "Dog", age=2))
    return owner

run_test(
    "Empty Schedule",
    make_empty_owner(),
    [
        ("3 agent steps recorded",  lambda a, s, c: len(s) == 3),
        ("Zero tasks in context",   lambda a, s, c: c["total_tasks"] == 0),
        ("Advice is non-empty",     lambda a, s, c: len(a) > 50),
    ]
)

# ── Test 3: High priority tasks ────────────────────────────────────────────
def make_high_priority_owner():
    owner = Owner("Jordan")
    dog = Pet("Rocky", "Dog", age=7)
    dog.add_task(Task("Medication",  "08:00", "daily",  priority=1, duration_minutes=5))
    dog.add_task(Task("Vet Checkup", "14:00", "once",   priority=1, duration_minutes=60))
    dog.add_task(Task("Walk",        "17:00", "daily",  priority=2, duration_minutes=30))
    owner.add_pet(dog)
    return owner

run_test(
    "High Priority Tasks",
    make_high_priority_owner(),
    [
        ("3 agent steps recorded",       lambda a, s, c: len(s) == 3),
        ("High priority flagged in plan", lambda a, s, c: "high-priority" in s[0]["detail"].lower()),
        ("Advice mentions medication or vet", lambda a, s, c: "medication" in a or "vet" in a or "checkup" in a),
        ("No conflicts in context",      lambda a, s, c: len(c["conflicts"]) == 0),
    ]
)

# ── Summary ────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print("  Evaluation Summary")
print(f"{'='*55}")
passed = sum(1 for _, _, s in results if s == PASS)
total  = len(results)
for test, check, status in results:
    print(f"  [{status}] {test} / {check}")
print(f"\n  Result: {passed}/{total} checks passed")
confidence = passed / total if total > 0 else 0
print(f"  Confidence score: {confidence:.2f}")
print(f"{'='*55}")