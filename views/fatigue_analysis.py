import streamlit as st
import pandas as pd
import altair as alt
from datetime import timedelta
import sys
import os
import json
from openai import OpenAI
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE
from utils.gist_helpers import load_gist_data, save_gist_data

# Initialize OpenAI client
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    client = None

# Function to load saved fatigue analyses from user's gist
def load_saved_fatigue_analyses(user_info, gist_id, filename, token):
    data = load_gist_data(gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    
    # Ensure user data structure exists
    if user_key not in data:
        data[user_key] = {}
    
    # Ensure fatigue_analyses key exists
    if "fatigue_analyses" not in data[user_key]:
        data[user_key]["fatigue_analyses"] = {}
    
    # Get the analyses
    analyses = data[user_key].get("fatigue_analyses", {})
    
    # Convert old format to new format if needed
    updated = False
    for key, analysis in analyses.items():
        if isinstance(analysis, str):
            # Old format - convert to new format
            analyses[key] = {
                'date': 'Unknown Date',
                'summary': analysis,
                'analysis_key': key
            }
            updated = True
    
    # Save the updated structure if we made changes
    if updated:
        try:
            save_gist_data(gist_id, filename, token, data)
        except Exception:
            pass  # Silently fail if we can't update the structure
        
    return analyses

# Function to delete fatigue analysis from Gist
def delete_fatigue_analysis(key, user_info, gist_id, filename, token):
    try:
        data = load_gist_data(gist_id, filename, token)
        user_key = user_info["USER_KEY"]
        if user_key in data and "fatigue_analyses" in data[user_key]:
            data[user_key]["fatigue_analyses"].pop(key, None)
            save_gist_data(gist_id, filename, token, data)
        return True
    except Exception as e:
        st.error(f"Error deleting fatigue analysis: {e}")
        return False

# Function to save fatigue analyses to user's gist with date
def save_fatigue_analysis(key, content, user_info, gist_id, filename, token):
    try:
        from datetime import datetime
        # Get the current data
        data = load_gist_data(gist_id, filename, token)
        user_key = user_info["USER_KEY"]
        
        # Ensure user data structure exists
        if user_key not in data:
            data[user_key] = {}
            
        # Ensure fatigue_analyses key exists
        if "fatigue_analyses" not in data[user_key]:
            data[user_key]["fatigue_analyses"] = {}
            
        # Create analysis entry with metadata
        analysis_entry = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'summary': content,
            'analysis_key': key
        }
        
        # Update the fatigue analysis
        data[user_key]["fatigue_analyses"][key] = analysis_entry
        
        # Save the updated data
        success = save_gist_data(gist_id, filename, token, data)
        return success
    except Exception as e:
        st.error(f"Error saving fatigue analysis: {e}")
        return False

def calculate_personal_if(df, weeks_back=4):
    """
    Calculate the user's personal average intensity factor from recent training data.
    
    Args:
        df: DataFrame with Date, Distance, TSS columns
        weeks_back: Number of weeks to look back for calculation
        
    Returns:
        float: Average intensity factor, or 0.80 if insufficient data
    """
    if df.empty or 'TSS' not in df.columns:
        return 0.80  # Default fallback
    
    # Get recent data
    cutoff_date = df['Date'].max() - timedelta(days=weeks_back * 7)
    recent_df = df[df['Date'] >= cutoff_date].copy()
    
    # Filter out rest days and very low TSS days
    recent_df = recent_df[(recent_df['TSS'] > 5) & (recent_df.get('Distance (km)', 0) > 1)]
    
    if len(recent_df) < 3:  # Need at least 3 data points
        return 0.80
    
    intensity_factors = []
    base_factor = 6  # Same as used in estimation
    
    for _, row in recent_df.iterrows():
        tss = row['TSS']
        distance = row.get('Distance (km)', 0)
        
        if distance > 0 and tss > 0:
            # Reverse engineer IF from actual data: IF = sqrt(TSS / (distance * base_factor))
            calculated_if = (tss / (distance * base_factor)) ** 0.5
            
            # Only include reasonable IF values (0.5 to 1.2)
            if 0.5 <= calculated_if <= 1.2:
                intensity_factors.append(calculated_if)
    
    if len(intensity_factors) >= 3:
        avg_if = sum(intensity_factors) / len(intensity_factors)
        return min(max(avg_if, 0.65), 1.05)  # Clamp between reasonable bounds
    else:
        return 0.80  # Default fallback

def estimate_tss_from_workout(distance, description):
    """
    Estimate TSS from workout distance and description using intensity factors.
    
    TSS = Duration (hours) × Intensity Factor² × 100
    
    For running without duration, we estimate based on typical paces:
    TSS ≈ Distance (km) × Intensity Factor² × 6 (assuming ~6 min/km base pace)
    """
    if distance <= 0:
        return 0
    
    description_lower = description.lower()
    
    # Determine intensity factor based on workout description
    if any(keyword in description_lower for keyword in ['rest', 'off', 'recovery', 'easy recovery']):
        intensity_factor = 0.0  # Rest day
    elif any(keyword in description_lower for keyword in ['recovery run', 'very easy', 'zone 1']):
        intensity_factor = 0.65  # Very easy recovery
    elif any(keyword in description_lower for keyword in ['easy', 'zone 2', 'conversational', 'aerobic']):
        intensity_factor = 0.75  # Easy/aerobic pace
    elif any(keyword in description_lower for keyword in ['long run', 'long', 'endurance']):
        # Long runs are typically easy but longer duration adds stress
        intensity_factor = 0.78  # Slightly higher than easy due to duration
    elif any(keyword in description_lower for keyword in ['tempo', 'threshold', 'comfortably hard', 'zone 4']):
        intensity_factor = 0.90  # Tempo/threshold pace
    elif any(keyword in description_lower for keyword in ['interval', 'repeat', 'vo2', 'zone 5', '5k pace', '10k pace']):
        intensity_factor = 1.05  # VO2 max intervals
    elif any(keyword in description_lower for keyword in ['fartlek', 'progression', 'build', 'moderate']):
        intensity_factor = 0.85  # Mixed intensity
    elif any(keyword in description_lower for keyword in ['race', 'time trial', 'test']):
        intensity_factor = 1.0  # Race effort
    elif any(keyword in description_lower for keyword in ['hill', 'climb', 'uphill']):
        intensity_factor = 0.95  # Hill work is intense
    elif any(keyword in description_lower for keyword in ['strides', 'pickup', 'surge']):
        intensity_factor = 0.80  # Easy run with strides
    else:
        # Default to moderate effort if we can't determine intensity
        intensity_factor = 0.80
    
    # Estimate TSS using: Distance × IF² × Base factor
    # Base factor assumes ~6 min/km average pace → 0.1 hours per km
    base_factor = 6  # Represents: 0.1 hours × 100 × 0.6 (time adjustment)
    estimated_tss = distance * (intensity_factor ** 2) * base_factor
    
    return max(0, estimated_tss)

def calculate_tss(duration_hrs, intensity_factor):
    return duration_hrs * (intensity_factor ** 2) * 100

def calculate_tss_from_hr(row, lthr):
    # Calculate Intensity Factor (IF) from Avg HR and LTHR
    try:
        avg_hr = float(row.get("Avg HR", 0))
        elapsed_min = float(row.get("Elapsed Time (min)", 0))
        if lthr and avg_hr > 0 and elapsed_min > 0:
            IF = avg_hr / lthr
            duration_hr = elapsed_min / 60.0
            tss = duration_hr * (IF ** 2) * 100
            return tss
        else:
            return 0.0
    except Exception:
        return 0.0

