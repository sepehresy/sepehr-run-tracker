import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from openai import OpenAI
import os

client = OpenAI(api_key=st.secrets("OPENAI_API_KEY"))

def render_activities(df):
    st.title("📋 Activities")

    st.dataframe(df.sort_values("Date", ascending=False))

    if "Lap Details" in df.columns:
        st.subheader("Splits (per run)")

        activity_options = df.sort_values("Date", ascending=False).apply(
            lambda row: f"{row['Date'].date()} - {row['Name']}", axis=1
        )
        selected_activity = st.selectbox("Select an activity to view splits:", activity_options)

        selected_row = df[df.apply(
            lambda row: f"{row['Date'].date()} - {row['Name']}" == selected_activity, axis=1
        )].iloc[0]

        def format_pace(p):
            try:
                minutes = int(p)
                seconds = int(round((p - minutes) * 60))
                return f"{minutes}:{seconds:02d}"
            except:
                return "-"

        # Show summary metrics above plot
        metrics = [
            ("Total Distance (km)", selected_row.get("Distance (km)", "-")),
            ("Pace (min/km)", format_pace(float(selected_row.get("Pace (min/km)", 0))) if selected_row.get("Pace (min/km)") != "-" else "-"),
            ("Moving Time", selected_row.get("Moving Time", "-")),
            ("Cadence", selected_row.get("Cadence", "-")),
            ("Power (W)", selected_row.get("Power (W)", "-")),
            ("Avg HR", selected_row.get("Avg HR", "-")),
            ("Max HR", selected_row.get("Max HR", "-")),
            ("Elevation Gain", selected_row.get("Elevation Gain", "-")),
            ("Calories", selected_row.get("Calories", "-")),
        ]
        cols = st.columns(len(metrics))
        for i, (label, value) in enumerate(metrics):
            cols[i].metric(label, value)

        if pd.notna(selected_row["Lap Details"]):
            try:
                laps_raw = re.findall(r"Lap (\d+):\s*([^|]+)", selected_row["Lap Details"].replace("\\n", " "))
                lap_data = []
                for lap_number, details in laps_raw:
                    parts = [x.strip() for x in details.split(",")]
                    lap_info = {"Lap": int(lap_number)}
                    for p in parts:
                        if p.endswith("km"):
                            lap_info["Distance"] = float(p.replace("km", ""))
                        elif re.match(r"\d+:\d+", p):
                            lap_info["Time"] = p
                        elif p.startswith("pace"):
                            lap_info["Pace"] = float(p.replace("pace", "").strip())
                        elif p.startswith("HR"):
                            lap_info["HR"] = int(float(p.replace("HR", "").strip()))
                        elif p.startswith("Cad"):
                            lap_info["Cad"] = int(float(p.replace("Cad", "").strip()))
                        elif p.startswith("ElevGain"):
                            lap_info["ElevGain"] = float(p.replace("ElevGain", "").strip())
                    lap_data.append(lap_info)

                lap_df = pd.DataFrame(lap_data)
                if not lap_df.empty:
                    fig, ax = plt.subplots(figsize=(10, 0.4 * len(lap_df)))
                    bars = ax.barh(lap_df.index, lap_df["Pace"], color="#1EBEFF")

                    avg_pace = lap_df["Pace"].mean()
                    ax.axvline(x=avg_pace, color="red", linestyle="--", linewidth=1, label=f"Avg Pace: {format_pace(avg_pace)}")
                    ax.legend(loc="lower right")

                    ax.text(-5.8, -1, "KM", fontweight='bold')
                    ax.text(-4.8, -1, "Time", fontweight='bold')
                    ax.text(-3.8, -1, "Elev", fontweight='bold')
                    ax.text(-2.8, -1, "HR", fontweight='bold')
                    ax.text(-1.8, -1, "Pace", fontweight='bold')

                    for i, row in lap_df.iterrows():
                        ax.text(-5.8, i, f"{row['Distance']:.2f}", va='center', ha='left', fontweight='bold')
                        ax.text(-4.8, i, f"{row['Time']}", va='center', ha='left')
                        ax.text(-3.8, i, f"{int(row['ElevGain'])}", va='center', ha='left')
                        ax.text(-2.8, i, f"{row['HR']}", va='center', ha='left')
                        ax.text(-1.8, i, format_pace(row['Pace']), va='center', ha='left')

                    ax.set_yticks([])
                    ax.set_xlabel("Pace (min/km)")
                    ax.invert_yaxis()
                    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
                    ax.set_xlim(0, max(lap_df["Pace"]) + 2)
                    st.pyplot(fig)

                    st.subheader("🧠 AI Analysis of This Run")
                    prompt = (
                        "Analyze this running activity based on the following per-lap data.\n"
                        "Comment on pacing, heart rate, cadence, and elevation gain.\n"
                        f"\nLap Data:\n{lap_df.to_csv(index=False)}"
                    )
                    with st.spinner("Thinking..."):
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are a professional running coach."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        st.success("Here's your AI feedback:")
                        st.write(response.choices[0].message.content)

            except Exception as e:
                st.warning(f"Could not parse lap details: {e}")

        st.markdown("---")
