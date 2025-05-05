
import streamlit as st
import pandas as pd
import altair as alt

def render_summary(df, today):
    st.markdown("# 🏃‍♂️ Summary Statistics (v1.0.0)")

    st.radio("Select View", ["Weekly", "4 Weeks", "3 Months", "6 Months", "1 Year", "All (monthly)", "All Yearly"], horizontal=True, key="summary_view")
    st.selectbox("Chart Style", ["Bar", "Area", "Line", "Area + Dots", "Bar + Line"], key="summary_chart_style")

    # Placeholder chart to keep layout (real logic omitted)
    st.altair_chart(
        alt.Chart(df).mark_bar().encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Distance (km):Q", title="Distance (km)")
        ).properties(height=400),
        use_container_width=True
    )
