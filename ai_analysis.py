
import streamlit as st

def render_ai_analysis(df, today):
    st.markdown("# 🧠 AI Performance Review")

    st.info("Select a run to analyze using the dropdown below.")
    run_options = df.sort_values(by='Date', ascending=False)["Date"].dt.strftime("%b %d, %Y").tolist()
    selected_date = st.selectbox("Choose a run date", run_options)

    # Placeholder AI coach feedback for selected run
    st.subheader(f"AI Coach Feedback for {selected_date}")
    st.write("""
    Based on your selected activity, you demonstrated consistent pacing with notable heart rate control in the early kilometers. However, there's a gradual decline in pace and rise in HR after the halfway point, suggesting fatigue.

    **Suggestions:**
    - Focus on mid-run fueling strategies to avoid the dip in performance.
    - Incorporate tempo efforts to maintain form during late stages.
    - Consider reviewing cadence stability during climb segments.

    Overall, you're progressing well. Keep up the consistency and tune recovery before your next intensity block!
    """)
