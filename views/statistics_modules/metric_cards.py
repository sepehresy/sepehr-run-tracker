"""
Metric cards and trend indicators for running statistics
"""
import pandas as pd
from .data_processing import format_time_from_minutes, format_pace_to_min_sec, format_number_with_commas, detect_workout_type


def get_trend_indicator(change):
    """Get trend indicator with appropriate color and icon"""
    if change > 5:
        return "📈", "positive", "Strong improvement"
    elif change > 0:
        return "↗️", "positive", "Improving"
    elif change < -5:
        return "📉", "negative", "Significant decline"
    elif change < 0:
        return "↘️", "negative", "Declining"
    else:
        return "➡️", "neutral", "Stable"


def create_metric_card(title, value, change=None, icon="📊", color="#3b82f6"):
    """Create a metric card with optional change indicator"""
    change_html = ""
    if change is not None:
        change_color = "#10b981" if change >= 0 else "#ef4444"
        change_symbol = "↗" if change >= 0 else "↘"
        change_html = f'<div class="metric-change" style="color: {change_color};">{change_symbol} {abs(change):.1f}%</div>'
    
    return f"""<div class="metric-card" style="border-left: 4px solid {color};"><div class="metric-icon">{icon}</div><div class="metric-content"><div class="metric-title">{title}</div><div class="metric-value">{value}</div>{change_html}</div></div>"""


def create_compact_summary_card(metrics, time_period):
    """Create a compact summary card for mobile devices"""
    total_distance = metrics['total_distance']
    total_runs = metrics['total_runs']
    total_time = metrics['total_time']
    avg_distance = metrics['avg_distance']
    avg_pace_minutes = metrics['avg_pace_minutes']
    avg_hr = metrics['avg_hr']
    total_elevation = metrics['total_elevation']
    training_load = metrics['training_load']
    distance_change = metrics['distance_change']
    runs_change = metrics['runs_change']
    
    # Format values for compact display
    distance_value = f"{format_number_with_commas(total_distance)} km"
    runs_value = f"{total_runs}"
    time_value = format_time_from_minutes(total_time)
    pace_value = format_pace_to_min_sec(avg_pace_minutes)
    avg_distance_value = f"{avg_distance:.1f} km"
    hr_value = f"{avg_hr:.0f} bpm" if avg_hr and not pd.isna(avg_hr) else "No data"
    load_value = f"{training_load:.0f}"
    elevation_value = f"{format_number_with_commas(total_elevation)} m"
    
    # Create period label
    period_label = f"Last {time_period} Days" if time_period else "All Time"
    
    return f"""<div class="metric-summary-card"><div style="text-align: center; margin-bottom: 1rem;"><h3 style="color: #f8fafc; margin: 0; font-size: 1.125rem; font-weight: 600;">📊 Running Summary ({period_label})</h3></div><div class="metric-summary-grid"><div class="metric-summary-item"><div class="metric-summary-icon">🏃‍♂️</div><div class="metric-summary-label">Distance</div><div class="metric-summary-value">{distance_value}</div></div><div class="metric-summary-item"><div class="metric-summary-icon">📊</div><div class="metric-summary-label">Runs</div><div class="metric-summary-value">{runs_value}</div></div><div class="metric-summary-item"><div class="metric-summary-icon">⏱️</div><div class="metric-summary-label">Time</div><div class="metric-summary-value">{time_value}</div></div><div class="metric-summary-item"><div class="metric-summary-icon">⚡</div><div class="metric-summary-label">Avg Pace</div><div class="metric-summary-value">{pace_value}</div></div><div class="metric-summary-item"><div class="metric-summary-icon">📏</div><div class="metric-summary-label">Avg Dist</div><div class="metric-summary-value">{avg_distance_value}</div></div><div class="metric-summary-item"><div class="metric-summary-icon">❤️</div><div class="metric-summary-label">Avg HR</div><div class="metric-summary-value">{hr_value}</div></div><div class="metric-summary-item"><div class="metric-summary-icon">🔥</div><div class="metric-summary-label">Load</div><div class="metric-summary-value">{load_value}</div></div><div class="metric-summary-item"><div class="metric-summary-icon">⛰️</div><div class="metric-summary-label">Elevation</div><div class="metric-summary-value">{elevation_value}</div></div></div></div>"""


