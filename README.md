# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

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
- `Scheduler` reads tasks only through the `Owner`, never from a single pet, so it plans across all pets at once. It places tasks by priority at their preferred times, shifts any that clash, and skips what doesn't fit. See [Smarter Scheduling](#-smarter-scheduling).
- `DailyPlan` is the result. It holds `ScheduledItem`s (task, start time, reason) and `SkippedItem`s (task, reason). `explain()` turns it into readable text.

**Known simplifications**

- `build_plan` ignores `Task.due_date`, so tasks due on a future date (for example the next occurrence of a daily task) are still scheduled today.
- Only task durations count against `available_minutes`. Idle gaps between tasks are free.
- A task that gets shifted is never moved earlier than its preferred time, only later.

**Run it**

```bash
python main.py   # prints today's schedule
pytest           # runs the tests
```

## 🖥️ Sample Output

Output of `python main.py`. Tasks are added out of order, then sorted, filtered, checked for conflicts, and scheduled. The dates in the recurring section depend on the day you run it.

```
Owner: Jordan (90 min available, starting 08:00)
  Mochi (dog): 5 tasks
  Luna (cat): 5 tasks

=== As added (out of order) ===
  --:--  Grooming       Mochi  done
  08:00  Morning walk   Mochi  todo
  17:00  Evening meal   Mochi  todo
  08:10  Brush teeth    Mochi  todo
  12:00  Medication     Mochi  todo
  18:00  Play session   Luna   todo
  --:--  litter box     Luna   todo
  07:30  Breakfast      Luna   todo
  08:15  Vet call       Luna   todo
  12:00  Training       Luna   todo

=== Sorted by title ===
  07:30  Breakfast      Luna   todo
  08:10  Brush teeth    Mochi  todo
  17:00  Evening meal   Mochi  todo
  --:--  Grooming       Mochi  done
  --:--  litter box     Luna   todo
  12:00  Medication     Mochi  todo
  08:00  Morning walk   Mochi  todo
  18:00  Play session   Luna   todo
  12:00  Training       Luna   todo
  08:15  Vet call       Luna   todo

=== Sorted by preferred time ===
  07:30  Breakfast      Luna   todo
  08:00  Morning walk   Mochi  todo
  08:10  Brush teeth    Mochi  todo
  08:15  Vet call       Luna   todo
  12:00  Medication     Mochi  todo
  12:00  Training       Luna   todo
  17:00  Evening meal   Mochi  todo
  18:00  Play session   Luna   todo
  --:--  Grooming       Mochi  done
  --:--  litter box     Luna   todo

=== Filter: Luna's tasks ===
  18:00  Play session   Luna   todo
  --:--  litter box     Luna   todo
  07:30  Breakfast      Luna   todo
  08:15  Vet call       Luna   todo
  12:00  Training       Luna   todo

=== Filter: completed ===
  --:--  Grooming       Mochi  done

=== Filter: Mochi + pending ===
  08:00  Morning walk   Mochi  todo
  17:00  Evening meal   Mochi  todo
  08:10  Brush teeth    Mochi  todo
  12:00  Medication     Mochi  todo

=== Luna's tasks, sorted by time ===
  07:30  Breakfast      Luna   todo
  08:15  Vet call       Luna   todo
  12:00  Training       Luna   todo
  18:00  Play session   Luna   todo
  --:--  litter box     Luna   todo

=== Conflict check ===
  Warning: Conflict (same pet): Morning walk for Mochi and Brush teeth for Mochi overlap 08:10-08:20
  Warning: Conflict (different pets): Morning walk for Mochi and Vet call for Luna overlap 08:15-08:30
  Warning: Conflict (different pets): Brush teeth for Mochi and Vet call for Luna overlap 08:15-08:20
  Warning: Conflict (different pets): Medication for Mochi and Training for Luna overlap 12:00-12:05

=== Recurring: complete a daily and a weekly task ===
  before: Mochi has 5 tasks
  completed 'Morning walk' (daily, due 2026-10-19) -> new one due 2026-10-20
  completed 'Grooming' (weekly, due 2026-10-19) -> new one due 2026-10-26
  after:  Mochi has 7 tasks

=== Today's Schedule ===
08:00 - Breakfast for Luna (10 min, high): high priority; preferred 07:30 is before the day starts
08:10 - Morning walk for Mochi (30 min, high): high priority; moved from preferred 08:00 because Breakfast for Luna was already scheduled
08:40 - Brush teeth for Mochi (10 min, medium): medium priority; moved from preferred 08:10 because Morning walk for Mochi was already scheduled
08:50 - Vet call for Luna (20 min, medium): medium priority; moved from preferred 08:15 because Brush teeth for Mochi was already scheduled
09:10 - litter box for Luna (5 min, medium): medium priority; first free slot after Vet call for Luna
12:00 - Medication for Mochi (5 min, high): high priority; at preferred time
17:00 - Evening meal for Mochi (10 min, high): high priority; at preferred time
Skipped - Training for Luna: needs 15 min but only 5 min left
Skipped - Play session for Luna: needs 20 min but only 5 min left
Skipped - Grooming for Mochi: needs 45 min but only 0 min left
Total scheduled time: 90 min
```

## 🧪 Testing PawPal+

Run the full test suite from the `pawpal/` directory:

```bash
python -m pytest
```

