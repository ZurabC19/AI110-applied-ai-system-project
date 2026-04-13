"""
pawpal_advisor.py
Agentic AI advisor for PawPal+.
Uses Groq (llama-3.1-8b-instant) to analyze the current schedule.

Three observable steps:
  Step 1 - Plan: decide what to look at
  Step 2 - Retrieve: pull schedule data from the Scheduler
  Step 3 - Advise: send context to Groq and return recommendations
"""

import os
import json
from datetime import date
from groq import Groq
from pawpal_system import Owner, Scheduler


def _load_api_key() -> str:
    """Load Groq API key from environment or .env file."""
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        break
    if not key:
        raise ValueError("GROQ_API_KEY not found. Add it to your .env file.")
    return key


class PawPalAdvisor:
    """
    Agentic AI advisor that analyzes a PawPal+ schedule and returns
    structured recommendations with observable intermediate steps.
    """

    MODEL = "llama-3.1-8b-instant"

    def __init__(self, owner: Owner, verbose: bool = True):
        """Initialize with an Owner instance and configure the Groq client."""
        self.owner = owner
        self.scheduler = Scheduler(owner)
        self.verbose = verbose
        self.client = Groq(api_key=_load_api_key())
        self.steps: list = []

    def _log(self, step: str, detail: str) -> None:
        """Record and optionally print an agent step."""
        entry = {"step": step, "detail": detail}
        self.steps.append(entry)
        if self.verbose:
            print(f"\n[Agent] {step}")
            print(f"  {detail}")

    def _plan(self) -> str:
        """Step 1: Decide what aspects of the schedule to analyze."""
        pets = [p.name for p in self.owner.pets]
        total = len(self.scheduler.get_all_tasks())
        conflicts = self.scheduler.detect_conflicts()

        focus_areas = []
        if conflicts:
            focus_areas.append(f"{len(conflicts)} scheduling conflict(s) detected")
        if total == 0:
            focus_areas.append("no tasks scheduled yet")
        else:
            focus_areas.append(f"{total} tasks across {len(pets)} pet(s)")

        high_priority = self.scheduler.filter_by_priority(1)
        if high_priority:
            focus_areas.append(f"{len(high_priority)} high-priority task(s)")

        plan = f"Analyzing schedule for {', '.join(pets)}. Focus: {'; '.join(focus_areas)}."
        self._log("Step 1 - Plan", plan)
        return plan

    def _retrieve(self) -> dict:
        """Step 2: Pull all relevant schedule data into a structured context object."""
        all_tasks = self.scheduler.get_all_tasks()
        conflicts = self.scheduler.detect_conflicts()
        pending = self.scheduler.filter_by_status(completed=False)
        next_slot = self.scheduler.next_available_slot()

        context = {
            "owner": self.owner.name,
            "today": date.today().isoformat(),
            "pets": [
                {
                    "name": p.name,
                    "species": p.species,
                    "age": p.age,
                    "task_count": len(p.tasks),
                    "pending_count": len(p.get_pending_tasks()),
                }
                for p in self.owner.pets
            ],
            "total_tasks": len(all_tasks),
            "pending_tasks": len(pending),
            "conflicts": conflicts,
            "next_available_slot": next_slot,
            "schedule": [
                {
                    "pet": pet_name,
                    "task": task.description,
                    "time": task.time,
                    "frequency": task.frequency,
                    "priority": {1: "High", 2: "Medium", 3: "Low"}.get(task.priority),
                    "duration_minutes": task.duration_minutes,
                    "completed": task.completed,
                }
                for pet_name, task in self.scheduler.sort_by_time()
            ],
        }

        self._log(
            "Step 2 - Retrieve",
            f"Collected {len(all_tasks)} tasks, {len(conflicts)} conflict(s), "
            f"next free slot: {next_slot or 'none'}",
        )
        return context

    def _advise(self, plan: str, context: dict) -> str:
        """Step 3: Send context to Groq and return structured recommendations."""
        prompt = f"""You are a helpful pet care scheduling assistant analyzing a pet owner's daily care plan.

Agent plan: {plan}

Current schedule data:
{json.dumps(context, indent=2)}

Give 3 to 5 specific, actionable recommendations based on this schedule. Focus on:
- Any scheduling conflicts that need resolving
- Tasks that seem missing for the pet's species and age
- Whether the workload is balanced across the day
- Any high-priority tasks that are incomplete
- General pet care advice based on what you see

Be direct and practical. Address the owner by name. Keep each recommendation to 2-3 sentences.
Format your response as a numbered list."""

        self._log("Step 3 - Advise", "Sending schedule context to Groq (llama-3.1-8b-instant) for analysis")

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()

    def run(self) -> dict:
        """Run the full three-step agent pipeline."""
        self.steps = []

        if self.verbose:
            print("\n" + "=" * 55)
            print("  PawPal+ AI Advisor")
            print("=" * 55)

        plan    = self._plan()
        context = self._retrieve()
        advice  = self._advise(plan, context)

        if self.verbose:
            print("\n" + "=" * 55)
            print("  AI Recommendations")
            print("=" * 55)
            print(advice)
            print("=" * 55)

        return {"steps": self.steps, "context": context, "advice": advice}

    def get_steps_summary(self) -> str:
        """Return a readable summary of the agent's intermediate steps."""
        if not self.steps:
            return "No steps recorded yet. Call run() first."
        return "\n".join(f"{s['step']}: {s['detail']}" for s in self.steps)