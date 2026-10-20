from pawpal_system import Pet, Priority, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30, Priority.HIGH)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Morning walk", 30, Priority.HIGH))
    assert len(pet.tasks) == 1

    pet.add_task(Task("Feeding", 10, Priority.MEDIUM))
    assert len(pet.tasks) == 2


def _scheduler_with(task):
    from datetime import date
    from pawpal_system import Owner, Pet, Scheduler

    owner = Owner("Jordan", 60)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(task)
    return Scheduler(owner), pet


def test_completing_daily_task_creates_next_day_instance():
    from datetime import date, timedelta
    from pawpal_system import Frequency

    # An old due date proves the new one is based on today, not on the old date.
    task = Task("Walk", 30, Priority.HIGH, frequency=Frequency.DAILY, due_date=date(2026, 1, 1))
    scheduler, pet = _scheduler_with(task)

    nxt = scheduler.complete_task(task)

    assert task.completed
    assert nxt is not None and nxt is not task
    assert nxt.due_date == date.today() + timedelta(days=1)
    assert not nxt.completed and nxt.id != task.id
    assert nxt.pet_name == "Mochi" and nxt in pet.tasks
    assert pet.get_pending_tasks() == [nxt]


def test_completing_weekly_task_creates_instance_seven_days_later():
    from datetime import date
    from pawpal_system import Frequency

    task = Task("Groom", 45, Priority.LOW, frequency=Frequency.WEEKLY, due_date=date(2026, 1, 1))
    scheduler, _ = _scheduler_with(task)

    assert scheduler.complete_task(task).due_date == date(2026, 1, 8)


def test_completing_one_off_task_creates_nothing():
    task = Task("Vet visit", 60, Priority.HIGH)
    scheduler, pet = _scheduler_with(task)

    assert scheduler.complete_task(task) is None
    assert pet.tasks == [task]


def _two_pet_scheduler():
    from pawpal_system import Owner, Pet, Scheduler

    owner = Owner("Jordan", 120)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return Scheduler(owner), mochi, luna


def test_detects_conflict_for_same_pet():
    scheduler, mochi, _ = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))
    mochi.add_task(Task("Brush", 10, Priority.LOW, preferred_minute=490))

    (c,) = scheduler.find_conflicts()

    assert c.same_pet
    assert (c.start_minute, c.end_minute) == (490, 500)


def test_detects_conflict_across_pets():
    scheduler, mochi, luna = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))
    luna.add_task(Task("Vet call", 20, Priority.LOW, preferred_minute=495))

    (c,) = scheduler.find_conflicts()

    assert not c.same_pet
    assert "different pets" in c.describe()


def test_back_to_back_and_unscheduled_tasks_do_not_conflict():
    scheduler, mochi, luna = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))
    luna.add_task(Task("Feed", 10, Priority.HIGH, preferred_minute=510))  # starts as walk ends
    luna.add_task(Task("Play", 20, Priority.LOW))  # no preferred time

    assert scheduler.find_conflicts() == []


def test_identical_start_times_conflict():
    scheduler, mochi, luna = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))
    luna.add_task(Task("Feed", 10, Priority.HIGH, preferred_minute=480))

    assert len(scheduler.find_conflicts()) == 1


def test_tasks_on_different_days_do_not_conflict():
    from datetime import date, timedelta

    scheduler, mochi, luna = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))
    luna.add_task(
        Task("Feed", 10, Priority.HIGH, preferred_minute=480, due_date=date.today() + timedelta(days=1))
    )

    assert scheduler.find_conflicts() == []


def test_completed_tasks_are_ignored():
    scheduler, mochi, luna = _two_pet_scheduler()
    done = Task("Walk", 30, Priority.HIGH, preferred_minute=480)
    mochi.add_task(done)
    luna.add_task(Task("Feed", 10, Priority.HIGH, preferred_minute=480))
    done.mark_complete()

    assert scheduler.find_conflicts() == []


def test_plan_honors_preferred_time():
    scheduler, mochi, _ = _two_pet_scheduler()  # day starts 08:00
    mochi.add_task(Task("Evening meal", 10, Priority.HIGH, preferred_minute=17 * 60))

    (item,) = scheduler.build_plan().items

    assert item.start_minute == 17 * 60


def test_plan_shifts_lower_priority_task_past_conflict():
    scheduler, mochi, luna = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))
    luna.add_task(Task("Vet call", 20, Priority.MEDIUM, preferred_minute=495))

    plan = scheduler.build_plan()
    starts = {i.task.title: i.start_minute for i in plan.items}

    assert starts == {"Walk": 480, "Vet call": 510}  # moved from 08:15 to 08:30
    assert "moved from preferred 08:15" in plan.items[1].reason
    assert scheduler.find_plan_conflicts(plan) == []


def test_plan_fills_gap_before_a_later_preferred_task():
    scheduler, mochi, luna = _two_pet_scheduler()
    mochi.add_task(Task("Dinner", 10, Priority.HIGH, preferred_minute=17 * 60))
    luna.add_task(Task("Litter box", 5, Priority.LOW))  # no preferred time

    starts = {i.task.title: i.start_minute for i in scheduler.build_plan().items}

    assert starts == {"Dinner": 17 * 60, "Litter box": 8 * 60}


def test_plan_skips_task_that_cannot_finish_before_midnight():
    scheduler, mochi, _ = _two_pet_scheduler()
    mochi.add_task(Task("Late walk", 30, Priority.HIGH, preferred_minute=23 * 60 + 50))

    plan = scheduler.build_plan()

    assert plan.items == []
    assert "midnight" in plan.skipped[0].reason


def test_plan_never_overlaps_for_many_clashing_tasks():
    scheduler, mochi, luna = _two_pet_scheduler()
    for i in range(4):
        mochi.add_task(Task(f"M{i}", 15, Priority.MEDIUM, preferred_minute=480))
        luna.add_task(Task(f"L{i}", 10, Priority.LOW, preferred_minute=485))

    plan = scheduler.build_plan()

    assert len(plan.items) + len(plan.skipped) == 8
    assert scheduler.find_plan_conflicts(plan) == []


def test_conflict_warnings_return_messages_instead_of_raising():
    scheduler, mochi, luna = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))
    luna.add_task(Task("Feed", 10, Priority.HIGH, preferred_minute=480))

    (msg,) = scheduler.conflict_warnings()

    assert msg.startswith("Warning:") and "Walk" in msg and "Feed" in msg


def test_conflict_warnings_empty_when_no_conflicts():
    scheduler, mochi, _ = _two_pet_scheduler()
    mochi.add_task(Task("Walk", 30, Priority.HIGH, preferred_minute=480))

    assert scheduler.conflict_warnings() == []


def test_conflict_warnings_survive_bad_data():
    scheduler, mochi, _ = _two_pet_scheduler()
    good = Task("Walk", 30, Priority.HIGH, preferred_minute=480)
    bad = Task("Feed", 10, Priority.HIGH, preferred_minute=480)
    bad.duration_minutes = None  # bypasses __post_init__ validation
    mochi.add_task(good)
    mochi.add_task(bad)

    (msg,) = scheduler.conflict_warnings()

    assert msg.startswith("Warning: could not check")
