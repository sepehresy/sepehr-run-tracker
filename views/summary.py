import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def render_summary(df, today):
    st.title("🏃 Summary Statistics (v1.0.0)")

    view_option = st.radio(
        "Select View",
        ["Weekly", "4 Weeks", "3 Months", "6 Months", "1 Year", "All (monthly)", "All Yearly"],
        horizontal=True
    )

    chart_style = st.selectbox(
        "Chart Style",
        ["Bar", "Bar + Line", "Line + Dots", "Area + Dots"],
        index=0
    )

    if view_option == "Weekly":
        start = today - timedelta(days=today.weekday())
        days = [start + timedelta(days=i) for i in range(7)]
        df["Day"] = df["Date"].dt.strftime("%a")
        daily_km = df[df["Date"].between(start, start + timedelta(days=6))].groupby("Day")["Distance (km)"].sum()
        df_agg = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]})
        df_agg["Distance (km)"] = df_agg["Day"].map(daily_km).fillna(0)
        x_field = "Day:N"
        x_title = "Day"
        bar_width = 60
        x_axis = alt.Axis(title=x_title)

    elif view_option == "4 Weeks":
        current_week_start = today - timedelta(days=today.weekday())
        start = current_week_start - timedelta(weeks=4)
        weeks = [start + timedelta(weeks=i) for i in range(5)]
        df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit='d')
        df["Week"] = df["Week"].dt.normalize()
        weekly_km = df.groupby("Week")["Distance (km)"].sum().reset_index()
        df_agg = pd.DataFrame({"Week": weeks}).merge(weekly_km, on="Week", how="left").fillna(0)
        df_agg["WeekStart"] = df_agg["Week"]
        x_field = "WeekStart:T"
        x_title = "Week"
        bar_width = 40
        x_axis = alt.Axis(title=x_title, format="%b-%d")

    elif view_option in ["3 Months", "6 Months"]:
        months_back = 3 if view_option == "3 Months" else 6
        start = today - relativedelta(months=months_back)
        df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit='d')
        df["Week"] = df["Week"].dt.normalize()
        weekly_km = df[df["Week"] >= start].groupby("Week")["Distance (km)"].sum().reset_index()
        df_agg = weekly_km.copy()
        df_agg["WeekStart"] = df_agg["Week"]
        df_agg = df_agg.sort_values("WeekStart")
        x_field = "WeekStart:T"
        x_title = "Week"
        bar_width = 20
        x_axis = alt.Axis(title=x_title, format="%b-%d", labelAngle=-45, labelFontSize=10)

    elif view_option == "1 Year":
        months = [(today.replace(day=1) - relativedelta(months=12 - i)) for i in range(13)]
        df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
        monthly_km = df.groupby("Month")["Distance (km)"].sum().reset_index()
        df_months = pd.DataFrame({"Month": months}).merge(monthly_km, on="Month", how="left").fillna(0)
        df_months["Month Label"] = df_months["Month"].dt.strftime("%b %Y")
        df_agg = df_months
        x_field = "Month Label:N"
        x_title = "Month"
        bar_width = 20
        x_axis = alt.Axis(title=x_title, labelAngle=-45)

    elif view_option == "All (monthly)":
        df["MonthStart"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
        monthly_km = df.groupby("MonthStart")["Distance (km)"].sum().reset_index()
        df_agg = monthly_km
        x_field = "MonthStart:T"
        x_title = "Month"
        bar_width = 10
        x_axis = alt.Axis(title=x_title, labelAngle=-45, labelFontSize=10)
        year_lines = alt.Chart(df_agg[df_agg["MonthStart"].dt.month == 1]).mark_rule(
            strokeDash=[4, 4], color="gray"
        ).encode(x="MonthStart:T")

    elif view_option == "All Yearly":
        df["YearStart"] = df["Date"].dt.to_period("Y").apply(lambda r: r.start_time)
        yearly_km = df.groupby("YearStart")["Distance (km)"].sum().reset_index()
        df_agg = yearly_km
        x_field = "YearStart:T"
        x_title = "Year"
        bar_width = 40
        x_axis = alt.Axis(title=x_title, labelAngle=0, labelFontSize=12)

    sort_field = x_field.split(":")[0] if x_field.endswith(":N") else None

    base = alt.Chart(df_agg).encode(
        x=alt.X(x_field, title=x_title, axis=x_axis, sort=df_agg[sort_field].tolist() if sort_field else None),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=[df_agg.columns[0], "Distance (km)"]
    )

    if chart_style == "Bar":
        chart = base.mark_bar(size=bar_width)
    elif chart_style == "Bar + Line":
        chart = base.mark_bar(size=bar_width) + base.mark_line(strokeWidth=2, color="orange")
    elif chart_style == "Line + Dots":
        chart = base.mark_line(strokeWidth=2) + base.mark_point(filled=True, size=70)
    elif chart_style == "Area + Dots":
        chart = base.mark_area(opacity=0.5, interpolate="monotone") + base.mark_point(filled=True, size=70)

    if view_option == "All (monthly)":
        chart = chart + year_lines

    st.altair_chart(chart.properties(height=400), use_container_width=True)
