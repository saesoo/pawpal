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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
