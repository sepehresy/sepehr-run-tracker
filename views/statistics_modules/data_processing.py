"""
Data processing utilities for running statistics
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def parse_time_to_minutes(time_str):
    """Convert time string (HH:MM:SS or MM:SS) to minutes"""
    if pd.isna(time_str) or time_str == '' or time_str == '-':
        return None
    try:
        if isinstance(time_str, str):
            parts = time_str.split(':')
            if len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
            elif len(parts) == 2:  # MM:SS
                return int(parts[0]) + int(parts[1]) / 60
        return float(time_str)
    except:
        return None


def parse_pace_to_seconds(pace_str):
    """Convert pace string (MM:SS) to seconds per km"""
    if pd.isna(pace_str) or pace_str == '' or pace_str == '-':
        return None
    try:
        if isinstance(pace_str, str) and ':' in pace_str:
            parts = pace_str.split(':')
            return int(parts[0]) * 60 + int(parts[1])
        return float(pace_str) * 60  # Assume it's in minutes
    except:
        return None


def format_pace_from_seconds(seconds):
    """Convert seconds per km back to MM:SS format"""
    if pd.isna(seconds) or seconds is None:
        return "-"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


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
    df_calc['pace_seconds'] = df_calc['Pace (min/km)'].apply(parse_pace_to_seconds)
    
    # Normalize pace to intensity (faster = higher intensity)
    if df_calc['pace_seconds'].notna().any():
        max_pace = df_calc['pace_seconds'].max()
        df_calc['intensity'] = (max_pace - df_calc['pace_seconds']) / max_pace + 0.5
        df_calc['intensity'] = df_calc['intensity'].fillna(0.7)  # Default intensity
    else:
        df_calc['intensity'] = 0.7
    
    df_calc['load'] = df_calc['Distance (km)'] * df_calc['intensity']
    return df_calc['load'].sum()


def detect_workout_type(row):
    """Detect workout type based on activity name and characteristics"""
    # Try different possible column names for activity name
    activity_name = ''
    for col_name in ['Name', 'Activity Name', 'Activity', 'name']:
        if col_name in row and not pd.isna(row.get(col_name, '')):
            activity_name = str(row[col_name]).lower()
            break
    
    # If no activity name found, use distance-based detection only
    if not activity_name:
        distance = row.get('Distance (km)', 0)
        if distance > 15:
            return 'Long Run'
        return 'Default'
    
    # Race detection (highest priority)
    race_keywords = ['race', 'marathon', 'half marathon', '10k', '5k', 'parkrun', 'competition', 'event']
    if any(keyword in activity_name for keyword in race_keywords):
        return 'Race'
    
    # Workout detection
    workout_keywords = ['tempo', 'interval', 'track', 'speed', 'fartlek', 'threshold', 'workout']
    if any(keyword in activity_name for keyword in workout_keywords):
        return 'Workout'
    
    # Long run detection
    long_run_keywords = ['long', 'lsd', 'endurance']
    distance = row.get('Distance (km)', 0)
    if any(keyword in activity_name for keyword in long_run_keywords) or distance > 15:
        return 'Long Run'
    
    # Commute detection
    commute_keywords = ['commute', 'work', 'office', 'home']
    if any(keyword in activity_name for keyword in commute_keywords):
        return 'Commute'
    
    return 'Default'


def get_workout_type_style(workout_type):
    """Get color and symbol for workout type"""
    styles = {
        'Race': {'color': '#ef4444', 'symbol': 'star', 'size': 12},
        'Workout': {'color': '#f97316', 'symbol': 'diamond', 'size': 10},
        'Long Run': {'color': '#3b82f6', 'symbol': 'circle', 'size': 8},
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
    df['pace_seconds'] = df['Pace (min/km)'].apply(parse_pace_to_seconds)
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
    avg_pace_seconds = df_filtered['pace_seconds'].mean()
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
        'avg_pace_seconds': avg_pace_seconds,
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