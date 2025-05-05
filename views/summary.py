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
        start = today - timedelta(days=6)
        end = today
        df_week = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
        ordered_days = [(start + timedelta(days=i)) for i in range(7)]
        day_labels = [(d.strftime("%a (%b %d)")) for d in ordered_days]
        df_week["Day"] = df_week["Date"].dt.strftime("%a (%b %d)")
        daily_km = df_week.groupby("Day")["Distance (km)"].sum().reindex(day_labels).fillna(0).reset_index()
        df_metrics = df_week.groupby("Day").agg({
            "Distance (km)": "sum",
            "Pace (min/km)": "mean",
            "Avg HR": "mean",
            "Cadence": "mean",
            "Elevation Gain": "sum"
        }).reindex(day_labels).fillna(0).reset_index()
        df_metrics["PaceLabel"] = df_metrics["Pace (min/km)"].apply(lambda x: f"Pace={int(x)}:{int((x%1)*60):02d}" if x > 0 else "")
        df_metrics["HRLabel"] = df_metrics["Avg HR"].apply(lambda x: f"HR={int(x)}" if x > 0 else "")
        df_metrics["CadLabel"] = df_metrics["Cadence"].apply(lambda x: f"Cad={int(x)}" if x > 0 else "")
        df_metrics["ElevLabel"] = df_metrics["Elevation Gain"].apply(lambda x: f"Elev={int(x)}" if x > 0 else "")
        df_agg = df_metrics
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
        df_agg = df_agg[df_agg["Distance (km)"] > 0]
        df_agg["WeekLabel"] = "Week-" + df_agg["WeekStart"].dt.isocalendar().week.astype(str)
        x_field = "WeekLabel:N"
        x_title = "Week #"
        bar_width = 40
        x_axis = alt.Axis(title=x_title, labelOverlap=False)

    elif view_option in ["3 Months", "6 Months"]:
        months_back = 3 if view_option == "3 Months" else 6
        start = today - relativedelta(months=months_back)
        df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit='d')
        df["Week"] = df["Week"].dt.normalize()
        weekly_km = df[df["Week"] >= start].groupby("Week")["Distance (km)"].sum().reset_index()
        df_agg = weekly_km.copy()
        df_agg = df_agg[df_agg["Distance (km)"] > 0]
        df_agg["WeekStart"] = df_agg["Week"]
        df_agg = df_agg.sort_values("WeekStart")
        df_agg["WeekLabel"] = "Week-" + df_agg["WeekStart"].dt.isocalendar().week.astype(str)
        x_field = "WeekLabel:N"
        x_title = "Week #"
        bar_width = 20
        x_axis = alt.Axis(title=x_title, labelAngle=-45, labelFontSize=10)

    elif view_option == "1 Year":
        months = [(today.replace(day=1) - relativedelta(months=12 - i)) for i in range(13)]
        df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
        monthly_km = df.groupby("Month")["Distance (km)"].sum().reset_index()
        df_months = pd.DataFrame({"Month": months}).merge(monthly_km, on="Month", how="left").fillna(0)
        df_months = df_months[df_months["Distance (km)"] > 0]
        df_months["Month Label"] = df_months["Month"].dt.strftime("%b %Y")
        df_agg = df_months
        x_field = "Month Label:N"
        x_title = "Month"
        bar_width = 20
        x_axis = alt.Axis(title=x_title, labelAngle=-45)

    elif view_option == "All (monthly)":
        df["MonthStart"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
        monthly_km = df.groupby("MonthStart")["Distance (km)"].sum().reset_index()
        df_agg = monthly_km[monthly_km["Distance (km)"] > 0]
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
        df_agg = yearly_km[yearly_km["Distance (km)"] > 0]
        x_field = "YearStart:T"
        x_title = "Year"
        bar_width = 40
        x_axis = alt.Axis(title=x_title, labelAngle=0, labelFontSize=12)

    sort_field = x_field.split(":")[0] if x_field.endswith(":N") else None

    if view_option == "Weekly":
        tooltip_fields = ["Day", "Distance (km)", "Pace (min/km)", "Avg HR", "Cadence", "Elevation Gain"]
    else:
        tooltip_fields = [df_agg.columns[0], "Distance (km)"]

    base = alt.Chart(df_agg).encode(
        x=alt.X(x_field, title=x_title, axis=x_axis, sort=df_agg[sort_field].tolist() if sort_field else None),
        y=alt.Y("Distance (km):Q", title="Distance (km)"),
        tooltip=tooltip_fields
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

    if view_option == "Weekly":
        for i, label_field in enumerate(["PaceLabel", "HRLabel", "CadLabel", "ElevLabel"]):
            annotation = alt.Chart(df_agg).mark_text(
                color="white",
                align="center",
                baseline="bottom",
                dy=-15 * (i + 1),
                fontSize=11
            ).encode(
                x=alt.X(x_field, sort=df_agg["Day"].tolist()),
                y=alt.Y("Distance (km):Q"),
                text=label_field
            )
            chart += annotation

    st.altair_chart(chart.properties(height=400), use_container_width=True)
