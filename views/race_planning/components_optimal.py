"""
Optimized UI components for race planning module with table-centric design.
"""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta, date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode, DataReturnMode

# Import calendar component with fallback
try:
    from streamlit_calendar import calendar  # Import the calendar component
except ImportError:
    calendar = None  # Handle missing package gracefully

# Add import for the AgGrid component
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode, DataReturnMode
except ImportError:
    # Fallback if AgGrid isn't available
    AgGrid = GridOptionsBuilder = GridUpdateMode = JsCode = DataReturnMode = None

# Add streamlit_js_eval for better JavaScript integration
try:
    from streamlit_js_eval import streamlit_js_eval
    HAS_JS_EVAL = True
except ImportError:
    HAS_JS_EVAL = False

from views.race_planning.data import save_races, save_training_plan, save_progress_feedback, load_training_plans
from views.race_planning.utils import create_empty_training_plan
from views.race_planning.plan_generators import generate_ai_training_plan, generate_ai_analysis
from utils.date_parser import parse_race_date, parse_training_date, format_date_for_display, safe_parse_date_series


def render_race_selector(races, plans, today, selected_race_id=None):
    """
    Render a compact race selector dropdown with key race info.
    
    Args:
        races: List of races
        plans: Dictionary of training plans
        today: Current date
        selected_race_id: Currently selected race ID
        
    Returns:
        str: Selected race ID
    """
    # Create a formatted list of races for the dropdown
    race_options = []
    race_labels = []
    
    for race in races:
        race_id = race.get("id")
        race_name = race.get("name", "Unnamed Race")
        race_date = parse_race_date(race.get("date", ""))
        race_distance = race.get("distance", 0)
        days_to_race = (race_date - today).days if race_date else 0
        
        # Status text
        if days_to_race < 0:
            status = "Completed"
        elif days_to_race == 0:
            status = "TODAY!"
        else:
            status = f"In {days_to_race} days"
            
        # Format the label for the dropdown
        label = f"{race_name} ({race_distance} km) - {race_date.strftime('%b %d, %Y')} - {status}"
        
        race_options.append(race_id)
        race_labels.append(label)
    
    # Default to the first race if none selected
    if selected_race_id is None and races:
        selected_race_id = races[0].get("id")
    
    # Index of the selected race
    selected_idx = race_options.index(selected_race_id) if selected_race_id in race_options else 0
    
    # Render the dropdown
    st.markdown("### Select Race")
    selected_label = st.selectbox(
        "Choose a race to plan",
        options=race_labels,
        index=selected_idx,
        label_visibility="collapsed"
    )
    
    # Return the race ID that corresponds to the selected label
    selected_idx = race_labels.index(selected_label)
    return race_options[selected_idx]


