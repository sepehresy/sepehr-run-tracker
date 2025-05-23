"""
Training plan generators for race planning module.
"""

import streamlit as st
import openai
from views.ai_prompt import generate_ai_plan_prompt
from utils.gsheet import fetch_gsheet_plan
from utils.parse_helper import parse_training_plan
from views.race_planning.utils import parse_day_cell
from views.race_planning.data import save_training_plan


# Path to debug file for AI plan generation
DEBUG_MODE = st.secrets.get("DEBUG_MODE", False)
# DEBUG_AI_PLAN_PATH = "data/analyses/ai_plan_debug3.txt"  # Remove local file dependency

# Hardcoded debug response for when DEBUG_MODE is enabled
DEBUG_AI_PLAN_RESPONSE = """| Week | Start Date | Monday | Tuesday | Wednesday | Thursday | Friday | Saturday | Sunday | Total | Comment |
|------|------------|--------|---------|-----------|----------|--------|----------|--------|-------|---------|
| Week 1 | 2024-01-01 | 0.0 km: Rest | 5.0 km: Easy run | 6.0 km: Easy run | 5.0 km: Easy run | 0.0 km: Rest | 12.0 km: Long run | 4.0 km: Recovery run | 32.0 km | Base building week |
| Week 2 | 2024-01-08 | 0.0 km: Rest | 6.0 km: Easy run | 7.0 km: Easy run | 6.0 km: Easy run | 0.0 km: Rest | 14.0 km: Long run | 5.0 km: Recovery run | 38.0 km | Base building week |
| Week 3 | 2024-01-15 | 0.0 km: Rest | 6.0 km: Tempo run | 8.0 km: Easy run | 6.0 km: Easy run | 0.0 km: Rest | 16.0 km: Long run | 5.0 km: Recovery run | 41.0 km | Build phase |"""


def generate_ai_training_plan(race_id, race, weeks, ai_note, user_info, gist_id, filename, token):
    """
    Generate a training plan using AI.
    
    Args:
        race_id: Race ID
        race: Race data
        weeks: Current training plan weeks
        ai_note: Additional notes for AI
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
        
    Returns:
        list: Updated training plan weeks
    """
    # Create default empty weeks to show while AI is generating
    default_weeks = []
    for w in weeks:
        default_weeks.append({
            "week_number": w.get("week_number"),
            "start_date": w.get("start_date"),
            "monday": {"distance": 0.0, "description": ""},
            "tuesday": {"distance": 0.0, "description": ""},
            "wednesday": {"distance": 0.0, "description": ""},
            "thursday": {"distance": 0.0, "description": ""},
            "friday": {"distance": 0.0, "description": ""},
            "saturday": {"distance": 0.0, "description": ""},
            "sunday": {"distance": 0.0, "description": ""},
            "comment": "",
            "total_distance": 0.0
        })
    
    st.session_state[f"plan_buffer_{race_id}"] = default_weeks
    
    # Generate AI prompt
    prompt = generate_ai_plan_prompt(race, ai_note)
    
    # Get AI response
    if DEBUG_MODE:
        ai_table_md = DEBUG_AI_PLAN_RESPONSE
    else:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a professional running coach."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_table_md = response.choices[0].message.content
    
    # Parse AI response
    df = parse_training_plan(ai_table_md)
    required_cols = ["Week", "Start Date", "Monday", "Tuesday", 
                    "Wednesday", "Thursday", "Friday", "Saturday", 
                    "Sunday", "Total", "Comment"]
    
    if df is None or not all(col in df.columns for col in required_cols):
        raise ValueError("AI plan table format is invalid. Please try again or edit manually.")
    
    # Convert dataframe to weeks format
    new_weeks = []
    for _, row in df.iterrows():
        week = {
            "week_number": int(str(row["Week"]).replace("Week ", "").strip())
                if str(row["Week"]).replace("Week ", "").strip().isdigit()
                else row["Week"],
            "start_date": str(row["Start Date"]),
            "monday": parse_day_cell(row["Monday"]),
            "tuesday": parse_day_cell(row["Tuesday"]),
            "wednesday": parse_day_cell(row["Wednesday"]),
            "thursday": parse_day_cell(row["Thursday"]),
            "friday": parse_day_cell(row["Friday"]),
            "saturday": parse_day_cell(row["Saturday"]),
            "sunday": parse_day_cell(row["Sunday"]),
            "comment": row["Comment"]
        }
        
        # Calculate total distance
        week["total_distance"] = sum(
            week[day]["distance"] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        )
        
        new_weeks.append(week)
    
    # Update session state and save to gist
    st.session_state[f"plan_buffer_{race_id}"] = new_weeks
    save_training_plan(race_id, {"weeks": new_weeks}, user_info, gist_id, filename, token)
    
    return new_weeks


