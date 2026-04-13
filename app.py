"""
app.py - Streamlit UI for PawPal+
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler
from pawpal_advisor import PawPalAdvisor

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session State + JSON persistence ───────────────────────────────────────
if "owner" not in st.session_state:
    loaded = Owner.load_from_json("data.json")
    st.session_state.owner = loaded

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Your smart pet care scheduling assistant")
st.divider()

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Owner Profile")

    if st.session_state.owner is None:
        with st.form("owner_form"):
            owner_name  = st.text_input("Your name", placeholder="e.g. Alex Johnson")
            owner_email = st.text_input("Email (optional)")
            if st.form_submit_button("Create Profile") and owner_name.strip():
                st.session_state.owner = Owner(name=owner_name.strip(), email=owner_email.strip())
                st.session_state.owner.save_to_json("data.json")
                st.rerun()
    else:
        owner = st.session_state.owner
        st.success(f"Logged in as **{owner.name}**")
        if st.button("Reset Profile"):
            import os
            if os.path.exists("data.json"):
                os.remove("data.json")
            st.session_state.owner = None
            st.rerun()

    st.divider()

    if st.session_state.owner:
        st.subheader("Add a Pet")
        with st.form("pet_form"):
            pet_name = st.text_input("Pet name", placeholder="e.g. Buddy")
            species  = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
            breed    = st.text_input("Breed (optional)")
            age      = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
            if st.form_submit_button("Add Pet") and pet_name.strip():
                existing = [p.name.lower() for p in st.session_state.owner.pets]
                if pet_name.strip().lower() in existing:
                    st.warning(f"'{pet_name}' already exists.")
                else:
                    st.session_state.owner.add_pet(
                        Pet(name=pet_name.strip(), species=species, breed=breed.strip(), age=age)
                    )
                    st.session_state.owner.save_to_json("data.json")
                    st.rerun()

# ── Guard ───────────────────────────────────────────────────────────────────
if st.session_state.owner is None:
    st.info("Create your owner profile in the sidebar to get started.")
    st.stop()

owner     = st.session_state.owner
scheduler = Scheduler(owner)

if not owner.pets:
    st.info("Add at least one pet in the sidebar to begin scheduling.")
    st.stop()

# ── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Daily Schedule", "➕ Add Task", "✅ Complete Task",
    "🧠 Smart Tools", "🤖 AI Advisor", "🐾 My Pets"
])

# ── Tab 1: Daily Schedule ───────────────────────────────────────────────────
with tab1:
    st.subheader("Today's Schedule")
    st.caption(f"{date.today().strftime('%A, %B %d, %Y')}")

    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        st.warning(warning)

    sort_mode = st.radio("Sort by", ["Time", "Priority", "Weighted Priority"], horizontal=True)

    if sort_mode == "Time":
        sorted_tasks = scheduler.sort_by_time()
    elif sort_mode == "Priority":
        sorted_tasks = scheduler.sort_by_priority()
    else:
        sorted_tasks = scheduler.sort_by_weighted_priority()

    if not sorted_tasks:
        st.info("No tasks yet. Add some in the Add Task tab.")
    else:
        rows = []
        for pet_name, task in sorted_tasks:
            rows.append({
                "Time":      task.time,
                "Pet":       pet_name,
                "Task":      task.description,
                "Duration":  f"{task.duration_minutes} min",
                "Priority":  {1: "High", 2: "Medium", 3: "Low"}.get(task.priority),
                "Frequency": task.frequency.capitalize(),
                "Status":    "Done" if task.completed else "Pending",
            })
        st.table(rows)

    st.divider()
    all_tasks = scheduler.get_all_tasks()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tasks", len(all_tasks))
    c2.metric("Completed",   sum(1 for _, t in all_tasks if t.completed))
    c3.metric("Pending",     sum(1 for _, t in all_tasks if not t.completed))

# ── Tab 2: Add Task ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("Add a New Task")
    with st.form("task_form"):
        selected_pet = st.selectbox("Select pet", [p.name for p in owner.pets])
        task_desc    = st.text_input("Task description", placeholder="e.g. Morning Walk")
        task_time    = st.time_input("Scheduled time")
        duration     = st.slider("Duration (minutes)", 5, 120, 30, step=5)
        frequency    = st.selectbox("Frequency", ["daily", "weekly", "once"])
        priority     = st.select_slider(
            "Priority", options=[1, 2, 3], value=2,
            format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x]
        )
        due = st.date_input("Due / start date", value=date.today())

        if st.form_submit_button("Add Task") and task_desc.strip():
            for pet in st.session_state.owner.pets:
                if pet.name == selected_pet:
                    pet.add_task(Task(
                        description=task_desc.strip(),
                        time=task_time.strftime("%H:%M"),
                        frequency=frequency,
                        priority=priority,
                        duration_minutes=duration,
                        due_date=due,
                    ))
            st.session_state.owner.save_to_json("data.json")
            st.success(f"Added '{task_desc}' for {selected_pet}")
            st.rerun()

# ── Tab 3: Complete Task ────────────────────────────────────────────────────
with tab3:
    st.subheader("Mark a Task Complete")
    pending = scheduler.filter_by_status(completed=False)

    if not pending:
        st.success("All tasks are complete!")
    else:
        options  = [f"{n} → {t.description} ({t.time})" for n, t in pending]
        selected = st.selectbox("Select a task to complete", options)
        if st.button("Mark Complete"):
            pet_part  = selected.split(" → ")[0]
            task_part = selected.split(" → ")[1].split(" (")[0]
            msg = scheduler.mark_task_complete(pet_part, task_part)
            st.session_state.owner.save_to_json("data.json")
            if "✅" in msg:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()

# ── Tab 4: Smart Tools ──────────────────────────────────────────────────────
with tab4:
    st.subheader("Smart Scheduling Tools")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Next Available Slot")
        duration_req = st.number_input("Duration needed (min)", min_value=5, max_value=120, value=30, step=5)
        if st.button("Find Slot"):
            slot = scheduler.next_available_slot(duration_req)
            if slot:
                st.success(f"Next free slot: **{slot}**")
            else:
                st.warning("No free slots found between 07:00 and 21:00.")

    with col_b:
        st.markdown("#### Weighted Priority Rankings")
        if st.button("Show Rankings"):
            ranked = scheduler.sort_by_weighted_priority()
            rows = []
            for pet_name, task in ranked:
                score = scheduler.weighted_priority_score(task)
                rows.append({
                    "Score":    f"{score:.1f}",
                    "Pet":      pet_name,
                    "Task":     task.description,
                    "Time":     task.time,
                    "Priority": {1: "High", 2: "Medium", 3: "Low"}.get(task.priority),
                })
            if rows:
                st.table(rows)
            else:
                st.info("No tasks to rank.")

    st.divider()
    st.markdown("#### Filter Tasks")
    filter_mode = st.selectbox("Filter by", ["Pet", "Status", "Priority"])

    if filter_mode == "Pet":
        pet_filter = st.selectbox("Choose pet", [p.name for p in owner.pets])
        results = [(pet_filter, t) for t in scheduler.filter_by_pet(pet_filter)]
    elif filter_mode == "Status":
        status_filter = st.radio("Status", ["Pending", "Completed"], horizontal=True)
        results = scheduler.filter_by_status(completed=(status_filter == "Completed"))
    else:
        pri_filter = st.select_slider(
            "Priority level", options=[1, 2, 3],
            format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x]
        )
        results = scheduler.filter_by_priority(pri_filter)

    if results:
        for pet_name, task in results:
            icon = "Done" if task.completed else "Pending"
            st.markdown(f"**[{pet_name}]** {task.time} — {task.description} ({task.frequency}) — {icon}")
    else:
        st.info("No matching tasks.")

# ── Tab 5: AI Advisor ───────────────────────────────────────────────────────
with tab5:
    st.subheader("AI Schedule Advisor")
    st.caption("Powered by Gemini. Analyzes your current schedule and gives actionable recommendations.")

    st.markdown("The advisor runs a 3-step agent pipeline:")
    st.markdown("1. **Plan** — decides what to focus on based on your schedule")
    st.markdown("2. **Retrieve** — pulls all task data into a structured context")
    st.markdown("3. **Advise** — sends the context to Gemini and returns recommendations")

    st.divider()

    if st.button("Run AI Advisor", type="primary"):
        with st.spinner("Agent running..."):
            try:
                advisor = PawPalAdvisor(owner, verbose=False)
                result  = advisor.run()

                st.markdown("#### Agent Steps")
                for i, step in enumerate(result["steps"], 1):
                    with st.expander(step["step"]):
                        st.write(step["detail"])

                st.markdown("#### Recommendations")
                st.markdown(result["advice"])

                st.divider()
                with st.expander("Raw schedule context sent to Gemini"):
                    st.json(result["context"])

            except ValueError as e:
                st.error(str(e))
                st.info("Add your GEMINI_API_KEY to a .env file in the project folder and restart the app.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ── Tab 6: My Pets ──────────────────────────────────────────────────────────
with tab6:
    st.subheader("Your Pets")
    for pet in owner.pets:
        with st.expander(f"{pet.name} — {pet.species}, age {pet.age}"):
            if not pet.tasks:
                st.caption("No tasks yet.")
            else:
                for task in pet.tasks:
                    status = "Done" if task.completed else "Pending"
                    st.markdown(
                        f"**{task.time}** — {task.description} "
                        f"({task.duration_minutes} min, {task.frequency}) — {status}"
                    )
            if st.button(f"Remove {pet.name}", key=f"remove_{pet.name}"):
                st.session_state.owner.remove_pet(pet.name)
                st.session_state.owner.save_to_json("data.json")
                st.rerun()