# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

The backend lives in `pawpal_system.py`, with the UML in `diagrams/uml.mmd`. `main.py` runs it in the terminal, and `tests/test_pawpal.py` covers it with pytest.

**How the classes work together**

- `Owner` holds the day's constraints (available minutes, start time) and a list of `Pet`s. `Owner.get_pending_tasks()` gathers every incomplete task across all pets.
- `Pet` holds its own `Task`s. `add_task` tags each task with the pet's name, so a task still knows whose it is after the tasks are combined.
- `Task` is a single activity: title, duration, `Priority`, `Frequency`, optional preferred time, and completion status.
- `Scheduler` reads tasks only through the `Owner`, never from a single pet, so it plans across all pets at once. It sorts by priority, then preferred time, then shortest duration, and fits tasks into the available time from the start of the day. Tasks that don't fit are skipped, and scheduling continues with the rest.
- `DailyPlan` is the result. It holds `ScheduledItem`s (task, start time, reason) and `SkippedItem`s (task, reason). `explain()` turns it into readable text.

**Known simplifications**

- Preferred time only breaks ties. Tasks are packed back to back from the start of the day rather than placed at their preferred time.
- Recurring tasks (daily or weekly) are marked but not yet reset automatically.

**Run it**

```bash
python main.py   # prints today's schedule
pytest           # runs the tests
```

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
Owner: Jordan (90 min available, starting 08:00)
  Mochi (dog): 2 tasks
  Luna (cat): 3 tasks

=== Today's Schedule ===
08:00 - Breakfast for Luna (10 min, high): high priority
08:10 - Morning walk for Mochi (30 min, high): high priority
08:40 - Play session for Luna (20 min, medium): medium priority
09:00 - Litter box for Luna (5 min, medium): medium priority
Skipped - Grooming for Mochi: needs 45 min but only 25 min left
Total scheduled time: 65 min
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
