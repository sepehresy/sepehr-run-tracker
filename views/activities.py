import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from openai import OpenAI
import json
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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

    # Sort and reset index for consistent row selection
    sorted_df = df.sort_values("Date", ascending=False).reset_index(drop=True)

    st.markdown("### 🧾 Click a row below to select")

    # Only show relevant columns in the AgGrid table
    display_columns = [
        "Date", "Name", "Type", "Distance (km)", "Pace (min/km)", "Moving Time",
        "Cadence", "Avg HR", "Elevation Gain"
    ]
    display_df = sorted_df[display_columns]

    # Setup AgGrid options for single-row selection
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_selection("single", use_checkbox=False)
    grid_options = gb.build()

    # Render AgGrid table
    grid_response = AgGrid(
        display_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme="balham-dark",
        height=350
    )

    selected_rows = grid_response["selected_rows"]

    # Map selected row back to full data using Date + Name as unique key
    selected_row_full = None
    # Robustly check for selection regardless of AgGrid return type
    if isinstance(selected_rows, pd.DataFrame):
        has_selection = not selected_rows.empty
    elif isinstance(selected_rows, list):
        has_selection = len(selected_rows) > 0
    else:
        has_selection = False

    if has_selection:
        if isinstance(selected_rows, pd.DataFrame):
            sel = selected_rows.iloc[0].to_dict()
        else:
            sel = selected_rows[0]
        # Defensive: handle both dict and DataFrame row
        sel_date = sel["Date"] if isinstance(sel, dict) else sel.Date
        sel_name = sel["Name"] if isinstance(sel, dict) else sel.Name
        # Find the full row in sorted_df
        match = (
            (sorted_df["Date"] == sel_date) & (sorted_df["Name"] == sel_name)
        )
        if match.any():
            selected_row_full = sorted_df[match].iloc[0]

    if selected_row_full is not None:
        selected_row = selected_row_full
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
            ("Avg HR ❤️", selected_row.get("Avg HR", "-")),
            ("Max HR ❤️", selected_row.get("Max HR", "-")),
            ("Elevation Gain 🏔️", selected_row.get("Elevation Gain", "-")),
            ("Calories", selected_row.get("Calories", "-")),
        ]
        cols = st.columns(len(metrics))
        for i, (label, value) in enumerate(metrics):
            cols[i].metric(label, value)

        lap_df = pd.DataFrame()
        if "Lap Details" in selected_row and pd.notna(selected_row["Lap Details"]):
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
                day_str = selected_row['Date'].strftime('%A')
                date_str = selected_row['Date'].strftime('%Y-%m-%d')
                name_str = selected_row['Name']
                st.subheader(f"{day_str}  -- {date_str} -- {name_str}")
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

            except Exception as e:
                st.warning(f"Could not parse lap details: {e}")

        st.markdown("---")

        # --- AI Analysis Section (always available) ---
        st.subheader("🧠 AI Analysis of This Run")

        # Create a unique key for this activity
        activity_key = f"analysis_{selected_row['Date']}_{selected_row['Name']}"

        # Load saved analyses
        saved_analyses = load_saved_analyses()

        # Feature-based access control for AI analysis
        user_info = st.session_state.get('user_info', {})
        features = user_info.get('Features', []) or user_info.get('features', [])
        if isinstance(features, str):
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
                    lap_csv = lap_df.to_csv(index=False) if 'lap_df' in locals() and not lap_df.empty else ''
                    # Get runner profile from session state if available
                    runner_profile = st.session_state.get('user_info', {}).get('runner_profile', {})
                    runner_profile_str = json.dumps(runner_profile, indent=2) if runner_profile else "Not available"
                    day_str = selected_row['Date'].strftime('%A')
                    date_str = selected_row['Date'].strftime('%Y-%m-%d')
                    name_str = selected_row['Name']
                    prompt = (
                        "Analyze this running activity based on the following data. looks at per lap data as well if available\n"
                        "Comment on what is the impact of the activity. what is ecexuted good and what needs to be improved \n"
                        "Comment on general feedback of this activity \n"
                        "Provide specific, actionable feedback for improvement.\n"
                        f"\nLap Data:\n{lap_csv}\n"
                        f"\nRun Summary: {selected_row['Distance (km)']}km, "
                        f"Avg Pace: {format_pace(selected_row['Pace (min/km)'])}, "
                        f"Avg HR: {selected_row['Avg HR']}, "
                        f"Max HR: {selected_row.get('Max HR', '-')}, "
                        f"Cadence: {selected_row.get('Cadence', '-')}, "
                        f"Power: {selected_row.get('Power (W)', '-')}, "
                        f"Calories: {selected_row.get('Calories', '-')}, "
                        f"Elevation Gain: {selected_row['Elevation Gain']}m, "
                        f"Day: {day_str}, Date: {date_str}, Name: {name_str}"
                        f"\n\nRunner Profile:\n{runner_profile_str}"
                    )
                    print (f"AI Prompt \n: {prompt}")
                    with st.spinner("Analyzing your run data..."):
                        try:
                            response = client.chat.completions.create(
                                model="gpt-4-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a professional running coach with expertise in analyzing running data. Provide specific insights and actionable advice."},
                                    {"role": "user", "content": prompt}
                                ]
                            )
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
            st.session_state[activity_key] = saved_analyses[activity_key]
            st.write(saved_analyses[activity_key])
        else:
            st.info("Click 'Generate Analysis' for AI insights on this run")
    else:
        st.info("Select an activity from the table above to view splits and analysis.")
