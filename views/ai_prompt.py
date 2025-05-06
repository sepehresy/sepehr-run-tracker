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
