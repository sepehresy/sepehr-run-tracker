import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import json
import os
from openai import OpenAI
from views.ai_prompt import generate_ai_prompt

# from app import load_gist_data, save_gist_data  # <-- Add this line
from utils.gist_helpers import load_gist_data, save_gist_data

USER_KEY = "sepehr"  # Later, make this dynamic per user

def load_gist_race_data():
    data = load_gist_data()
    if USER_KEY not in data:
        data[USER_KEY] = {"races": [], "training_plans": {}, "progress_feedback": {}}
    return data

def save_gist_race_data(data):
    return save_gist_data(data)

def load_saved_races():
    data = load_gist_race_data()
    return data[USER_KEY].get("races", [])

def save_races(races):
    data = load_gist_race_data()
    data[USER_KEY]["races"] = races
    return save_gist_race_data(data)

def load_training_plans():
    data = load_gist_race_data()
    return data[USER_KEY].get("training_plans", {})

def save_training_plan(race_id, plan):
    data = load_gist_race_data()
    data[USER_KEY].setdefault("training_plans", {})
    data[USER_KEY]["training_plans"][race_id] = plan
    return save_gist_race_data(data)

def load_progress_feedback():
    data = load_gist_race_data()
    return data[USER_KEY].get("progress_feedback", {})

def save_progress_feedback(race_id, entry):
    data = load_gist_race_data()
    data[USER_KEY].setdefault("progress_feedback", {})
    data[USER_KEY]["progress_feedback"].setdefault(race_id, []).append(entry)
    return save_gist_race_data(data)

