# ai_prompt.py
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

def generate_ai_prompt(selected_race, today_str, race_date, plan_df, chart_df, lap_text, previous_notes):
    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">🤖</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">AI Prompt</span>', unsafe_allow_html=True)
    
    progress_csv = chart_df.to_csv(index=False)
    plan_csv = plan_df.to_csv(index=False)

    # Find current week and day for more context
    today = pd.to_datetime(today_str).date()
    current_week_num = None
    current_week_idx = None
    for i, row in plan_df.iterrows():
        start = pd.to_datetime(row["Start Date"]).date()
        end = start + pd.Timedelta(days=6)
        if start <= today <= end:
            current_week_num = row["Week"]
            current_week_idx = i
            break

    # Find the current week's plan and what is left (from today onward)
    plan_left_str = ""
    if current_week_idx is not None:
        week_row = plan_df.iloc[current_week_idx]
        week_start = pd.to_datetime(week_row["Start Date"]).date()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_idx = (today - week_start).days
        plan_left = []
        for i, day in enumerate(days):
            if i >= today_idx:
                day_plan = week_row.get(day, "")
                plan_left.append(f"{day}: {day_plan}")
        plan_left_str = "\n".join(plan_left)

    # Use get_race_and_profile_info for consistent info formatting
    race_info_block, num_weeks = get_race_and_profile_info(selected_race)

    # Build prompt using f-strings for all interpolations
    prompt = (
        "You are an expert running coach and your job is to analyze the athlete's training and provide actionable, concise, and data-driven feedback.\n\n"
        f"{race_info_block}"
        f"📅 **Today:** {today_str} ({today.strftime('%A')})\n"
        f"{'📆 **Current Training Week:** ' + str(current_week_num) if current_week_num else ''}\n"
        f"{'**Workouts remaining this week (including today):***  ' + plan_left_str if plan_left_str else ''}\n"
        "---\n\n"
        "### 📅 Full Training Plan (for reference)\n"
        "```\n"
        f"{progress_csv}\n"
        "```\n\n"
        "---\n\n"
        "### 🏃 Last 20 Runs (Lap-by-Lap Details)\n"
        f"{plan_csv}\n\n"
        "---\n\n"
        "### 🧠 Previous AI Feedback\n"
        f"{previous_notes if previous_notes else '[No prior feedback yet]'}\n\n"
        "---\n\n"
        "## Please analyze and provide:\n\n"
        "1. **📈 Race Readiness:** 1-2 line summary of current readiness for the race.\n"
        "2. **✅ Strengths:** 2–3 concise points on what is working well (with metrics if possible).\n"
        "3. **⚠️ Risks / Gaps:** What is missing, at risk, or needs urgent adjustment? (focus on current and next week)\n"
        "4. **📉 Trends:** Notable trends in pacing, heart rate, fatigue, or compliance.\n"
        "5. **🧠 This Week’s Recommendations:** (specify week number)\n"
        "   - List remaining or suggested runs for this week (distance, type, and day if possible)\n"
        "   - Add rest/recovery cues and HR/pace targets if relevant\n"
        "   - If in the middle of a week, highlight what is left to do\n"
        "   - **Do NOT say workouts are missing for this week unless today is after the scheduled day.**\n"
        "6. **🛠️ Tweaks/Warnings:** Any minor tweaks, warnings, or gear/nutrition reminders for race success.\n"
        "7. **🔄 Plan Adjustments:** Should the user change anything for this week or next week? Be specific if so.\n\n"
        "**Instructions:**\n"
        "- Be brief (max 10 bullet points), clear, and actionable.\n"
        "- Use markdown formatting and emojis for clarity.\n"
        "- If the user is in the middle of a week, reference only what is left in the plan for this week.\n"
        "- If the user missed key workouts (i.e., days before today), suggest how to adapt.\n"
        "- If the race is very close, focus on taper, recovery, and readiness.\n"
        "- **Do NOT say workouts are missing for this week unless today is after the scheduled day.**\n"
    )
    print (prompt)
    return prompt

