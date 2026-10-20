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
