from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Dict, List, Optional
from uuid import uuid4


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

    def mark_complete(self) -> None:
        """Mark the task as done."""
        self.completed = True

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

    def build_plan(self) -> DailyPlan:
        """Fit the owner's pending tasks, by priority, into the available time."""
        plan = DailyPlan()
        remaining = self.owner.available_minutes
        cursor = self.owner.day_start_minute

        for task in self._sort_tasks(self.owner.get_pending_tasks()):
            if task.duration_minutes > remaining:
                plan.skipped.append(
                    SkippedItem(
                        task,
                        f"needs {task.duration_minutes} min but only {remaining} min left",
                    )
                )
                continue
            plan.items.append(
                ScheduledItem(task, cursor, f"{task.priority.name.lower()} priority")
            )
            cursor += task.duration_minutes
            remaining -= task.duration_minutes
        return plan

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Highest priority first, then earliest preferred time, then shortest.

        Python's sort is stable, so ties keep the owner's pet order.
        """
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority,
                t.preferred_minute if t.preferred_minute is not None else 24 * 60,
                t.duration_minutes,
            ),
        )
