import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from openai import OpenAI
import json
import os

# Create analyses directory if it doesn't exist
os.makedirs("data/analyses", exist_ok=True)

# Function to load saved analyses
def load_saved_analyses():
    try:
        with open("data/analyses/saved_analyses.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Function to save analyses
def save_analysis(key, content):
    try:
        analyses = load_saved_analyses()
        analyses[key] = content
        with open("data/analyses/saved_analyses.json", "w") as f:
            json.dump(analyses, f)
        return True
    except Exception as e:
        st.error(f"Error saving analysis: {e}")
        return False

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def render_activities(df):
    st.title("📋 Activities")

    st.dataframe(df.sort_values("Date", ascending=False))

    if "Lap Details" in df.columns:
        st.subheader("Splits (per run)")

        activity_options = df.sort_values("Date", ascending=False).apply(
            lambda row: f"{row['Date'].date()} - {row['Name']}", axis=1
        )
        selected_activity = st.selectbox("Select an activity to view splits:", activity_options)

        selected_row = df[df.apply(
            lambda row: f"{row['Date'].date()} - {row['Name']}" == selected_activity, axis=1
        )].iloc[0]

        def format_pace(p):
            try:
                minutes = int(p)
                seconds = int(round((p - minutes) * 60))
                return f"{minutes}:{seconds:02d}"
            except:
                return "-"

        # Show summary metrics above plot
        metrics = [
            ("Total Distance (km)", selected_row.get("Distance (km)", "-")),
            ("Pace (min/km)", format_pace(float(selected_row.get("Pace (min/km)", 0))) if selected_row.get("Pace (min/km)") != "-" else "-"),
            ("Moving Time", selected_row.get("Moving Time", "-")),
            ("Cadence", selected_row.get("Cadence", "-")),
            ("Power (W)", selected_row.get("Power (W)", "-")),
            ("Avg HR", selected_row.get("Avg HR", "-")),
            ("Max HR", selected_row.get("Max HR", "-")),
            ("Elevation Gain", selected_row.get("Elevation Gain", "-")),
            ("Calories", selected_row.get("Calories", "-")),
        ]
        cols = st.columns(len(metrics))
        for i, (label, value) in enumerate(metrics):
            cols[i].metric(label, value)

        if pd.notna(selected_row["Lap Details"]):
            try:
                laps_raw = re.findall(r"Lap (\d+):\s*([^|]+)", selected_row["Lap Details"].replace("\\n", " "))
                lap_data = []
                for lap_number, details in laps_raw:
                    parts = [x.strip() for x in details.split(",")]
                    lap_info = {"Lap": int(lap_number)}
                    for p in parts:
                        if p.endswith("km"):
                            lap_info["Distance"] = float(p.replace("km", ""))
                        elif re.match(r"\d+:\d+", p):
                            lap_info["Time"] = p
                        elif p.startswith("pace"):
                            lap_info["Pace"] = float(p.replace("pace", "").strip())
                        elif p.startswith("HR"):
                            lap_info["HR"] = int(float(p.replace("HR", "").strip()))
                        elif p.startswith("Cad"):
                            lap_info["Cad"] = int(float(p.replace("Cad", "").strip()))
                        elif p.startswith("ElevGain"):
                            lap_info["ElevGain"] = float(p.replace("ElevGain", "").strip())
                    lap_data.append(lap_info)

                lap_df = pd.DataFrame(lap_data)
                if not lap_df.empty:
                    fig, ax = plt.subplots(figsize=(10, 0.4 * len(lap_df)))
                    bars = ax.barh(lap_df.index, lap_df["Pace"], color="#1EBEFF")

                    avg_pace = lap_df["Pace"].mean()
                    ax.axvline(x=avg_pace, color="red", linestyle="--", linewidth=1, label=f"Avg Pace: {format_pace(avg_pace)}")
                    ax.legend(loc="lower right")

                    ax.text(-5.8, -1, "KM", fontweight='bold')
                    ax.text(-4.8, -1, "Time", fontweight='bold')
                    ax.text(-3.8, -1, "Elev", fontweight='bold')
                    ax.text(-2.8, -1, "HR", fontweight='bold')
                    ax.text(-1.8, -1, "Pace", fontweight='bold')

                    for i, row in lap_df.iterrows():
                        ax.text(-5.8, i, f"{row['Distance']:.2f}", va='center', ha='left', fontweight='bold')
                        ax.text(-4.8, i, f"{row['Time']}", va='center', ha='left')
                        ax.text(-3.8, i, f"{int(row['ElevGain'])}", va='center', ha='left')
                        ax.text(-2.8, i, f"{row['HR']}", va='center', ha='left')
                        ax.text(-1.8, i, format_pace(row['Pace']), va='center', ha='left')

                    ax.set_yticks([])
                    ax.set_xlabel("Pace (min/km)")
                    ax.invert_yaxis()
                    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
                    ax.set_xlim(0, max(lap_df["Pace"]) + 2)
                    st.pyplot(fig)

                    st.subheader("🧠 AI Analysis of This Run")
                    
                    # Create a unique key for this activity
                    activity_key = f"analysis_{selected_activity}"
                    
                    # Load saved analyses
                    saved_analyses = load_saved_analyses()
                    
                    # Feature-based access control for AI analysis
                    user_info = st.session_state.get('user_info', {})
                    features = user_info.get('Features', []) or user_info.get('features', [])
                    if isinstance(features, str):
                        import json
                        try:
                            features = json.loads(features)
                        except Exception:
                            features = []
                    ai_enabled = 'ai' in features
                    
                    # Create columns for analysis actions
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        # Add button to trigger AI analysis
                        if ai_enabled:
                            if st.button("Generate Analysis", key=f"button_{activity_key}"):
                                prompt = (
                                    "Analyze this running activity based on the following per-lap data.\n"
                                    "Comment on pacing strategy, consistency, heart rate trends, and elevation impact.\n"
                                    "Provide specific, actionable feedback for improvement.\n"
                                    f"\nLap Data:\n{lap_df.to_csv(index=False)}\n"
                                    f"\nRun Summary: {selected_row['Distance (km)']}km, "
                                    f"Avg Pace: {format_pace(selected_row['Pace (min/km)'])}, "
                                    f"Avg HR: {selected_row['Avg HR']}, "
                                    f"Elevation Gain: {selected_row['Elevation Gain']}m"
                                )
                                with st.spinner("Analyzing your run data..."):
                                    try:
                                        response = client.chat.completions.create(
                                            # model="gpt-4",
                                            model="gpt-3.5-turbo",
                                            messages=[
                                                {"role": "system", "content": "You are a professional running coach with expertise in analyzing running data. Provide specific insights and actionable advice."},
                                                {"role": "user", "content": prompt}
                                            ]
                                        )
                                        # Store in session state AND save to file
                                        analysis_content = response.choices[0].message.content
                                        st.session_state[activity_key] = analysis_content
                                        save_success = save_analysis(activity_key, analysis_content)
                                        if save_success:
                                            st.success("Analysis complete!")
                                    except Exception as e:
                                        st.error(f"Error generating analysis: {e}")
                        else:
                            st.button("Generate Analysis (Locked)", key=f"button_{activity_key}", disabled=True, help="You do not have access to AI features.")
                    
                    with col2:
                        # Button to delete analysis if it exists
                        if activity_key in saved_analyses or activity_key in st.session_state:
                            if st.button("Delete Analysis", key=f"delete_{activity_key}"):
                                if activity_key in st.session_state:
                                    del st.session_state[activity_key]
                                if activity_key in saved_analyses:
                                    saved_analyses.pop(activity_key)
                                    with open("data/analyses/saved_analyses.json", "w") as f:
                                        json.dump(saved_analyses, f)
                                    st.experimental_rerun()
                    
                    # Display analysis if it exists in session state OR in saved analyses
                    if activity_key in st.session_state:
                        st.write(st.session_state[activity_key])
                    elif activity_key in saved_analyses:
                        st.session_state[activity_key] = saved_analyses[activity_key]  # Load into session state
                        st.write(saved_analyses[activity_key])
                    else:
                        st.info("Click 'Generate Analysis' for AI insights on this run")

            except Exception as e:
                st.warning(f"Could not parse lap details: {e}")

        st.markdown("---")
