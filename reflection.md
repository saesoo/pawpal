# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
My initial UML design models PawPal+ as six classes. Four hold data (Owner, Pet, Task, ScheduledItem). Scheduler holds the scheduling logic, and DailyPlan holds its result. I kept the data separate from the scheduling logic so I could change the scheduling rules without touching the classes that store information.
- What classes did you include, and what responsibilities did you assign to each?
Owner: Stores the owner's name, how many minutes they have available each day, preferences, and their list of pets.
Pet: Stores the pet's name and species, and owns the pet's list of tasks. It can add and remove tasks.
Scheduler: Does the planning. It reads the owner's tasks and time limit, sorts the tasks by priority, and fits as many as it can into the available time
DailyPlan: Holds the final schedule and the tasks that didn't fit.
ScheduledItem: Pairs a Task with a start time and the reason the scheduler chose it. This is what lets the plan explain why each task is there.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
Yes my design changed. After I wrote the class skeleton, I reviewed it for missing relationships and likely logic problems, and I made several changes before implementing anything. The most important change was linking each Task back to its Pet. In my first design, Owner.get_all_tasks() combined every pet's tasks into one list. Once that happened, the scheduler could no longer tell which pet a task belonged to, so the plan couldn't say "walk Mochi". I fixed this by adding a pet_name field to Task, which Pet.add_task fills in.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
My scheduler considers three constraints, in this order of importance:

Available time: 
    The owner has a fixed number of minutes per day, and the plan can never exceed it. This is a hard limit: a task that doesn't fit in the remaining time is skipped, and the plan records why.
Priority: 
    Tasks are sorted high, then medium, then low, so the most important care (feeding, medication) gets time first.
Preferred time and duration:
     When two tasks have the same priority, the one with the earlier preferred time goes first, and after that the shorter one. These only break ties. They don't override priority or time.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
My scheduler uses a greedy approach. It sorts tasks by priority and adds each one to the plan if it fits in the remaining time. If a task doesn't fit, it's skipped and the scheduler moves on to the next one. The tradeoff is that this isn't guaranteed to use the available time as well as possible. For example, with 60 minutes available, a high-priority 45-minute task goes in first. That leaves 15 minutes, which might have been better spent on three medium-priority 20-minute tasks. 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used AI tools during this project to help me brainstorm ways on setting up my UML diagram. AI also helped alongside configuring the UML diagram into python code. For prompting, I used the recommeded prompts in the assignment description.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
When creating test cases, I used AI to help build it. However, the AI suggestion did not correlate to what I was wanting to test within my code, so I reprompted again to make sure it had the right context.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
I wrote two tests so far, both for core behaviors in pawpal_system.py
These matter because everything else depends on them. The scheduler only plans tasks that aren't completed, so if mark_complete() failed silently, finished tasks would keep reappearing in the plan. The scheduler also gets all its tasks by going through each pet, so if add_task didn't actually store the task, it would never reach the plan. Both tests check the state before and after the action, so they can't pass by accident.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident (4 out of 5) that the scheduler works correctly. All 23 tests pass, and they cover the behaviors the rest of the app depends on: sorting by time (including 9:00 before 17:00 and unscheduled tasks last), daily and weekly recurrence, conflict detection for the same pet and across pets, and plan building without overlaps. I held back one point because some cases aren't tested and a few known limits are in the code. For example, `build_plan` ignores due dates, and completing the same task twice creates two next occurrences. I also haven't tested the Streamlit UI beyond reading the code.

If I had more time, I would test these edge cases next:
- Recurrence across month, year and leap-year boundaries. Daily recurrence always uses `date.today()`, so I would need to inject or mock the date to test it.
- Daylight saving time changes for tasks scheduled in the early morning.
- Tasks whose durations run past midnight, and tasks that end exactly at midnight.
- Completing the same recurring task twice, which should not create duplicate next occurrences.
- Tasks with the same title for different pets, and very long or unusual names.
- `build_plan` with tasks due on future dates, which it currently schedules for today.
- Bad input, such as zero or negative durations and preferred times outside 00:00 to 23:59, through the UI as well as the code.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am satisfied with the system design and implemention of the UML into python code. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would make four changes:
- **Respect due dates in `build_plan`.** It currently schedules every pending task today, including tomorrow's copy of a daily task. It should only plan tasks due today or earlier.
- **Make recurrence testable and safer.** Daily recurrence is hard-coded to `date.today()`, which makes date edge cases hard to test. I would pass the current date in as a parameter. I would also guard against completing the same task twice, so it can't create duplicate next occurrences.
- **Make the schedule smarter about time.** Right now only task durations count against the available minutes, and a shifted task can only move later, never earlier. I would count idle gaps, and let a task move to an earlier free slot when one exists.
- **Improve the UI.** I would let users edit and delete tasks, add a screenshot or demo to the README, and keep the generated schedule on screen after other actions instead of only showing it right after the button click.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing I learned is that AI works best when I give it clear context and then check its output against what I actually want. Earlier, a test suggestion didn't match what I wanted to test, and I only got a useful result after I reprompted with more context. Reading the code and running the tests showed me what the AI had really done. I also learned that a design is never finished after the first draft. My first UML changed as I built the code, with new pieces like `Conflict` and recurring tasks, so I had to update the diagram to match the final system.
