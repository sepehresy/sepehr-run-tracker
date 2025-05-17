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
    
    # Add a section header for activity summary
    st.markdown('<div class="section-header"><span class="section-icon">📊</span> <span class="section-title">Activity Summary</span></div>', unsafe_allow_html=True)
    
    # Create a direct container with zero margins
    st.markdown('<div class="metrics-container" style="margin:0; padding:0;">', unsafe_allow_html=True)
    
    # Comprehensive CSS for consistent layout
    st.markdown("""
    <style>
    /* Reset spacing for metrics */
    .metrics-container > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Small metric styling */
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
      
    # Unified box with header and metrics in a nice container with explicit bottom margin
    box_style = """
    <style>
    .activity-box {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 6px;
        padding: 8px;
        margin-bottom: 0;
        background-color: rgba(49, 51, 63, 0.05);
        box-shadow: 0 1px 2px rgba(0,0,0,0.07);
    }    .activity-header {
        font-size: 0.85rem;
        margin-bottom: 3px;
        padding-bottom: 3px;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1);
    }    .activity-description {
        font-size: 0.75rem;
        margin: 4px 0;
        padding: 2px 0;
        color: rgba(250,250,250,0.8);
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: normal;
        line-height: 1.5;
        width: 100%;
        max-width: 100%;
    }
    .activity-description br {
        display: block;
        content: "";
        margin-top: 0.3em;
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
    """    # Clean the description text to ensure it displays correctly
    description = selected_row.get('Description', '-')
    # Make sure it's a string
    if not isinstance(description, str):
        description = str(description)
    # HTML escape any tags
    description = description.replace('<', '&lt;').replace('>', '&gt;')
    # Replace newlines with HTML line breaks to preserve formatting
    description = description.replace('\n', '<br>')

    summary_html = f"""
    {box_style}
    <div class="activity-box">
        <div class="activity-header">
            {day_str} — {date_str} — {name_str}
        </div>        <div class="activity-description">
            <span style="opacity:0.8;vertical-align:top;">📝</span> <span style="display:inline-block;width:calc(100% - 20px);vertical-align:top;">{description}</span>
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
    # Close the metrics container
    st.markdown('</div>', unsafe_allow_html=True)
    
def render_map(selected_row=None):
    # Add some spacing before the map to prevent overlap with metrics
    st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)
    
    # Add a section header for the map
    st.markdown('<div class="section-header"><span class="section-icon">🗺️</span> <span class="section-title">Route Map</span></div>', unsafe_allow_html=True)
    
    # Map container with explicit styling
    st.markdown('<div class="map-container" style="margin:0; padding:0; overflow:hidden;">', unsafe_allow_html=True)
    
    if selected_row is not None and "Route Polyline" in selected_row and pd.notna(selected_row["Route Polyline"]):
        coords = None
        try:
            coords = polyline.decode(selected_row["Route Polyline"])
        except Exception as e:
            st.warning(f"Could not decode route polyline: {e}")
        if coords:
            # Create a more visually appealing map
            m = folium.Map(location=coords[0], zoom_start=13)
            
            # Add start and end markers
            folium.Marker(
                coords[0],
                icon=folium.Icon(color="green", icon="play", prefix="fa"),
                popup="Start"
            ).add_to(m)
            
            folium.Marker(
                coords[-1],
                icon=folium.Icon(color="red", icon="stop", prefix="fa"),
                popup="Finish"
            ).add_to(m)
            
            # Add a more prominent route line
            folium.PolyLine(
                coords, 
                color="#1EBEFF", 
                weight=4,
                opacity=0.8,
                tooltip=f"Distance: {selected_row.get('Distance (km)', '-')} km"
            ).add_to(m)
            
            # Add distance scale
            folium.plugins.MeasureControl(position='bottomleft').add_to(m)
            
            # Use custom args to eliminate any margins
            st_folium(m, width=350, height=250, returned_objects=[])
    else:
        # Generic placeholder map with better styling
        default_location = [37.7749, -122.4194]  # Default location (San Francisco)
        m = folium.Map(location=default_location, zoom_start=10)
        folium.TileLayer('cartodbdark_matter').add_to(m)
        folium.plugins.MeasureControl(position='bottomleft').add_to(m)
        st_folium(m, width=350, height=250, returned_objects=[])
    
    # Add a subtle connector element that will help ensure the gap is filled
    st.markdown('<div style="height:1px;margin:-1px 0;padding:0;"></div>', unsafe_allow_html=True)
    
    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)

