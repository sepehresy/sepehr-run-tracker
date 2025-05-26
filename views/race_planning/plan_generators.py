"""
Training plan generators for race planning module.
"""

import streamlit as st
import openai
from datetime import datetime, timedelta
from views.ai_prompt import generate_ai_plan_prompt
from utils.gsheet import fetch_gsheet_plan
from utils.parse_helper import parse_training_plan
from views.race_planning.utils import parse_day_cell
from views.race_planning.data import save_training_plan
from utils.date_parser import parse_race_date, parse_training_date


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
    try:
        df = parse_training_plan(ai_table_md)
        required_cols = ["Week", "Start Date", "Monday", "Tuesday", 
                        "Wednesday", "Thursday", "Friday", "Saturday", 
                        "Sunday", "Total", "Comment"]
        
        # Debug: Show parsing results
        st.info(f"📊 Parsed {len(df)} weeks from AI response")
        
        if df is None or not all(col in df.columns for col in required_cols):
            # Show debug info for CSV parsing issues
            st.error("[❌ Parse Error] AI training plan format is invalid.")
            st.text("Debug information:")
            
            # Import and use debug helper
            from utils.parse_helper import debug_csv_structure
            debug_csv_structure(ai_table_md)
            
            # Show the raw AI response for debugging
            with st.expander("🔍 View Raw AI Response"):
                st.text(ai_table_md)
            
            raise ValueError("AI plan table format is invalid. Please try again or edit manually.")
            
    except Exception as e:
        # Enhanced error handling for CSV parsing
        st.error(f"[❌ Parse Error] Could not parse CSV: {e}")
        
        # Import and use debug helper
        from utils.parse_helper import debug_csv_structure
        debug_csv_structure(ai_table_md)
        
        # Show the raw AI response for debugging
        with st.expander("🔍 View Raw AI Response for Debugging"):
            st.text(ai_table_md)
        
        # Return default empty weeks instead of failing completely
        st.warning("⚠️ Falling back to empty training plan. You can edit it manually.")
        return default_weeks
    
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
    
    # Check if race week is missing and add it if needed
    import pandas as pd
    
    race_date = parse_race_date(race.get('date', ''))
    expected_weeks = len(weeks)  # Original number of weeks expected
    
    # Find if race week exists
    race_week_exists = False
    for week in new_weeks:
        week_start = parse_training_date(week['start_date'])
        week_end = week_start + timedelta(days=6)
        if week_start <= race_date <= week_end:
            race_week_exists = True
            break
    
    # If race week is missing, add it
    if not race_week_exists and len(new_weeks) > 0:
        st.warning(f"⚠️ Race week (containing {race_date}) was missing from AI plan. Adding it...")
        
        # Calculate race week start (Monday of race week)
        race_week_start = race_date - timedelta(days=race_date.weekday())
        
        # Determine which day the race is on
        race_day_name = race_date.strftime('%A').lower()
        
        # Create race week
        race_week = {
            "week_number": len(new_weeks) + 1,
            "start_date": race_week_start.strftime('%Y-%m-%d'),
            "monday": {"distance": 0.0, "description": "Rest"},
            "tuesday": {"distance": 0.0, "description": "Rest"},
            "wednesday": {"distance": 4.0, "description": "Easy shakeout run"},
            "thursday": {"distance": 0.0, "description": "Rest"},
            "friday": {"distance": 3.0, "description": "Easy run + 4x100m strides"},
            "saturday": {"distance": 0.0, "description": "Rest"},
            "sunday": {"distance": 0.0, "description": "Rest"},
            "comment": f"Race Week - {race.get('name', 'Race')} on {race_date.strftime('%A %B %d')}"
        }
        
        # Set the race day
        race_distance = race.get('distance', 21.1)  # Default to half marathon
        race_week[race_day_name] = {
            "distance": race_distance, 
            "description": f"🏁 RACE DAY - {race.get('name', 'Race')} ({race_distance}km)"
        }
        
        # Calculate total distance
        race_week["total_distance"] = sum(
            race_week[day]["distance"] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        )
        
        new_weeks.append(race_week)
        st.success(f"✅ Added race week containing race day ({race_date}) as Week {len(new_weeks)}")
    
    st.success(f"🎯 Generated {len(new_weeks)} weeks total (including race week)")
    
    # Ensure all weeks are consecutive with no gaps
    new_weeks = ensure_consecutive_weeks(new_weeks, race.get('training_start_date', ''), race.get('date', ''))
    
    st.info(f"✅ Ensured consecutive weeks: {len(new_weeks)} total weeks with no gaps")
    
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


def ensure_consecutive_weeks(weeks_list, training_start_date, race_date):
    """
    Ensure all weeks are consecutive with no gaps, filling missing weeks with rest days.
    
    Args:
        weeks_list: List of week dictionaries from AI
        training_start_date: Training start date (string)
        race_date: Race date (string)
        
    Returns:
        List of weeks with no gaps
    """
    if not weeks_list:
        return weeks_list
    
    # Parse dates
    start_date = parse_training_date(training_start_date)
    end_date = parse_race_date(race_date)
    
    if not start_date or not end_date:
        return weeks_list  # Return original if we can't parse dates
    
    # Calculate the Monday of the first week
    first_monday = start_date - timedelta(days=start_date.weekday())
    
    # Calculate the Monday of the race week  
    race_monday = end_date - timedelta(days=end_date.weekday())
    
    # Calculate total weeks needed
    total_weeks = ((race_monday - first_monday).days // 7) + 1
    
    # Create a dictionary of existing weeks by start date
    existing_weeks = {}
    for week in weeks_list:
        week_start = parse_training_date(week.get('start_date', ''))
        if week_start:
            existing_weeks[week_start] = week
    
    # Generate all consecutive weeks
    consecutive_weeks = []
    for week_num in range(total_weeks):
        week_monday = first_monday + timedelta(days=7 * week_num)
        
        if week_monday in existing_weeks:
            # Use existing week but ensure correct week number and start date
            week = existing_weeks[week_monday].copy()
            week['week_number'] = week_num + 1
            week['start_date'] = week_monday.strftime('%Y-%m-%d')
        else:
            # Create missing week with rest days
            week = {
                "week_number": week_num + 1,
                "start_date": week_monday.strftime('%Y-%m-%d'),
                "monday": {"distance": 0.0, "description": "Rest"},
                "tuesday": {"distance": 0.0, "description": "Rest"},
                "wednesday": {"distance": 0.0, "description": "Rest"},
                "thursday": {"distance": 0.0, "description": "Rest"},
                "friday": {"distance": 0.0, "description": "Rest"},
                "saturday": {"distance": 0.0, "description": "Rest"},
                "sunday": {"distance": 0.0, "description": "Rest"},
                "comment": "Recovery/Rest Week - All rest days",
                "total_distance": 0.0
            }
        
        consecutive_weeks.append(week)
    
    return consecutive_weeks 