def import_gsheet_plan(race_id, gsheet_url, user_info, gist_id, filename, token):
    """
    Import a training plan from a Google Sheet.
    
    Args:
        race_id: Race ID
        gsheet_url: Google Sheet URL
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
        
    Returns:
        list: Imported training plan weeks
    """
    # Fetch Google Sheet data
    gsheet_df = fetch_gsheet_plan(gsheet_url)
    
    if gsheet_df is None:
        raise ValueError("Failed to fetch Google Sheet plan. Check the URL and permissions.")
    
    # Validate format
    required_cols = ["Week", "Start Date", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Total", "Comment"]
    if not all(col in gsheet_df.columns for col in required_cols):
        raise ValueError("Google Sheet plan format is invalid. Please use the template.")
    
    # Convert dataframe to weeks format
    new_weeks = []
    for _, row in gsheet_df.iterrows():
        week = {
            "week_number": int(str(row["Week"]).replace("Week ", "").strip()),
            "start_date": str(row["Start Date"]),
            "monday": parse_day_cell(row["Monday"]),
            "tuesday": parse_day_cell(row["Tuesday"]),
            "wednesday": parse_day_cell(row["Wednesday"]),
            "thursday": parse_day_cell(row["Thursday"]),
            "friday": parse_day_cell(row["Friday"]),
            "saturday": parse_day_cell(row["Saturday"]),
            "sunday": parse_day_cell(row["Sunday"]),
            "comment": row["Comment"]
        }
        
        # Calculate total distance
        week["total_distance"] = sum([
            week[day]["distance"] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        ])
        
        new_weeks.append(week)
    
    # Update session state and save to gist
    st.session_state[f"plan_buffer_{race_id}"] = new_weeks
    save_training_plan(race_id, {"weeks": new_weeks}, user_info, gist_id, filename, token)
    
    return new_weeks


def generate_ai_analysis(race_id, race, user_info, gist_id, filename, token, plans=None, df=None):
    """
    Generate an AI analysis for a race.
    
    Args:
        race_id: Race ID
        race: Race data
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
        plans: Optional training plans data
        df: Optional running log dataframe
        
    Returns:
        str: AI feedback text
    """
    from datetime import datetime
    from views.race_planning.data import load_progress_feedback, save_progress_feedback
    from views.ai_prompt import generate_ai_prompt

    today_str = str(datetime.today().date())
    race_date = race.get('date', '')
    
    # Prepare training plan data for AI
    if plans is None:
        from views.race_planning.data import load_training_plans
        plans = load_training_plans(user_info, gist_id, filename, token)
    
    plan_weeks = plans.get(race_id, {}).get('weeks', [])
    
    if plan_weeks and isinstance(plan_weeks, list):
        import pandas as pd
        plan_df = pd.DataFrame(plan_weeks)
        if 'start_date' in plan_df.columns:
            plan_df = plan_df.rename(columns={
                'start_date': 'Start Date',
                'monday': 'Monday',
                'tuesday': 'Tuesday',
                'wednesday': 'Wednesday',
                'thursday': 'Thursday',
                'friday': 'Friday',
                'saturday': 'Saturday',
                'sunday': 'Sunday',
                'total_distance': 'Total',
                'comment': 'Comment',
                'week_number': 'Week'
            })
    else:
        import pandas as pd
        plan_df = pd.DataFrame()
    
    chart_df = pd.DataFrame() if df is None else df
    lap_text = ''  # You may want to use actual lap/run data if available
    
    # Get existing AI feedback for context
    ai_history_dict = load_progress_feedback(user_info, gist_id, filename, token)
    if isinstance(ai_history_dict, dict):
        ai_history = ai_history_dict.get(race_id, [])
    else:
        ai_history = []
    
    # Combine previous feedback for context
    if isinstance(ai_history, list):
        previous_notes = '\n\n'.join([
            entry.get('summary', '') for entry in ai_history if isinstance(entry, dict) and 'summary' in entry
        ])
    else:
        previous_notes = ''
    
    # Generate AI prompt
    prompt = generate_ai_prompt(race, today_str, race_date, plan_df, chart_df, lap_text, previous_notes)
    
    # Get AI response
    ai_feedback = None
    ai_feedback_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    try:
        if DEBUG_MODE:
            ai_feedback = 'This is a debug AI analysis summary. Your training plan looks good with balanced weekly mileage. Focus on consistency and listen to your body for injury prevention.'
        else:
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a professional running coach."},
                    {"role": "user", "content": prompt}
                ]
            )
            ai_feedback = response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"AI error: {str(e)}")
    
    if ai_feedback:
        # Save AI feedback
        entry = {
            'date': ai_feedback_date,
            'summary': ai_feedback
        }
        save_progress_feedback(race_id, entry, user_info, gist_id, filename, token)
    
    return ai_feedback 