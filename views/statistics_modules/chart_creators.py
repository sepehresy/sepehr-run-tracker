"""
Chart creation utilities for running statistics
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from .data_processing import (
    aggregate_data_by_time, 
    format_pace_to_min_sec, 
    detect_workout_type, 
    get_workout_type_style
)

# Cache for workout type detection to improve performance
_workout_type_cache = {}

def get_cached_workout_type(row_hash, row):
    """Get workout type with caching for better performance"""
    if row_hash not in _workout_type_cache:
        _workout_type_cache[row_hash] = detect_workout_type(row)
    return _workout_type_cache[row_hash]

def clear_workout_type_cache():
    """Clear the workout type cache"""
    global _workout_type_cache
    _workout_type_cache = {}

def create_distance_chart(df_filtered, time_aggregation):
    """Create distance over time chart"""
    if df_filtered.empty:
        return None
    
    df_plot, x_title, hover_template = aggregate_data_by_time(
        df_filtered, time_aggregation, 'Distance (km)', 'sum'
    )
    
    if df_plot.empty:
        return None
    
    if time_aggregation == "daily":
        # Use line chart for daily data
        fig = px.line(
            df_plot.sort_values('Date'), 
            x='Date', 
            y='Distance (km)',
            title="",
            color_discrete_sequence=['#3b82f6'],
            hover_data={'Distance (km)': ':.1f'}
        )
        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8, color='#3b82f6'),
            hovertemplate=hover_template
        )
    else:
        # Use bar chart for weekly, monthly, yearly data
        fig = px.bar(
            df_plot.sort_values('Date'), 
            x='Date', 
            y='Distance (km)',
            title="",
            color_discrete_sequence=['#3b82f6'],
            hover_data={'Distance (km)': ':.1f'}
        )
        fig.update_traces(hovertemplate=hover_template)
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6', 
            gridwidth=1,
            title=x_title,
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6', 
            gridwidth=1,
            title="Distance (km)",
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=350,
        hovermode='x unified'
    )
    
    return fig


def create_pace_trend_chart(df_filtered, time_aggregation):
    """Create pace trends chart"""
    pace_data = df_filtered.dropna(subset=['pace_minutes']).copy()
    if pace_data.empty:
        return None
    
    # Filter out unrealistic values (pace is already in min/km)
    pace_data = pace_data[pace_data['pace_minutes'] <= 12]
    
    if pace_data.empty:
        return None
    
    df_plot, x_title, hover_template = aggregate_data_by_time(
        pace_data, time_aggregation, 'pace_minutes', 'mean'
    )
    
    if time_aggregation == "daily":
        # Use line chart for daily data
        fig = px.line(
            df_plot.sort_values('Date'),
            x='Date',
            y='pace_minutes',
            title="",
            color_discrete_sequence=['#8b5cf6']
        )
        fig.update_traces(
            line=dict(width=3),
            hovertemplate='<b>%{customdata}</b><br>%{x}<extra></extra>',
            customdata=[format_pace_to_min_sec(pace) for pace in df_plot['pace_minutes']]
        )
    else:
        # Use bar chart for weekly, monthly, yearly data
        fig = px.bar(
            df_plot.sort_values('Date'),
            x='Date',
            y='pace_minutes',
            title="",
            color_discrete_sequence=['#8b5cf6']
        )
        fig.update_traces(
            hovertemplate='<b>%{customdata}</b><br>' + x_title.lower() + ' %{x}<extra></extra>',
            customdata=[format_pace_to_min_sec(pace) for pace in df_plot['pace_minutes']]
        )
    
    # Create custom y-axis tick labels in min:sec format
    y_tick_vals = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    y_tick_text = [format_pace_to_min_sec(val) for val in y_tick_vals]
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title=x_title,
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Pace",
            title_font=dict(size=14, color="#6b7280"),
            range=[3, 12],  # Set reasonable y-axis range for running paces
            tickvals=y_tick_vals,
            ticktext=y_tick_text
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    
    return fig


def create_heart_rate_chart(df_filtered, time_aggregation):
    """Create heart rate trends chart"""
    hr_data = df_filtered.dropna(subset=['Avg HR'])
    if hr_data.empty:
        return None
    
    df_plot, x_title, hover_template = aggregate_data_by_time(
        hr_data, time_aggregation, 'Avg HR', 'mean'
    )
    
    if time_aggregation == "daily":
        # Use line chart for daily data
        fig = px.line(
            df_plot.sort_values('Date'),
            x='Date',
            y='Avg HR',
            title="",
            color_discrete_sequence=['#ef4444']
        )
        fig.update_traces(
            line=dict(width=3),
            hovertemplate='<b>%{y:.0f} bpm</b><br>%{x}<extra></extra>'
        )
    else:
        # Use bar chart for weekly, monthly, yearly data
        fig = px.bar(
            df_plot.sort_values('Date'),
            x='Date',
            y='Avg HR',
            title="",
            color_discrete_sequence=['#ef4444']
        )
        fig.update_traces(
            hovertemplate=hover_template.replace(':.1f', ':.0f') + ' bpm'
        )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title=x_title,
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Heart Rate (bpm)",
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    
    return fig


def create_pace_distribution_chart(df_filtered):
    """Create pace distribution histogram"""
    pace_data = df_filtered['pace_minutes'].dropna()
    if pace_data.empty:
        return None
    
    # Filter out unrealistic values (pace is already in min/km)
    pace_minutes = pace_data[pace_data <= 12]  # Filter out pace above 12 min/km
    
    if pace_minutes.empty:
        return None
    
    fig = px.histogram(
        x=pace_minutes,
        nbins=20,
        title="",
        color_discrete_sequence=['#8b5cf6']
    )
    
    # Create custom x-axis tick labels in min:sec format
    x_tick_vals = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    x_tick_text = [format_pace_to_min_sec(val) for val in x_tick_vals]
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            title="Pace", 
            showgrid=True, 
            gridcolor='#f3f4f6',
            title_font=dict(size=14, color="#6b7280"),
            range=[3, 12],  # Set reasonable x-axis range for running paces
            tickvals=x_tick_vals,
            ticktext=x_tick_text
        ),
        yaxis=dict(
            title="Frequency", 
            showgrid=True, 
            gridcolor='#f3f4f6',
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    
    return fig


def create_cadence_chart(df_filtered, time_aggregation):
    """Create cadence trends chart"""
    cadence_data = df_filtered.dropna(subset=['Cadence']).copy()
    if cadence_data.empty:
        return None
    
    # Convert cadence to numeric and filter out unrealistic values
    cadence_data['Cadence'] = pd.to_numeric(cadence_data['Cadence'], errors='coerce')
    cadence_data = cadence_data.dropna(subset=['Cadence'])
    cadence_data = cadence_data[(cadence_data['Cadence'] >= 120) & (cadence_data['Cadence'] <= 220)]
    
    if cadence_data.empty:
        return None
    
    df_plot, x_title, hover_template = aggregate_data_by_time(
        cadence_data, time_aggregation, 'Cadence', 'mean'
    )
    
    if time_aggregation == "daily":
        # Use line chart for daily data
        fig = px.line(
            df_plot.sort_values('Date'),
            x='Date',
            y='Cadence',
            title="",
            color_discrete_sequence=['#f59e0b']
        )
        fig.update_traces(
            line=dict(width=3),
            hovertemplate='<b>%{y:.0f} spm</b><br>%{x}<extra></extra>'
        )
    else:
        # Use bar chart for weekly, monthly, yearly data
        fig = px.bar(
            df_plot.sort_values('Date'),
            x='Date',
            y='Cadence',
            title="",
            color_discrete_sequence=['#f59e0b']
        )
        fig.update_traces(
            hovertemplate=hover_template.replace(':.1f', ':.0f') + ' spm'
        )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title=x_title,
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Cadence (spm)",
            title_font=dict(size=14, color="#6b7280"),
            range=[120, 220]  # Set reasonable y-axis range for cadence
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    
    return fig


def create_elevation_chart(df_filtered, time_aggregation):
    """Create elevation gain trends chart"""
    elevation_data = df_filtered.dropna(subset=['Elevation Gain']).copy()
    if elevation_data.empty:
        return None
    
    # Convert elevation to numeric and filter out negative values
    elevation_data['Elevation Gain'] = pd.to_numeric(elevation_data['Elevation Gain'], errors='coerce')
    elevation_data = elevation_data.dropna(subset=['Elevation Gain'])
    elevation_data = elevation_data[elevation_data['Elevation Gain'] >= 0]  # Filter out negative values
    
    if elevation_data.empty:
        return None
    
    df_plot, x_title, hover_template = aggregate_data_by_time(
        elevation_data, time_aggregation, 'Elevation Gain', 'sum'
    )
    
    if time_aggregation == "daily":
        # Use line chart for daily data
        fig = px.line(
            df_plot.sort_values('Date'),
            x='Date',
            y='Elevation Gain',
            title="",
            color_discrete_sequence=['#10b981']
        )
        fig.update_traces(
            line=dict(width=3),
            hovertemplate='<b>%{y:.0f} m</b><br>%{x}<extra></extra>'
        )
    else:
        # Use bar chart for weekly, monthly, yearly data
        fig = px.bar(
            df_plot.sort_values('Date'),
            x='Date',
            y='Elevation Gain',
            title="",
            color_discrete_sequence=['#10b981']
        )
        fig.update_traces(
            hovertemplate=hover_template.replace(':.1f', ':.0f') + ' m'
        )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title=x_title,
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Elevation Gain (m)",
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    
    return fig


def create_elapsed_time_chart(df_filtered, time_aggregation):
    """Create elapsed time trends chart"""
    time_data = df_filtered.dropna(subset=['moving_time_minutes']).copy()
    if time_data.empty:
        return None
    
    df_plot, x_title, hover_template = aggregate_data_by_time(
        time_data, time_aggregation, 'moving_time_minutes', 'sum'
    )
    
    # Convert minutes to hours for better readability in display
    df_plot['time_hours'] = df_plot['moving_time_minutes'] / 60
    
    if time_aggregation == "daily":
        # Use line chart for daily data
        fig = px.line(
            df_plot.sort_values('Date'),
            x='Date',
            y='time_hours',
            title="",
            color_discrete_sequence=['#06b6d4']
        )
        fig.update_traces(
            line=dict(width=3),
            hovertemplate='<b>%{y:.1f} hrs</b><br>%{x}<extra></extra>'
        )
    else:
        # Use bar chart for weekly, monthly, yearly data
        fig = px.bar(
            df_plot.sort_values('Date'),
            x='Date',
            y='time_hours',
            title="",
            color_discrete_sequence=['#06b6d4']
        )
        fig.update_traces(
            hovertemplate='<b>%{y:.1f} hrs</b><br>' + x_title.lower() + ' %{x}<extra></extra>'
        )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title=x_title,
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Elapsed Time (hours)",
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    
    return fig


def create_run_frequency_chart(df_filtered):
    """Create run frequency by day chart"""
    # Day of week analysis
    df_dow = df_filtered.copy()
    df_dow['DayOfWeek'] = df_dow['Date'].dt.day_name()
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_counts = df_dow['DayOfWeek'].value_counts().reindex(dow_order, fill_value=0)
    
    fig = px.bar(
        x=dow_counts.index,
        y=dow_counts.values,
        title="",
        color_discrete_sequence=['#10b981']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Day of Week",
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Number of Runs",
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    fig.update_traces(
        hovertemplate='<b>%{y} runs</b><br>%{x}<extra></extra>'
    )
    
    return fig


def create_yearly_cumulative_chart(df, today):
    """Create yearly cumulative distance chart"""
    # Create yearly cumulative data
    df_yearly = df.copy()  # Use full dataset for yearly view
    df_yearly['Year'] = df_yearly['Date'].dt.year
    
    # Group by year and calculate cumulative distance by day of year
    yearly_data = []
    for year in sorted(df_yearly['Year'].unique()):
        year_df = df_yearly[df_yearly['Year'] == year].copy()
        year_df['DayOfYear'] = year_df['Date'].dt.dayofyear
        year_df = year_df.sort_values('DayOfYear')
        year_df['CumulativeDistance'] = year_df['Distance (km)'].cumsum()
        
        # Create a complete day range for the year
        max_day = 366 if year % 4 == 0 else 365  # Handle leap years
        complete_days = pd.DataFrame({
            'DayOfYear': range(1, max_day + 1),
            'Year': year
        })
        
        # Merge and forward fill cumulative distance
        year_complete = complete_days.merge(
            year_df[['DayOfYear', 'CumulativeDistance']], 
            on='DayOfYear', 
            how='left'
        )
        year_complete['CumulativeDistance'] = year_complete['CumulativeDistance'].ffill().fillna(0)
        yearly_data.append(year_complete)
    
    if not yearly_data:
        return None
    
    # Create the plot
    fig = go.Figure()
    
    # Color palette for different years
    colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16']
    
    # Get current date info
    current_year = today.year
    current_day_of_year = today.timetuple().tm_yday
    
    for i, year_data in enumerate(yearly_data):
        year = year_data['Year'].iloc[0]
        color = colors[i % len(colors)]
        
        if year == current_year:
            # For current year, split into past (solid) and future (dashed)
            past_data = year_data[year_data['DayOfYear'] <= current_day_of_year]
            future_data = year_data[year_data['DayOfYear'] > current_day_of_year]
            
            # Add past data (solid line)
            if not past_data.empty:
                fig.add_trace(go.Scatter(
                    x=past_data['DayOfYear'],
                    y=past_data['CumulativeDistance'],
                    mode='lines',
                    name=f'{year} (actual)',
                    line=dict(width=4, color=color),
                    hovertemplate=f'<b>{year}</b><br>Day %{{x}}<br><b>%{{y:.1f}} km total</b><extra></extra>'
                ))
            
            # Add future projection (dashed line)
            if not future_data.empty and not past_data.empty:
                # Connect the last actual point to future projection
                last_actual = past_data.iloc[-1]['CumulativeDistance']
                future_data_copy = future_data.copy()
                future_data_copy['CumulativeDistance'] = last_actual  # Flat projection
                
                fig.add_trace(go.Scatter(
                    x=future_data_copy['DayOfYear'],
                    y=future_data_copy['CumulativeDistance'],
                    mode='lines',
                    name=f'{year} (projection)',
                    line=dict(width=3, color=color, dash='dash'),
                    hovertemplate=f'<b>{year} (projected)</b><br>Day %{{x}}<br><b>%{{y:.1f}} km total</b><extra></extra>',
                    opacity=0.6
                ))
        else:
            # For other years, show complete data
            fig.add_trace(go.Scatter(
                x=year_data['DayOfYear'],
                y=year_data['CumulativeDistance'],
                mode='lines',
                name=f'{year}',
                line=dict(width=3, color=color),
                hovertemplate=f'<b>{year}</b><br>Day %{{x}}<br><b>%{{y:.1f}} km total</b><extra></extra>'
            ))
    
    # Add vertical line for "today"
    if current_year in [year_data['Year'].iloc[0] for year_data in yearly_data]:
        max_distance = max([year_data['CumulativeDistance'].max() for year_data in yearly_data])
        fig.add_vline(
            x=current_day_of_year,
            line=dict(color="red", width=3, dash="solid"),
            annotation=dict(
                text="Today",
                textangle=90,
                font=dict(color="red", size=12, family="Inter"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
        )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            title="Day of Year",
            showgrid=True,
            gridcolor='#f3f4f6',
            title_font=dict(size=14, color="#6b7280"),
            range=[1, 365]
        ),
        yaxis=dict(
            title="Cumulative Distance (km)",
            showgrid=True,
            gridcolor='#f3f4f6',
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_correlation_chart(df_filtered, x_col, y_col, title, x_label, y_label, color='#3b82f6'):
    """Create a correlation scatter plot with workout type styling"""
    valid_data = df_filtered.dropna(subset=[x_col, y_col])
    if valid_data.empty or len(valid_data) <= 3:
        return None
    
    # Add workout type detection
    valid_data = valid_data.copy()
    valid_data['workout_type'] = valid_data.apply(detect_workout_type, axis=1)
    
    # For pace data, filter out unrealistic values (pace is already in min/km)
    if 'pace' in x_col.lower() and 'minutes' in x_col.lower():
        valid_data = valid_data[valid_data[x_col] <= 12]
        x_label = "Pace"
    
    if 'pace' in y_col.lower() and 'minutes' in y_col.lower():
        valid_data = valid_data[valid_data[y_col] <= 12]
        y_label = "Pace"
    
    if valid_data.empty or len(valid_data) <= 3:
        return None
    
    fig = go.Figure()
    
    # Add traces for each workout type
    for workout_type in valid_data['workout_type'].unique():
        type_data = valid_data[valid_data['workout_type'] == workout_type]
        style = get_workout_type_style(workout_type)
        
        fig.add_trace(go.Scatter(
            x=type_data[x_col],
            y=type_data[y_col],
            mode='markers',
            name=workout_type,
            marker=dict(
                color=style['color'],
                size=style['size'],
                symbol=style['symbol'],
                line=dict(width=1, color='white')
            ),
            hovertemplate=f'<b>%{{text}}</b><br><b>{x_label}: %{{customdata[0]}}</b><br><b>{y_label}: %{{customdata[1]}}</b><extra></extra>',
            customdata=[[
                format_pace_to_min_sec(x) if 'pace' in x_label.lower() else f"{x:.1f}",
                format_pace_to_min_sec(y) if 'pace' in y_label.lower() else f"{y:.1f}"
            ] for x, y in zip(type_data[x_col], type_data[y_col])],
            text=[workout_type] * len(type_data)
        ))
    
    # Create custom tick labels for pace axes
    pace_tick_vals = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    pace_tick_text = [format_pace_to_min_sec(val) for val in pace_tick_vals]
    
    xaxis_config = dict(
        title=x_label, 
        showgrid=True, 
        gridcolor='#f3f4f6',
        title_font=dict(size=14, color="#6b7280")
    )
    yaxis_config = dict(
        title=y_label, 
        showgrid=True, 
        gridcolor='#f3f4f6',
        title_font=dict(size=14, color="#6b7280")
    )
    
    # Set reasonable axis ranges and custom ticks for pace charts
    if 'pace' in x_label.lower():
        xaxis_config.update({
            'range': [3, 12],
            'tickvals': pace_tick_vals,
            'ticktext': pace_tick_text
        })
    if 'pace' in y_label.lower():
        yaxis_config.update({
            'range': [3, 12],
            'tickvals': pace_tick_vals,
            'ticktext': pace_tick_text
        })
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=xaxis_config,
        yaxis=yaxis_config,
        margin=dict(l=0, r=0, t=20, b=0),
        height=300,
        showlegend=False  # Hide legend since we have the workout type legend above
    )
    
    return fig


def create_heart_rate_zones_chart(df_filtered):
    """Create heart rate zones distribution pie chart"""
    hr_data = df_filtered['Avg HR'].dropna()
    if hr_data.empty or len(hr_data) <= 5:
        return None
    
    # Define HR zones based on common training zones
    max_hr_estimate = 220 - 30  # Assume average age of 30 for estimation
    zones = {
        'Zone 1 (Recovery)\n{:.0f}-{:.0f} bpm'.format(max_hr_estimate * 0.5, max_hr_estimate * 0.6): (max_hr_estimate * 0.5, max_hr_estimate * 0.6),
        'Zone 2 (Aerobic)\n{:.0f}-{:.0f} bpm'.format(max_hr_estimate * 0.6, max_hr_estimate * 0.7): (max_hr_estimate * 0.6, max_hr_estimate * 0.7),
        'Zone 3 (Tempo)\n{:.0f}-{:.0f} bpm'.format(max_hr_estimate * 0.7, max_hr_estimate * 0.8): (max_hr_estimate * 0.7, max_hr_estimate * 0.8),
        'Zone 4 (Threshold)\n{:.0f}-{:.0f} bpm'.format(max_hr_estimate * 0.8, max_hr_estimate * 0.9): (max_hr_estimate * 0.8, max_hr_estimate * 0.9),
        'Zone 5 (VO2 Max)\n{:.0f}+ bpm'.format(max_hr_estimate * 0.9): (max_hr_estimate * 0.9, 220)
    }
    
    zone_counts = []
    zone_names = []
    zone_colors = ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444']
    
    for i, (zone_name, (min_hr, max_hr)) in enumerate(zones.items()):
        count = len(hr_data[(hr_data >= min_hr) & (hr_data <= max_hr)])
        if count > 0:  # Only include zones with data
            zone_counts.append(count)
            zone_names.append(zone_name)
    
    if not zone_counts:
        return None
    
    fig = px.pie(
        values=zone_counts,
        names=zone_names,
        title="",
        color_discrete_sequence=zone_colors[:len(zone_counts)]
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=10, color="#374151"),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=10)
        )
    )
    fig.update_traces(
        textposition='inside',
        textinfo='percent',
        textfont=dict(size=12),
        hovertemplate='<b>%{label}</b><br>%{value} runs (%{percent})<extra></extra>'
    )
    
    return fig


def create_monthly_volume_chart(df_filtered):
    """Create monthly running volume chart"""
    # Monthly aggregation as alternative
    df_monthly = df_filtered.copy()
    df_monthly['Month'] = df_monthly['Date'].dt.to_period('M')
    monthly_stats = df_monthly.groupby('Month').agg({
        'Distance (km)': 'sum',
        'moving_time_minutes': 'sum'
    }).reset_index()
    monthly_stats['Month'] = monthly_stats['Month'].astype(str)
    
    if monthly_stats.empty:
        return None
    
    fig = px.bar(
        monthly_stats,
        x='Month',
        y='Distance (km)',
        title="",
        color_discrete_sequence=['#8b5cf6']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        xaxis=dict(
            title="Month", 
            showgrid=True, 
            gridcolor='#f3f4f6',
            title_font=dict(size=14, color="#6b7280")
        ),
        yaxis=dict(
            title="Distance (km)", 
            showgrid=True, 
            gridcolor='#f3f4f6',
            title_font=dict(size=14, color="#6b7280")
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=300
    )
    fig.update_traces(
        hovertemplate='<b>%{y:.1f} km</b><br>%{x}<extra></extra>'
    )
    
    return fig 