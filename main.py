from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    format_minute,
)


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90, day_start_minute=8 * 60)

    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of order (by title, time, and pet) to exercise sorting.
    luna.add_task(Task("Play session", 20, Priority.MEDIUM, preferred_minute=18 * 60))
    mochi.add_task(Task("Grooming", 45, Priority.LOW, frequency=Frequency.WEEKLY))
    luna.add_task(Task("litter box", 5, Priority.MEDIUM, frequency=Frequency.DAILY))
    mochi.add_task(
        Task(
            "Morning walk",
            30,
            Priority.HIGH,
            description="Around the park",
            frequency=Frequency.DAILY,
            preferred_minute=8 * 60,
        )
    )
    luna.add_task(Task("Breakfast", 10, Priority.HIGH, preferred_minute=7 * 60 + 30))
    mochi.add_task(Task("Evening meal", 10, Priority.HIGH, preferred_minute=17 * 60))

    # Two deliberate clashes with Morning walk (08:00-08:30): one for the same pet,
    # one for the other pet.
    mochi.add_task(Task("Brush teeth", 10, Priority.MEDIUM, preferred_minute=8 * 60 + 10))
    luna.add_task(Task("Vet call", 20, Priority.MEDIUM, preferred_minute=8 * 60 + 15))

    # Two tasks at exactly the same time (12:00), for different pets.
    mochi.add_task(Task("Medication", 5, Priority.HIGH, preferred_minute=12 * 60))
    luna.add_task(Task("Training", 15, Priority.MEDIUM, preferred_minute=12 * 60))

    # Mark one task done so the completion filter has something to separate.
    mochi.tasks[0].mark_complete()  # Grooming

    scheduler = Scheduler(owner)

    print(f"Owner: {owner.name} ({owner.available_minutes} min available, "
          f"starting {format_minute(owner.day_start_minute)})")
    for pet in owner.pets:
        print(f"  {pet.name} ({pet.species}): {len(pet.tasks)} tasks")

    all_tasks = owner.get_all_tasks()

    def show(heading: str, tasks) -> None:
        print(f"\n=== {heading} ===")
        if not tasks:
            print("  (none)")
        for t in tasks:
            when = format_minute(t.preferred_minute) if t.preferred_minute is not None else "--:--"
            status = "done" if t.completed else "todo"
            print(f"  {when}  {t.title:<14} {t.pet_name:<6} {status}")

    show("As added (out of order)", all_tasks)
    show("Sorted by title", scheduler.sort_by_title(all_tasks))
    show("Sorted by preferred time", scheduler.sort_by_time(all_tasks))
    show("Filter: Luna's tasks", scheduler.filter_tasks(all_tasks, pet_name="Luna"))
    show("Filter: completed", scheduler.filter_tasks(all_tasks, completed=True))
    show("Filter: Mochi + pending", scheduler.filter_tasks(all_tasks, pet_name="Mochi", completed=False))
    show(
        "Luna's tasks, sorted by time",
        scheduler.sort_by_time(scheduler.filter_tasks(all_tasks, pet_name="Luna")),
    )

    print("\n=== Conflict check ===")
    warnings = scheduler.conflict_warnings()
    for w in warnings:
        print(f"  {w}")
    if not warnings:
        print("  no conflicts")

    print("\n=== Recurring: complete a daily and a weekly task ===")
    walk = next(t for t in all_tasks if t.title == "Morning walk")
    print(f"  before: Mochi has {len(mochi.tasks)} tasks")
    for task in (walk, mochi.tasks[0]):  # daily walk, then (already done) weekly grooming
        nxt = scheduler.complete_task(task)
        if nxt:
            print(f"  completed {task.title!r} ({task.frequency.value}, due {task.due_date})"
                  f" -> new one due {nxt.due_date}")
    print(f"  after:  Mochi has {len(mochi.tasks)} tasks")

    print("\n=== Today's Schedule ===")
    plan = scheduler.build_plan()
    print(plan.explain())


if __name__ == "__main__":
    main()
