import streamlit as st
import pandas as pd
import re
import altair as alt


def render_activities(df):
    st.title("📋 Activities")

    st.dataframe(df.sort_values("Date", ascending=False))

    if "Lap Details" in df.columns:
        st.subheader("Splits (per run)")

        for _, row in df.sort_values("Date", ascending=False).iterrows():
            if pd.notna(row["Lap Details"]):
                st.markdown(f"**{row['Date'].date()} - {row['Name']}**")
                try:
                    # Extract each Lap's data using a robust pattern
                    laps_raw = re.findall(
                        r"Lap (\d+):\s*([^|]+)", row["Lap Details"]
                    )
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
                                lap_info["HR"] = float(p.replace("HR", "").strip())
                            elif p.startswith("Cad"):
                                lap_info["Cad"] = float(p.replace("Cad", "").strip())
                            elif p.startswith("ElevGain"):
                                lap_info["ElevGain"] = float(p.replace("ElevGain", "").strip())
                        lap_data.append(lap_info)

                    lap_df = pd.DataFrame(lap_data)
                    if not lap_df.empty:
                        lap_df = lap_df.set_index("Lap")
                        st.dataframe(lap_df)

                        # Plot bar chart like Strava
                        base = alt.Chart(lap_df.reset_index()).encode(x=alt.X("Lap:O"))

                        pace_bar = base.mark_bar(color="#00BFFF").encode(
                            y=alt.Y("Pace:Q", title="Pace (min/km)")
                        )

                        annotation_text = base.mark_text(
                            align="left",
                            dx=2,
                            dy=-5,
                            fontSize=11,
                            color="white"
                        ).encode(
                            y="Pace:Q",
                            text=alt.Text("Lap:O",
                                format="Lap {Lap}: HR={HR}, Cad={Cad}, Elev={ElevGain}")
                        )

                        st.altair_chart(pace_bar + annotation_text, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not parse lap details: {e}")
                st.markdown("---")
