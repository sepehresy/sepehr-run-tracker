import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from openai import OpenAI
import json
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import requests
from utils.elevation import fetch_elevations
from streamlit_javascript import st_javascript
import folium
from streamlit_folium import st_folium
import polyline

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE

try:
    from streamlit_elements import elements, mui, html, sync, lazy, dashboard
    STREAMLIT_ELEMENTS_AVAILABLE = True
except ImportError:
    STREAMLIT_ELEMENTS_AVAILABLE = False


# Create analyses directory if it doesn't exist
os.makedirs("data/analyses", exist_ok=True)

def format_pace(p):
    try:
        p = float(p)
        minutes = int(p)
        seconds = int(round((p - minutes) * 60))
        return f"{minutes}:{seconds:02d}"
    except:
        return "-"

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

def build_activity_table(df):
    sorted_df = df.sort_values("Date", ascending=False).reset_index(drop=True)
    if 'is_mobile' not in st.session_state:
        st.session_state['is_mobile'] = False
    mobile_view = st.toggle("📱 Mobile View", value=st.session_state.get('is_mobile', False))
    display_columns = (
        ["Date", "Name", "Distance (km)", "Pace (min/km)", "Avg HR"]
        if mobile_view else
        ["Date", "Name", "Type", "Workout Type", "Description", "Distance (km)", "Pace (min/km)", "Moving Time", "Cadence", "Avg HR", "Elevation Gain"]
    )
    display_df = sorted_df[display_columns]
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_selection("single", use_checkbox=False)
    grid_options = gb.build()
    grid_response = AgGrid(
        display_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme="balham-dark",
        height=220 if mobile_view else 350
    )
    return display_df, grid_response["selected_rows"]

def get_selected_row(df, selected_rows):
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
        sel_date = sel["Date"] if isinstance(sel, dict) else sel.Date
        sel_name = sel["Name"] if isinstance(sel, dict) else sel.Name
        match = (df["Date"] == sel_date) & (df["Name"] == sel_name)
        if match.any():
            return df[match].iloc[0]
    return None