def calculate_atl_ctl_tsb(df, atl_days=7, ctl_days=42):
    # Assumes df has columns: Date, TSS
    df = df.sort_values("Date").copy()
    df["ATL"] = df["TSS"].ewm(span=atl_days, adjust=False).mean()
    df["CTL"] = df["TSS"].ewm(span=ctl_days, adjust=False).mean()
    df["TSB"] = df["CTL"] - df["ATL"]
    return df

def generate_fatigue_prompt(df, runner_profile, fatigue_metrics, selected_range, today):
    """
    Generate a prompt for the AI to analyze fatigue metrics and provide training recommendations.
    
    Parameters:
    - df: DataFrame containing activity data
    - runner_profile: Dict of runner profile information
    - fatigue_metrics: Dict of current fatigue metrics (ATL, CTL, TSB)
    - selected_range: String indicating the time range being analyzed
    - today: Current date
    
    Returns:
    - String containing the formatted prompt for OpenAI
    """
    # Get the last 10 activities for context
    recent_activities = df.sort_values("Date", ascending=False).head(10).sort_values("Date")
    
    # Format recent activities
    activities_str = ""
    for _, row in recent_activities.iterrows():
        date_str = row['Date'].strftime('%Y-%m-%d')
        name = row.get('Name', 'Unknown')
        distance = row.get('Distance (km)', '-')
        tss = row.get('TSS', '-')
        activities_str += f"Date: {date_str}, Name: {name}, Distance: {distance}km, TSS: {tss}\n"
    
    # Format runner experience info
    experience_level = runner_profile.get('experience', 'Unknown')
    running_years = runner_profile.get('years_running', 'Unknown')
    avg_weekly_km = runner_profile.get('avg_weekly_km', 'Unknown')
    
    # Format PRs
    pr_5k = runner_profile.get('pr_5k', '-')
    pr_10k = runner_profile.get('pr_10k', '-')
    pr_half = runner_profile.get('pr_half', '-')
    pr_full = runner_profile.get('pr_marathon', '-')
    
    # Format heart rate data
    resting_hr = runner_profile.get('resting_hr', '-')
    max_hr = runner_profile.get('max_hr', '-')
    lthr = runner_profile.get('LTHR', '-')
    
    # Format current fatigue metrics
    current_atl = fatigue_metrics.get('ATL', '-')
    current_ctl = fatigue_metrics.get('CTL', '-')
    current_tsb = fatigue_metrics.get('TSB', '-')
    
    # Check for injuries
    injuries = runner_profile.get('injuries', 'None reported')
    
    # Create the prompt
    prompt = f"""
As an expert running coach, analyze this runner's fatigue metrics and provide tailored advice.

RUNNER PROFILE:
- Experience: {experience_level} runner with {running_years} years of running
- Average weekly volume: {avg_weekly_km} km
- Personal Records: 5K: {pr_5k}, 10K: {pr_10k}, Half: {pr_half}, Marathon: {pr_full}
- Heart Rate Data: Resting: {resting_hr}, Max: {max_hr}, LTHR: {lthr}
- Injuries/Limitations: {injuries}

CURRENT FATIGUE METRICS ({today.strftime('%Y-%m-%d')}):
- CTL (Fitness): {current_ctl:.1f}
- ATL (Fatigue): {current_atl:.1f}
- TSB (Form): {current_tsb:.1f}
- Time Range Analyzed: {selected_range}

RECENT ACTIVITIES (LAST 10):
{activities_str}

QUESTIONS TO ANSWER:
1. What do the current CTL, ATL, and TSB values indicate about this runner's training status?
2. Is there evidence of overtraining or undertraining?
3. What's the ideal training approach for the next 7-14 days based on these metrics?
4. When would be an optimal time for a race or peak performance based on these trends?
5. Are there any warning signs or areas of concern in the data?

Please provide specific, actionable recommendations tailored to this runner's experience level and current fatigue state.
"""
    return prompt

