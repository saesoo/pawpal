from datetime import time

import streamlit as st

from pawpal_system import (
    Frequency,
    Owner,
    Pet,
    Priority,
    Scheduler,
    Task,
    format_minute,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planner: add your pets and their tasks, then build today's schedule.")

# The Owner lives in session_state so pets and tasks survive Streamlit reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)
owner: Owner = st.session_state.owner

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Minutes available today", min_value=1, max_value=1440, value=owner.available_minutes
        )
    )

st.subheader("Pets")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    st.write("")
    st.write("")
    add_pet_clicked = st.button("Add pet")

if add_pet_clicked:
    try:
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
    except ValueError as err:
        st.error(str(err))

if owner.pets:
    st.write(", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.subheader("Tasks")
if owner.pets:
    pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", [p.name.title() for p in Priority], index=2)
    with col4:
        frequency = st.selectbox("Frequency", [f.value.title() for f in Frequency])

    col1, col2 = st.columns([1, 3])
    with col1:
        use_preferred = st.checkbox("Preferred time")
    with col2:
        preferred = st.time_input("Time of day", value=time(8, 0), disabled=not use_preferred)

    if st.button("Add task"):
        owner.get_pet(pet_choice).add_task(
            Task(
                title=task_title.strip(),
                duration_minutes=int(duration),
                priority=Priority[priority.upper()],
                frequency=Frequency(frequency.lower()),
                preferred_minute=preferred.hour * 60 + preferred.minute if use_preferred else None,
            )
        )
else:
    st.caption("Add a pet before adding tasks.")

scheduler = Scheduler(owner)
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))
all_tasks = owner.get_all_tasks()
if all_tasks:
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Show status", ["All", "Pending", "Done"])
    with col3:
        sort_choice = st.selectbox("Sort by", ["Time", "Title"])

    shown = scheduler.filter_tasks(
        all_tasks,
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Pending": False, "Done": True}[status_filter],
    )
    shown = scheduler.sort_by_time(shown) if sort_choice == "Time" else scheduler.sort_by_title(shown)

    if shown:
        st.table(
            [
                {
                    "Pet": t.pet_name,
                    "Task": t.title,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority.name.title(),
                    "Frequency": t.frequency.value.title(),
                    "Preferred": format_minute(t.preferred_minute) if t.preferred_minute is not None else "Any",
                    "Due": t.due_date.isoformat(),
                    "Done": t.completed,
                }
                for t in shown
            ]
        )
    else:
        st.info("No tasks match these filters.")

    for warning in scheduler.conflict_warnings():
        st.warning(warning)

    pending = scheduler.sort_by_time(owner.get_pending_tasks())
    if pending:
        labels = {f"{t.title} for {t.pet_name} ({t.due_date})": t for t in pending}
        col1, col2 = st.columns([3, 1])
        with col1:
            to_complete = st.selectbox("Mark a task done", list(labels))
        with col2:
            st.write("")
            st.write("")
            complete_clicked = st.button("Complete")
        if complete_clicked:
            task = labels[to_complete]
            nxt = scheduler.complete_task(task)
            st.session_state.flash = (
                f"Done! Next {task.frequency.value} {task.title} is due {nxt.due_date}."
                if nxt is not None
                else f"Done: {task.title}."
            )
            st.rerun()
else:
    st.info("No tasks yet.")

st.divider()

st.subheader("Today's Schedule")
if st.button("Generate schedule"):
    plan = scheduler.build_plan()
    if plan.items:
        st.table(
            [
                {
                    "Start": format_minute(i.start_minute),
                    "Pet": i.task.pet_name,
                    "Task": i.task.title,
                    "Minutes": i.task.duration_minutes,
                    "Why": i.reason,
                }
                for i in plan.items
            ]
        )
    else:
        st.warning("Nothing could be scheduled. Add tasks or more available time.")
    for conflict in scheduler.find_plan_conflicts(plan):
        st.error(conflict.describe())
    for s in plan.skipped:
        st.warning(f"Skipped {s.task.title} for {s.task.pet_name}: {s.reason}")
    st.success(f"Scheduled {plan.total_minutes} of {owner.available_minutes} minutes.")