def get_race_and_profile_info(race_info):
    # Calculate number of weeks between training start date and race date
    try:
        start_date_str = race_info.get('training_start_date')
        race_date_str = race_info.get('date','')
        if not start_date_str or not race_date_str:
            raise ValueError('Missing training_start_date or race_date')
        start_date = pd.to_datetime(start_date_str, errors='coerce')
        race_date = pd.to_datetime(race_date_str, errors='coerce')
        if pd.isnull(start_date) or pd.isnull(race_date):
            raise ValueError('Invalid date format for training_start_date or race_date')
        # Align both to Monday
        start_monday = start_date - pd.Timedelta(days=start_date.weekday())
        race_monday = race_date - pd.Timedelta(days=race_date.weekday())
        num_weeks = ((race_monday - start_monday).days // 7) + 1
    except Exception as e:
        print(f"[AI PLAN PROMPT] Failed to calculate num_weeks: {e}")
        num_weeks = None
    # Dynamically format all runner profile fields
    runner_profile = st.session_state.get('user_info', {}).get('runner_profile', {})
    def _is_meaningful(val):
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, (list, dict)):
            return bool(val)
        return str(val).strip() not in ('', '0', '0.0', 'None', 'N/A')
    if isinstance(runner_profile, dict) and any(_is_meaningful(v) for v in runner_profile.values()):
        runner_profile_str = '\n'.join([
            f"    {k.replace('_', ' ').capitalize()}: {v}" for k, v in runner_profile.items() if _is_meaningful(v)
        ])
    else:
        runner_profile_str = '    [No runner profile data provided]'
    info = (
        f"🏁 Race Information\n"
        f"Race Name: {race_info.get('name','')}\n"
        f"Race Date: {race_info.get('date','')}\n"
        f"Training Start Date: {race_info.get('training_start_date','')}\n"
        f"Distance: {race_info.get('distance','')} km\n"
        f"Race Type: {race_info.get('type','')} (e.g., road, trail, ultra)\n"
        f"Elevation Gain: {race_info.get('elevation_gain','')} m\n"
        f"Goal Time: {race_info.get('goal_time','')}\n"
        f"Race Notes: {race_info.get('notes','')}\n"
        f"Number of weeks from training start to race week: {num_weeks if num_weeks is not None else '[calculate it]'}\n\n"
        f"🧍 Runner Profile\n{runner_profile_str}\n"
    )
    return info, num_weeks

