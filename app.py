import streamlit as st
# Set Streamlit app config - MUST be the first Streamlit command
st.set_page_config(page_title="Sepehr's Running Dashboard", layout="wide")

import pandas as pd
from datetime import datetime
from views.activities import render_activities
from views.race_planning import render_race_planning
from views.runner_profile import render_runner_profile
from views.fatigue_analysis import render_fatigue_analysis
from views.pace_calculator import render_pace_calculator
from views.statistics_modular import render_statistics
import requests
import json
from utils.gist_helpers import load_gist_data, save_gist_data
import io
import certifi
import urllib3
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE
import base64
import os
from utils.date_parser import safe_parse_date_series


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# Initialize first_load flag to handle initial rendering
if 'first_load' not in st.session_state:
    st.session_state['first_load'] = True

if not st.session_state.user_authenticated:
    # Complete fresh design - no stretching, compact, centered
    st.markdown("""
    <style>
    /* Complete reset */
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: none !important;
        width: 100% !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a2a2a 100%);
        min-height: 100vh;
    }
    
    /* Hide Streamlit elements and remove spacing */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header {visibility: hidden;}
    
    /* AGGRESSIVE: Override ALL Streamlit default widths */
    .stTextInput {
        width: 180px !important;
        max-width: 180px !important;
    }
    
    .stTextInput > div {
        width: 180px !important;
        max-width: 180px !important;
    }
    
    .stTextInput > div > div {
        width: 180px !important;
        max-width: 180px !important;
    }
    
    .stButton {
        width: 180px !important;
        max-width: 180px !important;
    }
    
    .stButton > button {
        width: 180px !important;
        max-width: 180px !important;
    }
    
    /* Remove ALL default Streamlit spacing */
    .block-container > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Remove spacing from elements */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Hide ANY empty elements */
    div:empty {
        display: none !important;
    }
    
    /* Centered container for everything */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding: 40px 20px 20px 20px;
        box-sizing: border-box;
    }
    
    /* Title styling */
    .app-title {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 8px;
        text-align: center;
    }
    
    .app-subtitle {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Video container */
    .video-container {
        width: 600px;
        height: 360px;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 20px;
        background: #1a1a1a;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }
    
    .video-container video {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 12px;
    }
    
    /* Form wrapper to center everything */
    .form-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        margin: 0 auto;
        padding: 0;
    }
    
    /* Form container */
    .form-container {
        width: 180px !important;
        max-width: 180px !important;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 16px;
        backdrop-filter: blur(20px);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* Force form elements to be narrow */
    .form-container * {
        width: 148px !important;
        max-width: 148px !important;
    }
    
    /* Clean form styling */
    .stTextInput > label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.75rem !important;
        margin-bottom: 2px !important;
        font-weight: 500 !important;
        width: 148px !important;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 6px !important;
        color: white !important;
        padding: 6px 8px !important;
        font-size: 0.8rem !important;
        margin-bottom: 8px !important;
        width: 148px !important;
        max-width: 148px !important;
        box-sizing: border-box !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
        font-size: 0.75rem !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        width: 148px !important;
        max-width: 148px !important;
        margin-top: 8px !important;
        box-sizing: border-box !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stAlert {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        margin-top: 8px !important;
        font-size: 0.8rem !important;
        padding: 8px !important;
        width: 148px !important;
        max-width: 148px !important;
        text-align: center !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .video-container {
            width: 450px;
            height: 270px;
        }
        .form-container {
            width: 160px !important;
        }
        .form-container * {
            width: 128px !important;
            max-width: 128px !important;
        }
    }
    
    @media (max-width: 480px) {
        .video-container {
            width: 300px;
            height: 180px;
        }
        .form-container {
            width: 140px !important;
        }
        .form-container * {
            width: 108px !important;
            max-width: 108px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # New layout structure
    st.markdown("""
    <div class="login-container">
        <div class="app-title">🏃‍♂️ RunTracker</div>
        <div class="app-subtitle">Your intelligent running companion</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Video section
    st.markdown("""
    <div style="display: flex; justify-content: center; margin-bottom: 15px;">
        <div class="video-container">
            <video autoplay muted loop playsinline>
                <source src="https://raw.githubusercontent.com/sepehresy/sepehr-run-tracker/main/assets/Running_Dashboard_Login_Video_Script.mp4" type="video/mp4">
            </video>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered form wrapper
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        st.markdown('''
        <div style="display: flex; justify-content: center; align-items: center; width: 100%;">
            <div class="form-container">
        ''', unsafe_allow_html=True)
        
        # Form inputs
        users = load_users()
        
        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        
        if st.button("Sign In to Dashboard", key="login_button"):
            if username and password:
                user_info = authenticate(username, password, users)
                if user_info:
                    with st.spinner("🚀 Launching your dashboard..."):
                        st.session_state['session_id'] = user_info["USER_KEY"]
                        st.session_state.user_authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.username = username
                        st.session_state['reload_data'] = True

                        # Initialize user data
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
                                        runner_profile = content[user_key].get("runner_profile", {})
                                        st.session_state.user_info["runner_profile"] = runner_profile
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

                    st.success("🎉 Welcome to your dashboard!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please check your username and password.")
            else:
                st.warning("⚠️ Please enter both username and password.")
        
        st.markdown('''
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.stop()

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
        # Clear all session state for clean logout
        for key in list(st.session_state.keys()):
            if key not in ['first_load']:  # Keep first_load for next login
                del st.session_state[key]
        
        # Reset authentication and flags
        st.session_state.user_authenticated = False
        st.session_state['reload_data'] = True
        st.session_state['first_load'] = True  # Reset for clean next login
        st.rerun()

    @st.cache_data(ttl=600, show_spinner=False)
    def load_data(sheet_url):
        # TEMPORARY WORKAROUND: Disable SSL verification if needed
        # WARNING: This is insecure and should only be used if you trust the data source/network
        response = requests.get(sheet_url, verify=False)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        df['Date'] = safe_parse_date_series(df['Date'], 'timestamp')
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
    # st.sidebar.title("📁 Dashboard View")
    view = st.sidebar.radio("Navigate to:", ["📈 Statistics", "📂 Activities", "🏁 Race Planning", "⏱️ Pace Calculator", "🧍 Runner Profile", "📊 Fatigue Analysis"])

    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)


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
    if view == "📈 Statistics":
        render_statistics(df, today)

    elif view == "📂 Activities":
        render_activities(df, user_info, gist_id, gist_filename, github_token)

    elif view == "🏁 Race Planning":
        render_race_planning(df, today, user_info, gist_id, gist_filename, github_token)    
        
    elif view == "⏱️ Pace Calculator":
        render_pace_calculator()
        
    elif view == "🧍 Runner Profile":
        render_runner_profile(user_info, save_user_profile_func)

    elif view == "📊 Fatigue Analysis":
        render_fatigue_analysis(df, today, user_info, gist_id, gist_filename, github_token)
