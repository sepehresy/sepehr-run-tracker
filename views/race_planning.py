import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from openai import OpenAI
from views.ai_prompt import generate_ai_prompt, generate_ai_plan_prompt
from utils.gist_helpers import load_gist_data, save_gist_data
import openai
from utils.gsheet import fetch_gsheet_plan
from utils.parse_helper import parse_markdown_plan_table, parse_csv_plan_table, load_csv_from_text, parse_training_plan

DEBUG_MODE = st.secrets.get("DEBUG_MODE", False)
print ("DEBUG_MODE:", DEBUG_MODE)
DEBUG_AI_PLAN_PATH = "data/analyses/ai_plan_debug3.txt"

def load_gist_race_data(user_info, gist_id, filename, token):
    data = load_gist_data(gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    if user_key not in data:
        data[user_key] = {"races": [], "training_plans": {}, "progress_feedback": {}}
    return data

def save_gist_race_data(data, user_info, gist_id, filename, token):
    return save_gist_data(gist_id, filename, token, data)

def load_saved_races(user_info, gist_id, filename, token):
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    return data[user_key].get("races", [])

def save_races(races, user_info, gist_id, filename, token):
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    data[user_key]["races"] = races
    return save_gist_race_data(data, user_info, gist_id, filename, token)

def load_training_plans(user_info, gist_id, filename, token):
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    return data[user_key].get("training_plans", {})

def save_training_plan(race_id, plan, user_info, gist_id, filename, token):
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    data[user_key].setdefault("training_plans", {})
    data[user_key]["training_plans"][race_id] = plan
    return save_gist_race_data(data, user_info, gist_id, filename, token)

def load_progress_feedback(user_info, gist_id, filename, token):
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    return data[user_key].get("progress_feedback", {})

def save_progress_feedback(race_id, entry, user_info, gist_id, filename, token):
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    data[user_key].setdefault("progress_feedback", {})
    data[user_key]["progress_feedback"].setdefault(race_id, []).append(entry)
    return save_gist_race_data(data, user_info, gist_id, filename, token)

def render_feedback_history(race_id, user_info, gist_id, filename, token):
    race_history = load_progress_feedback(user_info, gist_id, filename, token).get(race_id, [])
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
                    all_history = load_progress_feedback(user_info, gist_id, filename, token)
                    feedback_list = all_history.get(race_id, [])
                    del feedback_list[len(feedback_list)-1-i]
                    all_history[race_id] = feedback_list
                    save_progress_feedback(race_id, feedback_list, user_info, gist_id, filename, token)
                    st.success("Feedback removed.")
                    st.rerun()

def render_race_planning(df, today, user_info, gist_id, gist_filename, github_token):
    user_key = user_info["USER_KEY"]
    gist_id = user_info["GIST_ID"]
    filename = f"{user_key}.json"
    token = github_token

    if isinstance(today, datetime):
        today = today.date()
    if "race_edit_state" not in st.session_state:
        st.session_state["race_edit_state"] = {}
    if "plan_edit_buffer" not in st.session_state:
        st.session_state["plan_edit_buffer"] = {}
    if "plan_edit_meta" not in st.session_state:
        st.session_state["plan_edit_meta"] = {}

    st.markdown("""
    <style>
    .race-section {border-radius: 14px; margin-bottom: 28px; background: #fff; box-shadow: 0 2px 16px rgba(30,40,60,0.07); border: 1px solid #e6e6e6;}
    .race-header {padding: 20px 28px; font-size: 1.3rem; font-weight: 600; color: #1EBEFF; background: #f7fafd; border-radius: 14px 14px 0 0; letter-spacing: 0.5px;}
    .race-meta {color: #888; font-size: 1.05rem; margin-bottom: 8px;}
    .race-actions {margin-top: 8px;}
    .race-divider {border-bottom: 1px solid #f0f0f0; margin: 0 0 18px 0;}
    .plan-toolbar {margin-bottom: 18px;}
    .plan-toolbar .stButton>button {margin-right: 12px;}
    .plan-table {margin-bottom: 18px;}
    .stButton>button {border-radius: 8px !important; background: #1EBEFF !important; color: #fff !important; border: none !important; font-weight: 500; padding: 8px 18px; transition: background 0.2s;}
    .stButton>button:hover {background: #009fd9 !important;}
    .stTextInput>div>input, .stNumberInput>div>input, .stTextArea textarea, .stSelectbox>div>div {
        border-radius: 8px; border: 1px solid #e6e6e6; background: #23242a !important; color: #e6e6e6 !important; font-size: 1rem;
    }
    .stDataFrame, .stDataEditor {background: #f7fafd; border-radius: 10px;}
    .stExpanderHeader {font-size: 1.1rem; font-weight: 500; color: #1EBEFF;}
    .stAlert {border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='display:flex;align-items:center;gap:12px;margin-bottom:18px;'>
        <span style='font-size:2.1rem;'>🏁</span>
        <span style='font-size:1.7rem;font-weight:600;letter-spacing:0.5px;color:#222;'>Race Planning</span>
    </div>
    """, unsafe_allow_html=True)

    if "add_race_expanded" not in st.session_state:
        st.session_state["add_race_expanded"] = False
    else:
        st.session_state["add_race_expanded"] = False
    races = load_saved_races(user_info, gist_id, filename, token)
    plans = load_training_plans(user_info, gist_id, filename, token)

    ai_enabled = False
    # Features can be in 'Features' or 'features' depending on secrets.toml
    features = user_info.get('Features', []) or user_info.get('features', [])
    # print (user_info,features)
    if isinstance(features, str):
        import json
        try:
            features = json.loads(features)
        except Exception:
            features = []
    ai_enabled = 'ai' in features

    with st.expander("➕ Add New Race", expanded=st.session_state["add_race_expanded"]):
        with st.form("add_race_form"):
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.2,1,1,1,1,1,1,2])
            with col1:
                race_name = st.text_input("Race Name", placeholder="e.g. Berlin Marathon")
            with col2:
                goal_time = st.text_input("Goal Time (e.g., 3:45:00)", placeholder="3:45:00")
            with col3:
                race_date = st.date_input("Race Date", value=today)
            with col4:
                race_distance = st.number_input("Distance (km)", min_value=1.0, step=0.1, placeholder="42.2")
            with col5:
                start_date = st.date_input("Training Start Date", value=today)
            with col6:
                race_type = st.selectbox("Race Type", ["Road", "Trail", "Track", "Virtual"], index=0)
            with col7:
                elevation_gain = st.number_input("Elevation Gain (m)", min_value=0.0, step=10.0, placeholder="0")
            with col8:
                notes = st.text_area("Notes (optional)", placeholder="Add any notes or goals...", height=70)
            submit = st.form_submit_button("Create Race")
            
            if submit:
                st.session_state["add_race_expanded"] = False
                if any(r["name"].strip().lower() == race_name.strip().lower() for r in races):
                    st.error("A race with this name already exists. Please choose a different name.")
                else:
                    plan_start_date = start_date - timedelta(days=start_date.weekday())
                    plan_race_date = race_date
                    plan_race_week_start = plan_race_date - timedelta(days=plan_race_date.weekday())
                    num_weeks = max(1, ((plan_race_week_start - plan_start_date).days // 7) + 1)
                    weeks = []
                    for w in range(num_weeks):
                        week_start = plan_start_date + timedelta(days=7*w)
                        week = {
                            "week_number": w+1,
                            "start_date": week_start.strftime("%Y-%m-%d"),
                            "status": "💤 Future",
                            "monday": {"distance": 0.0, "description": "Rest"},
                            "tuesday": {"distance": 0.0, "description": "Rest"},
                            "wednesday": {"distance": 0.0, "description": "Rest"},
                            "thursday": {"distance": 0.0, "description": "Rest"},
                            "friday": {"distance": 0.0, "description": "Rest"},
                            "saturday": {"distance": 0.0, "description": "Rest"},
                            "sunday": {"distance": 0.0, "description": "Rest"},
                            "comment": ""
                        }
                        if week_start == plan_race_week_start:
                            race_week_idx = plan_race_date.weekday()
                            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                            week[day_names[race_week_idx]] = {"distance": race_distance, "description": "Race day"}
                        weeks.append(week)
                    new_race = {
                        "id": f"race_{len(races)+1}",
                        "name": race_name,
                        "date": race_date.isoformat(),
                        "distance": race_distance,
                        "type": race_type,
                        "elevation_gain": elevation_gain,
                        "goal_time": goal_time,
                        "notes": notes,
                        "created_at": datetime.now().isoformat(),
                        "runner_profile": {
                            "experience": "",
                            "weekly_km": 0.0,
                            "training_start_date": start_date.isoformat(),
                            "recent_race": "",
                            "goal_time": goal_time,
                            "available_days": [],
                            "limitations": "",
                            "preferred_workout_types": "",
                            "other_notes": ""
                        }
                    }
                    races.insert(0, new_race)
                    save_races(races, user_info, gist_id, filename, token)
                    plans = load_training_plans(user_info, gist_id, filename, token)
                    plans[new_race["id"]] = {"weeks": weeks}
                    save_training_plan(new_race["id"], {"weeks": weeks}, user_info, gist_id, filename, token)
                    st.success(f"Race '{race_name}' created!")
                    st.session_state["add_race_expanded"] = False
                    st.rerun()

    if not races:
        st.info("No races added yet. Add a race to get started.")
        return

    

    for i, race in enumerate(races):
        try:
            race_id = race.get("id", f"race_{i+1}")
            plan = plans.get(race_id, {})
            expanded = st.session_state["race_edit_state"].get(race_id, False)
            with st.container():
                race_header_col, delete_col = st.columns([0.93, 0.07])
                with race_header_col:
                    exp_label = f"🏁 {race.get('name', 'Unnamed Race')} ({race.get('date', '-')})"
                with delete_col:
                    delete_btn = st.button("🗑️", key=f"delete_race_{race_id}", help="Delete this race")
                if delete_btn:
                    races = [r for r in races if r.get("id") != race_id]
                    save_races(races, user_info, gist_id, filename, token)
                    st.success("Race deleted.")
                    st.rerun()
                with st.expander(exp_label, expanded=expanded):
                    st.session_state["race_edit_state"][race_id] = expanded
                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.2,1,1,1,1,1,1,2])
                    with col1:
                        race_name = st.text_input("Race Name", value=race.get("name", ""), key=f"name_{race_id}")
                    with col2:
                        start_date = st.date_input("Start", value=pd.to_datetime(race.get("runner_profile", {}).get("training_start_date", race.get("date", today))), key=f"start_{race_id}")
                    with col3:
                        race_date = st.date_input("Race", value=pd.to_datetime(race.get("date", today)), key=f"date_{race_id}")
                    with col4:
                        race_distance = st.number_input("Dist (km)", min_value=1.0, step=0.1, value=float(race.get("distance", 0)), key=f"dist_{race_id}")
                    with col5:
                        race_type = st.selectbox("Type", ["Road", "Trail", "Track", "Virtual"], index=["Road", "Trail", "Track", "Virtual"].index(race.get("type", "Road")), key=f"type_{race_id}")
                    with col6:
                        elevation_gain = st.number_input("Elev (m)", min_value=0.0, step=10.0, value=float(race.get("elevation_gain", 0)), key=f"elev_{race_id}")
                    with col7:
                        goal_time = st.text_input("Goal Time", value=race.get("goal_time", ""), key=f"goal_{race_id}")
                    with col8:
                        notes = st.text_area("Notes", value=race.get("notes", ""), key=f"notes_{race_id}", height=70)
                    b1, b2, b3 = st.columns([1,1,1])
                    if b1.button("Save Race Info", key=f"save_raceinfo_{race_id}"):
                        race["name"] = race_name
                        race["date"] = race_date.isoformat()
                        race["distance"] = race_distance
                        race["type"] = race_type
                        race["elevation_gain"] = elevation_gain
                        race["goal_time"] = goal_time
                        race["notes"] = notes
                        if "runner_profile" not in race or not isinstance(race["runner_profile"], dict):
                            race["runner_profile"] = {}
                        race["runner_profile"]["training_start_date"] = start_date.isoformat()
                        race["runner_profile"]["goal_time"] = goal_time
                        save_races(races, user_info, gist_id, filename, token)
                        st.success("Race info updated.")
                    # --- AI Plan Button ---
                    if ai_enabled:
                        if b2.button("AI Plan", key=f"ai_plan_btn_{race_id}"):
                            st.session_state[f"ai_plan_mode_{race_id}"] = True
                    else:
                        st.button("AI Plan (Locked)", key=f"ai_plan_btn_{race_id}", disabled=True, help="You do not have access to AI features.")
                    if st.session_state.get(f"ai_plan_mode_{race_id}", False):
                        st.info("Enter extra notes for the AI prompt (optional):")
                        ai_note = st.text_area("AI Notes", key=f"ai_note_{race_id}")
                        c1, c2 = st.columns([1,1])
                        if c1.button("Send to AI", key=f"send_ai_{race_id}"):
                            # --- Initialize default table skeleton before AI load ---
                            # Use existing plan weeks to set up skeleton rows
                            current_weeks = plan.get("weeks", [])
                            default_weeks = []
                            for w in current_weeks:
                                default_weeks.append({
                                    "week_number": w.get("week_number"),
                                    "start_date": w.get("start_date"),
                                    "status": "",
                                    "monday": {"distance": 0.0, "description": ""},
                                    "tuesday": {"distance": 0.0, "description": ""},
                                    "wednesday": {"distance": 0.0, "description": ""},
                                    "thursday": {"distance": 0.0, "description": ""},
                                    "friday": {"distance": 0.0, "description": ""},
                                    "saturday": {"distance": 0.0, "description": ""},
                                    "sunday": {"distance": 0.0, "description": ""},
                                    "comment": "",
                                    "total_distance": 0.0
                                })
                            st.session_state[f"plan_buffer_{race_id}"] = default_weeks
                            from views.ai_prompt import generate_ai_plan_prompt
                            prompt = generate_ai_plan_prompt(race, ai_note)
                            try:
                                if DEBUG_MODE:
                                    print("DEBUG_MODE: AI Plan", DEBUG_MODE)
                                    with open(DEBUG_AI_PLAN_PATH, 'r', encoding='utf-8') as f:
                                        ai_table_md = f.read().strip()
                                        if ai_table_md.startswith("'") and ai_table_md.endswith("'"):
                                            ai_table_md = ai_table_md[1:-1]
                                        ai_table_md = ai_table_md.replace("\\n", "\n")
                                        print("ai_table_md - \n", ai_table_md)
                                else:
                                    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                                    response = client.chat.completions.create(
                                        model="gpt-4-turbo",
                                        messages=[
                                            {"role": "system", "content": "You are a professional running coach."},
                                            {"role": "user", "content": prompt}
                                        ]
                                    )
                                    ai_table_md = response.choices[0].message.content
                                
                                # df = parse_csv_plan_table(ai_table_md)
                                df = parse_training_plan (ai_table_md)
                                print ("AI Plan DataFrame:\n", df)
                                # df = parse_csv_plan_table(df)
                                required_cols = ["Week","Start Date","Status","Monday","Tuesday",
                                                 "Wednesday","Thursday","Friday","Saturday",
                                                 "Sunday","Comment"]
                                if df is None or not all(col in df.columns for col in required_cols):
                                    st.error("AI plan table format is invalid. Please try again or edit manually.")
                                else:
                                    new_weeks = []
                                    for _, row in df.iterrows():
                                        # Build week dictionary
                                        week = {
                                            "week_number": int(str(row["Week"]).replace("Week ", "").strip())
                                                if str(row["Week"]).replace("Week ", "").strip().isdigit()
                                                else row["Week"],
                                            "start_date": str(row["Start Date"]),
                                            "status": row["Status"],
                                            "monday": _parse_day_cell(row["Monday"]),
                                            "tuesday": _parse_day_cell(row["Tuesday"]),
                                            "wednesday": _parse_day_cell(row["Wednesday"]),
                                            "thursday": _parse_day_cell(row["Thursday"]),
                                            "friday": _parse_day_cell(row["Friday"]),
                                            "saturday": _parse_day_cell(row["Saturday"]),
                                            "sunday": _parse_day_cell(row["Sunday"]),
                                            "comment": row["Comment"]
                                        }
                                        # Calculate total distance
                                        week["total_distance"] = sum(
                                            week[day]["distance"] for day in [
                                                "monday","tuesday","wednesday",
                                                "thursday","friday","saturday","sunday"
                                            ]
                                        )
                                        new_weeks.append(week)
                                    # write the new plan into session
                                    st.session_state[f"plan_buffer_{race_id}"] = new_weeks
                                    st.success("AI plan loaded. Don't forget to Save Plan to keep changes.")
                                    st.session_state[f"ai_plan_mode_{race_id}"] = False
                            except Exception as e:
                                st.error(f"AI error: {e}")
                        if c2.button("Cancel", key=f"cancel_ai_{race_id}"):
                            st.session_state[f"ai_plan_mode_{race_id}"] = False
                    if b3.button("Google Sheet Plan", key=f"gsheet_btn_{race_id}"):
                        st.session_state[f"gsheet_mode_{race_id}"] = True
                    if st.session_state.get(f"gsheet_mode_{race_id}", False):
                        st.info("Enter Google Sheet URL:")
                        gsheet_url = st.text_input("Google Sheet URL", key=f"gsheet_url_{race_id}")
                        c1, c2 = st.columns([1,1])
                        if c1.button("Fetch Plan", key=f"fetch_gsheet_{race_id}"):
                            from utils.gsheet import fetch_gsheet_plan
                            gsheet_df = fetch_gsheet_plan(gsheet_url)
                            # print (gsheet_url, gsheet_df)
                            if gsheet_df is not None:
                                required_cols = ["Week", "Start Date", "Status", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Comment"]
                                if not all(col in gsheet_df.columns for col in required_cols):
                                    st.error("Google Sheet plan format is invalid. Please use the template.")
                                else:
                                    new_weeks = []
                                    for _, row in gsheet_df.iterrows():
                                        week = {
                                            "week_number": int(str(row["Week"]).replace("Week ", "").strip()),
                                            "start_date": str(row["Start Date"]),
                                            "status": row["Status"],
                                            "monday": _parse_day_cell(row["Monday"]),
                                            "tuesday": _parse_day_cell(row["Tuesday"]),
                                            "wednesday": _parse_day_cell(row["Wednesday"]),
                                            "thursday": _parse_day_cell(row["Thursday"]),
                                            "friday": _parse_day_cell(row["Friday"]),
                                            "saturday": _parse_day_cell(row["Saturday"]),
                                            "sunday": _parse_day_cell(row["Sunday"]),
                                            "comment": row["Comment"]
                                        }
                                        week["total_distance"] = sum([
                                            week[day]["distance"] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                                        ])
                                        new_weeks.append(week)
                                    st.session_state[f"plan_buffer_{race_id}"] = new_weeks
                                    st.success("Google Sheet plan loaded. Don't forget to Save Plan to keep changes.")
                                    st.session_state[f"gsheet_mode_{race_id}"] = False
                        if c2.button("Cancel", key=f"cancel_gsheet_{race_id}"):
                            st.session_state[f"gsheet_mode_{race_id}"] = False

                    weeks = st.session_state.get(f"plan_buffer_{race_id}", plan.get("weeks", []))
                    for w in weeks:
                        w.setdefault("status", "💤 Future")
                        w.setdefault("monday", {"distance": 0.0, "description": "Rest"})
                        w.setdefault("tuesday", {"distance": 0.0, "description": "Rest"})
                        w.setdefault("wednesday", {"distance": 0.0, "description": "Rest"})
                        w.setdefault("thursday", {"distance": 0.0, "description": "Rest"})
                        w.setdefault("friday", {"distance": 0.0, "description": "Rest"})
                        w.setdefault("saturday", {"distance": 0.0, "description": "Rest"})
                        w.setdefault("sunday", {"distance": 0.0, "description": "Rest"})
                        w.setdefault("comment", "")
                    plan_df = pd.DataFrame([
                        {
                            "Week": f"Week {w.get('week_number', idx+1)}",
                            "Start Date": w.get("start_date", ""),
                            "Status": w.get("status", "💤 Future"),
                            "Monday": f"{w.get('monday', {}).get('distance', 0)} km: {w.get('monday', {}).get('description', '')}",
                            "Tuesday": f"{w.get('tuesday', {}).get('distance', 0)} km: {w.get('tuesday', {}).get('description', '')}",
                            "Wednesday": f"{w.get('wednesday', {}).get('distance', 0)} km: {w.get('wednesday', {}).get('description', '')}",
                            "Thursday": f"{w.get('thursday', {}).get('distance', 0)} km: {w.get('thursday', {}).get('description', '')}",
                            "Friday": f"{w.get('friday', {}).get('distance', 0)} km: {w.get('friday', {}).get('description', '')}",
                            "Saturday": f"{w.get('saturday', {}).get('distance', 0)} km: {w.get('saturday', {}).get('description', '')}",
                            "Sunday": f"{w.get('sunday', {}).get('distance', 0)} km: {w.get('sunday', {}).get('description', '')}",
                            "Comment": w.get("comment", "")
                        }
                        for idx, w in enumerate(weeks)
                    ])
                    total_col = []
                    for idx, row in plan_df.iterrows():
                        week_total = 0.0
                        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                            try:
                                dist, _ = str(row[day]).split(" km:", 1)
                                week_total += float(dist.strip())
                            except Exception:
                                pass
                        total_col.append(f"{week_total:.1f} km")
                    plan_df["Total"] = total_col
                    edited = st.data_editor(
                        plan_df,
                        num_rows="dynamic",
                        use_container_width=True,
                        disabled=["Total"],
                        key=f"manual_plan_editor_{race_id}_always"
                    )
                    if st.button("💾 Save Plan", key=f"save_plan_{race_id}_always"):
                        for idx, row in edited.iterrows():
                            for d, day in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                                try:
                                    dist, desc = str(row[day.capitalize()]).split(" km:", 1)
                                    weeks[idx][day] = {"distance": float(dist.strip()), "description": desc.strip()}
                                except Exception:
                                    weeks[idx][day] = {"distance": 0.0, "description": str(row[day.capitalize()])}
                            weeks[idx]["total_distance"] = sum([
                                weeks[idx].get(day, {}).get("distance", 0.0)
                                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                            ])
                            weeks[idx]["comment"] = row["Comment"]
                        save_training_plan(race_id, {"weeks": weeks}, user_info, gist_id, filename, token)
                        st.success("Training plan saved!")
                        st.rerun()

                    chart_df = edited.copy()
                    chart_df["WeekNum"] = chart_df["Week"].str.extract(r"(\d+)").astype(int)
                    chart_df["Planned"] = chart_df["Total"].apply(lambda x: float(str(x).replace(" km", "")))
                    chart_df["Actual"] = [
                        df[
                            (df["Date"].dt.date >= pd.to_datetime(row["Start Date"]).date()) &
                            (df["Date"].dt.date <= pd.to_datetime(row["Start Date"]).date() + timedelta(days=6))
                        ]["Distance (km)"].sum() if "Distance (km)" in df.columns else 0
                        for _, row in chart_df.iterrows()
                    ]
                    chart_df = chart_df.sort_values("WeekNum").reset_index(drop=True)
                    melted = chart_df.melt(id_vars=["Week", "WeekNum", "Start Date"], value_vars=["Planned", "Actual"], var_name="Type", value_name="Distance")
                    race_week_idx = None
                    for idx2, row in chart_df.iterrows():
                        try:
                            start_str = str(row["Start Date"])
                            start = pd.to_datetime(start_str, errors="coerce")
                            if pd.isnull(start):
                                continue
                            start = start.date()
                            end = start + timedelta(days=6)
                            race_date_val = pd.to_datetime(race.get("date", ""), errors="coerce")
                            if pd.isnull(race_date_val):
                                continue
                            race_date_val = race_date_val.date()
                            if start <= race_date_val <= end:
                                race_week_idx = idx2
                                break
                        except Exception:
                            continue
                    chart = alt.Chart(melted).mark_area(line=True, point=True, interpolate='monotone', opacity=0.5).encode(
                        x=alt.X("WeekNum:O", title="Week", sort="ascending", axis=alt.Axis(labelAngle=-45, labelOverlap=True)),
                        y=alt.Y("Distance:Q", title="Distance (km)", stack=None),
                        color=alt.Color("Type:N", scale=alt.Scale(domain=["Planned", "Actual"], range=["#1EBEFF", "#FF9633"]))
                    )
                    if race_week_idx is not None:
                        race_weeknum = chart_df.iloc[race_week_idx]["WeekNum"]
                        race_distance = chart_df.iloc[race_week_idx]["Planned"]
                        is_exact_race_day = False
                        try:
                            is_exact_race_day = pd.to_datetime(race.get("date", "")).date() == pd.to_datetime(chart_df.iloc[race_week_idx]["Start Date"]).date()
                        except Exception:
                            pass
                        label_text = "🏁 Race Day 🎉" if is_exact_race_day else "🏁 Race Week"
                        race_label = alt.Chart(pd.DataFrame({
                            "WeekNum": [race_weeknum],
                            "Distance": [race_distance],
                            "label": [label_text]
                        })).mark_text(
                            align='left', baseline='bottom', dx=10, dy=-10, fontSize=16, fontWeight="bold", color="#FFD700"
                        ).encode(
                            x=alt.X("WeekNum:O"),
                            y=alt.Y("Distance:Q"),
                            text="label:N"
                        )
                        chart = chart + race_label
                    st.altair_chart(chart.properties(height=260), use_container_width=True)

                    try:
                        render_feedback_history(race_id, user_info, gist_id, filename, token)
                    except Exception as e:
                        st.error(f"Error displaying feedback: {e}")

        except Exception as e:
            st.error(f"Error rendering race section: {e}")

def _parse_day_cell(cell):
    try:
        dist, desc = str(cell).split(" km:", 1)
        return {"distance": float(dist.strip()), "description": desc.strip()}
    except Exception:
        return {"distance": 0.0, "description": str(cell)}
