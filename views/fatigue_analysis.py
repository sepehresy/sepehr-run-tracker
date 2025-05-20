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
        
    return data[user_key].get("fatigue_analyses", {})

# Function to save fatigue analyses to user's gist
def save_fatigue_analysis(key, content, user_info, gist_id, filename, token):
    try:
        # Get the current data
        data = load_gist_data(gist_id, filename, token)
        user_key = user_info["USER_KEY"]
        
        # Ensure user data structure exists
        if user_key not in data:
            data[user_key] = {}
            
        # Ensure fatigue_analyses key exists
        if "fatigue_analyses" not in data[user_key]:
            data[user_key]["fatigue_analyses"] = {}
            
        # Update the fatigue analysis
        data[user_key]["fatigue_analyses"][key] = content
        
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
    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">📊</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">Fatigue Analysis</span>', unsafe_allow_html=True)

    

    # --- Get LTHR from runner profile (if available) ---
    lthr = None
    runner_profile = st.session_state.get("user_info", {}).get("runner_profile", {})
    lthr = runner_profile.get("LTHR") or runner_profile.get("lthr")
    if not lthr:
        lthr = st.number_input("Enter your Lactate Threshold HR (LTHR) for TSS calculation:", min_value=100, max_value=220, value=160)

    # --- Date Range Selector ---
    range_options = ["Last 4 Weeks", "Last 3 Months", "Last 6 Months", "Last Year", "Last 2 Years", "All Time"]
    range_days = {
        "Last 4 Weeks": 28,
        "Last 3 Months": 90,
        "Last 6 Months": 180,
        "Last Year": 365,
        "Last 2 Years": 730,
        "All Time": None
    }
    selected_range = st.radio("Time Range:", range_options, index=1, horizontal=True)

    # --- Data Preparation ---
    df = df.copy()
    # Calculate TSS from HR if not present
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
    # print (df)
    if range_days[selected_range]:
        min_date = today - timedelta(days=range_days[selected_range])
        df = df[df["Date"] >= min_date]

    # --- Chart Metric Selector ---
    metric_options = [
        ("None", None),
        ("Distance (km)", "#00bcd4"),
        ("Elapsed Time (min)", "#8bc34a"),
        ("Avg HR", "#ff9800"),
        ("Max HR", "#e91e63")
    ]
    metric_labels = [m[0] for m in metric_options]
    metric_colors = {m[0]: m[1] for m in metric_options if m[1]}
    metric_radio = st.radio(
        "Select metric to overlay:",
        metric_labels,
        index=0,
        horizontal=True,
        help="Choose one metric to overlay on the chart."
    )
    selected_metric = metric_radio if metric_radio != "None" else None
    # Custom style for radio text color
    if selected_metric:
        st.markdown(f"""
        <style>
        div[role='radiogroup'] label span[data-testid='stMarkdownContainer'] {{
            color: {metric_colors.get(selected_metric, '#fff')} !important;
            font-weight: 700;
        }}
        </style>
        """, unsafe_allow_html=True)

    # --- Main Chart (PMC) ---
    # Set x-axis label/tick formatting based on selected_range
    if selected_range == "Last 4 Weeks":
        x_axis = alt.Axis(title="Date", format="%b %d", labelAngle=-30, labelOverlap=True, tickCount="day")
    elif selected_range in ["Last 3 Months", "Last 6 Months"]:
        x_axis = alt.Axis(title="Date", format="%b %d", labelAngle=-45, labelOverlap=True, tickCount="week")
    elif selected_range in ["Last Year", "Last 2 Years"]:
        x_axis = alt.Axis(title="Date", format="%b %Y", labelAngle=-45, labelOverlap=True, tickCount="month")
    else:  # All Time
        x_axis = alt.Axis(title="Date", format="%Y", labelAngle=0, labelOverlap=True, tickCount="year")

    base = alt.Chart(df).encode(x=alt.X("Date:T", axis=x_axis))
    ctl_line = base.mark_line(color="#1976d2", strokeWidth=3).encode(y=alt.Y("CTL:Q", title="Score"), tooltip=["Date:T", "CTL:Q", "ATL:Q", "TSB:Q", "TSS:Q"])
    atl_line = base.mark_line(color="#b22222", strokeWidth=3).encode(y="ATL:Q")
    tsb_line = base.mark_line(color="#FFD600", strokeDash=[4,2], strokeWidth=2).encode(y="TSB:Q")
    chart = ctl_line + atl_line + tsb_line

    # Add user-selected metric as overlay (if not None)
    if selected_metric and selected_metric in df.columns:
        color = metric_colors.get(selected_metric, "#888")
        chart = chart + base.mark_line(strokeDash=[2,2], strokeWidth=2, color=color).encode(
            y=alt.Y(f"{selected_metric}:Q", axis=alt.Axis(title=None)),
            tooltip=["Date:T", f"{selected_metric}:Q"]
        )

    chart = chart.properties(height=400).interactive()
    st.altair_chart(chart, use_container_width=True)

    # --- Summary Cards & Gauge in a Single Row ---
    latest = df.iloc[-1]
    tsb = latest['TSB']
    import plotly.graph_objects as go

    # Modern, compact TSB gauge with color-coded arc and threshold
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = tsb,
        gauge = {
            'shape': 'angular',
            'axis': {'range': [-40, 40], 'tickwidth': 1, 'tickcolor': "#888", 'dtick': 10, 'tickvals': [-40, -15, 0, 10, 40], 'ticktext': ['-40', '-15', '0', '10', '40']},
            'bar': {'color': "#FFD600", 'thickness': 0.32},  # Thicker arc
            'bgcolor': "#18191a",
            'borderwidth': 0,
            'steps': [
                {'range': [-40, -15], 'color': '#ffebee'},   # Overreaching
                {'range': [-15, 10], 'color': '#e3f2fd'},    # Optimal
                {'range': [10, 40], 'color': '#fffde7'}      # Detraining
            ],
            'threshold': {
                'line': {'color': "#FFD600", 'width': 5},
                'thickness': 0.8,
                'value': tsb
            }
        },
        number={"font": {"size": 32, "color": "#FFD600"}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title = {'text': "<b>TSB (Form)</b><br><span style='font-size:1.1rem;font-weight:400;'>Training Stress Balance</span>", 'font': {"size": 18, "color": "#FFD600"}}
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=200,
        width=260,
        paper_bgcolor="#18191a",
        font_color="#e0e6f7"
    )

    # Use columns for cards and gauge
    card_col1, card_col2, card_col3, gauge_col = st.columns([1,1,1,1.1])
    with card_col1:
        st.markdown("""
        <div style='background:#e3f2fd;padding:0.7rem 1.2rem 0.7rem 1.2rem;border-radius:10px;box-shadow:0 2px 8px rgba(25,118,210,0.07);text-align:center;min-width:120px;'>
            <span style='font-size:1.3rem;'>🏋️</span><br>
            <b style='color:#1976d2;'>CTL (Fitness)</b><br>
            <span style='font-size:1.4rem;color:#1976d2;font-weight:700;'>{:.1f}</span>
        </div>
        """.format(latest['CTL']), unsafe_allow_html=True)
    with card_col2:
        st.markdown("""
        <div style='background:#ffebee;padding:0.7rem 1.2rem 0.7rem 1.2rem;border-radius:10px;box-shadow:0 2px 8px rgba(178,34,34,0.07);text-align:center;min-width:120px;'>
            <span style='font-size:1.3rem;'>⚡</span><br>
            <b style='color:#b22222;'>ATL (Fatigue)</b><br>
            <span style='font-size:1.4rem;color:#b22222;font-weight:700;'>{:.1f}</span>
        </div>
        """.format(latest['ATL']), unsafe_allow_html=True)
    with card_col3:
        st.markdown("""
        <div style='background:#fffde7;padding:0.7rem 1.2rem 0.7rem 1.2rem;border-radius:10px;box-shadow:0 2px 8px rgba(255,214,0,0.07);text-align:center;min-width:120px;'>
            <span style='font-size:1.3rem;'>🏁</span><br>
            <b style='color:#FFD600;'>TSB (Form)</b><br>
            <span style='font-size:1.4rem;color:#FFD600;font-weight:700;'>{:.1f}</span>
        </div>
        """.format(latest['TSB']), unsafe_allow_html=True)
    with gauge_col:
        st.plotly_chart(fig, use_container_width=True)
        # Centered range labels below gauge
        st.markdown("""
        <div style='display:flex;justify-content:center;gap:2.5rem;margin-top:-0.7rem;margin-bottom:0.7rem;font-size:1.08rem;'>
            <span style='color:#b22222;font-weight:600;'>Overreaching</span>
            <span style='color:#1976d2;font-weight:600;'>Optimal</span>
            <span style='color:#FFD600;font-weight:600;'>Detraining</span>
        </div>
        """, unsafe_allow_html=True)

    # Text badge for accessibility
    if tsb < -15:
        st.warning("⚠️ Overreaching: TSB very low. Consider recovery!")
    elif tsb > 10:
        st.info("💤 Detraining: TSB high. Consider increasing load.")
    else:
        st.success("✅ Optimal: TSB in performance range.")

    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)
    
    # --- Fatigue Analysis Explanation ---
    with st.expander("ℹ️ What is Fatigue Analysis? (CTL, ATL, TSB explained)"):
        st.markdown("""
        **Fatigue Analysis** helps you understand your training load, fitness, and recovery using three key metrics:

        - **CTL (Chronic Training Load / Fitness):**
            - Represents your long-term training load (fitness) as a rolling average of your daily TSS over 42 days.
            - Higher CTL means greater aerobic fitness, but also more accumulated fatigue.
        - **ATL (Acute Training Load / Fatigue):**
            - Measures your short-term training load (fatigue) as a rolling average of your daily TSS over 7 days.
            - High ATL means recent hard training; low ATL means you are fresh.
        - **TSB (Training Stress Balance / Form):**
            - Calculated as CTL minus ATL (TSB = CTL - ATL).
            - Positive TSB: you are fresh and well-recovered (good for races).
            - Negative TSB: you are carrying fatigue (normal during training blocks).

        **How to interpret:**
        - **TSB > +10:** You are very fresh, but may be detraining if this persists.
        - **TSB between -10 and +10:** You are in an optimal training or racing state.
        - **TSB < -15:** You are likely overreaching and need recovery.

        **How are these calculated?**
        - **TSS (Training Stress Score):**
            - Calculated from your workout's duration and intensity (using heart rate or power data).
            - If you have heart rate data: TSS = (Elapsed Time in hours) × (Avg HR / LTHR)^2 × 100
            - If you have power/IF: TSS = Duration (hrs) × IF² × 100
        - **CTL:** 42-day exponentially weighted moving average of daily TSS.
        - **ATL:** 7-day exponentially weighted moving average of daily TSS.
        - **TSB:** CTL - ATL (today's fitness minus today's fatigue).

        _Use these metrics to balance your training: build fitness (CTL), manage fatigue (ATL), and time your peak (TSB) for races!_
        """)
    
    # --- Daily TSS Table (Collapsible) ---
    with st.expander("Show Daily TSS Table"):
        st.dataframe(df[["Date", "TSS", "ATL", "CTL", "TSB"]].sort_values("Date", ascending=False), use_container_width=True)    # --- AI-Powered Fatigue Insights Section ---
    st.markdown("#### 🧠 AI Fatigue Analysis & Training Recommendations")
    
    # Create a unique key for this analysis based on date range and latest data
    if not df.empty:
        latest_date = df['Date'].max().strftime('%Y-%m-%d')
        analysis_key = f"fatigue_analysis_{latest_date}_{selected_range}"
        
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
        
        # Create UI for generating and displaying analysis
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if ai_enabled and client:
                if st.button("🔄 Generate Insights", key=f"button_{analysis_key}"):
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
                        except Exception as e:
                            st.error(f"Error generating fatigue analysis: {e}")
            else:
                if not client:
                    st.button("Generate Insights (API Key Missing)", disabled=True, 
                             help="OpenAI API key is missing. Please configure it in the app secrets.")
                else:
                    st.button("Generate Insights (Locked)", disabled=True, 
                             help="You do not have access to AI features.")
        
        with col2:
            if analysis_key in saved_analyses or analysis_key in st.session_state:
                if st.button("🗑️ Delete Analysis", key=f"delete_{analysis_key}"):
                    if analysis_key in st.session_state:
                        del st.session_state[analysis_key]
                    if analysis_key in saved_analyses:
                        # Delete from gist
                        data = load_gist_data(gist_id, gist_filename, github_token)
                        user_key = user_info["USER_KEY"]
                        if user_key in data and "fatigue_analyses" in data[user_key] and analysis_key in data[user_key]["fatigue_analyses"]:
                            del data[user_key]["fatigue_analyses"][analysis_key]
                            save_gist_data(gist_id, gist_filename, github_token, data)
                        st.rerun()
          # Display the analysis with nice formatting if available
        if analysis_key in st.session_state:
            st.markdown("""
            <style>
            .fatigue-analysis {
                background: rgba(49, 51, 63, 0.1);
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                border-left: 4px solid #FFD600;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="fatigue-analysis">{st.session_state[analysis_key]}</div>', unsafe_allow_html=True)
            
        elif analysis_key in saved_analyses:
            st.session_state[analysis_key] = saved_analyses[analysis_key]
            st.markdown("""
            <style>
            .fatigue-analysis {
                background: rgba(49, 51, 63, 0.1);
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                border-left: 4px solid #FFD600;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="fatigue-analysis">{saved_analyses[analysis_key]}</div>', unsafe_allow_html=True)
            
        else:
            st.info("Generate AI insights to see personalized recommendations based on your fatigue metrics.")
            
            # Show sample insights topics
            st.markdown("""
            <div style="margin-top:10px;">
                <details>
                    <summary style="cursor:pointer;color:#888;font-size:0.9rem;">What insights will I get?</summary>
                    <ul style="font-size:0.85rem;color:#888;">
                        <li>Analysis of your current fitness vs. fatigue balance</li>
                        <li>Early warning signs of overtraining</li>
                        <li>Recommendations for adjusting training intensity</li>
                        <li>Optimal timing for peak performance</li>
                        <li>Recovery strategies based on your metrics</li>
                    </ul>
                </details>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No training data available. Add activities to see AI fatigue insights.")
