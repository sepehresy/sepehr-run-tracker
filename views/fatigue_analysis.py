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
    .stRadio > div {
        gap: 0.5rem !important;
    }
    
    .stRadio label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        margin: 2px !important;
        transition: all 0.2s ease !important;
    }
    
    .stRadio label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Modern metric cards */
    .metric-cards-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .metric-card-modern {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .metric-card-modern:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        border-color: rgba(255, 255, 255, 0.15);
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.8;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
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
        }
        
        .control-grid {
            grid-template-columns: 1fr;
        }
        
        .metric-card-modern {
            padding: 1rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
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
    selected_range = st.radio("Time Range Selection", range_options, index=1, horizontal=True, label_visibility="collapsed")

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
    
    df = calculate_atl_ctl_tsb(df)
    df = df.dropna(subset=["Date"]).sort_values("Date")
    
    if range_days[selected_range]:
        min_date = today - timedelta(days=range_days[selected_range])
        df = df[df["Date"] >= min_date]

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
                        start_date = pd.to_datetime(first_week.get('start_date', ''), dayfirst=True).date()
                        if latest_race_date is None or start_date > latest_race_date:
                            latest_race_date = start_date
                            active_plan = plan
                
                if active_plan and 'weeks' in active_plan:
                    # Generate future fatigue data
                    future_data = []
                    last_date = df['Date'].max().date() if not df.empty else today
                    last_ctl = df['CTL'].iloc[-1] if not df.empty else 0
                    last_atl = df['ATL'].iloc[-1] if not df.empty else 0
                    
                    # Project each week from the training plan
                    for week in active_plan['weeks']:
                        start_date = pd.to_datetime(week.get('start_date', ''), dayfirst=True).date()
                        
                        # Only predict future weeks
                        if start_date > last_date:
                            # Calculate weekly TSS from planned training
                            weekly_tss = 0
                            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                            
                            for day in days:
                                day_plan = week.get(day, {})
                                distance = float(day_plan.get('distance', 0))
                                
                                # Estimate TSS from distance (rough approximation)
                                # This is a simple model - could be improved with intensity factors
                                if distance > 0:
                                    estimated_tss = distance * 7  # ~7 TSS per km for moderate effort
                                    weekly_tss += estimated_tss
                            
                            # Create daily projections for the week
                            for day_offset in range(7):
                                current_date = start_date + timedelta(days=day_offset)
                                daily_tss = weekly_tss / 7  # Distribute weekly TSS evenly
                                
                                # Calculate projected CTL and ATL using exponential moving averages
                                # CTL (42-day EMA) and ATL (7-day EMA)
                                alpha_ctl = 2 / (42 + 1)  # CTL smoothing factor
                                alpha_atl = 2 / (7 + 1)   # ATL smoothing factor
                                
                                new_ctl = last_ctl * (1 - alpha_ctl) + daily_tss * alpha_ctl
                                new_atl = last_atl * (1 - alpha_atl) + daily_tss * alpha_atl
                                new_tsb = new_ctl - new_atl
                                
                                future_data.append({
                                    'Date': pd.Timestamp(current_date),
                                    'TSS': daily_tss,
                                    'CTL': new_ctl,
                                    'ATL': new_atl,
                                    'TSB': new_tsb,
                                    'is_prediction': True
                                })
                                
                                last_ctl = new_ctl
                                last_atl = new_atl
                    
                    if future_data:
                        # Combine historical and future data
                        df_historical = df.copy()
                        df_historical['is_prediction'] = False
                        
                        df_future = pd.DataFrame(future_data)
                        df_extended = pd.concat([df_historical, df_future], ignore_index=True)
                        df_extended = df_extended.sort_values('Date').reset_index(drop=True)
                        
                        st.info(f"🔮 Showing prediction for {len(future_data)} future days based on your training plan")
        
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
        tsb_line_hist = base_historical.mark_line(color="#feca57", strokeDash=[8,4], strokeWidth=2, strokeCap="round").encode(
            y=alt.Y("TSB:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        
        # Predicted data (dashed lines with lower opacity)
        base_future = alt.Chart(chart_df[chart_df['is_prediction'] == True]).encode(x=alt.X("Date:T", axis=x_axis))
        ctl_line_pred = base_future.mark_line(color="#667eea", strokeWidth=2, strokeDash=[8,4], opacity=0.7).encode(
            y=alt.Y("CTL:Q"), 
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", alt.value("Predicted")]
        )
        atl_line_pred = base_future.mark_line(color="#ff6b6b", strokeWidth=2, strokeDash=[8,4], opacity=0.7).encode(
            y=alt.Y("ATL:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", alt.value("Predicted")]
        )
        tsb_line_pred = base_future.mark_line(color="#feca57", strokeDash=[12,8], strokeWidth=1.5, opacity=0.7).encode(
            y=alt.Y("TSB:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", alt.value("Predicted")]
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
        tsb_line = base.mark_line(color="#feca57", strokeDash=[8,4], strokeWidth=2, strokeCap="round").encode(
            y=alt.Y("TSB:Q"),
            tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"]
        )
        
        # Combine main lines
        chart = ctl_line + atl_line + tsb_line

    # Add overlay metric as columns/bars if selected
    if selected_metric and selected_metric in df.columns:
        color = metric_colors.get(selected_metric, "#888")
        
        # Only show overlay for historical data (predictions don't have overlay metrics)
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
    overlay_text = f" • {selected_metric} (Bars)" if selected_metric else ""
    
    chart = chart.properties(
        height=350,
        title=alt.TitleParams(
            text=["Training Load Analysis" + prediction_text, "CTL (Blue) • ATL (Red) • TSB (Yellow)" + overlay_text],
            fontSize=14,
            anchor='start',
            color='white',
            subtitleFontSize=11,
            subtitleColor='#888'
        )
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # Modern metric cards
    if not df.empty:
        latest = df.iloc[-1]
        tsb = latest['TSB']
        
        st.markdown("**📊 Current Metrics**")
        st.markdown(f"""
        <div class="metric-cards-container">
            <div class="metric-card-modern">
                <span class="metric-icon">🏋️</span>
                <div class="metric-label">CTL (Fitness)</div>
                <div class="metric-value" style="color: #667eea;">{latest['CTL']:.1f}</div>
            </div>
            <div class="metric-card-modern">
                <span class="metric-icon">⚡</span>
                <div class="metric-label">ATL (Fatigue)</div>
                <div class="metric-value" style="color: #ff6b6b;">{latest['ATL']:.1f}</div>
            </div>
            <div class="metric-card-modern">
                <span class="metric-icon">🎯</span>
                <div class="metric-label">TSB (Form)</div>
                <div class="metric-value" style="color: #feca57;">{latest['TSB']:.1f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Modern status indicator
        if tsb < -15:
            status_class = "status-danger"
            status_text = "⚠️ Overreaching - Consider Recovery"
        elif tsb > 10:
            status_class = "status-warning"
            status_text = "💤 Detraining - Consider Increasing Load"
        else:
            status_class = "status-optimal"
            status_text = "✅ Optimal Training Zone"

        st.markdown(f'<div class="status-indicator {status_class}">{status_text}</div>', unsafe_allow_html=True)

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
