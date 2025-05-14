import streamlit as st

def render_ai_analysis(df, today):
    st.markdown("# 🧠 AI Performance Review")

    if df.empty or "Date" not in df.columns:
        st.warning("No activity data found. Please upload or connect your activity source.")
        return

    run_options = df.sort_values(by='Date', ascending=False)["Date"].dt.strftime("%b %d, %Y").tolist()
    selected_date = st.selectbox("Choose a run date", run_options)

    st.subheader(f"AI Coach Feedback for {selected_date}")
    st.write("""
    This is a Pro Feature! Contact the developer to unlock this feature.
    """)