def render_training_plan_table(race, weeks, today, df, user_info, gist_id, filename, token):
    """
    Render a simplified training plan interface with both table and calendar views.
    
    Args:
        race: Race data
        weeks: List of training weeks
        today: Current date
        df: Running log dataframe
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
        
    Returns:
        str: "refresh" if data was updated, otherwise None
    """
    if not weeks:
        st.warning("No training plan has been created for this race yet. Use the options above to create a plan.")
        return None
    
    # Sort weeks by week number
    weeks = sorted(weeks, key=lambda w: w.get("week_number", 0))
    
    # Race date for highlighting race week
    race_date = parse_race_date(race.get("date", ""))
    
    # Initialize session state for selected week if not already set
    if "selected_week_idx" not in st.session_state:
        # Find current week
        for i, week in enumerate(weeks):
            start_date = parse_training_date(week.get("start_date", ""))
            if start_date:
                end_date = start_date + timedelta(days=6)
                if start_date <= today <= end_date:
                    st.session_state["selected_week_idx"] = i
                    break
        
        # If no current week found, use first week
        if "selected_week_idx" not in st.session_state and weeks:
            st.session_state["selected_week_idx"] = 0
    
    # Create a dataframe for the training plan table
    data = []
    for i, week in enumerate(weeks):
        week_num = int(week.get("week_number", i+1))
        start_date = parse_training_date(week.get("start_date", ""))
        if start_date:
            end_date = start_date + timedelta(days=6)
            is_current_week = start_date <= today <= end_date
            is_race_week = race_date and start_date <= race_date <= end_date
        else:
            end_date = None
            is_current_week = False
            is_race_week = False
        
        mon = week.get("monday", {})
        tue = week.get("tuesday", {})
        wed = week.get("wednesday", {})
        thu = week.get("thursday", {})
        fri = week.get("friday", {})
        sat = week.get("saturday", {})
        sun = week.get("sunday", {})
        week_total = sum(float(day.get("distance", 0)) for day in [mon, tue, wed, thu, fri, sat, sun])
        comment = week.get("comment", "")
        
        date_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}" if start_date and end_date else "Invalid Date"
        
        data.append({
            "week_idx": int(i),
            "Week": f"Week {week_num}",
            "Dates": date_str,
            "Monday": f"{mon.get('distance', 0)} km - {mon.get('description', 'Rest')}" if float(mon.get('distance', 0)) > 0 else "Rest",
            "Tuesday": f"{tue.get('distance', 0)} km - {tue.get('description', 'Rest')}" if float(tue.get('distance', 0)) > 0 else "Rest",
            "Wednesday": f"{wed.get('distance', 0)} km - {wed.get('description', 'Rest')}" if float(wed.get('distance', 0)) > 0 else "Rest",
            "Thursday": f"{thu.get('distance', 0)} km - {thu.get('description', 'Rest')}" if float(thu.get('distance', 0)) > 0 else "Rest",
            "Friday": f"{fri.get('distance', 0)} km - {fri.get('description', 'Rest')}" if float(fri.get('distance', 0)) > 0 else "Rest",
            "Saturday": f"{sat.get('distance', 0)} km - {sat.get('description', 'Rest')}" if float(sat.get('distance', 0)) > 0 else "Rest",
            "Sunday": f"{sun.get('distance', 0)} km - {sun.get('description', 'Rest')}" if float(sun.get('distance', 0)) > 0 else "Rest",
            "Total": f"{float(week_total):.1f} km",
            "current_week": bool(is_current_week),
            "race_week": bool(is_race_week),
            "Comment": comment
        })
    
    # Create the dataframe
    df_plan = pd.DataFrame(data)
    
    # Find the actual current week (where today falls)
    current_week_idx = None
    for i, week in enumerate(weeks):
        start_date = parse_training_date(week.get("start_date", ""))
        if start_date:
            end_date = start_date + timedelta(days=6)
            if start_date <= today <= end_date:
                current_week_idx = i
                break
    
    # Always use current week as default selection
    selected_week = st.session_state.get("selected_week_idx")
    if selected_week is None or selected_week >= len(weeks):
        # Default to current week, or first week if current not found
        selected_week = current_week_idx if current_week_idx is not None else 0
        st.session_state["selected_week_idx"] = selected_week
    
    # Configure the grid options
    gb = GridOptionsBuilder.from_dataframe(df_plan)
    
    # Hide the week_idx column
    gb.configure_column("week_idx", hide=True)
    
    # Hide the conditional styling columns
    gb.configure_column("current_week", hide=True)
    gb.configure_column("race_week", hide=True)
    
    # Configure column widths
    gb.configure_column("Week", width=100)
    gb.configure_column("Dates", width=150)
    day_columns = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for col in day_columns:
        gb.configure_column(col, width=140)
    gb.configure_column("Total", width=100)
    gb.configure_column("Comment", width=180)
    
    # Configure selection
    gb.configure_selection("single", use_checkbox=False)
    
    # Add custom CSS for better row hover and selection effects
    custom_css = {
        ".ag-row-hover": {"background-color": "rgba(102, 126, 234, 0.1) !important"},
        ".ag-row-selected": {"background-color": "rgba(102, 126, 234, 0.2) !important", "border-left": "4px solid #667eea !important"}
    }
    
    # Configure grid styling
    gb.configure_grid_options(
        rowStyle={"cursor": "pointer"},
        animateRows=True,
        domLayout="normal",
        ensureDomOrder=True
    )
    
    # Remove automatic row styling - only use selection highlighting
    # gb.configure_grid_options(getRowStyle=JsCode(row_style_js))
    
    # Build the grid options
    grid_options = gb.build()
    
    # Add JavaScript to auto-select the current week row on grid ready
    auto_select_js = JsCode("""
    function(params) {
        setTimeout(function() {
            // Find and select the row where current_week is true
            params.api.forEachNode(function(node) {
                if (node.data && node.data.current_week === true) {
                    node.setSelected(true);
                    params.api.ensureIndexVisible(node.rowIndex);
                }
            });
        }, 100);
    }
    """)
    grid_options["onGridReady"] = auto_select_js
    
    # Training Calendar heading
    st.markdown("<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'><h4 style='font-size: 1.2rem; margin: 0; color: white;'>Training Plan Table</h4><div style='font-size: 0.9rem; color: #aaa;'>Click any row to view details</div></div>", unsafe_allow_html=True)
    
    # Add stats about the training plan
    try:
        total_distance = sum(float(week.get("total_distance", 0)) for week in weeks)
        if total_distance == 0:  # If total_distance is 0, calculate it from the weeks data
            total_distance = sum(sum(float(week.get(day, {}).get("distance", 0)) for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]) for week in weeks)
            
        total_weeks = len(weeks)
        avg_weekly = total_distance / total_weeks if total_weeks > 0 else 0
        
        # Compact badge-style metrics
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 15px; gap: 12px; flex-wrap: wrap;">
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 8px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.85rem; font-weight: 600; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);">
                    📅 {total_weeks} Weeks
                </span>
            </div>
            <div style="
                background: linear-gradient(135deg, #28a745, #20c997);
                padding: 8px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.85rem; font-weight: 600; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);">
                    🏃 {total_distance:.1f} km Total
                </span>
            </div>
            <div style="
                background: linear-gradient(135deg, #ffc107, #ff8f00);
                padding: 8px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.85rem; font-weight: 600; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);">
                    📊 {avg_weekly:.1f} km/week
                </span>
            </div>
            <div style="
                background: linear-gradient(135deg, #dc3545, #c82333);
                padding: 8px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.85rem; font-weight: 600; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);">
                    ⏱️ {(race_date - today).days if (race_date - today).days >= 0 else "Completed"} days
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        pass  # Silently fail if we can't calculate stats
    
    # Render the AgGrid component
    grid_response = AgGrid(
        df_plan,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=300,
        data_return_mode=DataReturnMode.AS_INPUT,
        custom_css=custom_css,
        key=f"training_plan_grid_{race.get('id', 'default')}"  # Stable key per race
    )
    
    # Process grid selections normally
    selected_rows = grid_response.get("selected_rows")
    
    if selected_rows is not None:
        selected_week_idx = None
        
        if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
            selected_week_idx = selected_rows.iloc[0].get("week_idx")
        elif isinstance(selected_rows, list) and len(selected_rows) > 0:
            selected_week_idx = selected_rows[0].get("week_idx")
        
        # Update session state if we got a valid selection
        if selected_week_idx is not None:
            st.session_state["selected_week_idx"] = selected_week_idx
            selected_week = selected_week_idx
    
    # Always show the calendar view for the selected week (or default current week)
    if selected_week is not None and selected_week < len(weeks):
        week = weeks[selected_week]
        
        # Display the calendar view
        return render_simplified_week_calendar(race, week, selected_week, today, user_info, gist_id, filename, token)
    
    return None


