import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE

def render_ai_analysis(df, today):
    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">🧠</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">AI Performance Review</span>', unsafe_allow_html=True)

    if df.empty or "Date" not in df.columns:
        st.warning("No activity data found. Please upload or connect your activity source.")
        return

    run_options = df.sort_values(by='Date', ascending=False)["Date"].dt.strftime("%b %d, %Y").tolist()
    selected_date = st.selectbox("Choose a run date", run_options)

    st.subheader(f"AI Coach Feedback for {selected_date}")
    st.write("""
    This is a Pro Feature! Contact the developer to unlock this feature.
    """)

    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)
