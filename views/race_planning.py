import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import json
import os
from openai import OpenAI

# Create race planning directory if it doesn't exist
os.makedirs("data/races", exist_ok=True)

# Function to load saved races
def load_saved_races():
    try:
        with open("data/races/races.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Function to save races
def save_races(races):
    try:
        with open("data/races/races.json", "w") as f:
            json.dump(races, f)
        return True
    except Exception as e:
        st.error(f"Error saving races: {e}")
        return False

# Function to load training plans
def load_training_plans():
    try:
        with open("data/races/training_plans.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Function to save training plans
def save_training_plan(race_id, plan):
    try:
        plans = load_training_plans()
        plans[race_id] = plan
        with open("data/races/training_plans.json", "w") as f:
            json.dump(plans, f)
        return True
    except Exception as e:
        st.error(f"Error saving training plan: {e}")
        return False

def render_race_planning(df, today):
    # Ensure 'today' is a date object
    if isinstance(today, datetime):
        today = today.date()
    
    st.title("🏁 Race Planning")
    
    # Load existing races
    races = load_saved_races()
    
    # Section for adding a new race
    with st.expander("➕ Add a New Race", expanded=len(races) == 0):
        with st.form("add_race_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                race_name = st.text_input("Race Name", key="race_name_input")
                race_date = st.date_input("Race Date", min_value=today)
                
            with col2:
                race_distance = st.number_input("Distance (km)", min_value=1.0, step=0.1)
                race_type = st.selectbox("Race Type", ["Road", "Trail", "Track", "Virtual"])
            
            notes = st.text_area("Race Notes (optional)")
            
            submitted = st.form_submit_button("Save Race")
            if submitted and race_name:
                new_race = {
                    "id": f"race_{len(races) + 1}",
                    "name": race_name,
                    "date": race_date.isoformat(),
                    "distance": race_distance,
                    "type": race_type,
                    "notes": notes,
                    "created_at": datetime.now().isoformat()
                }
                races.append(new_race)
                save_success = save_races(races)
                if save_success:
                    st.success(f"Race '{race_name}' added successfully!")
                    st.rerun()
    
    # Show existing races
    if races:
        st.subheader("Your Upcoming Races")
        
        for i, race in enumerate(races):
            race_date = datetime.fromisoformat(race["date"]).date()
            days_until = (race_date - today).days
            
            with st.container():
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.markdown(f"### {race['name']}")
                    st.write(f"📅 {race_date} ({'in ' + str(days_until) + ' days' if days_until > 0 else 'Today!' if days_until == 0 else 'Completed'})")
                    st.write(f"🏃 {race['distance']} km | {race['type']}")
                    if race["notes"]:
                        st.write(f"📝 {race['notes']}")
                
                with cols[1]:
                    if st.button("🗑️ Delete", key=f"delete_race_{i}"):
                        races.pop(i)
                        save_races(races)
                        st.rerun()
                
                with cols[2]:
                    if st.button("📋 Training Plan", key=f"plan_race_{i}"):
                        st.session_state["selected_race"] = race
                        st.rerun()
            
            st.markdown("---")
        
        # Training plan section - show if a race is selected
        if "selected_race" in st.session_state:
            selected_race = st.session_state["selected_race"]
            race_date = datetime.fromisoformat(selected_race["date"]).date()
            
            st.header(f"Training Plan: {selected_race['name']}")
            st.write(f"Race Date: {race_date} | Distance: {selected_race['distance']} km")
            
            # Load existing plan if available
            plans = load_training_plans()
            race_id = selected_race["id"]
            existing_plan = plans.get(race_id, {})
            
            # AI Coach plan generation
            if not existing_plan:
                if st.button("🤖 Generate AI Coach Plan"):
                    with st.spinner("AI Coach is creating your training plan..."):
                        # Generate plan using OpenAI
                        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                        
                        # Prepare recent run history for context
                        recent_runs = df.sort_values("Date", ascending=False).head(10)
                        run_history = recent_runs.to_string()
                        
                        # Calculate training period
                        weeks_to_train = min(16, max(8, (race_date - today).days // 7))
                        start_date = race_date - timedelta(weeks=weeks_to_train)
                        
                        prompt = f"""
                        Create a {weeks_to_train} week running training plan for a {selected_race['distance']} km {selected_race['type']} race on {race_date}.
                        
                        Recent running history:
                        {run_history}
                        
                        Create a structured training plan with:
                        1. Weekly mileage gradually increasing then tapering before race
                        2. Each day should specify distance in km and run type (easy, tempo, intervals, long, rest)
                        3. Include weekly totals and brief comments on the focus for each week
                        
                        Format the response as JSON with structure:
                        {{
                            "weeks": [
                                {{
                                    "week_number": 1,
                                    "start_date": "YYYY-MM-DD",
                                    "monday": {{"distance": 5, "description": "Easy run"}},
                                    "tuesday": {{"distance": 0, "description": "Rest"}},
                                    "wednesday": {{"distance": 6, "description": "Tempo run"}},
                                    "thursday": {{"distance": 0, "description": "Rest"}},
                                    "friday": {{"distance": 5, "description": "Easy run"}},
                                    "saturday": {{"distance": 0, "description": "Rest"}},
                                    "sunday": {{"distance": 10, "description": "Long run"}},
                                    "total_distance": 26,
                                    "comment": "Base building week"
                                }},
                                // more weeks...
                            ]
                        }}
                        """
                        
                        try:
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo-16k",
                                messages=[
                                    {"role": "system", "content": "You are an expert running coach who creates training plans for races."},
                                    {"role": "user", "content": prompt}
                                ],
                                response_format={"type": "json_object"}
                            )
                            
                            plan_json = response.choices[0].message.content
                            plan_data = json.loads(plan_json)
                            
                            # Save the generated plan
                            save_training_plan(race_id, plan_data)
                            existing_plan = plan_data
                            st.success("AI Coach has created your training plan!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error generating training plan: {e}")
            
            # Show and allow editing of the training plan
            if existing_plan and "weeks" in existing_plan:
                # Convert plan to DataFrame for display and editing
                plan_data = []
                for week in existing_plan["weeks"]:
                    week_data = {
                        "Week": f"Week {week['week_number']}",
                        "Start Date": week.get("start_date", ""),
                        "Monday": f"{week.get('monday', {}).get('distance', 0)} km: {week.get('monday', {}).get('description', '')}",
                        "Tuesday": f"{week.get('tuesday', {}).get('distance', 0)} km: {week.get('tuesday', {}).get('description', '')}",
                        "Wednesday": f"{week.get('wednesday', {}).get('distance', 0)} km: {week.get('wednesday', {}).get('description', '')}",
                        "Thursday": f"{week.get('thursday', {}).get('distance', 0)} km: {week.get('thursday', {}).get('description', '')}",
                        "Friday": f"{week.get('friday', {}).get('distance', 0)} km: {week.get('friday', {}).get('description', '')}",
                        "Saturday": f"{week.get('saturday', {}).get('distance', 0)} km: {week.get('saturday', {}).get('description', '')}",
                        "Sunday": f"{week.get('sunday', {}).get('distance', 0)} km: {week.get('sunday', {}).get('description', '')}",
                        "Total": f"{week.get('total_distance', 0)} km",
                        "Comment": week.get("comment", "")
                    }
                    plan_data.append(week_data)
                
                plan_df = pd.DataFrame(plan_data)
                
                # Use the Streamlit data editor for editing the plan
                st.subheader("Training Schedule")
                edited_df = st.data_editor(
                    plan_df,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                )
                
                if st.button("Save Changes to Plan"):
                    # Convert edited DataFrame back to plan structure
                    updated_plan = {"weeks": []}
                    for i, row in edited_df.iterrows():
                        week_number = int(row["Week"].split(" ")[1])
                        
                        # Parse distance and description from each day
                        days = {}
                        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                            parts = row[day].split("km:", 1)
                            if len(parts) == 2:
                                distance = float(parts[0].strip().replace("km", ""))
                                description = parts[1].strip()
                                days[day.lower()] = {"distance": distance, "description": description}
                            else:
                                days[day.lower()] = {"distance": 0, "description": "Rest"}
                        
                        # Calculate total distance
                        total_distance = sum(day_data["distance"] for day_data in days.values())
                        
                        week_data = {
                            "week_number": week_number,
                            "start_date": row["Start Date"],
                            **days,
                            "total_distance": total_distance,
                            "comment": row["Comment"]
                        }
                        updated_plan["weeks"].append(week_data)
                    
                    # Save the updated plan
                    save_training_plan(race_id, updated_plan)
                    st.success("Training plan updated!")
                
                # Plot planned vs actual weekly distance
                st.subheader("Weekly Distance Comparison")
                
                # Create weekly planned distance data
                weekly_data = []
                for week in existing_plan["weeks"]:
                    # Extract week start date and calculate end date
                    try:
                        start_date = datetime.fromisoformat(week.get("start_date")).date()
                        end_date = start_date + timedelta(days=6)
                        
                        # Calculate actual distance from runs in this period
                        actual_distance = df[(df["Date"].dt.date >= start_date) & 
                                          (df["Date"].dt.date <= end_date)]["Distance (km)"].sum()
                        
                        weekly_data.append({
                            "Week": f"Week {week['week_number']}",
                            "Planned Distance": week.get("total_distance", 0),
                            "Actual Distance": actual_distance
                        })
                    except:
                        # Fallback if date parsing fails
                        weekly_data.append({
                            "Week": f"Week {week['week_number']}",
                            "Planned Distance": week.get("total_distance", 0),
                            "Actual Distance": 0
                        })
                
                weekly_df = pd.DataFrame(weekly_data)
                weekly_df = weekly_df.melt(id_vars=["Week"], 
                                          value_vars=["Planned Distance", "Actual Distance"],
                                          var_name="Type", value_name="Distance")
                
                # Create the chart
                chart = alt.Chart(weekly_df).mark_area(line=True, point=True, interpolate='monotone', opacity=0.5).encode(
                    x=alt.X("Week:N", sort=None),
                    y=alt.Y("Distance:Q", title="Distance (km)", stack=None),
                    color=alt.Color("Type:N", scale=alt.Scale(
                        domain=["Planned Distance", "Actual Distance"],
                        range=["#1EBEFF", "#FF9633"]
                    ))
                ).properties(height=300)
                
                st.altair_chart(chart, use_container_width=True)
                
                # Option to delete plan
                if st.button("🗑️ Delete Training Plan"):
                    plans = load_training_plans()
                    if race_id in plans:
                        del plans[race_id]
                        with open("data/races/training_plans.json", "w") as f:
                            json.dump(plans, f)
                        st.success("Training plan deleted.")
                        if "selected_race" in st.session_state:
                            del st.session_state["selected_race"]
                        st.rerun()
            else:
                st.info("No training plan exists yet. Use the AI Coach to create one, or add one manually.")
                
                # Option to add plan manually
                with st.expander("Create Manual Training Plan"):
                    # Calculate number of weeks until race
                    weeks_to_race = max(1, (race_date - today).days // 7)
                    num_weeks = st.slider("Number of weeks in plan", 4, 24, min(16, weeks_to_race))
                    
                    # Create a template for the manual plan
                    manual_plan = {"weeks": []}
                    for i in range(num_weeks):
                        week_start = today + timedelta(weeks=i)
                        manual_plan["weeks"].append({
                            "week_number": i + 1,
                            "start_date": week_start.isoformat(),
                            "monday": {"distance": 0, "description": "Rest"},
                            "tuesday": {"distance": 0, "description": "Rest"},
                            "wednesday": {"distance": 0, "description": "Rest"},
                            "thursday": {"distance": 0, "description": "Rest"},
                            "friday": {"distance": 0, "description": "Rest"},
                            "saturday": {"distance": 0, "description": "Rest"},
                            "sunday": {"distance": 0, "description": "Rest"},
                            "total_distance": 0,
                            "comment": f"Week {i + 1}"
                        })
                    
                    if st.button("Create Empty Plan Template"):
                        save_training_plan(race_id, manual_plan)
                        st.success("Empty training plan template created!")
                        st.rerun()
    else:
        st.info("No races added yet. Add your first race using the form above.")