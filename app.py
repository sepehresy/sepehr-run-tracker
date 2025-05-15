import streamlit as st
import pandas as pd
from datetime import datetime
from views.summary import render_summary
from views.activities import render_activities
from views.ai_analysis import render_ai_analysis
from views.race_planning import render_race_planning
from views.runner_profile import render_runner_profile
import requests
import json
from utils.gist_helpers import load_gist_data, save_gist_data
import io
import certifi
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set Streamlit app config
# st.set_page_config(page_title="Sepehr's Running Dashboard", layout="wide", theme={"base": "light"})
st.set_page_config(page_title="Sepehr's Running Dashboard", layout="wide")

# --- Authenticate user ---
def load_users():
    raw_users = st.secrets["users"]
    return {username: json.loads(data) for username, data in raw_users.items()}

def authenticate(username, password, users):
    if username in users and users[username]["password"] == password:
        return users[username]
    return None

# --- Login management ---
if 'user_authenticated' not in st.session_state:
    st.session_state['user_authenticated'] = False

if not st.session_state.user_authenticated:
    st.title("🔒 Login to Running Dashboard")
    users = load_users()

    with st.form("Login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        st.session_state['reload_data'] = True
        user_info = authenticate(username, password, users)
        if user_info:
            st.session_state.user_authenticated = True
            st.session_state.user_info = user_info
            st.session_state.username = username
            # print('LOGIN: runner_profile:', user_info.get('runner_profile', {}))

            # After successful login, ensure user's gist file exists and is initialized if needed
            user_key = user_info["USER_KEY"]
            gist_id = user_info["GIST_ID"]
            gist_filename = f"{user_key}.json"
            github_token = st.secrets["GITHUB_TOKEN"]
            url = f"https://api.github.com/gists/{gist_id}"
            headers = {"Authorization": f"token {github_token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                gist = response.json()
                files = gist.get("files", {})
                file_obj = files.get(gist_filename)
                needs_init = False
                if not file_obj or not file_obj.get("content"):
                    needs_init = True
                else:
                    try:
                        content = json.loads(file_obj["content"])
                        if user_key not in content:
                            needs_init = True
                        else:
                            # --- Load latest runner profile from Gist into session state ---
                            runner_profile = content[user_key].get("runner_profile", {})
                            st.session_state.user_info["runner_profile"] = runner_profile
                            # print('LOGIN: loaded runner_profile from Gist:', runner_profile)
                    except Exception:
                        needs_init = True
                if needs_init:
                    default_content = {
                        user_key: {
                            "races": [],
                            "training_plans": {},
                            "progress_feedback": {},
                            "runner_profile": {}
                        }
                    }
                    payload = {"files": {gist_filename: {"content": json.dumps(default_content, indent=2)}}}
                    requests.patch(url, headers=headers, json=payload)

            st.rerun()
        else:
            st.error("Invalid username or password.")

else:
    # --- User Authenticated ---
    user_info = st.session_state.user_info
    user_key = user_info["USER_KEY"]
    sheet_url = user_info["gsheet_url"]
    gist_id = user_info["GIST_ID"]
    gist_filename = f"{user_key}.json"
    github_token = st.secrets["GITHUB_TOKEN"]

    st.sidebar.write(f"✅ Logged in as: **{user_info['name']}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_authenticated = False
        st.session_state['reload_data'] = True
        st.rerun()

    @st.cache_data(ttl=600, show_spinner=False)
    def load_data(sheet_url):
        # TEMPORARY WORKAROUND: Disable SSL verification if needed
        # WARNING: This is insecure and should only be used if you trust the data source/network
        response = requests.get(sheet_url, verify=False)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

    # Load data and define reference date
    # Always reload data on login
    if st.session_state.get('reload_data'):
        df = load_data.__wrapped__(sheet_url)
    else:
        df = load_data(sheet_url)
    st.session_state['reload_data'] = False
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    # Sidebar navigation
    st.sidebar.title("📁 Dashboard View")
    view = st.sidebar.radio("Navigate to:", ["📊 Summary", "📂 Activities", "🏁 Race Planning", "🧠 AI Analysis", "🧍 Runner Profile"])

    def save_user_profile_func(new_profile):
        data = load_gist_data(gist_id, gist_filename, github_token)
        if user_key not in data:
            data[user_key] = {"races": [], "training_plans": {}, "progress_feedback": {}}
        user_data = data[user_key]
        user_data["runner_profile"] = new_profile
        data[user_key] = user_data
        save_gist_data(gist_id, gist_filename, github_token, data)
        st.session_state.user_info["runner_profile"] = new_profile

    # Render views based on selected section
    if view == "📊 Summary":
        render_summary(df, today)

    elif view == "📂 Activities":
        render_activities(df)

    elif view == "🏁 Race Planning":
        render_race_planning(df, today, user_info, gist_id, gist_filename, github_token)

    elif view == "🧠 AI Analysis":
        render_ai_analysis(df, today)

    elif view == "🧍 Runner Profile":
        render_runner_profile(user_info, save_user_profile_func)
