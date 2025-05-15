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

try:
    from streamlit_elements import elements, mui, html, sync, lazy, dashboard
    STREAMLIT_ELEMENTS_AVAILABLE = True
    print ("true", STREAMLIT_ELEMENTS_AVAILABLE)
except ImportError:
    print ("false", STREAMLIT_ELEMENTS_AVAILABLE)
    STREAMLIT_ELEMENTS_AVAILABLE = False

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
    global STREAMLIT_ELEMENTS_AVAILABLE
    st.title("📋 Activities")

    # Sort and reset index for consistent row selection
    sorted_df = df.sort_values("Date", ascending=False).reset_index(drop=True)
    # print (sorted_df)

    st.markdown("### 🧾 Click a row below to select")

    # --- Device detection for default mobile view ---
    if "is_mobile" not in st.session_state:
        user_agent = st_javascript("window.navigator.userAgent")
        st.write(f"[DEBUG] User agent: {user_agent}")
        if user_agent:
            is_mobile = any(x in user_agent for x in ["Android", "webOS", "iPhone", "iPad", "iPod", "BlackBerry", "IEMobile", "Opera Mini"])
            st.session_state['is_mobile'] = is_mobile
            st.write(f"[DEBUG] Detected mobile: {is_mobile}")
        else:
            st.session_state['is_mobile'] = False
            st.write("[DEBUG] Could not detect user agent, defaulting to desktop mode.")
    else:
        st.write(f"[DEBUG] Cached is_mobile: {st.session_state['is_mobile']}")

    # Use detected value for default
    mobile_view = st.toggle("📱 Mobile View", value=st.session_state.get('is_mobile', False))
    st.write(f"[DEBUG] Mobile view toggle value: {mobile_view}")

    # Choose columns for table
    display_columns = (
        ["Date", "Name", "Distance (km)", "Pace (min/km)", "Avg HR"]
        if mobile_view else
        ["Date", "Name", "Type", "Workout Type", "Description", "Distance (km)", "Pace (min/km)", "Moving Time", "Cadence", "Avg HR", "Elevation Gain"]
    )
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
        height=220 if mobile_view else 350
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
        
        day_str = selected_row['Date'].strftime('%A')
        date_str = selected_row['Date'].strftime('%Y-%m-%d')
        name_str = selected_row['Name']
        st.text(f"{day_str}  -- {date_str} -- {name_str}")
        
        # --- Workout Type & Description Card (side by side) ---
        Running_Type = selected_row.get("Type", "-")
        elapsed_time = selected_row.get("Elapsed Time (min)", "-")
        Distance = selected_row.get("Distance (km)", "-")
        Pace = selected_row.get("Pace (min/km)", "-")
        moving_time = selected_row.get("Moving Time", "-")
        cadence = selected_row.get("Cadence", "-")
        avg_hr = selected_row.get("Avg HR", "-")
        max_hr = selected_row.get("Max HR", "-")
        power = selected_row.get("Power (W)", "-")
        calories = selected_row.get("Calories", "-")
        elevation_gain = selected_row.get("Elevation Gain", "-")
        desc = selected_row.get("Description", "-")

        if mobile_view:
            st.markdown(
                f"""
                <div style='display:flex;flex-direction:column;gap:1.2rem;margin-bottom:1.2rem;'>
                    <div style='background:#222733;border-radius:12px;padding:0.7rem 1rem;'>
                        <span style='font-weight:600;color:#1EBEFF;'>🏷️ Running Type:</span> {Running_Type}<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>⏳ Elapsed Time:</span> {elapsed_time} min<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>⏱️ Moving Time:</span> {moving_time} min<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>🏃‍♂️ Distance:</span> {Distance} km<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>⚡ Pace:</span> {Pace} min/km<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>🏔️ Elevation Gain:</span> {elevation_gain} m<br/>
                    </div>
                    <div style='background:#222733;border-radius:12px;padding:0.7rem 1rem;'>
                        <span style='font-weight:600;color:#b0b8c9;'>👟 Cadence:</span> {cadence} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>❤️ Avg HR:</span> {avg_hr} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>💖 Max HR:</span> {max_hr} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>🔋 Power:</span> {power} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>🔥 Calories:</span> {calories} <br>
                    </div>
                    <div style='background:#222733;border-radius:12px;padding:0.7rem 1rem;'>
                        <span style='font-weight:600;color:#b0b8c9;'>📝 Description:</span><br>
                        <span style='color:#e0e6f7;font-size:1rem;'>{desc}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style='display:flex;gap:1.2rem;margin-bottom:1.2rem;'>
                    <div style='background:#222733;border-radius:12px;padding:0.7rem 1rem;'>
                        <span style='font-weight:600;color:#1EBEFF;'>🏷️ Running Type:</span> {Running_Type}<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>⏳ Elapsed Time:</span> {elapsed_time} min<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>⏱️ Moving Time:</span> {moving_time} min<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>🏃‍♂️ Distance:</span> {Distance} km<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>⚡ Pace:</span> {Pace} min/km<br/>
                        <span style='font-weight:600;color:#1EBEFF;'>🏔️ Elevation Gain:</span> {elevation_gain} m<br/>
                    </div>
                    <div style='background:#222733;border-radius:12px;padding:0.7rem 1rem;'>
                        <span style='font-weight:600;color:#b0b8c9;'>👟 Cadence:</span> {cadence} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>❤️ Avg HR:</span> {avg_hr} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>💖 Max HR:</span> {max_hr} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>🔋 Power:</span> {power} <br>
                        <span style='font-weight:600;color:#b0b8c9;'>🔥 Calories:</span> {calories} <br>
                    </div>
                    <div style='background:#222733;border-radius:12px;padding:0.7rem 1rem;flex:1;'>
                        <span style='font-weight:600;color:#b0b8c9;'>📝 Description:</span><br>
                        <span style='color:#e0e6f7;font-size:1rem;'>{desc}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )

        # Map view if Route Polyline is available
        map_html = None
        show_3d = False
        if "Route Polyline" in selected_row and pd.notna(selected_row["Route Polyline"]):
            show_3d = st.toggle("🗺️ 3D Map View", value=False, key="toggle_3d_map")
            coords = None
            try:
                import polyline
                coords = polyline.decode(selected_row["Route Polyline"])
            except Exception as e:
                st.warning(f"Could not decode route polyline: {e}")

            if coords:
                if show_3d:
                    import pydeck as pdk
                    route_df = pd.DataFrame(coords, columns=["lat", "lon"])
                    mapbox_api_key = st.secrets.get("MAPBOX_API_KEY", "")
                    pdk.settings.mapbox_api_key = mapbox_api_key

                    # --- Fetch elevations for each point ---
                    with st.spinner("Fetching elevation data for 3D route..."):
                        elevations = fetch_elevations(coords)
                    # Build [lon, lat, elevation] for PathLayer
                    path_coords = [[lon, lat, elev] for (lat, lon), elev in zip(coords, elevations)]

                    # TerrainLayer for real 3D terrain
                    terrain_layer = pdk.Layer(
                        "TerrainLayer",
                        data=None,
                        elevation_decoder={
                            "rScaler": 256,
                            "gScaler": 1,
                            "bScaler": 1/256,
                            "offset": -32768
                        },
                        texture="https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/256/{z}/{x}/{y}@2x?access_token=" + mapbox_api_key,
                        elevation_data="https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
                        bounds=[-180, -85.051129, 180, 85.051129],
                        wireframe=False,
                        material=True,
                    )
                    # PathLayer for the route (now with elevation)
                    path_layer = pdk.Layer(
                        "PathLayer",
                        [
                            {
                                "path": path_coords,
                                "color": [30, 190, 255],
                                "width": 6,
                            }
                        ],
                        get_path="path",
                        get_color="color",
                        width_scale=5,
                        width_min_pixels=3,
                        get_width=6,
                        opacity=0.9,
                        pickable=False,
                        auto_highlight=True,
                        material=True,
                    )
                    midpoint = route_df.iloc[len(route_df)//2]
                    view_state = pdk.ViewState(
                        longitude=midpoint["lon"],
                        latitude=midpoint["lat"],
                        zoom=14,
                        pitch=60,
                        bearing=30,
                    )
                    st.pydeck_chart(
                        pdk.Deck(
                            layers=[terrain_layer, path_layer],
                            initial_view_state=view_state,
                            map_style=None,
                        ),
                        width=350,
                        height=250,
                    )
                    map_html = "pydeck"
                else:
                    import folium
                    from streamlit_folium import st_folium
                    m = folium.Map(location=coords[0], zoom_start=13)
                    folium.PolyLine(coords, color="blue", weight=3).add_to(m)
                    map_html = m
            else:
                st.warning("No route coordinates available for map rendering.")

        lap_df = pd.DataFrame()
        if "Lap Details" in selected_row and pd.notna(selected_row["Lap Details"]):
            try:
                import matplotlib.pyplot as plt
                from streamlit_folium import st_folium
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
                    # Map display (folium only, not pydeck)
                    if map_html is not None and map_html != "pydeck":
                        if mobile_view:
                            st.markdown("<div style='margin-bottom:1.2rem;border-radius:14px;overflow:hidden;border:2px solid #1EBEFF;'>", unsafe_allow_html=True)
                            st_folium(map_html, width=350, height=250)
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='display:flex;gap:1.2rem;margin-bottom:1.2rem;'>", unsafe_allow_html=True)
                            st.markdown("<div style='flex:1;min-width:350px;border-radius:14px;overflow:hidden;border:2px solid #1EBEFF;'>", unsafe_allow_html=True)
                            st_folium(map_html, width=350, height=250)
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("<div style='flex:2;'>", unsafe_allow_html=True)

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

                    if map_html is not None and map_html != "pydeck" and not mobile_view:
                        st.markdown("</div></div>", unsafe_allow_html=True)

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
                    # Gather all relevant fields
                    Running_Type = selected_row.get("Type", "-")
                    elapsed_time = selected_row.get("Elapsed Time (min)", "-")
                    Distance = selected_row.get("Distance (km)", "-")
                    Pace = selected_row.get("Pace (min/km)", "-")
                    moving_time = selected_row.get("Moving Time", "-")
                    cadence = selected_row.get("Cadence", "-")
                    avg_hr = selected_row.get("Avg HR", "-")
                    max_hr = selected_row.get("Max HR", "-")
                    power = selected_row.get("Power (W)", "-")
                    calories = selected_row.get("Calories", "-")
                    elevation_gain = selected_row.get("Elevation Gain", "-")
                    desc = selected_row.get("Description", "-")
                    prompt = (
                        "Analyze this running activity based on the following data. Look at per lap data as well if available.\n"
                        "Comment on what is the impact of the activity, what is executed well, and what needs to be improved.\n"
                        f"Day: {day_str}, Date: {date_str}, Name: {name_str}\n"
                        f"Type: {Running_Type}\n"
                        f"Elapsed Time: {elapsed_time} min\n"
                        f"Moving Time: {moving_time} min\n"
                        f"Distance: {Distance} km\n"
                        f"Pace: {format_pace(Pace) if Pace != '-' else '-'} min/km\n"
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
                    # print (f"AI Prompt \n: {prompt}")
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