def render_simplified_week_calendar(race, week, week_idx, today, user_info, gist_id, filename, token):
    """
    Render a clean visual week calendar view using native Streamlit components.
    
    Args:
        race: Race data
        week: Selected week data
        week_idx: Week index
        today: Current date
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
        
    Returns:
        str: "refresh" if data was updated, otherwise None
    """
    try:
        # Week data
        week_num = week.get("week_number", week_idx+1)
        start_date = parse_training_date(week.get("start_date", ""))
        end_date = start_date + timedelta(days=6)
        
        # Load all weeks to enable navigation
        plans = load_training_plans(user_info, gist_id, filename, token)
        all_weeks = plans.get(race.get("id"), {}).get("weeks", [])
        
        # Modern minimalistic CSS
        st.markdown("""
        <style>
        /* Clean container styling */
        .stContainer, div[data-testid="column"] {
            background-color: transparent !important;
        }
        
                          /* Readable day cards with better height */
         .modern-day-card {
             background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
             border: 1px solid rgba(255, 255, 255, 0.08);
             border-radius: 8px;
             padding: 12px;
             margin-bottom: 6px;
             height: 150px;
             display: flex;
             flex-direction: column;
             transition: all 0.2s ease;
             box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
         }
         
         .modern-day-card:hover {
             border-color: rgba(255, 255, 255, 0.15);
             transform: translateY(-1px);
             box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
         }
        
                 /* Header row with day and date side by side */
         .day-header-row {
             display: flex;
             justify-content: space-between;
             align-items: center;
             margin-bottom: 8px;
         }
         
         .day-name-modern {
             font-weight: 600;
             font-size: 0.85rem;
             color: #ffffff;
             letter-spacing: 0.3px;
         }
         
         .day-date-modern {
             font-size: 0.75rem;
             color: #888;
             font-weight: 400;
         }
         
         /* Better sized distance badges */
         .distance-badge-modern {
             font-weight: 600;
             font-size: 0.8rem;
             margin-bottom: 8px;
             padding: 4px 10px;
             border-radius: 12px;
             display: inline-block;
             backdrop-filter: blur(10px);
             border: 1px solid rgba(255, 255, 255, 0.1);
         }
         
         .workout-desc-modern {
             font-size: 0.75rem;
             color: #ccc;
             margin-top: auto;
             overflow-wrap: break-word;
             line-height: 1.4;
             font-weight: 400;
             flex-grow: 1;
             overflow-y: auto;
             overflow-x: hidden;
             max-height: 80px;
             padding-right: 4px;
         }
         
         /* Custom scrollbar for workout descriptions */
         .workout-desc-modern::-webkit-scrollbar {
             width: 3px;
         }
         
         .workout-desc-modern::-webkit-scrollbar-track {
             background: rgba(255, 255, 255, 0.05);
             border-radius: 3px;
         }
         
         .workout-desc-modern::-webkit-scrollbar-thumb {
             background: rgba(255, 255, 255, 0.2);
             border-radius: 3px;
         }
         
         .workout-desc-modern::-webkit-scrollbar-thumb:hover {
             background: rgba(255, 255, 255, 0.3);
         }
        

        </style>
        """, unsafe_allow_html=True)
        
        # Compact week header with total distance
        total_distance = sum(float(week.get(day, {}).get("distance", 0)) for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
        week_title = f"Week {week_num}: {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        
        # Single row layout with week title and total distance aligned left
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 12px; gap: 12px;">
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 8px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.85rem; font-weight: 600; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);">
                    {week_title}
                </span>
            </div>
            <div style="
                background: linear-gradient(135deg, #28a745, #20c997);
                padding: 8px 16px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 0.85rem; font-weight: 600; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);">
                    {total_distance:.1f} km
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact notes section
        st.markdown("""
        <div style="margin: 8px 0 6px 0;">
            <span style="color: #ccc; font-size: 0.8rem; font-weight: 500; display: flex; align-items: center; gap: 6px;">
                💬 <span>Week Notes</span>
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Always use the current week's comment, not session state
        current_week_comment = week.get("comment", "")
        
        week_comment = st.text_area(
            "Week Notes", 
            value=current_week_comment, 
            height=68, 
            key=f"comment_week_{week_idx}_{week_num}",
            placeholder="Training focus, goals, notes...",
            label_visibility="collapsed"
        )
        
        # Only save if the comment actually changed
        if week_comment != current_week_comment:
            # Update the week comment in the data
            current_plan = plans.get(race.get("id"), {})
            plan_weeks = current_plan.get("weeks", [])
            plan_weeks[week_idx]["comment"] = week_comment
            current_plan["weeks"] = plan_weeks
            save_training_plan(race.get("id"), current_plan, user_info, gist_id, filename, token)
        
        # Initialize session state for edit popup
        if "edit_day_key" not in st.session_state:
            st.session_state.edit_day_key = None
        
        # Add some space before the calendar
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # Custom calendar layout
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        # Modern button and form styling
        st.markdown("""
        <style>
        /* Make all columns equal width and properly aligned */
        [data-testid="column"] {
            width: calc(100% / 7) !important;
            flex: none !important;
            padding: 0 4px !important;
        }
        
        /* Ensure consistent column spacing */
        div[data-testid="column"]:first-child {
            padding-left: 0 !important;
        }
        
        div[data-testid="column"]:last-child {
            padding-right: 0 !important;
        }
        
        /* Compact button styling */
        .main div[data-testid="stButton"] button {
            padding: 6px 12px !important;
            font-size: 11px !important;
            height: 28px !important;
            min-height: 28px !important;
            line-height: 1.1 !important;
            width: 100%;
            border-radius: 6px !important;
            background: linear-gradient(145deg, #2d2d2d, #3a3a3a) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            color: white !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .main div[data-testid="stButton"] button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }
        
        /* Primary button styling */
        .main div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(145deg, #667eea, #764ba2) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        /* Target text inside buttons */
        .main div[data-testid="stButton"] button p,
        .main div[data-testid="stButton"] button span {
            font-size: 12px !important;
            margin: 0 !important;
            padding: 0 !important;
            font-weight: 500 !important;
        }
        
        /* Modern form styling */
        .edit-form-container {
            margin-top: 10px;
            background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Input field styling */
        .stNumberInput input,
        .stTextArea textarea {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: white !important;
            font-size: 13px !important;
            padding: 10px !important;
        }
        
        .stNumberInput input:focus,
        .stTextArea textarea:focus {
            border-color: rgba(102, 126, 234, 0.5) !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
        }
        
        /* Label styling */
        .stNumberInput label,
        .stTextArea label {
            font-size: 13px !important;
            color: #ccc !important;
            font-weight: 500 !important;
            margin-bottom: 6px !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: linear-gradient(145deg, #2d2d2d, #3a3a3a) !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        .streamlit-expanderContent {
            background: linear-gradient(145deg, #1a1a1a, #2a2a2a) !important;
            border-radius: 0 0 10px 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-top: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create 7 columns for days of the week
        cols = st.columns(7)
        
        # Create day cards
        for day_idx, (col, day_key) in enumerate(zip(cols, day_keys)):
            with col:
                workout = week.get(day_key, {})
                distance = float(workout.get("distance", 0))
                description = workout.get("description", "Rest")
                badge_color = "#17a2b8"  # Default blue
                if distance > 0:
                    desc_lower = description.lower()
                    if "long" in desc_lower:
                        badge_color = "#007bff"  # Dark blue
                    elif "tempo" in desc_lower:
                        badge_color = "#28a745"  # Green
                    elif "race" in desc_lower:
                        badge_color = "#dc3545"  # Red
                day_date = start_date + timedelta(days=day_idx)
                
                # Create a modern card for this day with date on first row
                st.markdown(f"""
                <div class="modern-day-card">
                    <div class="day-header-row">
                        <span class="day-name-modern">{day_names[day_idx]}</span>
                        <span class="day-date-modern">{day_date.strftime('%b')} {day_date.day}</span>
                    </div>
                    {f'<div class="distance-badge-modern" style="background-color: {badge_color}; color: white;">{distance:.1f} km</div>' if distance > 0 else '<div style="color: #777; font-style: italic; font-size: 0.85rem; padding: 6px 12px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); display: inline-block;">Rest Day</div>'}
                    <div class="workout-desc-modern">{description if distance > 0 else ""}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add edit button section
                
                # Edit button
                if st.button("Edit", key=f"edit_{day_key}", use_container_width=True):
                    st.session_state.edit_day_key = day_key
                    st.rerun()
                
                # Show edit form if this is the day being edited
                if st.session_state.edit_day_key == day_key:
                    # Create edit form with proper Streamlit widgets
                    st.markdown("---")
                    st.markdown("**Edit Workout**")
                    
                    # Use Streamlit input widgets instead of HTML
                    current_distance = distance if distance > 0 else 0.0
                    current_desc = description if description != "Rest" else ""
                    
                    new_distance = st.number_input(
                        "Distance (km)", 
                        min_value=0.0, 
                        step=0.5, 
                        value=current_distance,
                        key=f"distance_input_{day_key}"
                    )
                    
                    new_description = st.text_area(
                        "Description", 
                        value=current_desc,
                        height=80,
                        key=f"desc_input_{day_key}"
                    )
                    
                    # Save and cancel buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", key=f"save_{day_key}", use_container_width=True, type="primary"):
                            try:
                                # Get the current plan and weeks first
                                current_plan = plans.get(race.get("id"), {})
                                plan_weeks = current_plan.get("weeks", [])
                                
                                # Update the specific day with new values
                                if new_distance <= 0:
                                    plan_weeks[week_idx][day_key] = {
                                        "distance": 0.0,
                                        "description": "Rest"
                                    }
                                else:
                                    plan_weeks[week_idx][day_key] = {
                                        "distance": float(new_distance),
                                        "description": new_description if new_description.strip() else "Easy Run"
                                    }
                                
                                # Save the updated plan
                                current_plan["weeks"] = plan_weeks
                                save_training_plan(race.get("id"), current_plan, user_info, gist_id, filename, token)
                                
                                # Clear edit state and refresh
                                st.session_state.edit_day_key = None
                                st.success("Workout updated!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error saving: {str(e)}")
                    
                    with col2:
                        if st.button("Cancel", key=f"cancel_{day_key}", use_container_width=True):
                            st.session_state.edit_day_key = None
                            st.rerun()
        
        return None
    
    except Exception as e:
        st.error(f"Error rendering calendar: {str(e)}")
        return None


def render_plan_generation_tools(race_id, race, weeks, user_info, gist_id, filename, token):
    """
    Render tools for generating a training plan with simple buttons.
    
    Args:
        race_id: Race ID
        race: Race data
        weeks: List of training weeks
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
    """
    # Simple heading
    st.markdown("### Create Training Plan")
    
    # Create simple buttons for each plan generation method
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 AI Coach", use_container_width=True, type="primary"):
            st.session_state["selected_plan_method"] = "ai"
    
    with col2:
        if st.button("📊 Google Sheets", use_container_width=True):
            st.session_state["selected_plan_method"] = "sheets"
    
    with col3:
        if st.button("✏️ Manual Entry", use_container_width=True):
            st.session_state["selected_plan_method"] = "manual"
    
    # Initialize plan method in session state if not present
    if "selected_plan_method" not in st.session_state:
        st.session_state["selected_plan_method"] = None
    
    # Show different forms based on the selected method
    if st.session_state["selected_plan_method"] == "ai":
        st.markdown("### 🤖 AI Training Plan Generator")
        
        # Compact race info
        race_date = parse_race_date(race.get("date", ""))
        race_distance = race.get("distance", 0)
        race_name = race.get("name", "")
        days_to_race = (race_date - datetime.today().date()).days
        
        st.markdown(f"**{race_name}** • {race_distance} km • {race_date.strftime('%b %d, %Y')} • {days_to_race} days away")
        
        # Simple AI notes input
        ai_note = st.text_area(
            "Notes for AI Coach",
            placeholder="Any special requirements? (e.g., 'focus on hills', 'include cross-training', 'avoid back-to-back long runs')",
            height=80,
            help="Optional: Tell the AI about your preferences, constraints, or goals"
        )
        
        # Action buttons
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Generate AI Training Plan", use_container_width=True, type="primary"):
                with st.spinner("Creating your personalized training plan..."):
                    try:
                        # Use runner profile data and race settings
                        generate_ai_training_plan(race_id, race, weeks, ai_note, user_info, gist_id, filename, token)
                        st.success("AI training plan generated successfully!")
                        st.session_state["selected_plan_method"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating AI plan: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state["selected_plan_method"] = None
                st.rerun()
            
    elif st.session_state["selected_plan_method"] == "sheets":
        st.markdown("### 📊 Google Sheets Import")
        
        # Google Sheets integration
        sheets_url = st.text_input(
            "Google Sheets URL",
            placeholder="https://docs.google.com/spreadsheets/d/..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            sheet_name = st.text_input("Sheet Name (optional)", placeholder="Sheet1")
        with col2:
            has_header = st.checkbox("First row is header", value=True)
        
        # Import button
        if st.button("Import from Google Sheets", use_container_width=True, type="primary"):
            if not sheets_url:
                st.error("Please enter a valid Google Sheets URL")
            else:
                st.info("This feature would connect to the Google Sheets API to import the training plan.")
                # Reset the method after user sees the message
                st.session_state["selected_plan_method"] = None
                st.rerun()
        
        # Cancel button
        if st.button("Cancel", use_container_width=True):
            st.session_state["selected_plan_method"] = None
            st.rerun()
            
    elif st.session_state["selected_plan_method"] == "manual":
        st.markdown("### ✏️ Manual Training Plan Creation")
        
        # Manual plan setup
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Training Start Date", 
                value=datetime.today().date(),
                help="When do you want to start your training plan?"
            )
        
        with col2:
            # The end date is automatically the race date
            race_date = parse_race_date(race.get("date", ""))
            days_to_race = (race_date - start_date).days
            weeks_to_race = days_to_race // 7
            
            st.info(f"Race Date: {race_date.strftime('%B %d, %Y')} - {days_to_race} days ({weeks_to_race} weeks) from start date")
        
        default_format = st.checkbox("Use default week format", value=True, help="Pre-fill with a basic training pattern")
        
        # Create button
        if st.button("Create Empty Training Plan", use_container_width=True, type="primary"):
            with st.spinner("Creating training plan template..."):
                # Generate empty training plan
                new_weeks = create_empty_training_plan(start_date, race_date, race.get("distance", 0), default_format=default_format)
                
                # Save to database
                save_training_plan(race_id, {"weeks": new_weeks}, user_info, gist_id, filename, token)
                
                st.success("Empty training plan created! You can now fill in the details.")
                st.session_state["selected_plan_method"] = None  # Reset the method
                st.rerun()
        
        # Cancel button
        if st.button("Cancel", use_container_width=True):
            st.session_state["selected_plan_method"] = None
            st.rerun()


def render_weekly_comparison_chart(race, weeks, df):
    """
    Render a chart comparing planned vs. actual weekly distances.
    
    Args:
        race: Race data
        weeks: List of training weeks
        df: Running log dataframe
    """
    st.markdown("### Planned vs. Actual Weekly Distance")
    
    # Early return if no data
    if not weeks:
        st.info("No training plan data available for comparison.")
        return
    
    # Prepare chart data
    chart_data = []
    
    for week in sorted(weeks, key=lambda w: w.get("week_number", 0)):
        week_num = week.get("week_number", 0)
        start_date = parse_training_date(week.get("start_date", ""))
        end_date = start_date + timedelta(days=6)
        
        # Planned distance
        planned_distance = sum(float(week.get(day, {}).get("distance", 0)) for day in 
                           ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
        
        chart_data.append({
            "Week": f"Week {week_num}",
            "Type": "Planned",
            "Distance (km)": planned_distance
        })
        
        # Actual distance from activity log
        actual_distance = 0
        try:
            if df is not None and not df.empty:
                # Try to find date and distance columns with flexible naming
                date_col = next((col for col in df.columns if col.lower() == 'date'), None)
                distance_col = next((col for col in df.columns if 'distance' in col.lower()), None)
                
                if date_col and distance_col:
                    # Use safe date parsing for the dataframe
                    df_dates = safe_parse_date_series(df[date_col], 'date')
                    actual_df = df[(df_dates >= start_date) & (df_dates <= end_date)]
                    actual_distance = actual_df[distance_col].sum() if not actual_df.empty else 0
                else:
                    if week_num == 1:  # Only show warning once
                        # Find available columns to help user troubleshoot
                        available_cols = ", ".join(df.columns.tolist())
                        st.warning(f"Running log data doesn't contain required 'Date' or 'Distance' columns. Available columns: {available_cols}")
        except Exception as e:
            if week_num == 1:  # Only show warning once
                st.warning(f"Error processing actual distances: {str(e)}")
        
        chart_data.append({
            "Week": f"Week {week_num}",
            "Type": "Actual",
            "Distance (km)": actual_distance
        })
    
    # Create chart
    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        
        # Create a layered chart with both areas and points for better visualization
        base = alt.Chart(chart_df).encode(
            x=alt.X("Week:N", title="Training Week", sort=None)
        )
        
        # Area layers with transparency
        area_planned = base.mark_area(opacity=0.4, color="#FF9633").encode(
            y=alt.Y("Distance (km):Q", title="Distance (km)")
        ).transform_filter(
            alt.datum.Type == 'Planned'
        )
        
        area_actual = base.mark_area(opacity=0.4, color="#1EBEFF").encode(
            y=alt.Y("Distance (km):Q", title="Distance (km)")
        ).transform_filter(
            alt.datum.Type == 'Actual'
        )
        
        # Add points and lines for clarity
        line_planned = base.mark_line(color="#E87203", strokeWidth=2).encode(
            y=alt.Y("Distance (km):Q")
        ).transform_filter(
            alt.datum.Type == 'Planned'
        )
        
        line_actual = base.mark_line(color="#0095DD", strokeWidth=2).encode(
            y=alt.Y("Distance (km):Q")
        ).transform_filter(
            alt.datum.Type == 'Actual'
        )
        
        point_planned = base.mark_point(color="#E87203", filled=True, size=80).encode(
            y=alt.Y("Distance (km):Q")
        ).transform_filter(
            alt.datum.Type == 'Planned'
        )
        
        point_actual = base.mark_point(color="#0095DD", filled=True, size=80).encode(
            y=alt.Y("Distance (km):Q")
        ).transform_filter(
            alt.datum.Type == 'Actual'
        )
        
        # Combine all layers
        chart = alt.layer(
            area_planned, area_actual, 
            line_planned, line_actual,
            point_planned, point_actual
        ).resolve_scale(
            y='shared'
        ).properties(
            width='container',
            height=300
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=True,
            gridOpacity=0.2
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data available for the chart.")


def render_ai_analysis_section(race_id, race, weeks, df, user_info, gist_id, filename, token):
    """
    Render AI analysis section with modern, minimalistic UI.
    
    Args:
        race_id: Race ID
        race: Race data
        weeks: List of training weeks
        df: Running log dataframe
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
    """
    # Modern CSS styling for the analysis section
    st.markdown("""
    <style>
    /* Modern tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background: transparent;
        border-radius: 8px;
        color: #ccc;
        font-weight: 500;
        padding: 0 16px;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }
    
    /* Modern expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(145deg, #2d2d2d, #3a3a3a) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: rgba(102, 126, 234, 0.3) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    }
    
    .streamlit-expanderContent {
        background: linear-gradient(145deg, #1a1a1a, #2a2a2a) !important;
        border-radius: 0 0 12px 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-top: none !important;
        padding: 16px !important;
    }
    
    /* Primary button enhancement */
    .main .stButton button[kind="primary"] {
        background: linear-gradient(145deg, #667eea, #764ba2) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    .main .stButton button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Delete button styling */
    .main .stButton button[title="Delete this analysis"] {
        background: rgba(220, 53, 69, 0.1) !important;
        border: 1px solid rgba(220, 53, 69, 0.3) !important;
        color: #dc3545 !important;
        border-radius: 8px !important;
        padding: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    .main .stButton button[title="Delete this analysis"]:hover {
        background: rgba(220, 53, 69, 0.2) !important;
        border-color: #dc3545 !important;
        transform: scale(1.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Modern section header
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem; margin-top: 2rem;">
        <span style="font-size: 1.5rem;">🧠</span>
        <h3 style="margin: 0; font-size: 1.4rem; font-weight: 600; color: white;">AI Training Analysis</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Load AI feedback history
    from views.race_planning.data import load_progress_feedback
    
    try:
        ai_history_dict = load_progress_feedback(user_info, gist_id, filename, token)
        if isinstance(ai_history_dict, dict):
            ai_history = ai_history_dict.get(race_id, [])
            # Validate entries
            if not isinstance(ai_history, list):
                st.warning("Feedback history has invalid format. Resetting.")
                ai_history = []
        else:
            st.warning("Invalid feedback history format. Using empty history.")
            ai_history = []
    except Exception as e:
        st.warning(f"Error loading feedback history: {str(e)}")
        ai_history = []

    # Tab layout for better organization
    analysis_tab, history_tab = st.tabs(["🔄 Generate New Analysis", "📚 Analysis History"])
    
    with analysis_tab:
        # Two column layout for action and info
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # Generate analysis button with modern styling
            if st.button("🧠 Get AI Training Analysis", use_container_width=True, type="primary"):
                with st.spinner("Analyzing your training data..."):
                    try:
                        # Validate dataframe has required columns before processing
                        if df is not None and not df.empty:
                            missing_columns = []
                            # Try to find date and distance columns with flexible naming
                            date_col = next((col for col in df.columns if col.lower() == 'date'), None)
                            distance_col = next((col for col in df.columns if 'distance' in col.lower()), None)
                            
                            if not date_col:
                                missing_columns.append("Date")
                            if not distance_col:
                                missing_columns.append("Distance")
                            
                            if missing_columns:
                                # Find available columns to help user troubleshoot
                                available_cols = ", ".join(df.columns.tolist())
                                st.warning(f"Your running log is missing these required columns: {', '.join(missing_columns)}. Available columns: {available_cols}")
                                st.info("Analysis will be based on plan data only.")
                        
                        ai_feedback = generate_ai_analysis(race_id, race, user_info, gist_id, filename, token, df=df)
                        if ai_feedback:
                            st.success("Analysis complete!")
                            # Reload history
                            try:
                                ai_history_dict = load_progress_feedback(user_info, gist_id, filename, token)
                                if isinstance(ai_history_dict, dict):
                                    ai_history = ai_history_dict.get(race_id, [])
                                else:
                                    ai_history = []
                            except Exception as reload_error:
                                st.warning(f"Error reloading feedback history: {str(reload_error)}")
                    except Exception as e:
                        st.error(f"Error generating analysis: {str(e)}")
        
        with col2:
            # Info card about what AI analysis provides
            st.markdown("""
            <div style="
                background: linear-gradient(145deg, #1a1a1a, #2a2a2a);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 1.5rem;
                border-left: 4px solid #667eea;
            ">
                <div style="font-weight: 600; margin-bottom: 0.75rem; color: #667eea; font-size: 1rem;">💡 AI Analysis Includes</div>
                <div style="font-size: 0.9rem; line-height: 1.5; color: #ccc;">
                    • <strong>Race Readiness:</strong> Current fitness assessment<br>
                    • <strong>Training Strengths:</strong> What's working well<br>
                    • <strong>Immediate Concerns:</strong> Areas needing attention<br>
                    • <strong>This Week's Plan:</strong> Specific recommendations<br>
                    • <strong>Next Week Adjustments:</strong> Key modifications
                </div>
            </div>
            """, unsafe_allow_html=True)

    with history_tab:
        # Display analysis history with modern cards
        if ai_history:
            # Helper function to extract date from any entry format
            def get_entry_date(entry):
                if isinstance(entry, dict):
                    return entry.get('date', 'Unknown Date')
                elif isinstance(entry, list) and len(entry) >= 1:
                    return entry[0] if entry[0] else 'Unknown Date'
                else:
                    return 'Unknown Date'
            
            # Sort by date (newest first) - handle both dict and list formats
            try:
                sorted_history = sorted(ai_history, key=get_entry_date, reverse=True)
            except Exception:
                # If sorting fails, just reverse the list
                sorted_history = list(reversed(ai_history))
            
            for idx, entry in enumerate(sorted_history):
                # Handle case where entry might be list or dict
                if isinstance(entry, dict):
                    date = entry.get("date", "Unknown Date")
                    summary = entry.get("summary", "[No summary]")
                elif isinstance(entry, list) and len(entry) >= 2:
                    # Assuming list format is [date, summary, ...]
                    date = entry[0] if entry[0] else "Unknown Date"
                    summary = entry[1] if entry[1] else "[No summary]"
                else:
                    # Fallback for unexpected formats
                    date = "Unknown Date"
                    summary = str(entry) if entry else "[No summary]"
                
                # Modern expandable analysis card
                with st.expander(f"📊 Analysis from {date}", expanded=(idx == 0)):
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="
                            background: rgba(255, 255, 255, 0.02);
                            border: 1px solid rgba(255, 255, 255, 0.08);
                            border-radius: 12px;
                            padding: 1.5rem;
                            border-left: 4px solid #667eea;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            line-height: 1.7;
                            color: #ffffff;
                        ">
                            {summary}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Delete button for individual analyses
                        if st.button("🗑️", key=f"delete_analysis_{idx}_{date}", help="Delete this analysis"):
                            # Here you would implement delete functionality
                            st.toast("Delete functionality would be implemented here", icon="🗑️")
        else:
            # Empty state with modern design
            st.markdown("""
            <div style="
                text-align: center; 
                padding: 3rem 2rem; 
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                margin-top: 1rem;
            ">
                <span style="font-size: 3rem; opacity: 0.6;">🧠</span><br>
                <div style="margin-top: 1rem; font-size: 1.1rem; color: #ccc;">No AI analysis history yet</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.7; color: #999;">
                    Generate your first analysis in the 'Generate New Analysis' tab to get personalized training insights.
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_add_race_form(today, user_info, gist_id, filename, token, races):
    """
    Render form for adding a new race.
    
    Args:
        today: Current date
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
        races: List of races
        
    Returns:
        bool: True if race was added, False otherwise
    """
    with st.form("add_race_form"):
        race_name = st.text_input("Race Name", placeholder="e.g. Berlin Marathon")
        
        col1, col2 = st.columns(2)
        with col1:
            race_date = st.date_input("Race Date", value=today + timedelta(days=90))
        with col2:
            race_distance = st.number_input("Distance (km)", min_value=1.0, step=0.1, value=42.2)
        
        col1, col2 = st.columns(2)
        with col1:
            race_type = st.selectbox(
                "Race Type",
                options=["Road", "Trail", "Ultra"],
                index=0
            )
        with col2:
            elevation_gain = st.number_input("Elevation (m)", min_value=0.0, step=10.0, value=0.0)
        
        col1, col2 = st.columns(2)
        with col1:
            goal_time = st.text_input("Goal Time", placeholder="e.g. 3:45:00")
        with col2:
            start_date = st.date_input("Training Start Date", value=today)
        
        notes = st.text_area("Notes", placeholder="Add any notes about this race...", height=80)
        
        # Submit button
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Race", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True, type="secondary")
        
        if submitted:
            if race_name.strip() == "":
                st.error("Please enter a race name.")
                return False
                
            if any(r.get("name", "").strip().lower() == race_name.strip().lower() for r in races):
                st.error("A race with this name already exists. Please choose a different name.")
                return False
            
            # Create a new race
            new_race = {
                "id": f"race_{len(races)+1}",
                "name": race_name,
                "date": race_date.isoformat(),
                "distance": race_distance,
                "type": race_type,
                "elevation_gain": elevation_gain,
                "goal_time": goal_time,
                "notes": notes,
                "created_at": datetime.now().isoformat(),
                "training_start_date": start_date.isoformat(),
            }
            
            # Create empty training plan
            weeks = create_empty_training_plan(start_date, race_date, race_distance)
            
            # Save race and plan
            races.insert(0, new_race)
            save_races(races, user_info, gist_id, filename, token)
            save_training_plan(new_race["id"], {"weeks": weeks}, user_info, gist_id, filename, token)
            
            # Update selected race
            st.session_state["race_planner"]["selected_race_id"] = new_race["id"]
            
            st.success(f"Race '{race_name}' created!")
            return True
        
        if cancelled:
            return True
    
    return False 

def render_race_settings_form(selected_race, selected_race_id, races, user_info, gist_id, filename, token):
    """
    Render race settings form for the Settings tab.
    
    Args:
        selected_race: Current race data
        selected_race_id: Selected race ID
        races: List of all races
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
    """
    from datetime import datetime
    import pandas as pd
    from views.race_planning.data import save_races
    
    st.markdown("### Race Settings")
    
    with st.form("race_settings_form"):
        race_name = st.text_input("Race Name", value=selected_race.get("name", ""))
        
        col1, col2 = st.columns(2)
        with col1:
            race_date = st.date_input(
                "Race Date", 
                value=parse_race_date(selected_race.get("date", datetime.today())) or datetime.today().date()
            )
        with col2:
            race_distance = st.number_input(
                "Distance (km)",
                min_value=1.0,
                step=0.1,
                value=float(selected_race.get("distance", 0))
            )
        
        col1, col2 = st.columns(2)
        with col1:
            race_type = st.selectbox(
                "Race Type",
                options=["Road", "Trail", "Ultra"],
                index=["Road", "Trail", "Ultra"].index(selected_race.get("type", "Road"))
            )
        with col2:
            elevation_gain = st.number_input(
                "Elevation (m)",
                min_value=0.0,
                step=10.0,
                value=float(selected_race.get("elevation_gain", 0))
            )
        
        # Training Settings
        st.markdown("### Training Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            goal_time = st.text_input("Goal Time", value=selected_race.get("goal_time", ""), placeholder="e.g. 3:45:00")
        with col2:
            training_start_date = st.date_input(
                "Training Start Date", 
                value=parse_training_date(selected_race.get("training_start_date", datetime.today())) or datetime.today().date()
            )
        
        notes = st.text_area("Notes", value=selected_race.get("notes", ""), height=100)
        
        # Submit button
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("💾 Save Settings", use_container_width=True)
        with col2:
            delete_button = st.form_submit_button("🗑️ Delete Race", use_container_width=True, type="secondary")
    
    if submit_button:
        # Update race data
        for r in races:
            if r.get("id") == selected_race_id:
                r["name"] = race_name
                r["distance"] = race_distance
                r["goal_time"] = goal_time
                r["training_start_date"] = training_start_date.isoformat() if hasattr(training_start_date, 'isoformat') else str(training_start_date)
                r["date"] = race_date.isoformat() if hasattr(race_date, 'isoformat') else str(race_date)
                r["type"] = race_type
                r["elevation_gain"] = elevation_gain
                r["notes"] = notes
                break
        
        save_races(races, user_info, gist_id, filename, token)
        st.success("Race settings updated!")
        return True
        
    if delete_button:
        st.warning("⚠️ Are you sure you want to delete this race? This action cannot be undone.")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Yes, Delete", use_container_width=True, key="confirm_delete"):
                # Remove race from races list
                updated_races = [r for r in races if r.get("id") != selected_race_id]
                save_races(updated_races, user_info, gist_id, filename, token)
                st.success("Race deleted!")
                return "deleted"
        
        with col2:
            if st.button("Cancel", use_container_width=True, key="cancel_delete"):
                st.rerun()
    
    return None

# Add some CSS to make the UI look cleaner
st.markdown("""
<style>
    /* Style the buttons in the calendar - specific to race planning */
    .main button[kind="secondary"] {
        background-color: #272727 !important;
        color: #AAA !important;
        border: 1px solid #333 !important;
        border-radius: 4px !important;
        padding: 2px 8px !important;
        font-size: 12px !important;
    }
    
    .main button[kind="primary"] {
        background-color: #FF4B4B !important;
        border-color: #FF4B4B !important;
    }
    
    /* Style input fields */
    .main input[type="number"], .main input[type="text"] {
        background-color: #333 !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 4px !important;
    }
    
    /* Add card styling to columns */
    .main div.css-1r6slb0 {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 8px;
        margin: 4px;
        min-height: 150px;
    }
</style>
""", unsafe_allow_html=True)

# Adjust the day column creation to add more space between days
st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True) 

# Improved button styling for better readability
st.markdown('''
<style>
/* Improved global button styling - specific to race planning */
.main button {
    font-size: 12px !important;
    padding: 6px 12px !important;
    min-height: 32px !important;
}

.main button p, .main button span {
    font-size: 12px !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Enhanced save/cancel buttons */
.main .stButton button[kind="secondary"], .main .stButton button[kind="primary"] {
    font-size: 12px !important;
    padding: 8px 16px !important;
    min-height: 36px !important;
}

.main .stButton button[kind="secondary"] p, .main .stButton button[kind="primary"] p,
.main .stButton button[kind="secondary"] span, .main .stButton button[kind="primary"] span {
    font-size: 12px !important;
}
</style>
''', unsafe_allow_html=True) 