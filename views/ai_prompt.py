# ai_prompt.py
import pandas as pd

def generate_ai_prompt(selected_race, today_str, race_date, plan_df, chart_df, lap_text, previous_notes):
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

    # Build prompt using string concatenation to avoid f-string backslash issues
    prompt = (
        "You are an expert running coach and your job is to analyze the athlete's training and provide actionable, concise, and data-driven feedback.\n\n"
        "🏁 **Race Goal:** {} km {} on {}\n"
        "📅 **Today:** {} ({})\n"
        "{}\n"
        "{}\n"
        "---\n\n"
        "### 📅 Full Training Plan (for reference)\n"
        "```\n"
        "{}\n"
        "```\n\n"
        "---\n\n"
        "### 🏃 Last 20 Runs (Lap-by-Lap Details)\n"
        "{}\n\n"
        "---\n\n"
        "### 🧠 Previous AI Feedback\n"
        "{}\n\n"
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
    ).format(
        selected_race['distance'],
        selected_race['type'],
        race_date,
        today_str,
        today.strftime('%A'),
        f"📆 **Current Training Week:** {current_week_num}" if current_week_num else "",
        f"\n**Workouts remaining this week (including today):**\n{plan_left_str}" if plan_left_str else "",
        progress_csv,
        plan_csv,
        lap_text,
        previous_notes if previous_notes else '[No prior feedback yet]'
    )
    # print (prompt)
    return prompt

def generate_ai_plan_prompt(race_info, ai_notes=None):
    """
    Generate a comprehensive prompt for the AI to create a training plan table for a race.
    race_info: dict with keys name, date, distance, type, elevation_gain, goal_time, notes, runner_profile
    ai_notes: str, extra user notes for the AI
    """
    # Calculate number of weeks between training start date and race date
    from datetime import datetime, timedelta
    try:
        start_date_str = race_info.get('runner_profile',{}).get('training_start_date','')
        race_date_str = race_info.get('date','')
        start_date = pd.to_datetime(start_date_str)
        race_date = pd.to_datetime(race_date_str)
        # Align both to Monday
        start_monday = start_date - pd.Timedelta(days=start_date.weekday())
        race_monday = race_date - pd.Timedelta(days=race_date.weekday())
        num_weeks = ((race_monday - start_monday).days // 7) + 1
    except Exception:
        num_weeks = None

    prompt = f"""
📋 ROLE:
You are a world-class expert running coach. Your task is to generate a complete, structured, and realistic weekly training plan for a runner targeting a race.

🏁 Race Information
Race Name: {race_info.get('name','')}
Race Date: {race_info.get('date','')}
Training Start Date: {race_info.get('runner_profile',{}).get('training_start_date','')}
Distance: {race_info.get('distance','')} km
Race Type: {race_info.get('type','')} (e.g., road, trail, ultra)
Elevation Gain: {race_info.get('elevation_gain','')} m
Goal Time: {race_info.get('goal_time','')}
Race Notes: {race_info.get('notes','')}
Number of weeks from training start to race week: {num_weeks if num_weeks is not None else '[calculate it]'}

🧍 Runner Profile
Experience Level: {race_info.get('runner_profile',{}).get('experience','')}
Average Weekly KM: {race_info.get('runner_profile',{}).get('weekly_km','')}
Most Recent Race: {race_info.get('runner_profile',{}).get('recent_race','')}
Available Training Days per Week: {race_info.get('runner_profile',{}).get('available_days','')}
Known Limitations (e.g., injuries): {race_info.get('runner_profile',{}).get('limitations','')}
Preferred Workout Types: {race_info.get('runner_profile',{}).get('preferred_workout_types','')}
Other Personal Notes: {race_info.get('runner_profile',{}).get('other_notes','')}

✍️ Additional Notes (from user):
{ai_notes or '[None]'}

✅ INSTRUCTIONS:
- Create a progressive, week-by-week training plan starting from the Training Start Date and ending the week of the Race Date.
- Fix: Add a down week every 3–4 weeks to reduce injury risk. drop the total volum minumum by 30–35%. 

Each row represents one full week of training. You must:
- Output exactly {num_weeks if num_weeks is not None else '[calculate it]'} rows.
- Always begin each week on a Monday.
- Include a taper phase and one final row containing Race Day.
- For Race Week,  mark the correct day as `X km: Race day – Execute race strategy`.
- If any field contains a comma, enclose that field in double quotes to ensure proper CSV parsing

Each day's value must follow this format:
X km: Workout type – Full detailed description include warming up, cooling down, and any specific instructions.
Examples:
- `10.0 km: Easy run – Zone 2 effort, nasal breathing`
- `0.0 km: Rest – Full rest day, mobility optional`
- `6.0 km: Intervals – 4x1km @ 10K pace with 90s jog`

✅ FORMAT:
Return the plan as **raw CSV only**. Do **not** include:
- Any markdown
- Code blocks
- Text explanations
- Headers or footers

Only return the table in this column order:

```
Week,Start Date,Status,Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday,Comment
```

Use:
- `💤 Future` for all weeks before race week
- `🏁 Race Week` as the final week's status

📌 Example line:
```
Week 1,2025-05-12,💤 Future,5.0 km: Easy run – Light form,0.0 km: Rest – Recovery,6.0 km: Intervals – 4x1km @ threshold,5.0 km: Easy – Nasal breathing,0.0 km: Rest – Optional yoga,14.0 km: Long run – Easy trail effort,3.0 km: Recovery – Gentle jog,Base phase: Establish consistency
```

⛔ STRICT RULE:
Return **CSV only**. No markdown formatting, no bullet points, no surrounding text.
"""
    print (prompt)
    return prompt
