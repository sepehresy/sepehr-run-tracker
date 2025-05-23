"""
Utility functions for race planning module.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd


def parse_day_cell(cell):
    """
    Parse a day cell string into a distance and description.
    
    Format: "10.0 km: Easy run"
    
    Returns:
        dict: {"distance": float, "description": str}
    """
    try:
        dist, desc = str(cell).split(" km:", 1)
        return {"distance": float(dist.strip()), "description": desc.strip()}
    except Exception:
        return {"distance": 0.0, "description": str(cell)}


def calculate_week_dates(start_date, race_date):
    """
    Calculate week dates for training plan.
    
    Args:
        start_date: Training start date
        race_date: Race date
        
    Returns:
        tuple: (plan_start_date, plan_race_date, num_weeks, week_starts)
    """
    # Align to start of week (Monday)
    plan_start_date = start_date - timedelta(days=start_date.weekday())
    plan_race_date = race_date
    plan_race_week_start = plan_race_date - timedelta(days=plan_race_date.weekday())
    
    # Calculate number of weeks
    num_weeks = max(1, ((plan_race_week_start - plan_start_date).days // 7) + 1)
    
    # Generate week start dates
    week_starts = [plan_start_date + timedelta(days=7*w) for w in range(num_weeks)]
    
    return (plan_start_date, plan_race_date, num_weeks, week_starts)


def create_empty_training_plan(start_date, race_date, race_distance, default_format=False):
    """
    Create an empty training plan with the specified parameters.
    
    Args:
        start_date: Training start date
        race_date: Race date
        race_distance: Race distance in km
        default_format: Whether to use default week templates instead of empty weeks
        
    Returns:
        list: List of week data for training plan
    """
    _, _, num_weeks, week_starts = calculate_week_dates(start_date, race_date)
    plan_race_date = race_date
    weeks = []
    
    # Setup templates if using default format
    if default_format:
        # Define templates for different phases of training
        base_template = {
            "monday": {"distance": 0.0, "description": "Rest"},
            "tuesday": {"distance": 5.0, "description": "Easy run"},
            "wednesday": {"distance": 0.0, "description": "Cross-training"},
            "thursday": {"distance": 6.0, "description": "Easy run"},
            "friday": {"distance": 0.0, "description": "Rest"},
            "saturday": {"distance": 10.0, "description": "Long run"},
            "sunday": {"distance": 5.0, "description": "Recovery run"}
        }
        
        build_template = {
            "monday": {"distance": 0.0, "description": "Rest"},
            "tuesday": {"distance": 6.0, "description": "Speed workout"},
            "wednesday": {"distance": 8.0, "description": "Moderate run"},
            "thursday": {"distance": 0.0, "description": "Cross-training"},
            "friday": {"distance": 5.0, "description": "Easy run"},
            "saturday": {"distance": 15.0, "description": "Long run"},
            "sunday": {"distance": 6.0, "description": "Recovery run"}
        }
        
        peak_template = {
            "monday": {"distance": 0.0, "description": "Rest"},
            "tuesday": {"distance": 8.0, "description": "Tempo run"},
            "wednesday": {"distance": 10.0, "description": "Hill workout"},
            "thursday": {"distance": 5.0, "description": "Easy run"},
            "friday": {"distance": 0.0, "description": "Rest"},
            "saturday": {"distance": 20.0, "description": "Long run"},
            "sunday": {"distance": 7.0, "description": "Recovery run"}
        }
        
        taper_template = {
            "monday": {"distance": 0.0, "description": "Rest"},
            "tuesday": {"distance": 5.0, "description": "Easy run"},
            "wednesday": {"distance": 4.0, "description": "Speed play"},
            "thursday": {"distance": 0.0, "description": "Rest"},
            "friday": {"distance": 3.0, "description": "Easy run + strides"},
            "saturday": {"distance": 6.0, "description": "Easy run"},
            "sunday": {"distance": 0.0, "description": "Rest"}
        }
    
    # Create weeks with appropriate templates or empty
    for w, week_start in enumerate(week_starts):
        # Default to empty week
        week = {
            "week_number": w+1,
            "start_date": week_start.strftime("%Y-%m-%d"),
            "status": "💤 Future",
            "monday": {"distance": 0.0, "description": "Rest"},
            "tuesday": {"distance": 0.0, "description": "Rest"},
            "wednesday": {"distance": 0.0, "description": "Rest"},
            "thursday": {"distance": 0.0, "description": "Rest"},
            "friday": {"distance": 0.0, "description": "Rest"},
            "saturday": {"distance": 0.0, "description": "Rest"},
            "sunday": {"distance": 0.0, "description": "Rest"},
            "comment": ""
        }
        
        # Apply template if using default format
        if default_format:
            phase_percent = w / max(1, num_weeks - 1)  # Training phase as percentage
            
            if phase_percent < 0.3:
                # Base phase (first 30% of plan)
                template = base_template
                week["comment"] = "Base building phase"
            elif phase_percent < 0.7:
                # Build phase (30-70% of plan)
                template = build_template
                week["comment"] = "Volume building phase"
            elif phase_percent < 0.85:
                # Peak phase (70-85% of plan)
                template = peak_template
                week["comment"] = "Peak training phase"
            else:
                # Taper phase (last 15% of plan)
                template = taper_template
                week["comment"] = "Taper phase"
            
            # Apply the template
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                week[day] = template[day].copy()
            
            # Scale distances based on race distance
            if race_distance > 0:
                scale_factor = min(2.0, max(0.7, race_distance / 42.2))  # Normalize against marathon
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    week[day]["distance"] = round(week[day]["distance"] * scale_factor, 1)
        
        # Check if this is the race week
        week_end = week_start + timedelta(days=6)
        if week_start <= race_date <= week_end:
            race_day_idx = plan_race_date.weekday()
            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            week[day_names[race_day_idx]] = {"distance": race_distance, "description": "Race day"}
            
            # Update days before race for taper
            for i in range(1, 4):  # Update 3 days before race
                if race_day_idx - i >= 0:  # Only update if day exists
                    prev_day = day_names[race_day_idx - i]
                    if i == 1:
                        week[prev_day] = {"distance": 0.0, "description": "Rest (day before race)"}
                    elif i == 2:
                        week[prev_day] = {"distance": 2.0, "description": "Easy run + strides"}
                    elif i == 3:
                        week[prev_day] = {"distance": 0.0, "description": "Rest"}
        
        # Calculate total weekly distance
        week["total_distance"] = sum(week[day]["distance"] for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
        
        weeks.append(week)
    
    return weeks


def prepare_training_plan_dataframe(weeks):
    """
    Convert training plan weeks into a DataFrame for display.
    
    Args:
        weeks: List of week data
        
    Returns:
        DataFrame: Training plan dataframe for display
    """
    plan_df = pd.DataFrame([
        {
            "Week": f"Week {w.get('week_number', idx+1)}",
            "Start Date": w.get("start_date", ""),
            "Status": w.get("status", "💤 Future"),
            "Monday": f"{w.get('monday', {}).get('distance', 0)} km: {w.get('monday', {}).get('description', '')}",
            "Tuesday": f"{w.get('tuesday', {}).get('distance', 0)} km: {w.get('tuesday', {}).get('description', '')}",
            "Wednesday": f"{w.get('wednesday', {}).get('distance', 0)} km: {w.get('wednesday', {}).get('description', '')}",
            "Thursday": f"{w.get('thursday', {}).get('distance', 0)} km: {w.get('thursday', {}).get('description', '')}",
            "Friday": f"{w.get('friday', {}).get('distance', 0)} km: {w.get('friday', {}).get('description', '')}",
            "Saturday": f"{w.get('saturday', {}).get('distance', 0)} km: {w.get('saturday', {}).get('description', '')}",
            "Sunday": f"{w.get('sunday', {}).get('distance', 0)} km: {w.get('sunday', {}).get('description', '')}",
            "Comment": w.get("comment", "")
        }
        for idx, w in enumerate(weeks)
    ])
    
    # Calculate week totals
    total_col = []
    for _, row in plan_df.iterrows():
        week_total = 0.0
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            try:
                dist, _ = str(row[day]).split(" km:", 1)
                week_total += float(dist.strip())
            except Exception:
                pass
        total_col.append(f"{week_total:.1f} km")
    plan_df["Total"] = total_col
    
    # Add index information
    plan_df["idx"] = list(range(len(plan_df)))
    plan_df["WeekNum"] = plan_df["Week"].str.extract(r"(\d+)").astype(int)
    
    return plan_df


def initialize_week_selection(race_id, race, weeks):
    """
    Initialize the selected week in session state.
    
    Args:
        race_id: Race ID
        race: Race data
        weeks: Training plan weeks
    """
    if f"selected_week_{race_id}" not in st.session_state:
        # Find current week or default to first week
        current_week_idx = None
        race_week_idx = None
        today_date = datetime.today().date()
        
        for idx, w in enumerate(weeks):
            try:
                start_date = pd.to_datetime(w.get("start_date", "")).date()
                end_date = start_date + timedelta(days=6)
                
                # Check if this is the race week
                race_date_val = pd.to_datetime(race.get("date", ""), errors="coerce")
                if not pd.isnull(race_date_val) and start_date <= race_date_val.date() <= end_date:
                    race_week_idx = idx
                
                # Check if this is the current week
                if start_date <= today_date <= end_date:
                    current_week_idx = idx
                    break
            except:
                continue
        
        # Default selection: current week > race week > first week
        if current_week_idx is not None:
            st.session_state[f"selected_week_{race_id}"] = current_week_idx
        elif race_week_idx is not None:
            st.session_state[f"selected_week_{race_id}"] = race_week_idx
        elif weeks:
            st.session_state[f"selected_week_{race_id}"] = 0
        else:
            st.session_state[f"selected_week_{race_id}"] = None 


def update_race_plan(race, race_id, form_data, races, weeks, user_info, gist_id, filename, token):
    """
    Update race information and training plan based on form data.
    
    Args:
        race: Race data dictionary
        race_id: Race ID
        form_data: Form data with updated race information
        races: List of all races
        weeks: Current training plan weeks
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
        
    Returns:
        list: Updated training plan weeks
    """
    from views.race_planning.data import save_races, save_training_plan
    
    # Check if dates have changed
    old_race_date = pd.to_datetime(race.get("date", form_data["date"])).date() if race.get("date") else form_data["date"]
    old_start_date = pd.to_datetime(race.get("training_start_date", form_data["training_start_date"])).date() if race.get("training_start_date") else form_data["training_start_date"]
    new_race_date = form_data["date"]
    new_start_date = form_data["training_start_date"]
    
    # Only regenerate weeks if dates have changed
    if old_race_date != new_race_date or old_start_date != new_start_date:
        new_plan_start = new_start_date - timedelta(days=new_start_date.weekday())
        new_plan_race = new_race_date
        new_plan_race_week_start = new_plan_race - timedelta(days=new_plan_race.weekday())
        new_num_weeks = max(1, ((new_plan_race_week_start - new_plan_start).days // 7) + 1)
        new_week_starts = [new_plan_start + timedelta(days=7*w) for w in range(new_num_weeks)]
        
        old_weeks_by_start = {pd.to_datetime(w.get("start_date")).date(): w for w in weeks if w.get("start_date")}
        new_weeks = []
        
        for i, week_start in enumerate(new_week_starts):
            week_date = week_start
            old_week = old_weeks_by_start.get(week_date)
            
            if old_week:
                new_week = dict(old_week)
            else:
                new_week = {
                    "week_number": i+1,
                    "start_date": week_start.strftime("%Y-%m-%d"),
                    "status": "💤 Future",
                    "monday": {"distance": 0.0, "description": "Rest"},
                    "tuesday": {"distance": 0.0, "description": "Rest"},
                    "wednesday": {"distance": 0.0, "description": "Rest"},
                    "thursday": {"distance": 0.0, "description": "Rest"},
                    "friday": {"distance": 0.0, "description": "Rest"},
                    "saturday": {"distance": 0.0, "description": "Rest"},
                    "sunday": {"distance": 0.0, "description": "Rest"},
                    "comment": ""
                }
                
            new_week["week_number"] = i+1
            new_week["start_date"] = week_start.strftime("%Y-%m-%d")
            new_weeks.append(new_week)
        
        # Add race day to the correct week
        if new_weeks:
            race_week_idx = new_plan_race.weekday()
            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            
            # Find the race week
            race_week = None
            for week in new_weeks:
                week_start = pd.to_datetime(week["start_date"]).date()
                week_end = week_start + timedelta(days=6)
                if week_start <= new_race_date <= week_end:
                    race_week = week
                    break
            
            if race_week:
                race_week[day_names[race_week_idx]] = {"distance": form_data["distance"], "description": "Race day"}
    else:
        # If dates haven't changed, just keep the existing weeks
        new_weeks = weeks
    
    # Update race data
    if "runner_profile" in race:
        del race["runner_profile"]
    
    # Update race in the races list
    for r in races:
        if r.get("id") == race_id:
            r["name"] = form_data["name"]
            r["distance"] = form_data["distance"]
            r["goal_time"] = form_data["goal_time"]
            r["date"] = form_data["date"].isoformat() if hasattr(form_data["date"], 'isoformat') else str(form_data["date"])
            r["training_start_date"] = form_data["training_start_date"].isoformat() if hasattr(form_data["training_start_date"], 'isoformat') else str(form_data["training_start_date"])
            r["elevation_gain"] = form_data["elevation_gain"]
            r["type"] = form_data["type"]
            r["notes"] = form_data["notes"]
            break
    
    # Save changes
    save_races(races, user_info, gist_id, filename, token)
    save_training_plan(race_id, {"weeks": new_weeks}, user_info, gist_id, filename, token)
    
    return new_weeks 