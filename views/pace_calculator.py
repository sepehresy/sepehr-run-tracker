import streamlit as st
import re
from datetime import timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE

def parse_pace_input(pace_str):
    """Parse pace input in MM:SS format"""
    if not pace_str:
        return None
    pace_str = pace_str.strip()
    match = re.match(r'^(\d{1,2}):(\d{2})$', pace_str)
    if match:
        minutes, seconds = map(int, match.groups())
        return timedelta(minutes=minutes, seconds=seconds)
    return None

def parse_time_input(time_str):
    """Parse time input in HH:MM:SS or MM:SS format"""
    if not time_str:
        return None
    time_str = time_str.strip()
    
    # Try HH:MM:SS format
    match = re.match(r'^(\d{1,2}):(\d{2}):(\d{2})$', time_str)
    if match:
        hours, minutes, seconds = map(int, match.groups())
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    # Try MM:SS format
    match = re.match(r'^(\d{1,3}):(\d{2})$', time_str)
    if match:
        minutes, seconds = map(int, match.groups())
        return timedelta(minutes=minutes, seconds=seconds)
    
    return None

def format_pace(td):
    """Format timedelta to MM:SS pace string"""
    if not td:
        return ""
    total_seconds = int(td.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def format_time(td):
    """Format timedelta to time string"""
    if not td:
        return ""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def calculate_time_from_pace(pace_td, distance_km):
    """Calculate finish time from pace and distance"""
    if not pace_td or not distance_km:
        return None
    total_seconds = pace_td.total_seconds() * distance_km
    return timedelta(seconds=total_seconds)

def calculate_pace_from_time(time_td, distance_km):
    """Calculate pace from finish time and distance"""
    if not time_td or not distance_km:
        return None
    pace_seconds = time_td.total_seconds() / distance_km
    return timedelta(seconds=pace_seconds)

def get_simple_css():
    """Simple, clean CSS"""
    return """
    <style>
    .pace-container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .pace-title {
        text-align: center;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        color: #f8fafc;
    }
    
    .pace-row {
        background: rgba(30, 41, 59, 0.9);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }
    
    .row-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #60a5fa;
        text-align: center;
    }
    
    .result-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    
    .result-box {
        background: rgba(51, 65, 85, 0.8);
        border-radius: 6px;
        padding: 0.5rem;
        text-align: center;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }
    
    .result-label {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-bottom: 0.25rem;
    }
    
    .result-value {
        font-size: 1rem;
        font-weight: 700;
        color: #f8fafc;
        font-family: 'Courier New', monospace;
    }
    
    .static-table {
        background: rgba(30, 41, 59, 0.9);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }
    
    .table-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #60a5fa;
        text-align: center;
    }
    
    .pace-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Courier New', monospace;
    }
    
    .pace-table th {
        background: rgba(51, 65, 85, 0.8);
        color: #94a3b8;
        padding: 0.75rem;
        text-align: center;
        border: 1px solid rgba(148, 163, 184, 0.2);
        font-size: 0.9rem;
    }
    
    .pace-table td {
        padding: 0.5rem;
        text-align: center;
        border: 1px solid rgba(148, 163, 184, 0.2);
        color: #f8fafc;
        font-size: 0.85rem;
    }
    
    .pace-table tr:nth-child(even) {
        background: rgba(51, 65, 85, 0.3);
    }
    
    .pace-table tr:hover {
        background: rgba(59, 130, 246, 0.2);
    }
    
    @media (max-width: 768px) {
        .result-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .pace-table {
            font-size: 0.75rem;
        }
        
        .pace-table th, .pace-table td {
            padding: 0.4rem;
        }
    }
    </style>
    """

def create_static_pace_table():
    """Create static pace/time reference table"""
    paces = ["4:00", "4:30", "5:00", "5:30", "6:00", "6:30", "7:00", "7:30", "8:00", "8:30", "9:00", "9:30", "10:00"]
    distances = {"5K": 5.0, "10K": 10.0, "Half": 21.0975, "Marathon": 42.195}
    
    table_html = """
    <table class="pace-table">
        <thead>
            <tr>
                <th>Pace/km</th>
                <th>5K</th>
                <th>10K</th>
                <th>Half Marathon</th>
                <th>Marathon</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for pace_str in paces:
        pace_td = parse_pace_input(pace_str)
        if pace_td:
            table_html += f"<tr><td><strong>{pace_str}</strong></td>"
            for dist_name, dist_km in distances.items():
                time_td = calculate_time_from_pace(pace_td, dist_km)
                time_str = format_time(time_td)
                table_html += f"<td>{time_str}</td>"
            table_html += "</tr>"
    
    table_html += "</tbody></table>"
    return table_html

def render_pace_calculator():
    """Render super simple pace calculator"""
    
    # Apply CSS
    st.markdown(get_simple_css(), unsafe_allow_html=True)

    # Sidebar version
    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)
    
    # Main container
    st.markdown('<div class="pace-container">', unsafe_allow_html=True)
    
    # Title
    st.markdown('<h1 class="pace-title">⏱️ Pace Calculator</h1>', unsafe_allow_html=True)
    
    # Distances
    distances = {"5K": 5.0, "10K": 10.0, "Half Marathon": 21.0975, "Marathon": 42.195}
    
    # ROW 1: Enter pace → Show times
    st.markdown("""
    <div class="pace-row">
        <div class="row-title">🏃‍♂️ Enter Pace → Get Times</div>
    </div>
    """, unsafe_allow_html=True)

    pace_input = st.text_input("Enter pace per km (MM:SS)", placeholder="5:00", key="pace_input")
        
    if pace_input:
        pace_td = parse_pace_input(pace_input)
        if pace_td:
            st.markdown('<div class="result-grid">', unsafe_allow_html=True)
            for dist_name, dist_km in distances.items():
                time_td = calculate_time_from_pace(pace_td, dist_km)
                time_str = format_time(time_td)
                st.markdown(f"""
                <div class="result-box">
                    <div class="result-label">{dist_name}</div>
                    <div class="result-value">{time_str}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Please enter pace in MM:SS format (e.g., 5:00)")
    
    # ROW 2: Enter times → Calculate pace
    st.markdown("""
    <div class="pace-row">
        <div class="row-title">⏰ Enter Times → Get Pace</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        time_5k = st.text_input("5K Time", placeholder="25:00", key="time_5k")
    with col2:
        time_10k = st.text_input("10K Time", placeholder="52:00", key="time_10k")
    with col3:
        time_half = st.text_input("Half Time", placeholder="1:50:00", key="time_half")
    with col4:
        time_marathon = st.text_input("Marathon Time", placeholder="3:45:00", key="time_marathon")
    
    # Calculate paces
    times_and_distances = [
        (time_5k, 5.0, "5K"),
        (time_10k, 10.0, "10K"), 
        (time_half, 21.0975, "Half Marathon"),
        (time_marathon, 42.195, "Marathon")
    ]
    
    calculated_paces = []
    for time_str, dist_km, dist_name in times_and_distances:
        if time_str:
            time_td = parse_time_input(time_str)
            if time_td:
                pace_td = calculate_pace_from_time(time_td, dist_km)
                pace_str = format_pace(pace_td)
                calculated_paces.append((dist_name, pace_str))
    
    if calculated_paces:
        st.markdown('<div class="result-grid">', unsafe_allow_html=True)
        for dist_name, pace_str in calculated_paces:
            st.markdown(f"""
            <div class="result-box">
                <div class="result-label">{dist_name} Pace</div>
                <div class="result-value">{pace_str}/km</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Optional: Add static table with expander
    with st.expander("📊 Pace Reference Table", expanded=False):
        st.markdown(create_static_pace_table(), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close container 