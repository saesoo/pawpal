from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    completed: bool = False

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, title: str) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass


@dataclass
class ScheduledItem:
    task: Task
    start_time: str
    reason: str


@dataclass
class DailyPlan:
    items: List[ScheduledItem] = field(default_factory=list)
    total_minutes: int = 0
    skipped: List[Task] = field(default_factory=list)

    def explain(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def build_plan(self) -> DailyPlan:
        pass

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        pass

    def _fits_in_time(self, task: Task, remaining: int) -> bool:
        pass
