"""
Modern Activities View - Redesigned UI for Sepehr's Running Tracker
Features:
- Modern card-based design system
- Mobile-first responsive layout
- Improved information architecture
- Enhanced data visualization
- Better user experience
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import numpy as np
from datetime import datetime, timedelta
import math
import re

def safe_float_convert(value, default=0.0):
    """Safely convert a value to float, handling N/A, None, and invalid values"""
    if value is None or pd.isna(value):
        return default
    
    # Handle string values
    if isinstance(value, str):
        value = str(value).strip()
        if value.upper() in ['N/A', 'NAN', '', 'NONE']:
            return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def load_modern_css():
    """Load modern CSS styling for the activities view"""
    st.markdown("""
    <style>
    /* Modern Design System Variables */
    :root {
        --primary-bg: #111827;
        --secondary-bg: #1f2937;
        --card-bg: rgba(31, 41, 55, 0.8);
        --accent-color: #3b82f6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --text-muted: #9ca3af;
        --border-color: rgba(75, 85, 99, 0.3);
        --shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    
    /* Modern Card System */
    .modern-card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
    }
    
    .modern-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-color);
    }
    
    .modern-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .modern-card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .modern-card-subtitle {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin: 4px 0 0 0;
    }
    
    /* Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }
    
    .metric-item {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-item:hover {
        background: rgba(59, 130, 246, 0.15);
        transform: scale(1.02);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-color);
        margin: 0;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 8px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-change {
        font-size: 0.75rem;
        margin-top: 4px;
        padding: 2px 8px;
        border-radius: 12px;
        display: inline-block;
    }
    
    .metric-change.positive {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
    }
    
    .metric-change.negative {
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger-color);
    }
    
    /* Activity Summary Cards */
    .activity-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }
    
    .summary-card {
        background: linear-gradient(135deg, var(--card-bg) 0%, rgba(59, 130, 246, 0.1) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        position: relative;
        overflow: hidden;
    }
    
    .summary-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-color), var(--success-color));
    }
    
    /* Performance Indicators */
    .performance-indicator {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .indicator-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.875rem;
    }
    
    .indicator-icon.excellent {
        background: var(--success-color);
        color: white;
    }
    
    .indicator-icon.good {
        background: var(--accent-color);
        color: white;
    }
    
    .indicator-icon.average {
        background: var(--warning-color);
        color: white;
    }
    
    .indicator-icon.poor {
        background: var(--danger-color);
        color: white;
    }
    
    /* Action Buttons */
    .action-buttons {
        display: flex;
        gap: 12px;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    
    .action-btn {
        background: var(--accent-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .action-btn:hover {
        background: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    .action-btn.secondary {
        background: var(--secondary-bg);
        border: 1px solid var(--border-color);
    }
    
    .action-btn.secondary:hover {
        background: var(--card-bg);
        border-color: var(--accent-color);
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .modern-card {
            padding: 16px;
            margin: 12px 0;
            border-radius: 12px;
        }
        
        .metrics-grid {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }
        
        .metric-item {
            padding: 16px;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
        
        .activity-summary {
            grid-template-columns: 1fr;
            gap: 16px;
        }
        
        .action-buttons {
            flex-direction: column;
        }
        
        .action-btn {
            width: 100%;
            justify-content: center;
        }
    }
    
    /* Loading States */
    .loading-skeleton {
        background: linear-gradient(90deg, var(--secondary-bg) 25%, var(--card-bg) 50%, var(--secondary-bg) 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 8px;
        height: 20px;
        margin: 8px 0;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Chart Containers */
    .chart-container {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        border: 1px solid var(--border-color);
    }
    
    /* Hide Streamlit Elements */
    .stDeployButton {
        display: none;
    }
    
    .stDecoration {
        display: none;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-bg);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #2563eb;
    }
    </style>
    """, unsafe_allow_html=True)

def create_modern_activity_table(df):
    """Create modern activity table with enhanced styling"""
    if df.empty:
        return
    
    # Prepare data for display - keep ALL data intact
    display_df = df.copy()
    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
    
    # Configure AgGrid with FULL dataframe
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection('single', use_checkbox=True)
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc='sum',
        editable=False
    )
    
    # Hide unwanted columns (don't remove them!)
    columns_to_hide = [
        'Activity ID', 'Stream Sheet',  # Add these two that are showing but not wanted
        'Avg HR', 'Max HR', 'Cadence', 'Power (W)', 'Weighted Power',
        'Calories', 'Moving Time', 'Elevation Gain', 'Elev Low', 'Elev High',
        'Route Polyline', 'Lap Details', 'Stream Data'
    ]
    
    # Hide columns that exist
    for col in columns_to_hide:
        if col in display_df.columns:
            gb.configure_column(col, hide=True)
    
    # Configure visible columns only
    gb.configure_column("Date", sort='desc', width=100)
    gb.configure_column("Name", width=200)
    gb.configure_column("Sport Type", width=80)
    gb.configure_column("Type", width=80)
    gb.configure_column("Workout Type", width=100)
    gb.configure_column("Description", width=150)
    gb.configure_column("Distance (km)", type=["numericColumn"], precision=2, width=100)
    gb.configure_column("Pace (min/km)", type=["numericColumn"], precision=2, width=100)
    gb.configure_column("Elapsed Time (min)", type=["numericColumn"], precision=0, width=110)
    
    gridOptions = gb.build()
    
    # Custom CSS for AgGrid
    custom_css = {
        ".ag-theme-streamlit": {
            "--ag-background-color": "rgba(31, 41, 55, 0.8)",
            "--ag-header-background-color": "rgba(17, 24, 39, 0.9)",
            "--ag-odd-row-background-color": "rgba(55, 65, 81, 0.3)",
            "--ag-row-hover-color": "rgba(59, 130, 246, 0.1)",
            "--ag-selected-row-background-color": "rgba(59, 130, 246, 0.2)",
            "--ag-border-color": "rgba(75, 85, 99, 0.3)",
            "--ag-header-foreground-color": "#f9fafb",
            "--ag-foreground-color": "#d1d5db",
        }
    }
    
    grid_response = AgGrid(
        display_df,  # Full dataframe with all columns
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        custom_css=custom_css,
        height=400
    )
    
    return grid_response

def create_route_map_from_polyline(selected_row):
    """Create route map from polyline data"""
    if selected_row is None:
        return
    
    # Convert to dict if needed
    if hasattr(selected_row, 'to_dict'):
        activity = selected_row.to_dict()
    else:
        activity = selected_row
    
    # Check if polyline data exists
    if 'Route Polyline' in activity and pd.notna(activity['Route Polyline']):
        try:
            import polyline
            coords = polyline.decode(activity['Route Polyline'])
            
            if coords:
                # Create map with route
                m = folium.Map(location=coords[0], zoom_start=13)
                
                # Add terrain theme
                folium.TileLayer(
                    tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
                    attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                    name='Terrain',
                    overlay=False,
                    control=True
                ).add_to(m)
                
                # Add start marker
                folium.Marker(
                    coords[0],
                    icon=folium.Icon(color='green', icon='play'),
                    popup='Start'
                ).add_to(m)
                
                # Add finish marker
                folium.Marker(
                    coords[-1],
                    icon=folium.Icon(color='red', icon='stop'),
                    popup='Finish'
                ).add_to(m)
                
                # Add route line
                folium.PolyLine(
                    coords,
                    color='#3b82f6',
                    weight=4,
                    opacity=0.8
                ).add_to(m)
                
                # Display map
                st_folium(m, width=350, height=300)
            else:
                st.info('📍 No route coordinates available')
        except ImportError:
            st.warning('📍 Polyline library not available for route decoding')
        except Exception as e:
            st.warning(f'📍 Could not decode route: {str(e)}')
    else:
        st.info('📍 No route polyline data available for this activity')

def create_activity_header_card(selected_row):
    """Create just the activity header card with name, date, and types"""
    if selected_row is None:
        return
    
    # Convert selected_row to dict if it's a pandas Series
    if hasattr(selected_row, 'to_dict'):
        activity = selected_row.to_dict()
    else:
        activity = selected_row
    
    # Create the main activity header
    description = activity.get('Description', '')
    description_html = ""
    
    # Clean and validate description
    if description and pd.notna(description):
        desc_str = str(description).strip()
        # Remove any HTML tags and clean the text
        desc_clean = re.sub(r'<[^>]+>', '', desc_str)
        desc_clean = desc_clean.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        
        if desc_clean and desc_clean not in ['nan', 'N/A', 'None', '']:
            # Escape any remaining HTML characters
            desc_escaped = desc_clean.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            description_html = f"<br><p style='margin-top: 12px; color: #9ca3af; font-style: italic;'>📝 {desc_escaped}</p>"
    
    # Prepare all metrics
    distance = safe_float_convert(activity.get('Distance (km)', 0))
    pace = safe_float_convert(activity.get('Pace (min/km)', 0))
    pace_formatted = convert_pace_to_mmss(pace)
    duration = safe_float_convert(activity.get('Elapsed Time (min)', 0))
    hours = int(duration // 60)
    minutes = int(duration % 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    # Heart Rate metrics
    avg_hr = activity.get('Avg HR', 'N/A')
    avg_hr_display = f"{safe_float_convert(avg_hr):.0f}" if pd.notna(avg_hr) and str(avg_hr) != 'nan' else 'N/A'
    
    max_hr = activity.get('Max HR', 'N/A')
    max_hr_display = f"{safe_float_convert(max_hr):.0f}" if pd.notna(max_hr) and str(max_hr) != 'nan' else 'N/A'
    
    # Elevation metrics
    elev_gain = activity.get('Elevation Gain', 'N/A')
    elev_gain_display = f"{safe_float_convert(elev_gain):.0f}m" if pd.notna(elev_gain) and str(elev_gain) != 'nan' else 'N/A'
    
    elev_low = activity.get('Elev Low', 'N/A')
    elev_low_display = f"{safe_float_convert(elev_low):.0f}m" if pd.notna(elev_low) and str(elev_low) != 'nan' else 'N/A'
    
    elev_high = activity.get('Elev High', 'N/A')
    elev_high_display = f"{safe_float_convert(elev_high):.0f}m" if pd.notna(elev_high) and str(elev_high) != 'nan' else 'N/A'
    
    # Performance metrics
    cadence = activity.get('Cadence', 'N/A')
    cadence_display = f"{safe_float_convert(cadence):.0f}" if pd.notna(cadence) and str(cadence) != 'nan' else 'N/A'
    
    power = activity.get('Power (W)', 'N/A')
    power_display = f"{safe_float_convert(power):.0f}W" if pd.notna(power) and str(power) != 'nan' else 'N/A'
    
    calories = activity.get('Calories', 'N/A')
    calories_display = f"{safe_float_convert(calories):.0f}" if pd.notna(calories) and str(calories) != 'nan' else 'N/A'
    
    moving_time = activity.get('Moving Time', 'N/A')
    workout_type = activity.get('Workout Type', 'N/A')
    weighted_power = activity.get('Weighted Power', 'N/A')
    
    # Render the header card with all metrics included
    st.markdown(f'''
    <div class="modern-card">
        <div class="modern-card-header">
            <div>
                <h2 class="modern-card-title">
                    🎯 {activity.get('Name', 'Unknown Activity')}
                </h2>
                <p class="modern-card-subtitle">
                    📅 {activity.get('Date', 'Unknown Date')} • 
                    🏃‍♂️ {activity.get('Sport Type', 'Running')} • 
                    🏷️ {activity.get('Type', 'N/A')} • 
                    💪 {workout_type}
                </p>
                <p class="modern-card-subtitle">
                    🏃 {distance:.2f} km • 
                    ⚡ {pace_formatted} • 
                    ⏱️ {duration_str} • 
                    🕐 {moving_time} • 
                    🔥 {calories_display} cal
                </p>
                <p class="modern-card-subtitle">
                    ❤️ {avg_hr_display} avg • 
                    💓 {max_hr_display} max • 
                    👟 {cadence_display} spm • 
                    ⚡ {power_display} • 
                    🏋️ {weighted_power}W
                </p>
                <p class="modern-card-subtitle">
                    ⛰️ {elev_gain_display} gain • 
                    📉 {elev_low_display} low • 
                    📈 {elev_high_display} high
                </p>{description_html}
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def create_performance_analysis_card(selected_row):
    """Create performance analysis header card with advanced metrics"""
    if selected_row is None:
        return
    
    # Convert selected_row to dict if it's a pandas Series
    if hasattr(selected_row, 'to_dict'):
        activity = selected_row.to_dict()
    else:
        activity = selected_row
    
    # Prepare performance metrics
    distance = safe_float_convert(activity.get('Distance (km)', 0))
    duration = safe_float_convert(activity.get('Elapsed Time (min)', 0))
    pace = safe_float_convert(activity.get('Pace (min/km)', 0))
    calories = activity.get('Calories', 'N/A')
    avg_hr = activity.get('Avg HR', 'N/A')
    
    # Build performance analysis lines
    performance_lines = []
    
    # Power Analysis (if available)
    weighted_power = activity.get('Weighted Power', 'N/A')
    power = activity.get('Power (W)', 'N/A')
    if pd.notna(weighted_power) and str(weighted_power) not in ['nan', 'N/A', ''] and pd.notna(power) and str(power) != 'nan':
        power_ratio = safe_float_convert(weighted_power) / safe_float_convert(power) if safe_float_convert(power) > 0 else 0
        performance_lines.append(f"⚡ {safe_float_convert(power):.0f}W avg • 🏋️ {weighted_power}W weighted • 📊 {power_ratio:.2f} variability")
    
    # Performance Analysis
    if distance > 0 and duration > 0:
        avg_speed_kmh = (distance / (duration / 60))
        calories_per_km = safe_float_convert(calories) / distance if pd.notna(calories) and str(calories) != 'nan' else None
        
        # Performance rating based on pace
        if pace < 4.5:
            performance = "🔥 Elite"
        elif pace < 5.5:
            performance = "🏃‍♂️ Fast"
        elif pace < 6.5:
            performance = "⚡ Good"
        elif pace < 8.0:
            performance = "👍 Moderate"
        else:
            performance = "🚶‍♂️ Easy"
        
        # Training load estimate (if HR data available)
        training_load = ""
        if pd.notna(avg_hr) and str(avg_hr) != 'nan':
            load_value = (safe_float_convert(avg_hr) * duration) / 100
            training_load = f" • 🎯 {load_value:.1f} load"
        
        calories_text = f" • 🔥 {calories_per_km:.0f} kcal/km" if calories_per_km else ""
        performance_lines.append(f"🚀 {avg_speed_kmh:.1f} km/h speed • {performance} level{calories_text}{training_load}")
    
    # Elevation Analysis
    elev_gain = activity.get('Elevation Gain', 'N/A')
    if pd.notna(elev_gain) and str(elev_gain) != 'nan' and safe_float_convert(elev_gain) > 0:
        elev_per_km = safe_float_convert(elev_gain) / distance if distance > 0 else 0
        
        # Grade calculation
        if elev_per_km > 100:
            grade_description = "Very Hilly 🏔️"
        elif elev_per_km > 50:
            grade_description = "Hilly ⛰️"
        elif elev_per_km > 20:
            grade_description = "Rolling 🌄"
        else:
            grade_description = "Flat 🏞️"
        
        performance_lines.append(f"🏔️ {elev_per_km:.1f} m/km grade • {grade_description}")
    
    # Only render the card if we have performance data
    if performance_lines:
        performance_html = "<br>".join([f'<p class="modern-card-subtitle">{line}</p>' for line in performance_lines])
        
        st.markdown(f'''
        <div class="modern-card">
            <div class="modern-card-header">
                <div>
                    <h2 class="modern-card-title">
                        📈 Performance Analysis
                    </h2>
                    {performance_html}
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

def create_selected_activity_card(selected_row):
    """Create a comprehensive card showing details of the selected activity (without header)"""
    if selected_row is None:
        st.info('👆 **Select an activity** from the table above to see detailed metrics, route map, and lap analysis')
        return
    
    # Convert selected_row to dict if it's a pandas Series
    if hasattr(selected_row, 'to_dict'):
        activity = selected_row.to_dict()
    else:
        activity = selected_row
    
    # Only show additional insights if any unique data is available
    st.info("📊 **Select different activities to compare performance metrics and route maps**")

def create_lap_analysis_chart(selected_row):
    """Create lap analysis chart with variable width bars proportional to distance"""
    if selected_row is None:
        return
    
    # Convert to dict if needed
    if hasattr(selected_row, 'to_dict'):
        activity = selected_row.to_dict()
    else:
        activity = selected_row
    
    lap_details = activity.get('Lap Details', '')
    
    if pd.isna(lap_details) or not str(lap_details) or str(lap_details) in ['nan', 'N/A']:
        st.info("📊 No lap data available for this activity")
        return
    
    # Removed the header card - just start with the chart
    try:
        # Parse lap details
        lap_data = []
        cumulative_distance = 0
        
        # Split by " | " to get individual laps
        laps = str(lap_details).split(' | ')
        
        for i, lap in enumerate(laps):
            if not lap.strip():
                continue
                
            # Extract all available metrics using regex
            import re
            distance_match = re.search(r'(\d+\.?\d*)km', lap)
            pace_match = re.search(r'pace (\d+\.?\d+)', lap)
            hr_match = re.search(r'HR (\d+\.?\d*)', lap)  # Handle decimal HR values
            cadence_match = re.search(r'Cad (\d+\.?\d*)', lap)  # Handle decimal cadence and "Cad" format
            power_match = re.search(r'power (\d+)', lap)
            
            # More flexible patterns for elevation and time
            elevation_match = re.search(r'ElevGain (\d+\.?\d*)', lap)  # Match "ElevGain" format
            time_match = re.search(r'time\s*(\d+):(\d+)', lap, re.IGNORECASE)
            
            # Alternative time patterns
            if not time_match:
                time_match = re.search(r'(\d+):(\d+)(?:\s*min)?', lap)
            if not time_match:
                time_match = re.search(r'(\d+)m\s*(\d+)s', lap)  # Format like "5m 32s"
            
            # Alternative elevation patterns (keep as fallback)
            if not elevation_match:
                elevation_match = re.search(r'elev(?:ation)?\s*(\d+)', lap, re.IGNORECASE)
            if not elevation_match:
                elevation_match = re.search(r'(\d+)\s*m(?:eters?)?(?:\s*elev)', lap, re.IGNORECASE)
            if not elevation_match:
                elevation_match = re.search(r'alt(?:itude)?\s*(\d+)', lap, re.IGNORECASE)
            
            if distance_match and pace_match:
                distance = safe_float_convert(distance_match.group(1))
                pace_decimal = safe_float_convert(pace_match.group(1))
                pace_formatted = convert_pace_to_mmss(pace_decimal)
                
                # Extract additional metrics
                hr = safe_float_convert(hr_match.group(1)) if hr_match else None
                cadence = safe_float_convert(cadence_match.group(1)) if cadence_match else None
                power = int(safe_float_convert(power_match.group(1))) if power_match else None
                elevation = safe_float_convert(elevation_match.group(1)) if elevation_match else None
                
                # Extract time and convert to formatted string
                time_formatted = None
                if time_match:
                    minutes = int(time_match.group(1))
                    seconds = int(time_match.group(2))
                    time_formatted = f"{minutes}:{seconds:02d}"
                
                lap_data.append({
                    'lap': i + 1,
                    'distance': distance,
                    'pace_decimal': pace_decimal,
                    'pace_formatted': pace_formatted,
                    'hr': hr,
                    'cadence': cadence,
                    'power': power,
                    'elevation': elevation,
                    'time_formatted': time_formatted,
                    'start_distance': cumulative_distance,
                    'end_distance': cumulative_distance + distance
                })
                
                cumulative_distance += distance
        
        if not lap_data:
            st.info("📊 Could not parse lap data")
            return
        
        # Create comprehensive chart with multiple metrics
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Pace by Distance', 'Heart Rate & Power'),
            shared_xaxes=True,
            vertical_spacing=0.1,
            specs=[[{"secondary_y": False}], [{"secondary_y": True}]],
            row_heights=[0.67, 0.33]  # Make pace chart exactly double the height
        )
        
        # Determine color scale based on pace
        paces = [lap['pace_decimal'] for lap in lap_data]
        min_pace = min(paces)
        max_pace = max(paces)
        
        # Add pace bars (top subplot)
        for i, lap in enumerate(lap_data):
            # Normalize pace for color (0 = fastest/green, 1 = slowest/red)
            if max_pace != min_pace:
                pace_norm = (lap['pace_decimal'] - min_pace) / (max_pace - min_pace)
            else:
                pace_norm = 0.5
            
            # Color interpolation from green (fast) to red (slow)
            red = int(255 * pace_norm)
            green = int(255 * (1 - pace_norm))
            color = f'rgba({red}, {green}, 50, 0.8)'
            
            # Add pace bar
            fig.add_shape(
                type="rect",
                x0=lap['start_distance'],
                x1=lap['end_distance'],
                y0=0,
                y1=lap['pace_decimal'],
                fillcolor=color,
                line=dict(color="rgba(255,255,255,0.3)", width=1),
                row=1, col=1
            )
            
            # Add pace annotation
            fig.add_annotation(
                x=(lap['start_distance'] + lap['end_distance']) / 2,
                y=lap['pace_decimal'] + 0.1,
                text=lap['pace_formatted'],
                showarrow=False,
                font=dict(size=9, color="white"),
                bgcolor="rgba(0,0,0,0.6)",
                bordercolor="white",
                borderwidth=1,
                row=1, col=1
            )
        
        # Add heart rate line (bottom subplot)
        hr_data = [lap for lap in lap_data if lap['hr'] is not None]
        if hr_data:
            hr_x = [(lap['start_distance'] + lap['end_distance']) / 2 for lap in hr_data]
            hr_y = [lap['hr'] for lap in hr_data]
            
            fig.add_trace(
                go.Scatter(
                    x=hr_x, y=hr_y,
                    mode='lines+markers',
                    name='Heart Rate',
                    line=dict(color='#ef4444', width=3),
                    marker=dict(size=6)
                ),
                row=2, col=1
            )
        
        # Add power line (bottom subplot, secondary y-axis)
        power_data = [lap for lap in lap_data if lap['power'] is not None]
        if power_data:
            power_x = [(lap['start_distance'] + lap['end_distance']) / 2 for lap in power_data]
            power_y = [lap['power'] for lap in power_data]
            
            fig.add_trace(
                go.Scatter(
                    x=power_x, y=power_y,
                    mode='lines+markers',
                    name='Power',
                    line=dict(color='#f59e0b', width=3),
                    marker=dict(size=6),
                    yaxis='y4'
                ),
                row=2, col=1, secondary_y=True
            )
        
        # Update layout
        fig.update_layout(
            title="",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update axes
        fig.update_xaxes(
            title_text="Cumulative Distance (km)",
            gridcolor='rgba(128,128,128,0.2)',
            linecolor='rgba(128,128,128,0.3)',
            row=2, col=1
        )
        
        fig.update_yaxes(
            title_text="Pace (min/km)",
            gridcolor='rgba(128,128,128,0.2)',
            linecolor='rgba(128,128,128,0.3)',
            row=1, col=1
        )
        
        fig.update_yaxes(
            title_text="Heart Rate (bpm)",
            gridcolor='rgba(128,128,128,0.2)',
            linecolor='rgba(128,128,128,0.3)',
            row=2, col=1
        )
        
        if power_data:
            fig.update_yaxes(
                title_text="Power (W)",
                side="right",
                row=2, col=1, secondary_y=True
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Create comprehensive breakdown table
        st.markdown("#### 📋 **Complete Lap Breakdown**")
        
        # Build table data with all available metrics
        table_data = []
        for lap in lap_data:
            row = {
                'Lap': lap['lap'],
                'Distance (km)': f"{lap['distance']:.2f}",
                'Pace': lap['pace_formatted'],
                'Cumulative (km)': f"{lap['end_distance']:.2f}"
            }
            
            # Add optional metrics if available
            if lap['hr'] is not None:
                row['Avg HR'] = f"{lap['hr']:.1f} bpm"
            if lap['cadence'] is not None:
                row['Cadence'] = f"{lap['cadence']:.1f} spm"
            if lap['power'] is not None:
                row['Power'] = f"{lap['power']} W"
            if lap['elevation'] is not None:
                row['Elevation Gain'] = f"{lap['elevation']:.1f} m"
            if lap['time_formatted'] is not None:
                row['Time'] = lap['time_formatted']
            
            table_data.append(row)
        
        lap_df = pd.DataFrame(table_data)
        
        st.dataframe(
            lap_df,
            use_container_width=True,
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"Error parsing lap data: {str(e)}")
        st.info("📊 Raw lap data format may have changed")

def create_horizontal_lap_chart(selected_row):
    """Create horizontal lap comparison chart with fixed height"""
    if selected_row is None:
        return
    
    # Convert to dict if needed
    if hasattr(selected_row, 'to_dict'):
        activity = selected_row.to_dict()
    else:
        activity = selected_row
    
    lap_details = activity.get('Lap Details', '')
    
    if pd.isna(lap_details) or not str(lap_details) or str(lap_details) in ['nan', 'N/A']:
        st.info("📊 No lap data available")
        return
    
    try:
        # Parse lap details (reuse existing logic)
        lap_data = []
        laps = str(lap_details).split(' | ')
        
        for i, lap in enumerate(laps):
            if not lap.strip():
                continue
                
            # Extract all available metrics using regex
            import re
            distance_match = re.search(r'(\d+\.?\d*)km', lap)
            pace_match = re.search(r'pace (\d+\.?\d+)', lap)
            hr_match = re.search(r'HR (\d+\.?\d*)', lap)
            cadence_match = re.search(r'Cad (\d+\.?\d*)', lap)
            elevation_match = re.search(r'ElevGain (\d+\.?\d*)', lap)
            time_match = re.search(r'(\d+):(\d+)', lap)
            
            if distance_match and pace_match:
                distance = safe_float_convert(distance_match.group(1))
                pace_decimal = safe_float_convert(pace_match.group(1))
                pace_formatted = convert_pace_to_mmss(pace_decimal)
                
                # Extract additional metrics
                hr = safe_float_convert(hr_match.group(1)) if hr_match else None
                cadence = safe_float_convert(cadence_match.group(1)) if cadence_match else None
                elevation = safe_float_convert(elevation_match.group(1)) if elevation_match else None
                
                time_formatted = None
                if time_match:
                    minutes = int(time_match.group(1))
                    seconds = int(time_match.group(2))
                    time_formatted = f"{minutes}:{seconds:02d}"
                
                lap_data.append({
                    'lap': i + 1,
                    'distance': distance,
                    'pace_decimal': pace_decimal,
                    'pace_formatted': pace_formatted,
                    'hr': hr,
                    'cadence': cadence,
                    'elevation': elevation,
                    'time_formatted': time_formatted
                })
        
        if not lap_data:
            st.info("📊 Could not parse lap data")
            return
        
        # Calculate average pace for reference line
        avg_pace = sum(lap['pace_decimal'] for lap in lap_data) / len(lap_data)
        avg_pace_formatted = convert_pace_to_mmss(avg_pace)
        
        # Create horizontal bar chart
        fig = go.Figure()
        
        # Determine colors based on pace performance
        paces = [lap['pace_decimal'] for lap in lap_data]
        min_pace = min(paces)
        max_pace = max(paces)
        
        # Create data for the chart
        y_labels = []
        colors = []
        pace_values = []
        
        for lap in reversed(lap_data):  # Reverse to show lap 1 at top
            # Create label with lap info
            label_parts = [f"Lap {lap['lap']}"]
            
            y_labels.append(f"Lap {lap['lap']}")
            pace_values.append(lap['pace_decimal'])
            
            # Color based on pace performance
            if max_pace != min_pace:
                pace_norm = (lap['pace_decimal'] - min_pace) / (max_pace - min_pace)
            else:
                pace_norm = 0.5
            
            # Color scheme: green (fast) to red (slow)
            if pace_norm < 0.33:
                colors.append('#10b981')  # Green
            elif pace_norm < 0.67:
                colors.append('#3b82f6')  # Blue
            else:
                colors.append('#ef4444')  # Red
        
        # Add horizontal bars
        fig.add_trace(go.Bar(
            x=pace_values,
            y=y_labels,
            orientation='h',
            marker=dict(color=colors),
            text=[lap['pace_formatted'] for lap in reversed(lap_data)],
            textposition='inside',
            textfont=dict(color='white', size=10),
            name='Pace'
        ))
        
        # Add metrics annotations to the right of bars
        max_pace_value = max(pace_values)
        for i, lap in enumerate(reversed(lap_data)):
            y_pos = i  # Position for each bar
            
            # Create annotation text with available metrics
            metrics_text = []
            metrics_text.append(f"⚡ {lap['pace_formatted']}")
            
            if lap['hr']:
                metrics_text.append(f"❤️ {lap['hr']:.0f}")
            
            if lap['elevation']:
                metrics_text.append(f"⛰️ {lap['elevation']:.0f}m")
            
            annotation_text = " • ".join(metrics_text)
            
            fig.add_annotation(
                x=max_pace_value + 0.3,  # Position to the right of the bars
                y=y_pos,
                text=annotation_text,
                showarrow=False,
                font=dict(size=15, color='white'),  # Reduced from 30 to 15 (half size)
                xanchor='left',
                yanchor='middle'
            )
        
        # Add average pace line
        fig.add_vline(
            x=avg_pace,
            line=dict(color='red', width=2, dash='dash'),
            annotation_text=f'Avg: {avg_pace_formatted}',
            annotation_position='top'
        )
        
        # Update layout
        fig.update_layout(
            title="",
            xaxis_title="Pace (min/km)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=800,  # Doubled from 400 to 800
            showlegend=False,
            margin=dict(l=60, r=150, t=20, b=40),  # Increased right margin for annotations
            xaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                linecolor='rgba(128,128,128,0.3)',
                range=[0, max_pace_value + 2]  # Extend x-axis for annotations
            ),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                linecolor='rgba(128,128,128,0.3)'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating horizontal lap chart: {str(e)}")

def convert_pace_to_mmss(decimal_pace):
    """Convert decimal pace (e.g., 7.70) to mm:ss format (e.g., '7:42')"""
    if pd.isna(decimal_pace):
        return "N/A"
    
    minutes = int(decimal_pace)
    seconds = int((decimal_pace - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def show_modern_activities():
    """Main function to display the modern activities view"""
    # Load modern CSS
    load_modern_css()
    
    # Load data
    try:
        # Check if activities_data exists in session state and is not empty
        if 'activities_data' in st.session_state:
            activities_df = st.session_state.activities_data
            if activities_df is not None and not activities_df.empty:
                df = activities_df.copy()
            else:
                st.warning("⚠️ No activity data available. Please check your data source.")
                return
        else:
            st.warning("⚠️ No activity data available. Please check your data source.")
            return
        
        # Create layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Modern Activity Table
            grid_response = create_modern_activity_table(df)
        
        # Determine selected row after table is rendered
        selected_row = None
        if grid_response and 'selected_rows' in grid_response:
            selected_rows = grid_response['selected_rows']
            # Properly handle different types of selected_rows
            if isinstance(selected_rows, pd.DataFrame):
                has_selection = not selected_rows.empty
            elif isinstance(selected_rows, list):
                has_selection = len(selected_rows) > 0
            else:
                has_selection = False
            
            if has_selection:
                if isinstance(selected_rows, pd.DataFrame):
                    selected_row = selected_rows.iloc[0]
                else:
                    selected_row = selected_rows[0]
        
        # Add lap analysis to left column after determining selected_row
        with col1:
            if selected_row is not None:
                # Add activity header card (moved from right column)
                create_activity_header_card(selected_row)
                # Add performance analysis card (moved from right column)
                create_performance_analysis_card(selected_row)
                # Add lap analysis chart (without header)
                create_lap_analysis_chart(selected_row)
        
        with col2:
            # Route Map
            create_route_map_from_polyline(selected_row)
            
            # Horizontal Lap Chart
            if selected_row is not None:
                create_horizontal_lap_chart(selected_row)
            
            # Activity Details Card (without header)
            if selected_row is not None:
                create_selected_activity_card(selected_row)
            else:
                st.info("👆 **Select an activity** from the table above to see detailed metrics and route map")
    
    except Exception as e:
        st.error(f"❌ Error loading activities: {str(e)}")
        st.info("💡 Please check your data source and try again.")

if __name__ == "__main__":
    show_modern_activities() 