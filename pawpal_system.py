from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from enum import Enum, IntEnum
from typing import Dict, List, Optional
from uuid import uuid4


MINUTES_PER_DAY = 24 * 60


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Task:
    """A single pet-care activity."""

    title: str
    duration_minutes: int
    priority: Priority
    description: str = ""
    frequency: Frequency = Frequency.ONCE
    preferred_minute: Optional[int] = None  # minutes since midnight; None = any time
    completed: bool = False
    due_date: date = field(default_factory=date.today)
    pet_name: str = ""  # set by Pet.add_task so a flattened task still knows its pet
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Reject non-positive durations and out-of-range preferred times."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.preferred_minute is not None and not 0 <= self.preferred_minute < 24 * 60:
            raise ValueError("preferred_minute must be between 0 and 1439")

    @property
    def is_recurring(self) -> bool:
        """True if the task repeats (daily or weekly)."""
        return self.frequency is not Frequency.ONCE

    def next_occurrence(self) -> Optional["Task"]:
        """A fresh, incomplete copy for the next occurrence, or None if one-off.

        Daily tasks are due tomorrow (today + 1 day); weekly tasks are due 7 days
        after this task's due date.
        """
        if self.frequency is Frequency.DAILY:
            next_due = date.today() + timedelta(days=1)
        elif self.frequency is Frequency.WEEKLY:
            next_due = self.due_date + timedelta(weeks=1)
        else:
            return None
        return replace(self, completed=False, due_date=next_due, id=uuid4().hex)

    def mark_complete(self) -> Optional["Task"]:
        """Mark the task as done; return the next occurrence if it recurs.

        The returned task is not attached to any pet. Use Scheduler.complete_task
        to have it added to the pet automatically.
        """
        self.completed = True
        return self.next_occurrence()

    def reset(self) -> None:
        """Clear completion so a recurring task can be scheduled again."""
        self.completed = False


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet and tag it with the pet's name."""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"Task {task.id} is already assigned to {self.name}")
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id, or raise KeyError."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                return
        raise KeyError(f"No task with id {task_id} for {self.name}")

    def get_pending_tasks(self) -> List[Task]:
        """Return this pet's tasks that aren't completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    day_start_minute: int = 8 * 60  # minutes since midnight; plan starts here
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet, rejecting duplicate names."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove the pet with the given name, or raise KeyError."""
        for i, pet in enumerate(self.pets):
            if pet.name == name:
                del self.pets[i]
                return
        raise KeyError(f"{self.name} has no pet named {name}")

    def get_pet(self, name: str) -> Pet:
        """Return the pet with the given name, or raise KeyError."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        raise KeyError(f"{self.name} has no pet named {name}")

    def get_all_tasks(self) -> List[Task]:
        """Every task across all pets, in pet order."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_pending_tasks(self) -> List[Task]:
        """Return every incomplete task across all pets."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]


@dataclass
class ScheduledItem:
    task: Task
    start_minute: int  # minutes since midnight; format only for display
    reason: str


@dataclass
class SkippedItem:
    task: Task
    reason: str


@dataclass
class DailyPlan:
    items: List[ScheduledItem] = field(default_factory=list)
    skipped: List[SkippedItem] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Sum of the durations of all scheduled tasks."""
        return sum(item.task.duration_minutes for item in self.items)

    def explain(self) -> str:
        """Return a readable summary of scheduled and skipped tasks."""
        lines = []
        for item in self.items:
            t = item.task
            lines.append(
                f"{format_minute(item.start_minute)} - {t.title} for {t.pet_name} "
                f"({t.duration_minutes} min, {t.priority.name.lower()}): {item.reason}"
            )
        if not lines:
            lines.append("No tasks were scheduled.")
        for skip in self.skipped:
            t = skip.task
            lines.append(f"Skipped - {t.title} for {t.pet_name}: {skip.reason}")
        lines.append(f"Total scheduled time: {self.total_minutes} min")
        return "\n".join(lines)


@dataclass
class Conflict:
    """Two tasks whose time slots overlap on the same day."""

    first: Task
    second: Task
    start_minute: int  # when the overlap begins
    end_minute: int  # when the overlap ends

    @property
    def same_pet(self) -> bool:
        """True if both tasks belong to the same pet."""
        return self.first.pet_name == self.second.pet_name

    def describe(self) -> str:
        """One-line warning suitable for printing or showing in the UI."""
        a, b = self.first, self.second
        scope = "same pet" if self.same_pet else "different pets"
        return (
            f"Conflict ({scope}): {a.title} for {a.pet_name} and {b.title} for "
            f"{b.pet_name} overlap {format_minute(self.start_minute)}-"
            f"{format_minute(self.end_minute)}"
        )


def format_minute(minute: int) -> str:
    """Minutes since midnight -> 'HH:MM'."""
    return f"{minute // 60:02d}:{minute % 60:02d}"