Successful run:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.8, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/anniesoonyadeth/Documents/codepath-AI101/pawpal
plugins: anyio-4.15.1
collected 23 items

tests/test_pawpal.py .......................                             [100%]

============================== 23 passed in 0.01s ==============================
```

**What the tests cover** (`tests/test_pawpal.py`):

- **Sorting correctness:** tasks come back in chronological order (9:00 before 17:00), unscheduled tasks go last, ties keep their original order, empty lists are safe, and built plans are in start-time order.
- **Recurrence logic:** completing a daily task creates a new task for the next day, a weekly task creates one 7 days later, and a one-off task creates nothing.
- **Conflict detection:** duplicate or overlapping times are flagged for the same pet and across pets. Back-to-back, unscheduled, different-day, and completed tasks are not flagged. Warnings are returned as messages instead of raising errors, even with bad data.
- **Plan building:** preferred times are honored, lower-priority tasks shift past conflicts, gaps are filled, tasks that can't finish before midnight are skipped, and plans never overlap.
- **Basics:** marking a task complete and adding tasks to a pet.

**Confidence Level: ⭐⭐⭐⭐ (4/5)**

All 23 tests pass and cover the core behaviors: sorting, recurrence, and conflict detection. I'm not giving 5 stars because some cases are untested: month, year and leap-year rollover for daily recurrence (it always uses `date.today()`), daylight saving time, task durations that overlap across midnight, and the Streamlit UI.

## 📐 Smarter Scheduling

All of these live in `pawpal_system.py` and are demonstrated by `python main.py`.

| Feature | Method(s) | What it does |
|---------|-----------|--------------|
| Sorting | `Scheduler.sort_by_title()`, `Scheduler.sort_by_time()`, `Scheduler._sort_tasks()` | Order tasks for display or scheduling |
| Filtering | `Scheduler.filter_tasks()` | Keep tasks by pet and/or completion status |
| Conflict detection | `Scheduler.find_conflicts()`, `Scheduler.find_plan_conflicts()`, `Scheduler.conflict_warnings()` | Find overlapping time slots and report them as warnings |
| Conflict resolution | `Scheduler.build_plan()` | Honors preferred times and moves clashing tasks to the next free slot |
| Recurring tasks | `Task.next_occurrence()`, `Task.mark_complete()`, `Scheduler.complete_task()` | Creates the next daily or weekly instance when a task is completed |

### Sorting

- `sort_by_title(tasks)` sorts alphabetically, ignoring case, so "litter box" sorts between "Grooming" and "Morning walk" instead of after every capitalized title.
- `sort_by_time(tasks)` sorts by `preferred_minute`, earliest first. Tasks with no preferred time go last.
- `_sort_tasks(tasks)` is what `build_plan` uses: highest priority first, then earliest preferred time, then shortest duration. Python's sort is stable, so ties keep the owner's pet order.

### Filtering

`filter_tasks(tasks, pet_name=None, completed=None)` keeps tasks that match every criterion you pass. A criterion left as `None` is ignored, so `filter_tasks(tasks, pet_name="Luna")` returns all of Luna's tasks and `filter_tasks(tasks, pet_name="Mochi", completed=False)` returns Mochi's pending ones. The result is a list, so it chains with the sorts: `sort_by_time(filter_tasks(...))`.

### Conflict detection

Two tasks conflict when their time ranges overlap, whether they belong to the same pet or different pets. A task occupies `[start, start + duration)`, so back-to-back tasks (one ends at 08:30, the next starts at 08:30) do not conflict.

- `find_conflicts(tasks=None)` checks pending tasks that have a `preferred_minute`. It returns `Conflict` objects (both tasks, the overlap window, and `same_pet`).
- `find_plan_conflicts(plan)` runs the same check on a built `DailyPlan`, using the scheduled start times.
- `conflict_warnings(tasks=None)` is the lightweight version: it returns plain strings such as `Warning: Conflict (different pets): Medication for Mochi and Training for Luna overlap 12:00-12:05`. It never raises. If the check itself fails, it returns a "could not check for conflicts" warning instead of crashing.

Detection groups tasks by `due_date` (tasks on different days never conflict), sorts each day by start time, and stops comparing a task as soon as the next one starts after it ends. Completed tasks and tasks with no preferred time are ignored.

### Conflict resolution in the plan

`build_plan()` places tasks in priority order. Each goes at its preferred time, or the day start if it has none. If a higher-priority task already holds that slot, it moves to the next free slot and the plan's reason text says why (for example `moved from preferred 08:15 because Brush teeth for Mochi was already scheduled`). A task is skipped if it needs more time than is left, or can't finish before midnight. Because of this, `find_plan_conflicts()` on a plan built by `build_plan()` always comes back empty.

### Recurring tasks

Tasks carry a `frequency` (`ONCE`, `DAILY`, `WEEKLY`) and a `due_date`.

- `Task.next_occurrence()` returns a fresh, incomplete copy with a new id, or `None` for a one-off task. A daily task is due tomorrow (`today + 1 day`). A weekly task is due 7 days after the completed task's `due_date`.
- `Task.mark_complete()` marks the task done and returns the next occurrence, but does not attach it to a pet.
- `Scheduler.complete_task(task)` is the one to call in the app: it marks the task complete and adds the next occurrence to the same pet.

Completing the same task twice creates two next occurrences, as nothing guards against it.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