def render_fatigue_analysis(df, today, user_info, gist_id, gist_filename, github_token):
    # Modern page header with minimalistic design
    st.markdown("""
    <style>
    /* Modern, minimalistic styling for fatigue analysis */
    .fatigue-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .fatigue-header-icon {
        font-size: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .fatigue-header-text {
        font-size: 1.75rem;
        font-weight: 600;
        color: white;
        margin: 0;
    }
    
    /* Responsive grid for controls */
    .control-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 1.5rem 0;
    }
    
    /* Modern input styling */
    .stNumberInput input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: white !important;
        font-size: 14px !important;
        padding: 12px !important;
    }
    
    .stNumberInput input:focus {
        border-color: rgba(102, 126, 234, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Radio button styling */
    .fatigue-controls .stRadio > div {
        gap: 0.5rem !important;
    }
    
    .fatigue-controls .stRadio label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        margin: 2px !important;
        transition: all 0.2s ease !important;
    }
    
    .fatigue-controls .stRadio label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Modern metric cards */
    .metric-cards-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.75rem;
        margin: 1.5rem 0;
    }
    
    .metric-card-modern {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-modern:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: rgba(255, 255, 255, 0.12);
    }
    
    .metric-icon {
        font-size: 1.2rem;
        margin-bottom: 0.25rem;
        display: block;
    }
    
    .metric-label {
        font-size: 0.7rem;
        opacity: 0.7;
        margin-bottom: 0.25rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    
    .metric-trend {
        font-size: 0.6rem;
        opacity: 0.8;
        margin-top: 0.25rem;
        font-weight: 500;
    }
    
    /* TSB Meter Styles */
    .tsb-meter-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        text-align: center;
    }
    
    .tsb-meter-title {
        font-size: 0.9rem;
        opacity: 0.8;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    
    .tsb-gauge {
        position: relative;
        width: 200px;
        height: 100px;
        margin: 0 auto 1rem;
    }
    
    .tsb-gauge-bg {
        width: 200px;
        height: 100px;
        border-radius: 100px 100px 0 0;
        background: linear-gradient(90deg, 
            #dc3545 0%, 
            #fd7e14 25%, 
            #28a745 50%, 
            #007bff 75%, 
            #ffc107 100%);
        position: relative;
        overflow: hidden;
    }
    
    .tsb-gauge-overlay {
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 160px;
        height: 80px;
        background: #0e1117;
        border-radius: 80px 80px 0 0;
    }
    
    .tsb-needle {
        position: absolute;
        bottom: 0;
        left: 50%;
        width: 2px;
        height: 70px;
        background: white;
        transform-origin: bottom center;
        transform: translateX(-50%);
        border-radius: 2px;
        box-shadow: 0 0 10px rgba(255,255,255,0.5);
    }
    
    .tsb-value-display {
        position: absolute;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 1.1rem;
        font-weight: 700;
        color: white;
    }
    
    .tsb-labels {
        display: flex;
        justify-content: space-between;
        width: 200px;
        margin: 0 auto;
        font-size: 0.7rem;
        opacity: 0.6;
    }
    
    .tsb-status {
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
    }
    
    .tsb-overreach { background: rgba(220, 53, 69, 0.2); color: #dc3545; }
    .tsb-fatigue { background: rgba(253, 126, 20, 0.2); color: #fd7e14; }
    .tsb-optimal { background: rgba(40, 167, 69, 0.2); color: #28a745; }
    .tsb-fresh { background: rgba(0, 123, 255, 0.2); color: #007bff; }
    .tsb-detraining { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
    
    .tsb-recommendation {
        font-size: 0.8rem;
        margin-top: 0.75rem;
        padding: 0.75rem;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        border-left: 3px solid #667eea;
        opacity: 0.9;
    }
    
    /* Status indicator */
    .status-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        margin: 1.5rem 0;
        backdrop-filter: blur(10px);
    }
    
    .status-optimal {
        background: rgba(40, 167, 69, 0.2);
        border: 1px solid rgba(40, 167, 69, 0.3);
        color: #28a745;
    }
    
    .status-warning {
        background: rgba(255, 193, 7, 0.2);
        border: 1px solid rgba(255, 193, 7, 0.3);
        color: #ffc107;
    }
    
    .status-danger {
        background: rgba(220, 53, 69, 0.2);
        border: 1px solid rgba(220, 53, 69, 0.3);
        color: #dc3545;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .fatigue-header-text {
            font-size: 1.5rem;
        }
        
        .metric-cards-container {
            grid-template-columns: 1fr;
            gap: 0.5rem;
        }
        
        .metric-card-modern {
            padding: 0.75rem;
            min-height: 100px;
        }
        
        .metric-value {
            font-size: 1.2rem;
        }
        
        .tsb-gauge {
            width: 150px;
            height: 75px;
        }
        
        .tsb-gauge-bg {
            width: 150px;
            height: 75px;
        }
        
        .tsb-gauge-overlay {
            width: 120px;
            height: 60px;
        }
        
        .tsb-needle {
            height: 50px;
        }
        
        .tsb-labels {
            width: 150px;
            font-size: 0.6rem;
        }
    }
    
    @media (max-width: 480px) {
        .metric-cards-container {
            grid-template-columns: repeat(3, 1fr);
            gap: 0.25rem;
        }
        
        .metric-card-modern {
            padding: 0.5rem;
            min-height: 90px;
        }
        
        .metric-value {
            font-size: 1rem;
        }
        
        .metric-icon {
            font-size: 1rem;
        }
        
        .metric-label {
            font-size: 0.6rem;
        }
    }
    
    /* Section spacing */
    .section-spacing {
        margin: 2.5rem 0;
    }
    
    /* Clean separator */
    .section-separator {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Clean header
    st.markdown("""
    <div class="fatigue-header">
        <span class="fatigue-header-icon">📊</span>
        <h1 class="fatigue-header-text">Fatigue Analysis</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Action Bar
    if not df.empty and 'TSB' in df.columns:
        latest = df.iloc[-1]
        tsb = latest['TSB']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📈 View Trends", use_container_width=True):
                st.session_state['show_trends'] = True
        with col2:
            if st.button("🎯 Race Readiness", use_container_width=True):
                st.session_state['show_race_readiness'] = True
        with col3:
            if st.button("📊 Export Data", use_container_width=True):
                st.session_state['show_export'] = True
        with col4:
            if st.button("💡 Quick Tips", use_container_width=True):
                st.session_state['show_tips'] = True

    # Get LTHR from runner profile or input
    runner_profile = st.session_state.get("user_info", {}).get("runner_profile", {})
    lthr = runner_profile.get("LTHR") or runner_profile.get("lthr")
    
    # Clean control section
    if not lthr:
        st.markdown("**⚙️ Configuration**")
        lthr = st.number_input(
            "Lactate Threshold HR (LTHR)", 
            min_value=100, 
            max_value=220, 
            value=160,
            help="Used for TSS calculation from heart rate data"
        )
        st.markdown('<div class="section-separator"></div>', unsafe_allow_html=True)

    # Simplified time range selector
    st.markdown("**📅 Time Range**")
    range_options = ["Last 4 Weeks", "Last 3 Months", "Last 6 Months", "Last Year", "Last 2 Years", "All Time"]
    range_days = {
        "Last 4 Weeks": 28, "Last 3 Months": 90, "Last 6 Months": 180,
        "Last Year": 365, "Last 2 Years": 730, "All Time": None
    }
    
    # Wrap radio button with fatigue-controls class
    st.markdown('<div class="fatigue-controls">', unsafe_allow_html=True)
    selected_range = st.radio("Time Range Selection", range_options, index=1, horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # Data preparation (unchanged logic)
    df = df.copy()
    
    if "TSS" not in df.columns:
        if "Avg HR" in df.columns and "Elapsed Time (min)" in df.columns:
            df["TSS"] = df.apply(lambda row: calculate_tss_from_hr(row, lthr), axis=1)
        elif "Duration (hrs)" in df.columns and "IF" in df.columns:
            df["TSS"] = calculate_tss(df["Duration (hrs)"], df["IF"])
        else:
            st.error("Your data must have a 'TSS' column, or columns for 'Avg HR' and 'Elapsed Time (min)', or both 'Duration (hrs)' and 'IF'.")
            st.stop()
    
    # st.info(f"🔍 Debug: Initial data shape: {df.shape}, columns: {list(df.columns)}")
    
    # st.info(f"📈 TSS Summary: Min={df['TSS'].min():.1f}, Max={df['TSS'].max():.1f}, Mean={df['TSS'].mean():.1f}")
    
    # Ensure we have valid TSS data
    if df.empty or df["TSS"].isna().all():
        st.warning("No valid TSS data found. Please check your activity data.")
        st.stop()
    
    df = calculate_atl_ctl_tsb(df)
    df = df.dropna(subset=["Date"]).sort_values("Date")
    
    # Verify fatigue metrics were calculated
    if 'CTL' not in df.columns or 'ATL' not in df.columns or 'TSB' not in df.columns:
        st.error("Failed to calculate fatigue metrics (CTL, ATL, TSB). Please check your TSS data.")
        st.stop()
    
    if range_days[selected_range]:
        min_date = today - timedelta(days=range_days[selected_range])
        df = df[df["Date"] >= min_date]
    
    # Final check that we still have data after filtering
    if df.empty:
        st.warning(f"No data available for the selected time range: {selected_range}")
        st.stop()
    
    # Simplified metric overlay (optional, collapsed by default)
    with st.expander("📈 Chart Options", expanded=False):
        metric_options = [
            ("None", None), ("Distance (km)", "#00bcd4"), ("Elapsed Time (min)", "#8bc34a"),
            ("Avg HR", "#ff9800"), ("Max HR", "#e91e63")
        ]
        metric_labels = [m[0] for m in metric_options]
        metric_colors = {m[0]: m[1] for m in metric_options if m[1]}
        selected_metric = st.selectbox("Overlay metric:", metric_labels, index=0)
        selected_metric = None if selected_metric == "None" else selected_metric
        
        # Future prediction toggle
        predict_future = st.checkbox("🔮 Predict future fatigue based on race plan", value=False, 
                                    help="Projects CTL, ATL, TSB into the future using your current race training plan")

    st.markdown('<div class="section-separator"></div>', unsafe_allow_html=True)

    # Future fatigue prediction logic
    df_extended = df.copy()
    future_data = None
    
    if predict_future:
        try:
            # Load race planning data
            from views.race_planning.data import load_training_plans
            training_plans = load_training_plans(user_info, gist_id, gist_filename, github_token)
            
            if training_plans:
                # Get the most recent/active training plan
                active_plan = None
                latest_race_date = None
                
                for race_id, plan in training_plans.items():
                    if 'weeks' in plan and plan['weeks']:
                        # Find the race with the latest start date
                        first_week = plan['weeks'][0]
                        raw_start_date = first_week.get('start_date', '')
                        
                        # Determine the date format for this plan
                        detected_format = None
                        start_date_ts = None
                        for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                            try:
                                start_date_ts = pd.to_datetime(raw_start_date, format=date_format, errors='raise')
                                detected_format = date_format
                                break
                            except Exception:
                                continue
                        
                        # If no format worked, try general parsing
                        if start_date_ts is None or pd.isna(start_date_ts):
                            try:
                                start_date_ts = pd.to_datetime(raw_start_date, errors='coerce')
                                if not pd.isna(start_date_ts):
                                    pass
                            except Exception:
                                pass
                        
                        # Skip if date is still invalid
                        if start_date_ts is None or pd.isna(start_date_ts):
                            continue
                        
                        start_date = start_date_ts.date()
                        if latest_race_date is None or start_date > latest_race_date:
                            latest_race_date = start_date
                            active_plan = plan
                            active_plan['_detected_format'] = detected_format  # Store the detected format
                
                if active_plan and 'weeks' in active_plan:
                    # Initialize variables early to avoid scope issues
                    last_date = df['Date'].max().date() if not df.empty else today
                    last_ctl = df['CTL'].iloc[-1] if not df.empty else 0
                    last_atl = df['ATL'].iloc[-1] if not df.empty else 0
                    
                    # Calculate user's personal average intensity factor from recent data
                    personal_if = calculate_personal_if(df, weeks_back=4)
                    
                    # Generate future fatigue data
                    future_data = []
                    weekly_breakdown = []  # For debugging
                    
                    # Validate training plan dates for sequential order
                    plan_dates = []
                    detected_format = active_plan.get('_detected_format')
                    
                    for week in active_plan['weeks']:
                        raw_week_date = week.get('start_date', '')
                        if raw_week_date:
                            # Use the detected format first, then try others as fallback
                            week_start_ts = None
                            
                            if detected_format:
                                try:
                                    week_start_ts = pd.to_datetime(raw_week_date, format=detected_format, errors='raise')
                                except Exception:
                                    pass
                            
                            # If detected format failed, try others
                            if week_start_ts is None or pd.isna(week_start_ts):
                                for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                                    if date_format == detected_format:
                                        continue  # Already tried
                                    try:
                                        week_start_ts = pd.to_datetime(raw_week_date, format=date_format, errors='raise')
                                        break
                                    except Exception:
                                        continue
                            
                            if week_start_ts and not pd.isna(week_start_ts):
                                plan_dates.append((week.get('week_number', '?'), week_start_ts.date(), raw_week_date))
                    
                    # Check for date inconsistencies
                    if len(plan_dates) > 1:
                        non_sequential = []
                        for i in range(1, len(plan_dates)):
                            prev_week, prev_date, prev_raw = plan_dates[i-1]
                            curr_week, curr_date, curr_raw = plan_dates[i]
                            expected_gap = 7  # Should be 7 days apart
                            actual_gap = (curr_date - prev_date).days
                            
                            if abs(actual_gap - expected_gap) > 3:  # Allow some tolerance
                                non_sequential.append(f"Week {prev_week} ({prev_raw}) → Week {curr_week} ({curr_raw}): {actual_gap} days gap")
                        
                        if non_sequential:
                            st.warning("⚠️ **Training Plan Date Issues Detected:**")
                            for issue in non_sequential[:5]:  # Show first 5 issues
                                st.warning(f"• {issue}")
                            if len(non_sequential) > 5:
                                st.warning(f"• ... and {len(non_sequential) - 5} more issues")
                            st.warning("📝 **Recommendation:** Check your race planning data for incorrect dates. The prediction may be inaccurate.")
                    
                    # First, fill any gap between last data and first training plan week
                    first_plan_date = None
                    for week in active_plan['weeks']:
                        raw_week_date = week.get('start_date', '')
                        
                        # Use the detected format first, then try others as fallback
                        week_start_ts = None
                        
                        if detected_format:
                            try:
                                week_start_ts = pd.to_datetime(raw_week_date, format=detected_format, errors='raise')
                            except Exception:
                                pass
                        
                        # If detected format failed, try others
                        if week_start_ts is None or pd.isna(week_start_ts):
                            for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                                if date_format == detected_format:
                                    continue  # Already tried
                                try:
                                    week_start_ts = pd.to_datetime(raw_week_date, format=date_format, errors='raise')
                                    break
                                except Exception:
                                    continue
                        
                        # If no format worked, try general parsing
                        if week_start_ts is None or pd.isna(week_start_ts):
                            try:
                                week_start_ts = pd.to_datetime(raw_week_date, errors='coerce')
                            except Exception:
                                pass
                        
                        # Skip if date is invalid
                        if week_start_ts is None or pd.isna(week_start_ts):
                            continue
                        
                        week_start = week_start_ts.date()
                        if week_start > last_date:
                            first_plan_date = week_start
                            break
                    
                    # Fill gap with low TSS rest days if there's a gap > 1 day
                    if first_plan_date and (first_plan_date - last_date).days > 1:
                        gap_days = (first_plan_date - last_date).days - 1
                        for i in range(1, gap_days):  # Start from day after last_date
                            gap_date = last_date + timedelta(days=i)
                            # Assume rest days in the gap
                            gap_tss = 0
                            
                            # Calculate projected CTL and ATL with rest days
                            alpha_ctl = 2 / (42 + 1)
                            alpha_atl = 2 / (7 + 1)
                            
                            new_ctl = last_ctl * (1 - alpha_ctl) + gap_tss * alpha_ctl
                            new_atl = last_atl * (1 - alpha_atl) + gap_tss * alpha_atl
                            new_tsb = new_ctl - new_atl
                            
                            future_data.append({
                                'Date': pd.Timestamp(gap_date),
                                'TSS': gap_tss,
                                'CTL': new_ctl,
                                'ATL': new_atl,
                                'TSB': new_tsb,
                                'is_prediction': True
                            })
                            
                            last_ctl = new_ctl
                            last_atl = new_atl
                    
                    # Project each week from the training plan
                    for week in active_plan['weeks']:
                        raw_week_date = week.get('start_date', '')
                        week_number = week.get('week_number', '?')
                        
                        # Use the detected format first, then try others as fallback
                        week_start_ts = None
                        
                        if detected_format:
                            try:
                                week_start_ts = pd.to_datetime(raw_week_date, format=detected_format, errors='raise')
                            except Exception:
                                pass
                        
                        # If detected format failed, try others
                        if week_start_ts is None or pd.isna(week_start_ts):
                            for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                                if date_format == detected_format:
                                    continue  # Already tried
                                try:
                                    week_start_ts = pd.to_datetime(raw_week_date, format=date_format, errors='raise')
                                    break
                                except Exception:
                                    continue
                        
                        # If no format worked, try general parsing
                        if week_start_ts is None or pd.isna(week_start_ts):
                            try:
                                week_start_ts = pd.to_datetime(raw_week_date, errors='coerce')
                            except Exception:
                                pass
                        
                        # Skip if date is invalid
                        if week_start_ts is None or pd.isna(week_start_ts):
                            continue
                        
                        week_start = week_start_ts.date()
                        week_end_date = week_start + timedelta(days=6)
                        
                        # Include this week if it contains any future days
                        if week_end_date > last_date:
                            # Calculate weekly TSS from planned training using personal IF
                            weekly_tss = 0
                            week_details = []
                            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                            
                            for day_idx, day in enumerate(days):
                                current_day_date = week_start + timedelta(days=day_idx)
                                
                                # Only include days that are in the future
                                if current_day_date > last_date:
                                    day_plan = week.get(day, {})
                                    distance = float(day_plan.get('distance', 0))
                                    description = day_plan.get('description', '')
                                    
                                    # Use personal IF for all non-rest workouts
                                    if distance > 0:
                                        # Still check for rest days
                                        if any(keyword in description.lower() for keyword in ['rest', 'off']):
                                            estimated_tss = 0
                                        else:
                                            # Use personal IF for all actual workouts
                                            base_factor = 6
                                            estimated_tss = distance * (personal_if ** 2) * base_factor
                                        
                                        weekly_tss += estimated_tss
                                        week_details.append(f"{day.title()}: {distance}km ({description[:20]}...) = {estimated_tss:.0f} TSS")
                            
                            # Only add week to breakdown if it has future training
                            if weekly_tss > 0 or week_details:
                                weekly_breakdown.append({
                                    'week': f"Week {week_number}",
                                    'start_date': week_start.strftime('%b %d'),
                                    'total_tss': weekly_tss,
                                    'details': week_details
                                })
                            
                            # Create daily projections for future days in this week
                            for day_idx, day in enumerate(days):
                                current_day_date = week_start + timedelta(days=day_idx)
                                
                                # Only create predictions for future days
                                if current_day_date > last_date:
                                    day_plan = week.get(day, {})
                                    distance = float(day_plan.get('distance', 0))
                                    description = day_plan.get('description', '')
                                    
                                    # Calculate daily TSS
                                    if distance > 0:
                                        if any(keyword in description.lower() for keyword in ['rest', 'off']):
                                            daily_tss = 0
                                        else:
                                            base_factor = 6
                                            daily_tss = distance * (personal_if ** 2) * base_factor
                                    else:
                                        daily_tss = 0
                                    
                                    # Calculate projected CTL and ATL
                                    alpha_ctl = 2 / (42 + 1)
                                    alpha_atl = 2 / (7 + 1)
                                    
                                    new_ctl = last_ctl * (1 - alpha_ctl) + daily_tss * alpha_ctl
                                    new_atl = last_atl * (1 - alpha_atl) + daily_tss * alpha_atl
                                    new_tsb = new_ctl - new_atl
                                    
                                    future_data.append({
                                        'Date': pd.Timestamp(current_day_date),
                                        'TSS': daily_tss,
                                        'CTL': new_ctl,
                                        'ATL': new_atl,
                                        'TSB': new_tsb,
                                        'is_prediction': True,
                                        'Distance (km)': distance,  # Add planned distance for overlay
                                        'Planned_Distance': distance  # Alternative column name
                                    })
                                    
                                    last_ctl = new_ctl
                                    last_atl = new_atl
                        
                        else:
                            pass
                    
                    if future_data:
                        # Combine historical and future data
                        df_historical = df.copy()
                        df_historical['is_prediction'] = False
                        
                        df_future = pd.DataFrame(future_data)
                        df_extended = pd.concat([df_historical, df_future], ignore_index=True)
                        df_extended = df_extended.sort_values('Date').reset_index(drop=True)
                        
                        st.success(f"🔮 Showing prediction for {len(future_data)} future days based on your training plan")
                        
                        # Show gap information if applicable
                        if first_plan_date and (first_plan_date - last_date).days > 1:
                            gap_days = (first_plan_date - last_date).days - 1
                            st.info(f"📅 Filled {gap_days} gap days between last data ({last_date.strftime('%b %d')}) and training plan start ({first_plan_date.strftime('%b %d')}) with rest days")
                        
                        # Show TSS prediction breakdown
                        with st.expander("🔍 TSS Prediction Breakdown", expanded=False):
                            # Show personal IF calculation
                            recent_activities = df[df['Date'] >= (df['Date'].max() - timedelta(days=28))]
                            recent_activities = recent_activities[(recent_activities['TSS'] > 5) & (recent_activities.get('Distance (km)', 0) > 1)]
                            
                            st.markdown(f"**📊 Your Personal Training Profile:**")
                            st.markdown(f"- **Personal Intensity Factor:** {personal_if:.3f}")
                            st.markdown(f"- **Based on:** {len(recent_activities)} activities from last 4 weeks")
                            if not recent_activities.empty:
                                avg_tss_per_km = (recent_activities['TSS'] / recent_activities.get('Distance (km)', 1)).mean()
                                st.markdown(f"- **Your average:** {avg_tss_per_km:.1f} TSS per km")
                            st.markdown("")
                            
                            st.markdown("**Weekly TSS Estimates:**")
                            for week_info in weekly_breakdown[:4]:  # Show first 4 weeks
                                st.markdown(f"**{week_info['week']} ({week_info['start_date']})** - Total: {week_info['total_tss']:.0f} TSS")
                                for detail in week_info['details']:
                                    st.markdown(f"  • {detail}")
                                st.markdown("")
                            
                            if len(weekly_breakdown) > 4:
                                st.markdown(f"... and {len(weekly_breakdown) - 4} more weeks")
                            
                            st.markdown("**📈 Prediction Method:**")
                            st.markdown(f"""
                            - Uses your personal IF ({personal_if:.3f}) calculated from recent training
                            - Formula: TSS = Distance × (Personal IF)² × 6
                            - Rest days automatically detected and set to 0 TSS
                            - More accurate than generic intensity factors
                            """)
                    else:
                        st.warning("⚠️ Debug: No future data generated - this could mean:")
                        st.warning("• All training plan weeks are in the past")
                        st.warning("• No training plan weeks have valid dates")
                        st.warning("• Training plan structure is not as expected")
                        
                        # Show some sample weeks for debugging
                        if active_plan and 'weeks' in active_plan:
                            st.write("📝 Sample week structure:")
                            for i, week in enumerate(active_plan['weeks'][:2]):  # Show first 2 weeks
                                st.write(f"Week {i+1}: {week}")
                else:
                    st.warning("⚠️ Debug: No active training plan found or no weeks in plan")
            else:
                st.warning("⚠️ Debug: No training plans found in race planning data")
        
        except Exception as e:
            st.warning(f"Could not load race plan for prediction: {str(e)}")
            predict_future = False

    # Use extended dataframe for charting
    chart_df = df_extended

    # Simplified chart
    if selected_range == "Last 4 Weeks":
        x_axis = alt.Axis(title="Date", format="%b %d", labelAngle=-30, labelOverlap=True, tickCount="day")
    elif selected_range in ["Last 3 Months", "Last 6 Months"]:
        x_axis = alt.Axis(title="Date", format="%b %d", labelAngle=-45, labelOverlap=True, tickCount="week")
    elif selected_range in ["Last Year", "Last 2 Years"]:
        x_axis = alt.Axis(title="Date", format="%b %Y", labelAngle=-45, labelOverlap=True, tickCount="month")
    else:
        x_axis = alt.Axis(title="Date", format="%Y", labelAngle=0, labelOverlap=True, tickCount="year")

    base = alt.Chart(chart_df).encode(x=alt.X("Date:T", axis=x_axis))
    
    # Main fatigue metrics as lines
    if predict_future and future_data:
        # Historical data (solid lines)
        base_historical = alt.Chart(chart_df[chart_df['is_prediction'] == False]).encode(x=alt.X("Date:T", axis=x_axis))
        ctl_line_hist = base_historical.mark_line(color="#667eea", strokeWidth=3, strokeCap="round").encode(
            y=alt.Y("CTL:Q", title="Training Load Score"), 
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        atl_line_hist = base_historical.mark_line(color="#ff6b6b", strokeWidth=3, strokeCap="round").encode(
            y=alt.Y("ATL:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        tsb_line_hist = base_historical.mark_line(color="#feca57", strokeWidth=3, strokeCap="round").encode(
            y=alt.Y("TSB:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        
        # Predicted data (dashed lines with lower opacity)
        base_future = alt.Chart(chart_df[chart_df['is_prediction'] == True]).encode(x=alt.X("Date:T", axis=x_axis))
        ctl_line_pred = base_future.mark_line(color="#667eea", strokeWidth=2, strokeDash=[8,4], opacity=0.7).encode(
            y=alt.Y("CTL:Q"), 
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q"]
        )
        atl_line_pred = base_future.mark_line(color="#ff6b6b", strokeWidth=2, strokeDash=[8,4], opacity=0.7).encode(
            y=alt.Y("ATL:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q"]
        )
        tsb_line_pred = base_future.mark_line(color="#feca57", strokeDash=[12,8], strokeWidth=1.5, opacity=0.7).encode(
            y=alt.Y("TSB:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q"]
        )
        
        # Combine historical and predicted lines
        chart = ctl_line_hist + atl_line_hist + tsb_line_hist + ctl_line_pred + atl_line_pred + tsb_line_pred
    else:
        # Standard lines for historical data only
        ctl_line = base.mark_line(color="#667eea", strokeWidth=3, strokeCap="round").encode(
            y=alt.Y("CTL:Q", title="Training Load Score"), 
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        atl_line = base.mark_line(color="#ff6b6b", strokeWidth=3, strokeCap="round").encode(
            y=alt.Y("ATL:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        tsb_line = base.mark_line(color="#feca57", strokeWidth=3, strokeCap="round").encode(
            y=alt.Y("TSB:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        
        # Combine main lines
        chart = ctl_line + atl_line + tsb_line

    # Add overlay metric as columns/bars if selected
    if selected_metric and selected_metric in df.columns:
        color = metric_colors.get(selected_metric, "#888")
        
        if predict_future and future_data and selected_metric in ['Distance (km)', 'Planned_Distance']:
            # Show both historical and predicted data for distance
            historical_df = chart_df[chart_df['is_prediction'] == False]
            predicted_df = chart_df[chart_df['is_prediction'] == True]
            
            base_overlay = alt.Chart(chart_df).encode(x=alt.X("Date:T", axis=x_axis))
            
            # Historical bars (solid)
            if not historical_df.empty:
                historical_bars = alt.Chart(historical_df).encode(x=alt.X("Date:T", axis=x_axis)).mark_bar(
                    color=color, 
                    opacity=0.7,
                    size=20
                ).encode(
                    y=alt.Y(f"{selected_metric}:Q", 
                           axis=alt.Axis(title=f"{selected_metric} (Actual/Planned)", titleColor=color, labelColor=color),
                           scale=alt.Scale(domain=[0, chart_df[selected_metric].max() * 1.1]) if not chart_df.empty else alt.Scale(domain=[0, 100])),
                    tooltip=["Date:T", f"{selected_metric}:Q"]
                )
            else:
                historical_bars = alt.Chart()
            
            # Predicted bars (hatched pattern simulation with lower opacity)
            if not predicted_df.empty and selected_metric in predicted_df.columns:
                predicted_bars = alt.Chart(predicted_df).encode(x=alt.X("Date:T", axis=x_axis)).mark_bar(
                    color=color,
                    opacity=0.4,  # Lower opacity for predicted
                    size=20,
                    stroke=color,
                    strokeWidth=1
                ).encode(
                    y=alt.Y(f"{selected_metric}:Q", 
                           axis=alt.Axis(title=f"{selected_metric} (Actual/Planned)", titleColor=color, labelColor=color),
                           scale=alt.Scale(domain=[0, chart_df[selected_metric].max() * 1.1]) if not chart_df.empty else alt.Scale(domain=[0, 100])),
                    tooltip=["Date:T", f"{selected_metric}:Q"]
                )
            else:
                predicted_bars = alt.Chart()
            
            # Combine historical and predicted bars
            overlay_bars = historical_bars + predicted_bars
            
        else:
            # Standard overlay for non-distance metrics or when prediction is off
            overlay_df = chart_df[chart_df['is_prediction'] == False] if predict_future and future_data else chart_df
            base_overlay = alt.Chart(overlay_df).encode(x=alt.X("Date:T", axis=x_axis))
            
            # Create bars for the overlay metric with secondary y-axis
            overlay_bars = base_overlay.mark_bar(
                color=color, 
                opacity=0.6,
                size=20
            ).encode(
                y=alt.Y(f"{selected_metric}:Q", 
                       axis=alt.Axis(title=selected_metric, titleColor=color, labelColor=color),
                       scale=alt.Scale(domain=[0, overlay_df[selected_metric].max() * 1.1]) if not overlay_df.empty else alt.Scale(domain=[0, 100])),
                tooltip=["Date:T", f"{selected_metric}:Q"]
            )
        
        # Layer the charts with proper axis resolution
        chart = alt.layer(
            overlay_bars,  # Put bars behind lines
            chart
        ).resolve_scale(
            y='independent'
        ).resolve_axis(
            y='independent'
        )
    
    # Configure final chart properties
    prediction_text = " (Dashed = Predicted)" if predict_future and future_data else ""
    
    if selected_metric and predict_future and future_data and selected_metric in ['Distance (km)', 'Planned_Distance']:
        overlay_text = f" • {selected_metric} (Solid = Actual, Faded = Planned)"
    elif selected_metric:
        overlay_text = f" • {selected_metric} (Bars)"
    else:
        overlay_text = ""
    
    # Get current metrics for chart title
    current_metrics_text = ""
    if not df.empty and all(col in df.columns for col in ['CTL', 'ATL', 'TSB']):
        latest_for_chart = df.iloc[-1]
        current_metrics_text = f"Current: CTL {latest_for_chart['CTL']:.1f} | ATL {latest_for_chart['ATL']:.1f} | TSB {latest_for_chart['TSB']:.1f}"
    
    chart = chart.properties(
        height=400,
        title=alt.TitleParams(
            text=["🏃‍♂️ Training Load Analysis" + prediction_text, 
                  f"CTL: Fitness (Blue) • ATL: Fatigue (Red) • TSB: Form (Yellow){overlay_text}",
                  current_metrics_text],
            fontSize=16,
            anchor='start',
            color='white',
            subtitleFontSize=12,
            subtitleColor='#888'
        )
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
    
    # Summary Dashboard Widget
    if not df.empty and all(col in df.columns for col in ['CTL', 'ATL', 'TSB']):
        latest = df.iloc[-1]
        
        # Calculate key insights
        fitness_trend = "📈 Building" if len(df) > 7 and latest['CTL'] > df.iloc[-7]['CTL'] else "📉 Declining" if len(df) > 7 and latest['CTL'] < df.iloc[-7]['CTL'] else "→ Stable"
        days_until_peak = max(0, int((5 - latest['TSB']) / 0.5)) if latest['TSB'] < 5 else 0
        recommended_action = "🏃‍♂️ Add training load" if latest['TSB'] > 15 else "💪 Quality training time" if -5 <= latest['TSB'] <= 15 else "😴 Recovery needed"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        ">
            <div style="text-align: center;">
                <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem;">FITNESS TREND</div>
                <div style="font-size: 1.1rem; font-weight: 600;">{fitness_trend}</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem;">RECOMMENDED ACTION</div>
                <div style="font-size: 1.1rem; font-weight: 600;">{recommended_action}</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem;">TRAINING STATUS</div>
                <div style="font-size: 1.1rem; font-weight: 600;">{"🎯 Race Ready" if -5 <= latest['TSB'] <= 5 else "🚀 Very Fresh" if latest['TSB'] > 10 else "⚡ High Load"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Modern metric cards
    if not df.empty and all(col in df.columns for col in ['CTL', 'ATL', 'TSB']):
        latest = df.iloc[-1]
        tsb = latest['TSB']
        
        # Calculate trends (compare to 7 days ago)
        week_ago_data = df[df['Date'] <= (latest['Date'] - timedelta(days=7))]
        if not week_ago_data.empty:
            week_ago = week_ago_data.iloc[-1]
            ctl_change = ((latest['CTL'] - week_ago['CTL']) / week_ago['CTL']) * 100 if week_ago['CTL'] != 0 else 0
            atl_change = ((latest['ATL'] - week_ago['ATL']) / week_ago['ATL']) * 100 if week_ago['ATL'] != 0 else 0
            tsb_change = latest['TSB'] - week_ago['TSB']  # Absolute change for TSB
            
            ctl_trend = "↗️" if ctl_change > 2 else "↘️" if ctl_change < -2 else "→"
            atl_trend = "↗️" if atl_change > 2 else "↘️" if atl_change < -2 else "→"
            tsb_trend = "↗️" if tsb_change > 2 else "↘️" if tsb_change < -2 else "→"
            
            ctl_trend_text = f"{ctl_trend} {ctl_change:+.1f}%"
            atl_trend_text = f"{atl_trend} {atl_change:+.1f}%"
            tsb_trend_text = f"{tsb_trend} {tsb_change:+.1f}"
        else:
            ctl_trend_text = atl_trend_text = tsb_trend_text = ""
        
        # Calculate TSB needle position (0-180 degrees)
        # TSB range from -30 to +30, mapped to 0-180 degrees
        tsb_clamped = max(-30, min(30, tsb))
        needle_angle = ((tsb_clamped + 30) / 60) * 180
        
        # Determine TSB status
        if tsb < -15:
            tsb_status_class = "tsb-overreach"
            tsb_status_text = "⚠️ Overreaching"
            recovery_days = int(abs(tsb) / 2)  # Rough estimate: 2 TSB points per day of recovery
            recommendation = f"🛌 Take {recovery_days} easy days to recover"
        elif tsb < -5:
            tsb_status_class = "tsb-fatigue"
            tsb_status_text = "🔥 High Fatigue"
            recovery_days = int(abs(tsb + 5) / 2)
            recommendation = f"😴 Consider {recovery_days} lighter days"
        elif tsb < 5:
            tsb_status_class = "tsb-optimal"
            tsb_status_text = "✅ Optimal Zone"
            recommendation = "🎯 Perfect for quality training"
        elif tsb < 15:
            tsb_status_class = "tsb-fresh"
            tsb_status_text = "🚀 Fresh & Ready"
            recommendation = "💪 Great time for hard sessions"
        else:
            tsb_status_class = "tsb-detraining"
            tsb_status_text = "💤 Very Fresh"
            detraining_days = int((tsb - 10) / 1.5)  # Rough estimate
            recommendation = f"🏃‍♂️ Add training load soon ({detraining_days}+ days fresh)"
        
        st.markdown("**📊 Current Metrics**")
        
        # Compact metric cards
        st.markdown(f"""
        <div class="metric-cards-container">
            <div class="metric-card-modern">
                <span class="metric-icon">🏋️</span>
                <div class="metric-label">Fitness</div>
                <div class="metric-value" style="color: #667eea;">{latest['CTL']:.1f}</div>
                <div class="metric-trend">{ctl_trend_text}</div>
                <div style="font-size: 0.6rem; opacity: 0.6; margin-top: 0.25rem;">Target: 80-120</div>
            </div>
            <div class="metric-card-modern">
                <span class="metric-icon">⚡</span>
                <div class="metric-label">Fatigue</div>
                <div class="metric-value" style="color: #ff6b6b;">{latest['ATL']:.1f}</div>
                <div class="metric-trend">{atl_trend_text}</div>
                <div style="font-size: 0.6rem; opacity: 0.6; margin-top: 0.25rem;">Ratio: {(latest['CTL']/latest['ATL']):.1f}x</div>
            </div>
            <div class="metric-card-modern">
                <span class="metric-icon">🎯</span>
                <div class="metric-label">Form</div>
                <div class="metric-value" style="color: #feca57;">{latest['TSB']:.1f}</div>
                <div class="metric-trend">{tsb_trend_text}</div>
                <div style="font-size: 0.6rem; opacity: 0.6; margin-top: 0.25rem;">Optimal: -10 to +10</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # TSB Meter
        st.markdown(f"""
        <div class="tsb-meter-container">
            <div class="tsb-meter-title">📊 Training Status Meter</div>
            <div class="tsb-gauge">
                <div class="tsb-gauge-bg">
                    <div class="tsb-gauge-overlay"></div>
                    <div class="tsb-needle" style="transform: translateX(-50%) rotate({needle_angle}deg);"></div>
                    <div class="tsb-value-display">{tsb:.1f}</div>
                </div>
            </div>
            <div class="tsb-labels">
                <span>Overreach</span>
                <span>Fatigue</span>
                <span>Optimal</span>
                <span>Fresh</span>
                <span>Detraining</span>
            </div>
            <div class="tsb-status {tsb_status_class}">{tsb_status_text}</div>
            <div class="tsb-recommendation">{recommendation}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick insights
        fitness_fatigue_ratio = latest['CTL'] / latest['ATL'] if latest['ATL'] > 0 else 0
        recent_7d_tss = df[df['Date'] >= (latest['Date'] - timedelta(days=6))]['TSS'].sum()
        
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin: 1rem 0;">
            <div class="metric-card-modern">
                <span class="metric-icon">⚖️</span>
                <div class="metric-label">Fitness/Fatigue</div>
                <div class="metric-value" style="color: #9c88ff;">{fitness_fatigue_ratio:.2f}</div>
                <div class="metric-trend">{'Balanced' if 1.2 <= fitness_fatigue_ratio <= 1.8 else 'Imbalanced'}</div>
            </div>
            <div class="metric-card-modern">
                <span class="metric-icon">📅</span>
                <div class="metric-label">7-Day TSS</div>
                <div class="metric-value" style="color: #26d0ce;">{recent_7d_tss:.0f}</div>
                <div class="metric-trend">Last week</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Collapsible sections for less clutter
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("ℹ️ Understanding Fatigue Metrics"):
            st.markdown("""
            **CTL (Chronic Training Load)** - Your fitness level  
            42-day average of training stress
            
            **ATL (Acute Training Load)** - Your fatigue level  
            7-day average of training stress
            
            **TSB (Training Stress Balance)** - Your form  
            CTL minus ATL (fitness minus fatigue)
            
            **Optimal Ranges:**
            - TSB > +10: Very fresh (potential detraining)
            - TSB -10 to +10: Optimal range
            - TSB < -15: Overreaching (need recovery)
            """)
    
    with col2:
        with st.expander("📋 Daily TSS Data"):
            if not df.empty:
                st.dataframe(
                    df[["Date", "TSS", "ATL", "CTL", "TSB"]].sort_values("Date", ascending=False).head(20),
                    use_container_width=True,
                    height=250
                )

    st.markdown('<div class="section-separator"></div>', unsafe_allow_html=True)

    # Modern AI Analysis Section
    if not df.empty:
        latest_date = df['Date'].max().strftime('%Y-%m-%d')
        analysis_key = f"fatigue_analysis_{latest_date}_{selected_range.replace(' ', '_')}"
        
        # Get current values for prompt
        latest = df.iloc[-1]
        current_fatigue_metrics = {
            'ATL': latest['ATL'],
            'CTL': latest['CTL'], 
            'TSB': latest['TSB']
        }
        
        # Load saved analyses from user's gist
        saved_analyses = load_saved_fatigue_analyses(user_info, gist_id, gist_filename, github_token)
        
        # Check if AI features are enabled for this user
        features = user_info.get('Features', []) or user_info.get('features', [])
        if isinstance(features, str):
            try:
                features = json.loads(features)
            except Exception:
                features = []
        ai_enabled = 'ai' in features
        
        # Modern section header
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <span style="font-size: 1.5rem;">🧠</span>
            <h3 style="margin: 0; font-size: 1.4rem; font-weight: 600;">AI Training Insights</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Tab layout for better organization
        analysis_tab, history_tab = st.tabs(["🔄 Generate Analysis", "📚 History"])
        
        with analysis_tab:
            # Analysis generation section with modern styling
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Context card
                st.markdown(f"""
                <div class="metric-card-modern" style="text-align: left; margin-bottom: 1rem;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #667eea;">📊 Analysis Context</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                        <div><strong>Range:</strong> {selected_range}</div>
                        <div><strong>CTL:</strong> {current_fatigue_metrics['CTL']:.1f}</div>
                        <div><strong>ATL:</strong> {current_fatigue_metrics['ATL']:.1f}</div>
                        <div><strong>TSB:</strong> {current_fatigue_metrics['TSB']:.1f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate button
                if ai_enabled and client:
                    if st.button("🔄 Generate AI Insights", key=f"button_{analysis_key}", use_container_width=True, type="primary"):
                        runner_profile = user_info.get('runner_profile', {})
                        prompt = generate_fatigue_prompt(df, runner_profile, current_fatigue_metrics, selected_range, today)
                        
                        with st.spinner("Analyzing your training data..."):
                            try:
                                response = client.chat.completions.create(
                                    model="gpt-4-turbo",
                                    messages=[
                                        {"role": "system", "content": "You are an elite running coach with expertise in analyzing fatigue and training metrics. Your analysis is evidence-based, practical, and personalized to each runner's current state."},
                                        {"role": "user", "content": prompt}
                                    ]
                                )
                                analysis_content = response.choices[0].message.content
                                st.session_state[analysis_key] = analysis_content
                                save_success = save_fatigue_analysis(analysis_key, analysis_content, user_info, gist_id, gist_filename, github_token)
                                if save_success:
                                    st.toast("Fatigue analysis complete!", icon="✅")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error generating fatigue analysis: {e}")
                else:
                    disabled_text = "🔒 Generate Insights (API Key Missing)" if not client else "🔒 Generate Insights (Premium Feature)"
                    help_text = "OpenAI API key is missing. Please configure it in the app secrets." if not client else "You do not have access to AI features."
                    st.button(disabled_text, disabled=True, help=help_text, use_container_width=True)
            
            with col2:
                # What you'll get card
                st.markdown("""
                <div class="metric-card-modern" style="text-align: left;">
                    <div style="font-weight: 600; margin-bottom: 0.75rem; color: #feca57;">💡 AI Insights Include</div>
                    <div style="font-size: 0.85rem; line-height: 1.4;">
                        • Training status analysis<br>
                        • Overtraining detection<br>
                        • Load recommendations<br>
                        • Performance timing<br>
                        • Recovery strategies<br>
                        • Next 1-2 weeks plan
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with history_tab:
            # Analysis history section with modern cards
            if saved_analyses:
                # Sort analyses by date (newest first)
                sorted_analyses = []
                for key, analysis in saved_analyses.items():
                    if isinstance(analysis, dict) and 'date' in analysis:
                        sorted_analyses.append((key, analysis))
                    elif isinstance(analysis, str):
                        sorted_analyses.append((key, {
                            'date': 'Unknown Date',
                            'summary': analysis,
                            'analysis_key': key
                        }))
                
                sorted_analyses.sort(key=lambda x: x[1]['date'], reverse=True)
                
                for key, analysis_data in sorted_analyses:
                    analysis_date = analysis_data.get('date', 'Unknown Date')
                    analysis_summary = analysis_data.get('summary', analysis_data if isinstance(analysis_data, str) else 'No content')
                    
                    with st.expander(f"📊 Analysis from {analysis_date}", expanded=False):
                        col1, col2 = st.columns([5, 1])
                        
                        with col1:
                            st.markdown(f"""
                            <div style="
                                background: rgba(255, 255, 255, 0.02);
                                border: 1px solid rgba(255, 255, 255, 0.08);
                                border-radius: 8px;
                                padding: 1rem;
                                border-left: 3px solid #feca57;
                                line-height: 1.6;
                            ">
                                {analysis_summary}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("🗑️", key=f"delete_history_{key}", help="Delete this analysis"):
                                delete_success = delete_fatigue_analysis(key, user_info, gist_id, gist_filename, github_token)
                                if delete_success:
                                    st.toast("Analysis deleted!", icon="🗑️")
                                    st.rerun()
            else:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; opacity: 0.7;">
                    <span style="font-size: 3rem;">🧠</span><br>
                    <div style="margin-top: 1rem;">No previous analyses found.</div>
                    <div style="font-size: 0.9rem; margin-top: 0.5rem;">Generate your first analysis in the 'Generate Analysis' tab.</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Display current analysis if it exists
        if analysis_key in st.session_state:
            st.markdown("**📊 Latest Analysis**")
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 1.5rem;
                margin-top: 1rem;
                border-left: 4px solid #feca57;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                line-height: 1.7;
            ">
                {st.session_state[analysis_key]}
            </div>
            """, unsafe_allow_html=True)
            
        elif analysis_key in saved_analyses:
            analysis_data = saved_analyses[analysis_key]
            analysis_content = analysis_data.get('summary', analysis_data if isinstance(analysis_data, str) else 'No content')
            st.session_state[analysis_key] = analysis_content
            
            st.markdown("**📊 Latest Analysis**")
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 1.5rem;
                margin-top: 1rem;
                border-left: 4px solid #feca57;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                line-height: 1.7;
            ">
                {analysis_content}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; opacity: 0.7;">
            <span style="font-size: 3rem;">📊</span><br>
            <div style="margin-top: 1rem;">No training data available.</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">Add activities to see AI fatigue insights.</div>
        </div>
        """, unsafe_allow_html=True)

    # Add version info in sidebar
    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)