def render_feedback_history(race_id):
    race_history = load_progress_feedback().get(race_id, [])
    if race_history:
        st.markdown("""
        <style>
        .ai-feedback-card {
            border-radius: 10px;
            margin-bottom: 14px;
            background: #18191a;
            box-shadow: 0 2px 8px rgba(30,40,60,0.07);
            border: 1px solid #23272f;
            transition: box-shadow 0.2s;
        }
        .ai-feedback-summary {
            display: flex;
            align-items: center;
            cursor: pointer;
            padding: 14px 18px;
            font-size: 1.05rem;
            color: #e6e6e6;
            font-weight: 500;
            border-bottom: 1px solid #23272f;
            transition: background 0.2s;
            justify-content: space-between;
        }
        .ai-feedback-summary-left {
            display: flex;
            align-items: center;
        }
        .ai-feedback-date {
            font-size: 0.92rem;
            color: #8a8f98;
            margin-left: 10px;
            font-weight: 400;
        }
        .ai-feedback-content {
            padding: 18px 18px 14px 48px;
            color: #e6e6e6;
            font-size: 0.98rem;
            line-height: 1.7;
            background: #18191a;
        }
        .ai-feedback-icon {
            font-size: 1.3rem;
            margin-right: 8px;
            color: #1EBEFF;
        }
        .ai-feedback-remove-btn {
            background: none;
            border: none;
            color: #FF4B4B;
            font-size: 1.1rem;
            cursor: pointer;
            padding: 2px 10px;
            border-radius: 6px;
            transition: background 0.15s;
            margin-left: 18px;
        }
        .ai-feedback-remove-btn:hover {
            background: #2a2323;
        }
        details[open] .ai-feedback-summary {
            border-bottom: 1px solid #23272f;
            background: #212226;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("### 🕓 AI Feedback History")
        for i, item in enumerate(reversed(race_history)):
            feedback_key = f"{race_id}_feedback_{len(race_history)-1-i}"
            # Use columns to align the button with the summary (Streamlit only)
            cols = st.columns([0.88, 0.12])
            with cols[0]:
                st.markdown(f"""
                <details class="ai-feedback-card" {'open' if i == 0 else ''}>
                  <summary class="ai-feedback-summary">
                    <span class="ai-feedback-summary-left">
                      <span class="ai-feedback-icon">🤖</span>
                      <span>AI Feedback</span>
                      <span class="ai-feedback-date">{item['date']}</span>
                    </span>
                  </summary>
                  <div class="ai-feedback-content">{item['feedback']}</div>
                </details>
                """, unsafe_allow_html=True)
            with cols[1]:
                remove_btn = st.button("🗑️", key=f"remove_{feedback_key}", help="Delete this feedback")
                if remove_btn:
                    all_history = load_progress_feedback()
                    feedback_list = all_history.get(race_id, [])
                    del feedback_list[len(feedback_list)-1-i]
                    all_history[race_id] = feedback_list
                    save_progress_feedback(race_id, feedback_list)
                    st.success("Feedback removed.")
                    st.rerun()

def render_race_planning(df, today):
    if isinstance(today, datetime):
        today = today.date()

    # Ensure df["Date"] is datetime
    if "Date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"])

    st.title("🏁 Race Planning")
    races = load_saved_races()

    with st.expander("➕ Add a New Race", expanded=len(races) == 0):
        with st.form("add_race_form"):
            col1, col2 = st.columns(2)
            with col1:
                race_name = st.text_input("Race Name")
                race_date = st.date_input("Race Date", min_value=today)
            with col2:
                race_distance = st.number_input("Distance (km)", min_value=1.0, step=0.1)
                race_type = st.selectbox("Race Type", ["Road", "Trail", "Track", "Virtual"])
            notes = st.text_area("Race Notes (optional)")
            if st.form_submit_button("Save Race") and race_name:
                new_race = {
                    "id": f"race_{len(races)+1}",
                    "name": race_name,
                    "date": race_date.isoformat(),
                    "distance": race_distance,
                    "type": race_type,
                    "notes": notes,
                    "created_at": datetime.now().isoformat()
                }
                races.append(new_race)
                if save_races(races):
                    st.success(f"Race '{race_name}' added.")
                    st.rerun()

    if not races:
        st.info("No races added yet.")
        return

    st.subheader("Your Upcoming Races")
    for i, race in enumerate(races):
        race_date = datetime.fromisoformat(race["date"]).date()
        days_until = (race_date - today).days
        with st.container():
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(f"### {race['name']}")
                st.write(f"📅 {race_date} ({'in ' + str(days_until) + ' days' if days_until > 0 else 'Today!' if days_until == 0 else 'Completed'})")
                st.write(f"🏃 {race['distance']} km | {race['type']}")
                if race["notes"]:
                    st.write(f"📝 {race['notes']}")
            with cols[1]:
                if st.button("🗑️ Delete", key=f"delete_{i}"):
                    races.pop(i)
                    save_races(races)
                    st.rerun()
            with cols[2]:
                if st.button("📋 Training Plan", key=f"plan_{i}"):
                    st.session_state["selected_race"] = race
                    st.rerun()

    st.markdown("---")

    if "selected_race" in st.session_state:
        selected_race = st.session_state["selected_race"]
        race_date = datetime.fromisoformat(selected_race["date"]).date()
        st.header(f"Training Plan: {selected_race['name']}")
        st.write(f"Race Date: {race_date} | Distance: {selected_race['distance']} km")
        plans = load_training_plans()
        race_id = selected_race["id"]
        existing_plan = plans.get(race_id, {})

        if existing_plan and "weeks" in existing_plan:
            plan_data = []
            for week in existing_plan["weeks"]:
                start_date = datetime.fromisoformat(week["start_date"]).date()
                end_date = start_date + timedelta(days=6)
                if end_date < today:
                    status = "✅ Completed"
                elif start_date <= today <= end_date:
                    status = "⏳ Current"
                else:
                    status = "💤 Future"

                week_data = {
                    "Week": f"Week {week['week_number']}",
                    "Start Date": start_date.strftime("%Y-%m-%d"),
                    "Status": status,
                    **{day: f"{week.get(day.lower(), {}).get('distance', 0)} km: {week.get(day.lower(), {}).get('description', '')}" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
                    "Total": f"{week.get('total_distance', 0)} km",
                    "Comment": week.get("comment", "")
                }
                plan_data.append(week_data)

            plan_df = pd.DataFrame(plan_data)

            # Highlight today's cell and race day cell in the training schedule
            def highlight_func(row):
                # Only highlight the cell for today in the current week and the race day cell
                styles = ['' for _ in row.index]
                # Highlight today
                start = datetime.strptime(row["Start Date"], "%Y-%m-%d").date()
                end = start + timedelta(days=6)
                if start <= today <= end:
                    today_idx = today.weekday()
                    day_col = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][today_idx]
                    for idx, col in enumerate(row.index):
                        if col == day_col:
                            styles[idx] = 'background-color: #1EBEFF; color: #fff; font-weight: bold;'
                # Highlight race day
                if start <= race_date <= end:
                    race_idx = race_date.weekday()
                    race_col = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][race_idx]
                    for idx, col in enumerate(row.index):
                        if col == race_col:
                            # Add icons and highlight
                            val = row[col]
                            # Add icons only if not already present
                            if "🏁" not in str(val):
                                row[col] = f"🏁🎉 {val} 🎉🏁"
                            styles[idx] = 'background-color: #FFD700; color: #222; font-weight: bold;'
                return styles

            st.subheader("Training Schedule")
            st.dataframe(
                plan_df.style.apply(highlight_func, axis=1),
                use_container_width=True,
                hide_index=True
            )

            # --- Chart with race label ---
            chart_df = pd.DataFrame([
                {
                    "Week": row["Week"],
                    "Planned": float(row["Total"].replace(" km", "")),
                    "Actual": df[
                        (df["Date"].dt.date >= datetime.strptime(row["Start Date"], "%Y-%m-%d").date()) &
                        (df["Date"].dt.date <= datetime.strptime(row["Start Date"], "%Y-%m-%d").date() + timedelta(days=6))
                    ]["Distance (km)"].sum() if "Distance (km)" in df.columns else 0,
                    "Start Date": row["Start Date"]
                }
                for _, row in plan_df.iterrows()
            ])

            melted = chart_df.melt(id_vars=["Week", "Start Date"], var_name="Type", value_name="Distance")

            # Find the race week (the week containing the race date)
            race_week_idx = None
            for idx, row in chart_df.iterrows():
                start = datetime.strptime(row["Start Date"], "%Y-%m-%d").date()
                end = start + timedelta(days=6)
                if start <= race_date <= end:
                    race_week_idx = idx
                    break

            # Create the base chart
            chart = alt.Chart(melted).mark_area(line=True, point=True, interpolate='monotone', opacity=0.5).encode(
                x=alt.X("Week:N"),
                y=alt.Y("Distance:Q", title="Distance (km)", stack=None),
                color=alt.Color("Type:N", scale=alt.Scale(domain=["Planned", "Actual"], range=["#1EBEFF", "#FF9633"]))
            )

            # Add a label for the race week on the planned line
            if race_week_idx is not None:
                race_week = chart_df.iloc[race_week_idx]["Week"]
                race_distance = chart_df.iloc[race_week_idx]["Planned"]
                # Determine if race day is exactly on the start date or within the week
                is_exact_race_day = race_date == datetime.strptime(chart_df.iloc[race_week_idx]["Start Date"], "%Y-%m-%d").date()
                label_text = "🏁 Race Day 🎉" if is_exact_race_day else "🏁 Race Week"
                race_label = alt.Chart(pd.DataFrame({
                    "Week": [race_week],
                    "Distance": [race_distance],
                    "label": [label_text]
                })).mark_text(
                    align='left', baseline='bottom', dx=10, dy=-10, fontSize=16, fontWeight="bold", color="#FFD700"
                ).encode(
                    x=alt.X("Week:N"),
                    y=alt.Y("Distance:Q"),
                    text="label:N"
                )
                chart = chart + race_label

            st.altair_chart(chart.properties(height=300), use_container_width=True)

            with st.expander("🧠 AI Review of Your Progress Toward Race"):
                if st.button("🔍 Analyze Progress with AI"):
                    st.write('🧠 Sending request to OpenAI...')
                    today_str = datetime.today().strftime("%Y-%m-%d")

                    recent_runs = df.sort_values("Date", ascending=False).head(20)
                    lap_data = []
                    for _, row in recent_runs.iterrows():
                        date = row["Date"].strftime("%Y-%m-%d")
                        name = row.get("Name", "Unnamed Run")
                        summary = (
                            f"Run: {date} - {name}\n"
                            f"Distance: {row.get('Distance (km)', '-'):.2f} km | "
                            f"Pace: {row.get('Pace (min/km)', '-')} | "
                            f"Time: {row.get('Moving Time', '-')} | "
                            f"HR: {row.get('Avg HR', '-')} | Cadence: {row.get('Cadence', '-')} | "
                            f"Elev Gain: {row.get('Elevation Gain', '-')}"
                        )
                        lap_details = row.get("Lap Details", "").strip()
                        lap_data.append(summary + "\n" + lap_details)
                    lap_text = "\n\n".join(lap_data)

                    history = load_progress_feedback()
                    race_history = history.get(race_id, [])
                    previous_notes = "\n".join(f"- {item['feedback']}" for item in race_history[-2:])

                    prompt = generate_ai_prompt(selected_race, today_str, race_date, plan_df, chart_df, lap_text, previous_notes)

                    try:
                        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                        response = client.chat.completions.create(
                            model="gpt-4-turbo",
                            messages=[
                                {"role": "system", "content": "You are a professional running coach offering insights."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        feedback = response.choices[0].message.content
                        st.success("✅ Feedback received:")
                        st.markdown(f"""<div style='padding:12px; background:#1c1c1e; border-radius:10px; line-height:1.6; font-size:0.95rem;'>{feedback}</div>""", unsafe_allow_html=True)
                        save_progress_feedback(race_id, {"date": today_str, "feedback": feedback})
                        st.session_state['last_ai_feedback'] = feedback
                    except Exception as e:
                        st.error(f"Failed to analyze progress: {e}")

                render_feedback_history(race_id)