def render_lap_chart(selected_row=None):
    # Create a seamless connection with the map above by using negative margin
    st.markdown('<div class="lap-chart-container" style="margin-top:-20px; padding:0;">', unsafe_allow_html=True)
    
    # Add a section header for lap splits
    st.markdown('<div class="section-header"><span class="section-icon">⏱️</span> <span class="section-title">Lap Splits</span></div>', unsafe_allow_html=True)
    
    if selected_row is not None and "Lap Details" in selected_row and pd.notna(selected_row["Lap Details"]):
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
            
            if not lap_df.empty:                # Add a small summary of lap data
                total_laps = len(lap_df)
                avg_pace = lap_df["Pace"].mean()
                fastest_lap = lap_df["Pace"].min()
                fastest_lap_num = lap_df.loc[lap_df["Pace"].idxmin(), "Lap"]
                  
                # Get average HR from either activity summary or lap data
                avg_hr_display = ""
                avg_hr = None
                
                # Try to get avg_hr from activity summary first
                if 'Avg HR' in selected_row and pd.notna(selected_row['Avg HR']):
                    try:
                        avg_hr = float(selected_row['Avg HR'])
                        avg_hr_display = f"""<div class="lap-summary-item"><span class="summary-label">Avg HR:</span> <span class="summary-value">{int(avg_hr)}</span></div>"""
                    except (ValueError, TypeError):
                        avg_hr = None
                        
                # If not available in summary, calculate from lap data (fallback)
                if avg_hr is None and "HR" in lap_df.columns and not lap_df["HR"].isna().all():
                    avg_hr = lap_df["HR"].mean()
                    avg_hr_display = f"""<div class="lap-summary-item"><span class="summary-label">Avg HR:</span> <span class="summary-value">{int(avg_hr)}</span></div>"""
                
                st.markdown(f"""
                <div class="lap-summary">
                    <div class="lap-summary-item"><span class="summary-label">Total Laps:</span> <span class="summary-value">{total_laps}</span></div>
                    <div class="lap-summary-item"><span class="summary-label">Avg Pace:</span> <span class="summary-value">{format_pace(avg_pace)}</span></div>
                    <div class="lap-summary-item"><span class="summary-label">Fastest Lap:</span> <span class="summary-value">Lap {fastest_lap_num} ({format_pace(fastest_lap)})</span></div>
                    {avg_hr_display}
                </div>
                """, unsafe_allow_html=True)
                
                # Wrap the chart in a container div for better spacing control
                st.markdown('<div class="chart-wrapper" style="margin:0; padding:0;">', unsafe_allow_html=True)
                  # Set global font size for the plot to be consistent with UI
                plt.rcParams.update({'font.size': 8})  # Smaller base font size that applies to all elements                # Set a fixed width for the chart and adjust height based on lap count
                fig_width = 9  # wider than before                  # Dynamic height calculation based on number of laps
                if len(lap_df) <= 1:
                    fig_height = 1  # Fixed minimum height for 1 lap
                elif len(lap_df) <= 3:
                    fig_height = 2  # Good size for 2-3 laps
                else:
                    fig_height = max(3, 0.35 * len(lap_df))  # Scale for many laps but not too tall
                
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                  # Get average HR from activity summary (or calculate from lap data if not available)
                avg_hr = None
                hr_colors = []
                
                # First try to get avg_hr from selected_row (activity summary)
                if 'Avg HR' in selected_row and pd.notna(selected_row['Avg HR']):
                    try:
                        avg_hr = float(selected_row['Avg HR'])
                    except (ValueError, TypeError):
                        avg_hr = None
                        
                # If not available in summary, calculate from lap data (fallback)
                if avg_hr is None and "HR" in lap_df.columns and not lap_df["HR"].isna().all():
                    avg_hr = lap_df["HR"].mean()
                
                # Color-code HR values if HR data is available
                if "HR" in lap_df.columns and not lap_df["HR"].isna().all() and avg_hr is not None:
                    for hr in lap_df["HR"]:
                        if pd.isna(hr):
                            hr_colors.append("#AAAAAA")  # Gray for missing data
                        elif hr < avg_hr * 0.95:  # Significantly lower than average
                            hr_colors.append("#4CAF50")  # Green (easier effort)
                        elif hr > avg_hr * 1.05:  # Significantly higher than average
                            hr_colors.append("#F44336")  # Red (harder effort)
                        else:  # Close to average
                            hr_colors.append("#1EBEFF")  # Blue (average effort)
                else:
                    # If no HR data, use a neutral color for all
                    hr_colors = ["#AAAAAA"] * len(lap_df)
                
                # Color-code bars based on pace relative to average
                bar_colors = []
                for pace in lap_df["Pace"]:
                    if pace < avg_pace * 0.95:  # Significantly faster than average
                        bar_colors.append("#4CAF50")  # Green
                    elif pace > avg_pace * 1.05:  # Significantly slower than average
                        bar_colors.append("#F44336")  # Red
                    else:  # Close to average
                        bar_colors.append("#1EBEFF")  # Blue
                  # Adjust bar height based on number of laps
                bar_height = 0.6 if len(lap_df) <= 3 else 0.8
                
                bars = ax.barh(lap_df.index, lap_df["Pace"], color=bar_colors, height=bar_height)
                avg_pace = lap_df["Pace"].mean()
                ax.axvline(x=avg_pace, color="red", linestyle="--", linewidth=1, label=f"Avg Pace: {format_pace(avg_pace)}")
                  # Fixed x positions for 5 columns, spaced for readability
                x_positions = [-8, -6, -4, -2, 0]
                headers = ["KM", "Time", "Elev", "HR", "Pace"]
                
                # Adjust header position based on number of laps
                header_y_position = -0.5 if len(lap_df) <= 3 else -1
                
                # Draw headers with smaller font size
                for x, header in zip(x_positions, headers):
                    # Add a small indicator for color-coded fields
                    if header == "HR" and "HR" in lap_df.columns and not lap_df["HR"].isna().all():
                        ax.text(x, header_y_position, f"{header}*", fontweight='bold', ha='center', va='bottom', fontsize=5)
                    else:
                        ax.text(x, header_y_position, header, fontweight='bold', ha='center', va='bottom', fontsize=5)
                # Draw row values with smaller consistent font size
                for i, row in lap_df.iterrows():                
                    ax.text(x_positions[0], i, f"{row['Distance']:.2f}", va='center', ha='center', fontweight='bold', fontsize=7)
                    ax.text(x_positions[1], i, f"{row['Time']}", va='center', ha='center', fontsize=7)
                    ax.text(x_positions[2], i, f"{int(row['ElevGain'])}", va='center', ha='center', fontsize=7)
                    
                    # Color-code HR value based on zones
                    if 'HR' in row:
                        # Get the appropriate color for this HR value
                        hr_color = hr_colors[i]
                        ax.text(x_positions[3], i, f"{row['HR']}", va='center', ha='center', fontsize=7, color=hr_color)
                    else:
                        ax.text(x_positions[3], i, "-", va='center', ha='center', fontsize=7)
                        
                    ax.text(x_positions[4], i, format_pace(row['Pace']), va='center', ha='center', fontsize=7)
                ax.legend(loc="lower right", fontsize=10)                
                ax.set_yticks([])
                # Show x-axis and x labels, but only for positive side
                ax.get_xaxis().set_visible(True)
                ax.set_xlabel("Pace (min/km)", fontsize=7)  # Consistent font size for axis label
                ax.invert_yaxis()
                ax.grid(True, axis='x', linestyle='--', alpha=0.5)
                # Set xlim to always show all 5 columns, but only show positive x-ticks/labels
                min_x = 0
                max_x = max(lap_df["Pace"]) + 2
                ax.set_xlim(left=x_positions[0] - 1, right=max_x)                # Only show x-ticks/labels for positive values
                xticks = ax.get_xticks()
                ax.set_xticks([tick for tick in xticks if tick >= 0])
                ax.tick_params(axis='x', labelsize=7)  # Ensure tick labels have consistent font size
                plt.tight_layout(pad=0.5)  # Tighter layout with minimal padding
                  # Use the pyplot container with custom config
                st.pyplot(fig, use_container_width=False)
                
                # Add a legend for the color coding if HR data is available
                if "HR" in lap_df.columns and not lap_df["HR"].isna().all():
                    st.markdown("""
                    <div style="font-size:0.65rem; color:#999; margin-top:0px; padding-left:5px;">
                    * Color coding: <span style="color:#4CAF50">Green</span> = lower than avg, 
                    <span style="color:#1EBEFF">Blue</span> = near avg, 
                    <span style="color:#F44336">Red</span> = higher than avg
                    </div>
                    """, unsafe_allow_html=True)
                
                # Close the chart wrapper
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Could not parse lap details: {e}")
    else:        # Create a placeholder chart with consistent dimensions to prevent layout shifts
        st.markdown('<div class="chart-placeholder" style="width:350px;height:150px;background:#1E1E1E;border-radius:10px;margin:0;padding:0;display:flex;align-items:center;justify-content:center;">', unsafe_allow_html=True)
        st.markdown('<span style="color:#888;">No lap data available</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Close the lap chart container
    st.markdown('</div>', unsafe_allow_html=True)

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
    # Use consistent styling with other sections
    st.markdown('<div class="section-header"><span class="section-icon">🧠</span> <span class="section-title">AI Analysis of This Run</span></div>', unsafe_allow_html=True)
    
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
    
    # Use different column arrangement for better layout
    col1, col2 = st.columns([1, 4])
    with col1:
        if ai_enabled:
            if st.button("📝 Generate Analysis", key=f"button_{activity_key}"):
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
    # Add comprehensive CSS right at the start to fix all spacing issues and improve UI
    st.markdown("""
    <style>
    /* Fix for all Streamlit spacing issues */
    .stMapGlWrapper, .element-container, div[data-testid="stVerticalBlock"] > div {
        margin: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
    }
    
    /* Remove the default margin between blocks */
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
      /* Custom class for our unified layout container */
    .unified-activity-layout {
        display: flex;
        flex-direction: column;
        gap: 0px;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Force streamlit elements to have zero spacing */
    .unified-activity-layout > div {
        margin: 0 !important;
        padding: 0 !important;
    }
      /* Target folium map specifically */
    .stFolium {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Additional fixes for pyplot charts */
    .stPlotlyChart {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Target specific spacing between metrics and map */
    .metrics-container + div {
        margin-top: 5px !important;
        padding-top: 0 !important;
    }
    
    /* Eliminate gap between activity box and map */
    .activity-box {
        margin-bottom: 0 !important;
    }
    
    /* Fix for initial load gap between map and lap chart */
    .map-container + div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Better folium control - ensure map renders correctly */
    .stFolium iframe {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ensure info message has no bottom margin */
    .element-container .stAlert {
        margin-bottom: 0 !important;
    }
    
    /* Improved section headers */
    .section-header {
        display: flex;
        align-items: center;
        margin: 20px 0 20px 0;
        padding: 0;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
    }
    
    .section-icon {
        font-size: 1.1rem;
        margin-right: 8px;
        opacity: 0.8;
    }
    
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
        padding: 0;
    }
    
    /* Lap summary styling */
    .lap-summary {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin: 8px 0;
        padding: 8px;
        background: rgba(49, 51, 63, 0.1);
        border-radius: 4px;
        font-size: 0.8rem;
    }
    
    .lap-summary-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .summary-label {
        font-size: 0.7rem;
        opacity: 0.7;
    }
    
    .summary-value {
        font-weight: bold;
    }
    
    /* Improve mobile responsiveness */
    @media (max-width: 768px) {
        .metrics-grid {
            gap: 3px;
        }
        
        .metric-card {
            min-width: 60px;
            padding: 3px;
        }
        
        .metric-label {
            font-size: 0.6rem;
        }
        
        .metric-value {
            font-size: 0.7rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">📋</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">Activities</span>', unsafe_allow_html=True)
    display_df, selected_rows = build_activity_table(df)
    selected = get_selected_row(df, selected_rows)
    
    # Create a wrapper div for consistent spacing - ALWAYS use this
    st.markdown('<div class="unified-activity-layout">', unsafe_allow_html=True)
    
    if selected is not None:
        # Single column layout for predictable spacing
        render_summary_metrics(selected)
        
        # No spacing between components
        render_map(selected) 
        
        # Lap chart with tighter integration
        render_lap_chart(selected)
        
        # Close the wrapper
        st.markdown('</div>', unsafe_allow_html=True)
        
        # AI analysis can remain outside the unified layout
        render_ai_analysis(selected)      
    else:
        # Show a message
        st.info("Please select an activity.")
        
        # Always render a placeholder map to establish layout structure
        # This loads the map component so subsequent renders won't cause jumps
        render_map(None)
        
        # Don't render lap chart until an activity is selected
        # Just add some padding to maintain consistent layout height
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        
        # Close the wrapper
        st.markdown('</div>', unsafe_allow_html=True)
