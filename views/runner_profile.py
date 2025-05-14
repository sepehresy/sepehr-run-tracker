import streamlit as st
import pandas as pd
from datetime import date
from utils.gist_helpers import load_gist_data

def render_runner_profile(user_info, save_user_profile_func):
    # Use the runner profile from session state (which is kept up to date after login and on save)
    profile = st.session_state.get('user_info', {}).get('runner_profile', {})

    st.title("🏃 Runner Profile")
    st.markdown("Use this profile to help AI understand your background for a tailored training plan.")

    with st.form("runner_profile_form"):

        # === Experience Section ===
        with st.expander("📘 Experience"):
            # st.subheader("📘 Experience")
            col1, col2, col3, col4 = st.columns(4)
            experience = col1.selectbox("Experience Level", ["Beginner", "Intermediate", "Experienced"], index=["Beginner", "Intermediate", "Experienced"].index(profile.get("experience", "Beginner")))
            years_running = col2.number_input("Years of Running", 0, 50, step=1, value=int(profile.get("years_running", 0)))
            half_count = col3.number_input("Half Marathons Completed", 0, 50, step=1, value=int(profile.get("half_marathons", 0)))
            full_count = col4.number_input("Marathons Completed", 0, 50, step=1, value=int(profile.get("marathons", 0)))

        # === Heart Rate Section ===
        with st.expander("❤️ Heart Rate Zones"):
            # st.subheader("❤️ Heart Rate Zones")
            col1, col2 = st.columns(2)
            resting_hr_val = int(profile.get("resting_hr", 60))
            if resting_hr_val < 30:
                resting_hr_val = 30
            resting_hr = col1.number_input("Resting HR (bpm)", 30, 100, step=1, value=resting_hr_val)
            max_hr_val = int(profile.get("max_hr", 180))
            if max_hr_val < 100:
                max_hr_val = 100
            max_hr = col2.number_input("Max HR (bpm)", 100, 220, step=1, value=max_hr_val)

            hr_zones = st.columns(5)
            z1 = hr_zones[0].text_input("Z1 (Recovery)", value=profile.get("z1", ""), placeholder="e.g. 100–120")
            z2 = hr_zones[1].text_input("Z2 (Easy)", value=profile.get("z2", ""), placeholder="e.g. 121–135")
            z3 = hr_zones[2].text_input("Z3 (Moderate)", value=profile.get("z3", ""), placeholder="e.g. 136–150")
            z4 = hr_zones[3].text_input("Z4 (Threshold)", value=profile.get("z4", ""), placeholder="e.g. 151–165")
            z5 = hr_zones[4].text_input("Z5 (VO2 Max)", value=profile.get("z5", ""), placeholder="e.g. 166–180")

        # === PR Section ===
        with st.expander("🏅 Personal Records"):
            # st.subheader("🏅 Personal Records")
            pr_cols = st.columns(4)
            pr_5k = pr_cols[0].text_input("5K Time", value=profile.get("pr_5k", ""), placeholder="e.g. 22:30")
            pr_10k = pr_cols[1].text_input("10K Time", value=profile.get("pr_10k", ""), placeholder="e.g. 48:00")
            pr_half = pr_cols[2].text_input("Half Marathon", value=profile.get("pr_half", ""), placeholder="e.g. 1:50:00")
            pr_full = pr_cols[3].text_input("Marathon", value=profile.get("pr_marathon", ""), placeholder="e.g. 4:00:00")

        # === Training Overview ===
        with st.expander("📈 Recent Training Volume"):
            # st.subheader("📈 Recent Training load")
            col1, col2 = st.columns(2)
            avg_km_val = int(profile.get("avg_weekly_km", 0))
            if avg_km_val < 0:
                avg_km_val = 0
            avg_km = col1.number_input("Avg Weekly KM (Last 4 Weeks)", 0, 300, step=10, value=avg_km_val)

        # === Training Preferences ===
        with st.expander("📆 Training Preferences"):
            # st.subheader("📆 Training Preferences")
            run_days = st.multiselect(
                "Preferred Training Days",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=profile.get("preferred_training_days", [
                    "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"
                ])
            )
            rest_days = st.multiselect(
                "Preferred Rest Days",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=profile.get("preferred_rest_days", ["Monday", "Friday"])
            )
            num_run_days = st.selectbox(
                "How many days per week do you want to run?",
                list(range(1, 8)),
                index=(int(profile.get("run_freq", 3)) - 1) if profile.get("run_freq") else 2
            )

        # === Injuries & Limitations ===
        with st.expander("🚑 Injuries, Health & Limitations"):
            injury = st.text_input("Current or past Injuries (if any)", value=profile.get("injuries", ""), placeholder="e.g. shin splints , IT band syndrome")

        # === Submit Button ===
        submitted = st.form_submit_button("💾 Save Profile")
        if submitted:
            new_profile = {
                "experience": experience,
                "years_running": years_running,
                "half_marathons": half_count,
                "marathons": full_count,
                "resting_hr": resting_hr,
                "max_hr": max_hr,
                "z1": z1,
                "z2": z2,
                "z3": z3,
                "z4": z4,
                "z5": z5,
                "pr_5k": pr_5k,
                "pr_10k": pr_10k,
                "pr_half": pr_half,
                "pr_marathon": pr_full,
                "avg_weekly_km": avg_km,
                "preferred_training_days": run_days,
                "preferred_rest_days": rest_days,
                "run_freq": num_run_days,
                "injuries": injury
            }
            save_user_profile_func(new_profile)
            st.success("Runner profile saved successfully! ✅")