class Scheduler:
    """Builds a daily plan from every pet's tasks, read through the Owner."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for the given owner's pets."""
        self.owner = owner

    def tasks_by_pet(self) -> Dict[str, List[Task]]:
        """Pending tasks across all pets, grouped by pet name."""
        grouped: Dict[str, List[Task]] = {}
        for task in self.owner.get_pending_tasks():
            grouped.setdefault(task.pet_name, []).append(task)
        return grouped

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task done and, if it recurs, add its next occurrence to the pet.

        Returns the newly created task, or None for a one-off task.
        """
        pet = self.owner.get_pet(task.pet_name)
        nxt = task.mark_complete()
        if nxt is not None:
            pet.add_task(nxt)
        return nxt

    def find_conflicts(self, tasks: Optional[List[Task]] = None) -> List[Conflict]:
        """Find pending tasks whose preferred time slots overlap on the same day.

        Only tasks with a preferred_minute can conflict. Tasks on different due
        dates never do, so tomorrow's copy of a daily task is not flagged.
        Never raises; an empty list means no conflicts.
        """
        if tasks is None:
            tasks = self.owner.get_pending_tasks()
        slots = [
            (t, t.preferred_minute)
            for t in tasks
            if t.preferred_minute is not None and not t.completed
        ]
        return self._overlaps(slots)

    def conflict_warnings(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Lightweight check: warning messages for overlapping tasks, never an exception.

        Returns an empty list when there are no conflicts. If the check itself
        fails (e.g. malformed task data), the failure is reported as a warning
        instead of crashing the caller.
        """
        try:
            return [f"Warning: {c.describe()}" for c in self.find_conflicts(tasks)]
        except Exception as exc:  # deliberate: a scheduling check must not take the app down
            return [f"Warning: could not check for conflicts ({exc})"]

    def find_plan_conflicts(self, plan: DailyPlan) -> List[Conflict]:
        """Find overlapping items in an already-built plan (by scheduled start)."""
        return self._overlaps([(i.task, i.start_minute) for i in plan.items])

    @staticmethod
    def _overlaps(slots: List[tuple]) -> List[Conflict]:
        """Sweep over (task, start) slots per day and report every overlapping pair."""
        by_day: Dict[date, List[tuple]] = {}
        for task, start in slots:
            by_day.setdefault(task.due_date, []).append((task, start))

        conflicts: List[Conflict] = []
        for day_slots in by_day.values():
            day_slots.sort(key=lambda s: s[1])
            for i, (a, a_start) in enumerate(day_slots):
                a_end = a_start + a.duration_minutes
                for b, b_start in day_slots[i + 1:]:
                    if b_start >= a_end:  # sorted by start, so nothing later overlaps a
                        break
                    conflicts.append(
                        Conflict(a, b, b_start, min(a_end, b_start + b.duration_minutes))
                    )
        return conflicts

    def sort_by_title(self, tasks: List[Task]) -> List[Task]:
        """Alphabetical by title, case-insensitive."""
        return sorted(tasks, key=lambda t: t.title.lower())

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Earliest preferred time first; tasks with no preferred time go last."""
        return sorted(
            tasks,
            key=lambda t: t.preferred_minute if t.preferred_minute is not None else MINUTES_PER_DAY,
        )

    def filter_tasks(
        self,
        tasks: List[Task],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Keep tasks matching the given pet name and/or completion status.

        A criterion left as None is ignored.
        """
        return [
            t
            for t in tasks
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
        ]

    def build_plan(self) -> DailyPlan:
        """Place pending tasks by priority, honoring preferred times without overlaps.

        Each task goes at its preferred time (or the day start if it has none). If
        that slot is taken by a higher-priority task, it shifts to the next free
        slot. A task is skipped if its duration exceeds the time budget left or it
        can't finish before midnight. Only task durations count against
        available_minutes, not idle gaps. Items come back in start-time order.
        """
        plan = DailyPlan()
        remaining = self.owner.available_minutes
        placed: List[tuple] = []  # (start, end, task), kept sorted by start

        for task in self._sort_tasks(self.owner.get_pending_tasks()):
            if task.duration_minutes > remaining:
                plan.skipped.append(
                    SkippedItem(
                        task,
                        f"needs {task.duration_minutes} min but only {remaining} min left",
                    )
                )
                continue

            wanted = task.preferred_minute
            earliest = max(self.owner.day_start_minute, wanted if wanted is not None else 0)
            start, blocker = self._first_free_slot(placed, earliest, task.duration_minutes)
            if start + task.duration_minutes > MINUTES_PER_DAY:
                plan.skipped.append(
                    SkippedItem(task, "no free slot left before midnight")
                )
                continue

            plan.items.append(
                ScheduledItem(task, start, self._reason(task, start, blocker))
            )
            placed.append((start, start + task.duration_minutes, task))
            placed.sort(key=lambda p: p[0])
            remaining -= task.duration_minutes

        plan.items.sort(key=lambda i: i.start_minute)
        return plan

    @staticmethod
    def _first_free_slot(placed: List[tuple], earliest: int, duration: int):
        """Earliest start >= `earliest` that fits `duration` without overlapping.

        Returns (start, blocker) where blocker is the task that pushed the start
        later, or None if it fit at `earliest`.
        """
        start, blocker = earliest, None
        for p_start, p_end, p_task in placed:  # sorted by start
            if start + duration <= p_start:
                break
            if start < p_end:
                start, blocker = p_end, p_task
        return start, blocker

    @staticmethod
    def _reason(task: Task, start: int, blocker: Optional[Task]) -> str:
        """Explain why the task landed where it did."""
        base = f"{task.priority.name.lower()} priority"
        wanted = task.preferred_minute
        if blocker is not None and wanted is not None and start != wanted:
            return (
                f"{base}; moved from preferred {format_minute(wanted)} because "
                f"{blocker.title} for {blocker.pet_name} was already scheduled"
            )
        if blocker is not None:
            return f"{base}; first free slot after {blocker.title} for {blocker.pet_name}"
        if wanted is not None and start != wanted:
            return f"{base}; preferred {format_minute(wanted)} is before the day starts"
        if wanted is not None:
            return f"{base}; at preferred time"
        return base

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Highest priority first, then earliest preferred time, then shortest.

        Python's sort is stable, so ties keep the owner's pet order.
        """
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority,
                t.preferred_minute if t.preferred_minute is not None else MINUTES_PER_DAY,
                t.duration_minutes,
            ),
        )
