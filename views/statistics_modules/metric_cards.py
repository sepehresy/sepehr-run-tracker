"""
Metric cards and trend indicators for running statistics
"""
import pandas as pd
from .data_processing import format_time_from_minutes


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


def create_metric_card(icon, value, label, unit="", change=None, subtitle="", goal_progress=None):
    """Create an enhanced metric card with icons, trends, and optional goal progress"""
    
    # Format the change indicator
    change_html = ""
    if change is not None:
        trend_icon, trend_class, trend_desc = get_trend_indicator(change)
        change_html = f"""
        <div class="metric-change {trend_class}">
            <span class="trend-icon">{trend_icon}</span>
            <span class="trend-text">{abs(change):.1f}% vs prev period</span>
            <div class="trend-tooltip">{trend_desc}</div>
        </div>
        """
    
    # Format goal progress bar
    goal_html = ""
    if goal_progress is not None:
        progress_percent = min(100, goal_progress)
        goal_html = f"""
        <div class="goal-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress_percent}%;"></div>
            </div>
            <div class="progress-text">{progress_percent:.0f}% of goal</div>
        </div>
        """
    
    return f"""
    <div class="metric-card enhanced">
        <div class="metric-header">
            <span class="metric-icon">{icon}</span>
            <div class="metric-main">
                <div class="metric-value-container">
                    <span class="metric-value">{value}</span>
                    <span class="metric-unit">{unit}</span>
                </div>
                <div class="metric-label">{label}</div>
                {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
            </div>
        </div>
        {goal_html}
        {change_html}
    </div>
    """


def create_all_metric_cards(metrics, time_period):
    """Create all 8 metric cards with the calculated metrics"""
    total_distance = metrics['total_distance']
    total_runs = metrics['total_runs']
    total_time = metrics['total_time']
    avg_distance = metrics['avg_distance']
    avg_pace_seconds = metrics['avg_pace_seconds']
    avg_hr = metrics['avg_hr']
    total_elevation = metrics['total_elevation']
    training_load = metrics['training_load']
    distance_change = metrics['distance_change']
    runs_change = metrics['runs_change']
    
    # Calculate derived values
    total_hours = total_time / 60
    pace_minutes = int(avg_pace_seconds // 60) if not pd.isna(avg_pace_seconds) else 0
    pace_seconds_val = int(avg_pace_seconds % 60) if not pd.isna(avg_pace_seconds) else 0
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
    
    # Card 1: Total Distance
    card1_html = f"""
    <div class="metric-card">
        <span class="metric-icon">🏃‍♂️</span>
        <div>
            <div class="metric-value">{total_distance:.1f}<span class="metric-unit">km</span></div>
            <div class="metric-label">Total Distance</div>
            <div class="metric-subtitle">{total_distance/total_runs if total_runs > 0 else 0:.1f} km avg per run</div>
        </div>
        <div class="metric-change {'positive' if distance_change > 0 else 'negative' if distance_change < 0 else 'neutral'}">
            {'↗' if distance_change > 0 else '↘' if distance_change < 0 else '→'} {abs(distance_change):.1f}%
        </div>
    </div>
    """
    
    # Card 2: Total Runs
    card2_html = f"""
    <div class="metric-card">
        <span class="metric-icon">📊</span>
        <div>
            <div class="metric-value">{total_runs}<span class="metric-unit">runs</span></div>
            <div class="metric-label">Total Runs</div>
            <div class="metric-subtitle">{total_runs/(time_period/7) if time_period else 0:.1f} per week</div>
        </div>
        <div class="metric-change {'positive' if runs_change > 0 else 'negative' if runs_change < 0 else 'neutral'}">
            {'↗' if runs_change > 0 else '↘' if runs_change < 0 else '→'} {abs(runs_change):.1f}%
        </div>
    </div>
    """
    
    # Card 3: Total Time
    time_display = f"{total_hours:.1f}" if total_hours >= 1 else f"{total_time:.0f}"
    time_unit = "hrs" if total_hours >= 1 else "min"
    
    card3_html = f"""
    <div class="metric-card">
        <span class="metric-icon">⏱️</span>
        <div>
            <div class="metric-value">{time_display}<span class="metric-unit">{time_unit}</span></div>
            <div class="metric-label">Total Time</div>
            <div class="metric-subtitle">{format_time_from_minutes(total_time/total_runs) if total_runs > 0 else "-"} avg per run</div>
        </div>
    </div>
    """
    
    # Card 4: Average Pace
    card4_html = f"""
    <div class="metric-card">
        <span class="metric-icon">⚡</span>
        <div>
            <div class="metric-value">{pace_minutes}:{pace_seconds_val:02d}<span class="metric-unit">min/km</span></div>
            <div class="metric-label">Average Pace</div>
            <div class="metric-subtitle">per kilometer</div>
        </div>
    </div>
    """
    
    # Card 5: Average Distance
    card5_html = f"""
    <div class="metric-card">
        <span class="metric-icon">📏</span>
        <div>
            <div class="metric-value">{avg_distance:.1f}<span class="metric-unit">km</span></div>
            <div class="metric-label">Avg Distance</div>
            <div class="metric-subtitle">per run</div>
        </div>
    </div>
    """
    
    # Card 6: Heart Rate
    if not pd.isna(avg_hr):
        card6_html = f"""
        <div class="metric-card">
            <span class="metric-icon">❤️</span>
            <div>
                <div class="metric-value">{avg_hr:.0f}<span class="metric-unit">bpm</span></div>
                <div class="metric-label">Avg Heart Rate</div>
                <div class="metric-subtitle">{hr_zone}</div>
            </div>
        </div>
        """
    else:
        card6_html = f"""
        <div class="metric-card" style="opacity: 0.6;">
            <span class="metric-icon">❤️</span>
            <div>
                <div class="metric-value">-<span class="metric-unit"></span></div>
                <div class="metric-label">Avg Heart Rate</div>
                <div class="metric-subtitle">No HR data</div>
            </div>
        </div>
        """
    
    # Card 7: Training Load
    card7_html = f"""
    <div class="metric-card">
        <span class="metric-icon">🔥</span>
        <div>
            <div class="metric-value">{training_load:.0f}<span class="metric-unit">pts</span></div>
            <div class="metric-label">Training Load</div>
            <div class="metric-subtitle">{load_per_week:.0f} per week</div>
        </div>
    </div>
    """
    
    # Card 8: Elevation Gain
    if not pd.isna(total_elevation) and total_elevation > 0:
        card8_html = f"""
        <div class="metric-card">
            <span class="metric-icon">⛰️</span>
            <div>
                <div class="metric-value">{total_elevation:,.0f}<span class="metric-unit">m</span></div>
                <div class="metric-label">Elevation Gain</div>
                <div class="metric-subtitle">{total_elevation/total_runs if total_runs > 0 else 0:.0f}m avg per run</div>
            </div>
        </div>
        """
    else:
        card8_html = f"""
        <div class="metric-card" style="opacity: 0.6;">
            <span class="metric-icon">⛰️</span>
            <div>
                <div class="metric-value">-<span class="metric-unit"></span></div>
                <div class="metric-label">Elevation Gain</div>
                <div class="metric-subtitle">No elevation data</div>
            </div>
        </div>
        """
    
    return [card1_html, card2_html, card3_html, card4_html, 
            card5_html, card6_html, card7_html, card8_html] 