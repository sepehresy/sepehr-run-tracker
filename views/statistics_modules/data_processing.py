"""
Data processing utilities for running statistics
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def parse_time_to_minutes(time_str):
    """Convert time string to minutes
    
    Handles multiple formats:
    - MM:SS:00 (minutes:seconds:centiseconds) - common in running data
    - HH:MM:SS (hours:minutes:seconds) - for very long activities
    - MM:SS (minutes:seconds)
    - Numeric values (already in minutes)
    """
    if pd.isna(time_str) or time_str == '' or time_str == '-':
        return None
    try:
        if isinstance(time_str, str):
            parts = time_str.split(':')
            if len(parts) == 3:
                # Check if this looks like MM:SS:00 format (common in running data)
                # If first part > 24, it's likely minutes, not hours
                first_part = int(parts[0])
                if first_part > 24:  # Likely MM:SS:00 format
                    return first_part + int(parts[1]) / 60 + int(parts[2]) / 3600
                else:  # Traditional HH:MM:SS format
                    return first_part * 60 + int(parts[1]) + int(parts[2]) / 60
            elif len(parts) == 2:  # MM:SS
                return int(parts[0]) + int(parts[1]) / 60
        return float(time_str)
    except:
        return None


def parse_pace_to_minutes(pace_input):
    """Convert pace input to minutes per km (handles both min:sec and decimal formats)
    
    Input formats supported:
    - "5:30" -> 5.5 minutes
    - "6:15" -> 6.25 minutes  
    - 5.5 -> 5.5 minutes (decimal)
    - 6.25 -> 6.25 minutes (decimal)
    """
    if pd.isna(pace_input) or pace_input == '' or pace_input == '-':
        return None
    try:
        if isinstance(pace_input, str) and ':' in pace_input:
            # Handle min:sec format (e.g., "5:30")
            parts = pace_input.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes + seconds / 60.0
        else:
            # Handle decimal format (e.g., 5.5) or numeric input
            return float(pace_input)
    except:
        return None


def format_pace_to_min_sec(minutes):
    """Convert decimal minutes to MM:SS format for display"""
    if pd.isna(minutes) or minutes is None:
        return "-"
    try:
        total_minutes = int(minutes)
        seconds = round((minutes - total_minutes) * 60)
        return f"{total_minutes}:{seconds:02d}"
    except:
        return "-"


def format_time_from_minutes(minutes):
    """Convert minutes to HH:MM format"""
    if pd.isna(minutes) or minutes is None:
        return "-"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}:{mins:02d}"
    else:
        return f"{mins}min"


def format_number_with_commas(number):
    """Format numbers with commas for better readability"""
    if number >= 1000:
        return f"{number:,.1f}"
    else:
        return f"{number:.1f}"


def calculate_training_load_score(df):
    """Calculate a simple training load score based on distance and intensity"""
    if df.empty:
        return 0
    
    # Simple formula: distance * intensity factor (based on pace)
    # Faster paces get higher intensity multiplier
    df_calc = df.copy()
    df_calc['pace_minutes'] = df_calc['Pace (min/km)'].apply(parse_pace_to_minutes)
    
    # Normalize pace to intensity (faster = higher intensity)
    if df_calc['pace_minutes'].notna().any():
        max_pace = df_calc['pace_minutes'].max()
        df_calc['intensity'] = (max_pace - df_calc['pace_minutes']) / max_pace + 0.5
        df_calc['intensity'] = df_calc['intensity'].fillna(0.7)  # Default intensity
    else:
        df_calc['intensity'] = 0.7
    
    df_calc['load'] = df_calc['Distance (km)'] * df_calc['intensity']
    return df_calc['load'].sum()


def detect_workout_type(row):
    """Detect workout type based on Workout Type column first, then activity name and characteristics"""
    # First, check if there's a "Workout Type" column with a valid value
    for col_name in ['Workout Type', 'workout_type', 'WorkoutType', 'Type']:
        if col_name in row and not pd.isna(row.get(col_name, '')):
            workout_type = str(row[col_name]).strip()
            if workout_type and workout_type.lower() not in ['', 'none', 'null', 'default']:
                # Map common workout type values to our standard categories
                workout_type_lower = workout_type.lower()
                
                # Race mapping
                if any(keyword in workout_type_lower for keyword in ['race', 'competition', 'event']):
                    return 'Race'
                
                # Workout mapping
                if any(keyword in workout_type_lower for keyword in ['workout', 'tempo', 'interval', 'speed', 'track', 'fartlek', 'threshold']):
                    return 'Workout'
                
                # Long run mapping
                if any(keyword in workout_type_lower for keyword in ['long', 'endurance', 'lsd']):
                    return 'Long Run'
                
                # Commute mapping
                if any(keyword in workout_type_lower for keyword in ['commute', 'work']):
                    return 'Commute'
                
                # If it's a specific workout type that doesn't match our keywords, 
                # return it as-is if it's one of our standard types
                if workout_type in ['Race', 'Workout', 'Long Run', 'Commute', 'Default']:
                    return workout_type
                
                # For other specific workout types, try to categorize them
                if any(keyword in workout_type_lower for keyword in ['easy', 'recovery', 'base', 'aerobic']):
                    return 'Default'
    
    # Enhanced fallback detection using multiple data points
    # Get activity characteristics
    activity_name = ''
    for col_name in ['Name', 'Activity Name', 'Activity', 'name']:
        if col_name in row and not pd.isna(row.get(col_name, '')):
            activity_name = str(row[col_name]).lower()
            break
    
    distance = row.get('Distance (km)', 0)
    pace_minutes = row.get('pace_minutes', None)
    avg_hr = row.get('Avg HR', None)
    description = str(row.get('Description', '')).lower()
    
    # Combine name and description for better keyword detection
    full_text = f"{activity_name} {description}".lower()
    
    # Race detection (highest priority) - enhanced keywords
    race_keywords = [
        'race', 'marathon', 'half marathon', '10k', '5k', 'parkrun', 'competition', 
        'event', 'championship', 'triathlon', 'ultra', 'trail race', 'road race',
        'time trial', 'tt', 'fun run', 'charity run'
    ]
    if any(keyword in full_text for keyword in race_keywords):
        return 'Race'
    
    # Workout detection - enhanced with intensity indicators
    workout_keywords = [
        'tempo', 'interval', 'track', 'speed', 'fartlek', 'threshold', 'workout',
        'repeats', 'splits', 'vo2', 'lactate', 'hill repeats', 'progression',
        'build', 'negative split', 'pyramid', 'ladder'
    ]
    if any(keyword in full_text for keyword in workout_keywords):
        return 'Workout'
    
    # Enhanced workout detection using pace analysis
    if pace_minutes and distance > 3:  # Only for runs > 3km
        # If pace is significantly faster than typical easy pace (< 5:30/km), likely a workout
        if pace_minutes < 5.5:  # Less than 5:30/km
            return 'Workout'
    
    # Long run detection - enhanced criteria
    long_run_keywords = ['long', 'lsd', 'endurance', 'marathon pace', 'mp']
    distance_threshold = 15  # km
    
    # More nuanced long run detection
    if any(keyword in full_text for keyword in long_run_keywords):
        return 'Long Run'
    elif distance > distance_threshold:
        return 'Long Run'
    elif distance > 12 and pace_minutes and pace_minutes > 6.0:  # >12km and slower than 6:00/km
        return 'Long Run'
    
    # Commute detection
    commute_keywords = ['commute', 'work', 'office', 'home', 'to work', 'from work']
    if any(keyword in full_text for keyword in commute_keywords):
        return 'Commute'
    
    # Recovery run detection
    recovery_keywords = ['recovery', 'easy', 'shakeout', 'cool down', 'warm up']
    if any(keyword in full_text for keyword in recovery_keywords):
        return 'Recovery'
    
    # Trail run detection (could be separate category)
    trail_keywords = ['trail', 'hiking', 'mountain', 'hill', 'forest', 'nature']
    if any(keyword in full_text for keyword in trail_keywords):
        # Check if it's also a race or long run
        if distance > 15:
            return 'Long Run'
        return 'Trail Run'
    
    return 'Default'


def get_workout_type_style(workout_type):
    """Get color and symbol for workout type"""
    styles = {
        'Race': {'color': '#ef4444', 'symbol': 'star', 'size': 12},
        'Workout': {'color': '#f97316', 'symbol': 'diamond', 'size': 10},
        'Long Run': {'color': '#3b82f6', 'symbol': 'circle', 'size': 8},
        'Trail Run': {'color': '#8b5cf6', 'symbol': 'triangle-up', 'size': 8},
        'Recovery': {'color': '#06b6d4', 'symbol': 'circle-open', 'size': 8},
        'Commute': {'color': '#10b981', 'symbol': 'square', 'size': 8},
        'Default': {'color': '#6b7280', 'symbol': 'circle', 'size': 8}
    }
    return styles.get(workout_type, styles['Default'])


def preprocess_dataframe(df):
    """Preprocess the dataframe with all necessary data transformations"""
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Distance (km)'] = pd.to_numeric(df['Distance (km)'], errors='coerce')
    df['moving_time_minutes'] = df['Moving Time'].apply(parse_time_to_minutes)
    
    # Parse pace data (handles both min:sec and decimal formats)
    df['pace_minutes'] = df['Pace (min/km)'].apply(parse_pace_to_minutes)
    
    df['Avg HR'] = pd.to_numeric(df['Avg HR'], errors='coerce')
    df['Elevation Gain'] = pd.to_numeric(df['Elevation Gain'], errors='coerce')
    
    # Filter out invalid data
    df = df[df['Distance (km)'] > 0]
    
    return df


def filter_data_by_time_period(df, time_period, today):
    """Filter dataframe based on time period"""
    if time_period:
        cutoff_date = today - timedelta(days=time_period)
        return df[df['Date'] >= cutoff_date]
    return df


def calculate_key_metrics(df_filtered, time_period, today, df_full):
    """Calculate all key metrics for the dashboard"""
    total_distance = df_filtered['Distance (km)'].sum()
    total_runs = len(df_filtered)
    total_time = df_filtered['moving_time_minutes'].sum()
    avg_distance = df_filtered['Distance (km)'].mean()
    avg_pace_minutes = df_filtered['pace_minutes'].mean()
    avg_hr = df_filtered['Avg HR'].mean()
    total_elevation = df_filtered['Elevation Gain'].sum()
    training_load = calculate_training_load_score(df_filtered)
    
    # Calculate previous period for comparison
    distance_change = 0
    runs_change = 0
    
    if time_period:
        cutoff_date = today - timedelta(days=time_period)
        prev_start = cutoff_date - timedelta(days=time_period)
        prev_end = cutoff_date
        df_prev = df_full[(df_full['Date'] >= prev_start) & (df_full['Date'] < prev_end)]
        
        prev_distance = df_prev['Distance (km)'].sum() if not df_prev.empty else 0
        prev_runs = len(df_prev)
        
        distance_change = ((total_distance - prev_distance) / prev_distance * 100) if prev_distance > 0 else 0
        runs_change = ((total_runs - prev_runs) / prev_runs * 100) if prev_runs > 0 else 0
    
    return {
        'total_distance': total_distance,
        'total_runs': total_runs,
        'total_time': total_time,
        'avg_distance': avg_distance,
        'avg_pace_minutes': avg_pace_minutes,
        'avg_hr': avg_hr,
        'total_elevation': total_elevation,
        'training_load': training_load,
        'distance_change': distance_change,
        'runs_change': runs_change
    }


def aggregate_data_by_time(df, time_aggregation, value_column, agg_method='sum'):
    """Aggregate data based on time aggregation setting"""
    df_agg = df.copy()
    
    if time_aggregation == "daily":
        if agg_method == 'sum':
            df_plot = df_agg.groupby('Date')[value_column].sum().reset_index()
        else:
            df_plot = df_agg.groupby('Date')[value_column].mean().reset_index()
        x_title = "Date"
        hover_template = f'<b>%{{y:.1f}}</b><br>%{{x}}<extra></extra>'
    elif time_aggregation == "weekly":
        df_agg['Week'] = df_agg['Date'].dt.to_period('W').dt.start_time
        if agg_method == 'sum':
            df_plot = df_agg.groupby('Week')[value_column].sum().reset_index()
        else:
            df_plot = df_agg.groupby('Week')[value_column].mean().reset_index()
        df_plot.rename(columns={'Week': 'Date'}, inplace=True)
        x_title = "Week"
        hover_template = f'<b>%{{y:.1f}}</b><br>Week of %{{x}}<extra></extra>'
    elif time_aggregation == "monthly":
        df_agg['Month'] = df_agg['Date'].dt.to_period('M').dt.start_time
        if agg_method == 'sum':
            df_plot = df_agg.groupby('Month')[value_column].sum().reset_index()
        else:
            df_plot = df_agg.groupby('Month')[value_column].mean().reset_index()
        df_plot.rename(columns={'Month': 'Date'}, inplace=True)
        x_title = "Month"
        hover_template = f'<b>%{{y:.1f}}</b><br>%{{x|%B %Y}}<extra></extra>'
    else:  # yearly
        df_agg['Year'] = df_agg['Date'].dt.year
        if agg_method == 'sum':
            df_plot = df_agg.groupby('Year')[value_column].sum().reset_index()
        else:
            df_plot = df_agg.groupby('Year')[value_column].mean().reset_index()
        df_plot['Date'] = pd.to_datetime(df_plot['Year'], format='%Y')
        x_title = "Year"
        hover_template = f'<b>%{{y:.1f}}</b><br>%{{x|%Y}}<extra></extra>'
    
    return df_plot, x_title, hover_template 