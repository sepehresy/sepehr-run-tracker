"""
Optimized UI renderer for race planning module with table-centric design.
Focuses on providing a comprehensive table view of training plans.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE

from views.race_planning.data import (
    load_saved_races, save_races, load_training_plans, 
    load_progress_feedback, save_progress_feedback, save_training_plan
)
from views.race_planning.styles import load_app_css
from views.race_planning.utils import prepare_training_plan_dataframe, initialize_week_selection, calculate_week_dates
from views.race_planning.components_optimal import (
    render_race_selector,
    render_training_plan_table,
    render_plan_generation_tools,
    render_weekly_comparison_chart,
    render_ai_analysis_section,
    render_add_race_form,
    render_race_settings_form
)

def render_race_planning_optimal(df, today, user_info, gist_id, gist_filename, github_token):
    """
    Optimized implementation of race planning view with table-based UI.
    
    Args:
        df: Running log dataframe
        today: Current date
        user_info: User information
        gist_id: Gist ID
        gist_filename: Gist filename
        github_token: GitHub token
    """
    # Load app CSS
    load_app_css()
    
    # Initialize session variables
    user_key = user_info["USER_KEY"]
    gist_id = user_info["GIST_ID"]
    filename = f"{user_key}.json"
    token = github_token

    if isinstance(today, datetime):
        today = today.date()
    
    # Initialize session state
    if "race_planner" not in st.session_state:
        st.session_state["race_planner"] = {
            "selected_race_id": None,
            "add_race_modal_open": False,
            "view_mode": "table",  # Options: table, week, analysis
            "selected_week_idx": None,
            "plan_generated": False,
            "edit_cell": None,
        }
    
    # Display version in sidebar
    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)

    # Page header with improved styling
    st.markdown(
        '<div style="display:flex;align-items:center;margin-bottom:1rem;">'
        '<span style="font-size:1.75rem;vertical-align:middle;margin-right:0.5rem;">🏁</span>'
        '<span style="font-size:1.5rem;font-weight:600;vertical-align:middle;">Race Planning</span>'
        '</div>', 
        unsafe_allow_html=True
    )
    
    # Load data
    races = load_saved_races(user_info, gist_id, filename, token)
    plans = load_training_plans(user_info, gist_id, filename, token)
    
    # Check for empty state - No races added yet
    if not races:
        st.info("No races added yet. Add your first race to get started with planning.")
        
        if st.button("➕ Add Your First Race", use_container_width=True):
            st.session_state["race_planner"]["add_race_modal_open"] = True
        
        if st.session_state["race_planner"]["add_race_modal_open"]:
            added = render_add_race_form(today, user_info, gist_id, filename, token, races)
            if added:
                st.session_state["race_planner"]["add_race_modal_open"] = False
                st.rerun()
        return
    
    # Race selector at the top - compact dropdown with key race info
    st.session_state["race_planner"]["selected_race_id"] = render_race_selector(
        races, 
        plans, 
        today, 
        st.session_state["race_planner"]["selected_race_id"]
    )
    
    selected_race_id = st.session_state["race_planner"]["selected_race_id"]
    
    # Get the selected race and its plan
    selected_race = None
    selected_plan = None
    selected_weeks = []
    
    if selected_race_id:
        selected_race = next((r for r in races if r.get("id") == selected_race_id), None)
        selected_plan = plans.get(selected_race_id, {})
        selected_weeks = selected_plan.get("weeks", [])
    
    # Add Race button always visible in top-right corner
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        if st.button("➕ Add Race", key="add_race_button", use_container_width=True):
            st.session_state["race_planner"]["add_race_modal_open"] = True
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Training Plan", "📊 Analysis", "⚙️ Settings"])
    
    with tab1:
        if selected_race:
            # Main content area - changes based on view mode
            if st.session_state["race_planner"]["view_mode"] == "table":
                # Plan generation tools above the table
                render_plan_generation_tools(
                    selected_race_id, 
                    selected_race, 
                    selected_weeks, 
                    user_info, 
                    gist_id, 
                    filename, 
                    token
                )
                
                # Training plan table with all weeks visible
                table_clicked = render_training_plan_table(
                    selected_race, 
                    selected_weeks, 
                    today, 
                    df,
                    user_info,
                    gist_id,
                    filename,
                    token
                )
                
                if table_clicked and table_clicked != "refresh":
                    # If a week was clicked, switch to week detail view
                    week_idx, day = table_clicked
                    st.session_state["race_planner"]["selected_week_idx"] = week_idx
                    st.session_state["race_planner"]["view_mode"] = "week"
                    st.rerun()
                    
            elif st.session_state["race_planner"]["view_mode"] == "week":
                # Week Detail View - Single week with day cards and editing
                selected_week_idx = st.session_state["race_planner"]["selected_week_idx"]
                
                if selected_week_idx is not None and selected_week_idx < len(selected_weeks):
                    # Back button to return to table
                    if st.button("← Back to Training Plan Table", key="back_to_table"):
                        st.session_state["race_planner"]["view_mode"] = "table"
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # The detailed view is now handled directly in the render_training_plan_table function
                    # We can just set the view mode back to table to show the integrated view
                    st.session_state["race_planner"]["view_mode"] = "table"
                    st.rerun()
                else:
                    st.session_state["race_planner"]["view_mode"] = "table"
                    st.rerun()
    
    with tab2:
        if selected_race:
            # Analysis Tab
            # 1. Weekly Distance Comparison Chart
            render_weekly_comparison_chart(selected_race, selected_weeks, df)
            
            st.markdown("---")
            
            # 2. AI Analysis Section
            render_ai_analysis_section(
                selected_race_id, 
                selected_race, 
                selected_weeks,
                df, 
                user_info, 
                gist_id, 
                filename, 
                token
            )
    
    with tab3:
        # Settings Tab
        if selected_race:
            result = render_race_settings_form(
                selected_race, 
                selected_race_id, 
                races, 
                user_info, 
                gist_id, 
                filename, 
                token
            )
            
            if result == "deleted":
                st.session_state["race_planner"]["selected_race_id"] = None
                st.rerun()
            elif result:
                st.rerun()
    
    # Add race modal - appears when add_race_modal_open is True
    if st.session_state["race_planner"]["add_race_modal_open"]:
        with st.expander("Add New Race", expanded=True):
            added = render_add_race_form(today, user_info, gist_id, filename, token, races)
            if added:
                st.session_state["race_planner"]["add_race_modal_open"] = False
                st.rerun() 