def render_summary_metrics(selected_row):
    day_str = selected_row['Date'].strftime('%A')
    date_str = selected_row['Date'].strftime('%Y-%m-%d')
    name_str = selected_row['Name']
    
    
    # Use 8 columns for a more compact layout
    cols = st.columns(8)
    
    # Custom CSS for smaller metrics
    st.markdown("""
    <style>
    .small-metric {
        font-size: 0.9rem !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .small-metric .metric-label {
        font-size: 0.8rem !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .small-metric .metric-value {
        font-size: 0.8rem !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
      # Unified box with header and metrics in a nice container
    box_style = """
    <style>
    .activity-box {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 6px;
        padding: 8px;
        margin-bottom: 10px;
        background-color: rgba(49, 51, 63, 0.05);
        box-shadow: 0 1px 2px rgba(0,0,0,0.07);
    }
    .activity-header {
        font-size: 0.85rem;
        margin-bottom: 3px;
        padding-bottom: 3px;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1);
    }
    .activity-description {
        font-size: 0.75rem;
        margin: 4px 0;
        color: rgba(250,250,250,0.8);
    }
    .metrics-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-top: 5px;
    }
    .metric-card {
        flex: 1;
        min-width: 70px;
        padding: 4px;
        border-radius: 4px;
        background-color: rgba(49, 51, 63, 0.15);
        text-align: center;
    }
    .metric-label {
        font-size: 0.65rem;
        opacity: 0.75;
    }
    .metric-value {
        font-size: 0.75rem;
        font-weight: bold;
    }
    </style>
    """
    
    summary_html = f"""
    {box_style}
    <div class="activity-box">
        <div class="activity-header">
            {day_str} — {date_str} — {name_str}
        </div>
        <div class="activity-description">
            <span style="opacity:0.8;">📝</span> {selected_row.get('Description', '-')}
        </div>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">🏃‍♂️ Distance</div>
                <div class="metric-value">{selected_row.get('Distance (km)', '-')} km</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">⚡ Pace</div>
                <div class="metric-value">{format_pace(selected_row.get("Pace (min/km)", "-"))}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">⏳ Time</div>
                <div class="metric-value">{selected_row.get('Elapsed Time (min)', '-')} min</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">🏔️ Elevation</div>
                <div class="metric-value">{selected_row.get('Elevation Gain', '-')} m</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">👟 Cadence</div>
                <div class="metric-value">{selected_row.get('Cadence', '-')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">❤️ Avg HR</div>
                <div class="metric-value">{selected_row.get('Avg HR', '-')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">💖 Max HR</div>
                <div class="metric-value">{selected_row.get('Max HR', '-')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">🔥 Calories</div>
                <div class="metric-value">{selected_row.get('Calories', '-')}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)
    


def render_map(selected_row):
    if "Route Polyline" in selected_row and pd.notna(selected_row["Route Polyline"]):
        coords = None
        try:
            coords = polyline.decode(selected_row["Route Polyline"])
        except Exception as e:
            st.warning(f"Could not decode route polyline: {e}")
        if coords:
            m = folium.Map(location=coords[0], zoom_start=13)
            folium.PolyLine(coords, color="blue", weight=3).add_to(m)
            st_folium(m, width=350, height=250)
    else:
        st.markdown("<div style='width:350px;height:250px;background:#232733;border-radius:14px;display:flex;align-items:center;justify-content:center;color:#888;'>No Map</div>", unsafe_allow_html=True)

def render_lap_chart(selected_row):
    st.markdown("#### Lap Splits")
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
            lap_df = pd.DataFrame(lap_data)
            # print (lap_df)
            if not lap_df.empty:
                # Set a fixed width for the chart and ensure enough space for 5 columns of text
                fig_width = 9  # wider than before
                fig_height = max(5, 0.4 * len(lap_df))
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                bars = ax.barh(lap_df.index, lap_df["Pace"], color="#1EBEFF")
                avg_pace = lap_df["Pace"].mean()
                ax.axvline(x=avg_pace, color="red", linestyle="--", linewidth=1, label=f"Avg Pace: {avg_pace:.2f}")

                # Fixed x positions for 5 columns, spaced for readability
                x_positions = [-8, -6, -4, -2, 0]
                headers = ["KM", "Time", "Elev", "HR", "Pace"]
                # Draw headers
                for x, header in zip(x_positions, headers):
                    ax.text(x, -1, header, fontweight='bold', ha='center', va='bottom')
                # Draw row values
                for i, row in lap_df.iterrows():
                    ax.text(x_positions[0], i, f"{row['Distance']:.2f}", va='center', ha='center', fontweight='bold')
                    ax.text(x_positions[1], i, f"{row['Time']}", va='center', ha='center')
                    ax.text(x_positions[2], i, f"{int(row['ElevGain'])}", va='center', ha='center')
                    ax.text(x_positions[3], i, f"{row['HR']}", va='center', ha='center')
                    ax.text(x_positions[4], i, format_pace(row['Pace']), va='center', ha='center')
                ax.legend(loc="lower right")
                ax.set_yticks([])
                # Show x-axis and x labels, but only for positive side
                ax.get_xaxis().set_visible(True)
                ax.set_xlabel("Pace (min/km)")
                ax.invert_yaxis()
                ax.grid(True, axis='x', linestyle='--', alpha=0.5)
                # Set xlim to always show all 5 columns, but only show positive x-ticks/labels
                min_x = 0
                max_x = max(lap_df["Pace"]) + 2
                ax.set_xlim(left=x_positions[0] - 1, right=max_x)
                # Only show x-ticks/labels for positive values
                xticks = ax.get_xticks()
                ax.set_xticks([tick for tick in xticks if tick >= 0])
                plt.tight_layout()
                st.pyplot(fig, use_container_width=False)
        except Exception as e:
            st.warning(f"Could not parse lap details: {e}")
    else:
        st.markdown("<div style='display:flex;align-items:center;justify-content:center;color:#888;'>No lap data available</div>", unsafe_allow_html=True)

def generate_prompt(row, lap_csv, runner_profile_str):
    day_str = row['Date'].strftime('%A')
    date_str = row['Date'].strftime('%Y-%m-%d')
    name_str = row['Name']
    Running_Type = row.get("Type", "-")
    elapsed_time = row.get("Elapsed Time (min)", "-")
    Distance = row.get("Distance (km)", "-")
    Pace = row.get("Pace (min/km)", "-")
    moving_time = row.get("Moving Time", "-")
    cadence = row.get("Cadence", "-")
    avg_hr = row.get("Avg HR", "-")
    max_hr = row.get("Max HR", "-")
    power = row.get("Power (W)", "-")
    calories = row.get("Calories", "-")
    elevation_gain = row.get("Elevation Gain", "-")
    desc = row.get("Description", "-")
    return (
        "Analyze this running activity based on the following data. Look at per lap data as well if available.\n"
        "Comment on what is the impact of the activity, what is executed well, and what needs to be improved.\n"
        f"Day: {day_str}, Date: {date_str}, Name: {name_str}\n"
        f"Type: {Running_Type}\n"
        f"Elapsed Time: {elapsed_time} min\n"
        f"Moving Time: {moving_time} min\n"
        f"Distance: {Distance} km\n"
        f"Pace: {Pace} min/km\n"
        f"Cadence: {cadence}\n"
        f"Avg HR: {avg_hr}\n"
        f"Max HR: {max_hr}\n"
        f"Power: {power}\n"
        f"Calories: {calories}\n"
        f"Elevation Gain: {elevation_gain} m\n"
        f"Description: {desc}\n"
        f"\nLap Data:\n{lap_csv}\n"
        f"\n\nThese are the Runner Profile information:\n{runner_profile_str}"
    )

def render_ai_analysis(row):
    st.subheader("🧠 AI Analysis of This Run")
    activity_key = f"analysis_{row['Date']}_{row['Name']}"
    saved_analyses = load_saved_analyses()
    user_info = st.session_state.get('user_info', {})
    features = user_info.get('Features', []) or user_info.get('features', [])
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except Exception:
            features = []
    ai_enabled = 'ai' in features
    col1, col2 = st.columns([1, 4])
    with col1:
        if ai_enabled:
            if st.button("Generate Analysis", key=f"button_{activity_key}"):
                lap_csv = row['Lap Details'] if 'Lap Details' in row and pd.notna(row['Lap Details']) else ''
                runner_profile = st.session_state.get('user_info', {}).get('runner_profile', {})
                runner_profile_str = json.dumps(runner_profile, indent=2) if runner_profile else "Not available"
                prompt = generate_prompt(row, lap_csv, runner_profile_str)
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
                            st.toast("Analysis complete!", icon="✅")
                    except Exception as e:
                        st.error(f"Error generating analysis: {e}")
        else:
            st.button("Generate Analysis (Locked)", key=f"button_{activity_key}", disabled=True, help="You do not have access to AI features.")
    with col2:
        if activity_key in saved_analyses or activity_key in st.session_state:
            if st.button("Delete Analysis", key=f"delete_{activity_key}"):
                if activity_key in st.session_state:
                    del st.session_state[activity_key]
                if activity_key in saved_analyses:
                    saved_analyses.pop(activity_key)
                    with open("data/analyses/saved_analyses.json", "w") as f:
                        json.dump(saved_analyses, f)
                    st.rerun()
    if activity_key in st.session_state:
        st.write(st.session_state[activity_key])
    elif activity_key in saved_analyses:
        st.session_state[activity_key] = saved_analyses[activity_key]
        st.write(saved_analyses[activity_key])
    else:
        st.info("Click 'Generate Analysis' for AI insights on this run")

def render_activities(df):
    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">📋</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">Activities</span>', unsafe_allow_html=True)
    display_df, selected_rows = build_activity_table(df)
    selected = get_selected_row(df, selected_rows)
    if selected is not None:
        render_summary_metrics(selected)
        render_map(selected)
        render_lap_chart(selected)
        render_ai_analysis(selected)
    else:
        st.info("Please select an activity.")
