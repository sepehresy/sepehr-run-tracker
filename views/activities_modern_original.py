"""
Modern Activities View - Redesigned UI for Sepehr's Running Tracker
Features:
- Modern card-based design system
- Mobile-first responsive layout
- Improved information architecture
- Enhanced data visualization
- Better user experience
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import numpy as np
from datetime import datetime, timedelta
import math

def load_modern_css():
    """Load modern CSS styling for the activities view"""
    st.markdown("""
    <style>
    /* Modern Design System Variables */
    :root {
        --primary-bg: #111827;
        --secondary-bg: #1f2937;
        --card-bg: rgba(31, 41, 55, 0.8);
        --accent-color: #3b82f6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --text-muted: #9ca3af;
        --border-color: rgba(75, 85, 99, 0.3);
        --shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    
    /* Modern Card System */
    .modern-card {
        background: var(--card-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
    }
    
    .modern-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-color);
    }
    
    .modern-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .modern-card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .modern-card-subtitle {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin: 4px 0 0 0;
    }
    
    /* Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }
    
    .metric-item {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-item:hover {
        background: rgba(59, 130, 246, 0.15);
        transform: scale(1.02);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-color);
        margin: 0;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 8px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-change {
        font-size: 0.75rem;
        margin-top: 4px;
        padding: 2px 8px;
        border-radius: 12px;
        display: inline-block;
    }
    
    .metric-change.positive {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
    }
    
    .metric-change.negative {
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger-color);
    }
    
    /* Activity Summary Cards */
    .activity-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }
    
    .summary-card {
        background: linear-gradient(135deg, var(--card-bg) 0%, rgba(59, 130, 246, 0.1) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        position: relative;
        overflow: hidden;
    }
    
    .summary-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-color), var(--success-color));
    }
    
    /* Performance Indicators */
    .performance-indicator {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .indicator-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.875rem;
    }
    
    .indicator-icon.excellent {
        background: var(--success-color);
        color: white;
    }
    
    .indicator-icon.good {
        background: var(--accent-color);
        color: white;
    }
    
    .indicator-icon.average {
        background: var(--warning-color);
        color: white;
    }
    
    .indicator-icon.poor {
        background: var(--danger-color);
        color: white;
    }
    
    /* Action Buttons */
    .action-buttons {
        display: flex;
        gap: 12px;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    
    .action-btn {
        background: var(--accent-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .action-btn:hover {
        background: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    .action-btn.secondary {
        background: var(--secondary-bg);
        border: 1px solid var(--border-color);
    }
    
    .action-btn.secondary:hover {
        background: var(--card-bg);
        border-color: var(--accent-color);
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .modern-card {
            padding: 16px;
            margin: 12px 0;
            border-radius: 12px;
        }
        
        .metrics-grid {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }
        
        .metric-item {
            padding: 16px;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
        
        .activity-summary {
            grid-template-columns: 1fr;
            gap: 16px;
        }
        
        .action-buttons {
            flex-direction: column;
        }
        
        .action-btn {
            width: 100%;
            justify-content: center;
        }
    }
    
    /* Loading States */
    .loading-skeleton {
        background: linear-gradient(90deg, var(--secondary-bg) 25%, var(--card-bg) 50%, var(--secondary-bg) 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 8px;
        height: 20px;
        margin: 8px 0;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Chart Containers */
    .chart-container {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        border: 1px solid var(--border-color);
    }
    
    /* Hide Streamlit Elements */
    .stDeployButton {
        display: none;
    }
    
    .stDecoration {
        display: none;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-bg);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #2563eb;
    }
    </style>
    """, unsafe_allow_html=True)

def create_activity_overview_card(df):
    """Create modern activity overview card with key metrics"""
    if df.empty:
        return
    
    # Calculate key metrics
    total_activities = len(df)
    total_distance = df['Distance (km)'].sum()
    total_time = df['Elapsed Time (min)'].sum()
    avg_pace = df['Pace (min/km)'].mean()
    
    # Calculate trends (last 30 days vs previous 30 days) - use copy to avoid modifying original
    df_copy = df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Date'])
    recent_date = df_copy['Date'].max()
    last_30_days = df_copy[df_copy['Date'] >= (recent_date - timedelta(days=30))]
    prev_30_days = df_copy[(df_copy['Date'] >= (recent_date - timedelta(days=60))) & 
                          (df_copy['Date'] < (recent_date - timedelta(days=30)))]
    
    # Calculate changes
    distance_change = ((last_30_days['Distance (km)'].sum() - prev_30_days['Distance (km)'].sum()) / 
                      max(prev_30_days['Distance (km)'].sum(), 1)) * 100 if not prev_30_days.empty else 0
    
    activities_change = ((len(last_30_days) - len(prev_30_days)) / 
                        max(len(prev_30_days), 1)) * 100 if not prev_30_days.empty else 0
    
    st.markdown("""
    <div class="modern-card">
        <div class="modern-card-header">
            <div>
                <h2 class="modern-card-title">
                    🏃‍♂️ Activity Overview
                </h2>
                <p class="modern-card-subtitle">Your running journey at a glance</p>
            </div>
        </div>
        <div class="metrics-grid">
            <div class="metric-item">
                <h3 class="metric-value">{}</h3>
                <p class="metric-label">Total Activities</p>
                <span class="metric-change {}">
                    {} {:+.1f}%
                </span>
            </div>
            <div class="metric-item">
                <h3 class="metric-value">{:.1f}</h3>
                <p class="metric-label">Total Distance (km)</p>
                <span class="metric-change {}">
                    {} {:+.1f}%
                </span>
            </div>
            <div class="metric-item">
                <h3 class="metric-value">{:.0f}</h3>
                <p class="metric-label">Total Time (hours)</p>
                <span class="metric-change positive">
                    ⏱️ {:.1f} hrs/week avg
                </span>
            </div>
            <div class="metric-item">
                <h3 class="metric-value">{:.2f}</h3>
                <p class="metric-label">Average Pace (min/km)</p>
                <span class="metric-change {}">
                    {} Pace trend
                </span>
            </div>
        </div>
    </div>
    """.format(
        total_activities,
        "positive" if activities_change >= 0 else "negative",
        "📈" if activities_change >= 0 else "📉",
        activities_change,
        total_distance,
        "positive" if distance_change >= 0 else "negative",
        "📈" if distance_change >= 0 else "📉",
        distance_change,
        total_time / 60,
        total_time / 60 / (total_activities / 7) if total_activities > 0 else 0,
        avg_pace,
        "positive" if avg_pace < 6 else "negative",
        "🚀" if avg_pace < 6 else "🐌"
    ), unsafe_allow_html=True)

def create_performance_insights_card(df):
    """Create performance insights with visual indicators"""
    if df.empty:
        return
    
    # Calculate performance metrics
    recent_runs = df.tail(10)
    avg_pace = recent_runs['Pace (min/km)'].mean()
    pace_consistency = recent_runs['Pace (min/km)'].std()
    avg_distance = recent_runs['Distance (km)'].mean()
    
    # Determine performance levels
    pace_level = "excellent" if avg_pace < 5 else "good" if avg_pace < 6 else "average" if avg_pace < 7 else "poor"
    consistency_level = "excellent" if pace_consistency < 0.5 else "good" if pace_consistency < 1 else "average" if pace_consistency < 1.5 else "poor"
    distance_level = "excellent" if avg_distance > 10 else "good" if avg_distance > 7 else "average" if avg_distance > 5 else "poor"
    
    # Create the card header
    st.markdown("""
    <div class="modern-card">
        <div class="modern-card-header">
            <div>
                <h2 class="modern-card-title">
                    📊 Performance Insights
                </h2>
                <p class="modern-card-subtitle">Based on your last 10 activities</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Use Streamlit columns for better rendering
    col1, col2 = st.columns([1, 4])
    
    # Pace Performance
    with col1:
        if pace_level == "excellent":
            st.markdown("🟢 **P**")
        elif pace_level == "good":
            st.markdown("🔵 **P**")
        elif pace_level == "average":
            st.markdown("🟡 **P**")
        else:
            st.markdown("🔴 **P**")
    
    with col2:
        st.markdown("**Pace Performance**")
        st.markdown(f"Average: {avg_pace:.2f} min/km")
    
    st.markdown("---")
    
    # Pace Consistency
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if consistency_level == "excellent":
            st.markdown("🟢 **C**")
        elif consistency_level == "good":
            st.markdown("🔵 **C**")
        elif consistency_level == "average":
            st.markdown("🟡 **C**")
        else:
            st.markdown("🔴 **C**")
    
    with col2:
        st.markdown("**Pace Consistency**")
        st.markdown(f"Variation: ±{pace_consistency:.2f} min/km")
    
    st.markdown("---")
    
    # Distance Endurance
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if distance_level == "excellent":
            st.markdown("🟢 **D**")
        elif distance_level == "good":
            st.markdown("🔵 **D**")
        elif distance_level == "average":
            st.markdown("🟡 **D**")
        else:
            st.markdown("🔴 **D**")
    
    with col2:
        st.markdown("**Distance Endurance**")
        st.markdown(f"Average: {avg_distance:.1f} km per run")
    
    st.markdown("---")
    
    # Action buttons using Streamlit buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("📈 View Detailed Analytics", key="detailed_analytics")
    with col2:
        st.button("🎯 Set New Goals", key="set_goals")

def create_modern_pace_chart(df):
    """Create modern pace progression chart using Plotly"""
    if df.empty:
        return
    
    df_sorted = df.sort_values('Date')
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Pace Progression', 'Distance & Duration Trends'),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4]
    )
    
    # Pace line chart
    fig.add_trace(
        go.Scatter(
            x=df_sorted['Date'],
            y=df_sorted['Pace (min/km)'],
            mode='lines+markers',
            name='Pace',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=6, color='#3b82f6'),
            hovertemplate='<b>%{x}</b><br>Pace: %{y:.2f} min/km<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add trend line
    z = np.polyfit(range(len(df_sorted)), df_sorted['Pace (min/km)'], 1)
    p = np.poly1d(z)
    fig.add_trace(
        go.Scatter(
            x=df_sorted['Date'],
            y=p(range(len(df_sorted))),
            mode='lines',
            name='Trend',
            line=dict(color='#10b981', width=2, dash='dash'),
            hovertemplate='Trend: %{y:.2f} min/km<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Distance bars
    fig.add_trace(
        go.Bar(
            x=df_sorted['Date'],
            y=df_sorted['Distance (km)'],
            name='Distance (km)',
            marker_color='rgba(59, 130, 246, 0.6)',
            hovertemplate='<b>%{x}</b><br>Distance: %{y:.1f} km<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=600,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f9fafb'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    fig.update_xaxes(
        gridcolor='rgba(75, 85, 99, 0.3)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor='rgba(75, 85, 99, 0.3)',
        showgrid=True,
        zeroline=False
    )
    
    return fig

def create_modern_activity_table(df):
    """Create modern activity table with enhanced styling"""
    if df.empty:
        return
    
    # Prepare data for display
    display_df = df.copy()
    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
    
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection('single', use_checkbox=True)
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc='sum',
        editable=False
    )
    
    # Custom column configurations
    gb.configure_column("Date", sort='desc', width=120)
    gb.configure_column("Distance (km)", type=["numericColumn"], precision=2, width=130)
    gb.configure_column("Elapsed Time (min)", type=["numericColumn"], precision=0, width=130)
    gb.configure_column("Pace (min/km)", type=["numericColumn"], precision=2, width=130)
    gb.configure_column("Avg HR", type=["numericColumn"], precision=0, width=100)
    gb.configure_column("Max HR", type=["numericColumn"], precision=0, width=100)
    
    gridOptions = gb.build()
    
    # Custom CSS for AgGrid
    custom_css = {
        ".ag-theme-streamlit": {
            "--ag-background-color": "rgba(31, 41, 55, 0.8)",
            "--ag-header-background-color": "rgba(17, 24, 39, 0.9)",
            "--ag-odd-row-background-color": "rgba(55, 65, 81, 0.3)",
            "--ag-row-hover-color": "rgba(59, 130, 246, 0.1)",
            "--ag-selected-row-background-color": "rgba(59, 130, 246, 0.2)",
            "--ag-border-color": "rgba(75, 85, 99, 0.3)",
            "--ag-header-foreground-color": "#f9fafb",
            "--ag-foreground-color": "#d1d5db",
        }
    }
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="modern-card-header">
        <div>
            <h2 class="modern-card-title">
                📋 Activity History
            </h2>
            <p class="modern-card-subtitle">Detailed view of all your running activities</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    grid_response = AgGrid(
        display_df,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        custom_css=custom_css,
        height=400
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return grid_response

def create_route_visualization(df, selected_activity=None):
    """Create enhanced route visualization with modern styling"""
    if df.empty:
        return
    
    st.markdown("""
    <div class="modern-card">
        <div class="modern-card-header">
            <div>
                <h2 class="modern-card-title">
                    🗺️ Route Visualization
                </h2>
                <p class="modern-card-subtitle">Interactive map of your running routes</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create map centered on activities
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        center_lat = df['Latitude'].mean()
        center_lon = df['Longitude'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=None
        )
        
        # Add dark theme tile layer
        folium.TileLayer(
            tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            name='Dark Theme',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add activity markers
        for idx, row in df.iterrows():
            if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
                color = '#3b82f6' if selected_activity is None or idx == selected_activity else '#6b7280'
                
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=8 if selected_activity is None or idx == selected_activity else 5,
                    popup=f"""
                    <div style="font-family: Arial; color: #1f2937;">
                        <b>{row['Date']}</b><br>
                        Distance: {row['Distance (km)']:.2f} km<br>
                        Pace: {row['Pace (min/km)']:.2f} min/km<br>
                        Duration: {row['Elapsed Time (min)']:.0f} min
                    </div>
                    """,
                    color=color,
                    fillColor=color,
                    fillOpacity=0.8,
                    weight=2
                ).add_to(m)
        
        # Display map
        map_data = st_folium(m, width=700, height=400)
        
        return map_data
    else:
        st.info("📍 Location data not available for route visualization")

def show_modern_activities():
    """Main function to display the modern activities view"""
    # Load modern CSS
    load_modern_css()
    
    # Page header
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h1 style="color: var(--text-primary); font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">
            🏃‍♂️ Activities Dashboard
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem; margin: 0;">
            Modern view of your running journey with enhanced analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    try:
        # Check if activities_data exists in session state and is not empty
        if 'activities_data' in st.session_state:
            activities_df = st.session_state.activities_data
            if activities_df is not None and not activities_df.empty:
                df = activities_df.copy()
            else:
                st.warning("⚠️ No activity data available. Please check your data source.")
                return
        else:
            st.warning("⚠️ No activity data available. Please check your data source.")
            return
        
        # Create layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Activity Overview Card
            create_activity_overview_card(df)
            
            # Modern Activity Table
            grid_response = create_modern_activity_table(df)
            
            # Chart Container
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown("""
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">
                📈 Performance Analytics
            </h3>
            """, unsafe_allow_html=True)
            
            chart = create_modern_pace_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Performance Insights Card
            create_performance_insights_card(df)
            
            # Route Visualization
            selected_row = None
            if grid_response and 'selected_rows' in grid_response:
                selected_rows = grid_response['selected_rows']
                # Properly handle different types of selected_rows
                if isinstance(selected_rows, pd.DataFrame):
                    has_selection = not selected_rows.empty
                elif isinstance(selected_rows, list):
                    has_selection = len(selected_rows) > 0
                else:
                    has_selection = False
                
                if has_selection:
                    if isinstance(selected_rows, pd.DataFrame):
                        selected_row = selected_rows.iloc[0]
                    else:
                        selected_row = selected_rows[0]
            
            create_route_visualization(df, selected_row)
            
            # Quick Stats Card
            # Calculate stats safely
            try:
                # Ensure Date column is datetime
                df_copy = df.copy()
                df_copy['Date'] = pd.to_datetime(df_copy['Date'])
                
                # Calculate this month's activities
                thirty_days_ago = datetime.now() - timedelta(days=30)
                this_month_activities = df_copy[df_copy['Date'] >= thirty_days_ago]
                this_month_count = len(this_month_activities)
                
                # Calculate longest run and best pace
                longest_run = df['Distance (km)'].max() if len(df['Distance (km)']) > 0 and not df['Distance (km)'].isna().all() else 0
                best_pace = df['Pace (min/km)'].min() if len(df['Pace (min/km)']) > 0 and not df['Pace (min/km)'].isna().all() else 0
                
            except Exception:
                # Fallback values if date parsing fails
                this_month_count = len(df)
                longest_run = df['Distance (km)'].max() if len(df['Distance (km)']) > 0 and not df['Distance (km)'].isna().all() else 0
                best_pace = df['Pace (min/km)'].min() if len(df['Pace (min/km)']) > 0 and not df['Pace (min/km)'].isna().all() else 0
            
            st.markdown("""
            <div class="modern-card">
                <div class="modern-card-header">
                    <div>
                        <h2 class="modern-card-title">
                            ⚡ Quick Stats
                        </h2>
                    </div>
                </div>
                <div style="text-align: center;">
                    <div style="margin: 16px 0;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--accent-color);">
                            {}
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">
                            Last 30 Days
                        </div>
                    </div>
                    <div style="margin: 16px 0;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--success-color);">
                            {:.1f} km
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">
                            Longest Run
                        </div>
                    </div>
                    <div style="margin: 16px 0;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--warning-color);">
                            {:.2f}
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">
                            Best Pace (min/km)
                        </div>
                    </div>
                </div>
            </div>
            """.format(
                this_month_count,
                longest_run,
                best_pace
            ), unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ Error loading activities: {str(e)}")
        st.info("💡 Please check your data source and try again.")

if __name__ == "__main__":
    show_modern_activities() 