def create_training_diversity_card(df_filtered):
    """Create a card showing training diversity"""
    if df_filtered.empty:
        return create_metric_card("Training Variety", "No data", icon="🎯", color="#8b5cf6")
    
    # Calculate workout type diversity
    df_with_types = df_filtered.copy()
    df_with_types['workout_type'] = df_with_types.apply(detect_workout_type, axis=1)
    workout_types = df_with_types['workout_type'].value_counts()
    
    # Calculate diversity score (number of different workout types)
    diversity_score = len(workout_types)
    total_runs = len(df_filtered)
    
    # Create a diversity description
    if diversity_score >= 5:
        diversity_text = f"Excellent ({diversity_score} types)"
        color = "#10b981"
    elif diversity_score >= 3:
        diversity_text = f"Good ({diversity_score} types)"
        color = "#3b82f6"
    elif diversity_score >= 2:
        diversity_text = f"Moderate ({diversity_score} types)"
        color = "#f59e0b"
    else:
        diversity_text = f"Limited ({diversity_score} type)"
        color = "#ef4444"
    
    return create_metric_card("Training Variety", diversity_text, icon="🎯", color=color)


def create_all_metric_cards(metrics, time_period):
    """Create all metric cards - compact for mobile, individual for desktop"""
    total_distance = metrics['total_distance']
    total_runs = metrics['total_runs']
    total_time = metrics['total_time']
    avg_distance = metrics['avg_distance']
    avg_pace_minutes = metrics['avg_pace_minutes']
    avg_hr = metrics['avg_hr']
    total_elevation = metrics['total_elevation']
    training_load = metrics['training_load']
    distance_change = metrics['distance_change']
    runs_change = metrics['runs_change']
    
    # Calculate derived values
    total_hours = total_time / 60
    load_per_week = training_load / (time_period / 7) if time_period else training_load
    
    # Determine HR zone
    hr_zone = ""
    if not pd.isna(avg_hr):
        if avg_hr < 120:
            hr_zone = "Recovery zone"
        elif avg_hr < 140:
            hr_zone = "Aerobic zone"
        elif avg_hr < 160:
            hr_zone = "Threshold zone"
        else:
            hr_zone = "VO2 Max zone"
    
    # Create compact summary card (shown on mobile)
    compact_card = create_compact_summary_card(metrics, time_period)
    
    # Card 1: Total Distance
    distance_value = f"{format_number_with_commas(total_distance)} km"
    card1_html = create_metric_card(
        "Total Distance", 
        distance_value, 
        distance_change,
        "🏃‍♂️", 
        "#3b82f6"
    )
    
    # Card 2: Total Runs
    runs_value = f"{total_runs}"
    card2_html = create_metric_card(
        "Total Runs", 
        runs_value, 
        runs_change,
        "📊", 
        "#10b981"
    )
    
    # Card 3: Total Time
    time_display = f"{total_hours:.1f}" if total_hours >= 1 else f"{total_time:.0f}"
    time_unit = "hrs" if total_hours >= 1 else "min"
    time_value = format_time_from_minutes(total_time)
    card3_html = create_metric_card(
        "Total Time", 
        time_value, 
        None,
        "⏱️", 
        "#f59e0b"
    )
    
    # Card 4: Average Pace
    pace_value = format_pace_to_min_sec(avg_pace_minutes)
    card4_html = create_metric_card(
        "Avg Pace", 
        pace_value, 
        None,
        "⚡", 
        "#ef4444"
    )
    
    # Card 5: Average Distance
    avg_distance_value = f"{avg_distance:.1f} km"
    card5_html = create_metric_card(
        "Avg Distance", 
        avg_distance_value, 
        None,
        "📏", 
        "#8b5cf6"
    )
    
    # Card 6: Heart Rate
    hr_value = f"{avg_hr:.0f} bpm" if avg_hr and not pd.isna(avg_hr) else "No data"
    card6_html = create_metric_card(
        "Avg Heart Rate", 
        hr_value, 
        None,
        "❤️", 
        "#f97316"
    )
    
    # Card 7: Training Load
    load_value = f"{training_load:.0f}"
    card7_html = create_metric_card(
        "Training Load", 
        load_value, 
        None,
        "🔥", 
        "#84cc16"
    )
    
    # Card 8: Elevation Gain
    elevation_value = f"{format_number_with_commas(total_elevation)} m"
    card8_html = create_metric_card(
        "Total Elevation", 
        elevation_value, 
        None,
        "⛰️", 
        "#06b6d4"
    )
    
    # Return compact card first (for mobile), then individual cards (for desktop)
    return [compact_card, card1_html, card2_html, card3_html, card4_html, 
            card5_html, card6_html, card7_html, card8_html] 