def generate_ai_plan_prompt(race_info, ai_notes=None):
    race_info_block, num_weeks = get_race_and_profile_info(race_info)

    prompt = f"""
    📋 ROLE:
    You are a certified world-class expert running coach. Your primary task is to generate a complete, structured, realistic, and personalized weekly training plan for a runner targeting a specific race, based on the information provided below. The plan must strictly adhere to the CSV output format specified.
    
    {race_info_block}

    ✍️ Additional Notes (from user for AI Coach):
    {ai_notes or '[None provided]'}

    ✅ INSTRUCTIONS FOR TRAINING PLAN GENERATION:

    1.  **Plan Duration & Calculation**:
        * Create a comprehensive, week-by-week training plan.
        * The plan must start from the `Training Start Date` and end on the week of the `Race Date`.
        * If `Number of weeks from training start to race week` is '[AI to calculate]' or not provided, you MUST calculate it as the total number of full weeks from the `Training Start Date` up to and including the `Race Date`'s week. Ensure this calculation correctly determines the number of rows for the CSV.

    2.  **Training Principles**:
        * **Progressive Overload**: Gradually increase weekly volume (km) and/or intensity. Avoid increasing total weekly mileage by more than 10-15% per week (excluding post-down week adjustments).
        * **Rest and Recovery**: Incorporate adequate rest. If `Preferred Rest Days` are specified, try to use them. Otherwise, intelligently place rest days.
        * **Down Weeks**: Include a "down week" (reduced volume) approximately every 3-4 weeks (e.g., after 3 weeks of building, the 4th week is a down week). During a down week, reduce total weekly kilometrage by 25-35% compared to the previous peak week in that cycle.
        * **Tapering**: Implement a taper phase in the final 2-3 weeks before race day. The taper length depends on the race `Distance` (e.g., 1 week for 5K/10K, 2-3 weeks for half/full marathon, 3+ for ultras). During the taper, reduce volume significantly but maintain some intensity with shorter, faster workouts.
        * **Variety**: Ensure the plan includes a mix of workouts appropriate for the runner's level and goal:
            * Easy Runs (Zone 2, conversational pace)
            * Long Runs (essential for endurance, progressively longer)
            * Intervals (e.g., VO2 max: 400m-1km repeats; Lactate Threshold: longer repeats like 1km-2km or cruise intervals)
            * Tempo Runs (sustained effort at lactate threshold pace or comfortably hard)
            * Hill Repeats (if `Elevation Gain` is significant or for strength)
            * Recovery Runs (very easy, short, day after hard workout)
            * Strides (short bursts of speed, e.g., 4-6 x 100m after easy runs)
            * Rest Days ( crucial for adaptation and injury prevention)
            * Cross-Training: `"0.0 km: Cross-Train – 45 mins cycling, Zone 2 effort (optional or if specified by user)"`
        * **Race Specificity**:
            * If `Elevation Gain` is significant (e.g., >20m/km on average, or substantial total gain for the distance), incorporate hill training (repeats, hilly routes for long runs).
            * For `Race Type` 'trail' or 'ultra', include considerations like: terrain-specific training advice (if possible), practicing with gear/nutrition on long runs, and potentially back-to-back long runs for ultras if appropriate for the runner's experience.

    3.  **Workout Details**:
        * The `X km` in daily entries must represent the TOTAL distance for that session (e.g., including warm-up, main set, and cool-down).
        * The description must clearly state the workout structure. Examples:
            * Easy Run: `"10.0 km: Easy run – Zone 2 effort, conversational pace, maintain nasal breathing if possible"`
            * Intervals: `"12.0 km: Intervals – WU: 2km easy; Main: 5 x 1km @ 5:00/km pace (or 10K pace) with 400m jog recovery; CD: 2km easy"`
            * Tempo: `"10.0 km: Tempo Run – WU: 2km easy; Main: 6km @ 6:00/km pace (or half marathon pace); CD: 2km easy"`
            * Long Run: `"25.0 km: Long Run – Easy, conversational pace. Practice race day nutrition/hydration strategy."`
            * Rest: `"0.0 km: Rest – Full rest day. Optional: light stretching or mobility work."`
        * Pacing: Define paces based on `Goal Time`, `Experience Level`, `Most Recent Race`, or provide them in terms of Perceived Effort (RPE 1-10), Heart Rate Zones (if user mentions them), or relative to common race paces (e.g., 'Marathon Pace', '10K Pace'). Be realistic with paces.

    4.  **Runner Profile Adaptation**:
        * Adjust the plan based on `Experience Level`, `Average Weekly KM`, and `Longest Run Recently`. Start the plan at a volume and intensity appropriate for the runner's current fitness.
        * Distribute workouts across the `Available Training Days per Week`. If the user specifies "5 days", you decide the 2 rest days unless `Preferred Rest Days` are given.
        * Address `Known Limitations`: If injuries are mentioned, be conservative. Suggest cross-training or reduced impact alternatives if appropriate. Explicitly mention in the 'Comment' for that week if a modification is due to a limitation.
        * Incorporate `Preferred Workout Types` if they align with sound training principles for the target race.

    5.  **Race Week**:
        * The final row of the CSV is Race Week.
        * On Race Day (typically Saturday or Sunday, confirm with `Race Date` if possible, otherwise assume weekend):
            * Format: `"{race_info.get('distance','')} km: Race Day – Execute race strategy. Good luck!"`
        * Workouts in race week should be very light (e.g., short shakeout runs, rest).

    ✅ CSV FORMAT RULES (MANDATORY):
    - **Output a valid CSV table ONLY.** Absolutely NO code blocks, no markdown formatting (like ` ```csv ... ``` `), no introductory or concluding text, no explanations, or any other text outside the CSV data itself.
    - Each row in the CSV must represent one full week of training.
    - The first line of the output MUST be the header row.
    - The header row must be EXACTLY: `"Week","Start Date","Status","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday","Comment"`
    - Each subsequent row must contain **exactly 11 fields**, corresponding to the header.
    - Use a **comma (`,`)** as the sole column delimiter.
    - **Enclose EVERY field in double quotes (`"`)**, including numbers, dates, and simple words.
    - **Do not include any blank lines** in the output, not even at the end.
    - **No line breaks or newline characters (`\\\\n`)** are allowed inside a quoted field. Each CSV record must be a single line.
    - If any field's content naturally contains a comma, it must still be enclosed in double quotes as per the rule above (e.g., `"Build: Week 1, focusing on mileage"`).
    - The "Start Date" for each week must be a Monday. Format dates as "YYYY-MM-DD".

    ✅ STATUS & COMMENT COLUMN RULES:
    - **Status Column**:
        * Use `"🏁 Race Week"` for the week of the race.
        * Use `"✅ Completed"` if the `End Date` of the week is in the past relative to the current date 
        * Use `"💤 Future"` if the `Start Date` of the week is in the future or is the current week.
    - **Comment Column**:
        * Must start with the training phase name (e.g., "Base:", "Build 1:", "Build 2:", "Peak:", "Recovery:", "Taper:").
        * Follow with a brief description of the week's primary focus or purpose (e.g., "Adapting to volume", "Introducing speed work", "Peak mileage week", "Reducing volume, maintaining intensity").

    ✅ EXAMPLE OUTPUT SNIPPET (Illustrative - follow all rules for full output):
    "Week","Start Date","Status","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday","Comment"
    "Week 1","2025-07-07","💤 Future","6.0 km: Easy aerobic run – Zone 2, conversational","0.0 km: Rest","8.0 km: Easy run + 4x100m strides – WU: 1km easy; Main: 6km easy; Strides: 4x100m fast w/ recovery; CD: 1km easy","0.0 km: Rest","6.0 km: Easy aerobic run – Zone 2","14.0 km: Long Run – Easy, conversational pace","0.0 km: Rest","Base: Initial adaptation and building aerobic base"
    "Week 2","2025-07-14","💤 Future","6.0 km: Easy recovery run – Zone 1-2","0.0 km: Rest","10.0 km: Intervals – WU: 2km easy; Main: 4x1km @5:00/km w/ 90s jog recovery; CD: 2km easy","0.0 km: Rest","6.0 km: Easy aerobic run – Zone 2","16.0 km: Long Run – Steady pace, building endurance","0.0 km: Rest","Base: Introducing speed work and increasing long run"

    ⛔ STRICT FINAL INSTRUCTIONS:
    - **CSV ONLY**: You MUST return only the CSV formatted text as described. No other text, explanation, or formatting.
    - **ROW COUNT**: Output exactly the {num_weeks} weeks for the plan (plus the header). No more, no fewer.
    - **HEADER MATCH**: The header must match the specified format character-for-character.
    - **ADHERENCE TO FORMAT**: If you are absolutely unable to generate a plan that adheres to ALL the above formatting and content rules (e.g., due to contradictory or insufficient input), output a single CSV row with an error message in the "Comment" field: `"Week","Start Date","Status","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday","Comment"`
    `"Error","N/A","N/A","N/A","N/A","N/A","N/A","N/A","N/A","N/A","Error: Could not generate plan due to [brief reason, e.g., invalid dates, insufficient info]."`
    This error CSV is a last resort; strive to generate the full plan. 

    """

    print(prompt)
    return prompt
