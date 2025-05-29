"""
Modular running statistics dashboard
"""
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE

# Import our modular components
from .statistics_modules.data_processing import (
    preprocess_dataframe,
    filter_data_by_time_period,
    calculate_key_metrics
)
from .statistics_modules.metric_cards import create_all_metric_cards
from .statistics_modules.styles import get_statistics_css
from .statistics_modules.chart_creators import (
    create_distance_chart,
    create_pace_trend_chart,
    create_heart_rate_chart,
    create_pace_distribution_chart,
    create_cadence_chart,
    create_elevation_chart,
    create_elapsed_time_chart,
    create_run_frequency_chart,
    create_yearly_cumulative_chart,
    create_correlation_chart,
    create_heart_rate_zones_chart,
    create_monthly_volume_chart
)
from .statistics_modules.insights import generate_insights, get_no_insights_message


def render_header():
    """Render the page header"""
    st.markdown("""
    <div class="stats-header">
        <h1 class="stats-title">📊 Running Analytics</h1>
        <p class="stats-subtitle">Performance insights and training metrics</p>
    </div>
    """, unsafe_allow_html=True)


def render_time_controls():
    """Render radio button controls in a single compact row"""
    st.markdown("""
    <style>
    /* Radio button styling - specific to statistics controls only */
    .statistics-controls .stRadio > div {
        gap: 0.5rem !important;
        display: flex !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
    }
    
    .statistics-controls .stRadio label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        margin: 2px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    .statistics-controls .stRadio label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Active/selected state - specific to statistics controls */
    .statistics-controls .stRadio label[data-baseweb="radio"] input:checked + div {
        background: rgba(59, 130, 246, 0.2) !important;
        border-color: rgba(59, 130, 246, 0.4) !important;
        color: #3b82f6 !important;
    }
    
    /* Single row container */
    .statistics-controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        margin: 1rem 0 1.5rem 0;
        flex-wrap: wrap;
    }
    
    .statistics-controls .control-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Wrap controls in a specific container class
    st.markdown('<div class="statistics-controls">', unsafe_allow_html=True)
    
    # Single row with both controls
    col1, col2 = st.columns(2)
    
    with col1:
        period_options = ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time"]
        period_values = [7, 30, 90, 365, None]
        
        # Get current selection index
        current_period = st.session_state.get('time_period', None)
        try:
            current_index = period_values.index(current_period)
        except ValueError:
            current_index = 4  # Default to "All Time"
        
        selected_period = st.radio(
            "Time Period Selection",
            period_options,
            index=current_index,
            horizontal=True,
            label_visibility="collapsed",
            key="period_radio"
        )
        
        # Update session state
        st.session_state.time_period = period_values[period_options.index(selected_period)]
    
    with col2:
        aggregation_options = ["Daily", "Weekly", "Monthly", "Yearly"]
        aggregation_values = ["daily", "weekly", "monthly", "yearly"]
        
        # Get current selection index
        current_aggregation = st.session_state.get('time_aggregation', "weekly")
        try:
            current_agg_index = aggregation_values.index(current_aggregation)
        except ValueError:
            current_agg_index = 1  # Default to "Weekly"
        
        selected_aggregation = st.radio(
            "Time Aggregation Selection",
            aggregation_options,
            index=current_agg_index,
            horizontal=True,
            label_visibility="collapsed",
            key="aggregation_radio"
        )
        
        # Update session state
        st.session_state.time_aggregation = aggregation_values[aggregation_options.index(selected_aggregation)]
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Set defaults if not already set
    if 'time_period' not in st.session_state:
        st.session_state.time_period = None
    if 'time_aggregation' not in st.session_state:
        st.session_state.time_aggregation = "weekly"


def render_metric_cards(metrics, time_period):
    """Render all metric cards"""
    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
    
    # Create all cards (compact + individual)
    cards = create_all_metric_cards(metrics, time_period)
    
    # First card is the compact summary (shown on mobile only)
    compact_card = cards[0]
    individual_cards = cards[1:]  # Remaining 8 cards (shown on desktop only)
    
    # Display compact card (mobile)
    st.markdown(compact_card, unsafe_allow_html=True)
    
    # Display individual cards in 8 columns (desktop)
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    columns = [col1, col2, col3, col4, col5, col6, col7, col8]
    
    for i, card_html in enumerate(individual_cards):
        with columns[i]:
            st.markdown(card_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_performance_trends(df_filtered, time_aggregation):
    """Render performance trends section"""
    st.markdown('<h2 class="section-header">📈 Performance Trends</h2>', unsafe_allow_html=True)
    
    # Distance over time
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown(f'<h3 class="chart-title">📏 Distance Over Time ({time_aggregation.title()})</h3>', unsafe_allow_html=True)
    
    fig_distance = create_distance_chart(df_filtered, time_aggregation)
    if fig_distance:
        st.plotly_chart(fig_distance, use_container_width=True, key="distance_chart")
    else:
        st.info(f"No data available for {time_aggregation} aggregation")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Pace and Heart Rate trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(f'<h3 class="chart-title">⚡ Pace Trends ({time_aggregation.title()})</h3>', unsafe_allow_html=True)
        
        fig_pace = create_pace_trend_chart(df_filtered, time_aggregation)
        if fig_pace:
            st.plotly_chart(fig_pace, use_container_width=True, key="pace_trend_chart")
        else:
            st.info("No valid pace data available for trend analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        fig_hr = create_heart_rate_chart(df_filtered, time_aggregation)
        if fig_hr:
            st.markdown(f'<h3 class="chart-title">❤️ Heart Rate Trends ({time_aggregation.title()})</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_hr, use_container_width=True, key="hr_chart")
        else:
            st.markdown('<h3 class="chart-title">📊 Pace Distribution</h3>', unsafe_allow_html=True)
            fig_pace_dist = create_pace_distribution_chart(df_filtered)
            if fig_pace_dist:
                st.plotly_chart(fig_pace_dist, use_container_width=True, key="pace_dist_chart")
            else:
                st.info("No pace data available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Cadence and Elevation trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(f'<h3 class="chart-title">👟 Cadence Trends ({time_aggregation.title()})</h3>', unsafe_allow_html=True)
        
        fig_cadence = create_cadence_chart(df_filtered, time_aggregation)
        if fig_cadence:
            st.plotly_chart(fig_cadence, use_container_width=True, key="cadence_chart")
        else:
            st.info("No cadence data available for trend analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(f'<h3 class="chart-title">⛰️ Elevation Gain Trends ({time_aggregation.title()})</h3>', unsafe_allow_html=True)
        
        fig_elevation = create_elevation_chart(df_filtered, time_aggregation)
        if fig_elevation:
            st.plotly_chart(fig_elevation, use_container_width=True, key="elevation_chart")
        else:
            st.info("No elevation gain data available for trend analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Elapsed Time and Run Frequency
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(f'<h3 class="chart-title">⏱️ Elapsed Time Trends ({time_aggregation.title()})</h3>', unsafe_allow_html=True)
        
        fig_time = create_elapsed_time_chart(df_filtered, time_aggregation)
        if fig_time:
            st.plotly_chart(fig_time, use_container_width=True, key="time_chart")
        else:
            st.info("No elapsed time data available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🏃‍♂️ Run Frequency by Day</h3>', unsafe_allow_html=True)
        
        fig_frequency = create_run_frequency_chart(df_filtered)
        if fig_frequency:
            st.plotly_chart(fig_frequency, use_container_width=True, key="run_frequency_chart")
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_yearly_cumulative(df, today):
    """Render yearly cumulative distance chart"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">📈 Distance per Year (Cumulative)</h3>', unsafe_allow_html=True)
    
    fig_yearly = create_yearly_cumulative_chart(df, today)
    if fig_yearly:
        st.plotly_chart(fig_yearly, use_container_width=True, key="yearly_chart")
    else:
        st.info("No data available for yearly cumulative analysis")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_advanced_analytics(df_filtered):
    """Render advanced analytics section"""
    st.markdown('<h2 class="section-header">🔬 Advanced Analytics</h2>', unsafe_allow_html=True)
    
    # Add workout type legend
    st.markdown("""
    <div class="workout-legend">
        <div class="legend-title">🏃‍♂️ Workout Type Legend</div>
        <div class="legend-items">
            <div class="legend-item">
                <span style="color: #ef4444; font-size: 1.2rem;">⭐</span>
                <span>Race</span>
            </div>
            <div class="legend-item">
                <span style="color: #f97316; font-size: 1.2rem;">♦</span>
                <span>Workout</span>
            </div>
            <div class="legend-item">
                <span style="color: #3b82f6; font-size: 1.2rem;">●</span>
                <span>Long Run</span>
            </div>
            <div class="legend-item">
                <span style="color: #8b5cf6; font-size: 1.2rem;">▲</span>
                <span>Trail Run</span>
            </div>
            <div class="legend-item">
                <span style="color: #06b6d4; font-size: 1.2rem;">○</span>
                <span>Recovery</span>
            </div>
            <div class="legend-item">
                <span style="color: #10b981; font-size: 1.2rem;">■</span>
                <span>Commute</span>
            </div>
            <div class="legend-item">
                <span style="color: #6b7280; font-size: 1.2rem;">●</span>
                <span>Default</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # First row of correlation charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🎯 Distance vs Pace Correlation</h3>', unsafe_allow_html=True)
        
        fig_dist_pace = create_correlation_chart(
            df_filtered, 'Distance (km)', 'pace_minutes', 
            'Distance vs Pace', 'Distance (km)', 'Pace'
        )
        if fig_dist_pace:
            st.plotly_chart(fig_dist_pace, use_container_width=True, key="scatter_chart")
        else:
            st.info("Need valid distance and pace data for correlation analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        fig_hr_zones = create_heart_rate_zones_chart(df_filtered)
        if fig_hr_zones:
            st.markdown('<h3 class="chart-title">❤️ Heart Rate Zones Distribution</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_hr_zones, use_container_width=True, key="zones_chart")
        else:
            st.markdown('<h3 class="chart-title">📊 Monthly Running Volume</h3>', unsafe_allow_html=True)
            fig_monthly = create_monthly_volume_chart(df_filtered)
            if fig_monthly:
                st.plotly_chart(fig_monthly, use_container_width=True, key="monthly_chart")
            else:
                st.info("No monthly data available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional correlation charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">💓 Distance vs Heart Rate</h3>', unsafe_allow_html=True)
        
        fig_dist_hr = create_correlation_chart(
            df_filtered, 'Distance (km)', 'Avg HR',
            'Distance vs Heart Rate', 'Distance (km)', 'Average Heart Rate (bpm)'
        )
        if fig_dist_hr:
            st.plotly_chart(fig_dist_hr, use_container_width=True, key="hr_distance_chart")
        else:
            st.info("Need both distance and heart rate data for correlation analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">⚡💓 Pace vs Heart Rate</h3>', unsafe_allow_html=True)
        
        fig_pace_hr = create_correlation_chart(
            df_filtered, 'pace_minutes', 'Avg HR',
            'Pace vs Heart Rate', 'Pace', 'Average Heart Rate (bpm)'
        )
        if fig_pace_hr:
            st.plotly_chart(fig_pace_hr, use_container_width=True, key="pace_hr_chart")
        else:
            st.info("Need both pace and heart rate data for correlation analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Third row of correlation charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">⛰️ Distance vs Elevation Gain</h3>', unsafe_allow_html=True)
        
        fig_dist_elev = create_correlation_chart(
            df_filtered, 'Distance (km)', 'Elevation Gain',
            'Distance vs Elevation', 'Distance (km)', 'Elevation Gain (m)'
        )
        if fig_dist_elev:
            st.plotly_chart(fig_dist_elev, use_container_width=True, key="elevation_correlation_chart")
        else:
            st.info("Need both distance and elevation data for correlation analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">🕐 Time vs Pace Efficiency</h3>', unsafe_allow_html=True)
        
        fig_time_pace = create_correlation_chart(
            df_filtered, 'moving_time_minutes', 'pace_minutes',
            'Time vs Pace', 'Moving Time (minutes)', 'Pace'
        )
        if fig_time_pace:
            st.plotly_chart(fig_time_pace, use_container_width=True, key="time_pace_chart")
        else:
            st.info("Need both time and pace data for correlation analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_insights(df_filtered, time_period):
    """Render insights and recommendations section"""
    st.markdown('<h2 class="section-header">💡 Insights & Recommendations</h2>', unsafe_allow_html=True)
    
    insights = generate_insights(df_filtered, time_period)
    
    if insights:
        for i, insight in enumerate(insights):
            st.markdown(f"""
            <div class="insight-card" style="animation-delay: {i * 0.1}s;">
                {insight}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(get_no_insights_message(), unsafe_allow_html=True)


def render_statistics(df, today):
    """Main function to render the statistics dashboard"""
    # Apply CSS styles
    st.markdown(get_statistics_css(), unsafe_allow_html=True)
    
    # Render header
    render_header()
    
    # Sidebar version
    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)
    
    if df.empty:
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem; color: #6b7280;">
            <h3>No running data available</h3>
            <p>Start logging your runs to see detailed statistics and insights!</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Preprocess data
    df = preprocess_dataframe(df)
    
    if df.empty:
        st.error("No valid running data found.")
        return
    
    # Time controls
    render_time_controls()
    
    # Filter data based on time period
    df_filtered = filter_data_by_time_period(df, st.session_state.time_period, today)
    
    if df_filtered.empty:
        period_label = f"Last {st.session_state.time_period} Days" if st.session_state.time_period else "All Time"
        st.warning(f"No data available for the selected period ({period_label})")
        return
    
    # Calculate key metrics
    metrics = calculate_key_metrics(df_filtered, st.session_state.time_period, today, df)
    
    # Render metric cards
    render_metric_cards(metrics, st.session_state.time_period)
    
    # Render performance trends
    render_performance_trends(df_filtered, st.session_state.time_aggregation)
    
    # Render yearly cumulative chart
    render_yearly_cumulative(df, today)
    
    # Render advanced analytics
    render_advanced_analytics(df_filtered)
    
    # Render insights
    render_insights(df_filtered, st.session_state.time_period) 