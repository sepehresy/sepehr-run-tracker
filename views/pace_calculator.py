import streamlit as st
import re
from datetime import timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE

def parse_time_input(time_str):
    """Parse time input in various formats (HH:MM:SS, MM:SS, minutes, etc.)"""
    if not time_str:
        return None
    
    time_str = time_str.strip()
    
    # Try to match HH:MM:SS format
    match = re.match(r'^(\d{1,2}):(\d{2}):(\d{2})$', time_str)
    if match:
        hours, minutes, seconds = map(int, match.groups())
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    # Try to match MM:SS format
    match = re.match(r'^(\d{1,3}):(\d{2})$', time_str)
    if match:
        minutes, seconds = map(int, match.groups())
        return timedelta(minutes=minutes, seconds=seconds)
    
    # Try to match just minutes (as float)
    try:
        total_minutes = float(time_str)
        minutes = int(total_minutes)
        seconds = int((total_minutes - minutes) * 60)
        return timedelta(minutes=minutes, seconds=seconds)
    except ValueError:
        pass
    
    return None

def parse_pace_input(pace_str):
    """Parse pace input in MM:SS format per km"""
    if not pace_str:
        return None
    
    pace_str = pace_str.strip()
    
    # Try to match MM:SS format
    match = re.match(r'^(\d{1,2}):(\d{2})$', pace_str)
    if match:
        minutes, seconds = map(int, match.groups())
        return timedelta(minutes=minutes, seconds=seconds)
    
    return None

