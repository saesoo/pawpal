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
    mochi.add_task(Task("Grooming", 45, Priority.LOW, frequency=Frequency.WEEKLY))
    luna.add_task(Task("Breakfast", 10, Priority.HIGH, preferred_minute=7 * 60 + 30))
    luna.add_task(Task("Play session", 20, Priority.MEDIUM, preferred_minute=18 * 60))
    luna.add_task(Task("Litter box", 5, Priority.MEDIUM, frequency=Frequency.DAILY))

    scheduler = Scheduler(owner)

    print(f"Owner: {owner.name} ({owner.available_minutes} min available, "
          f"starting {format_minute(owner.day_start_minute)})")
    for pet in owner.pets:
        print(f"  {pet.name} ({pet.species}): {len(pet.tasks)} tasks")

    print("\n=== Today's Schedule ===")
    plan = scheduler.build_plan()
    print(plan.explain())


if __name__ == "__main__":
    main()
