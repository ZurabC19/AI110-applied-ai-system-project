"""
app.py - Streamlit UI for PawPal+
Run with: streamlit run app.py
"""

import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session State ──────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None

# ── Header ─────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Your smart pet care scheduling assistant")
st.divider()

# ── Sidebar: Owner + Pet setup ─────────────────────────────
with st.sidebar:
    st.header("👤 Owner Profile")

    if st.session_state.owner is None:
        with st.form("owner_form"):
            owner_name = st.text_input("Your name", placeholder="e.g. Alex Johnson")
            owner_email = st.text_input("Email (optional)")
            if st.form_submit_button("Create Profile") and owner_name.strip():
                st.session_state.owner = Owner(name=owner_name.strip(), email=owner_email.strip())
                st.rerun()
    else:
        owner = st.session_state.owner
        st.success(f"Logged in as **{owner.name}**")
        if st.button("🔄 Reset Profile"):
            st.session_state.owner = None
            st.rerun()

    st.divider()

    if st.session_state.owner:
        st.subheader("🐶 Add a Pet")
        with st.form("pet_form"):
            pet_name = st.text_input("Pet name", placeholder="e.g. Buddy")
            species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
            breed = st.text_input("Breed (optional)")
            age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
            if st.form_submit_button("Add Pet") and pet_name.strip():
                existing = [p.name.lower() for p in st.session_state.owner.pets]
                if pet_name.strip().lower() in existing:
                    st.warning(f"'{pet_name}' already exists.")
                else:
                    st.session_state.owner.add_pet(Pet(
                        name=pet_name.strip(), species=species,
                        breed=breed.strip(), age=age
                    ))
                    st.rerun()

# ── Guard: need owner + pet before showing main UI ─────────
if st.session_state.owner is None:
    st.info("👈 Create your owner profile in the sidebar to get started.")
    st.stop()

owner = st.session_state.owner
scheduler = Scheduler(owner)

if not owner.pets:
    st.info("👈 Add at least one pet in the sidebar to begin scheduling.")
    st.stop()

# ── Tabs ───────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Daily Schedule", "➕ Add Task", "✅ Complete Task", "🐾 My Pets"
])

# ── Tab 1: Daily Schedule ──────────────────────────────────
with tab1:
    st.subheader("📅 Today's Schedule")
    st.caption(f"Date: {date.today().strftime('%A, %B %d, %Y')}")

    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        st.warning(warning)

    sorted_tasks = scheduler.sort_by_time()
    if not sorted_tasks:
        st.info("No tasks yet. Add some in the **Add Task** tab.")
    else:
        rows = []
        for pet_name, task in sorted_tasks:
            rows.append({
                "Time": task.time,
                "Pet": pet_name,
                "Task": task.description,
                "Duration": f"{task.duration_minutes} min",
                "Priority": {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(task.priority),
                "Frequency": task.frequency.capitalize(),
                "Status": "✅ Done" if task.completed else "⏳ Pending",
            })
        st.table(rows)

    st.divider()
    all_tasks = scheduler.get_all_tasks()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tasks", len(all_tasks))
    c2.metric("Completed", sum(1 for _, t in all_tasks if t.completed))
    c3.metric("Pending", sum(1 for _, t in all_tasks if not t.completed))

# ── Tab 2: Add Task ────────────────────────────────────────
with tab2:
    st.subheader("➕ Add a New Task")
    with st.form("task_form"):
        selected_pet = st.selectbox("Select pet", [p.name for p in owner.pets])
        task_desc = st.text_input("Task description", placeholder="e.g. Morning Walk")
        task_time = st.time_input("Scheduled time")
        duration = st.slider("Duration (minutes)", 5, 120, 30, step=5)
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        priority = st.select_slider(
            "Priority", options=[1, 2, 3], value=2,
            format_func=lambda x: {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}[x]
        )
        due = st.date_input("Due / start date", value=date.today())

        if st.form_submit_button("Add Task") and task_desc.strip():
            for pet in owner.pets:
                if pet.name == selected_pet:
                    pet.add_task(Task(
                        description=task_desc.strip(),
                        time=task_time.strftime("%H:%M"),
                        frequency=frequency,
                        priority=priority,
                        duration_minutes=duration,
                        due_date=due,
                    ))
            st.success(f"Added '{task_desc}' for {selected_pet} ✅")
            st.rerun()

# ── Tab 3: Complete Task ───────────────────────────────────
with tab3:
    st.subheader("✅ Mark a Task Complete")
    pending = scheduler.filter_by_status(completed=False)

    if not pending:
        st.success("All tasks are complete! Great job. 🎉")
    else:
        options = [f"{n} → {t.description} ({t.time})" for n, t in pending]
        selected = st.selectbox("Select a task to complete", options)
        if st.button("Mark Complete ✅"):
            pet_part = selected.split(" → ")[0]
            task_part = selected.split(" → ")[1].split(" (")[0]
            msg = scheduler.mark_task_complete(pet_part, task_part)
            if "✅" in msg:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()

# ── Tab 4: My Pets ─────────────────────────────────────────
with tab4:
    st.subheader("🐾 Your Pets")
    for pet in owner.pets:
        with st.expander(f"{pet.name} — {pet.species}, age {pet.age}"):
            if not pet.tasks:
                st.caption("No tasks yet.")
            else:
                for task in pet.tasks:
                    icon = "✅" if task.completed else "⏳"
                    st.markdown(f"{icon} **{task.time}** — {task.description} ({task.duration_minutes} min, {task.frequency})")
            if st.button(f"Remove {pet.name}", key=f"remove_{pet.name}"):
                owner.remove_pet(pet.name)
                st.rerun()