def timedelta_to_pace_string(td):
    """Convert timedelta to pace string (MM:SS)"""
    if not td:
        return ""
    total_seconds = int(td.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def timedelta_to_time_string(td):
    """Convert timedelta to time string (HH:MM:SS or MM:SS)"""
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

def pace_to_mile_pace(km_pace_td):
    """Convert km pace to mile pace"""
    if not km_pace_td:
        return None
    # 1 mile = 1.609344 km
    mile_pace_seconds = km_pace_td.total_seconds() * 1.609344
    return timedelta(seconds=mile_pace_seconds)

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

def update_pace_input():
    """Callback function for pace input changes"""
    pass

def update_time_input():
    """Callback function for time input changes"""
    pass

def render_pace_calculator():
    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">⏱️</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">Pace Calculator</span>', unsafe_allow_html=True)
    st.markdown("Convert between pace and finish times for various race distances. **Press Enter or Tab after typing** to see results!")

    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)

    # Define race distances
    distances = {
        "5K": 5.0,
        "10K": 10.0,
        "Half Marathon": 21.0975,
        "Marathon": 42.195
    }
    
    # Add some custom CSS for better styling
    st.markdown("""
    <style>
    .pace-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    .pace-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
    }
    .pace-card h3 {
        margin: 0 0 10px 0;
        font-size: 1.2rem;
        font-weight: 600;
    }
    .pace-display {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 5px 0;
    }
    .time-display {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 5px 0;
    }
    .converter-section {
        background: rgba(0, 0, 0, 0.02);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    .stTextInput input {
        font-family: 'Courier New', monospace !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        text-align: center !important;
    }
    .result-card {
        background: rgba(76, 175, 80, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0;
        border-left: 4px solid #4CAF50;
        transition: all 0.2s ease;
    }
    .result-card:hover {
        background: rgba(76, 175, 80, 0.15);
    }
    .warning-card {
        background: rgba(255, 193, 7, 0.1);
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 4px solid #FFC107;
    }
    .info-card {
        background: rgba(33, 150, 243, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Quick example section
    st.markdown("""
    <div class="info-card">
        <strong>💡 Quick Start:</strong> Try entering "5:00" in pace or "25:00" in 5K time to see how it works!
    </div>
    """, unsafe_allow_html=True)

    # Create two main sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="converter-section">', unsafe_allow_html=True)
        st.markdown("### 🏃‍♂️ Pace → Time Converter")
        st.markdown("Enter your target pace to see predicted finish times")
        
        pace_input = st.text_input(
            "Target Pace (per km)",
            placeholder="5:30",
            help="Format: MM:SS (e.g., 5:30 for 5 minutes 30 seconds per km)",
            key="pace_input_field",
            on_change=update_pace_input
        )
        
        # Parse the pace input
        pace_td = parse_pace_input(pace_input)
        
        if pace_td:
            # Show mile pace
            mile_pace_td = pace_to_mile_pace(pace_td)
            mile_pace_str = timedelta_to_pace_string(mile_pace_td)
            
            st.markdown(f"""
            <div class="result-card">
                <strong>📏 Equivalent pace per mile:</strong> {mile_pace_str}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**🏁 Predicted Finish Times:**")
            
            # Calculate and display times for each distance
            for distance_name, distance_km in distances.items():
                finish_time_td = calculate_time_from_pace(pace_td, distance_km)
                finish_time_str = timedelta_to_time_string(finish_time_td)
                
                st.markdown(f"""
                <div class="pace-card">
                    <h3>{distance_name} ({distance_km}km)</h3>
                    <div class="time-display">🏁 {finish_time_str}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            if pace_input:
                st.markdown("""
                <div class="warning-card">
                    <strong>⚠️ Invalid format</strong><br>
                    Please enter pace in MM:SS format (e.g., 5:30)
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="info-card">
                    💡 Enter a pace above to see finish time predictions<br>
                    <small>Example: 5:30 (5 minutes 30 seconds per km)</small>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="converter-section">', unsafe_allow_html=True)
        st.markdown("### ⏰ Time → Pace Converter")
        st.markdown("Enter your target finish times to see required pace")
        
        for distance_name, distance_km in distances.items():
            time_input = st.text_input(
                f"🎯 {distance_name} Target Time",
                placeholder="25:00" if distance_km <= 10 else "1:45:00",
                help=f"Format: MM:SS or HH:MM:SS (e.g., {'25:00' if distance_km <= 10 else '1:45:00'})",
                key=f"time_input_{distance_name}",
                on_change=update_time_input
            )
            
            # Parse and calculate pace
            time_td = parse_time_input(time_input)
            
            if time_td:
                pace_td = calculate_pace_from_time(time_td, distance_km)
                pace_str = timedelta_to_pace_string(pace_td)
                mile_pace_td = pace_to_mile_pace(pace_td)
                mile_pace_str = timedelta_to_pace_string(mile_pace_td)
                
                st.markdown(f"""
                <div class="result-card">
                    <strong>Required pace for {distance_name}:</strong><br>
                    🏃‍♂️ <strong>{pace_str}/km</strong><br>
                    🇺🇸 <strong>{mile_pace_str}/mile</strong>
                </div>
                """, unsafe_allow_html=True)
            elif time_input:
                st.markdown(f"""
                <div class="warning-card">
                    <small>⚠️ Please enter time in MM:SS or HH:MM:SS format</small>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional information section
    st.markdown("---")
    st.markdown("### 📚 Usage Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🏃‍♂️ Pace → Time:**
        - Enter pace per kilometer (e.g., **5:30**)
        - See finish times for all distances
        - Mile pace shown for reference
        
        **⚡ Pro Tip:** Use common paces like 4:00, 5:00, 6:00 for round numbers
        """)
    
    with col2:
        st.markdown("""
        **⏰ Time → Pace:**
        - Enter target times for any distance
        - See required pace per km and mile
        - Try: 20:00 (5K), 45:00 (10K), 1:30:00 (HM)
        
        **⚡ Pro Tip:** Press **Tab** instead of **Enter** for faster input
        """)
    
    st.markdown("""
    ---
    **🎯 Quick Examples to Try:**
    - **Pace 4:00** → See sub-20 5K, sub-42 10K times
    - **5K time 22:30** → See what pace that requires  
    - **Marathon 3:30:00** → See the 4:58/km pace needed
    """) 