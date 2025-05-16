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
import urllib3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEBUG_MODE = st.secrets.get("DEBUG_MODE", False)
# print ("DEBUG_MODE:", DEBUG_MODE)
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

    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)

    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">🎯</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">Race Planning</span>', unsafe_allow_html=True)

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
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.2, 0.8, 0.9, 0.9, 0.9, 0.9, 1, 2])
            with col1:
                race_name = st.text_input("Race Name", placeholder="e.g. Berlin Marathon")
            with col2:
                race_distance = st.number_input("Distance", min_value=1.0, step=0.1, placeholder="42.2")
            with col3:
                goal_time = st.text_input("Goal time", placeholder="e.g. 3:45:00")
            with col4:
                race_date = st.date_input("Race date", value=today)
            with col5:
                start_date = st.date_input("Training start date", value=today)
            with col6:
                elevation_gain = st.number_input("Elevation gain", min_value=0.0, step=10.0, placeholder="0")
            with col7:
                race_type = st.selectbox(
                    "Race type",
                    ["Road", "Trail", "Ultra"],
                    index=0,
                    key="add_race_type",
                )
                st.markdown("""
                <style>
                div[data-baseweb="select"] > div {
                    min-height: 40px !important;
                }
                </style>
                """, unsafe_allow_html=True)
            with col8:
                notes = st.text_input("Notes", placeholder="Add any notes or goals...")
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
                    # Defensive: ensure weeks is exactly num_weeks long
                    if len(weeks) != num_weeks:
                        st.error(f"Internal error: weeks list is not the expected length ({len(weeks)} vs {num_weeks})")
                        return
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
                        "training_start_date": start_date.isoformat(),
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

    day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    exp_levels = ["", "Beginner", "Intermediate", "Advanced"]

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
                    user_profile = user_info.get("user_profile", {})
                    # Remove all race-related runner profile usage
                    # Only use runner profile from user_info (set in runner_profile view)
                    st.markdown("<div class='modern-section-header'>🏁 Race Information</div>", unsafe_allow_html=True)
                    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6, r1c7, r1c8 = st.columns([1, 0.8, 0.9, 0.9, 0.9, 0.9, 1, 2])
                    with r1c1:
                        race_name = st.text_input("Race Name", value=race.get("name", ""), key=f"name_{race_id}", placeholder="e.g. Berlin Marathon")
                    with r1c2:
                        race_distance = st.number_input("Distance", min_value=1.0, step=0.1, value=float(race.get("distance", 0)), key=f"dist_{race_id}")
                    with r1c3:
                        goal_time = st.text_input("Goal time", value=race.get("goal_time", ""), key=f"goal_{race_id}", placeholder="e.g. 3:45:00")
                    with r1c4:
                        race_date = st.date_input("Race date", value=pd.to_datetime(race.get("date", today)), key=f"date_{race_id}")
                    with r1c5:
                        start_date = st.date_input("Training start date", value=pd.to_datetime(race.get("date", today)), key=f"start_{race_id}")
                    with r1c6:
                        elevation_gain = st.number_input("Elevation gain", min_value=0.0, step=10.0, value=float(race.get("elevation_gain", 0)), key=f"elev_{race_id}")
                    with r1c7:
                        race_type = st.selectbox("Race type", ["Road", "Trail", "Ultra"], index=["Road", "Trail", "Ultra"].index(race.get("type", "Road")), key=f"type_{race_id}")
                        st.markdown("""
                        <style>
                        div[data-baseweb=\"select\"] > div {
                            min-height: 50px !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                    with r1c8:
                        notes = st.text_input("Notes", value=race.get("notes", ""), key=f"notes_{race_id}", placeholder="Add any notes or goals...")
                    
                    if st.button("💾 Save Race Info", key=f"save_raceinfo_{race_id}"):
                        old_race_date = pd.to_datetime(race.get("date", race_date)).date() if race.get("date") else race_date
                        old_start_date = start_date
                        new_race_date = race_date
                        new_start_date = start_date
                        plan = plans.get(race_id, {"weeks": []})
                        weeks = plan.get("weeks", [])
                        weeks = sorted(weeks, key=lambda w: w.get("start_date", ""))
                        new_plan_start = new_start_date - timedelta(days=new_start_date.weekday())
                        new_plan_race = new_race_date
                        new_plan_race_week_start = new_plan_race - timedelta(days=new_plan_race.weekday())
                        new_num_weeks = max(1, ((new_plan_race_week_start - new_plan_start).days // 7) + 1)
                        new_week_starts = [new_plan_start + timedelta(days=7*w) for w in range(new_num_weeks)]
                        old_weeks_by_start = {pd.to_datetime(w.get("start_date")).date(): w for w in weeks if w.get("start_date")}
                        new_weeks = []
                        for i, week_start in enumerate(new_week_starts):
                            week_date = week_start
                            old_week = old_weeks_by_start.get(week_date)
                            if old_week:
                                new_week = dict(old_week)
                            else:
                                new_week = {
                                    "week_number": i+1,
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
                            new_week["week_number"] = i+1
                            new_week["start_date"] = week_start.strftime("%Y-%m-%d")
                            new_weeks.append(new_week)
                        if new_weeks:
                            race_week_idx = new_plan_race.weekday()
                            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                            last_week = new_weeks[-1]
                            last_week[day_names[race_week_idx]] = {"distance": race_distance, "description": "Race day"}
                        if "runner_profile" in race:
                            del race["runner_profile"]
                        for r in races:
                            if r.get("id") == race_id:
                                r["name"] = race_name
                                r["distance"] = race_distance
                                r["goal_time"] = goal_time
                                r["date"] = race_date.isoformat() if hasattr(race_date, 'isoformat') else str(race_date)
                                r["training_start_date"] = start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date)
                                r["elevation_gain"] = elevation_gain
                                r["type"] = race_type
                                r["notes"] = notes
                                break
                        save_races(races, user_info, gist_id, filename, token)
                        save_training_plan(race_id, {"weeks": new_weeks}, user_info, gist_id, filename, token)
                        st.success("Race info and plan updated for new dates.")
                        st.rerun()
                    
                    st.markdown("<hr class='modern-hr'/>", unsafe_allow_html=True)

                    profile_prefix = f"{race_id}_{i}"
                    
                    ai_plan_active = st.session_state.get(f"ai_plan_mode_{race_id}", False)
                    gsheet_active = st.session_state.get(f"gsheet_mode_{race_id}", False)
                    action_col, ai_input_col = st.columns([1, 6], gap="small")
                    with action_col:
                        if st.button("🤖 AI Plan", key=f"ai_plan_btn_{race_id}", use_container_width=True):
                            st.session_state[f"ai_plan_mode_{race_id}"] = not ai_plan_active
                            st.session_state[f"gsheet_mode_{race_id}"] = False
                        if st.button("📄 Google Sheet Plan", key=f"gsheet_btn_{race_id}", use_container_width=True):
                            st.session_state[f"gsheet_mode_{race_id}"] = not gsheet_active
                            st.session_state[f"ai_plan_mode_{race_id}"] = False
                    with ai_input_col:
                        if st.session_state.get(f"ai_plan_mode_{race_id}", False):
                            c1, c2, c3 = st.columns([2.5, 4, 1.5], gap="small")
                            with c1:
                                st.markdown("<span style='color:#FF9633;font-size:0.92rem;'>⚠️ Update your runner profile before sending to AI.</span>", unsafe_allow_html=True)
                            with c2:
                                ai_note = st.text_input(
                                    "AI Notes",  
                                    value=st.session_state.get(f"ai_note_{race_id}", ""),
                                    key=f"ai_note_{race_id}",
                                    placeholder="Add notes for AI (optional)",
                                    label_visibility="collapsed"
                                )
                            with c3:
                                if st.button("Send to AI", key=f"send_ai_{race_id}"):
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
                                            with open(DEBUG_AI_PLAN_PATH, 'r', encoding='utf-8') as f:
                                                ai_table_md = f.read().strip()
                                                if ai_table_md.startswith("'") and ai_table_md.endswith("'"):
                                                    ai_table_md = ai_table_md[1:-1]
                                                ai_table_md = ai_table_md.replace("\\n", "\n")
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
                                        from utils.parse_helper import parse_training_plan
                                        df = parse_training_plan(ai_table_md)
                                        required_cols = ["Week","Start Date","Status","Monday","Tuesday",
                                                         "Wednesday","Thursday","Friday","Saturday",
                                                         "Sunday","Comment"]
                                        if df is None or not all(col in df.columns for col in required_cols):
                                            st.error("AI plan table format is invalid. Please try again or edit manually.")
                                        else:
                                            new_weeks = []
                                            for _, row in df.iterrows():
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
                                                week["total_distance"] = sum(
                                                    week[day]["distance"] for day in [
                                                        "monday","tuesday","wednesday",
                                                        "thursday","friday","saturday","sunday"
                                                    ]
                                                )
                                                new_weeks.append(week)
                                            st.session_state[f"plan_buffer_{race_id}"] = new_weeks
                                            st.success("AI plan loaded. Don't forget to Save Plan to keep changes.")
                                            st.session_state[f"ai_plan_mode_{race_id}"] = False
                                    except Exception as e:
                                        st.error(f"AI error: {e}")
                        elif st.session_state.get(f"gsheet_mode_{race_id}", False):
                            c1, c2, c3 = st.columns([2.5, 4, 1.5], gap="small")
                            with c1:
                                st.markdown("<span style='color:#FF9633;font-size:0.92rem;'>⚠️ Make sure your Google Sheet format matches the template.</span>", unsafe_allow_html=True)
                            with c2:
                                gsheet_url = st.text_input(
                                    "Google Sheet URL",  
                                    value=st.session_state.get(f"gsheet_url_{race_id}", ""),
                                    key=f"gsheet_url_{race_id}",
                                    placeholder="Paste Google Sheet URL",
                                    label_visibility="collapsed"
                                )
                            with c3:
                                if st.button("Upload GSheet", key=f"upload_gsheet_{race_id}"):
                                    from utils.gsheet import fetch_gsheet_plan
                                    gsheet_df = fetch_gsheet_plan(gsheet_url)
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

                    # --- AI Analysis Section for this race ---
                    st.markdown("<hr/>", unsafe_allow_html=True)
                    # --- AI Analysis History (newest first) ---
                    st.markdown("<div class='modern-subheader'>🧠 AI Analysis History</div>", unsafe_allow_html=True)
                    ai_history_dict = load_progress_feedback(user_info, gist_id, filename, token)
                    if isinstance(ai_history_dict, dict):
                        ai_history = ai_history_dict.get(race_id, [])
                    else:
                        ai_history = []
                    # --- New AI Analysis Button (moved above history) ---
                    if st.button(f"🧠 Run AI Analysis for this race", key=f"ai_analysis_btn_{race_id}"):
                        # print ("butt pressed 1")

                        # Prepare data for AI prompt
                        today_str = str(datetime.today().date())
                        race_date = race.get('date', '')
                        # Defensive: ensure plan_df columns exist
                        plan_weeks = plans.get(race_id, {}).get('weeks', [])
                        if plan_weeks and isinstance(plan_weeks, list):
                            plan_df = pd.DataFrame(plan_weeks)
                            if 'start_date' in plan_df.columns:
                                plan_df = plan_df.rename(columns={
                                    'start_date': 'Start Date',
                                    'status': 'Status',
                                    'monday': 'Monday',
                                    'tuesday': 'Tuesday',
                                    'wednesday': 'Wednesday',
                                    'thursday': 'Thursday',
                                    'friday': 'Friday',
                                    'saturday': 'Saturday',
                                    'sunday': 'Sunday',
                                    'comment': 'Comment',
                                    'week_number': 'Week'
                                })
                        else:
                            plan_df = pd.DataFrame()
                        # print ("butt 3")

                        chart_df = pd.DataFrame()  # You may want to use actual chart data if available
                        lap_text = ''  # You may want to use actual lap/run data if available
                        # Robustly join summaries from ai_history if it is a list of dicts
                        if isinstance(ai_history, list):
                            previous_notes = '\n\n'.join([
                                entry.get('summary', '') for entry in ai_history if isinstance(entry, dict) and 'summary' in entry
                            ])
                        else:
                            previous_notes = ''
                        # print ("butt 4")
                        from views.ai_prompt import generate_ai_prompt
                        # print ("but pressed 2")
                        prompt = generate_ai_prompt(race, today_str, race_date, plan_df, chart_df, lap_text, previous_notes)
                        # print (prompt)
                        ai_feedback = None
                        ai_feedback_date = datetime.now().strftime('%Y-%m-%d %H:%M')
                        try:
                            # print (DEBUG_MODE, "    0000 debbbbbbbbbugggg")
                            if DEBUG_MODE:
                                ai_feedback = 'This is a debug AI analysis summary.'
                            else:
                                client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                                response = client.chat.completions.create(
                                    model="gpt-4-turbo",
                                    messages=[
                                        {"role": "system", "content": "You are a professional running coach."},
                                        {"role": "user", "content": prompt}
                                    ]
                                )
                                ai_feedback = response.choices[0].message.content.strip()
                        except Exception as e:
                            st.error(f"AI error: {e}")
                            ai_feedback = None
                        if ai_feedback:
                            entry = {
                                'date': ai_feedback_date,
                                'summary': ai_feedback
                            }
                            save_progress_feedback(race_id, entry, user_info, gist_id, filename, token)
                            st.success("AI analysis saved!")
                            st.rerun()
                    if ai_history:
                        for entry in reversed(ai_history):
                            st.markdown(f"<details class='ai-feedback-card'>"
                                        f"<summary class='ai-feedback-summary'>"
                                        f"<span class='ai-feedback-icon'>🤖</span>"
                                        f"<span>AI Feedback</span>"
                                        f"<span class='ai-feedback-date'>{entry.get('date', 'Unknown Date')}</span>"
                                        f"</summary>"
                                        f"<div class='ai-feedback-content'>{entry.get('summary', '[No summary]')}</div>"
                                        f"</details>", unsafe_allow_html=True)
                    else:
                        st.info("No AI analysis history for this race yet.")
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
